# LCP — Largest Contentful Paint

**Good:** ≤ 2.5 s | **Needs improvement:** 2.5–4.0 s | **Poor:** > 4.0 s
(measured at the 75th percentile of field loads)

## What qualifies as the LCP element?

Only these element types are considered:
- `<img>` elements (including `<image>` inside SVG)
- `<video>` elements (poster image only)
- Block-level elements with a CSS `background-image` loaded via `url()`
- Block-level text elements (`<p>`, `<h1>`, etc.)

Elements excluded from LCP consideration: full-viewport background images,
`opacity: 0` elements, placeholder images, elements the browser heuristically
considers non-contentful.

LCP is the *last* candidate emitted before user interaction or page hide —
the browser continuously updates the candidate as larger elements paint.

## LCP timing breakdown

LCP time = TTFB + resource load delay + resource load time + element render time

1. **TTFB** — time until first byte of HTML arrives
2. **Resource load delay** — time from TTFB until the LCP resource starts downloading
3. **Resource load time** — how long the resource takes to download
4. **Element render time** — time from download complete to paint on screen

Diagnosing which phase dominates tells you what to fix.

## Common causes and fixes

### Slow TTFB (phase 1)
- Use a CDN geographically close to users
- Enable server-side caching, edge caching, or stale-while-revalidate
- Reduce database query time / server processing time
- Target: TTFB ≤ 800 ms

### LCP image not discoverable (phase 2)
- **Don't** hide the LCP image behind `data-src`, JS lazy-loading, or CSS
  `background-image` in a stylesheet — the preload scanner can't find it
- **Do** use `<img src="...">` or `<img srcset="...">` in the HTML source
- **Do** use `<link rel="preload" as="image" href="...">` if the image must
  come from CSS/JS
- **Do** prefer SSR/SSG over CSR — CSR blocks image discovery behind JS execution
- Remove `loading="lazy"` from the LCP image; lazy-loading delays it

### LCP image deprioritized (phase 2)
```html
<!-- Add fetchpriority="high" to your LCP image -->
<img src="/hero.jpg" fetchpriority="high" alt="..." width="1200" height="600">

<!-- Or on the preload link -->
<link rel="preload" as="image" href="/hero.jpg" fetchpriority="high">
```

### Slow resource download (phase 3)
- Compress images (use WebP or AVIF; target < 200 KB for hero images)
- Use `srcset` + `sizes` to serve appropriately sized images per viewport
- Serve from a CDN with HTTP/2 or HTTP/3
- Defer non-critical resources to reduce bandwidth contention

### Render delay (phase 4)
- Minimize render-blocking scripts and stylesheets in `<head>`
- Avoid long tasks on the main thread that block painting
- If using a web font for LCP text: `font-display: optional` or preload the font

## JavaScript API (raw, without web-vitals library)

```js
new PerformanceObserver((list) => {
  const entries = list.getEntries();
  const last = entries[entries.length - 1];
  console.log('LCP candidate:', last.startTime, last.element);
}).observe({ type: 'largest-contentful-paint', buffered: true });
```

Prefer `onLCP()` from the `web-vitals` library — it handles bfcache restores,
prerendered page activation, and iframe aggregation automatically.

## Key nuances

- LCP from bfcache restores counts as a new page visit — measure it
- Images inside cross-origin iframes contribute to LCP but are not observable
  from the parent frame via the raw API (web-vitals library handles this)
- For prerendered pages, measure LCP from `activationStart`, not navigation start
- The largest element is determined by rendered size in the viewport, not
  intrinsic dimensions
