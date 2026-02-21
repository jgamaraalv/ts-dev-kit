# Caching Strategies

## Table of Contents

- [Cache-First (Cache Falling Back to Network)](#cache-first)
- [Network-First (Network Falling Back to Cache)](#network-first)
- [Stale-While-Revalidate](#stale-while-revalidate)
- [Cache-Only](#cache-only)
- [Network-Only](#network-only)
- [Dynamic Caching with Fallback](#dynamic-caching-with-fallback)
- [Cache Versioning and Cleanup](#cache-versioning-and-cleanup)
- [Strategy Selection Guide](#strategy-selection-guide)

## Cache-First

Best for: static assets (CSS, JS, images, fonts) that change infrequently.

```js
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        // Cache new responses for future use
        const clone = response.clone();
        caches.open("static-v1").then((cache) => cache.put(event.request, clone));
        return response;
      });
    }),
  );
});
```

## Network-First

Best for: API calls, frequently updated content, HTML pages.

```js
const networkFirst = async (request, cacheName = "dynamic-v1") => {
  try {
    const response = await fetch(request);
    const cache = await caches.open(cacheName);
    cache.put(request, response.clone()); // update cache in background
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response("Offline", { status: 503, headers: { "Content-Type": "text/plain" } });
  }
};

self.addEventListener("fetch", (event) => {
  if (event.request.url.includes("/api/")) {
    event.respondWith(networkFirst(event.request));
  }
});
```

## Stale-While-Revalidate

Best for: resources where freshness matters but stale content is acceptable briefly (avatars, non-critical API data).

```js
self.addEventListener("fetch", (event) => {
  const cache = caches.open("swr-v1");
  const cached = cache.then((c) => c.match(event.request));
  const fetched = fetch(event.request);
  const fetchedCopy = fetched.then((r) => r.clone());

  // Return cached immediately if available, race with network otherwise
  event.respondWith(
    Promise.race([fetched.catch(() => cached), cached])
      .then((r) => r || fetched)
      .catch(() => new Response("Offline", { status: 503 })),
  );

  // Keep SW alive until the cache is updated with the fresh response
  event.waitUntil(Promise.all([cache, fetchedCopy]).then(([c, r]) => c.put(event.request, r)));
});
```

**Important:** Always use `event.waitUntil()` around the cache update promise. Without it, the SW may terminate before the background fetch completes, and the cache will never be refreshed.

## Cache-Only

Best for: pre-cached assets during install that never change within a version.

```js
self.addEventListener("fetch", (event) => {
  event.respondWith(caches.match(event.request));
});
```

## Network-Only

Best for: non-GET requests, analytics pings, real-time data. Typically just don't call `respondWith()`:

```js
self.addEventListener("fetch", (event) => {
  // Non-GET → let browser handle normally
  if (event.request.method !== "GET") return;
  // Otherwise apply a cache strategy
  event.respondWith(/* ... */);
});
```

## Dynamic Caching with Fallback

Complete pattern combining pre-cache, dynamic cache, and offline fallback:

```js
const CACHE_NAME = "app-v1";
const PRECACHE = ["/", "/offline.html", "/style.css", "/app.js"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE)));
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  event.respondWith(
    (async () => {
      // 1. Check cache
      const cached = await caches.match(event.request);
      if (cached) return cached;

      // 2. Try network
      try {
        const response = await fetch(event.request);
        // Cache successful responses
        if (response.ok) {
          const cache = await caches.open(CACHE_NAME);
          event.waitUntil(cache.put(event.request, response.clone()));
        }
        return response;
      } catch {
        // 3. Offline fallback for navigations
        if (event.request.mode === "navigate") {
          return caches.match("/offline.html");
        }
        return new Response("Offline", { status: 503 });
      }
    })(),
  );
});
```

## Cache Versioning and Cleanup

Increment the cache name on each deploy. Delete stale caches during activate:

```js
const CACHE_VERSION = 2;
const CACHES = {
  static: `static-v${CACHE_VERSION}`,
  dynamic: `dynamic-v${CACHE_VERSION}`,
};

self.addEventListener("activate", (event) => {
  const keep = new Set(Object.values(CACHES));
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => !keep.has(k)).map((k) => caches.delete(k)))),
  );
});
```

## Strategy Selection Guide

| Content type              | Strategy                | Why                                |
| ------------------------- | ----------------------- | ---------------------------------- |
| App shell (HTML, CSS, JS) | Cache-first             | Instant load, update on next visit |
| API responses             | Network-first           | Fresh data, offline fallback       |
| User avatars, thumbnails  | Stale-while-revalidate  | Fast display, background update    |
| Fonts, icons              | Cache-first             | Rarely change                      |
| Analytics, real-time data | Network-only            | Must be fresh, no offline value    |
| Critical offline page     | Cache-only (pre-cached) | Always available                   |

### Per-route strategy pattern

```js
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== "GET") return;

  if (url.origin === location.origin) {
    // Same-origin: cache-first for assets, network-first for HTML
    if (request.destination === "document") {
      event.respondWith(networkFirst(request));
    } else {
      event.respondWith(cacheFirst(request));
    }
  } else {
    // Cross-origin: stale-while-revalidate
    event.respondWith(staleWhileRevalidate(request));
  }
});
```
