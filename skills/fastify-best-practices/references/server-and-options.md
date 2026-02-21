# Server Factory & Options

## Table of Contents

- [Factory: fastify(options)](#factory-fastifyoptions)
  - [Core options](#core-options)
  - [Router options](#router-options)
  - [Security options](#security-options)
  - [Validation/serialization options](#validationserialization-options)
  - [Advanced options](#advanced-options)
- [Key server methods](#key-server-methods)
- [Key properties](#key-properties)
- [Graceful shutdown pattern](#graceful-shutdown-pattern)

## Factory: `fastify(options)`

### Core options

| Option                  | Type                  | Default         | Description                                      |
| ----------------------- | --------------------- | --------------- | ------------------------------------------------ |
| `logger`                | bool/object           | `false`         | Pino logger config. `true` enables with defaults |
| `loggerInstance`        | object                | —               | Custom Pino-compatible logger instance           |
| `disableRequestLogging` | bool/fn               | `false`         | Disable auto request/response logging            |
| `trustProxy`            | bool/string/number/fn | `false`         | Trust X-Forwarded-\* headers                     |
| `bodyLimit`             | number                | `1048576` (1MB) | Max request body bytes                           |
| `maxParamLength`        | number                | 100             | Max URL parameter length                         |
| `pluginTimeout`         | number                | `10000`         | Max ms for plugin load                           |
| `requestTimeout`        | number                | `0`             | Max ms to receive full request                   |
| `connectionTimeout`     | number                | `0`             | Socket timeout ms                                |
| `keepAliveTimeout`      | number                | `72000`         | HTTP/1 keep-alive timeout ms                     |
| `requestIdHeader`       | string                | `'request-id'`  | Header for request ID                            |
| `genReqId`              | fn(rawReq)            | auto-increment  | Custom request ID generator                      |

### Router options

| Option                   | Type | Default | Description                          |
| ------------------------ | ---- | ------- | ------------------------------------ |
| `caseSensitive`          | bool | `true`  | Case-sensitive route matching        |
| `ignoreTrailingSlash`    | bool | `false` | Match `/foo` and `/foo/`             |
| `ignoreDuplicateSlashes` | bool | `false` | Treat `//` as `/`                    |
| `exposeHeadRoutes`       | bool | `true`  | Auto-create HEAD for GET routes      |
| `return503OnClosing`     | bool | `true`  | 503 for new requests during shutdown |

### Security options

| Option                   | Type   | Default   | Description                                                 |
| ------------------------ | ------ | --------- | ----------------------------------------------------------- |
| `onProtoPoisoning`       | string | `'error'` | Handle `__proto__` in JSON: `'error'`/`'remove'`/`'ignore'` |
| `onConstructorPoisoning` | string | `'error'` | Handle `constructor` in JSON                                |

### Validation/serialization options

| Option           | Type   | Default | Description                             |
| ---------------- | ------ | ------- | --------------------------------------- |
| `ajv`            | object | —       | `{ customOptions, plugins }` for Ajv v8 |
| `serializerOpts` | object | —       | fast-json-stringify options             |

### Advanced options

| Option              | Type    | Default | Description                   |
| ------------------- | ------- | ------- | ----------------------------- |
| `http2`             | bool    | `false` | Enable HTTP/2                 |
| `https`             | object  | —       | TLS options                   |
| `serverFactory`     | fn      | —       | Custom HTTP server factory    |
| `rewriteUrl`        | fn(req) | —       | Rewrite request URL           |
| `querystringParser` | fn      | —       | Custom query string parser    |
| `frameworkErrors`   | fn      | —       | Handle framework-level errors |

## Key server methods

```
.listen({ port, host })          → Start server (returns Promise)
.close()                         → Graceful shutdown (returns Promise)
.ready()                         → Wait for plugins to load (returns Promise)
.inject(request)                 → Fake HTTP request for testing (returns Promise)

.register(plugin, opts?)         → Register plugin (creates new scope)
.addHook(name, handler)          → Add lifecycle hook
.route(options)                  → Add route (full form)
.get/post/put/delete/patch(...)  → Add route (shorthand)

.decorate(name, value)           → Decorate server instance
.decorateRequest(name, value)    → Decorate Request prototype
.decorateReply(name, value)      → Decorate Reply prototype
.hasDecorator(name)              → Check if decorator exists

.addSchema({ $id, ... })         → Add reusable JSON schema
.getSchema(id)                   → Retrieve schema by $id
.getSchemas()                    → Get all schemas (encapsulation-aware)

.setErrorHandler(fn)             → Set custom error handler
.setNotFoundHandler(fn)          → Set custom 404 handler
.setValidatorCompiler(fn)        → Set schema validator compiler
.setSerializerCompiler(fn)       → Set response serializer compiler

.addContentTypeParser(type, fn)  → Register custom content-type parser
.hasContentTypeParser(type)      → Check if parser exists

.printRoutes()                   → Print route tree (debugging)
.printPlugins()                  → Print plugin tree (debugging)
.addresses()                     → Get listening addresses [{port, family, address}]
```

## Key properties

```
.server          → Node.js HTTP/HTTPS server instance
.log             → Pino logger instance
.prefix          → Current route prefix (scoped to plugin)
.pluginName      → Current plugin name (root = 'fastify')
.version         → Fastify version string
.initialConfig   → Frozen read-only initial options
.listeningOrigin → Current listening address string
```

## Graceful shutdown pattern

```ts
const signals = ["SIGTERM", "SIGINT"];
for (const signal of signals) {
  process.on(signal, async () => {
    fastify.log.info(`Received ${signal}, shutting down...`);
    await fastify.close();
    process.exit(0);
  });
}
```
