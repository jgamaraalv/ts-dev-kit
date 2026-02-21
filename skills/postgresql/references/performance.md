# PostgreSQL Performance Reference

## Table of Contents

1. [EXPLAIN basics](#explain)
2. [Reading EXPLAIN output](#reading-explain)
3. [Common bad plans and fixes](#bad-plans)
4. [Statistics and planner](#statistics)
5. [VACUUM and ANALYZE](#vacuum)
6. [Configuration knobs](#configuration)
7. [Bulk loading](#bulk-loading)

---

## EXPLAIN

Always use `EXPLAIN (ANALYZE, BUFFERS)` for real data — plain `EXPLAIN` shows only planner estimates.

```sql
-- Full diagnostic
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT ...;

-- JSON format (machine-parseable, tools like pev2 use this)
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT ...;

-- With settings
EXPLAIN (ANALYZE, BUFFERS, SETTINGS) SELECT ...;

-- Verbose (shows output column list per node)
EXPLAIN (ANALYZE, VERBOSE, BUFFERS) SELECT ...;

-- Auto-explain slow queries (postgresql.conf)
-- shared_preload_libraries = 'auto_explain'
-- auto_explain.log_min_duration = '1s'
-- auto_explain.log_analyze = on
-- auto_explain.log_buffers = on
```

---

## Reading EXPLAIN output

```
Seq Scan on orders  (cost=0.00..45231.00 rows=2000001 width=88)
                          (actual time=0.028..312.483 rows=2000001 loops=1)
  Buffers: shared hit=22727 read=4615
  Planning Time: 0.086 ms
  Execution Time: 401.123 ms
```

### Cost components

`(cost=startup_cost..total_cost rows=estimated_rows width=avg_row_bytes)`

- **startup_cost**: cost before first row is returned (sorting, aggregation have high startup)
- **total_cost**: estimated total cost (arbitrary planner units)
- **rows**: planner's row estimate — compare to `actual rows` to spot bad estimates
- **width**: average row size in bytes

### Actual vs estimated

`(actual time=first_row_ms..last_row_ms rows=actual_rows loops=N)`

- `rows` vs `actual rows`: large discrepancy → stale stats → run `ANALYZE`
- `loops`: node executes N times (multiply time by loops for total cost of that node)
- Total actual time = `time * loops`

### Buffer hits

`Buffers: shared hit=N read=M written=K`

- **hit**: pages from shared buffer (RAM) — fast
- **read**: pages from disk — slow
- **written**: dirty pages flushed
- High `read` = data not cached, consider increasing `shared_buffers` or adding indexes

### Node types

| Node                                     | Meaning                                                           |
| ---------------------------------------- | ----------------------------------------------------------------- |
| `Seq Scan`                               | Full table scan — fine for small tables or large fraction of rows |
| `Index Scan`                             | Uses index, fetches heap for each row                             |
| `Index Only Scan`                        | Uses covering index, no heap fetch — fastest                      |
| `Bitmap Index Scan` + `Bitmap Heap Scan` | Batches index hits, then fetches heap — good for many rows        |
| `Nested Loop`                            | Good for small inner sets                                         |
| `Hash Join`                              | Builds hash table on smaller side — good for medium sets          |
| `Merge Join`                             | Both sides pre-sorted — good for large sorted sets                |
| `Sort`                                   | Explicit sort (check if an index can eliminate)                   |
| `Hash`                                   | Build phase of Hash Join                                          |
| `Aggregate`                              | GROUP BY or aggregate function                                    |
| `Limit`                                  | Stop after N rows                                                 |

---

## Common bad plans and fixes

### Sequential scan instead of index scan

```sql
-- Problem: planner chose Seq Scan despite index existing
-- Causes:
--   1. Low selectivity (returning >10-20% of rows) — Seq Scan is correct
--   2. Stale statistics → run ANALYZE
--   3. Query prevents index use (function on column, implicit cast)

-- Bad (function on indexed column prevents index use):
WHERE date_trunc('day', created_at) = '2025-01-01'
-- Fix: use range query instead:
WHERE created_at >= '2025-01-01' AND created_at < '2025-01-02'

-- Bad (implicit cast):
WHERE user_id = '123'   -- user_id is integer, '123' is text
-- Fix: use correct type:
WHERE user_id = 123

-- Force index for testing (don't do in production):
SET enable_seqscan = off;
EXPLAIN SELECT ...;
SET enable_seqscan = on;
```

### Bad row estimate

```sql
-- symptoms: estimated rows=1000, actual rows=1000000
-- fix:
ANALYZE tablename;
-- or update stats target for this column:
ALTER TABLE orders ALTER COLUMN status SET STATISTICS 500;
ANALYZE orders;
-- default is 100; higher = more samples, better estimates, slower ANALYZE
```

### Slow Hash Join (out-of-memory)

```sql
-- In EXPLAIN output: "Batches: 8" means hash table spilled to disk
-- Fix: increase work_mem (per-session, per-sort/hash operation)
SET work_mem = '64MB';
-- Or globally in postgresql.conf: work_mem = 64MB
-- Warning: work_mem applies per operation per query, can multiply quickly
```

### N+1 queries

Not a planner issue — fix in application. Use JOINs or `jsonb_agg` instead of per-row queries.

### Slow COUNT(\*)

```sql
-- Fast approximate count (no lock needed):
SELECT reltuples::bigint AS approx_count FROM pg_class WHERE relname = 'orders';

-- Fast exact count on filtered data — use a partial index condition:
CREATE INDEX idx_orders_pending ON orders (id) WHERE status = 'pending';
SELECT COUNT(*) FROM orders WHERE status = 'pending';  -- Index Only Scan

-- Avoid COUNT(*) on entire large table; use triggers or materialized counters instead
```

### Missing index for ORDER BY + LIMIT

```sql
-- Slow: Seq Scan + Sort + Limit
SELECT * FROM orders ORDER BY created_at DESC LIMIT 20;

-- Fix: index with matching sort order
CREATE INDEX idx_orders_created_desc ON orders (created_at DESC);
-- Now: Index Scan Backward → Limit (no sort step needed)
```

---

## Statistics and planner

```sql
-- View planner statistics for a column
SELECT * FROM pg_stats WHERE tablename = 'orders' AND attname = 'status';
-- most_common_vals, most_common_freqs, n_distinct, histogram_bounds

-- Extended statistics (cross-column correlations)
CREATE STATISTICS stat_orders_user_status ON user_id, status FROM orders;
ANALYZE orders;
-- Helps planner when filtering on multiple columns with correlated values

-- Force specific join strategy (debugging only)
SET enable_hashjoin = off;
SET enable_mergejoin = off;
SET enable_nestloop = off;
```

---

## VACUUM and ANALYZE

```sql
-- Manual vacuum (removes dead tuples, no lock)
VACUUM orders;
VACUUM VERBOSE orders;   -- show progress

-- Vacuum + update stats
VACUUM ANALYZE orders;

-- Full vacuum (rewrites table, reclaims disk, EXCLUSIVE LOCK — use rarely)
VACUUM FULL orders;

-- Update stats only (lightweight, no dead tuple removal)
ANALYZE orders;
ANALYZE orders (status, user_id);  -- specific columns

-- Monitor autovacuum health
SELECT
  schemaname, relname,
  n_live_tup, n_dead_tup,
  ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_pct,
  last_autovacuum, last_autoanalyze,
  autovacuum_count
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;

-- Table bloat: if dead_pct > 20% and autovacuum hasn't run recently, investigate
-- Check autovacuum config:
SHOW autovacuum_vacuum_scale_factor;  -- default 0.2 (20% dead rows triggers vacuum)
SHOW autovacuum_vacuum_threshold;     -- default 50 (minimum dead rows)
```

---

## Configuration

Key settings (set in `postgresql.conf` or per-session):

| Parameter                      | Default | Recommended        | Notes                                 |
| ------------------------------ | ------- | ------------------ | ------------------------------------- |
| `shared_buffers`               | 128MB   | 25% of RAM         | Main cache; requires restart          |
| `work_mem`                     | 4MB     | 16–64MB            | Per operation, per query — be careful |
| `maintenance_work_mem`         | 64MB    | 256MB–1GB          | For VACUUM, CREATE INDEX              |
| `effective_cache_size`         | 4GB     | 75% of RAM         | Planner hint only (no allocation)     |
| `max_connections`              | 100     | 20–100 + pgBouncer | Each connection uses ~5MB             |
| `random_page_cost`             | 4.0     | 1.1–2.0 for SSD    | Lower = planner favors indexes        |
| `effective_io_concurrency`     | 1       | 200 for SSD        | Enables prefetching                   |
| `max_wal_size`                 | 1GB     | 2–4GB              | Larger = less WAL checkpoints         |
| `checkpoint_completion_target` | 0.5     | 0.9                | Spread checkpoint I/O                 |
| `wal_compression`              | off     | on                 | Reduces WAL size, small CPU cost      |

```sql
-- Check current settings
SHOW work_mem;
SHOW all;
SELECT name, setting, unit FROM pg_settings WHERE name IN ('work_mem', 'shared_buffers');

-- Change for current session
SET work_mem = '64MB';

-- Change permanently (needs reload, not restart)
ALTER SYSTEM SET work_mem = '64MB';
SELECT pg_reload_conf();
```

---

## Bulk loading

```sql
-- Fastest bulk insert
COPY orders FROM '/path/to/data.csv' WITH (FORMAT csv, HEADER true);
-- Or from stdin:
COPY orders FROM STDIN WITH (FORMAT csv);

-- Speed up bulk loading:
BEGIN;
  -- 1. Disable autocommit (batch in one transaction)
  -- 2. Drop indexes before load, recreate after
  DROP INDEX idx_orders_created;
  -- 3. Disable FK checks temporarily
  ALTER TABLE order_items DISABLE TRIGGER ALL;
  -- 4. Set maintenance_work_mem high
  SET maintenance_work_mem = '1GB';

  COPY orders FROM '/path/data.csv' WITH (FORMAT csv);

  ALTER TABLE order_items ENABLE TRIGGER ALL;
  CREATE INDEX idx_orders_created ON orders (created_at);
COMMIT;

-- 5. Run ANALYZE after
ANALYZE orders;

-- INSERT ... SELECT (fast for transformations)
INSERT INTO orders_archive SELECT * FROM orders WHERE created_at < '2024-01-01';
```
