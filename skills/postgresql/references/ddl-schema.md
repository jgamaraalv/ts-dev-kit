# PostgreSQL DDL & Schema Reference

## Table of Contents

1. [Data types cheatsheet](#data-types)
2. [CREATE TABLE](#create-table)
3. [Constraints](#constraints)
4. [ALTER TABLE](#alter-table)
5. [Sequences & identity](#sequences)
6. [Schemas & namespaces](#schemas)
7. [Views & materialized views](#views)
8. [Partitioning](#partitioning)

---

## Data types

| Category       | Types                                                | Notes                                                     |
| -------------- | ---------------------------------------------------- | --------------------------------------------------------- |
| Integer        | `smallint` (2B), `integer`/`int` (4B), `bigint` (8B) | Use `bigint` for PKs on large tables                      |
| Auto-increment | `GENERATED ALWAYS AS IDENTITY`                       | Preferred over `SERIAL`                                   |
| Decimal        | `numeric(p,s)` / `decimal(p,s)`                      | Exact; use for money. `real`/`double precision` are float |
| Text           | `text` (unlimited), `varchar(n)`, `char(n)`          | `text` = `varchar` without limit; prefer `text`           |
| Boolean        | `boolean`                                            | Values: `true`/`false`, `'t'`/`'f'`, `1`/`0`              |
| Dates          | `date`, `time`, `timestamp`, `timestamptz`           | Always use `timestamptz` for app timestamps               |
| Interval       | `interval`                                           | e.g., `INTERVAL '3 days'`, `INTERVAL '1 hour 30 min'`     |
| UUID           | `uuid`                                               | Use `gen_random_uuid()` (pgcrypto) for default            |
| JSON           | `json`, `jsonb`                                      | Use `jsonb` — binary, indexable, faster queries           |
| Arrays         | `int[]`, `text[]`                                    | e.g., `ARRAY['a','b']` or `'{a,b}'::text[]`               |
| Geometric      | `point`, `line`, `polygon`, `circle`                 | Use PostGIS for serious geo work                          |
| Network        | `inet`, `cidr`, `macaddr`                            |                                                           |
| Bytea          | `bytea`                                              | Binary data                                               |
| Enum           | `CREATE TYPE mood AS ENUM ('happy','sad')`           | Fast equality, no range ops                               |
| Composite      | `CREATE TYPE address AS (street text, city text)`    |                                                           |

---

## CREATE TABLE

```sql
CREATE TABLE users (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email       text NOT NULL UNIQUE,
  username    text NOT NULL CHECK (length(username) >= 3),
  status      text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','banned')),
  role        text NOT NULL DEFAULT 'user',
  metadata    jsonb NOT NULL DEFAULT '{}',
  created_at  timestamptz NOT NULL DEFAULT NOW(),
  updated_at  timestamptz NOT NULL DEFAULT NOW()
);

-- With composite primary key
CREATE TABLE order_items (
  order_id    bigint NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id  bigint NOT NULL REFERENCES products(id),
  quantity    integer NOT NULL CHECK (quantity > 0),
  price       numeric(10,2) NOT NULL,
  PRIMARY KEY (order_id, product_id)
);

-- Partitioned table
CREATE TABLE logs (
  id         bigint GENERATED ALWAYS AS IDENTITY,
  created_at timestamptz NOT NULL,
  payload    jsonb
) PARTITION BY RANGE (created_at);

-- IF NOT EXISTS
CREATE TABLE IF NOT EXISTS config (key text PRIMARY KEY, value text);

-- LIKE (copy structure)
CREATE TABLE users_archive (LIKE users INCLUDING ALL);
```

---

## Constraints

### Check constraints

```sql
-- Inline
amount numeric NOT NULL CHECK (amount > 0)

-- Named (easier to drop/identify)
amount numeric NOT NULL CONSTRAINT positive_amount CHECK (amount > 0)

-- Table-level (multi-column)
ALTER TABLE orders ADD CONSTRAINT valid_date_range CHECK (end_date > start_date);

-- Drop
ALTER TABLE orders DROP CONSTRAINT valid_date_range;
```

### NOT NULL

```sql
-- Add NOT NULL (requires a default or no existing NULLs)
ALTER TABLE users ALTER COLUMN phone SET NOT NULL;

-- Remove NOT NULL
ALTER TABLE users ALTER COLUMN phone DROP NOT NULL;
```

### UNIQUE constraints

```sql
-- Single column (inline)
email text UNIQUE

-- Named single column
email text CONSTRAINT unique_email UNIQUE

-- Composite unique (table-level only)
ALTER TABLE user_roles ADD CONSTRAINT unique_user_role UNIQUE (user_id, role_id);

-- Unique index (same effect, more control)
CREATE UNIQUE INDEX ON users (lower(email));   -- case-insensitive unique email
```

### Primary keys

```sql
-- Inline
id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY

-- Table-level (composite)
PRIMARY KEY (tenant_id, user_id)

-- Add PK after creation
ALTER TABLE old_table ADD PRIMARY KEY (id);
```

### Foreign keys

```sql
-- Basic
REFERENCES other_table(id)

-- Named with actions
CONSTRAINT fk_user
  FOREIGN KEY (user_id)
  REFERENCES users(id)
  ON DELETE CASCADE       -- also: SET NULL, SET DEFAULT, RESTRICT, NO ACTION
  ON UPDATE CASCADE
  DEFERRABLE INITIALLY DEFERRED  -- check at COMMIT time, not row-by-row

-- Add after creation
ALTER TABLE orders ADD CONSTRAINT fk_customer
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT;

-- Drop
ALTER TABLE orders DROP CONSTRAINT fk_customer;
```

### Exclusion constraints (PostGIS / ranges)

```sql
-- No overlapping reservations for the same room
ALTER TABLE reservations ADD CONSTRAINT no_overlap
  EXCLUDE USING GIST (room_id WITH =, period WITH &&);
```

---

## ALTER TABLE

```sql
-- Add column
ALTER TABLE users ADD COLUMN avatar_url text;
ALTER TABLE users ADD COLUMN score integer NOT NULL DEFAULT 0;

-- Drop column
ALTER TABLE users DROP COLUMN avatar_url;
ALTER TABLE users DROP COLUMN avatar_url CASCADE;  -- also drops dependencies

-- Rename column
ALTER TABLE users RENAME COLUMN username TO handle;

-- Change type
ALTER TABLE users ALTER COLUMN score TYPE bigint;
ALTER TABLE users ALTER COLUMN score TYPE numeric USING score::numeric;

-- Set/drop default
ALTER TABLE users ALTER COLUMN status SET DEFAULT 'active';
ALTER TABLE users ALTER COLUMN status DROP DEFAULT;

-- Rename table
ALTER TABLE users RENAME TO accounts;

-- Add/drop schema
ALTER TABLE users SET SCHEMA archive;
```

---

## Sequences & identity

```sql
-- Modern: GENERATED ALWAYS AS IDENTITY (SQL standard, preferred)
id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY
-- Override allowed only with OVERRIDING SYSTEM VALUE:
INSERT INTO t (id, name) OVERRIDING SYSTEM VALUE VALUES (999, 'admin');

-- GENERATED BY DEFAULT AS IDENTITY (allows override without keyword)
id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY

-- Old: SERIAL (shorthand, still common)
id serial PRIMARY KEY       -- int + sequence
id bigserial PRIMARY KEY    -- bigint + sequence

-- Manual sequence
CREATE SEQUENCE order_number_seq START 1000 INCREMENT 1;
SELECT nextval('order_number_seq');
SELECT currval('order_number_seq');
SELECT setval('order_number_seq', 5000);

-- Reset identity sequence after bulk insert
ALTER TABLE users ALTER COLUMN id RESTART WITH 1;
```

---

## Schemas

```sql
CREATE SCHEMA analytics;
CREATE TABLE analytics.events (...);

-- Search path (which schemas to look in, in order)
SET search_path TO myapp, public;
SHOW search_path;

-- Grant
GRANT USAGE ON SCHEMA analytics TO readonly_role;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO readonly_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO readonly_role;
```

---

## Views & materialized views

```sql
-- View
CREATE OR REPLACE VIEW active_users AS
SELECT * FROM users WHERE status = 'active';

-- Updatable views (automatically updatable if simple enough)
CREATE VIEW recent_orders AS SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '30 days';

-- Materialized view (cached snapshot)
CREATE MATERIALIZED VIEW daily_stats AS
SELECT DATE_TRUNC('day', created_at) AS day, COUNT(*) FROM events GROUP BY 1;

-- Refresh (blocks reads by default)
REFRESH MATERIALIZED VIEW daily_stats;

-- Refresh without locking (needs unique index)
CREATE UNIQUE INDEX ON daily_stats (day);
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_stats;
```

---

## Partitioning

```sql
-- Create parent table
CREATE TABLE metrics (
  id         bigint GENERATED ALWAYS AS IDENTITY,
  recorded_at timestamptz NOT NULL,
  value      numeric
) PARTITION BY RANGE (recorded_at);

-- Create monthly partitions
CREATE TABLE metrics_2025_01 PARTITION OF metrics
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE metrics_2025_02 PARTITION OF metrics
  FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Default partition (catches anything not matched)
CREATE TABLE metrics_default PARTITION OF metrics DEFAULT;

-- List partitioning
CREATE TABLE orders (id bigint, region text, ...) PARTITION BY LIST (region);
CREATE TABLE orders_br PARTITION OF orders FOR VALUES IN ('BR', 'PT');
CREATE TABLE orders_us PARTITION OF orders FOR VALUES IN ('US', 'CA');

-- Detach (fast, non-blocking) / Attach partition
ALTER TABLE metrics DETACH PARTITION metrics_2025_01 CONCURRENTLY;
ALTER TABLE metrics ATTACH PARTITION metrics_archive
  FOR VALUES FROM ('2020-01-01') TO ('2025-01-01');
```

Key partitioning facts:

- Partition key column cannot be NULL (goes to DEFAULT partition).
- Indexes must be created on each partition separately (or on the parent to cascade).
- `PARTITION PRUNING` happens automatically at query time when the WHERE clause matches the partition key.
