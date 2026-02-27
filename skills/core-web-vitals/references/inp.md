# INP — Interaction to Next Paint

**Good:** ≤ 200 ms | **Needs improvement:** 200–500 ms | **Poor:** > 500 ms
(measured at the 75th percentile of field loads)

INP replaced FID (First Input Delay) as a Core Web Vital in March 2024.
Unlike FID (only measured the first interaction's input delay), INP measures
**all interactions** on the page — clicks, taps, and key presses — and reports
the worst one observed.

## What makes up an interaction?

Each interaction has three phases:

```
[user gesture]
     │
     ▼
┌─────────────────┐
│  Input delay    │  Time before event handlers start (blocked by other tasks)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Processing time │  Time to run event handlers (JS execution)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Presentation     │  Time to render the next frame (layout, paint, composite)
│delay            │
└─────────────────┘
         │
         ▼
  [visual feedback]
```

INP = input delay + processing time + presentation delay

Only clicks, taps, and key presses count. Hover and scroll do not.
No INP value is reported if the user never interacts with the page.

## Common causes of high INP

### Long input delay (main thread is busy)
- Long tasks (> 50 ms) scheduled during or just before the interaction
- Timer callbacks (`setInterval`, `setTimeout`) running too frequently
- Third-party scripts blocking the main thread

**Fix: yield to the main thread between tasks**

```js
// Instead of doing everything synchronously:
function handleClick() {
  doHeavyWork();   // blocks interaction handling
  updateUI();
}

// Yield after each chunk using scheduler.yield() (Chrome 129+)
async function handleClick() {
  doFirstChunk();
  await scheduler.yield();  // gives browser a chance to handle interactions
  doSecondChunk();
  await scheduler.yield();
  updateUI();
}

// Fallback for older browsers
function yieldToMain() {
  return new Promise(resolve => setTimeout(resolve, 0));
}
```

### Heavy event handler processing time
- Running too much synchronous JS inside `onclick`/`onkeydown` handlers
- Triggering expensive recalculations (style, layout) inside handlers

**Fix: defer non-essential work**

```js
element.addEventListener('click', async (event) => {
  // Do only what's needed for the immediate visual update
  updateButtonState(event.target);

  // Defer expensive analytics/processing until after the frame paints
  await scheduler.yield();
  sendAnalytics(event);
  prefetchRelatedContent();
});
```

### Large rendering updates (presentation delay)
- Re-rendering a large DOM subtree unnecessarily
- Causing style recalculation on many elements
- JavaScript animations that force layout (reading `offsetWidth`, `getBoundingClientRect`)
  then writing styles in a loop

**Fix: minimize DOM size and avoid layout thrashing**

```js
// Layout thrashing (bad) — forces synchronous layout each iteration
elements.forEach(el => {
  const height = el.offsetHeight;  // forces layout
  el.style.height = height * 2 + 'px';  // invalidates layout
});

// Batch reads then writes (good)
const heights = elements.map(el => el.offsetHeight);  // one layout
elements.forEach((el, i) => { el.style.height = heights[i] * 2 + 'px'; });
```

## Avoid unnecessary JavaScript

- Code-split aggressively — defer JS not needed for initial interaction
- Remove unused polyfills and libraries
- Avoid loading third-party scripts that add long tasks during user sessions

## Measure INP in JavaScript (raw API)

```js
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.interactionId) {
      console.log('Interaction:', entry.name, entry.duration, 'ms');
    }
  }
}).observe({ type: 'event', buffered: true, durationThreshold: 16 });
```

Prefer `onINP()` from the `web-vitals` library — it correctly aggregates all
interactions, selects the worst, and handles attribution.

## Key nuances

- INP is the **worst interaction** observed (excluding statistical outliers at
  very high page load counts to reduce noise from accidental interactions)
- If a page has ≤ 50 interactions, INP = worst interaction
- If a page has > 50 interactions, the 98th percentile interaction is used
- Animations triggered by JS do not count as interactions
- INP is not measurable in lab tools (Lighthouse uses TBT as a proxy)
