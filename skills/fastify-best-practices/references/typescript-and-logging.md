# TypeScript & Logging

## Table of Contents

- [TypeScript Patterns](#typescript-patterns)
  - [Route generics](#route-generics)
  - [Type providers (Zod integration)](#type-providers-zod-integration)
  - [Augmenting FastifyInstance (custom decorators)](#augmenting-fastifyinstance-custom-decorators)
  - [Plugin typing](#plugin-typing)
  - [Decorator typing gotchas](#decorator-typing-gotchas)
  - [Import style (ESM)](#import-style-esm)
- [Logging with Pino](#logging-with-pino)
  - [Basic setup](#basic-setup)
  - [Development (pretty printing)](#development-pretty-printing)
  - [Production recommendations](#production-recommendations)
  - [Disable request logging](#disable-request-logging)
  - [Request-scoped logging](#request-scoped-logging)
  - [Custom request ID](#custom-request-id)

## TypeScript Patterns

## Route generics

Type request parts using generics:

```ts
interface CreateUserBody {
  email: string;
  name: string;
}

interface UserParams {
  id: string;
}

interface UserQuery {
  include?: string;
}

fastify.post<{
  Body: CreateUserBody;
  Params: UserParams;
  Querystring: UserQuery;
  Headers: { "x-api-key": string };
}>("/users/:id", async (request) => {
  request.body.email; // typed as string
  request.params.id; // typed as string
  request.query.include; // typed as string | undefined
});
```

## Type providers (Zod integration)

```ts
import Fastify from "fastify";
import { serializerCompiler, validatorCompiler, ZodTypeProvider } from "fastify-type-provider-zod";
import { z } from "zod";

const fastify = Fastify().withTypeProvider<ZodTypeProvider>();
fastify.setValidatorCompiler(validatorCompiler);
fastify.setSerializerCompiler(serializerCompiler);

fastify.post(
  "/users",
  {
    schema: {
      body: z.object({ email: z.string().email() }),
      response: { 201: z.object({ id: z.string() }) },
    },
  },
  async (request) => {
    request.body.email; // inferred from Zod schema
    return { id: "123" };
  },
);
```

## Augmenting FastifyInstance (custom decorators)

```ts
declare module "fastify" {
  interface FastifyInstance {
    db: Pool;
    redis: Redis;
  }
  interface FastifyRequest {
    user?: { id: string; email: string };
  }
}
```

## Plugin typing

See [plugins-and-encapsulation.md](plugins-and-encapsulation.md) for the full `FastifyPluginCallback` and `FastifyPluginAsync` patterns.

**Quick reference for type annotations:**

```ts
import type { FastifyPluginCallback, FastifyPluginAsync } from "fastify";
```

## Logging with Pino

## Pino logging configuration

### Basic setup

```ts
const fastify = Fastify({
  logger: true, // default Pino with info level
});

// Or with options:
const fastify = Fastify({
  logger: {
    level: "info",
  },
});
```

### Development (pretty printing)

```ts
const fastify = Fastify({
  logger: {
    level: "debug",
    transport: {
      target: "pino-pretty",
      options: {
        translateTime: "HH:MM:ss Z",
        ignore: "pid,hostname",
      },
    },
  },
});
```

### Production recommendations

```ts
const fastify = Fastify({
  logger: {
    level: process.env.LOG_LEVEL ?? "info",
    // Redact sensitive data
    redact: ["req.headers.authorization", "req.headers.cookie"],
    serializers: {
      req(request) {
        return {
          method: request.method,
          url: request.url,
          hostname: request.hostname,
          remoteAddress: request.ip,
        };
      },
    },
  },
});
```

### Disable request logging

```ts
const fastify = Fastify({
  disableRequestLogging: true, // no auto req/res logs
});

// Or conditionally:
const fastify = Fastify({
  disableRequestLogging: (req) => req.url === "/health",
});
```

### Request-scoped logging

Every request has `request.log` — a child logger with `reqId` bound:

```ts
fastify.get("/", async (request) => {
  request.log.info("processing request"); // includes reqId
  request.log.info({ userId: 123 }, "user found"); // structured data
});
```

### Custom request ID

```ts
const fastify = Fastify({
  requestIdHeader: "x-request-id", // read from header
  genReqId: (req) => crypto.randomUUID(), // or generate
  requestIdLogLabel: "reqId", // log field name
});
```

## Decorator typing gotchas

**Wrong — shared reference:**

```ts
fastify.decorateRequest("data", {}); // ALL requests share same object!
```

**Right — null initial + onRequest assignment:**

```ts
fastify.decorateRequest("user", null);

fastify.addHook("onRequest", async (request) => {
  request.user = await getUser(request); // unique per request
});
```

## Import style (ESM)

```ts
// Fastify:
import Fastify from "fastify";
import type { FastifyInstance, FastifyRequest, FastifyReply } from "fastify";

// fastify-plugin:
import fp from "fastify-plugin";
```

> **ioredis**: See CLAUDE.md for the canonical ioredis import convention (`import { Redis } from "ioredis"`).
