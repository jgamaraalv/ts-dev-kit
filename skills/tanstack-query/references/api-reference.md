# TanStack Query v5 — API Reference

## Table of Contents
- [useQuery Options](#usequery-options)
- [useQuery Returns](#usequery-returns)
- [useMutation Options](#usemutation-options)
- [useMutation Returns](#usemutation-returns)
- [useInfiniteQuery Options](#useinfinitequery-options)
- [useInfiniteQuery Returns](#useinfinitequery-returns)
- [QueryClient Methods](#queryclient-methods)
- [QueryCache](#querycache)
- [MutationCache](#mutationcache)
- [queryOptions / infiniteQueryOptions](#queryoptions--infinitequeryoptions)

## useQuery Options

```tsx
const result = useQuery(options, queryClient?)
```

| Option | Type | Default |
|--------|------|---------|
| `queryKey` | `unknown[]` | **required** |
| `queryFn` | `(context: QueryFunctionContext) => Promise<TData>` | **required** (unless default set) |
| `enabled` | `boolean \| (query: Query) => boolean` | `true` |
| `staleTime` | `number \| 'static' \| ((query) => number \| 'static')` | `0` |
| `gcTime` | `number \| Infinity` | `300000` (5 min) / `Infinity` on server |
| `retry` | `boolean \| number \| (failureCount, error) => boolean` | `3` client / `0` server |
| `retryDelay` | `number \| (attempt, error) => number` | exponential backoff |
| `retryOnMount` | `boolean` | `true` |
| `refetchInterval` | `number \| false \| ((query) => number \| false)` | — |
| `refetchIntervalInBackground` | `boolean` | `false` |
| `refetchOnMount` | `boolean \| 'always' \| ((query) => boolean \| 'always')` | `true` |
| `refetchOnWindowFocus` | `boolean \| 'always' \| ((query) => boolean \| 'always')` | `true` |
| `refetchOnReconnect` | `boolean \| 'always' \| ((query) => boolean \| 'always')` | `true` |
| `networkMode` | `'online' \| 'always' \| 'offlineFirst'` | `'online'` |
| `select` | `(data: TData) => unknown` | — |
| `initialData` | `TData \| () => TData` | — |
| `initialDataUpdatedAt` | `number \| (() => number)` | — |
| `placeholderData` | `TData \| (previousValue, previousQuery) => TData` | — |
| `notifyOnChangeProps` | `string[] \| 'all'` | tracked access |
| `structuralSharing` | `boolean \| (oldData, newData) => unknown` | `true` |
| `throwOnError` | `boolean \| (error, query) => boolean` | — |
| `meta` | `Record<string, unknown>` | — |
| `subscribed` | `boolean` | `true` |

**QueryFunctionContext** passed to `queryFn`:
- `queryKey` — the query key array
- `client` — the QueryClient instance
- `signal` — AbortSignal for cancellation
- `meta` — optional metadata from the query option

**Key notes:**
- `queryFn` must resolve data; data **cannot be `undefined`**
- `initialData` persists to cache; `placeholderData` does not
- `select` only re-runs when data or function reference changes — wrap in `useCallback` if inline
- `staleTime: 'static'` — data is never stale, even `refetchOnWindowFocus: 'always'` is blocked

## useQuery Returns

| Property | Type | Notes |
|----------|------|-------|
| `data` | `TData \| undefined` | |
| `error` | `TError \| null` | |
| `status` | `'pending' \| 'error' \| 'success'` | |
| `isPending` | `boolean` | No cached data |
| `isSuccess` | `boolean` | |
| `isError` | `boolean` | |
| `isLoading` | `boolean` | `isPending && isFetching` (first load) |
| `isLoadingError` | `boolean` | Failed on first fetch |
| `isRefetchError` | `boolean` | Failed while refetching |
| `fetchStatus` | `'fetching' \| 'paused' \| 'idle'` | |
| `isFetching` | `boolean` | queryFn running |
| `isPaused` | `boolean` | Wants to fetch but offline |
| `isRefetching` | `boolean` | `isFetching && !isPending` |
| `isStale` | `boolean` | |
| `isPlaceholderData` | `boolean` | |
| `isFetched` | `boolean` | |
| `isFetchedAfterMount` | `boolean` | |
| `dataUpdatedAt` | `number` | Timestamp |
| `errorUpdatedAt` | `number` | |
| `failureCount` | `number` | Resets to 0 on success |
| `failureReason` | `TError \| null` | |
| `errorUpdateCount` | `number` | Total errors ever |
| `isEnabled` | `boolean` | |
| `refetch` | `(opts?) => Promise<UseQueryResult>` | `cancelRefetch` defaults to `true` |

## useMutation Options

```tsx
const result = useMutation(options, queryClient?)
```

| Option | Type | Default |
|--------|------|---------|
| `mutationFn` | `(variables, context: MutationFunctionContext) => Promise<TData>` | **required** |
| `mutationKey` | `unknown[]` | — |
| `gcTime` | `number \| Infinity` | — |
| `retry` | `boolean \| number \| (failureCount, error) => boolean` | `0` |
| `retryDelay` | `number \| (attempt, error) => number` | — |
| `networkMode` | `'online' \| 'always' \| 'offlineFirst'` | `'online'` |
| `onMutate` | `(variables, context) => Promise<TOnMutateResult> \| TOnMutateResult` | — |
| `onSuccess` | `(data, variables, onMutateResult, context) => Promise \| void` | — |
| `onError` | `(error, variables, onMutateResult, context) => Promise \| void` | — |
| `onSettled` | `(data, error, variables, onMutateResult, context) => Promise \| void` | — |
| `scope` | `{ id: string }` | unique (parallel) |
| `throwOnError` | `boolean \| (error) => boolean` | — |
| `meta` | `Record<string, unknown>` | — |

**Callback context:** `onMutate` return value is passed as `onMutateResult` to `onSuccess`/`onError`/`onSettled`. The `context` object provides `context.client` (the QueryClient).

**Scope:** Mutations with the same `scope.id` run **serially** (queued), not in parallel.

## useMutation Returns

| Property | Type | Notes |
|----------|------|-------|
| `mutate` | `(variables, { onSuccess?, onError?, onSettled? }) => void` | Fire and forget |
| `mutateAsync` | `(variables, opts?) => Promise<TData>` | Returns promise |
| `status` | `'idle' \| 'pending' \| 'error' \| 'success'` | |
| `isIdle`, `isPending`, `isSuccess`, `isError` | `boolean` | |
| `isPaused` | `boolean` | |
| `data` | `TData \| undefined` | |
| `error` | `TError \| null` | |
| `variables` | `TVariables \| undefined` | Last call's variables |
| `reset` | `() => void` | Clear mutation state |
| `submittedAt` | `number` | |
| `failureCount` | `number` | |
| `failureReason` | `TError \| null` | |

## useInfiniteQuery Options

Inherits all `useQuery` options plus:

| Option | Type | Default |
|--------|------|---------|
| `initialPageParam` | `TPageParam` | **required** |
| `getNextPageParam` | `(lastPage, allPages, lastPageParam, allPageParams) => TPageParam \| undefined \| null` | **required** |
| `getPreviousPageParam` | `(firstPage, allPages, firstPageParam, allPageParams) => TPageParam \| undefined \| null` | — |
| `maxPages` | `number` | `undefined` (unlimited) |

Return `undefined`/`null` from page param getters to signal no more pages. When `maxPages` is set, both `getNextPageParam` and `getPreviousPageParam` must be defined.

## useInfiniteQuery Returns

Inherits all `useQuery` returns plus:

| Property | Type | Notes |
|----------|------|-------|
| `data.pages` | `TData[]` | Array of page results |
| `data.pageParams` | `unknown[]` | Array of page params used |
| `fetchNextPage` | `(opts?) => Promise` | |
| `fetchPreviousPage` | `(opts?) => Promise` | |
| `hasNextPage` | `boolean` | |
| `hasPreviousPage` | `boolean` | |
| `isFetchingNextPage` | `boolean` | |
| `isFetchingPreviousPage` | `boolean` | |
| `isFetchNextPageError` | `boolean` | |
| `isFetchPreviousPageError` | `boolean` | |

## QueryClient Methods

### Constructor

```tsx
const queryClient = new QueryClient({
  queryCache?: QueryCache,
  mutationCache?: MutationCache,
  defaultOptions?: {
    queries?: QueryOptions,
    mutations?: MutationOptions,
    hydrate?: HydrateOptions,
    dehydrate?: DehydrateOptions,
  },
})
```

### Data Access (synchronous)

| Method | Signature | Notes |
|--------|-----------|-------|
| `getQueryData` | `(queryKey) => TData \| undefined` | |
| `getQueriesData` | `(filters) => [QueryKey, TData \| undefined][]` | |
| `getQueryState` | `(queryKey) => QueryState \| undefined` | |
| `setQueryData` | `(queryKey, updater: TData \| (old => TData)) => TData \| undefined` | **Must be immutable** |
| `setQueriesData` | `(filters, updater) => [QueryKey, TData \| undefined][]` | Only updates existing entries |

### Fetching (async)

| Method | Signature | Notes |
|--------|-----------|-------|
| `fetchQuery` | `(options) => Promise<TData>` | Returns cached data if fresh; throws on error |
| `prefetchQuery` | `(options) => Promise<void>` | Never throws; never returns data |
| `ensureQueryData` | `(options) => Promise<TData>` | Only fetches if not cached; `revalidateIfStale` option |
| `fetchInfiniteQuery` | `(options) => Promise<InfiniteData>` | |
| `prefetchInfiniteQuery` | `(options) => Promise<void>` | |
| `ensureInfiniteQueryData` | `(options) => Promise<InfiniteData>` | |

### Cache Management

| Method | Signature | Notes |
|--------|-----------|-------|
| `invalidateQueries` | `(filters?, options?) => Promise<void>` | Marks stale + refetches active |
| `refetchQueries` | `(filters?, options?) => Promise<void>` | |
| `cancelQueries` | `(filters?) => Promise<void>` | |
| `removeQueries` | `(filters?) => void` | |
| `resetQueries` | `(filters?, options?) => Promise<void>` | Resets to initial state |
| `clear` | `() => void` | Clears all caches |

### invalidateQueries filters

```tsx
queryClient.invalidateQueries({
  queryKey?: QueryKey,     // prefix match by default
  exact?: boolean,         // exact key match
  refetchType?: 'active' | 'inactive' | 'all' | 'none', // default: 'active'
  predicate?: (query: Query) => boolean,
})
```

### Defaults

| Method | Signature |
|--------|-----------|
| `setQueryDefaults` | `(queryKey, options) => void` |
| `getQueryDefaults` | `(queryKey) => QueryOptions` |
| `setMutationDefaults` | `(mutationKey, options) => void` |
| `getMutationDefaults` | `(mutationKey) => MutationOptions` |
| `setDefaultOptions` | `(options) => void` |

`setQueryDefaults` order matters: register from most generic to least generic key.

### Status

| Method | Returns |
|--------|---------|
| `isFetching(filters?)` | `number` — count of fetching queries |
| `isMutating(filters?)` | `number` — count of in-flight mutations |

## QueryCache

```tsx
const queryCache = new QueryCache({
  onError?: (error, query) => void,
  onSuccess?: (data, query) => void,
  onSettled?: (data, error, query) => void,
})
```

| Method | Returns |
|--------|---------|
| `queryCache.find(filters)` | `Query \| undefined` |
| `queryCache.findAll(filters?)` | `Query[]` |
| `queryCache.subscribe(callback)` | `() => void` (unsubscribe) |
| `queryCache.clear()` | `void` |

## MutationCache

```tsx
const mutationCache = new MutationCache({
  onMutate?: (variables, mutation, context) => void,
  onError?: (error, variables, onMutateResult, mutation, context) => void,
  onSuccess?: (data, variables, onMutateResult, mutation, context) => void,
  onSettled?: (data, error, variables, onMutateResult, mutation, context) => void,
})
```

Global MutationCache callbacks **always fire** and cannot be overridden by individual mutations. If callbacks return a Promise, it is awaited.

| Method | Returns |
|--------|---------|
| `mutationCache.getAll()` | `Mutation[]` |
| `mutationCache.subscribe(callback)` | `() => void` |
| `mutationCache.clear()` | `void` |

## queryOptions / infiniteQueryOptions

```tsx
import { queryOptions, infiniteQueryOptions } from '@tanstack/react-query'

// queryOptions — preserves type inference across useQuery, prefetchQuery, getQueryData
const opts = queryOptions({
  queryKey: ['groups', id],
  queryFn: () => fetchGroups(id),
  staleTime: 5000,
})

// infiniteQueryOptions — same for infinite queries
const infOpts = infiniteQueryOptions({
  queryKey: ['projects'],
  queryFn: ({ pageParam }) => fetchProjects(pageParam),
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor,
})
```

Without `queryOptions`, `getQueryData` returns `unknown`. With it, types flow automatically.
