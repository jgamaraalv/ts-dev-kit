---
name: typescript-conventions
description: "TypeScript coding conventions for strict, type-safe projects. Use when: (1) writing or reviewing TypeScript code, (2) choosing between `any` and `unknown`, (3) structuring imports with verbatimModuleSyntax, (4) defining types, interfaces, unions, or generics, (5) naming functions, booleans, queries, and commands, (6) handling errors with guard clauses and early returns, (7) narrowing types with guards and discriminated unions, or (8) avoiding common anti-patterns like primitive obsession, magic strings, and premature abstraction."
---

# TypeScript Conventions

Project-wide TypeScript standards that complement agent-specific instructions.

<rules>

## Type Safety

- **No `any`**: Use `unknown` if the type is truly dynamic, then narrow.
- **Strict config**: `strict: true`, `noUncheckedIndexedAccess`, `verbatimModuleSyntax`.
- Use `Readonly<T>`, `Pick`, `Omit`, and `Record` for precise types.
- Use branded types for entity IDs (e.g., `UserId`, `OrderId`) to prevent mixing.
- Prefer `z.infer<typeof schema>` over hand-written types when a Zod schema exists.

## Interface vs Type

- **Interfaces** for object shapes that may grow — they support `extends` and declaration merging.
- **Type aliases** for unions, intersections, mapped types, and complex compositions.
- Simple rule: `interface` for plain objects, `type` for everything else.

```typescript
// Interface: object shape, extensible
interface User {
  id: string;
  name: string;
}

interface Employee extends User {
  company: string;
}

// Type: union, intersection, computed
type Result = Success | Failure;
type UserProfile = User & { bio: string };
type Nullable<T> = { [K in keyof T]: T[K] | null };
```

## Unions and Literal Types

- **Prefer literal unions over enums** — zero runtime cost, better tree-shaking, full autocomplete.
- Use enums only when you need a runtime object (iteration, reverse lookup).

```typescript
// Prefer this
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";
type Direction = "north" | "south" | "east" | "west";

// Over this (emits runtime JS)
enum HttpMethod { GET, POST, PUT, DELETE }
```

## Discriminated Unions

Add a `type` (or `kind`) literal field to each variant. Always handle exhaustiveness with `assertNever`.

```typescript
interface Circle { type: "circle"; radius: number }
interface Square { type: "square"; side: number }
interface Triangle { type: "triangle"; base: number; height: number }

type Shape = Circle | Square | Triangle;

function assertNever(x: never): never {
  throw new Error(`Unexpected value: ${x}`);
}

function area(shape: Shape): number {
  switch (shape.type) {
    case "circle": return Math.PI * shape.radius ** 2;
    case "square": return shape.side ** 2;
    case "triangle": return (shape.base * shape.height) / 2;
    default: return assertNever(shape);
  }
}
```

## Type Narrowing

Always narrow before accessing type-specific properties.

- `typeof` for primitives: `typeof x === "string"`
- `in` for object shapes: `"swim" in pet`
- Custom type guards for reusable checks: `function isBook(item): item is Book`

```typescript
function format(input: string | number): string {
  if (typeof input === "string") return input.toUpperCase();
  return input.toFixed(2);
}

// Custom type guard
function isError(result: Result): result is ErrorResult {
  return result.success === false;
}
```

## Generics

- Constrain with `extends` — never assume properties exist on unconstrained `T`.
- Use defaults (`T = unknown`) when callers often use a single type.
- Keep generics to one or two parameters; more suggests the function is too broad.

```typescript
// Constrained generic
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// With default
type ApiResponse<T = unknown> = { data: T; status: number };
```

## Mapped & Template Literal Types

Use mapped types to derive variants from a base — never duplicate type definitions.

```typescript
// All fields optional (equivalent to built-in Partial<T>)
type Optional<T> = { [K in keyof T]?: T[K] };

// All fields nullable
type Nullable<T> = { [K in keyof T]: T[K] | null };

// Key remapping with template literals
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};
```

## Intersection Types

- Use `&` to compose smaller interfaces into richer types.
- If two intersected types define the same key with incompatible types, the result collapses to `never` — check for this.

```typescript
type Timestamped = { createdAt: Date; updatedAt: Date };
type UserRecord = User & Timestamped;
```

## Imports

```typescript
// Type-only imports (required by verbatimModuleSyntax)
import type { FastifyInstance } from "fastify";

// Mixed imports: separate values and types
import { z } from "zod/v4";
import type { ZodType } from "zod/v4";

// ioredis: always named import
import { Redis } from "ioredis";
```

## Error Handling

- Handle errors at the beginning of functions with early returns / guard clauses.
- Avoid deep nesting — use if-return pattern instead of else chains.
- In Fastify routes, throw `httpErrors` or use `reply.status().send()` — the centralized `setErrorHandler` formats the response.
- Custom error classes for domain-specific errors (e.g., `NotFoundError`, `ConflictError`).

## Naming

- **Functions**: `getUserById`, `createReport`, `isActive`, `hasPermission`
- **Booleans**: `is/has/can/should` prefix
- **Query** (returns data): `get`, `find`, `list`, `fetch`
- **Command** (changes state): `create`, `update`, `delete`, `add`, `remove`

</rules>

<anti_patterns>

## Anti-Patterns

- **Primitive obsession**: Use branded types or Zod enums, not raw strings for IDs and statuses.
- **Magic numbers/strings**: Use constants from a shared package (e.g., `RATE_LIMITS`, `PAGINATION`, `CACHE`).
- **Long parameter lists**: Use an options object or a Zod schema.
- **Premature abstraction**: Three similar lines > one premature helper. Abstract on the third repetition.
- **Using union values without narrowing**: Accessing `.length` on `string | number` fails at runtime if it's a number.
- **Unions too broad**: A dozen options may suggest generics or a different pattern.
- **`readonly` is shallow**: `readonly` prevents reassignment but doesn't freeze nested objects.
- **Enums for simple sets**: Prefer literal unions when you don't need runtime iteration.
- **Unconstrained generics**: `<T>` with no `extends` loses type info — constrain or use a concrete type.
- **Conflicting intersections**: `{ status: string } & { status: number }` silently collapses to `never`.
- **Forgetting exhaustiveness**: Always add a `default: return assertNever(x)` in discriminated union switches.

</anti_patterns>
