# Drizzle Kit & Migrations Reference

## Table of Contents

- [Commands Overview](#commands-overview)
- [drizzle.config.ts](#drizzleconfigts)
- [Workflow: Code-First](#workflow-code-first)
- [Workflow: Direct Push](#workflow-direct-push)
- [Programmatic Migrations](#programmatic-migrations)
- [Custom Migrations](#custom-migrations)
- [CLI Flags](#cli-flags)

## Commands Overview

| Command                    | Purpose                                       |
| -------------------------- | --------------------------------------------- |
| `npx drizzle-kit generate` | Generate SQL migration files from schema diff |
| `npx drizzle-kit migrate`  | Apply pending SQL migrations to database      |
| `npx drizzle-kit push`     | Push schema directly to DB (no SQL files)     |
| `npx drizzle-kit pull`     | Introspect DB and generate Drizzle schema     |
| `npx drizzle-kit check`    | Check migrations for race conditions          |
| `npx drizzle-kit up`       | Upgrade migration snapshots to latest format  |
| `npx drizzle-kit studio`   | Open Drizzle Studio UI (browser)              |

## drizzle.config.ts

### Minimal (PostgreSQL)

```typescript
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  dialect: "postgresql",
  schema: "./src/db/schema.ts",
});
```

### Full options

```typescript
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  // Required
  dialect: "postgresql", // "postgresql" | "mysql" | "sqlite" | "turso" | "singlestore" | "mssql" | "cockroachdb"
  schema: "./src/db/schema.ts", // string | string[] — glob patterns supported

  // Migration output
  out: "./drizzle", // default: "./drizzle"
  breakpoints: true, // add statement breakpoints in SQL

  // Database connection (for migrate/push/pull/studio)
  dbCredentials: {
    url: process.env.DATABASE_URL!,
    // or individual fields:
    // host: "localhost", port: 5432, user: "postgres", password: "pass", database: "mydb", ssl: true
  },

  // Migration tracking table
  migrations: {
    table: "__drizzle_migrations", // default
    schema: "drizzle", // default (PG schema)
  },

  // Filtering
  tablesFilter: ["*"], // include specific tables: ["users", "posts"]
  schemaFilter: ["public"], // PG schemas to include
  extensionsFilters: ["postgis"], // skip extension-managed tables

  // Introspection (pull)
  introspect: {
    casing: "camel", // "camel" (default) | "preserve"
  },

  // Push behavior
  strict: false, // require approval before executing
  verbose: true, // print SQL before execution

  // Roles (PG-specific)
  entities: {
    roles: false, // true | false | { provider: "neon" | "supabase", include/exclude: [...] }
  },
});
```

### Environment variables pattern

```typescript
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  dialect: "postgresql",
  schema: "./src/db/schema.ts",
  out: "./drizzle",
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
```

### Multiple schema files

```typescript
schema: "./src/db/schema/*.ts"; // glob
schema: ["./src/db/users.ts", "./src/db/posts.ts"]; // explicit array
```

## Workflow: Code-First

Best for production, team collaboration, and audit trails.

```
1. Edit TypeScript schema
2. npx drizzle-kit generate          → creates timestamped SQL in ./drizzle/
3. Review generated .sql files
4. npx drizzle-kit migrate           → applies to database
```

Output structure:

```
drizzle/
├── 0000_init.sql
├── 0001_add_posts.sql
├── meta/
│   ├── 0000_snapshot.json
│   ├── 0001_snapshot.json
│   └── _journal.json
```

Applied migrations tracked in `__drizzle_migrations` table.

### Programmatic migrate

```typescript
import { drizzle } from "drizzle-orm/node-postgres";
import { migrate } from "drizzle-orm/node-postgres/migrator";

const db = drizzle(process.env.DATABASE_URL);

await migrate(db, { migrationsFolder: "./drizzle" });
```

## Workflow: Direct Push

Best for rapid prototyping, local dev, serverless databases.

```
1. Edit TypeScript schema
2. npx drizzle-kit push              → diffs and applies directly
```

No SQL files generated. Use `--strict` for approval prompts, `--force` to auto-accept data-loss.

## Custom Migrations

Generate empty migration for manual SQL (seeding, unsupported DDL):

```bash
npx drizzle-kit generate --custom --name=seed-users
```

Creates empty `.sql` file to fill in:

```sql
-- Custom migration: seed-users
INSERT INTO "users" ("name", "email") VALUES ('Dan', 'dan@example.com');
INSERT INTO "users" ("name", "email") VALUES ('Andrew', 'andrew@example.com');
```

## CLI Flags

### generate

```
--name=<name>         Custom migration name
--custom              Generate empty SQL for manual migration
--config=<path>       Config file path (default: drizzle.config.ts)
```

### migrate

```
--config=<path>       Config file path
```

### push

```
--strict              Require approval before executing SQL
--verbose             Print all SQL before execution
--force               Auto-accept data-loss statements
--config=<path>       Config file path
```

### pull

```
--config=<path>       Config file path
```

### studio

```
--port=<number>       Studio port (default: 4983)
--host=<string>       Studio host (default: localhost)
--config=<path>       Config file path
```

### Global

```
--config=<path>       Path to drizzle.config.ts (works with all commands)
```
