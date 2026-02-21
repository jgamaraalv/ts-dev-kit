# Routes & Handlers

## Table of Contents

- [Route declaration](#route-declaration)
- [URL parameters](#url-parameters)
- [Async handler patterns](#async-handler-patterns)
- [Route-level config](#route-level-config)
- [Route constraints](#route-constraints)
- [Gotchas](#gotchas)

## Route declaration

**Full form:**

```ts
fastify.route({
  method: "GET",           // or ["GET", "POST"]
  url: "/users/:id",
  schema: { ... },         // validation + serialization
  handler: async (request, reply) => { ... },
  // Optional hooks (run AFTER app-level hooks):
  onRequest: [fn],
  preHandler: [fn],
  preSerialization: [fn],
  onSend: [fn],
  onResponse: [fn],
  onError: [fn],
  onTimeout: [fn],
  // Options:
  config: { ... },         // access via reply.routeOptions.config
  bodyLimit: 1048576,
  logLevel: "warn",
  constraints: { version: "1.0.0", host: "example.com" },
});
```

**Shorthand:**

```ts
fastify.get(url, [options], handler);
fastify.post(url, [options], handler);
fastify.put(url, [options], handler);
fastify.delete(url, [options], handler);
fastify.patch(url, [options], handler);
fastify.head(url, [options], handler);
fastify.options(url, [options], handler);
fastify.all(url, [options], handler); // all HTTP methods
```

## URL parameters

```ts
// Parametric
fastify.get("/users/:id", handler); // request.params.id

// Multiple params
fastify.get("/users/:id/posts/:postId", handler);

// Optional param
fastify.get("/posts/:id?", handler); // id is optional

// Wildcard (catch-all)
fastify.get("/files/*", handler); // request.params["*"]

// Multi-param with separators
fastify.get("/near/:lat-:lng/radius/:r", handler);

// Regex (expensive — avoid on hot paths)
fastify.get("/file/:name(^\\d+).png", handler);

// Escape colon (literal colon)
fastify.post("/name::verb"); // matches /name:verb
```

## Async handler patterns

**Return value (preferred):**

```ts
fastify.get("/", async (request, reply) => {
  const data = await getData();
  return data; // auto-sends with 200
});
```

**With status code:**

```ts
fastify.post("/", async (request, reply) => {
  const user = await createUser(request.body);
  return reply.code(201).send(user);
});
```

**Deferred reply (callback outside promise chain):**

```ts
fastify.get("/", async (request, reply) => {
  setImmediate(() => reply.send({ hello: "world" }));
  await reply; // MUST await reply when sending outside promise
});
```

## Route-level config

Access custom config via `reply.routeOptions.config`:

```ts
fastify.get("/hello", { config: { greeting: "Hi!" } }, (req, reply) => {
  reply.send(reply.routeOptions.config.greeting);
});
```

## Route constraints

```ts
// Version constraint (requires Accept-Version header)
fastify.get("/", { constraints: { version: "1.0.0" } }, handlerV1);
fastify.get("/", { constraints: { version: "2.0.0" } }, handlerV2);

// Host constraint
fastify.get("/", { constraints: { host: "api.example.com" } }, handler);
```

## Gotchas

- **Don't mix async + callback** — pick one pattern per handler
- **Don't return undefined** in async handlers (Fastify waits for response)
- **Arrow functions** don't bind `this` to Fastify instance — use `function` if you need `this`
- **Regex params** hurt routing performance — use sparingly
- **Multiple params per path segment** (`:lat-:lng`) reduce router perf
- **HEAD routes** auto-created from GET unless you define HEAD first; disable with `exposeHeadRoutes: false`
- **Version constraints** require `Accept-Version` header in requests; add `Vary` header to prevent cache poisoning
