# TanStack Query v5 — SSR & Next.js

## Table of Contents
- [Core Concept](#core-concept)
- [Next.js Pages Router](#nextjs-pages-router)
- [Next.js App Router](#nextjs-app-router)
- [Streaming](#streaming)
- [Critical Gotchas](#critical-gotchas)

## Core Concept

Server rendering with TanStack Query follows three steps:
1. **Prefetch** data on the server with `queryClient.prefetchQuery()`
2. **Dehydrate** the cache with `dehydrate(queryClient)`
3. **Hydrate** on the client with `<HydrationBoundary state={dehydratedState}>`

## Next.js Pages Router

### getStaticProps / getServerSideProps

```tsx
import { dehydrate, QueryClient } from '@tanstack/react-query'

export async function getStaticProps() {
  const queryClient = new QueryClient()

  await queryClient.prefetchQuery({
    queryKey: ['posts'],
    queryFn: getPosts,
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
    },
  }
}
```

### _app.tsx setup

```tsx
import { HydrationBoundary, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export default function MyApp({ Component, pageProps }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { staleTime: 60 * 1000 },
    },
  }))

  return (
    <QueryClientProvider client={queryClient}>
      <HydrationBoundary state={pageProps.dehydratedState}>
        <Component {...pageProps} />
      </HydrationBoundary>
    </QueryClientProvider>
  )
}
```

### Page component — uses useQuery normally

```tsx
export default function PostsPage() {
  const { data } = useQuery({ queryKey: ['posts'], queryFn: getPosts })
  // data is immediately available from the hydrated cache
}
```

## Next.js App Router

### Provider setup (app/providers.tsx)

```tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // must be > 0 for SSR
      },
    },
  })
}

let browserQueryClient: QueryClient | undefined

function getQueryClient() {
  if (typeof window === 'undefined') {
    // Server: always make a new query client
    return makeQueryClient()
  }
  // Browser: reuse singleton
  if (!browserQueryClient) browserQueryClient = makeQueryClient()
  return browserQueryClient
}

export default function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

**Why not `useState`?** If there is no Suspense boundary between the provider and suspending code, React throws away state on initial suspend. The singleton pattern avoids losing the client.

### Root layout (app/layout.tsx)

```tsx
import Providers from './providers'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

### Prefetch in Server Components

```tsx
// app/posts/page.tsx (Server Component)
import { dehydrate, HydrationBoundary, QueryClient } from '@tanstack/react-query'
import Posts from './posts' // Client Component

export default async function PostsPage() {
  const queryClient = new QueryClient()

  await queryClient.prefetchQuery({
    queryKey: ['posts'],
    queryFn: getPosts,
  })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <Posts />
    </HydrationBoundary>
  )
}
```

```tsx
// app/posts/posts.tsx (Client Component)
'use client'

import { useQuery } from '@tanstack/react-query'

export default function Posts() {
  const { data } = useQuery({ queryKey: ['posts'], queryFn: getPosts })
  // data is available immediately from hydration
}
```

### Nested prefetching

Multiple `<HydrationBoundary>` with separate queryClients at different levels is fine. Deeply nested Server Components can each prefetch their own data.

### Shared queryClient with React.cache

```tsx
import { cache } from 'react'

const getQueryClient = cache(() => new QueryClient())

// Any Server Component in the same request:
export default async function Page() {
  const queryClient = getQueryClient()
  await queryClient.prefetchQuery({ queryKey: ['posts'], queryFn: getPosts })
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <Posts />
    </HydrationBoundary>
  )
}
```

Downside: each `dehydrate()` serializes the entire cache, including previously serialized queries.

## Streaming

Available since v5.40.0. Pending queries can be dehydrated and streamed without `await`.

### Setup — configure dehydration to include pending queries

```tsx
function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: 60 * 1000 },
      dehydrate: {
        shouldDehydrateQuery: (query) =>
          defaultShouldDehydrateQuery(query) || query.state.status === 'pending',
      },
    },
  })
}
```

### Stream prefetch (no await)

```tsx
// app/posts/page.tsx
export default function PostsPage() {
  const queryClient = new QueryClient()

  // No await — query starts but doesn't block rendering
  queryClient.prefetchQuery({ queryKey: ['posts'], queryFn: getPosts })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <Posts />
    </HydrationBoundary>
  )
}
```

On the client, use `useSuspenseQuery` to consume the streamed promise:

```tsx
'use client'
export default function Posts() {
  const { data } = useSuspenseQuery({ queryKey: ['posts'], queryFn: getPosts })
  // Suspends until streamed data arrives, then renders
}
```

### Non-JSON serialization

For data with Dates, Maps, etc., configure custom serialization:

```tsx
defaultOptions: {
  dehydrate: { serializeData: superjson.serialize },
  hydrate: { deserializeData: superjson.deserialize },
}
```

## Critical Gotchas

1. **Never create QueryClient at module scope** — it leaks data between requests/users:
   ```tsx
   // WRONG
   const queryClient = new QueryClient()
   export default function App() { ... }

   // CORRECT
   const [queryClient] = useState(() => new QueryClient())
   ```

2. **Set `staleTime > 0` for SSR** — with default `staleTime: 0`, the client immediately refetches on mount, negating the prefetch.

3. **Don't use `fetchQuery` in Server Components to render data** — if both a Server Component and a Client Component use the same data, they desync when the client revalidates. Use `prefetchQuery` (which only populates the cache) and let client components own the data rendering.

4. **`hydrate` only overwrites if incoming data is newer** — checked by timestamp.

5. **`Error` objects and `undefined` are not JSON-serializable** — handle serialization manually if dehydrating errors. By default, errors are redacted (replaced with `null`).

6. **Data ownership rule:** The component that renders the data should own it. Server Components prefetch; Client Components consume via `useQuery`/`useSuspenseQuery`.
