# TanStack Query v5 — Advanced Patterns

## Table of Contents
- [TypeScript](#typescript)
- [Suspense](#suspense)
- [Dependent Queries](#dependent-queries)
- [Disabling Queries](#disabling-queries)
- [Network Modes](#network-modes)
- [Request Waterfalls](#request-waterfalls)
- [Default Query Function](#default-query-function)
- [Window Focus Refetching](#window-focus-refetching)
- [Placeholder Data](#placeholder-data)

## TypeScript

Requires TypeScript v4.7+. Type changes ship as **patch** semver.

### Type Inference

Types flow from `queryFn` automatically — do not pass generics unless necessary:

```tsx
// GOOD — types inferred
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: () => fetchTodos(), // returns Promise<Todo[]>
})
// data: Todo[] | undefined

// BAD — explicit generics break inference for other params
const { data } = useQuery<Todo[], Error>({ ... })
```

### Type Narrowing (discriminated union)

```tsx
const { data, isSuccess, error, isError } = useQuery({ ... })

if (isSuccess) {
  data // Todo[] (not undefined)
}
if (isError) {
  error // Error (not null)
}
```

### Custom Error Types

Prefer type narrowing over generics:

```tsx
if (axios.isAxiosError(error)) {
  error // AxiosError
}
```

### Register Interface — global type overrides

```tsx
declare module '@tanstack/react-query' {
  interface Register {
    defaultError: AxiosError         // all errors typed as AxiosError
    queryMeta: { auth?: boolean }    // must extend Record<string, unknown>
    mutationMeta: { auth?: boolean }
  }
}
```

### queryOptions / mutationOptions for type flow

```tsx
import { queryOptions, mutationOptions } from '@tanstack/react-query'

const todosOpts = (filters: Filters) => queryOptions({
  queryKey: ['todos', filters],
  queryFn: () => fetchTodos(filters),
})

// Types flow to getQueryData:
const data = queryClient.getQueryData(todosOpts({ status: 'done' }).queryKey)
//    ^? Todo[] | undefined

const addTodoOpts = () => mutationOptions({
  mutationKey: ['addTodo'],
  mutationFn: (input: CreateTodo) => createTodo(input),
})
```

### skipToken — type-safe conditional queries

```tsx
import { skipToken, useQuery } from '@tanstack/react-query'

const { data } = useQuery({
  queryKey: ['user', userId],
  queryFn: userId ? () => fetchUser(userId) : skipToken,
})
// queryFn type is correctly inferred without worrying about undefined userId
```

## Suspense

### Dedicated Hooks

| Hook | Purpose |
|------|---------|
| `useSuspenseQuery` | Suspends until data ready; `data` guaranteed defined |
| `useSuspenseInfiniteQuery` | Same for infinite queries |
| `useSuspenseQueries` | Parallel suspense queries (avoids serial waterfall) |

### Key differences from useQuery

- No `enabled` option — cannot conditionally disable
- No `placeholderData` — use `startTransition` to avoid fallback on key change
- `data` is always defined (never `undefined`)
- Multiple suspense queries in same component fetch **serially** — use `useSuspenseQueries` for parallel

### Parallel suspense queries

```tsx
// WRONG — serial (Article suspends, then Comments fetches after)
function Page({ id }: { id: string }) {
  const { data: article } = useSuspenseQuery(articleOptions(id))
  const { data: comments } = useSuspenseQuery(commentsOptions(id))
}

// CORRECT — parallel
function Page({ id }: { id: string }) {
  const [{ data: article }, { data: comments }] = useSuspenseQueries({
    queries: [articleOptions(id), commentsOptions(id)],
  })
}
```

### Error boundary reset

```tsx
import { QueryErrorResetBoundary } from '@tanstack/react-query'
import { ErrorBoundary } from 'react-error-boundary'

function App() {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary onReset={reset} fallbackRender={({ resetErrorBoundary }) => (
          <div>
            <p>Something went wrong</p>
            <button onClick={() => resetErrorBoundary()}>Try again</button>
          </div>
        )}>
          <Page />
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  )
}
```

### throwOnError default for suspense

```tsx
// Only throws when there's NO cached data
throwOnError: (error, query) => typeof query.state.data === 'undefined'
```

To throw all errors: manually throw when `error && !isFetching`.

## Dependent Queries

Use `enabled` to chain queries:

```tsx
const { data: user } = useQuery({
  queryKey: ['user', email],
  queryFn: () => getUserByEmail(email),
})

const { data: projects } = useQuery({
  queryKey: ['projects', user?.id],
  queryFn: () => getProjectsByUser(user!.id),
  enabled: !!user?.id,
})
```

**Dynamic parallel dependent queries:**

```tsx
const { data: userIds } = useQuery({
  queryKey: ['users'],
  queryFn: getUsersData,
  select: (users) => users.map(u => u.id),
})

const usersMessages = useQueries({
  queries: userIds
    ? userIds.map((id) => ({
        queryKey: ['messages', id],
        queryFn: () => getMessagesByUser(id),
      }))
    : [],
})
```

## Disabling Queries

### enabled: false

- No auto-fetch on mount, no background refetch
- Ignores `invalidateQueries` and `refetchQueries`
- Manual `refetch()` still works
- Without cache: starts `status: 'pending'`, `fetchStatus: 'idle'`

### skipToken (preferred for TypeScript)

```tsx
const { data } = useQuery({
  queryKey: ['todos', filter],
  queryFn: filter ? () => fetchTodos(filter) : skipToken,
})
```

**skipToken does NOT support `refetch()`** — throws "Missing queryFn". Use `enabled: false` if manual refetch is needed.

### Lazy queries (preferred pattern)

```tsx
const [enabled, setEnabled] = useState(false)
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  enabled,
})
<button onClick={() => setEnabled(true)}>Load</button>
```

### isLoading vs isPending

- `isPending` = no cached data (regardless of fetch status)
- `isLoading` = `isPending && isFetching` (first actual load)

Use `isLoading` to distinguish "first load" from "disabled/idle".

## Network Modes

`networkMode: 'online' | 'always' | 'offlineFirst'` (default: `'online'`)

| Mode | Behavior | Use Case |
|------|----------|----------|
| `online` | Only fetches with network; pauses retries offline | Default for most APIs |
| `always` | Ignores online/offline; never pauses | AsyncStorage, local data, `Promise.resolve` |
| `offlineFirst` | Tries once, pauses retries if offline | Service worker / HTTP cache (PWAs) |

**Key:** With `online` mode, check both `status` and `fetchStatus` before showing spinners — a query can be `pending` + `paused` (no data, no network).

## Request Waterfalls

Each waterfall step = at least one server roundtrip. At 250ms latency (3G), 4 steps = 1000ms overhead.

### Three types

**1. Serial queries in one component:**
```tsx
// BAD — waterfall
const { data: user } = useQuery(userOptions(email))
const { data: projects } = useQuery({ ...projectsOptions(user?.id), enabled: !!user?.id })

// FIX — restructure API to avoid dependency
const { data: projects } = useQuery(projectsByEmailOptions(email))
```

**2. Nested component waterfalls:**
Parent suspends → child mounts → child fetches. Fix: hoist child query up or prefetch at route level.

**3. Code splitting + queries:**
`Markup → JS → Lazy chunk → Query` = quadruple waterfall. Fix: prefetch at route level.

### Fix with useSuspenseQueries

```tsx
// BAD — serial (each suspends before next mounts)
const { data: a } = useSuspenseQuery(optionsA)
const { data: b } = useSuspenseQuery(optionsB)

// GOOD — parallel
const [{ data: a }, { data: b }] = useSuspenseQueries({
  queries: [optionsA, optionsB],
})
```

### Fix with prefetching

```tsx
// In route loader or parent component:
queryClient.prefetchQuery(articleOptions(id))
queryClient.prefetchQuery(commentsOptions(id))
// Both start fetching immediately, no waterfall
```

## Default Query Function

Share one `queryFn` across all queries:

```tsx
const defaultQueryFn = async ({ queryKey }: { queryKey: QueryKey }) => {
  const { data } = await axios.get(`https://api.example.com${queryKey[0]}`)
  return data
}

const queryClient = new QueryClient({
  defaultOptions: { queries: { queryFn: defaultQueryFn } },
})

// Usage — no queryFn needed:
useQuery({ queryKey: ['/posts'] })
useQuery({ queryKey: [`/posts/${postId}`], enabled: !!postId })
```

Per-query `queryFn` overrides the default.

## Window Focus Refetching

Enabled by default. Stale queries refetch when the browser tab regains focus.

```tsx
// Disable globally:
new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false } },
})

// Disable per query:
useQuery({ queryKey: ['todos'], queryFn: fetchTodos, refetchOnWindowFocus: false })
```

### React Native

```tsx
import { AppState, Platform } from 'react-native'
import { focusManager } from '@tanstack/react-query'

function onAppStateChange(status: AppStateStatus) {
  if (Platform.OS !== 'web') {
    focusManager.setFocused(status === 'active')
  }
}

useEffect(() => {
  const sub = AppState.addEventListener('change', onAppStateChange)
  return () => sub.remove()
}, [])
```

## Placeholder Data

Temporary display data that is NOT persisted to cache (unlike `initialData`).

```tsx
// Static placeholder
useQuery({ queryKey: ['todos'], queryFn: fetchTodos, placeholderData: [] })

// Keep previous data during key changes (pagination)
useQuery({
  queryKey: ['todos', id],
  queryFn: () => fetchTodo(id),
  placeholderData: (previousData) => previousData,
})

// From another query's cache (list → detail preview)
useQuery({
  queryKey: ['todo', todoId],
  queryFn: () => fetchTodo(todoId),
  placeholderData: () =>
    queryClient.getQueryData<Todo[]>(['todos'])?.find(t => t.id === todoId),
})
```

`isPlaceholderData` is `true` when showing placeholder data.
