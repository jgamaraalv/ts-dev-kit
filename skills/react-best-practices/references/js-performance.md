# JavaScript Performance

Low-level JS optimizations for DOM manipulation, caching, and data structures.

## Table of Contents

- [Avoid Layout Thrashing](#avoid-layout-thrashing)
- [Cache Repeated Function Calls](#cache-repeated-function-calls)
- [Cache Storage API Calls](#cache-storage-api-calls)
- [Build Index Maps for Repeated Lookups](#build-index-maps-for-repeated-lookups)
- [Use Loop for Min/Max Instead of Sort](#use-loop-for-minmax-instead-of-sort)

---

## Avoid Layout Thrashing

Avoid interleaving style writes with layout reads. Reading layout properties (`offsetWidth`, `getBoundingClientRect()`, `getComputedStyle()`) between style changes forces a synchronous reflow.

**Incorrect (interleaved reads and writes):**

```typescript
function layoutThrashing(element: HTMLElement) {
  element.style.width = "100px";
  const width = element.offsetWidth; // Forces reflow
  element.style.height = "200px";
  const height = element.offsetHeight; // Forces another reflow
}
```

**Correct (batch writes, then read once):**

```typescript
function updateElementStyles(element: HTMLElement) {
  element.style.width = "100px";
  element.style.height = "200px";
  element.style.backgroundColor = "blue";
  element.style.border = "1px solid black";

  const { width, height } = element.getBoundingClientRect();
}
```

**Better: use CSS classes:**

```typescript
element.classList.add("highlighted-box");
const { width, height } = element.getBoundingClientRect();
```

**React example:**

```tsx
// Incorrect
useEffect(() => {
  ref.current.style.width = "100px";
  const width = ref.current.offsetWidth; // Forces layout
  ref.current.style.height = "200px";
}, [isHighlighted]);

// Correct: toggle class
<div className={isHighlighted ? "highlighted-box" : ""}>Content</div>;
```

Prefer CSS classes over inline styles. See [layout-forcing properties gist](https://gist.github.com/paulirish/5d52fb081b3570c81e3a) for more information.

---

## Cache Repeated Function Calls

Use a module-level Map to cache function results when the same function is called repeatedly with the same inputs.

**Incorrect (redundant computation):**

```typescript
function ProjectList({ projects }: { projects: Project[] }) {
  return (
    <div>
      {projects.map((project) => {
        const slug = slugify(project.name); // Called 100+ times for same names
        return <ProjectCard key={project.id} slug={slug} />;
      })}
    </div>
  );
}
```

**Correct (cached results):**

```typescript
const slugifyCache = new Map<string, string>();

function cachedSlugify(text: string): string {
  if (slugifyCache.has(text)) return slugifyCache.get(text)!;
  const result = slugify(text);
  slugifyCache.set(text, result);
  return result;
}
```

Use a Map (not a hook) so it works everywhere: utilities, event handlers, not just React components.

Reference: [How we made the Vercel Dashboard twice as fast](https://vercel.com/blog/how-we-made-the-vercel-dashboard-twice-as-fast)

---

## Cache Storage API Calls

`localStorage`, `sessionStorage`, and `document.cookie` are synchronous and expensive. Cache reads in memory.

**Incorrect (reads storage on every call):**

```typescript
function getTheme() {
  return localStorage.getItem("theme") ?? "light";
}
// Called 10 times = 10 storage reads
```

**Correct (Map cache):**

```typescript
const storageCache = new Map<string, string | null>();

function getLocalStorage(key: string) {
  if (!storageCache.has(key)) {
    storageCache.set(key, localStorage.getItem(key));
  }
  return storageCache.get(key);
}

function setLocalStorage(key: string, value: string) {
  localStorage.setItem(key, value);
  storageCache.set(key, value);
}
```

**Invalidate on external changes:**

```typescript
window.addEventListener("storage", (e) => {
  if (e.key) storageCache.delete(e.key);
});

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") storageCache.clear();
});
```

---

## Build Index Maps for Repeated Lookups

Multiple `.find()` calls by the same key should use a Map.

**Incorrect (O(n) per lookup):**

```typescript
function processOrders(orders: Order[], users: User[]) {
  return orders.map((order) => ({
    ...order,
    user: users.find((u) => u.id === order.userId),
  }));
}
```

**Correct (O(1) per lookup):**

```typescript
function processOrders(orders: Order[], users: User[]) {
  const userById = new Map(users.map((u) => [u.id, u]));

  return orders.map((order) => ({
    ...order,
    user: userById.get(order.userId),
  }));
}
```

Build map once O(n), then all lookups are O(1). For 1000 orders x 1000 users: 1M ops down to 2K ops.

---

## Use Loop for Min/Max Instead of Sort

Finding the smallest or largest element only requires a single pass. Sorting is O(n log n) waste.

**Incorrect (O(n log n)):**

```typescript
function getLatestProject(projects: Project[]) {
  const sorted = [...projects].sort((a, b) => b.updatedAt - a.updatedAt);
  return sorted[0];
}
```

**Correct (O(n)):**

```typescript
function getLatestProject(projects: Project[]) {
  if (projects.length === 0) return null;

  let latest = projects[0];
  for (let i = 1; i < projects.length; i++) {
    if (projects[i].updatedAt > latest.updatedAt) latest = projects[i];
  }
  return latest;
}
```

`Math.min(...arr)` / `Math.max(...arr)` works for small arrays but throws on very large arrays due to spread operator limitations (~124K in Chrome, ~638K in Safari).
