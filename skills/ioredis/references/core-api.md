# ioredis Core API Reference

## Quick Start

```ts
const redis = new Redis(); // localhost:6379

// All Redis commands are methods: redis.hset(), redis.zadd(), redis.xadd(), etc.
// Format: redis[commandInLowerCase](...args) — returns Promise
// Buffer variants: redis.getBuffer("key") returns Buffer instead of string
```

## Connection

```ts
new Redis(); // 127.0.0.1:6379
new Redis(6380); // 127.0.0.1:6380
new Redis(6379, "192.168.1.1"); // 192.168.1.1:6379
new Redis("/tmp/redis.sock"); // Unix socket
new Redis("redis://:password@host:6379/0"); // URL (redis:// or rediss://)
new Redis("redis://user:pass@host:6379/4"); // With username (Redis >= 6)

new Redis({
  host: "127.0.0.1",
  port: 6379,
  username: "default", // Redis >= 6 ACL
  password: "secret",
  db: 0, // Database index (default: 0)
  keyPrefix: "app:", // Auto-prefix all keys
  lazyConnect: false, // true = don't connect until first command
  enableReadyCheck: true, // Wait for server to finish loading
  maxRetriesPerRequest: 20, // null = wait forever
  connectTimeout: 10000, // ms
  commandTimeout: undefined, // ms, throws "Command timed out"
  keepAlive: 0, // ms, 0 = disabled
  noDelay: true, // Nagle's algorithm
  connectionName: "my-app", // CLIENT SETNAME
  enableAutoPipelining: false,
  retryStrategy(times) {
    return Math.min(times * 50, 2000); // ms delay, or undefined to stop
  },
});
```

**Full options reference**: See [connection-options.md](connection-options.md)

### TLS

```ts
new Redis({ host: "redis.example.com", tls: {} });
// or
new Redis("rediss://redis.example.com");
// or with CA:
new Redis({ host: "redis.example.com", tls: { ca: fs.readFileSync("cert.pem") } });
```

## Pipeline

Batch commands for 50-300% throughput improvement:

```ts
const pipeline = redis.pipeline();
pipeline.set("foo", "bar");
pipeline.get("foo");
const results = await pipeline.run();
// results === [[null, "OK"], [null, "bar"]]
// Each entry: [error, result]
```

**Note:** The actual method to run a pipeline is `.exec()` — shown as `.run()` here for brevity. In ioredis, both pipelines and transactions use the `.exec()` method to send queued commands to Redis.

## Transaction (multi)

```ts
const tx = redis.multi();
tx.set("foo", "bar");
tx.get("foo");
const results = await tx.exec();
// results === [[null, "OK"], [null, "bar"]]

// Without pipeline (sends immediately):
redis.multi({ pipeline: false });
redis.set("foo", "bar");
redis.get("foo");
await redis.exec();
```

## Pub/Sub

A subscribed connection cannot run other commands. Use separate instances:

```ts
const sub = new Redis();
const pub = new Redis();

await sub.subscribe("channel-1", "channel-2");
sub.on("message", (channel, message) => {
  /* ... */
});
// Also: "messageBuffer" for binary data

pub.publish("channel-1", JSON.stringify({ data: 123 }));
```

## Lua Scripting

```ts
// Define at runtime:
redis.defineCommand("mycommand", {
  numberOfKeys: 2,
  lua: "return {KEYS[1],KEYS[2],ARGV[1],ARGV[2]}",
});
const result = await redis.mycommand("k1", "k2", "a1", "a2");

// Define via constructor:
const redis = new Redis({
  scripts: {
    mycommand: {
      numberOfKeys: 2,
      lua: "return {KEYS[1],KEYS[2],ARGV[1],ARGV[2]}",
    },
  },
});

// Dynamic key count — pass numberOfKeys as first arg:
redis.defineCommand("dynamicCmd", { lua: "return KEYS[1]" });
await redis.dynamicCmd(1, "mykey");
```

## Scan (Streaming)

```ts
const stream = redis.scanStream({ match: "user:*", count: 100 });
stream.on("data", (keys) => {
  // keys: string[], may contain duplicates
  stream.pause();
  processKeys(keys).then(() => stream.resume());
});
stream.on("end", () => console.log("done"));

// Hash/Set/ZSet variants:
redis.hscanStream("myhash", { match: "field:*" });
redis.sscanStream("myset", { match: "*" });
redis.zscanStream("myzset", { match: "*" });
```

## Connection Events

| Event          | Description                                                     |
| -------------- | --------------------------------------------------------------- |
| `connect`      | TCP connection established                                      |
| `ready`        | Server ready for commands (after loading if `enableReadyCheck`) |
| `error`        | Connection error (emitted silently — only if listener exists)   |
| `close`        | Connection closed                                               |
| `reconnecting` | Reconnection scheduled, arg = delay in ms                       |
| `end`          | No more reconnections will be made                              |
| `wait`         | `lazyConnect` is set, waiting for first command                 |

```ts
redis.on("error", (err) => console.error("Redis error:", err));
redis.on("ready", () => console.log("Redis ready"));

// Check status programmatically:
redis.status; // "wait" | "reconnecting" | "connecting" | "connect" | "ready" | "close" | "end"
```

## Key Methods

| Method                  | Description                                                  |
| ----------------------- | ------------------------------------------------------------ |
| `redis.connect()`       | Connect manually (when `lazyConnect: true`). Returns Promise |
| `redis.disconnect()`    | Force close. No reconnect. Pending commands rejected         |
| `redis.quit()`          | Graceful close. Waits for pending replies, then sends QUIT   |
| `redis.duplicate()`     | Create new instance with same options                        |
| `redis.pipeline()`      | Create pipeline                                              |
| `redis.multi()`         | Create transaction                                           |
| `redis.defineCommand()` | Register Lua script as command                               |
| `redis.monitor()`       | Enter MONITOR mode (returns monitor instance)                |
| `redis.scanStream()`    | Create readable stream for SCAN                              |
