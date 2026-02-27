# CLS — Cumulative Layout Shift

**Good:** ≤ 0.1 | **Needs improvement:** 0.1–0.25 | **Poor:** > 0.25
(measured at the 75th percentile of field loads)

CLS measures the largest burst of layout shift scores across the entire page
lifecycle. A layout shift occurs when a visible element changes its start
position from one rendered frame to the next.

## How the CLS score is calculated

```
layout shift score = impact fraction × distance fraction

impact fraction = combined area of unstable elements (before + after)
                  ─────────────────────────────────────────────────
                  total viewport area

distance fraction = greatest distance any unstable element moved
                    ──────────────────────────────────────────────
                    largest viewport dimension (width or height)
```

Shifts are grouped into **session windows** (max 5 s, max 1 s gap between
shifts). CLS = the session window with the highest cumulative score.

**Example:** element moves from top 25% to top 50% of viewport →
- impact fraction ≈ 0.75 (covers 75% of viewport across both positions)
- distance fraction = 0.25 (moved 25% of viewport height)
- layout shift score = 0.75 × 0.25 = **0.1875**

## Expected vs. unexpected layout shifts

Only **unexpected** shifts count toward CLS. User-initiated shifts are excluded:
- Clicking a button that expands content ✓ (expected)
- Content jumping after an ad loads without reserved space ✗ (unexpected)
- A banner appearing after page load without reserved space ✗ (unexpected)

Shifts within 500 ms of a user interaction do not count.
Animations and transitions using CSS `transform` do not cause layout shifts —
they run off the main thread and do not trigger layout recalculation.

## Common causes and fixes

### Images and videos without dimensions
Images load asynchronously; without explicit dimensions, the browser doesn't
know how much space to reserve.

```html
<!-- Bad: no dimensions, causes layout shift when image loads -->
<img src="/hero.jpg" alt="hero">

<!-- Good: explicit width/height let browser reserve space -->
<img src="/hero.jpg" alt="hero" width="1200" height="600">

<!-- Also good for responsive images -->
<img src="/hero.jpg" alt="hero" width="1200" height="600"
     style="width: 100%; height: auto;">
```

The `aspect-ratio` CSS property is a modern alternative:
```css
img { aspect-ratio: 16 / 9; width: 100%; }
```

### Ads, embeds, and iframes without reserved space
Always define a minimum height for ad slots and dynamic embed containers:
```css
.ad-slot { min-height: 250px; }
.video-embed { aspect-ratio: 16 / 9; }
```

### Dynamically injected content above existing content
Avoid inserting banners, cookie notices, or promotional elements above existing
page content after load. If necessary, reserve the space in the layout before
content loads, or insert below the fold.

### Web fonts causing FOUT/FOIT shifts
Flash of Unstyled Text (FOUT) can cause layout shifts if the fallback font
has different metrics than the loaded font.

```css
/* Preferred: font-display: optional never shows fallback, eliminates shift */
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont.woff2') format('woff2');
  font-display: optional;
}
```

Use the `size-adjust`, `ascent-override`, `descent-override`, and
`line-gap-override` descriptors to match fallback font metrics:
```css
@font-face {
  font-family: 'MyFont-fallback';
  src: local('Arial');
  size-adjust: 104%;
  ascent-override: 90%;
}
```

### Animations that trigger layout (not using transform)
CSS properties that trigger layout recalculation cause shifts:
- **Avoid:** `top`, `left`, `right`, `bottom`, `margin`, `padding`, `width`, `height`
- **Use instead:** `transform: translate()`, `transform: scale()`, `opacity`

```css
/* Bad: triggers layout */
.slide-in { transition: margin-left 0.3s ease; }

/* Good: compositor-only, no layout shift */
.slide-in { transition: transform 0.3s ease; transform: translateX(0); }
.slide-in.hidden { transform: translateX(-100%); }
```

## bfcache eligibility improves CLS

Pages restored from the back/forward cache (bfcache) don't reload resources,
which eliminates many common layout shifts. Ensure your pages are bfcache
eligible:
- Avoid `unload` event listeners
- Don't use `Cache-Control: no-store` unnecessarily
- Close open `IndexedDB` transactions before navigating away
- Avoid `window.opener` references

Check bfcache eligibility in Chrome DevTools: Application → Back/forward cache.

## Measure CLS in JavaScript

```js
let clsValue = 0;
let clsEntries = [];

new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (!entry.hadRecentInput) {
      clsValue += entry.value;
      clsEntries.push(entry);
    }
  }
}).observe({ type: 'layout-shift', buffered: true });
```

Prefer `onCLS()` from the `web-vitals` library — it correctly implements
session windowing and excludes user-initiated shifts.

## Key nuances

- CLS is measured for the entire page lifecycle, including after user interaction
- `layout-shift` entries from iframes are not visible in the parent frame's
  raw API — the web-vitals library does not cover this gap either
- CLS is 0 for pages with no layout shifts (even with heavy JS)
- Adding new DOM elements that push existing elements down = layout shift
  only if it changes the **start position** of existing visible elements
