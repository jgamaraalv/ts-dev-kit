# Rendering Performance

Optimize DOM rendering, hydration, and visual transitions.

## Table of Contents

- [Animate SVG Wrapper Instead of SVG Element](#animate-svg-wrapper-instead-of-svg-element)
- [CSS content-visibility for Long Lists](#css-content-visibility-for-long-lists)
- [Hoist Static JSX Elements](#hoist-static-jsx-elements)
- [Prevent Hydration Mismatch Without Flickering](#prevent-hydration-mismatch-without-flickering)
- [Use useTransition Over Manual Loading States](#use-usetransition-over-manual-loading-states)

---

## Animate SVG Wrapper Instead of SVG Element

Many browsers don't have hardware acceleration for CSS3 animations on SVG elements. Wrap SVG in a `<div>` and animate the wrapper instead.

**Incorrect (no hardware acceleration):**

```tsx
function LoadingSpinner() {
  return (
    <svg className="animate-spin" width="24" height="24" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" stroke="currentColor" />
    </svg>
  );
}
```

**Correct (hardware accelerated):**

```tsx
function LoadingSpinner() {
  return (
    <div className="animate-spin">
      <svg width="24" height="24" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" stroke="currentColor" />
      </svg>
    </div>
  );
}
```

Applies to all CSS transforms and transitions (`transform`, `opacity`, `translate`, `scale`, `rotate`).

---

## CSS content-visibility for Long Lists

Apply `content-visibility: auto` to defer off-screen rendering.

```css
.message-item {
  content-visibility: auto;
  contain-intrinsic-size: 0 80px;
}
```

```tsx
function MessageList({ messages }: { messages: Message[] }) {
  return (
    <div className="overflow-y-auto h-screen">
      {messages.map((msg) => (
        <div key={msg.id} className="message-item">
          <Avatar user={msg.author} />
          <div>{msg.content}</div>
        </div>
      ))}
    </div>
  );
}
```

For 1000 messages, browser skips layout/paint for ~990 off-screen items (10x faster initial render).

---

## Hoist Static JSX Elements

Extract static JSX outside components to avoid re-creation.

**Incorrect (recreates element every render):**

```tsx
function LoadingSkeleton() {
  return <div className="animate-pulse h-20 bg-gray-200" />;
}

function Container() {
  return <div>{loading && <LoadingSkeleton />}</div>;
}
```

**Correct (reuses same element):**

```tsx
const loadingSkeleton = <div className="animate-pulse h-20 bg-gray-200" />;

function Container() {
  return <div>{loading && loadingSkeleton}</div>;
}
```

Especially helpful for large and static SVG nodes. React Compiler automatically hoists static JSX when enabled.

---

## Prevent Hydration Mismatch Without Flickering

When rendering content that depends on client-side storage (localStorage, cookies), avoid both SSR breakage and post-hydration flickering by injecting a synchronous inline script that updates the DOM before React hydrates.

**Incorrect (visual flickering):**

```tsx
function ThemeWrapper({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState("light");

  useEffect(() => {
    const stored = localStorage.getItem("theme");
    if (stored) setTheme(stored);
  }, []);

  return <div className={theme}>{children}</div>;
}
```

**Correct (no flicker, no hydration mismatch):**

Use an inline `<script>` tag with a self-executing function that reads localStorage synchronously and sets the className on the wrapper element before React hydrates. The script runs before the browser paints, ensuring correct initial render.

```tsx
function ThemeWrapper({ children }: { children: ReactNode }) {
  return (
    <>
      <div id="theme-wrapper">{children}</div>
      {/* Inline script reads localStorage and sets className synchronously */}
      <ThemeScript />
    </>
  );
}
```

The inline script executes synchronously before showing the element. Useful for theme toggles, user preferences, and authentication states.

---

## Use useTransition Over Manual Loading States

Use `useTransition` instead of manual `useState` for loading states. Provides built-in `isPending` state and automatically manages transitions.

**Incorrect (manual loading state):**

```tsx
function SearchResults() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async (value: string) => {
    setIsLoading(true);
    setQuery(value);
    const data = await fetchResults(value);
    setResults(data);
    setIsLoading(false);
  };

  return (
    <>
      <input onChange={(e) => handleSearch(e.target.value)} />
      {isLoading && <Spinner />}
      <ResultsList results={results} />
    </>
  );
}
```

**Correct (useTransition):**

```tsx
import { useTransition, useState } from "react";

function SearchResults() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isPending, startTransition] = useTransition();

  const handleSearch = (value: string) => {
    setQuery(value);

    startTransition(async () => {
      const data = await fetchResults(value);
      setResults(data);
    });
  };

  return (
    <>
      <input onChange={(e) => handleSearch(e.target.value)} />
      {isPending && <Spinner />}
      <ResultsList results={results} />
    </>
  );
}
```

Benefits: automatic pending state, error resilience, better responsiveness, interrupt handling (new transitions cancel pending ones).

Reference: [useTransition](https://react.dev/reference/react/useTransition)
