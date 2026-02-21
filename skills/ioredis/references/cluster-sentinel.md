# ioredis Cluster & Sentinel Reference

## Table of Contents

- [Redis Cluster](#redis-cluster)
- [ClusterOptions](#clusteroptions)
- [Read-write splitting](#read-write-splitting)
- [NAT mapping](#nat-mapping)
- [Pipeline & transaction in Cluster](#pipeline--transaction-in-cluster)
- [Pub/Sub in Cluster](#pubsub-in-cluster)
- [Cluster events](#cluster-events)
- [Cluster password](#cluster-password)
- [AWS ElastiCache with TLS](#aws-elasticache-with-tls)
- [Sentinel](#sentinel)
- [SentinelConnectionOptions](#sentinelconnectionoptions)
- [Sentinel failover](#sentinel-failover)

> **Terminology note:** ioredis uses `slave` in its API (e.g., `scaleReads: "slave"`, `role: "slave"`, `preferredSlaves`); Redis 5.0+ documentation uses `replica` instead.

## Redis Cluster

```ts
import { Cluster } from "ioredis";

const cluster = new Cluster([
  { host: "127.0.0.1", port: 6380 },
  { host: "127.0.0.1", port: 6381 },
]);

await cluster.set("foo", "bar");
const val = await cluster.get("foo"); // "bar"
```

First argument: startup nodes (not all nodes needed — ioredis auto-discovers the rest).

## ClusterOptions

Second argument to `new Cluster(nodes, options)`:

| Option                    | Type                                       | Default                        | Description                                                                    |
| ------------------------- | ------------------------------------------ | ------------------------------ | ------------------------------------------------------------------------------ |
| `clusterRetryStrategy`    | `(times) => number \| void`                | backoff 100+times\*2, max 2000 | Delay before reconnecting when no startup nodes reachable. Return void to stop |
| `scaleReads`              | `"master" \| "slave" \| "all" \| Function` | `"master"`                     | Where to route read queries                                                    |
| `enableOfflineQueue`      | `boolean`                                  | `true`                         | Queue commands before ready                                                    |
| `enableReadyCheck`        | `boolean`                                  | `true`                         | Wait for CLUSTER INFO ready                                                    |
| `maxRedirections`         | `number`                                   | `16`                           | Max MOVED/ASK redirections per command                                         |
| `retryDelayOnFailover`    | `number`                                   | `100`                          | Ms delay when target node disconnected                                         |
| `retryDelayOnClusterDown` | `number`                                   | `100`                          | Ms delay on CLUSTERDOWN error                                                  |
| `retryDelayOnTryAgain`    | `number`                                   | `100`                          | Ms delay on TRYAGAIN error                                                     |
| `retryDelayOnMoved`       | `number`                                   | `0`                            | Ms delay on MOVED error                                                        |
| `slotsRefreshTimeout`     | `number`                                   | `1000`                         | Ms timeout for slot refresh                                                    |
| `slotsRefreshInterval`    | `number`                                   | disabled                       | Ms between automatic slot refreshes                                            |
| `redisOptions`            | `RedisOptions`                             | `{}`                           | Default options for each node connection                                       |
| `dnsLookup`               | `Function`                                 | `dns.lookup`                   | Custom DNS resolution                                                          |
| `natMap`                  | `object \| Function`                       | `undefined`                    | NAT address translation                                                        |
| `shardedSubscribers`      | `boolean`                                  | `false`                        | Enable sharded Pub/Sub connections                                             |

### clusterRetryStrategy

```ts
// Default:
clusterRetryStrategy(times) {
  return Math.min(100 + times * 2, 2000);
}

// Switch startup nodes on failure:
clusterRetryStrategy(times) {
  this.startupNodes = [{ port: 6790, host: "127.0.0.1" }];
  return Math.min(100 + times * 2, 2000);
}
```

## Read-write splitting

```ts
const cluster = new Cluster(nodes, { scaleReads: "slave" });
cluster.set("foo", "bar"); // -> master
cluster.get("foo"); // -> random slave (may lag behind master)
```

`scaleReads` values:

- `"master"` (default) — all queries to master
- `"slave"` — writes to master, reads to slaves
- `"all"` — writes to master, reads to master or slaves randomly
- `function(nodes, command)` — custom routing. First node is always master. Return single node or array (random pick)

## NAT mapping

For clusters behind NAT (Docker, AWS VPC):

```ts
// Object mapping:
const cluster = new Cluster([{ host: "203.0.113.73", port: 30001 }], {
  natMap: {
    "10.0.1.230:30001": { host: "203.0.113.73", port: 30001 },
    "10.0.1.231:30001": { host: "203.0.113.73", port: 30002 },
  },
});

// Function mapping:
const cluster = new Cluster([{ host: "203.0.113.73", port: 30001 }], {
  natMap: (key) => {
    if (key.includes("30001")) return { host: "203.0.113.73", port: 30001 };
    return null;
  },
});
```

## Pipeline & transaction in Cluster

**Constraint**: All keys in a pipeline must hash to slots on the same node.

```ts
// Works — same slot via hash tags:
cluster.pipeline().set("{user:1}:name", "Alice").set("{user:1}:email", "alice@example.com").exec();

// multi() without pipeline is NOT supported in Cluster:
// cluster.multi({ pipeline: false }) — throws error
```

Auto-resend: If all commands get the same MOVED/ASK error and all successful commands were read-only, ioredis automatically resends the entire pipeline to the correct node.

## Pub/Sub in Cluster

Works the same as standalone. One node is subscribed; messages are broadcast cluster-wide.

```ts
const pub = new Cluster(nodes);
const sub = new Cluster(nodes);

sub.on("message", (channel, message) => console.log(channel, message));
await sub.subscribe("news");
pub.publish("news", "hello");
```

### Sharded Pub/Sub (Redis >= 7)

Enable `shardedSubscribers: true`. All channels in one `ssubscribe` call must hash to the same slot.

```ts
const cluster = new Cluster(nodes, { shardedSubscribers: true });

cluster.on("smessage", (channel, message) => console.log(message));
await cluster.ssubscribe("channel{my}:1", "channel{my}:2");
cluster.spublish("channel{my}:1", "test message");
```

## Cluster events

| Event          | Description                                              |
| -------------- | -------------------------------------------------------- |
| `connect`      | Connection established                                   |
| `ready`        | Cluster ready (after CLUSTER INFO if `enableReadyCheck`) |
| `error`        | Error with `lastNodeError` property                      |
| `close`        | Connection closed                                        |
| `reconnecting` | Reconnecting, arg = delay ms                             |
| `end`          | No more reconnections                                    |
| `+node`        | New node connected                                       |
| `-node`        | Node disconnected                                        |
| `node error`   | Error connecting to node (2nd arg = address)             |

## Cluster password

```ts
// Same password for all nodes:
const cluster = new Cluster(nodes, {
  redisOptions: { password: "cluster-password" },
});

// Per-node passwords:
const cluster = new Cluster(
  [
    { port: 30001, password: "pass-for-30001" },
    { port: 30002, password: null }, // no password
  ],
  {
    redisOptions: { password: "fallback-password" },
  },
);
```

## AWS ElastiCache with TLS

```ts
const cluster = new Cluster(
  [{ host: "clustercfg.myCluster.abcdefg.xyz.cache.amazonaws.com", port: 6379 }],
  {
    dnsLookup: (address, callback) => callback(null, address),
    redisOptions: { tls: {} },
  },
);
```

The `dnsLookup` override prevents certificate validation errors with ElastiCache TLS.

## Sentinel

```ts
import { Redis } from "ioredis";

const redis = new Redis({
  sentinels: [
    { host: "localhost", port: 26379 },
    { host: "localhost", port: 26380 },
  ],
  name: "mymaster", // Master group name
  // Optional:
  sentinelPassword: "sentinel-pass",
  sentinelUsername: "sentinel-user", // Redis >= 6
  role: "master", // "master" (default) or "slave"
  password: "redis-pass", // Password for the actual Redis instance
});
```

ioredis guarantees:

- Always connects to the current master (even after failover)
- Commands during failover are queued and run on the new master
- If `role: "slave"`, always connects to a slave; reconnects to another slave if promoted

### preferredSlaves

```ts
// Array format (lower prio = higher priority):
const redis = new Redis({
  sentinels: [...],
  name: "mymaster",
  role: "slave",
  preferredSlaves: [
    { ip: "127.0.0.1", port: "31231", prio: 1 },
    { ip: "127.0.0.1", port: "31232", prio: 2 },
  ],
});

// Function format:
const redis = new Redis({
  sentinels: [...],
  name: "mymaster",
  role: "slave",
  preferredSlaves(availableSlaves) {
    return availableSlaves.find(s => s.port === "31234") || false;
  },
});
```

## SentinelConnectionOptions

| Option                      | Type                        | Default               | Description                                 |
| --------------------------- | --------------------------- | --------------------- | ------------------------------------------- |
| `sentinels`                 | `Array<{ host?, port? }>`   | required              | List of sentinel nodes                      |
| `name`                      | `string`                    | required              | Master group name                           |
| `role`                      | `"master" \| "slave"`       | `"master"`            | Connect to master or slave                  |
| `sentinelPassword`          | `string`                    | `undefined`           | Password for sentinel instances             |
| `sentinelUsername`          | `string`                    | `undefined`           | Username for sentinel (Redis >= 6)          |
| `sentinelRetryStrategy`     | `(times) => number \| void` | `min(times*10, 1000)` | Retry when all sentinels unreachable        |
| `sentinelReconnectStrategy` | `(times) => number \| void` | —                     | Reconnect strategy for sentinel connections |
| `preferredSlaves`           | `Array \| Function`         | `undefined`           | Slave selection preference                  |
| `enableTLSForSentinelMode`  | `boolean`                   | `false`               | TLS for sentinel connections                |
| `sentinelTLS`               | `tls.ConnectionOptions`     | `undefined`           | TLS options for sentinel                    |
| `tls`                       | `tls.ConnectionOptions`     | `undefined`           | TLS for Redis connection                    |
| `updateSentinels`           | `boolean`                   | `true`                | Auto-update sentinel list                   |
| `failoverDetector`          | `boolean`                   | `false`               | Detect failover proactively                 |
| `natMap`                    | `object \| Function`        | `undefined`           | NAT mapping                                 |
| `sentinelMaxConnections`    | `number`                    | `10`                  | Max sentinel connections                    |
| `sentinelCommandTimeout`    | `number`                    | `undefined`           | Timeout for sentinel commands               |
| `connectTimeout`            | `number`                    | `undefined`           | Connect timeout for sentinel                |
| `disconnectTimeout`         | `number`                    | `undefined`           | Disconnect timeout                          |

## Sentinel failover

Default `sentinelRetryStrategy`:

```ts
sentinelRetryStrategy(times) {
  return Math.min(times * 10, 1000);
}
```

When all sentinels are unreachable, this controls the delay before retrying from scratch. Return `undefined` to stop.
