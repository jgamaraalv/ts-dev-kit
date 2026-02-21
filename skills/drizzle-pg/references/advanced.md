# Advanced Features Reference

## Table of Contents

- [Type Inference](#type-inference)
- [Dynamic Query Building](#dynamic-query-building)
- [Transactions](#transactions)
- [Utility Functions](#utility-functions)
- [Logging](#logging)
- [Custom Types](#custom-types)
- [Table Name Prefixing](#table-name-prefixing)
- [Standalone Query Builder](#standalone-query-builder)
- [Zod Integration](#zod-integration)
- [Anti-Patterns](#anti-patterns)

## Type Inference

```typescript
// Infer select/insert types from table definition
type SelectUser = typeof users.$inferSelect;
type InsertUser = typeof users.$inferInsert;

// Alternative with utility types
import type { InferSelectModel, InferInsertModel } from "drizzle-orm";
type SelectUser = InferSelectModel<typeof users>;
type InsertUser = InferInsertModel<typeof users>;
```

## Dynamic Query Building

Use `$dynamic()` to remove the restriction that query methods can only be called once:

```typescript
import type { PgSelect } from "drizzle-orm/pg-core";

function withPagination<T extends PgSelect>(qb: T, page = 1, pageSize = 10) {
  return qb.limit(pageSize).offset((page - 1) * pageSize);
}

function withOrderBy<T extends PgSelect>(qb: T, column: PgColumn, dir: "asc" | "desc" = "asc") {
  return qb.orderBy(dir === "asc" ? asc(column) : desc(column));
}

// Usage
const query = db.select().from(users).where(eq(users.active, true)).$dynamic();
const result = await withPagination(withOrderBy(query, users.createdAt, "desc"), 2, 20);
```

Available types by operation: `PgSelect`, `PgInsert`, `PgUpdate`, `PgDelete`, `PgSelectQueryBuilder`.

## Transactions

```typescript
await db.transaction(async (tx) => {
  const [user] = await tx.insert(users).values({ name: "Dan" }).returning();
  await tx.insert(posts).values({ title: "Hello", authorId: user.id });
});

// Nested savepoints
await db.transaction(async (tx) => {
  await tx.insert(users).values({ name: "Dan" });

  await tx.transaction(async (tx2) => {
    // This is a savepoint
    await tx2.insert(posts).values({ title: "Nested" });
  });
});

// Rollback
await db.transaction(async (tx) => {
  await tx.insert(users).values({ name: "Dan" });
  tx.rollback(); // Rolls back entire transaction
});

// Isolation level
await db.transaction(
  async (tx) => {
    // ...
  },
  {
    isolationLevel: "serializable", // "read uncommitted" | "read committed" | "repeatable read" | "serializable"
  },
);
```

## Utility Functions

### getColumns — extract columns (exclude sensitive fields)

```typescript
import { getColumns } from "drizzle-orm";

const { password, ...publicColumns } = getColumns(users);
await db.select(publicColumns).from(users);
```

### getTableConfig — table metadata

```typescript
import { getTableConfig } from "drizzle-orm/pg-core";

const config = getTableConfig(users);
// config.columns, config.indexes, config.foreignKeys, config.checks, config.primaryKeys, config.name, config.schema
```

### toSQL — inspect generated SQL

```typescript
const query = db.select().from(users).where(eq(users.id, 1)).toSQL();
// { sql: "select ... from \"users\" where \"users\".\"id\" = $1", params: [1] }
```

### db.execute — raw SQL

```typescript
const result = await db.execute(sql`SELECT * FROM users WHERE id = ${userId}`);
```

### is — runtime type checking

```typescript
import { is, Column } from "drizzle-orm";

if (is(value, Column)) {
  // value narrowed to Column type
}
```

## Logging

```typescript
// Built-in logger
const db = drizzle(process.env.DATABASE_URL, { logger: true });

// Custom logger
import type { Logger } from "drizzle-orm";

class MyLogger implements Logger {
  logQuery(query: string, params: unknown[]): void {
    console.log({ query, params });
  }
}

const db = drizzle(process.env.DATABASE_URL, { logger: new MyLogger() });
```

## Custom Types

Define custom column types for special mappings:

```typescript
import { customType } from "drizzle-orm/pg-core";

// Example: monetary type stored as integer cents
const money = customType<{ data: number; driverData: number }>({
  dataType() {
    return "integer";
  },
  fromDriver(value: number): number {
    return value / 100;
  },
  toDriver(value: number): number {
    return Math.round(value * 100);
  },
});

// Usage
const products = pgTable("products", {
  price: money("price_cents").notNull(),
});

// Example: JSONB with typed shape
const typedJsonb = <T>(name: string) =>
  customType<{ data: T; driverData: string }>({
    dataType() {
      return "jsonb";
    },
    toDriver(value: T): string {
      return JSON.stringify(value);
    },
  })(name);

const settings = pgTable("settings", {
  config: typedJsonb<{ theme: string; lang: string }>("config"),
});
```

### customType parameters

```typescript
customType<{
  data: AppType;           // Required — the TS type for select/insert
  driverData: DriverType;  // Type the driver returns
  config: ConfigType;      // Config object shape for dataType()
}>({
  dataType(config): string;          // Returns SQL type string
  toDriver?(value): driverData;     // App → Database
  fromDriver?(value): data;         // Database → App
})
```

## Table Name Prefixing

Useful for multi-project schemas sharing one database:

```typescript
import { pgTableCreator } from "drizzle-orm/pg-core";

const pgTable = pgTableCreator((name) => `myapp_${name}`);

const users = pgTable("users", {
  id: serial("id").primaryKey(),
});
// Creates table "myapp_users" in database
```

## Standalone Query Builder

Build queries without a database connection (for inspection or testing):

```typescript
import { QueryBuilder } from "drizzle-orm/pg-core";

const qb = new QueryBuilder();
const query = qb.select().from(users).where(eq(users.name, "Dan"));
const { sql, params } = query.toSQL();
```

## Zod Integration

Generate Zod schemas from Drizzle tables:

```typescript
import { createInsertSchema, createSelectSchema } from "drizzle-zod";

const insertUserSchema = createInsertSchema(users);
const selectUserSchema = createSelectSchema(users);

// With refinements
const insertUserSchema = createInsertSchema(users, {
  email: (schema) => schema.email(),
  name: (schema) => schema.min(1).max(100),
});

// Usage with Fastify/Express
const parsed = insertUserSchema.parse(req.body);
await db.insert(users).values(parsed);
```

Requires `drizzle-zod` package: `npm i drizzle-zod`

## Anti-Patterns

### Raw SQL with user input (SQL injection risk)

```typescript
// BAD -- string interpolation bypasses parameterization
const name = req.query.name;
await db.execute(sql.raw(`SELECT * FROM users WHERE name = '${name}'`));

// GOOD -- use sql template literal for automatic parameterization
await db.execute(sql`SELECT * FROM users WHERE name = ${name}`);

// GOOD -- use Drizzle operators
await db.select().from(users).where(eq(users.name, name));
```

`sql.raw()` should only be used for trusted, static SQL fragments (column names, table names), never for user-provided values.

### Missing `.returning()` on insert/update/delete

```typescript
// BAD -- no way to get the created record without a second query
await db.insert(users).values({ name: "Dan", email: "dan@ex.com" });
const user = await db.select().from(users).where(eq(users.email, "dan@ex.com"));

// GOOD -- get the result in a single round-trip
const [user] = await db.insert(users).values({ name: "Dan", email: "dan@ex.com" }).returning();
```

Always use `.returning()` when you need the inserted/updated/deleted row. PostgreSQL supports this natively with no performance penalty.

### Mixing relational query API with SQL-like joins

```typescript
// BAD -- cannot use db.query.* (relational API) and then chain .leftJoin()
// The relational API (findMany/findFirst) and SQL-like API (select/from/join) are separate systems
const result = await db.query.users.findMany({
  with: { posts: true },
}); // This returns nested objects

const result2 = await db.select().from(users).leftJoin(posts, eq(users.id, posts.authorId)); // This returns flat rows

// Pick one approach per query:
// - Relational API (db.query.*) for nested/eager loading with `with`
// - SQL-like API (db.select().from()) for joins, aggregations, complex SQL
```

Do not attempt to mix `db.query.*` with `.leftJoin()`, `.innerJoin()`, or other SQL-like methods. They are different query builders with different return shapes.
