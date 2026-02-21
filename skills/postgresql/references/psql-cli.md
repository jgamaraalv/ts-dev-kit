# psql CLI Reference

## Table of Contents

1. [Inspection commands](#inspection)
2. [Query execution](#query-execution)
3. [Import / export](#import-export)
4. [Useful quick queries](#useful-quick-queries)

---

## Inspection

```sql
-- Databases
\l         -- list databases
\l+        -- with sizes

-- Schemas
\dn        -- list schemas
\dn+       -- with owners

-- Tables
\dt                  -- tables in current schema
\dt schema.*         -- tables in specific schema
\dt *.*              -- all tables
\dt+                 -- with sizes

-- Table structure
\d orders            -- columns, indexes, constraints
\d+ orders           -- verbose (with storage, stats target)

-- Indexes
\di orders           -- indexes on table
\di+                 -- with sizes

-- Views
\dv                  -- views
\dm                  -- materialized views

-- Functions
\df                  -- list functions
\df+ funcname        -- function definition

-- Sequences
\ds                  -- sequences

-- Roles / users
\du                  -- list roles
\du myuser           -- specific role

-- Extensions
\dx                  -- installed extensions

-- Describe a type
\dT enum_name

-- Show foreign tables
\det

-- Search in object names
\dt *order*          -- tables containing "order" in name
```

---

## Query execution

```sql
-- Run a single command and exit (shell)
psql -c "SELECT COUNT(*) FROM users"

-- Run a file
psql -f script.sql
\i /path/to/script.sql     -- from inside psql

-- Repeat last query
\g                    -- re-execute
\g output.txt         -- re-execute and write to file
\gx                   -- re-execute in expanded mode

-- Timing
\timing               -- toggle execution time display
\timing on

-- Edit query in $EDITOR then execute
\e

-- Edit a function
\ef function_name

-- Watch (re-run query every N seconds)
\watch 2              -- re-run last query every 2 seconds
```

---

## Import / export

```sql
-- Import CSV (client-side, works over network)
\copy tablename FROM 'file.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT col1, col2) FROM 'file.csv' WITH (FORMAT csv)

-- Import with null handling
\copy orders FROM 'data.csv' WITH (FORMAT csv, HEADER true, NULL '')

-- Export query result
\copy (SELECT * FROM users WHERE active) TO 'users.csv' WITH (FORMAT csv, HEADER true)

-- Server-side COPY (faster, requires file on server)
COPY orders FROM '/tmp/data.csv' WITH (FORMAT csv, HEADER true);
COPY (SELECT * FROM orders) TO '/tmp/export.csv' WITH (FORMAT csv, HEADER true);

-- Import SQL dump
\i dump.sql
-- Or from shell:
psql -d mydb -f dump.sql

-- pg_dump / pg_restore (shell)
pg_dump -Fc mydb > mydb.dump                    -- custom format
pg_restore -d mydb mydb.dump                    -- restore
pg_dump -h prod -d mydb | psql -h dev -d mydb  -- copy between servers
```

---

## Useful quick queries

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size(current_database()));

-- Table sizes (top 10)
SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::regclass)) AS size
FROM pg_tables WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC LIMIT 10;

-- Long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > INTERVAL '1 minute';

-- Kill a query
SELECT pg_cancel_backend(pid);    -- sends SIGINT (cancel)
SELECT pg_terminate_backend(pid); -- sends SIGTERM (disconnect)

-- Connections by state
SELECT state, COUNT(*) FROM pg_stat_activity GROUP BY state;

-- Check replication lag
SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;
```
