# Flows and Job Schedulers

## Table of Contents

- [FlowProducer — Parent-Child Relationships](#flowproducer--parent-child-relationships)
- [Job Schedulers (v5.16.0+)](#job-schedulers-v5160)

## FlowProducer — Parent-Child Relationships

A parent job waits in `waiting-children` state until all its children complete. Children can be in different queues.

```ts
import { FlowProducer } from "bullmq";

const flowProducer = new FlowProducer({ connection });

const flow = await flowProducer.add({
  name: "renovate-interior",
  queueName: "renovate",
  children: [
    { name: "paint", data: { place: "ceiling" }, queueName: "steps" },
    { name: "paint", data: { place: "walls" }, queueName: "steps" },
    { name: "fix", data: { place: "floor" }, queueName: "steps" },
  ],
});
```

This atomically adds 4 jobs. The parent (`renovate`) processes only after all 3 children complete.

### Accessing Children Results

```ts
const renovateWorker = new Worker("renovate", async (job) => {
  const childrenValues = await job.getChildrenValues();
  // { "bull:steps:paint:1": 2500, "bull:steps:fix:3": 1750 }
  const total = Object.values(childrenValues).reduce((a, b) => a + b, 0);
  return total;
});
```

### Serial Chains (Deep Hierarchies)

Nest children to create sequential execution:

```ts
await flowProducer.add({
  name: "car",
  data: { step: "engine" },
  queueName: "assembly",
  children: [
    {
      name: "car",
      data: { step: "wheels" },
      queueName: "assembly",
      children: [{ name: "car", data: { step: "chassis" }, queueName: "assembly" }],
    },
  ],
});
// Processing order: chassis → wheels → engine
```

### Flow Getters

```ts
// Get direct children
const deps = await job.getDependencies();

// Paginated by type
const { processed, nextProcessedCursor } = await job.getDependencies({
  processed: { count: 5, cursor: 0 },
});

// Count by type
const { failed, ignored, processed, unprocessed } = await job.getDependenciesCount();

// Check state
const state = await job.getState(); // "waiting-children"
```

### Queue Options for Flows

```ts
await flowProducer.add(flowDefinition, {
  queuesOptions: {
    assembly: {
      defaultJobOptions: { removeOnComplete: true },
    },
  },
});
```

### Flow Job Removal

- Removing a **parent** removes all its children.
- Removing a **child** removes the parent's dependency on it. If it was the last child, the parent completes.
- If any job to be removed is **locked** (being processed), the removal throws an exception.

```ts
await job.remove();
// or
await queue.remove(jobId);
```

### Add Flows in Bulk

```ts
await flowProducer.addBulk([
  { name: "flow1", queueName: "q", children: [...] },
  { name: "flow2", queueName: "q", children: [...] },
]);
```

## Job Schedulers (v5.16.0+)

Job Schedulers replace legacy "repeatable jobs". They act as factories producing jobs on a schedule.

### Fixed Interval

```ts
const firstJob = await queue.upsertJobScheduler("my-scheduler", {
  every: 1000, // every 1 second
});
```

### Cron Pattern

```ts
await queue.upsertJobScheduler(
  "daily-report",
  { pattern: "0 15 3 * * *" }, // daily at 3:15 AM
  {
    name: "generate-report",
    data: { type: "daily" },
    opts: { attempts: 5, backoff: 3, removeOnFail: 1000 },
  },
);
```

### Key Behaviors

- **Upsert semantics**: calling `upsertJobScheduler` with the same ID updates the existing scheduler (no duplicates).
- **Production rate**: a new job is only produced when the previous one starts processing. If the queue is busy, jobs may arrive less frequently than the interval.
- **Job ID**: jobs get auto-generated IDs — you cannot use custom job IDs. Use `name` to discriminate.
- There is always one associated job in "delayed" status.

### Manage Schedulers

```ts
// List all schedulers
const schedulers = await queue.getJobSchedulers(0, 100);

// Remove a scheduler
await queue.removeJobScheduler("my-scheduler");
```

### Repeat Strategies

Built-in: `every` (fixed interval) and `pattern` (cron). You can define custom strategies:

```ts
const queue = new Queue("q", {
  settings: {
    repeatStrategy: (millis, opts) => {
      // Return next execution timestamp
      return Date.now() + customDelay;
    },
  },
});
```

### Repeat Options

```ts
await queue.upsertJobScheduler("scheduler-id", {
  pattern: "0 * * * *", // cron expression
  // or
  every: 5000, // fixed ms interval

  // Optional:
  limit: 100, // max times to repeat
  startDate: new Date("2025-01-01"),
  endDate: new Date("2025-12-31"),
  tz: "America/Sao_Paulo", // timezone for cron
  immediately: true, // produce first job immediately
});
```
