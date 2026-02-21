# ioredis Advanced Patterns Reference

## Table of Contents

- [Streams (XADD/XREAD)](#streams)
- [Auto-pipelining](#auto-pipelining)
- [Lua scripting details](#lua-scripting-details)
- [Argument and reply transformers](#argument-and-reply-transformers)
- [Binary data](#binary-data)
- [Key prefixing](#key-prefixing)
- [Monitor mode](#monitor-mode)
- [Error handling](#error-handling)
- [Debugging](#debugging)

## Streams

Redis Streams (v5+) for event streaming and log-like data:

```ts
// Producer:
await redis.xadd("mystream", "*", "field1", "value1", "field2", "value2");

// Consumer (blocking read):
async function listenForMessage(lastId = "$") {
  const results = await redis.xread("BLOCK", 0, "STREAMS", "mystream", lastId);
  const [key, messages] = results[0];
  // messages: Array<[id, [field1, value1, field2, value2]]>

  for (const [id, fields] of messages) {
    console.log("Id:", id, "Data:", fields);
  }

  // Continue from the last received ID:
  const lastMsg = messages[messages.length - 1];
  await listenForMessage(lastMsg[0]);
}

listenForMessage();
```

Consumer groups:

```ts
// Create group:
await redis.xgroup("CREATE", "mystream", "mygroup", "0", "MKSTREAM");

// Read as consumer:
const results = await redis.xreadgroup(
  "GROUP",
  "mygroup",
  "consumer1",
  "COUNT",
  10,
  "BLOCK",
  5000,
  "STREAMS",
  "mystream",
  ">",
);

// Acknowledge:
await redis.xack("mystream", "mygroup", messageId);
```

## Auto-pipelining

Automatically batches all commands issued in the same event loop tick into a single pipeline:

```ts
const redis = new Redis({ enableAutoPipelining: true });

// These three commands from the same tick are sent as one pipeline:
const [a, b, c] = await Promise.all([redis.get("key1"), redis.get("key2"), redis.get("key3")]);
```

Performance: 35-50% throughput improvement in benchmarks.

In Cluster mode, one pipeline per node is created. Commands are routed by slot.

Exclude specific commands from auto-pipelining:

```ts
const redis = new Redis({
  enableAutoPipelining: true,
  autoPipeliningIgnoredCommands: ["subscribe", "unsubscribe"],
});
```

## Lua scripting details

### defineCommand

```ts
redis.defineCommand("mycommand", {
  numberOfKeys: 2,
  lua: `
    local key1 = KEYS[1]
    local key2 = KEYS[2]
    local arg1 = ARGV[1]
    return redis.call('SET', key1, arg1)
  `,
});

// Use:
await redis.mycommand("k1", "k2", "value");

// Buffer variant is auto-created:
await redis.mycommandBuffer("k1", "k2", "value");

// Works with pipeline:
await redis.pipeline().mycommand("k1", "k2", "value").exec();
```

### Dynamic key count

Omit `numberOfKeys` and pass it as the first argument each time:

```ts
redis.defineCommand("dynamicScript", {
  lua: "return {KEYS[1], ARGV[1]}",
});

await redis.dynamicScript(1, "mykey", "myarg"); // 1 = numberOfKeys
```

### Constructor option

```ts
const redis = new Redis({
  scripts: {
    mycommand: {
      numberOfKeys: 2,
      lua: "return {KEYS[1],KEYS[2],ARGV[1]}",
      readOnly: true, // Hint for Cluster read-write splitting
    },
  },
});
```

ioredis uses EVALSHA internally and falls back to EVAL only when the script is not cached.

### TypeScript typing

For TypeScript projects, declare custom commands on the Redis interface:

```ts
declare module "ioredis" {
  interface RedisCommander<Context> {
    mycommand(key1: string, key2: string, arg1: string): Result<string, Context>;
  }
}
```

## Argument and reply transformers

Transform command arguments or replies globally:

```ts
import { Redis } from "ioredis";

// Built-in: hmset accepts objects:
await redis.hmset("hash", { field1: "val1", field2: "val2" });
// Equivalent to: HMSET hash field1 val1 field2 val2

// Built-in: hgetall returns object:
const hash = await redis.hgetall("hash");
// { field1: "val1", field2: "val2" }

// Built-in: mset accepts objects:
await redis.mset({ k1: "v1", k2: "v2" });

// Custom argument transformer:
Redis.Command.setArgumentTransformer("hmset", (args) => {
  if (args.length === 2 && typeof args[1] === "object") {
    const flat = [];
    for (const [k, v] of Object.entries(args[1])) {
      flat.push(k, v);
    }
    return [args[0], ...flat];
  }
  return args;
});

// Custom reply transformer:
Redis.Command.setReplyTransformer("hgetall", (result) => {
  if (Array.isArray(result)) {
    const obj: Record<string, string> = {};
    for (let i = 0; i < result.length; i += 2) {
      obj[result[i]] = result[i + 1];
    }
    return obj;
  }
  return result;
});
```

## Binary data

Send binary data with Buffers:

```ts
await redis.set("binary", Buffer.from([0x62, 0x75, 0x66]));

// Use Buffer variant to receive binary:
const buf = await redis.getBuffer("binary");
// buf: <Buffer 62 75 66>

// Every bulk-string command has a Buffer variant:
// getBuffer, hgetallBuffer, lrangeBuffer, etc.

// You don't need setBuffer — regular set() accepts Buffers:
await redis.set("key", Buffer.from("hello"));
```

## Key prefixing

Auto-prefix all keys transparently:

```ts
const redis = new Redis({ keyPrefix: "app:" });

await redis.set("user:1", "Alice");
// Actually sends: SET app:user:1 Alice

await redis.get("user:1");
// Actually sends: GET app:user:1

// Works with pipeline and custom commands:
redis
  .pipeline()
  .set("k1", "v1") // SET app:k1 v1
  .get("k1") // GET app:k1
  .exec();
```

**Limitation**: Does not apply to pattern-based commands like `KEYS`, `SCAN`, or to reply values that happen to be key names.

## Monitor mode

See all commands received by the server across all clients:

```ts
const monitor = await redis.monitor();

monitor.on("monitor", (time, args, source, database) => {
  // time: Unix timestamp from Redis
  // args: command arguments array
  // source: client address
  // database: database number
  console.log(time, args.join(" "), "from", source);
});

// When done:
monitor.disconnect();
```

A monitor connection cannot run other commands.

## Error handling

All Redis server errors are `ReplyError` instances:

```ts
import { Redis } from "ioredis";

try {
  await redis.set("foo"); // wrong number of args
} catch (err) {
  if (err instanceof Redis.ReplyError) {
    console.log(err.message); // "ERR wrong number of arguments for 'set' command"
  }
}
```

### Friendly error stacks (dev only)

```ts
// Default stack: internal ioredis frames (useless for debugging)
// Friendly stack: points to your code

const redis = new Redis({ showFriendlyErrorStack: true });
// NEVER use in production — significant performance overhead
```

### Pipeline error handling

`pipeline.exec()` never rejects. Each command's result is `[error, value]`:

```ts
const results = await redis.pipeline().set("foo", "bar").get("nonexistent").exec();

// results[0] = [null, "OK"]     — success
// results[1] = [null, null]     — key doesn't exist (not an error)

// If a command fails:
// results[N] = [ReplyError, undefined]
```

## Debugging

Enable debug logging via the DEBUG environment variable:

```bash
DEBUG=ioredis:* node app.js
```

Prefix patterns:

- `ioredis:*` — all logs
- `ioredis:redis` — connection/command logs
- `ioredis:cluster` — cluster-specific logs
- `ioredis:sentinel` — sentinel-specific logs
