# Hooks & Lifecycle

## Table of Contents

- [Request/Reply hooks (in execution order)](#requestreply-hooks-in-execution-order)
- [Application hooks](#application-hooks)
- [Hook signatures](#hook-signatures)
- [Early response pattern](#early-response-pattern)
- [Scope rules](#scope-rules)
- [Common patterns](#common-patterns)
- [Gotchas](#gotchas)

## Request/Reply hooks (in execution order)

| Hook               | Signature                   | When                                                                  | Can modify response?        |
| ------------------ | --------------------------- | --------------------------------------------------------------------- | --------------------------- |
| `onRequest`        | `(request, reply)`          | First hook; body is `undefined`                                       | Yes                         |
| `preParsing`       | `(request, reply, payload)` | Before body parsing; receives raw stream                              | Yes (return new stream)     |
| `preValidation`    | `(request, reply)`          | After parsing, before schema validation                               | Yes                         |
| `preHandler`       | `(request, reply)`          | After validation, before handler                                      | Yes                         |
| _handler_          | `(request, reply)`          | Route handler                                                         | Yes                         |
| `preSerialization` | `(request, reply, payload)` | Before response serialization (skipped for string/buffer/stream/null) | Yes (return new payload)    |
| `onSend`           | `(request, reply, payload)` | Before sending; payload is serialized string/buffer                   | Yes (return new payload)    |
| `onResponse`       | `(request, reply)`          | After response sent                                                   | No                          |
| `onError`          | `(request, reply, error)`   | When error thrown                                                     | No (read-only, for logging) |
| `onTimeout`        | `(request, reply)`          | Request timed out                                                     | No                          |
| `onRequestAbort`   | `(request)`                 | Client closed connection                                              | No                          |

## Application hooks

| Hook         | Signature          | When                                |
| ------------ | ------------------ | ----------------------------------- |
| `onReady`    | `()`               | Before server starts listening      |
| `onListen`   | `()`               | After server starts listening       |
| `preClose`   | `()`               | Before in-flight requests complete  |
| `onClose`    | `(instance)`       | After in-flight requests complete   |
| `onRoute`    | `(routeOptions)`   | New route registered (synchronous!) |
| `onRegister` | `(instance, opts)` | New plugin context created          |

## Hook signatures

**Async (preferred):**

```ts
fastify.addHook("onRequest", async (request, reply) => {
  // do work; throw to abort
});
```

**Callback:**

```ts
fastify.addHook("onRequest", (request, reply, done) => {
  // do work; call done() to continue, done(err) to abort
  done();
});
```

**With payload (preParsing, preSerialization, onSend):**

```ts
fastify.addHook("onSend", async (request, reply, payload) => {
  return modifiedPayload; // must return new payload
});
```

## Early response pattern

Send response from a hook to short-circuit the lifecycle:

```ts
fastify.addHook("onRequest", async (request, reply) => {
  if (!request.headers.authorization) {
    return reply.code(401).send({ error: "Unauthorized" });
    // Remaining hooks and handler are skipped
  }
});
```

In callback style: call `reply.send()` without calling `done()`.

## Scope rules

- **App-level hooks** run for ALL routes (including child plugin routes)
- **Route-level hooks** run AFTER app-level hooks of the same type
- **Encapsulated hooks** only affect routes within the same plugin scope
- **Exception**: `onClose` does NOT respect encapsulation (always global)
- Multiple hooks of the same type: specified as arrays `preHandler: [fn1, fn2]`

## Common patterns

**Request timing:**

```ts
fastify.addHook("onRequest", async (request) => {
  request.startTime = Date.now();
});
fastify.addHook("onResponse", async (request, reply) => {
  request.log.info({ ms: Date.now() - request.startTime }, "request completed");
});
```

**Auth guard (plugin-scoped):**

```ts
function authPlugin(fastify, opts, done) {
  fastify.addHook("onRequest", async (request, reply) => {
    const token = request.headers.authorization;
    if (!token) return reply.code(401).send({ error: "Unauthorized" });
    request.user = await verifyToken(token);
  });
  done();
}
```

## Gotchas

- `onRequest`: body is always `undefined` (parsing hasn't happened yet)
- `onError`: read-only — use `setErrorHandler()` to modify error responses
- `preSerialization`: skipped for strings, buffers, streams, and null payloads
- Don't use async functions with streams in hooks — use callback style
- Hook errors in async: just `throw`; in callback: pass to `done(err)`
