# Production Guide

## Table of Contents

- [Redis Configuration](#redis-configuration)
- [Connection Strategy](#connection-strategy)
- [Graceful Shutdown](#graceful-shutdown)
- [Retry Strategies](#retry-strategies)
- [Stalled Jobs](#stalled-jobs)
- [Sandboxed Processors](#sandboxed-processors)
- [Concurrency](#concurrency)
- [Auto-Job Removal](#auto-job-removal)
- [Error Handling](#error-handling)
- [Monitoring with Prometheus](#monitoring-with-prometheus)
- [Data Security](#data-security)
- [Troubleshooting Checklist](#troubleshooting-checklist)

## Redis Configuration

### Persistence

Enable AOF (Append Only File) for durability. 1-second fsync is sufficient for most apps:

```
# redis.conf
appendonly yes
appendfsync everysec
```

### Memory Policy

**Critical:** BullMQ will malfunction if Redis evicts keys.

```
maxmemory-policy noeviction
```

## Connection Strategy

Different needs for producers vs consumers:

### Producers (Queue class) — fail fast

```ts
import { Redis } from "ioredis";

const producerConn = new Redis({
  host: "redis.example.com",
  port: 6379,
  maxRetriesPerRequest: 1, // fail quickly on disconnect
  enableOfflineQueue: false, // don't queue commands when offline
});

const queue = new Queue("q", { connection: producerConn });
```

### Consumers (Worker class) — wait indefinitely

```ts
const workerConn = new Redis({
  host: "redis.example.com",
  port: 6379,
  maxRetriesPerRequest: null, // REQUIRED for workers — retry forever
  // enableOfflineQueue: true  // default, keeps queuing commands
});

const worker = new Worker("q", processor, { connection: workerConn });
```

### Retry Strategy

BullMQ default (for internally created connections):

```ts
retryStrategy: (times) => Math.max(Math.min(Math.exp(times), 20000), 1000);
// Exponential backoff: min 1s, max 20s
```

## Graceful Shutdown

```ts
const gracefulShutdown = async (signal: string) => {
  console.log(`Received ${signal}, closing worker...`);
  await worker.close();
  process.exit(0);
};

process.on("SIGINT", () => gracefulShutdown("SIGINT"));
process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
```

If the worker doesn't close before the process is killed, in-progress jobs become **stalled** and are re-processed after ~30 seconds by another worker.

## Retry Strategies

### Fixed Backoff

Retry after a constant delay:

```ts
await queue.add("job", data, {
  attempts: 3,
  backoff: { type: "fixed", delay: 1000 }, // retry every 1s
  // With jitter (0-1, randomizes between delay*jitter and delay):
  // backoff: { type: "fixed", delay: 1000, jitter: 0.5 },
});
```

### Exponential Backoff

Retry after `2^(attempts-1) * delay` ms:

```ts
await queue.add("job", data, {
  attempts: 5,
  backoff: { type: "exponential", delay: 1000 },
  // Attempt 1: 1s, Attempt 2: 2s, Attempt 3: 4s, Attempt 4: 8s, Attempt 5: 16s
});
```

### Custom Backoff

Define on the worker:

```ts
const worker = new Worker("q", processor, {
  settings: {
    backoffStrategy: (attemptsMade, type, err, job) => {
      if (type === "linear") return attemptsMade * 1000;
      if (type === "custom-exp") return Math.pow(2, attemptsMade) * 500;
      throw new Error("unknown type");
    },
  },
});

// Use in job options
await queue.add("job", data, {
  attempts: 5,
  backoff: { type: "linear" },
});
```

**Special return values from `backoffStrategy`:**

- `0` → move to end of waiting list (or back to prioritized if priority > 0)
- `-1` → don't retry, move to failed immediately

### Default Job Options

Set retry defaults for all jobs in a queue:

```ts
const queue = new Queue("q", {
  defaultJobOptions: {
    attempts: 3,
    backoff: { type: "exponential", delay: 1000 },
    removeOnComplete: { count: 200 },
    removeOnFail: { count: 1000 },
  },
});
```

## Stalled Jobs

A job becomes stalled when the worker holding it doesn't renew its lock within `stalledInterval` (default: 30s). Causes:

- CPU-intensive synchronous code blocking the event loop
- Process crash or kill without graceful shutdown

Stalled jobs are automatically moved back to waiting. After `maxStalledCount` (default: 1), they move to failed.

**Prevention:**

- Avoid blocking the event loop — use `async`/`await`, break CPU work into chunks
- Use sandboxed processors for CPU-intensive tasks
- Increase `stalledInterval` if jobs legitimately need long uninterrupted processing

## Sandboxed Processors

Run processors in separate child processes for CPU-intensive work:

```ts
// processor.ts (separate file)
import { SandboxedJob } from "bullmq";

export default async function (job: SandboxedJob) {
  // CPU-intensive work — runs in a child process
  return heavyComputation(job.data);
}

// main.ts
const worker = new Worker("q", "./processor.ts", { connection });
```

Benefits: isolates CPU-heavy work, prevents stalled jobs, true parallelism with `concurrency > 1`.

## Concurrency

### Local Concurrency (single worker)

```ts
const worker = new Worker("q", processor, { concurrency: 50 });
```

Only effective for I/O-bound (async) work. For CPU-bound work, use sandboxed processors.

### Multiple Workers (recommended for high availability)

Run workers across multiple processes/machines. Combine with local concurrency:

```ts
// Each machine runs:
const worker = new Worker("q", processor, { concurrency: 10 });
// 5 machines × 10 concurrency = 50 jobs processed concurrently
```

### Global Concurrency

Limit total concurrent processing across ALL workers:

```ts
await queue.setGlobalConcurrency(1); // only 1 job at a time, globally
```

### Global Rate Limit

```ts
const queue = new Queue("q");
// Must configure on the queue, not the worker
await queue.setGlobalConcurrency(5); // combined with worker limiter

// Check if rate limited
const ttl = await queue.getRateLimitTtl(100);
if (ttl > 0) console.log("Queue is rate limited");

// Reset rate limit
await queue.removeRateLimitKey();
```

## Auto-Job Removal

By default, completed and failed jobs are kept forever. Always configure removal:

```ts
const queue = new Queue("q", {
  defaultJobOptions: {
    removeOnComplete: { count: 100, age: 3600 }, // keep 100 or 1 hour
    removeOnFail: { count: 5000 }, // keep last 5000 failures
  },
});
```

## Error Handling

Always attach error handlers to prevent unhandled exceptions:

```ts
worker.on("error", (err) => {
  logger.error(err, "Worker error");
});

queue.on("error", (err) => {
  logger.error(err, "Queue error");
});

// Global safety net
process.on("uncaughtException", (err) => {
  logger.error(err, "Uncaught exception");
});

process.on("unhandledRejection", (reason, promise) => {
  logger.error({ promise, reason }, "Unhandled rejection");
});
```

**Important:** processor functions must throw `Error` objects (not strings or other types).

## Monitoring with Prometheus

```ts
import { Queue, MetricsTime } from "bullmq";

const queue = new Queue("q", {
  metrics: {
    maxDataPoints: MetricsTime.ONE_WEEK * 2, // collect 2 weeks of data
  },
});

// Retrieve metrics
const completedMetrics = await queue.getMetrics("completed");
// { meta: { count, prevCount }, data: number[] }

const failedMetrics = await queue.getMetrics("failed");
```

## Data Security

Job data is stored in **plain text** in Redis. Never store sensitive data (passwords, tokens, PII) in job payloads. If unavoidable, encrypt sensitive fields before adding to the queue.

## Troubleshooting Checklist

1. **Jobs not processing?** Check worker is connected to the same queue name with matching `prefix`.
2. **Stalled jobs?** CPU blocking the event loop — use sandboxed processors or break up work.
3. **Missing error handler?** Worker may silently stop processing — always attach `worker.on("error", ...)`.
4. **Redis memory growing?** Configure `removeOnComplete`/`removeOnFail`, check `maxmemory-policy`.
5. **Delayed jobs not firing?** Ensure Redis is reachable and no clock skew issues.
6. **Rate limiting not working?** `limiter` must be set on the worker options for `rateLimit()` to function.
7. **ioredis keyPrefix?** Don't use it — use BullMQ's `prefix` option instead.
