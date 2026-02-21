# PostgreSQL Schema Reference

## Table of Contents

- [Column Types](#column-types)
- [Column Modifiers](#column-modifiers)
- [Enums](#enums)
- [Indexes](#indexes)
- [Constraints](#constraints)
- [Foreign Keys](#foreign-keys)
- [PostGIS](#postgis)
- [pg_vector](#pg_vector)

## Column Types

All imports from `drizzle-orm/pg-core`.

### Integer types

```typescript
integer("age"); // 4-byte signed integer
smallint("small"); // 2-byte integer
bigint("big", { mode: "number" }); // 8-byte; mode: "number" | "bigint"
serial("id"); // auto-increment 4-byte (NOT NULL by default)
smallserial("small_id"); // auto-increment 2-byte
bigserial("big_id", { mode: "number" }); // auto-increment 8-byte
```

### Text types

```typescript
text("bio"); // unlimited length
text("role", { enum: ["admin", "user"] }); // text with enum check
varchar("name", { length: 256 }); // variable length
char("code", { length: 3 }); // fixed length
```

### Numeric types

```typescript
numeric("price", { precision: 10, scale: 2 }); // exact; mode: "string" (default) | "number" | "bigint"
real("score"); // float4
doublePrecision("precise"); // float8
```

### JSON types

```typescript
json("data"); // textual JSON
jsonb("metadata"); // binary JSON (preferred for queries)
// Type-safe:
jsonb("config").$type<{ theme: string; lang: string }>();
```

### Date/time types

```typescript
timestamp("created_at", { withTimezone: true, mode: "date" }); // mode: "date" | "string"
timestamp("updated_at", { precision: 3, withTimezone: true }).defaultNow();
date("birth_date", { mode: "date" }); // mode: "date" | "string"
time("start_time", { precision: 0 });
interval("duration", { fields: "day" });
```

### Special types

```typescript
uuid("id").defaultRandom(); // UUID v4 default
boolean("active");
bytea("file_data"); // binary
point("location", { mode: "xy" }); // { x: number, y: number } or mode: "tuple" for [number, number]
line("path", { mode: "abc" }); // { a, b, c } or mode: "tuple"
```

### Identity columns (PG 10+)

```typescript
integer("id").generatedAlwaysAsIdentity({ startWith: 1000 });
integer("id").generatedByDefaultAsIdentity(); // allows manual override
```

## Column Modifiers

```typescript
column
  .notNull() // NOT NULL
  .primaryKey() // PRIMARY KEY
  .default(42) // static default
  .default(sql`gen_random_uuid()`) // SQL-level default
  .defaultNow() // timestamp shortcut: default now()
  .defaultRandom() // UUID shortcut: default gen_random_uuid()
  .$defaultFn(() => cuid2()) // runtime JS default (insert-time)
  .$onUpdateFn(() => new Date()) // runtime JS default (update-time)
  .$type<MyType>() // override TS type (compile-time only)
  .references(() => otherTable.id) // inline foreign key
  .unique(); // UNIQUE constraint
```

## Enums

```typescript
import { pgEnum } from "drizzle-orm/pg-core";

export const roleEnum = pgEnum("role", ["admin", "user", "moderator"]);

// Use in table:
export const users = pgTable("users", {
  role: roleEnum().default("user").notNull(),
});
```

## Indexes

Defined in pgTable's third argument (callback returning array):

```typescript
import { pgTable, index, uniqueIndex } from "drizzle-orm/pg-core";

export const users = pgTable(
  "users",
  {
    id: serial("id").primaryKey(),
    email: text("email").notNull(),
    name: text("name"),
    age: integer("age"),
  },
  (t) => [
    // Single column
    index("name_idx").on(t.name),

    // Composite
    index("name_age_idx").on(t.name, t.age),

    // Unique index
    uniqueIndex("email_idx").on(t.email),

    // Partial index
    index("active_idx")
      .on(t.id)
      .where(sql`${t.age} >= 18`),

    // Expression index with btree
    index("lower_name_idx").using("btree", sql`lower(${t.name})`),

    // Advanced sorting
    index("sorted_idx")
      .on(t.name.asc(), t.age.desc().nullsFirst())
      .concurrently()
      .with({ fillfactor: "70" }),

    // GiST index (for PostGIS/pg_vector)
    index("geo_idx").using("gist", t.location),

    // HNSW index (for pg_vector)
    index("embedding_idx").using("hnsw", t.embedding.op("vector_cosine_ops")),
  ],
);
```

## Constraints

```typescript
import { pgTable, unique, check, primaryKey, foreignKey } from "drizzle-orm/pg-core";

export const table = pgTable(
  "table",
  {
    id: serial("id").primaryKey(),
    email: text("email").notNull().unique(),
    age: integer("age"),
    firstName: text("first_name"),
    lastName: text("last_name"),
  },
  (t) => [
    // Composite unique
    unique("name_unique").on(t.firstName, t.lastName),

    // Unique with NULLS NOT DISTINCT (PG 15+)
    unique("email_unique").on(t.email).nullsNotDistinct(),

    // Check constraint
    check("age_positive", sql`${t.age} >= 0`),

    // Composite primary key
    primaryKey({ columns: [t.firstName, t.lastName] }),
  ],
);
```

## Foreign Keys

### Inline (single column)

```typescript
integer("author_id").references(() => users.id);
integer("author_id").references(() => users.id, { onDelete: "cascade", onUpdate: "cascade" });
```

### Self-reference (requires AnyPgColumn)

```typescript
import type { AnyPgColumn } from "drizzle-orm/pg-core";

integer("parent_id").references((): AnyPgColumn => categories.id);
```

### Multi-column (in third argument)

```typescript
pgTable("profile", { firstName, lastName }, (t) => [
  foreignKey({
    columns: [t.firstName, t.lastName],
    foreignColumns: [users.firstName, users.lastName],
    name: "profile_user_fk",
  })
    .onDelete("cascade")
    .onUpdate("cascade"),
]);
```

### onDelete/onUpdate values

`"cascade"` | `"restrict"` | `"no action"` | `"set null"` | `"set default"`

## PostGIS

```typescript
import { geometry } from "drizzle-orm/pg-core";

const places = pgTable("places", {
  location: geometry("location", { type: "point", mode: "xy", srid: 4326 }),
  // mode: "xy" → { x: number, y: number }
  // mode: "tuple" → [number, number]
});

// GiST index for spatial queries
pgTable("places", { location }, (t) => [index("geo_idx").using("gist", t.location)]);
```

## pg_vector

```typescript
import { vector } from "drizzle-orm/pg-core";
import { l2Distance, cosineDistance, innerProduct } from "drizzle-orm";

const items = pgTable(
  "items",
  {
    embedding: vector("embedding", { dimensions: 1536 }),
  },
  (t) => [index("embedding_idx").using("hnsw", t.embedding.op("vector_cosine_ops"))],
);

// Similarity search
await db.select().from(items).orderBy(cosineDistance(items.embedding, queryVector)).limit(10);
```
