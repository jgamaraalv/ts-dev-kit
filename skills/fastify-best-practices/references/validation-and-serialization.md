# Validation & Serialization

## Table of Contents

- [Request validation (JSON Schema + Ajv v8)](#request-validation-json-schema--ajv-v8)
  - [Ajv defaults](#ajv-defaults)
  - [Customizing Ajv](#customizing-ajv)
- [Response serialization (fast-json-stringify)](#response-serialization-fast-json-stringify)
- [Schema reuse with $ref](#schema-reuse-with-ref)
- [Custom validator compiler (e.g., Zod)](#custom-validator-compiler-eg-zod)
- [Error formatting](#error-formatting)
- [Gotchas](#gotchas)

## Request validation (JSON Schema + Ajv v8)

Fastify validates request data against JSON Schema. Invalid requests get **400** automatically.

```ts
fastify.post("/users", {
  schema: {
    body: {
      type: "object",
      required: ["email"],
      properties: {
        email: { type: "string", format: "email" },
        name: { type: "string", minLength: 1, maxLength: 100 },
        age: { type: "integer", minimum: 0 },
      },
      additionalProperties: false,
    },
    querystring: {
      type: "object",
      properties: {
        page: { type: "integer", default: 1 },
        limit: { type: "integer", default: 20, maximum: 100 },
      },
    },
    params: {
      type: "object",
      properties: {
        id: { type: "string", format: "uuid" },
      },
    },
    headers: {
      type: "object",
      properties: {
        "x-api-key": { type: "string" },
      },
      required: ["x-api-key"],
    },
  },
  handler: async (request, reply) => { ... },
});
```

### Ajv defaults

Fastify configures Ajv with:

- `coerceTypes: true` — strings coerced to numbers/booleans for query/params
- `removeAdditional: true` — extra properties stripped
- `useDefaults: true` — missing properties get defaults
- `allErrors: false` — stops at first error (faster)

### Customizing Ajv

```ts
const fastify = Fastify({
  ajv: {
    customOptions: {
      allErrors: true, // return all errors
      removeAdditional: "all", // strip all extra properties
    },
    plugins: [ajvFormats], // add format validators
  },
});
```

## Response serialization (fast-json-stringify)

Define response schemas per status code. Fastify uses `fast-json-stringify` for 2-5x faster serialization than `JSON.stringify`, and it **prevents leaking fields** not in the schema.

```ts
schema: {
  response: {
    200: {
      type: "object",
      properties: {
        id: { type: "string" },
        email: { type: "string" },
      },
    },
    "4xx": {
      type: "object",
      properties: {
        error: { type: "string" },
        message: { type: "string" },
      },
    },
    default: {
      type: "object",
      properties: {
        error: { type: "string" },
      },
    },
  },
}
```

## Schema reuse with $ref

**Register shared schemas:**

```ts
fastify.addSchema({
  $id: "user",
  type: "object",
  properties: {
    id: { type: "string" },
    email: { type: "string" },
    name: { type: "string" },
  },
});

fastify.addSchema({
  $id: "pagination",
  type: "object",
  properties: {
    page: { type: "integer", default: 1 },
    limit: { type: "integer", default: 20 },
    total: { type: "integer" },
  },
});
```

**Reference in routes:**

```ts
schema: {
  response: {
    200: { $ref: "user#" },           // whole schema
  },
}

// Or reference properties:
schema: {
  body: {
    type: "object",
    properties: {
      user: { $ref: "user#" },
      meta: { $ref: "pagination#" },
    },
  },
}
```

## Custom validator compiler (e.g., Zod)

```ts
import { serializerCompiler, validatorCompiler } from "fastify-type-provider-zod";

fastify.setValidatorCompiler(validatorCompiler);
fastify.setSerializerCompiler(serializerCompiler);

// Then in routes:
fastify.post("/users", {
  schema: {
    body: z.object({ email: z.string().email(), name: z.string() }),
    response: { 201: z.object({ id: z.string(), email: z.string() }) },
  },
  handler: async (request) => { ... },
});
```

## Error formatting

```ts
fastify.setSchemaErrorFormatter((errors, dataVar) => {
  const message = errors.map((e) => `${dataVar}${e.instancePath} ${e.message}`).join("; ");
  return new Error(message);
});
```

## Gotchas

- **No response schema = slow + leaky** — `JSON.stringify()` is used, and all object properties are included
- **`additionalProperties: false`** is important — without it, extra fields pass validation
- **Ajv formats** (`email`, `uuid`, `date-time`, etc.) require `ajv-formats` plugin
- **Schema compilation** happens at startup — errors are thrown during `.listen()`, not at runtime
- **Shared schemas** are encapsulation-aware — schemas in child plugins are invisible to parents unless using `fastify-plugin`
