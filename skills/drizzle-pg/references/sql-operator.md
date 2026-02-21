# Magic sql`` Operator Reference

## Table of Contents

- [Basic Usage](#basic-usage)
- [Type Annotations](#type-annotations)
- [sql.raw()](#sqlraw)
- [sql.empty() + append()](#sqlempty--append)
- [sql.join()](#sqljoin)
- [sql.identifier()](#sqlidentifier)
- [Placeholders](#placeholders)
- [Helpers: .as(), .mapWith()](#helpers)
- [Converting to String](#converting-to-string)
- [Usage in Queries](#usage-in-queries)

## Basic Usage

The `sql` template literal auto-parameterizes values and escapes table/column references:

```typescript
import { sql } from "drizzle-orm";

const id = 69;
await db.execute(sql`select * from ${usersTable} where ${usersTable.id} = ${id}`);
// → select * from "users" where "users"."id" = $1;  params: [69]
```

Table/column references (`${usersTable}`, `${usersTable.id}`) are escaped as identifiers.
Scalar values (`${id}`) become parameterized placeholders.

## Type Annotations

Use `sql<T>` to annotate the return type:

```typescript
const result = await db
  .select({
    lowerName: sql<string>`lower(${users.name})`,
    count: sql<number>`count(*)`,
  })
  .from(users);
// result[0].lowerName → string
// result[0].count → number
```

For nullable contexts (e.g., LEFT JOIN), explicitly type as nullable:

```typescript
sql<string | null>`upper(${pets.name})`;
```

## sql.raw()

Insert raw, unescaped SQL (no parameterization). Use for dynamic SQL fragments, not user input:

```typescript
const column = "name";
sql`select ${sql.raw(column)} from users`;
// → select name from users  (no quoting, no $1)

// vs parameterized
sql`select * from users where id = ${12}`;
// → select * from users where id = $1; params: [12]
```

## sql.empty() + append()

Build SQL incrementally:

```typescript
const query = sql.empty();
query.append(sql`select * from users`);
query.append(sql` where `);

const conditions = [sql`id = ${1}`, sql`name = ${"Dan"}`];
for (let i = 0; i < conditions.length; i++) {
  query.append(conditions[i]);
  if (i < conditions.length - 1) query.append(sql` or `);
}
// → select * from users where id = $1 or name = $2; params: [1, "Dan"]
```

## sql.join()

Join an array of SQL chunks with a separator:

```typescript
const conditions: SQL[] = [sql`id = ${1}`, sql`name = ${"Dan"}`, sql`age > ${18}`];

const where = sql.join(conditions, sql` AND `);
const query = sql`select * from users where ${where}`;
// → select * from users where id = $1 AND name = $2 AND age > $3
```

## sql.identifier()

Escape a dynamic identifier (table/column name):

```typescript
const tableName = "users";
sql`SELECT * FROM ${sql.identifier(tableName)}`;
// → SELECT * FROM "users"
```

## Placeholders

Use `sql.placeholder()` for prepared statements:

```typescript
const stmt = db
  .select()
  .from(users)
  .where(eq(users.id, sql.placeholder("userId")))
  .prepare("get_user_by_id");

// Execute with named params
await stmt.execute({ userId: 42 });
```

## Helpers

### .as() — alias a column

```typescript
sql<number>`count(*)`.as("total_count");
// → count(*) AS "total_count"
```

### .mapWith() — transform driver output

```typescript
sql<number>`count(*)`.mapWith(Number);
// Converts string "42" from driver to number 42
```

### .inlineParams() — inline parameters instead of $N

```typescript
sql`select * from users where id = ${42}`.inlineParams();
// → select * from users where id = 42 (no parameterization)
```

## Converting to String

```typescript
import { PgDialect } from "drizzle-orm/pg-core";

const pgDialect = new PgDialect();
const { sql: sqlStr, params } = pgDialect.sqlToQuery(
  sql`select * from ${usersTable} where ${usersTable.id} = ${12}`,
);
// sqlStr: 'select * from "users" where "users"."id" = $1'
// params: [12]
```

## Usage in Queries

### In SELECT

```typescript
await db
  .select({
    id: users.id,
    fullName: sql<string>`${users.firstName} || ' ' || ${users.lastName}`.as("full_name"),
  })
  .from(users);
```

### In WHERE

```typescript
await db
  .select()
  .from(users)
  .where(sql`${users.age} > 18 AND ${users.role} = 'admin'`);

// Full-text search
await db
  .select()
  .from(users)
  .where(sql`to_tsvector('english', ${users.bio}) @@ to_tsquery('english', ${searchTerm})`);
```

### In ORDER BY

```typescript
await db
  .select()
  .from(users)
  .orderBy(sql`${users.id} desc nulls first`);
```

### In GROUP BY / HAVING

```typescript
await db
  .select({
    category: products.category,
    total: sql<number>`sum(${products.price})`.mapWith(Number),
  })
  .from(products)
  .groupBy(sql`${products.category}`)
  .having(sql`sum(${products.price}) > 1000`);
```

### In schema defaults

```typescript
const users = pgTable("users", {
  id: uuid("id")
    .default(sql`gen_random_uuid()`)
    .primaryKey(),
  createdAt: timestamp("created_at").default(sql`now()`),
});
```
