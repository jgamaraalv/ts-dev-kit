---
name: tanstack-query
description: |
  TanStack Query v5 (React Query) reference for data fetching, caching,
  and server state management in React. Use when: (1) writing useQuery,
  useMutation, or useInfiniteQuery hooks, (2) setting up QueryClient
  and queryOptions, (3) implementing optimistic updates or cache
  invalidation, (4) configuring SSR/hydration with Next.js App Router
  or Pages Router, (5) testing React Query hooks, (6) working with
  TypeScript types, Suspense, or advanced patterns like dependent
  queries and infinite scroll.
---

# TanStack Query v5 (React)

<quick_reference>

## Setup

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 min (default is 0)
      gcTime: 5 * 60 * 1000, // 5 min (default)
      retry: 3,              // 3 retries with exponential backoff (default)
      refetchOnWindowFocus: true, // default
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
    </QueryClientProvider>
  )
}
```

## Important Defaults

| Default | Value | Notes |
|---------|-------|-------|
| `staleTime` | `0` | Cached data is immediately stale; triggers background refetch on mount/focus/reconnect |
| `gcTime` | `5 min` | Inactive queries garbage collected after 5 minutes |
| `retry` | `3` (queries) / `0` (mutations) | Queries retry 3x with exponential backoff; mutations do NOT retry |
| `refetchOnWindowFocus` | `true` | Stale queries refetch when tab regains focus |
| `refetchOnReconnect` | `true` | Stale queries refetch when network reconnects |
| `refetchOnMount` | `true` | Stale queries refetch when new instance mounts |
| `structuralSharing` | `true` | Preserves referential identity if data is structurally equal |

**Key recommendation:** Set `staleTime` above 0 to control refetch frequency rather than disabling individual refetch triggers.

</quick_reference>

<examples>

## queryOptions — co-locate key + fn

Always use `queryOptions` to define query configurations. It enables type inference across `useQuery`, `prefetchQuery`, `getQueryData`, and `setQueryData`.

```tsx
import { queryOptions, infiniteQueryOptions } from '@tanstack/react-query'

export function todosOptions(filters: TodoFilters) {
  return queryOptions({
    queryKey: ['todos', filters],
    queryFn: () => fetchTodos(filters),
    staleTime: 5 * 1000,
  })
}

// Works everywhere with full type inference:
useQuery(todosOptions({ status: 'done' }))
useSuspenseQuery(todosOptions({ status: 'done' }))
queryClient.prefetchQuery(todosOptions({ status: 'done' }))
queryClient.setQueryData(todosOptions({ status: 'done' }).queryKey, newData)
const cached = queryClient.getQueryData(todosOptions({ status: 'done' }).queryKey)
//    ^? TodoItem[] | undefined
```

For infinite queries, use `infiniteQueryOptions` (same pattern, adds `initialPageParam` and `getNextPageParam`).

## useQuery

```tsx
const {
  data,              // TData | undefined
  error,             // TError | null
  status,            // 'pending' | 'error' | 'success'
  isPending,         // no cached data yet
  isError,
  isSuccess,
  isFetching,        // queryFn is running (including background refetch)
  isLoading,         // isPending && isFetching (first load only)
  isPlaceholderData, // showing placeholder, not real data
  isStale,
  refetch,
  fetchStatus,       // 'fetching' | 'paused' | 'idle'
} = useQuery({
  queryKey: ['todos', userId],  // unique cache key (Array)
  queryFn: () => fetchTodos(userId),
  enabled: !!userId,            // disable until userId exists
  staleTime: 60_000,
  select: (data) => data.filter(t => !t.done), // transform/filter
  placeholderData: keepPreviousData,            // smooth pagination
})
```

**Query states:** `status` tells you "do we have data?"; `fetchStatus` tells you "is the queryFn running?". They are orthogonal — a query can be `pending` + `paused` (no data, no network).

## Query Keys

Keys must be Arrays. They are hashed deterministically.

```tsx
// Object key order does NOT matter — these are equivalent:
useQuery({ queryKey: ['todos', { status, page }] })
useQuery({ queryKey: ['todos', { page, status }] })

// Array item order DOES matter — these are different:
useQuery({ queryKey: ['todos', status, page] })
useQuery({ queryKey: ['todos', page, status] })
```

**Rule:** If your queryFn depends on a variable, include it in the queryKey. The key acts as a dependency array.

## useMutation

```tsx
const queryClient = useQueryClient()

const mutation = useMutation({
  mutationFn: (newTodo: CreateTodoInput) => api.post('/todos', newTodo),
  onSuccess: (data, variables) => {
    // Invalidate related queries to trigger refetch
    queryClient.invalidateQueries({ queryKey: ['todos'] })
    // Or update cache directly with response data
    queryClient.setQueryData(['todos', data.id], data)
  },
  onError: (error, variables, onMutateResult) => {},
  onSettled: (data, error, variables, onMutateResult) => {},
})

// Trigger:
mutation.mutate({ title: 'New todo' })

// Or with per-call callbacks:
mutation.mutate(input, { onSuccess: () => navigate('/todos') })

// Async variant (returns Promise):
const data = await mutation.mutateAsync(input)
```

**Lifecycle:** `onMutate` → `mutationFn` → `onSuccess`/`onError` → `onSettled`. Callbacks returning promises are awaited.

**Gotcha:** Per-call `mutate()` callbacks only fire for the *latest* call if mutations overlap. Use `useMutation`-level callbacks for reliable logic.

## Query Invalidation

```tsx
// Prefix match (default) — invalidates ['todos'] and ['todos', { page: 1 }]
queryClient.invalidateQueries({ queryKey: ['todos'] })

// Exact match only
queryClient.invalidateQueries({ queryKey: ['todos'], exact: true })

// Predicate for fine-grained control
queryClient.invalidateQueries({
  predicate: (query) => query.queryKey[0] === 'todos' && query.queryKey[1]?.version >= 10,
})

// ALL queries
queryClient.invalidateQueries()
```

Invalidation marks queries as stale and triggers background refetch for active (rendered) queries.

## Optimistic Updates

### Approach 1: Via the UI (simpler, recommended)

Render optimistic state from `variables` directly in JSX:

```tsx
const { mutate, variables, isPending, isError } = useMutation({
  mutationFn: (text: string) => api.post('/todos', { text }),
  onSettled: () => queryClient.invalidateQueries({ queryKey: ['todos'] }),
})

// In JSX:
{todos.map(todo => <li key={todo.id}>{todo.text}</li>)}
{isPending && <li style={{ opacity: 0.5 }}>{variables}</li>}
```

Access pending mutations from other components with `useMutationState`:

```tsx
const pendingTodos = useMutationState<string>({
  filters: { mutationKey: ['addTodo'], status: 'pending' },
  select: (mutation) => mutation.state.variables,
})
```

### Approach 2: Via cache (with rollback)

```tsx
useMutation({
  mutationFn: updateTodo,
  onMutate: async (newTodo, context) => {
    await context.client.cancelQueries({ queryKey: ['todos'] })
    const previous = context.client.getQueryData(['todos'])
    context.client.setQueryData(['todos'], (old) => [...old, newTodo])
    return { previous }
  },
  onError: (err, newTodo, onMutateResult, context) => {
    context.client.setQueryData(['todos'], onMutateResult.previous)
  },
  onSettled: (data, error, variables, onMutateResult, context) => {
    context.client.invalidateQueries({ queryKey: ['todos'] })
  },
})
```

**Always** `cancelQueries` before optimistic update to prevent background refetches from overwriting.

## Infinite Queries

```tsx
const {
  data,               // { pages: T[], pageParams: unknown[] }
  fetchNextPage,
  fetchPreviousPage,
  hasNextPage,        // true when getNextPageParam returns non-null/undefined
  hasPreviousPage,
  isFetchingNextPage,
  isFetchingPreviousPage,
} = useInfiniteQuery({
  queryKey: ['projects'],
  queryFn: ({ pageParam }) => fetchProjects(pageParam),
  initialPageParam: 0,     // REQUIRED
  getNextPageParam: (lastPage, allPages) => lastPage.nextCursor ?? undefined,
  maxPages: 3,             // optional: cap cached pages
})

// Render all pages:
{data.pages.map((page, i) => (
  <Fragment key={i}>
    {page.items.map(item => <div key={item.id}>{item.name}</div>)}
  </Fragment>
))}

// Load more:
<button onClick={() => fetchNextPage()} disabled={!hasNextPage || isFetchingNextPage}>
  {isFetchingNextPage ? 'Loading...' : hasNextPage ? 'Load More' : 'No more'}
</button>
```

**Gotcha:** `data` is `{ pages, pageParams }`, not flat data. `initialData` and `placeholderData` must match this shape.

## Paginated Queries (keep previous data)

```tsx
import { keepPreviousData, useQuery } from '@tanstack/react-query'

const { data, isPlaceholderData } = useQuery({
  queryKey: ['projects', page],
  queryFn: () => fetchProjects(page),
  placeholderData: keepPreviousData,
})

// Prefetch next page for instant transitions:
queryClient.prefetchQuery({
  queryKey: ['projects', page + 1],
  queryFn: () => fetchProjects(page + 1),
})
```

## Prefetching

```tsx
// In event handlers (hover/focus):
const prefetch = () => queryClient.prefetchQuery(todosOptions())
<button onMouseEnter={prefetch} onFocus={prefetch} onClick={handleClick}>Show</button>

// In components (avoid Suspense waterfalls):
function Layout({ id }: { id: string }) {
  usePrefetchQuery(commentsOptions(id)) // starts fetch immediately
  return (
    <Suspense fallback="Loading...">
      <Article id={id} />
    </Suspense>
  )
}

// Prefetch infinite queries:
queryClient.prefetchInfiniteQuery({
  ...projectsInfiniteOptions(),
  pages: 3, // prefetch first 3 pages
})
```

## Dependent Queries

```tsx
const { data: user } = useQuery({
  queryKey: ['user', email],
  queryFn: () => getUserByEmail(email),
})

const { data: projects } = useQuery({
  queryKey: ['projects', user?.id],
  queryFn: () => getProjectsByUser(user!.id),
  enabled: !!user?.id, // waits for user query
})
```

**Type-safe disabling with skipToken:**

```tsx
import { skipToken } from '@tanstack/react-query'

const { data } = useQuery({
  queryKey: ['projects', userId],
  queryFn: userId ? () => getProjects(userId) : skipToken,
})
```

`skipToken` prevents `refetch()` from working — use `enabled: false` if you need manual refetch.

</examples>

<gotchas>

## setQueryData — immutability

```tsx
// WRONG — mutating cache in place
queryClient.setQueryData(['todo', id], (old) => {
  if (old) old.title = 'new' // DO NOT DO THIS
  return old
})

// CORRECT — return new object
queryClient.setQueryData(['todo', id], (old) =>
  old ? { ...old, title: 'new' } : old
)
```

</gotchas>

<references>

## Further Reference

- **Full API signatures** (useQuery, useMutation, useInfiniteQuery, QueryClient): See [references/api-reference.md](references/api-reference.md)
- **SSR & Next.js** (hydration, App Router, streaming): See [references/ssr-nextjs.md](references/ssr-nextjs.md)
- **Testing** (renderHook, mocking, setup): See [references/testing.md](references/testing.md)
- **Advanced patterns** (TypeScript, Suspense, waterfalls, network modes): See [references/advanced-patterns.md](references/advanced-patterns.md)

</references>
