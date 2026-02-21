# Relations & Relational Query API (v2)

## Table of Contents

- [Defining Relations](#defining-relations)
- [Relational Query API](#relational-query-api)
- [Where Filters](#where-filters)
- [Columns, OrderBy, Limit](#columns-orderby-limit)
- [Filtering by Relations](#filtering-by-relations)

## Defining Relations

Relations are defined separately from tables using `defineRelations()`. They do NOT create foreign keys in the database — they are purely for the relational query API.

### Setup

```typescript
// schema.ts — tables only
import { pgTable, serial, text, integer } from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
});

export const posts = pgTable("posts", {
  id: serial("id").primaryKey(),
  title: text("title").notNull(),
  authorId: integer("author_id")
    .notNull()
    .references(() => users.id),
});

// relations.ts
import { defineRelations } from "drizzle-orm";
import * as schema from "./schema";

export const relations = defineRelations(schema, (r) => ({
  users: {
    posts: r.many.posts({
      from: r.users.id,
      to: r.posts.authorId,
    }),
  },
  posts: {
    author: r.one.users({
      from: r.posts.authorId,
      to: r.users.id,
    }),
  },
}));
```

### One-to-One

```typescript
export const relations = defineRelations(schema, (r) => ({
  users: {
    profile: r.one.profiles({
      from: r.users.id,
      to: r.profiles.userId,
    }),
  },
  profiles: {
    user: r.one.users({
      from: r.profiles.userId,
      to: r.users.id,
    }),
  },
}));
```

### One-to-Many

```typescript
export const relations = defineRelations(schema, (r) => ({
  users: {
    posts: r.many.posts({
      from: r.users.id,
      to: r.posts.authorId,
    }),
  },
  posts: {
    author: r.one.users({
      from: r.posts.authorId,
      to: r.users.id,
    }),
  },
}));
```

### Many-to-Many (through junction table)

```typescript
export const users = pgTable("users", { id: serial("id").primaryKey() });
export const groups = pgTable("groups", { id: serial("id").primaryKey() });
export const usersToGroups = pgTable(
  "users_to_groups",
  {
    userId: integer("user_id")
      .notNull()
      .references(() => users.id),
    groupId: integer("group_id")
      .notNull()
      .references(() => groups.id),
  },
  (t) => [primaryKey({ columns: [t.userId, t.groupId] })],
);

export const relations = defineRelations(schema, (r) => ({
  users: {
    groups: r.many.groups({
      from: r.users.id.through(r.usersToGroups.userId),
      to: r.groups.id.through(r.usersToGroups.groupId),
    }),
  },
  groups: {
    users: r.many.users({
      from: r.groups.id.through(r.usersToGroups.groupId),
      to: r.users.id.through(r.usersToGroups.userId),
    }),
  },
}));
```

### Required relations (optional: false)

```typescript
users: {
  posts: r.many.posts({
    from: r.users.id,
    to: r.posts.authorId,
    optional: false,  // makes the relation required at type level
  }),
},
```

### Predefined filters on relations

```typescript
groups: {
  verifiedUsers: r.many.users({
    from: r.groups.id.through(r.usersToGroups.groupId),
    to: r.users.id.through(r.usersToGroups.userId),
    where: { verified: true },
  }),
},
```

## Relational Query API

Pass schema + relations to `drizzle()`:

```typescript
import { drizzle } from "drizzle-orm/node-postgres";
import * as schema from "./schema";
import { relations } from "./relations";

const db = drizzle(process.env.DATABASE_URL, { schema, relations });
```

### findMany / findFirst

```typescript
// All users
const users = await db.query.users.findMany();

// First match
const user = await db.query.users.findFirst({
  where: { id: 1 },
});

// With nested relations
const usersWithPosts = await db.query.users.findMany({
  with: {
    posts: {
      with: {
        comments: true,
      },
    },
  },
});
```

## Where Filters

### Object-based (v2)

```typescript
// Simple equality
where: { id: 1 }

// Multiple = implicit AND
where: { age: 18, role: "admin" }

// Operators
where: { age: { gt: 18 } }
where: { name: { like: "Dan%" } }
where: { name: { ilike: "%dan%" } }     // case-insensitive
where: { id: { gte: 10, lte: 100 } }    // BETWEEN via AND

// Explicit AND/OR/NOT
where: { AND: [{ age: { gt: 18 } }, { role: "admin" }] }
where: { OR: [{ role: "admin" }, { role: "mod" }] }
where: { NOT: { role: "banned" } }

// Raw SQL
where: { RAW: (table) => sql`${table.name} ~* 'pattern'` }
```

### Available operators

`eq` (default), `ne`, `gt`, `gte`, `lt`, `lte`, `like`, `ilike`, `notLike`, `notIlike`, `inArray`, `notInArray`, `isNull`, `isNotNull`, `between`, `notBetween`

## Columns, OrderBy, Limit

### Select specific columns

```typescript
await db.query.users.findMany({
  columns: {
    id: true,
    name: true,
    // password: false  (omit or set false to exclude)
  },
  with: {
    posts: {
      columns: { id: true, title: true },
    },
  },
});
```

### OrderBy

```typescript
await db.query.users.findMany({
  orderBy: { createdAt: "desc" },
});
```

### Limit / Offset (including nested)

```typescript
await db.query.posts.findMany({
  limit: 10,
  offset: 20,
  with: {
    comments: {
      limit: 5,
      offset: 0,
    },
  },
});
```

## Filtering by Relations

Query users that have posts matching a condition:

```typescript
const usersWithMatchingPosts = await db.query.users.findMany({
  where: {
    id: { gt: 10 },
    posts: {
      content: { like: "Drizzle%" },
    },
  },
});
```

This generates a subquery/EXISTS condition — only users with at least one matching post are returned.
