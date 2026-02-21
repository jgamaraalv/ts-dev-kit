# Server-Side Performance

Optimize RSC data fetching, caching, and serialization.

## Table of Contents

- [Use after() for Non-Blocking Operations](#use-after-for-non-blocking-operations)
- [Authenticate Server Actions](#authenticate-server-actions)
- [Cross-Request LRU Caching](#cross-request-lru-caching)
- [Per-Request Deduplication with React.cache()](#per-request-deduplication-with-reactcache)
- [Avoid Duplicate Serialization in RSC Props](#avoid-duplicate-serialization-in-rsc-props)
- [Parallel Data Fetching with Component Composition](#parallel-data-fetching-with-component-composition)
- [Minimize Serialization at RSC Boundaries](#minimize-serialization-at-rsc-boundaries)

---

## Use after() for Non-Blocking Operations

Use Next.js's `after()` to schedule work that should execute after a response is sent. Prevents logging, analytics, and other side effects from blocking the response.

**Incorrect (blocks response):**

```tsx
export async function POST(request: Request) {
  await updateDatabase(request);
  const userAgent = request.headers.get("user-agent") || "unknown";
  await logUserAction({ userAgent }); // Blocks response
  return new Response(JSON.stringify({ status: "success" }));
}
```

**Correct (non-blocking):**

```tsx
import { after } from "next/server";
import { headers, cookies } from "next/headers";

export async function POST(request: Request) {
  await updateDatabase(request);

  after(async () => {
    const userAgent = (await headers()).get("user-agent") || "unknown";
    const sessionCookie = (await cookies()).get("session-id")?.value || "anonymous";
    logUserAction({ sessionCookie, userAgent });
  });

  return new Response(JSON.stringify({ status: "success" }));
}
```

Common use cases: analytics tracking, audit logging, notifications, cache invalidation.

`after()` runs even if the response fails or redirects. Works in Server Actions, Route Handlers, and Server Components.

Reference: [next/server after()](https://nextjs.org/docs/app/api-reference/functions/after)

---

## Authenticate Server Actions

Server Actions (`"use server"`) are exposed as public endpoints. Always verify authentication and authorization **inside** each Server Action -- do not rely solely on middleware or layout guards.

**Incorrect (no authentication check):**

```typescript
"use server";

export async function deleteUser(userId: string) {
  await db.user.delete({ where: { id: userId } });
  return { success: true };
}
```

**Correct (authentication + authorization + validation):**

```typescript
"use server";

import { verifySession } from "@/lib/auth";
import { z } from "zod";

const updateProfileSchema = z.object({
  userId: z.string().uuid(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
});

export async function updateProfile(data: unknown) {
  const validated = updateProfileSchema.parse(data);
  const session = await verifySession();
  if (!session) throw new Error("Unauthorized");
  if (session.user.id !== validated.userId) throw new Error("Can only update own profile");

  await db.user.update({
    where: { id: validated.userId },
    data: { name: validated.name, email: validated.email },
  });

  return { success: true };
}
```

Reference: [Next.js Authentication Guide](https://nextjs.org/docs/app/guides/authentication)

---

## Cross-Request LRU Caching

`React.cache()` only works within one request. For data shared across sequential requests, use an LRU cache.

```typescript
import { LRUCache } from "lru-cache";

const cache = new LRUCache<string, any>({
  max: 1000,
  ttl: 5 * 60 * 1000, // 5 minutes
});

export async function getUser(id: string) {
  const cached = cache.get(id);
  if (cached) return cached;

  const user = await db.user.findUnique({ where: { id } });
  cache.set(id, user);
  return user;
}
```

With Vercel's [Fluid Compute](https://vercel.com/docs/fluid-compute), LRU caching is especially effective because multiple concurrent requests share the same function instance. In traditional serverless, consider Redis for cross-process caching.

Reference: [node-lru-cache](https://github.com/isaacs/node-lru-cache)

---

## Per-Request Deduplication with React.cache()

Use `React.cache()` for server-side request deduplication. Authentication and database queries benefit most.

```typescript
import { cache } from "react";

export const getCurrentUser = cache(async () => {
  const session = await auth();
  if (!session?.user?.id) return null;
  return await db.user.findUnique({ where: { id: session.user.id } });
});
```

**Avoid inline objects as arguments** -- `React.cache()` uses `Object.is` equality. Inline objects always create new references, causing cache misses.

```typescript
// Incorrect (always cache miss)
const getUser = cache(async (params: { uid: number }) => {
  /* ... */
});
getUser({ uid: 1 });
getUser({ uid: 1 }); // Miss -- new object reference

// Correct (cache hit)
const getUser = cache(async (uid: number) => {
  /* ... */
});
getUser(1);
getUser(1); // Hit -- same primitive value
```

**Next.js note:** `fetch` is automatically deduplicated within a single request. `React.cache()` is still essential for database queries, auth checks, heavy computations, and any non-fetch async work.

Reference: [React.cache documentation](https://react.dev/reference/react/cache)

---

## Avoid Duplicate Serialization in RSC Props

RSC-to-client serialization deduplicates by object reference, not value. Same reference = serialized once; new reference = serialized again. Do transformations in the client, not server.

**Incorrect (duplicates array):**

```tsx
// RSC: sends 6 strings (2 arrays x 3 items)
<ClientList usernames={usernames} usernamesOrdered={usernames.toSorted()} />
```

**Correct (sends 3 strings):**

```tsx
// RSC: send once
<ClientList usernames={usernames} />;

// Client: transform there
("use client");
const sorted = useMemo(() => [...usernames].sort(), [usernames]);
```

Operations that break deduplication (create new references): `.toSorted()`, `.filter()`, `.map()`, `.slice()`, `[...arr]`, `{...obj}`, `structuredClone()`.

**Exception:** Pass derived data when transformation is expensive or client doesn't need the original.

---

## Parallel Data Fetching with Component Composition

React Server Components execute sequentially within a tree. Restructure with composition to parallelize data fetching.

**Incorrect (Sidebar waits for Page's fetch):**

```tsx
export default async function Page() {
  const header = await fetchHeader();
  return (
    <div>
      <div>{header}</div>
      <Sidebar />
    </div>
  );
}
```

**Correct (both fetch simultaneously):**

```tsx
async function Header() {
  const data = await fetchHeader();
  return <div>{data}</div>;
}

async function Sidebar() {
  const items = await fetchSidebarItems();
  return <nav>{items.map(renderItem)}</nav>;
}

export default function Page() {
  return (
    <div>
      <Header />
      <Sidebar />
    </div>
  );
}
```

---

## Minimize Serialization at RSC Boundaries

The RSC/Client boundary serializes all object properties into the HTML response. Only pass fields that the client actually uses.

**Incorrect (serializes all 50 fields):**

```tsx
async function Page() {
  const user = await fetchUser(); // 50 fields
  return <Profile user={user} />;
}

("use client");
function Profile({ user }: { user: User }) {
  return <div>{user.name}</div>; // uses 1 field
}
```

**Correct (serializes only 1 field):**

```tsx
async function Page() {
  const user = await fetchUser();
  return <Profile name={user.name} />;
}

("use client");
function Profile({ name }: { name: string }) {
  return <div>{name}</div>;
}
```
