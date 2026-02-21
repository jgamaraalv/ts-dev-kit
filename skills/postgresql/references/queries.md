# PostgreSQL Queries Reference

## Table of Contents

1. [SELECT anatomy](#select-anatomy)
2. [JOINs](#joins)
3. [Subqueries](#subqueries)
4. [CTEs (WITH clauses)](#ctes)
5. [Window functions](#window-functions)
6. [Aggregation](#aggregation)
7. [Set operations](#set-operations)
8. [INSERT / UPDATE / DELETE / UPSERT](#dml)
9. [LATERAL joins](#lateral)

---

## SELECT anatomy

```sql
SELECT [DISTINCT] expression [AS alias], ...
FROM table [AS alias]
[JOIN ...]
[WHERE condition]
[GROUP BY expression, ...]
[HAVING condition]
[WINDOW w AS (window_def)]
[ORDER BY expression [ASC|DESC] [NULLS FIRST|LAST]]
[LIMIT n] [OFFSET n]
[FOR UPDATE | FOR SHARE]
```

Execution order (logical): FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT/OFFSET.

```sql
-- DISTINCT ON — keep first row per group (PostgreSQL extension)
SELECT DISTINCT ON (department_id) department_id, name, salary
FROM employees
ORDER BY department_id, salary DESC;

-- Return row if exists, else nothing
SELECT * FROM users WHERE email = $1 FOR UPDATE;
```

---

## JOINs

```sql
-- INNER JOIN (default)
SELECT o.id, c.name FROM orders o JOIN customers c ON o.customer_id = c.id;

-- LEFT JOIN — all rows from left, NULL for unmatched right
SELECT c.name, COUNT(o.id) FROM customers c LEFT JOIN orders o ON o.customer_id = c.id GROUP BY c.id;

-- FULL OUTER JOIN
SELECT a.id, b.id FROM a FULL OUTER JOIN b ON a.key = b.key;

-- CROSS JOIN — cartesian product
SELECT * FROM sizes CROSS JOIN colors;

-- Self-join
SELECT e.name, m.name AS manager FROM employees e LEFT JOIN employees m ON e.manager_id = m.id;

-- Multiple join conditions
SELECT * FROM a JOIN b ON a.x = b.x AND a.y > b.y;
```

---

## Subqueries

```sql
-- In WHERE
SELECT * FROM orders WHERE customer_id IN (SELECT id FROM customers WHERE country = 'BR');

-- EXISTS (stops at first match — efficient)
SELECT * FROM customers c WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);

-- Correlated subquery in SELECT (runs once per row — can be slow)
SELECT name, (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) AS order_count
FROM customers c;

-- Scalar subquery
SELECT * FROM orders WHERE total > (SELECT AVG(total) FROM orders);

-- Derived table (subquery in FROM)
SELECT dept, avg_sal FROM (
  SELECT department, AVG(salary) AS avg_sal FROM employees GROUP BY department
) AS dept_avg
WHERE avg_sal > 50000;
```

---

## CTEs

```sql
-- Basic CTE
WITH recent_orders AS (
  SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days'
)
SELECT customer_id, COUNT(*) FROM recent_orders GROUP BY customer_id;

-- Multiple CTEs
WITH
  a AS (SELECT ...),
  b AS (SELECT ... FROM a)
SELECT * FROM b;

-- Writable CTE (INSERT/UPDATE/DELETE returning rows)
WITH deleted AS (
  DELETE FROM sessions WHERE expires_at < NOW() RETURNING user_id
)
INSERT INTO audit_log (user_id, event) SELECT user_id, 'session_expired' FROM deleted;

-- Recursive CTE (e.g., tree traversal)
WITH RECURSIVE tree AS (
  -- Base case
  SELECT id, parent_id, name, 0 AS depth FROM categories WHERE parent_id IS NULL
  UNION ALL
  -- Recursive case
  SELECT c.id, c.parent_id, c.name, t.depth + 1
  FROM categories c JOIN tree t ON c.parent_id = t.id
)
SELECT * FROM tree ORDER BY depth, name;
```

CTE materialization: By default CTEs are optimization fences (materialized once). Add `NOT MATERIALIZED` to allow the planner to inline them:

```sql
WITH data AS NOT MATERIALIZED (SELECT * FROM big_table WHERE ...)
SELECT * FROM data WHERE extra_filter;
```

---

## Window functions

```sql
-- Syntax
function() OVER ([PARTITION BY col] [ORDER BY col] [frame_clause])

-- ROW_NUMBER, RANK, DENSE_RANK
SELECT name, salary,
  ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) AS rn,
  RANK()       OVER (PARTITION BY dept ORDER BY salary DESC) AS rnk,
  DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS drnk
FROM employees;

-- Running total
SELECT date, amount, SUM(amount) OVER (ORDER BY date) AS running_total FROM sales;

-- Moving average (last 7 rows)
SELECT date, amount,
  AVG(amount) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS moving_avg
FROM sales;

-- LAG / LEAD — access adjacent rows
SELECT date, amount,
  LAG(amount, 1) OVER (ORDER BY date) AS prev_day,
  amount - LAG(amount, 1) OVER (ORDER BY date) AS delta
FROM sales;

-- FIRST_VALUE / LAST_VALUE
SELECT dept, name, salary,
  FIRST_VALUE(name) OVER (PARTITION BY dept ORDER BY salary DESC) AS top_earner
FROM employees;

-- Named WINDOW clause (reuse)
SELECT name, salary,
  RANK() OVER w,
  DENSE_RANK() OVER w
FROM employees
WINDOW w AS (PARTITION BY dept ORDER BY salary DESC);
```

Frame clauses: `ROWS BETWEEN n PRECEDING AND CURRENT ROW`, `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`.

---

## Aggregation

```sql
SELECT dept,
  COUNT(*),
  COUNT(DISTINCT manager_id),
  SUM(salary),
  AVG(salary),
  MIN(salary), MAX(salary),
  ARRAY_AGG(name ORDER BY salary DESC),
  STRING_AGG(name, ', ' ORDER BY name),
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) AS median
FROM employees
WHERE active = true
GROUP BY dept
HAVING COUNT(*) > 5
ORDER BY AVG(salary) DESC;

-- FILTER clause (conditional aggregate)
SELECT
  COUNT(*) FILTER (WHERE status = 'active') AS active_count,
  COUNT(*) FILTER (WHERE status = 'inactive') AS inactive_count
FROM users;

-- GROUPING SETS / ROLLUP / CUBE
SELECT region, product, SUM(revenue)
FROM sales
GROUP BY ROLLUP (region, product);   -- subtotals per region + grand total
```

---

## Set operations

```sql
UNION     -- deduplicate
UNION ALL -- keep duplicates (faster)
INTERSECT -- rows in both
EXCEPT    -- rows in first but not second

SELECT id FROM table_a
UNION ALL
SELECT id FROM table_b
ORDER BY id;           -- ORDER BY applies to the combined result
```

---

## DML

```sql
-- INSERT
INSERT INTO users (name, email, created_at)
VALUES ('Alice', 'alice@example.com', NOW())
RETURNING id, created_at;

-- INSERT multiple rows
INSERT INTO tags (name) VALUES ('dogs'), ('cats'), ('pets');

-- UPSERT (ON CONFLICT)
INSERT INTO user_prefs (user_id, key, value)
VALUES ($1, $2, $3)
ON CONFLICT (user_id, key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

-- ON CONFLICT DO NOTHING
INSERT INTO events (id, payload) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING;

-- UPDATE
UPDATE orders
SET status = 'shipped', updated_at = NOW()
WHERE id = $1 AND status = 'processing'
RETURNING *;

-- UPDATE with JOIN (using FROM)
UPDATE employees e
SET salary = e.salary * 1.1
FROM departments d
WHERE e.dept_id = d.id AND d.name = 'Engineering';

-- DELETE
DELETE FROM sessions WHERE expires_at < NOW() RETURNING id;

-- TRUNCATE (faster than DELETE for full table, unlogged)
TRUNCATE TABLE audit_log RESTART IDENTITY CASCADE;
```

---

## LATERAL

`LATERAL` allows a subquery in `FROM` to reference columns from preceding tables:

```sql
-- Get latest N orders per customer
SELECT c.name, o.*
FROM customers c,
LATERAL (
  SELECT * FROM orders WHERE customer_id = c.id ORDER BY created_at DESC LIMIT 3
) o;

-- With LEFT JOIN LATERAL (include customers with no orders)
SELECT c.name, o.id
FROM customers c
LEFT JOIN LATERAL (
  SELECT id FROM orders WHERE customer_id = c.id ORDER BY created_at DESC LIMIT 1
) o ON true;
```
