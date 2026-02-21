# Job Types and Options

## Table of Contents

- [Delayed Jobs](#delayed-jobs)
- [Prioritized Jobs](#prioritized-jobs)
- [FIFO and LIFO](#fifo-and-lifo)
- [Custom Job IDs](#custom-job-ids)
- [Job Data](#job-data)
- [Deduplication](#deduplication)
- [Repeatable Jobs (Legacy)](#repeatable-jobs-legacy)
- [Auto-Removal Options](#auto-removal-options)
- [Returning Job Data](#returning-job-data)

## Delayed Jobs

```ts
await queue.add("email", { to: "user@example.com" }, { delay: 60000 }); // 1 min delay
```

Jobs wait in the "delayed" set, then move to "wait" (or "prioritized") when the delay expires. No `QueueScheduler` needed since BullMQ 2.0.

## Prioritized Jobs

Priority range: `0` (highest) to `2^21` (lowest). Default is `0`. Follows Unix nice convention — higher number = lower priority.

```ts
await queue.add("urgent", data, { priority: 1 });
await queue.add("normal", data, { priority: 100 });
await queue.add("low", data, { priority: 2097152 }); // 2^21
```

Prioritized jobs go into a dedicated set and are picked before regular "wait" jobs.

## FIFO and LIFO

Default is FIFO. Use `{ lifo: true }` to place jobs at the head of the waiting list.

## Custom Job IDs

```ts
await queue.add("job", data, { jobId: "my-unique-id" });
```

If a job with the same ID exists and is not yet removed, the `add` call is ignored. Useful for idempotency. Do NOT use colons `:` in job IDs (used as internal separator).

## Job Data

Keep job data small — it's stored in Redis. For large payloads, store data externally and pass a reference.

```ts
// Update data during processing
await job.updateData({ ...job.data, step: "next" });

// Get current data
const data = job.data;
```

## Deduplication

Three modes, all use a `deduplication` option with an `id`:

### Simple Mode — deduplicate until job completes/fails

```ts
await queue.add("process", data, {
  deduplication: { id: "unique-key" },
});
```

Subsequent adds with same dedup ID are ignored while the job is active.

### Throttle Mode — deduplicate for a TTL period

```ts
await queue.add("process", data, {
  deduplication: { id: "unique-key", ttl: 5000 },
});
```

Ignores duplicate adds for 5 seconds regardless of job state.

### Debounce Mode — replace previous job, reset TTL

```ts
await queue.add("process", data, {
  deduplication: { id: "unique-key", ttl: 5000, extend: true, replace: true },
  delay: 5000,
});
```

Replaces the previous pending job with new data. Only the last added job is processed.

### Deduplication API

```ts
// Check which job holds the dedup key
const jobId = await queue.getDeduplicationJobId("unique-key");

// Remove dedup key manually
await queue.removeDeduplicationKey("unique-key");
// Or from the job itself
const removed = await job.removeDeduplicationKey();
```

Listen for dedup events:

```ts
queueEvents.on("deduplicated", ({ jobId, deduplicationId, deduplicatedJobId }) => {
  console.log(`Job ${deduplicatedJobId} was deduplicated`);
});
```

## Repeatable Jobs (Legacy)

Prefer Job Schedulers (`upsertJobScheduler`) for new code. Legacy `repeat` option still works:

```ts
await queue.add("report", data, {
  repeat: { every: 60000 }, // every 60s
  // or
  repeat: { pattern: "0 * * * *" }, // cron: every hour
});
```

## Auto-Removal Options

Control how many completed/failed jobs to keep:

```ts
await queue.add("job", data, {
  // removeOnComplete: true,           // Option A: remove immediately
  // removeOnComplete: { count: 100 }, // Option B: keep last 100
  removeOnComplete: { age: 3600 }, // Option C: keep for 1 hour
  removeOnFail: { count: 500 }, // keep last 500 failed
});
```

Set defaults for all jobs:

```ts
const queue = new Queue("q", {
  defaultJobOptions: {
    removeOnComplete: { count: 200 },
    removeOnFail: { count: 1000 },
  },
});
```

## Returning Job Data

The value returned from the processor is stored as the job's `returnvalue`:

```ts
// In the worker
async (job) => {
  return { processedAt: Date.now() };
};

// Retrieve later
const job = await Job.fromId(queue, jobId);
console.log(job.returnvalue); // { processedAt: ... }
```
