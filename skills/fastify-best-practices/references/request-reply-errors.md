# Request, Reply & Error Handling

## Table of Contents

- [Request object](#request-object)
  - [Key properties](#key-properties)
  - [Methods](#methods)
- [Reply object](#reply-object)
  - [Key methods](#key-methods)
  - [Key properties](#key-properties-1)
- [Error handling](#error-handling)
  - [Default behavior](#default-behavior)
  - [Custom error handler](#custom-error-handler)
  - [Creating errors with status codes](#creating-errors-with-status-codes)
  - [Error handler scoping](#error-handler-scoping)
  - [Key FST_ERR codes](#key-fst_err-codes)
  - [404 handler](#404-handler)
- [Gotchas](#gotchas)

## Request object

### Key properties

| Property       | Type            | Description                     |
| -------------- | --------------- | ------------------------------- |
| `query`        | object          | Parsed query string             |
| `body`         | any             | Parsed request body             |
| `params`       | object          | URL parameters                  |
| `headers`      | object          | Request headers                 |
| `raw`          | IncomingMessage | Node.js raw request             |
| `id`           | string          | Request ID                      |
| `ip`           | string          | Client IP (respects trustProxy) |
| `ips`          | string[]        | Proxy chain IPs                 |
| `hostname`     | string          | Host from header                |
| `protocol`     | string          | `http` or `https`               |
| `method`       | string          | HTTP method                     |
| `url`          | string          | Request URL                     |
| `routeOptions` | object          | Route config, schema, bodyLimit |
| `server`       | FastifyInstance | Fastify instance                |
| `log`          | Logger          | Request-scoped Pino logger      |
| `is404`        | boolean         | True if no route matched        |

### Methods

```ts
request.getValidationFunction("body"); // get compiled validator
request.validateInput(data, "querystring"); // validate arbitrary data
```

## Reply object

### Key methods

```ts
reply.code(201); // set status code (chainable)
reply.status(201); // alias for .code()
reply.header("X-Custom", "val"); // set single header (chainable)
reply.headers({ k: "v" }); // set multiple headers
reply.type("application/json"); // set Content-Type (chainable)
reply.redirect("/new-url"); // redirect (302 default)
reply.redirect("/url", 301); // redirect with status

reply.send(payload); // send response
// payload can be: object, string, Buffer, Stream, Error, null

reply.hijack(); // take over response (skips serialization + onSend)
reply.callNotFound(); // invoke 404 handler

reply.serialize(payload); // serialize using route's serializer
reply.serializer(fn); // set custom serializer for this reply

reply.getHeader("key"); // get response header
reply.hasHeader("key"); // check header exists
reply.removeHeader("key"); // remove header
```

### Key properties

| Property      | Type            | Description               |
| ------------- | --------------- | ------------------------- |
| `statusCode`  | number          | Current status code       |
| `sent`        | boolean         | True after response sent  |
| `elapsedTime` | number          | Ms since request received |
| `raw`         | ServerResponse  | Node.js raw response      |
| `request`     | Request         | Associated request        |
| `server`      | FastifyInstance | Fastify instance          |

## Error handling

### Default behavior

Fastify catches errors from:

- Sync `throw` in handler
- Rejected promise in async handler
- `done(error)` in callback handler

Default error response:

```json
{ "statusCode": 500, "error": "Internal Server Error", "message": "..." }
```

### Custom error handler

```ts
fastify.setErrorHandler((error, request, reply) => {
  request.log.error(error);

  // Validation errors
  if (error.validation) {
    return reply.code(400).send({
      error: "Validation Error",
      message: error.message,
      details: error.validation,
    });
  }

  // Custom app errors
  const statusCode = error.statusCode ?? 500;
  reply.code(statusCode).send({
    error: statusCode >= 500 ? "Internal Server Error" : error.message,
    statusCode,
  });
});
```

### Creating errors with status codes

```ts
// Option 1: Set statusCode on Error
const err = new Error("Not found");
err.statusCode = 404;
throw err;

// Option 2: reply.send(error) with code
reply.code(404).send(new Error("Not found"));

// Option 3: Use http-errors
import createError from "http-errors";
throw createError(404, "User not found");
```

### Error handler scoping

Error handlers are encapsulated. A plugin can set its own error handler:

```ts
fastify.register(async (instance) => {
  instance.setErrorHandler((error, request, reply) => {
    // handles errors only for routes in this plugin
  });
});
```

If a new error is thrown inside an error handler, the **parent** error handler handles it.

### Key FST_ERR codes

| Code                         | Description                  |
| ---------------------------- | ---------------------------- |
| `FST_ERR_CTP_BODY_TOO_LARGE` | Body exceeds bodyLimit       |
| `FST_ERR_VALIDATION`         | Schema validation failed     |
| `FST_ERR_BAD_STATUS_CODE`    | Invalid HTTP status code     |
| `FST_ERR_REP_ALREADY_SENT`   | Reply already sent           |
| `FST_ERR_HOOK_TIMEOUT`       | Hook timed out               |
| `FST_ERR_PLUGIN_TIMEOUT`     | Plugin took too long to load |
| `FST_ERR_DUPLICATED_ROUTE`   | Route already registered     |

Access: `import { errorCodes } from "fastify"` → check with `instanceof`.

### 404 handler

```ts
fastify.setNotFoundHandler((request, reply) => {
  reply.code(404).send({ error: "Not Found", message: `Route ${request.url} not found` });
});

// With preHandler hooks:
fastify.setNotFoundHandler({ preHandler: [authHook] }, handler);
```

## Gotchas

- **reply.send() in async**: always `return reply.send()` or `return reply` — otherwise Fastify also sends the return value
- **reply.sent**: check this before sending to avoid `FST_ERR_REP_ALREADY_SENT`
- **reply.hijack()**: use for SSE, WebSockets — Fastify won't touch the response after this
- **Error objects only**: `reply.send("string error")` sends as plain text, not through error handler. Always send `Error` instances
- **Streams**: if a stream errors after headers are sent, Fastify can't change the status code
