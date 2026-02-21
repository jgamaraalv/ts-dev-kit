# PostgreSQL Transactions Reference

## Table of Contents

1. [Transaction basics](#basics)
2. [Savepoints](#savepoints)
3. [Isolation levels](#isolation-levels)
4. [Locking](#locking)
5. [Advisory locks](#advisory-locks)
6. [MVCC overview](#mvcc)
7. [Common patterns](#patterns)

---

## Basics

Every SQL statement runs inside a transaction. Without `BEGIN`, each statement has an implicit `BEGIN` + `COMMIT`.

```sql
-- Explicit transaction block
BEGIN;
  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
  UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;

-- Rollback on error
BEGIN;
  DELETE FROM orders WHERE id = 42;
  -- Discovered wrong order, cancel:
ROLLBACK;

-- Set isolation level (must be first statement after BEGIN)
BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
  SELECT ...;
COMMIT;

-- Shorthand
BEGIN ISOLATION LEVEL REPEATABLE READ;
```

DDL statements (`CREATE TABLE`, `ALTER TABLE`, `DROP`) are transactional in PostgreSQL — they can be rolled back.

---

## Savepoints

Savepoints allow partial rollback within a transaction:

```sql
BEGIN;
  INSERT INTO orders (customer_id, total) VALUES (1, 100) RETURNING id;  -- id = 42

  SAVEPOINT sp1;

  INSERT INTO order_items (order_id, product_id, qty)
  VALUES (42, 999, 1);  -- product 999 doesn't exist → error

  ROLLBACK TO SAVEPOINT sp1;  -- undo order_items insert, keep orders insert

  INSERT INTO order_items (order_id, product_id, qty)
  VALUES (42, 1, 1);   -- correct product

  RELEASE SAVEPOINT sp1;  -- optional cleanup
COMMIT;
```

After `ROLLBACK TO SAVEPOINT`, the savepoint still exists and can be rolled back to again. Use `RELEASE SAVEPOINT` to free it.

---

## Isolation levels

PostgreSQL supports four isolation levels. Default is **Read Committed**.

| Level                        | Dirty Read     | Non-repeatable Read | Phantom Read     | Serialization Anomaly |
| ---------------------------- | -------------- | ------------------- | ---------------- | --------------------- |
| Read Uncommitted             | Not possible\* | Possible            | Possible         | Possible              |
| **Read Committed** (default) | Not possible\* | **Possible**        | **Possible**     | **Possible**          |
| Repeatable Read              | Not possible   | Not possible        | Not possible\*\* | **Possible**          |
| Serializable                 | Not possible   | Not possible        | Not possible     | Not possible          |

\* PostgreSQL never allows dirty reads even at Read Uncommitted.
\*\* PostgreSQL's Repeatable Read prevents phantoms using MVCC snapshots.

### Read Committed (default)

Each statement sees its own snapshot (data committed before the statement started). Safe for most OLTP. Vulnerable to "lost update" in read-modify-write patterns without locking.

```sql
-- Common pattern: SELECT FOR UPDATE to prevent lost update
BEGIN;
SELECT * FROM products WHERE id = $1 FOR UPDATE;  -- lock the row
UPDATE products SET stock = stock - 1 WHERE id = $1;
COMMIT;
```

### Repeatable Read

The entire transaction sees a single consistent snapshot (taken at first statement). Prevents non-repeatable reads and phantoms. May abort with:
`ERROR: could not serialize access due to concurrent update` — retry the transaction.

```sql
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT SUM(balance) FROM accounts;   -- snapshot taken here
-- Other transactions' commits won't affect our subsequent reads
COMMIT;
```

### Serializable

Strongest guarantee. Transactions execute as if run serially. Uses Serializable Snapshot Isolation (SSI). May abort with:
`ERROR: could not serialize access due to read/write dependencies among transactions` — must retry.

```sql
BEGIN ISOLATION LEVEL SERIALIZABLE;
-- Safe for concurrent write-skew prevention
COMMIT;
```

---

## Locking

### Row-level locks

```sql
-- FOR UPDATE — exclusive lock; blocks other FOR UPDATE, FOR SHARE, UPDATE, DELETE
SELECT * FROM orders WHERE id = $1 FOR UPDATE;

-- FOR SHARE — shared lock; blocks FOR UPDATE but not other FOR SHARE
SELECT * FROM users WHERE id = $1 FOR SHARE;

-- SKIP LOCKED — skip rows currently locked (queue processing)
SELECT * FROM jobs WHERE status = 'pending' LIMIT 1 FOR UPDATE SKIP LOCKED;

-- NOWAIT — fail immediately if lock unavailable
SELECT * FROM orders WHERE id = $1 FOR UPDATE NOWAIT;

-- Lock specific tables (usually not needed)
LOCK TABLE orders IN EXCLUSIVE MODE;
LOCK TABLE orders IN ACCESS SHARE MODE;  -- weakest, just prevents DROP TABLE
```

### Table-level lock modes (strongest to weakest)

| Mode                     | Blocks                             | When acquired                              |
| ------------------------ | ---------------------------------- | ------------------------------------------ |
| `ACCESS EXCLUSIVE`       | Everything                         | ALTER TABLE, DROP TABLE, VACUUM FULL       |
| `EXCLUSIVE`              | All writes + ACCESS SHARE          | Rare                                       |
| `SHARE ROW EXCLUSIVE`    | Row writes + SHARE                 | CREATE TRIGGER                             |
| `SHARE`                  | Row writes                         | CREATE INDEX (non-concurrent)              |
| `SHARE UPDATE EXCLUSIVE` | Schema changes                     | VACUUM, ANALYZE, CREATE INDEX CONCURRENTLY |
| `ROW EXCLUSIVE`          | ACCESS EXCLUSIVE, EXCLUSIVE, SHARE | INSERT, UPDATE, DELETE                     |
| `ROW SHARE`              | ACCESS EXCLUSIVE, EXCLUSIVE        | SELECT FOR UPDATE/SHARE                    |
| `ACCESS SHARE`           | ACCESS EXCLUSIVE only              | SELECT                                     |

### Detecting lock conflicts

```sql
-- See current locks
SELECT pid, relation::regclass, mode, granted
FROM pg_locks
WHERE relation IS NOT NULL;

-- Find blocking queries
SELECT blocked.pid, blocked.query, blocking.pid AS blocking_pid, blocking.query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE NOT blocked.granted;
```

---

## Advisory locks

Application-level locks not tied to any table — useful for mutual exclusion across processes.

```sql
-- Session-level (auto-released on disconnect)
SELECT pg_advisory_lock(12345);        -- exclusive
SELECT pg_advisory_lock_shared(12345); -- shared
SELECT pg_advisory_unlock(12345);
SELECT pg_advisory_unlock_all();

-- Transaction-level (auto-released at COMMIT/ROLLBACK)
SELECT pg_advisory_xact_lock(12345);
SELECT pg_advisory_xact_lock_shared(12345);

-- Try to acquire without blocking (returns bool)
SELECT pg_try_advisory_lock(12345);

-- Use hash of text for namespacing
SELECT pg_advisory_lock(hashtext('my-job-lock'));
```

---

## MVCC

PostgreSQL uses Multi-Version Concurrency Control: readers never block writers; writers never block readers.

Key concepts:

- Each row has `xmin` (transaction that inserted) and `xmax` (transaction that deleted/updated).
- A transaction sees rows where `xmin` is committed and visible, and `xmax` is not yet committed.
- Dead tuples (old row versions) accumulate and must be reclaimed by `VACUUM`.

```sql
-- See transaction ID (xmin) of rows
SELECT *, xmin, xmax FROM users LIMIT 5;

-- Current transaction ID (txid_current() is deprecated since PG 13)
SELECT pg_current_xact_id();
```

For VACUUM and maintenance, see [performance.md](performance.md).

---

## Common patterns

### Optimistic locking (application-level)

```sql
-- Add version column
ALTER TABLE products ADD COLUMN version integer NOT NULL DEFAULT 0;

-- Read
SELECT id, price, version FROM products WHERE id = $1;

-- Update — fail if version changed since read
UPDATE products
SET price = $new_price, version = version + 1
WHERE id = $1 AND version = $expected_version;
-- Check affected rows: if 0, conflict detected → retry
```

### Queue processing with SKIP LOCKED

```sql
BEGIN;
SELECT id, payload FROM jobs
WHERE status = 'pending'
ORDER BY created_at
LIMIT 1
FOR UPDATE SKIP LOCKED;

-- Process the job...

UPDATE jobs SET status = 'done', processed_at = NOW() WHERE id = $1;
COMMIT;
```

### Deferred constraint checking

```sql
-- Useful for circular references or bulk data loading
BEGIN;
SET CONSTRAINTS ALL DEFERRED;
  INSERT INTO a (id, b_id) VALUES (1, 2);
  INSERT INTO b (id, a_id) VALUES (2, 1);  -- FK to a(1) is deferred
COMMIT;  -- constraints checked here
```

### Two-phase commit (distributed transactions)

```sql
-- Prepare
BEGIN;
  UPDATE ...;
PREPARE TRANSACTION 'my-txn-id';

-- Commit or rollback from any connection
COMMIT PREPARED 'my-txn-id';
ROLLBACK PREPARED 'my-txn-id';

-- View prepared transactions
SELECT * FROM pg_prepared_xacts;
```
