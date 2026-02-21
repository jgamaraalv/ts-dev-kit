# Queries Reference (SQL-like API)

## Table of Contents

- [Select](#select)
- [Insert](#insert)
- [Update](#update)
- [Delete](#delete)
- [Joins](#joins)
- [Filters (operators)](#filters)

## Select

### Basic

```typescript
// All columns
await db.select().from(users);

// Partial select (flat result)
await db.select({ id: users.id, name: users.name }).from(users);

// With SQL expression
await db
  .select({
    id: users.id,
    lowerName: sql<string>`lower(${users.name})`.as("lower_name"),
  })
  .from(users);
```

### Where, orderBy, limit, offset

```typescript
await db.select().from(users)
  .where(eq(users.id, 42))
  .orderBy(asc(users.name))
  .limit(10)
  .offset(20);

// Multiple order columns
.orderBy(desc(users.createdAt), asc(users.name))
```

### Conditional where (composable)

```typescript
async function getProducts({ name, category, maxPrice }: Filters) {
  const filters: SQL[] = [];
  if (name) filters.push(ilike(products.name, `%${name}%`));
  if (category) filters.push(eq(products.category, category));
  if (maxPrice) filters.push(lte(products.price, maxPrice));

  return db
    .select()
    .from(products)
    .where(and(...filters));
}
```

### Subqueries

```typescript
const subquery = db
  .select({ avgPrice: sql<number>`avg(${products.price})`.as("avg_price") })
  .from(products)
  .as("sub");

await db.select().from(subquery);
```

### WITH (CTEs)

```typescript
const topUsers = db.$with("top_users").as(db.select().from(users).where(gt(users.score, 100)));

await db.with(topUsers).select().from(topUsers);
```

### Distinct

```typescript
await db.selectDistinct().from(users);
await db.selectDistinctOn([users.name]).from(users); // PG-specific
```

### Aggregations

```typescript
await db
  .select({
    category: products.category,
    count: sql<number>`count(*)`.mapWith(Number),
    avgPrice: sql<number>`avg(${products.price})`.mapWith(Number),
  })
  .from(products)
  .groupBy(products.category)
  .having(sql`count(*) > 5`);
```

### Prepared statements

```typescript
const prepared = db
  .select()
  .from(users)
  .where(eq(users.id, sql.placeholder("id")))
  .prepare("get_user");

await prepared.execute({ id: 42 });
```

## Insert

### Batch insert

```typescript
await db.insert(users).values([
  { name: "Dan", email: "dan@example.com" },
  { name: "Andrew", email: "andrew@example.com" },
]);
```

### Returning

```typescript
const [inserted] = await db.insert(users).values({ name: "Dan" }).returning(); // all columns

const [{ id }] = await db.insert(users).values({ name: "Dan" }).returning({ id: users.id }); // partial
```

### Upsert (on conflict)

```typescript
// Do nothing
await db.insert(users).values({ id: 1, name: "Dan" }).onConflictDoNothing();
await db.insert(users).values({ id: 1, name: "Dan" }).onConflictDoNothing({ target: users.id });

// Do update
await db
  .insert(users)
  .values({ id: 1, name: "Dan" })
  .onConflictDoUpdate({
    target: users.id,
    set: { name: "Dan Updated" },
  });

// Composite target
await db
  .insert(users)
  .values({ firstName: "Dan", lastName: "Smith" })
  .onConflictDoUpdate({
    target: [users.firstName, users.lastName],
    set: { name: sql`excluded.first_name || ' ' || excluded.last_name` },
  });

// With where on set (conditional upsert)
await db
  .insert(users)
  .values({ id: 1, name: "Dan" })
  .onConflictDoUpdate({
    target: users.id,
    set: { name: "Dan" },
    setWhere: sql`${users.updatedAt} < now() - interval '1 day'`,
  });
```

### Insert from select

```typescript
await db.insert(archive).select(db.select().from(users).where(lt(users.createdAt, cutoffDate)));
```

## Update

### With SQL expressions

```typescript
await db.update(users).set({ name: "Dan Updated" }).where(eq(users.id, 1));

const [updated] = await db.update(users).set({ name: "Dan" }).where(eq(users.id, 1)).returning();

await db
  .update(products)
  .set({ price: sql`${products.price} * 1.1` })
  .where(eq(products.category, "electronics"));

// Increment
await db
  .update(users)
  .set({ viewCount: sql`${users.viewCount} + 1` })
  .where(eq(users.id, 1));
```

## Delete

```typescript
await db.delete(users).where(eq(users.id, 1));

// With returning
const [deleted] = await db.delete(users).where(eq(users.id, 1)).returning();

// With limit + orderBy
await db.delete(logs).where(lt(logs.createdAt, cutoff)).orderBy(asc(logs.createdAt)).limit(1000);
```

### With CTE

```typescript
const avgAmount = db
  .$with("avg_amount")
  .as(db.select({ value: sql`avg(${orders.amount})`.as("value") }).from(orders));

await db
  .with(avgAmount)
  .delete(orders)
  .where(gt(orders.amount, sql`(select * from ${avgAmount})`));
```

## Joins

### Join types

```typescript
// LEFT JOIN -- right table nullable
db.select().from(users).leftJoin(posts, eq(users.id, posts.authorId));
// -> { users: User; posts: Post | null }[]

// RIGHT JOIN -- left table nullable
db.select().from(users).rightJoin(posts, eq(users.id, posts.authorId));

// INNER JOIN -- neither nullable
db.select().from(users).innerJoin(posts, eq(users.id, posts.authorId));

// FULL JOIN -- both nullable
db.select().from(users).fullJoin(posts, eq(users.id, posts.authorId));

// CROSS JOIN -- no condition
db.select().from(users).crossJoin(posts);

// LATERAL joins (correlated subqueries)
const sq = db.select().from(posts).where(eq(posts.authorId, users.id)).as("user_posts");
db.select()
  .from(users)
  .leftJoinLateral(sq, sql`true`);
```

### Partial select (flatten)

```typescript
const result = await db
  .select({
    userId: users.id,
    userName: users.name,
    postTitle: posts.title,
  })
  .from(users)
  .leftJoin(posts, eq(users.id, posts.authorId));
// -> { userId: number; userName: string; postTitle: string | null }[]
```

### Table aliases (self-join)

```typescript
import { alias } from "drizzle-orm/pg-core";

const parent = alias(users, "parent");
await db.select().from(users).leftJoin(parent, eq(parent.id, users.parentId));
```

### Many-to-many via junction

```typescript
await db
  .select()
  .from(usersToGroups)
  .leftJoin(users, eq(usersToGroups.userId, users.id))
  .leftJoin(groups, eq(usersToGroups.groupId, groups.id))
  .where(eq(groups.id, 1));
```

### Post-query aggregation (manual)

Drizzle returns flat rows -- aggregate one-to-many manually:

```typescript
const rows = await db
  .select({ user: users, pet: pets })
  .from(users)
  .leftJoin(pets, eq(users.id, pets.ownerId));

const result = rows.reduce<Record<number, { user: User; pets: Pet[] }>>((acc, row) => {
  if (!acc[row.user.id]) acc[row.user.id] = { user: row.user, pets: [] };
  if (row.pet) acc[row.user.id].pets.push(row.pet);
  return acc;
}, {});
```

## Filters

All operators imported from `drizzle-orm`:

| Operator                | SQL equivalent    | Example                                              |
| ----------------------- | ----------------- | ---------------------------------------------------- |
| `eq(col, val)`          | `= val`           | `eq(users.id, 1)`                                    |
| `ne(col, val)`          | `!= val`          | `ne(users.id, 1)`                                    |
| `gt(col, val)`          | `> val`           | `gt(users.age, 18)`                                  |
| `gte(col, val)`         | `>= val`          | `gte(users.age, 18)`                                 |
| `lt(col, val)`          | `< val`           | `lt(users.age, 65)`                                  |
| `lte(col, val)`         | `<= val`          | `lte(users.age, 65)`                                 |
| `isNull(col)`           | `IS NULL`         | `isNull(users.deletedAt)`                            |
| `isNotNull(col)`        | `IS NOT NULL`     | `isNotNull(users.email)`                             |
| `inArray(col, vals)`    | `IN (...)`        | `inArray(users.role, ["admin", "mod"])`              |
| `notInArray(col, vals)` | `NOT IN (...)`    | `notInArray(users.role, ["banned"])`                 |
| `between(col, a, b)`    | `BETWEEN a AND b` | `between(users.age, 18, 65)`                         |
| `like(col, pat)`        | `LIKE pat`        | `like(users.name, "%Dan%")`                          |
| `ilike(col, pat)`       | `ILIKE pat`       | `ilike(users.name, "%dan%")`                         |
| `exists(subquery)`      | `EXISTS (...)`    | `exists(db.select().from(posts).where(...))`         |
| `and(...conds)`         | `AND`             | `and(eq(users.role, "admin"), gt(users.age, 21))`    |
| `or(...conds)`          | `OR`              | `or(eq(users.role, "admin"), eq(users.role, "mod"))` |
| `not(cond)`             | `NOT`             | `not(eq(users.role, "admin"))`                       |
