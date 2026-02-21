# PostgreSQL JSONB Reference

## Table of Contents

1. [json vs jsonb](#json-vs-jsonb)
2. [Operators](#operators)
3. [Functions](#functions)
4. [Modifying JSONB](#modifying)
5. [GIN indexing](#gin-indexing)
6. [jsonpath](#jsonpath)
7. [Common patterns](#patterns)

---

## json vs jsonb

| Feature          | `json`                      | `jsonb`                   |
| ---------------- | --------------------------- | ------------------------- |
| Storage          | Raw text (input preserved)  | Binary parsed             |
| Write speed      | Faster                      | Slower (parsing overhead) |
| Read/query speed | Slower (re-parse each time) | **Faster**                |
| Indexing         | Not possible                | **GIN indexable**         |
| Key order        | Preserved                   | **Not preserved**         |
| Duplicate keys   | Last one wins at read       | First one kept            |
| Whitespace       | Preserved                   | Stripped                  |

**Always use `jsonb`** unless you need exact input preservation.

---

## Operators

### Field access

```sql
data -> 'key'          -- returns jsonb (preserves type)
data ->> 'key'         -- returns text
data -> 2              -- array element by index (0-based)
data ->> 2             -- array element as text
data #> '{a,b,c}'      -- nested path → jsonb
data #>> '{a,b,c}'     -- nested path → text

-- Examples
SELECT data -> 'name' FROM profiles;             -- jsonb: "Alice"
SELECT data ->> 'name' FROM profiles;            -- text: Alice
SELECT data #>> '{address,city}' FROM profiles;  -- text: New York
SELECT data -> 'tags' -> 0 FROM profiles;        -- first tag (jsonb)
```

### Containment

```sql
-- @>  left contains right (right is a subset of left)
SELECT * FROM products WHERE attributes @> '{"color": "red"}';
SELECT * FROM products WHERE attributes @> '{"tags": ["sale"]}';

-- <@  left is contained in right
SELECT * FROM products WHERE '{"color": "red"}' <@ attributes;
```

### Key existence

```sql
-- ?   key exists at top level
SELECT * FROM profiles WHERE data ? 'email';

-- ?|  any of these keys exist
SELECT * FROM profiles WHERE data ?| ARRAY['email', 'phone'];

-- ?&  all of these keys exist
SELECT * FROM profiles WHERE data ?& ARRAY['email', 'phone'];
```

### Concatenation & deletion

```sql
-- ||  merge two jsonb values (right overwrites left on conflict)
SELECT '{"a":1}'::jsonb || '{"b":2}'::jsonb;  -- {"a":1,"b":2}
SELECT data || '{"verified":true}'::jsonb FROM users;

-- -   delete key or array element
SELECT '{"a":1,"b":2}'::jsonb - 'a';      -- {"b":2}
SELECT '{"a":1,"b":2}'::jsonb - ARRAY['a','b'];  -- {}
SELECT '[1,2,3]'::jsonb - 1;              -- removes index 1 → [1,3]

-- #-  delete at path
SELECT '{"a":{"b":1}}'::jsonb #- '{a,b}';  -- {"a":{}}
```

---

## Functions

```sql
-- Build
jsonb_build_object('key', value, 'key2', value2)
jsonb_build_array(1, 2, 3)
to_jsonb(any_value)
row_to_json(row)

-- Inspect
jsonb_typeof(data)          -- 'object', 'array', 'string', 'number', 'boolean', 'null'
jsonb_array_length(data)    -- length of JSON array
jsonb_object_keys(data)     -- set of top-level keys

-- Array elements as rows
SELECT elem FROM jsonb_array_elements('["a","b","c"]'::jsonb) AS elem;
SELECT elem ->> 0 FROM jsonb_array_elements_text('["a","b","c"]'::jsonb) AS elem;

-- Object as key-value rows
SELECT key, value FROM jsonb_each('{"a":1,"b":2}'::jsonb);
SELECT key, value FROM jsonb_each_text('{"a":1,"b":2}'::jsonb);

-- Strip nulls
jsonb_strip_nulls('{"a":1,"b":null}'::jsonb)  -- {"a":1}

-- Pretty print
jsonb_pretty('{"a":1}'::jsonb)
```

---

## Modifying

```sql
-- jsonb_set(target, path, new_value, create_if_missing = true)
SELECT jsonb_set(data, '{address,city}', '"Rio de Janeiro"') FROM profiles;
SELECT jsonb_set(data, '{score}', '42', true) FROM profiles;  -- creates if missing

-- jsonb_insert(target, path, value, insert_after = false)
-- Inserts into array (doesn't overwrite existing)
SELECT jsonb_insert('{"a":[1,2,3]}'::jsonb, '{a,1}', '99');  -- [1,99,2,3]

-- UPDATE with jsonb_set
UPDATE users
SET metadata = jsonb_set(metadata, '{last_login}', to_jsonb(NOW()))
WHERE id = $1;

-- Merge/update top-level key
UPDATE users
SET preferences = preferences || '{"theme":"dark"}'::jsonb
WHERE id = $1;

-- Delete a key
UPDATE users
SET metadata = metadata - 'temp_token'
WHERE id = $1;
```

---

## GIN indexing

```sql
-- Default operator class: supports @>, ?, ?|, ?&
CREATE INDEX idx_products_attrs ON products USING GIN (attributes);

-- jsonb_path_ops: only supports @>, but smaller and faster
CREATE INDEX idx_products_attrs_path ON products USING GIN (attributes jsonb_path_ops);

-- Index a specific extracted value (B-tree on expression)
CREATE INDEX idx_users_role ON users ((metadata ->> 'role'));
```

For detailed GIN indexing, see [indexes.md](indexes.md).

---

## jsonpath

jsonpath is a query language for JSONB (similar to XPath for XML). Available since PG 12.

```sql
-- @ represents the current node
-- $  represents the root

-- Check if path matches
SELECT jsonb_path_exists('{"a":{"b":1}}', '$.a.b');  -- true

-- Extract matching values
SELECT jsonb_path_query('{"items":[1,2,3]}', '$.items[*]');
-- Returns 1, 2, 3 as separate rows

-- Query first match
SELECT jsonb_path_query_first('{"users":[{"name":"Alice"},{"name":"Bob"}]}', '$.users[0].name');
-- "Alice"

-- Filter array elements
SELECT jsonb_path_query('[{"n":1},{"n":5},{"n":2}]'::jsonb, '$[*] ? (@.n > 3)');
-- {"n":5}

-- Arithmetic
SELECT jsonb_path_query('{"price":100}', '$.price * 1.1');
-- 110.0

-- String operations
SELECT jsonb_path_query_array('{"tags":["dog","cat","bird"]}', '$.tags[*] ? (@ starts with "d")');
```

jsonpath in WHERE clause:

```sql
SELECT * FROM products WHERE jsonb_path_exists(data, '$.price ? (@ > 100)');
-- Equivalent to: WHERE (data ->> 'price')::numeric > 100
-- But jsonpath is more powerful for nested structures
```

---

## Common patterns

### Validate JSON structure before insert

```sql
ALTER TABLE configs ADD CONSTRAINT valid_schema
  CHECK (jsonb_typeof(settings) = 'object' AND settings ? 'version');
```

### Aggregate rows into JSON array

```sql
SELECT user_id, jsonb_agg(order_id ORDER BY created_at) AS order_ids
FROM orders
GROUP BY user_id;

SELECT jsonb_object_agg(key, value) FROM kv_table;
```

### Expand JSONB array to rows for JOINs

```sql
SELECT p.id, tag
FROM products p
CROSS JOIN LATERAL jsonb_array_elements_text(p.tags) AS tag
WHERE tag = 'sale';
```

### Store and query flexible attributes

```sql
CREATE TABLE products (
  id bigint PRIMARY KEY,
  name text NOT NULL,
  attributes jsonb NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_products_attrs ON products USING GIN (attributes);

-- Query by any attribute:
SELECT * FROM products WHERE attributes @> '{"color":"red","size":"M"}';
-- Add new attribute without schema change:
UPDATE products SET attributes = attributes || '{"material":"cotton"}' WHERE id = 1;
```

### Upsert into JSONB key

```sql
-- Atomic "set if not exists"
UPDATE users
SET metadata = jsonb_set(metadata, '{onboarding_completed}', 'true', true)
WHERE id = $1 AND NOT (metadata ? 'onboarding_completed');
```
