# Patterns

## Table of Contents

- [Process Step Jobs](#process-step-jobs)
- [Idempotent Jobs](#idempotent-jobs)
- [Throttle Jobs](#throttle-jobs)
- [Manual Rate Limiting](#manual-rate-limiting)
- [Static Rate Limiting](#static-rate-limiting)
- [Global Concurrency](#global-concurrency)
- [Failing Fast When Redis Is Down](#failing-fast-when-redis-is-down)
- [Redis Cluster](#redis-cluster)

## Process Step Jobs

Break processor logic into resumable steps. Save step state in `job.data` so retries resume from the correct step.

```ts
import { Worker } from "bullmq";

enum Step {
  Initial,
  Second,
  Finish,
}

const worker = new Worker(
  "queueName",
  async (job) => {
    let step = job.data.step;
    while (step !== Step.Finish) {
      switch (step) {
        case Step.Initial: {
          await doInitialStepStuff();
          await job.updateData({ step: Step.Second });
          step = Step.Second;
          break;
        }
        case Step.Second: {
          await doSecondStepStuff();
          await job.updateData({ step: Step.Finish });
          step = Step.Finish;
          return Step.Finish;
        }
        default:
          throw new Error("invalid step");
      }
    }
  },
  { connection },
);
```

### Delaying Mid-Process

Use `moveToDelayed` + `DelayedError` to pause a job and resume later:

```ts
import { DelayedError, Worker } from "bullmq";

const worker = new Worker(
  "queueName",
  async (job, token) => {
    let step = job.data.step;
    switch (step) {
      case Step.Initial: {
        await doStuff();
        await job.moveToDelayed(Date.now() + 5000, token);
        await job.updateData({ step: Step.Second });
        throw new DelayedError(); // signals worker to release the job
      }
      case Step.Second: {
        // resumes here after 5s delay
        return doMoreStuff();
      }
    }
  },
  { connection },
);
```

### Waiting for Dynamic Children

Add children at runtime, then wait for them with `moveToWaitingChildren`:

```ts
import { WaitingChildrenError, Worker } from "bullmq";

const worker = new Worker(
  "parentQueue",
  async (job, token) => {
    let step = job.data.step;
    switch (step) {
      case Step.Initial: {
        // Add child dynamically
        await childQueue.add(
          "child-1",
          { foo: "bar" },
          {
            parent: { id: job.id!, queue: job.queueQualifiedName },
          },
        );
        await job.updateData({ step: Step.WaitForChildren });
        step = Step.WaitForChildren;
        break;
      }
      case Step.WaitForChildren: {
        const shouldWait = await job.moveToWaitingChildren(token!);
        if (shouldWait) {
          throw new WaitingChildrenError();
        }
        // All children done — continue
        return "done";
      }
    }
  },
  { connection },
);
```

### Chaining Flows at Runtime

```ts
import { FlowProducer, WaitingChildrenError, Worker } from "bullmq";

const flow = new FlowProducer({ connection });

const worker = new Worker(
  "parentQueue",
  async (job, token) => {
    // Add a full flow as children
    await flow.add({
      name: "child-job",
      queueName: "childQueue",
      data: {},
      children: [
        { name: "gc1", data: {}, queueName: "grandchildQueue" },
        { name: "gc2", data: {}, queueName: "grandchildQueue" },
      ],
      opts: {
        parent: { id: job.id!, queue: job.queueQualifiedName },
      },
    });

    const shouldWait = await job.moveToWaitingChildren(token!);
    if (shouldWait) throw new WaitingChildrenError();
    return "all children done";
  },
  { connection },
);
```

**Note:** `DelayedError`, `WaitingChildrenError`, and `RateLimitError` do NOT increment `attemptsMade`. Use `maxStartedAttempts` to limit how many times a job can start processing.

## Idempotent Jobs

Use `jobId` to prevent duplicate processing:

```ts
await queue.add(
  "process-order",
  { orderId: 123 },
  {
    jobId: "order-123",
  },
);
// Second add with same jobId is silently ignored
await queue.add(
  "process-order",
  { orderId: 123 },
  {
    jobId: "order-123",
  },
);
```

## Throttle Jobs

Use deduplication throttle mode to limit how often a job type runs:

```ts
await queue.add("sync", data, {
  deduplication: { id: "sync-user-42", ttl: 60000 },
});
// Any add with same dedup ID within 60s is ignored
```

## Manual Rate Limiting

Handle external API rate limits (e.g., 429 responses):

```ts
import { Worker } from "bullmq";

const worker = new Worker(
  "api-calls",
  async () => {
    const [isRateLimited, duration] = await callExternalApi();
    if (isRateLimited) {
      await worker.rateLimit(duration);
      throw Worker.RateLimitError();
    }
  },
  {
    connection,
    limiter: { max: 1, duration: 500 }, // REQUIRED: must set limiter for rateLimit to work
  },
);
```

## Static Rate Limiting

```ts
const worker = new Worker("painter", async (job) => paintCar(job), {
  limiter: {
    max: 10, // max 10 jobs
    duration: 1000, // per 1 second
  },
});
```

The rate limiter is **global** across all workers for the queue.

## Global Concurrency

Limit to 1 job processing at a time across all workers:

```ts
await queue.setGlobalConcurrency(1);
```

## Failing Fast When Redis Is Down

For producer services (HTTP endpoints), disable offline queue so calls fail immediately:

```ts
import { Redis } from "ioredis";

const connection = new Redis({
  maxRetriesPerRequest: 1,
  enableOfflineQueue: false,
});

const queue = new Queue("q", { connection });

try {
  await queue.add("job", data);
} catch (err) {
  // Redis is down — return 503 to the client
}
```

## Redis Cluster

```ts
import { Cluster } from "ioredis";

const connection = new Cluster(
  [
    { host: "node1", port: 6380 },
    { host: "node2", port: 6380 },
  ],
  {
    natMap: {
      /* ... */
    },
  },
);

const queue = new Queue("q", { connection, prefix: "{myprefix}" });
```

Use `{hashTag}` prefix to ensure all keys for a queue land on the same slot.
