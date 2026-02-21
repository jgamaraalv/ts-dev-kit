# Service Worker API Reference

## Table of Contents

- [Cache](#cache)
- [CacheStorage (caches)](#cachestorage)
- [FetchEvent](#fetchevent)
- [Clients](#clients)
- [Client / WindowClient](#client--windowclient)

## Cache

A single named cache. Stores `Request`/`Response` pairs.

### Methods

| Method                         | Returns                          | Description                        |
| ------------------------------ | -------------------------------- | ---------------------------------- |
| `match(request, options?)`     | `Promise<Response \| undefined>` | Find first matching response       |
| `matchAll(request?, options?)` | `Promise<Response[]>`            | Find all matching responses        |
| `add(request)`                 | `Promise<void>`                  | Fetch URL and cache the response   |
| `addAll(requests)`             | `Promise<void>`                  | Fetch all URLs and cache responses |
| `put(request, response)`       | `Promise<void>`                  | Store a request/response pair      |
| `delete(request, options?)`    | `Promise<boolean>`               | Remove a cached entry              |
| `keys(request?, options?)`     | `Promise<Request[]>`             | List cached requests               |

**Match options:** `{ ignoreSearch, ignoreMethod, ignoreVary }`

**Notes:**

- `add()`/`addAll()` will reject for non-2xx responses
- `put()` accepts any response (including opaque)
- Always `response.clone()` before caching if you also need to return it
- Cache API ignores HTTP caching headers
- `Set-Cookie` headers are stripped from cached responses

## CacheStorage

Accessed via `caches` (global in SW and window).

### Methods

| Method                     | Returns                          | Description                 |
| -------------------------- | -------------------------------- | --------------------------- |
| `open(name)`               | `Promise<Cache>`                 | Open/create a named cache   |
| `match(request, options?)` | `Promise<Response \| undefined>` | Search across all caches    |
| `has(name)`                | `Promise<boolean>`               | Check if named cache exists |
| `delete(name)`             | `Promise<boolean>`               | Delete a named cache        |
| `keys()`                   | `Promise<string[]>`              | List all cache names        |

## FetchEvent

Passed to `fetch` event handlers. Only available in SW context.

### Properties

| Property            | Type                             | Description                               |
| ------------------- | -------------------------------- | ----------------------------------------- |
| `request`           | `Request`                        | The intercepted request                   |
| `clientId`          | `string`                         | ID of the client that initiated the fetch |
| `resultingClientId` | `string`                         | ID of the client being navigated to       |
| `replacesClientId`  | `string`                         | ID of the client being replaced           |
| `preloadResponse`   | `Promise<Response \| undefined>` | Navigation preload response               |
| `handled`           | `Promise<void>`                  | Resolves when the event has been handled  |

### Methods

| Method                 | Description                                              |
| ---------------------- | -------------------------------------------------------- |
| `respondWith(promise)` | Provide a custom response. Must be called synchronously. |
| `waitUntil(promise)`   | Extend event lifetime (inherited from ExtendableEvent)   |

## Clients

Access controlled pages from the SW. Available via `self.clients`.

### Methods

| Method               | Returns                         | Description                                                        |
| -------------------- | ------------------------------- | ------------------------------------------------------------------ |
| `get(id)`            | `Promise<Client \| undefined>`  | Get a client by ID                                                 |
| `matchAll(options?)` | `Promise<Client[]>`             | Get all matching clients. Options: `{ type, includeUncontrolled }` |
| `openWindow(url)`    | `Promise<WindowClient \| null>` | Open a new window/tab                                              |
| `claim()`            | `Promise<void>`                 | Take control of all in-scope clients without reload                |

## Client / WindowClient

Represents a controlled page/worker.

### Client Properties

| Property | Type     | Description                              |
| -------- | -------- | ---------------------------------------- |
| `id`     | `string` | Unique identifier                        |
| `type`   | `string` | `"window" \| "worker" \| "sharedworker"` |
| `url`    | `string` | URL of the client                        |

### Client Methods

| Method                         | Description                |
| ------------------------------ | -------------------------- |
| `postMessage(data, transfer?)` | Send message to the client |

### WindowClient (extends Client)

| Property          | Type      | Description                   |
| ----------------- | --------- | ----------------------------- |
| `focused`         | `boolean` | Whether the window is focused |
| `visibilityState` | `string`  | `"visible" \| "hidden"`       |

| Method          | Returns                         | Description      |
| --------------- | ------------------------------- | ---------------- |
| `focus()`       | `Promise<WindowClient>`         | Focus the window |
| `navigate(url)` | `Promise<WindowClient \| null>` | Navigate to URL  |
