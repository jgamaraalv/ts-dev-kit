# TanStack Query v5 — Testing

## Setup

Use `@testing-library/react` (v14+) directly — no need for `@testing-library/react-hooks`.

### Create a wrapper with isolated QueryClient

```tsx
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,  // CRITICAL: disable retries in tests
      },
    },
  })
}

function createWrapper() {
  const queryClient = createTestQueryClient()
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}
```

## Testing a Custom Hook

```tsx
// hooks/useTodos.ts
export function useTodos() {
  return useQuery({ queryKey: ['todos'], queryFn: fetchTodos })
}

// hooks/useTodos.test.ts
import { renderHook, waitFor } from '@testing-library/react'
import { useTodos } from './useTodos'

test('fetches todos', async () => {
  const { result } = renderHook(() => useTodos(), {
    wrapper: createWrapper(),
  })

  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data).toEqual([{ id: 1, title: 'Test' }])
})
```

## Network Mocking

### With nock

```tsx
import nock from 'nock'

test('fetches data from API', async () => {
  nock('http://example.com')
    .get('/api/todos')
    .reply(200, [{ id: 1, title: 'Test' }])

  const { result } = renderHook(() => useTodos(), {
    wrapper: createWrapper(),
  })

  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data).toEqual([{ id: 1, title: 'Test' }])
})
```

### With msw (recommended)

```tsx
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

const server = setupServer(
  http.get('/api/todos', () =>
    HttpResponse.json([{ id: 1, title: 'Test' }])
  ),
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

## Testing Infinite Queries

```tsx
import nock from 'nock'

test('fetches multiple pages', async () => {
  const expectation = nock('http://example.com')
    .persist()  // .persist() for multiple requests
    .query(true)
    .get('/api/items')
    .reply(200, (uri) => {
      const url = new URL(`http://example.com${uri}`)
      const page = url.searchParams.get('page') ?? '1'
      return { items: [`item-${page}`], nextPage: Number(page) < 3 ? Number(page) + 1 : null }
    })

  const { result } = renderHook(() => useInfiniteItems(), {
    wrapper: createWrapper(),
  })

  await waitFor(() => expect(result.current.isSuccess).toBe(true))
  expect(result.current.data.pages).toHaveLength(1)

  // Fetch next page
  result.current.fetchNextPage()

  await waitFor(() => expect(result.current.data.pages).toHaveLength(2))
})
```

## Testing Mutations

```tsx
test('creates a todo and invalidates list', async () => {
  const queryClient = createTestQueryClient()
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  // Pre-populate cache
  queryClient.setQueryData(['todos'], [{ id: 1, title: 'Existing' }])

  const { result } = renderHook(() => useCreateTodo(), { wrapper })

  result.current.mutate({ title: 'New Todo' })

  await waitFor(() => expect(result.current.isSuccess).toBe(true))
})
```

## Key Gotchas

1. **Always disable retries** — Default 3 retries with exponential backoff causes test timeouts:
   ```tsx
   new QueryClient({ defaultOptions: { queries: { retry: false } } })
   ```
   Note: explicit `retry` on individual queries overrides this default.

2. **Always use `waitFor`** — Query state updates are async. Never assert synchronously after `renderHook`.

3. **Isolate QueryClient per test** — Create a new `QueryClient` for each test to prevent cross-test contamination. Do not share a client across tests.

4. **Jest "did not exit" warning** — If you get this, set `gcTime: Infinity` on the test QueryClient to prevent garbage collection timers from hanging:
   ```tsx
   new QueryClient({
     defaultOptions: {
       queries: { retry: false, gcTime: Infinity },
     },
   })
   ```

5. **Component testing** — For testing components (not just hooks), render the component inside the wrapper:
   ```tsx
   import { render, screen, waitFor } from '@testing-library/react'

   test('renders todo list', async () => {
     render(<TodoList />, { wrapper: createWrapper() })
     await waitFor(() => expect(screen.getByText('Test Todo')).toBeInTheDocument())
   })
   ```
