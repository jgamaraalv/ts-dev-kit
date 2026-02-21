# PostgreSQL Indexes Reference

## Table of Contents

1. [Index type decision guide](#decision-guide)
2. [B-tree](#b-tree)
3. [Hash](#hash)
4. [GIN](#gin)
5. [GiST](#gist)
6. [BRIN](#brin)
7. [Partial indexes](#partial-indexes)
8. [Expression indexes](#expression-indexes)
9. [Multicolumn indexes](#multicolumn-indexes)
10. [Index creation options](#creation-options)
11. [Inspecting indexes](#inspecting)

---

## Decision guide

| Situation                                                        | Use                                                |
| ---------------------------------------------------------------- | -------------------------------------------------- |
| Equality / range on any sortable type (int, text, date, numeric) | **B-tree** (default)                               |
| Equality-only on large values where hash fits in memory          | **Hash**                                           |
| `LIKE 'foo%'` prefix match                                       | **B-tree** with `text_pattern_ops` if non-C locale |
| `LIKE '%foo'` suffix / `LIKE '%foo%'`                            | **GIN** with `pg_trgm` extension                   |
| Full-text search (`@@` tsvector)                                 | **GIN**                                            |
| Array containment (`@>`, `<@`, `&&`)                             | **GIN**                                            |
| JSONB containment / key existence                                | **GIN**                                            |
| Geometric / PostGIS spatial queries                              | **GiST**                                           |
| Nearest-neighbor (`ORDER BY location <-> point`)                 | **GiST**                                           |
| `tsvector` (alternative to GIN, smaller, faster build)           | **GiST**                                           |
| Range types (`int4range`, `tstzrange`)                           | **GiST**                                           |
| Append-only / time-series, very large tables, loose range filter | **BRIN**                                           |
| Index only non-null or subset of rows                            | **Partial index**                                  |
| Index on expression / function result                            | **Expression index**                               |

---

## B-tree

Default type. Use for: `<`, `<=`, `=`, `>=`, `>`, `BETWEEN`, `IN`, `IS NULL`, `IS NOT NULL`, `LIKE 'prefix%'`.

```sql
-- Basic
CREATE INDEX idx_users_email ON users (email);

-- Descending (useful when queries ORDER BY col DESC)
CREATE INDEX idx_orders_created_desc ON orders (created_at DESC);

-- Include (covering index — avoid heap fetch)
CREATE INDEX idx_orders_customer ON orders (customer_id) INCLUDE (status, total);

-- Pattern matching (non-C locale requires operator class)
CREATE INDEX idx_users_name_pattern ON users (name text_pattern_ops);
-- Then: WHERE name LIKE 'Alice%' uses this index
```

B-tree index can support `ORDER BY` without a sort step if the index column order matches.

---

## Hash

Only for `=` comparisons. Faster than B-tree for pure equality on large keys, but cannot support range queries or sorting.

```sql
CREATE INDEX idx_sessions_token ON sessions USING HASH (token);
```

Note: Hash indexes are WAL-logged (crash-safe) since PostgreSQL 10.

---

## GIN (Generalized Inverted Index)

Best for multi-valued columns: arrays, JSONB, full-text (`tsvector`). Slower to build and update than B-tree; query-time is faster than GiST for containment checks.

```sql
-- Full-text search
CREATE INDEX idx_posts_search ON posts USING GIN (to_tsvector('portuguese', content));

-- JSONB — supports @>, ?, ?|, ?&
CREATE INDEX idx_profiles_data ON profiles USING GIN (data);
-- Specific path (jsonb_path_ops — smaller, only @> operator)
CREATE INDEX idx_profiles_data_path ON profiles USING GIN (data jsonb_path_ops);

-- Array containment
CREATE INDEX idx_products_tags ON products USING GIN (tags);

-- Trigram (requires pg_trgm extension) — enables LIKE '%foo%', ILIKE, similarity
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_users_name_trgm ON users USING GIN (name gin_trgm_ops);
-- Now: WHERE name ILIKE '%alice%' uses the index
```

GIN vs `jsonb_path_ops`:

- Default `jsonb_ops`: supports `@>`, `?`, `?|`, `?&`
- `jsonb_path_ops`: supports only `@>` but index is smaller and faster

---

## GiST (Generalized Search Tree)

Infrastructure for custom index types. Built-in support for: geometric types, `tsvector`, range types, PostGIS geometry.

```sql
-- Geometric nearest-neighbor
CREATE INDEX idx_locations_point ON locations USING GIST (coordinates);
-- Query: SELECT * FROM locations ORDER BY coordinates <-> '(0,0)'::point LIMIT 10;

-- Range type (no overlap)
CREATE INDEX idx_reservations_period ON reservations USING GIST (period);
-- Query: WHERE period && '[2025-01-01, 2025-01-07)'::daterange

-- Full-text (alternative to GIN — smaller index, slower search)
CREATE INDEX idx_posts_fts ON posts USING GIST (to_tsvector('english', body));

-- PostGIS
CREATE INDEX idx_geom ON places USING GIST (geom);
```

---

## BRIN (Block Range INdex)

Tiny footprint index. Stores min/max per block range. Effective when column values are physically correlated with insertion order (e.g., `created_at` on append-only tables, sensor readings, log IDs).

```sql
CREATE INDEX idx_logs_created ON logs USING BRIN (created_at);
-- pages_per_range controls granularity (default 128)
CREATE INDEX idx_metrics_time ON metrics USING BRIN (recorded_at) WITH (pages_per_range = 32);
```

Do NOT use BRIN if rows are frequently updated or if values are randomly distributed — the index will be ineffective.

---

## Partial indexes

Index only a subset of rows. Reduces index size and maintenance cost. The WHERE clause must be satisfied by the query for the index to be used.

```sql
-- Index only active users (most queries filter by status = 'active')
CREATE INDEX idx_users_active_email ON users (email) WHERE status = 'active';

-- Index only unprocessed jobs
CREATE INDEX idx_jobs_pending ON jobs (created_at) WHERE processed_at IS NULL;

-- Unique partial index — email unique only among active users
CREATE UNIQUE INDEX idx_users_unique_email_active ON users (email) WHERE deleted_at IS NULL;
```

The query WHERE clause must be _implied_ by the partial index's condition for the planner to use it. Example: `WHERE status = 'active' AND email = $1` will use `WHERE status = 'active'` partial index.

---

## Expression indexes

Index on the result of an expression or function. The query must use the exact same expression.

```sql
-- Case-insensitive unique email
CREATE UNIQUE INDEX idx_users_email_lower ON users (lower(email));
-- Query must use: WHERE lower(email) = lower($1)

-- Date part
CREATE INDEX idx_orders_year ON orders (EXTRACT(YEAR FROM created_at));

-- Computed column (immutable functions only)
CREATE INDEX idx_products_slug ON products (regexp_replace(lower(name), '\s+', '-', 'g'));
```

Only **immutable** functions can be indexed (same input always yields same output). `NOW()` is volatile — cannot be indexed.

---

## Multicolumn indexes

```sql
CREATE INDEX idx_orders_user_status ON orders (user_id, status, created_at DESC);
```

Rules:

- Columns are used left-to-right. An index on `(a, b, c)` supports queries on `a`, `(a, b)`, and `(a, b, c)`.
- A query on just `b` or `c` cannot use this index (unless the planner can bitmap-and with other indexes).
- Leading equality columns are most important; put high-selectivity equality columns first.
- Put the range/sort column last.

Example query that uses `(user_id, status, created_at DESC)`:

```sql
WHERE user_id = $1 AND status = 'pending' ORDER BY created_at DESC LIMIT 10
```

---

## Creation options

```sql
-- Non-blocking creation (cannot be in a transaction block)
CREATE INDEX CONCURRENTLY idx_name ON table (col);

-- Named index
CREATE INDEX idx_orders_customer_id ON orders (customer_id);

-- Unique
CREATE UNIQUE INDEX idx_users_email ON users (email);

-- Tablespace
CREATE INDEX idx_name ON table (col) TABLESPACE fast_ssd;

-- Fill factor (leave space for HOT updates)
CREATE INDEX idx_name ON table (col) WITH (fillfactor = 70);

-- Drop
DROP INDEX idx_name;
DROP INDEX CONCURRENTLY idx_name;  -- non-blocking

-- Rebuild (e.g., after bloat)
REINDEX INDEX idx_name;
REINDEX TABLE tablename;          -- rebuilds all indexes on table
REINDEX TABLE CONCURRENTLY tablename;
```

---

## Inspecting

```sql
-- List indexes on a table
\di+ tablename    -- in psql
-- or:
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'orders';

-- Index usage stats (reset on restart)
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan;

-- Find unused indexes (idx_scan = 0 after some time in prod)
SELECT indexrelid::regclass, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND schemaname = 'public';

-- Index bloat check
SELECT relname, pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- Check if a query uses an index
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
-- Look for: "Index Scan", "Index Only Scan", "Bitmap Index Scan"
-- "Seq Scan" means no index was used
```
