# Plugins & Encapsulation

## Table of Contents

- [Creating a plugin](#creating-a-plugin)
- [Registering plugins](#registering-plugins)
- [fastify-plugin wrapper](#fastify-plugin-wrapper)
  - [When to use fastify-plugin](#when-to-use-fastify-plugin)
- [Encapsulation rules](#encapsulation-rules)
- [Plugin structure pattern](#plugin-structure-pattern)
- [Plugin timeout](#plugin-timeout)
- [Checking plugin registration](#checking-plugin-registration)
- [Gotchas](#gotchas)

## Creating a plugin

**Callback plugin (FastifyPluginCallback -- project convention):**

```ts
import type { FastifyPluginCallback } from "fastify";

const myPlugin: FastifyPluginCallback = (fastify, opts, done) => {
  fastify.decorate("myService", new MyService(opts));
  done();
};
```

**Async plugin:**

```ts
async function myPlugin(fastify, opts) {
  fastify.decorate("myService", new MyService(opts));
  fastify.get("/my-route", async (request) => {
    return fastify.myService.getData();
  });
}
```

## Registering plugins

```ts
fastify.register(myPlugin, { option1: "value" });

// With prefix (all routes inside get this prefix)
fastify.register(myPlugin, { prefix: "/api/v1" });
```

## fastify-plugin wrapper

By default, `register()` creates a **new encapsulation scope**. Decorators, hooks, and schemas registered inside are invisible to the parent and siblings.

**Use `fastify-plugin` to break encapsulation** and share state with the parent:

```ts
import fp from "fastify-plugin";

export default fp(myPlugin, {
  name: "my-plugin", // for hasPlugin() checks
  fastify: "5.x", // version constraint
  dependencies: ["other-plugin"], // require other plugins first
});
```

### When to use fastify-plugin

| Scenario                           | Use fp? | Why                             |
| ---------------------------------- | ------- | ------------------------------- |
| Shared service (DB, Redis, auth)   | Yes     | Parent and siblings need access |
| Scoped routes (e.g., `/admin/*`)   | No      | Routes stay isolated            |
| Decorating request/reply           | Yes     | Available to all routes         |
| Adding application hooks           | Yes     | Hooks apply globally            |
| Feature module with its own routes | No      | Encapsulation is desired        |

## Encapsulation rules

```
Root context (parent)
├── Plugin A (registered with fp → shares with root)
│   └── decorators visible to root and siblings
├── Plugin B (registered WITHOUT fp → scoped)
│   ├── decorators invisible to root and Plugin A
│   └── BUT can see root decorators (inheritance flows DOWN)
└── Plugin C
    └── can see root + Plugin A decorators
    └── cannot see Plugin B decorators
```

**Key rules:**

1. Child contexts inherit from parent (decorators, hooks, schemas)
2. Parent contexts CANNOT see child decorators/hooks
3. `fastify-plugin` makes child behave as if registered in parent scope
4. Hooks always execute parent-first, then child
5. Same decorator name in different scopes = OK (no collision)

## Plugin structure pattern

Order inside a plugin: **decorators → hooks → routes**

```ts
import fp from "fastify-plugin";

export default fp(
  async (fastify, opts) => {
    // 1. Decorators first
    fastify.decorate("db", await connectDB(opts.dbUrl));

    // 2. Hooks second
    fastify.addHook("onClose", async () => {
      await fastify.db.close();
    });

    // 3. Routes last (if any)
    fastify.get("/health", async () => ({ status: "ok" }));
  },
  { name: "database" },
);
```

## Plugin timeout

Default: 10 seconds. If a plugin takes longer to load, Fastify throws `FST_ERR_PLUGIN_TIMEOUT`.

Fix: set `pluginTimeout: 0` on the Fastify instance to disable, or increase the timeout.

## Checking plugin registration

```ts
fastify.hasPlugin("my-plugin"); // true if registered (uses fp name)
```

## Gotchas

- **Lint errors with async plugin signatures**: See CLAUDE.md for why callback plugins avoid the `require-await` lint issue
- **Plugin options are scoped**: `prefix`, `logLevel`, `logSerializers` are ignored when using `fastify-plugin`
- **Decorator reference types**: `decorateRequest("data", {})` shares one object across ALL requests. Use `null` + `onRequest` hook instead
- **await register**: You can `await fastify.register(plugin)` for sequencing, but the plugin still loads in its own tick
