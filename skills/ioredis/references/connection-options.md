# ioredis Connection Options Reference

## Table of Contents

- [RedisOptions type alias](#redisoptions-type-alias)
- [CommonRedisOptions](#commonredisoptions)
- [StandaloneConnectionOptions](#standaloneconnectionoptions)
- [SentinelConnectionOptions](#sentinelconnectionoptions-summary)
- [retryStrategy patterns](#retrystrategy-patterns)
- [reconnectOnError patterns](#reconnectonerror-patterns)
- [TLS configuration](#tls-configuration)
- [Blocking command timeout](#blocking-command-timeout)
- [Connection lifecycle](#connection-lifecycle)

## RedisOptions type alias

```ts
type RedisOptions = CommonRedisOptions & SentinelConnectionOptions & StandaloneConnectionOptions;
```

All three interfaces are merged. Standalone options include `host`, `port`, `path`, `tls`, and `disconnectTimeout`.

## CommonRedisOptions

| Property                        | Type                                                | Default             | Description                                                             |
| ------------------------------- | --------------------------------------------------- | ------------------- | ----------------------------------------------------------------------- |
| `retryStrategy`                 | `(times: number) => number \| void`                 | exponential backoff | Return ms to wait before reconnect. Return `undefined` to stop          |
| `commandTimeout`                | `number`                                            | `undefined`         | Ms before "Command timed out" error                                     |
| `blockingTimeout`               | `number`                                            | `undefined`         | Client-side timeout for blocking commands (opt-in, disabled by default) |
| `blockingTimeoutGrace`          | `number`                                            | `100`               | Grace period ms added to blocking timeouts                              |
| `socketTimeout`                 | `number`                                            | `undefined`         | Ms of socket inactivity before destroying                               |
| `keepAlive`                     | `number`                                            | `0`                 | TCP keepalive initial delay in ms. `0` = disabled                       |
| `noDelay`                       | `boolean`                                           | `true`              | Disable Nagle's algorithm (TCP_NODELAY)                                 |
| `connectionName`                | `string`                                            | `undefined`         | CLIENT SETNAME value                                                    |
| `disableClientInfo`             | `boolean`                                           | `false`             | Skip CLIENT SETINFO                                                     |
| `clientInfoTag`                 | `string`                                            | `undefined`         | Tag appended to library name in CLIENT SETINFO                          |
| `username`                      | `string`                                            | `undefined`         | AUTH username (Redis >= 6 ACL)                                          |
| `password`                      | `string`                                            | `undefined`         | AUTH password                                                           |
| `db`                            | `number`                                            | `0`                 | Database index                                                          |
| `autoResubscribe`               | `boolean`                                           | `true`              | Re-subscribe channels on reconnect                                      |
| `autoResendUnfulfilledCommands` | `boolean`                                           | `true`              | Resend pending blocking commands on reconnect                           |
| `reconnectOnError`              | `(err: Error) => boolean \| 0 \| 1 \| 2`            | `null`              | See reconnectOnError patterns below                                     |
| `readOnly`                      | `boolean`                                           | `false`             | Send READONLY after connect                                             |
| `stringNumbers`                 | `boolean`                                           | `false`             | Return numbers as strings (safe for > 2^53)                             |
| `connectTimeout`                | `number`                                            | `10000`             | Ms before killing socket during initial connection                      |
| `monitor`                       | `boolean`                                           | `false`             | Enter MONITOR mode on connect (internal use)                            |
| `maxRetriesPerRequest`          | `number \| null`                                    | `20`                | Flush queue after N reconnects. `null` = wait forever                   |
| `maxLoadingRetryTime`           | `number`                                            | `10000`             | Max ms to wait for server to finish loading                             |
| `enableAutoPipelining`          | `boolean`                                           | `false`             | Auto-batch commands per event loop tick                                 |
| `autoPipeliningIgnoredCommands` | `string[]`                                          | `[]`                | Commands excluded from auto-pipelining                                  |
| `enableOfflineQueue`            | `boolean`                                           | `true`              | Queue commands before "ready". `false` = error immediately              |
| `enableReadyCheck`              | `boolean`                                           | `true`              | Wait for INFO loading:0 before emitting "ready"                         |
| `lazyConnect`                   | `boolean`                                           | `false`             | Delay connection until first command or explicit `connect()`            |
| `scripts`                       | `Record<string, { lua, numberOfKeys?, readOnly? }>` | `undefined`         | Pre-define Lua commands                                                 |
| `keyPrefix`                     | `string`                                            | `undefined`         | Auto-prefix all keys                                                    |
| `showFriendlyErrorStack`        | `boolean`                                           | `false`             | Better stacks in dev (perf cost — never in production)                  |
| `Connector`                     | `ConnectorConstructor`                              | `undefined`         | Custom connector class                                                  |

## StandaloneConnectionOptions

```ts
type StandaloneConnectionOptions = Partial<TcpOptions & IpcOptions> & {
  disconnectTimeout?: number;
  tls?: ConnectionOptions;
};
```

Includes Node.js `net.connect()` options:

- `host`: string (default `"127.0.0.1"`)
- `port`: number (default `6379`)
- `path`: string (Unix socket path, overrides host/port)
- `tls`: Node.js `tls.connect()` options
- `disconnectTimeout`: ms to wait for graceful disconnect

## SentinelConnectionOptions (summary)

See [cluster-sentinel.md](cluster-sentinel.md) for full Sentinel reference.

Key properties: `sentinels`, `name`, `role`, `sentinelPassword`, `sentinelUsername`, `sentinelTLS`, `enableTLSForSentinelMode`, `failoverDetector`, `sentinelRetryStrategy`, `sentinelReconnectStrategy`, `updateSentinels`, `natMap`, `preferredSlaves`, `sentinelMaxConnections`, `sentinelCommandTimeout`.

## retryStrategy patterns

```ts
// Default: exponential backoff capped at 2s
retryStrategy(times) {
  return Math.min(times * 50, 2000);
}

// Stop after 10 attempts:
retryStrategy(times) {
  if (times > 10) return undefined; // stop reconnecting
  return Math.min(times * 100, 3000);
}

// Immediate reconnect for first 3 attempts, then backoff:
retryStrategy(times) {
  if (times <= 3) return 0;
  return Math.min(times * 100, 5000);
}

// Never reconnect (disable auto-reconnect):
retryStrategy() {
  return undefined;
}
```

`times` is the number of reconnection attempts so far (starts at 1). When the function returns `undefined` or a non-number, ioredis stops reconnecting and emits the `end` event.

## reconnectOnError patterns

```ts
// Reconnect on READONLY (AWS ElastiCache failover):
reconnectOnError(err) {
  if (err.message.includes("READONLY")) return true;
  return false;
}
```

Return values:

- `false` / `0` — do not reconnect
- `true` / `1` — reconnect
- `2` — reconnect AND resend the failed command after reconnection

Default is `null` (never reconnect on Redis errors).

## TLS configuration

```ts
// Minimal (system CAs):
new Redis({ host: "redis.example.com", tls: {} });

// With CA certificate:
new Redis({
  host: "redis.example.com",
  tls: { ca: fs.readFileSync("ca.pem") },
});

// Via URL (rediss:// = TLS):
new Redis("rediss://redis.example.com:6380");

// TLS profiles (deprecated, will be removed in v6):
new Redis({ host: "localhost", tls: "RedisCloudFixed" });
new Redis({ host: "localhost", tls: "RedisCloudFlexible" });
```

## Blocking command timeout

Opt-in client-side protection for blocking commands (`blpop`, `brpop`, `xread`, etc.):

```ts
const redis = new Redis({
  blockingTimeout: 30000, // Enable — 30s safety net for "block forever" commands
  blockingTimeoutGrace: 100, // Grace period added to finite timeouts (default: 100ms)
});
```

- Disabled by default (`blockingTimeout` undefined, 0, or negative)
- For finite-timeout commands (e.g., `blpop("key", 5)`): deadline = command timeout + grace
- For infinite-timeout commands (`timeout = 0`): deadline = `blockingTimeout` value
- On timeout: resolves with `null` (same as Redis native timeout behavior)

## Connection lifecycle

```
[new Redis()] → connecting → connect → ready → (commands execute)
                    ↑                     ↓
                    └── reconnecting ← close → end (if retryStrategy returns undefined)
```

- `connect`: TCP established
- `ready`: Server loaded and accepting commands
- `close` → `reconnecting`: Auto-reconnect cycle
- `end`: Final — no more reconnection attempts

Graceful shutdown:

```ts
await redis.quit(); // Waits for pending replies, sends QUIT, closes
```

Force shutdown:

```ts
redis.disconnect(); // Immediate close, pending commands rejected
```
