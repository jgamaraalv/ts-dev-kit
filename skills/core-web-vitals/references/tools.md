# CWV Tools & Top Optimization Checklist

## Field tools (real user data)

### Chrome User Experience Report (CrUX)
- 28-day rolling window of anonymized Chrome user data
- Aggregated by origin and URL-pattern (template level)
- Requires sufficient traffic (threshold: ~100 qualifying visits/28 days)
- Access via: BigQuery, PageSpeed Insights API, CrUX API, Search Console

### PageSpeed Insights (PSI)
- URL: https://pagespeed.web.dev/
- Shows CrUX field data (if available) + Lighthouse lab audit in one view
- API available for programmatic access:
  ```
  https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=<URL>&strategy=mobile
  ```

### Search Console — Core Web Vitals report
- Groups pages by URL template (not individual URLs)
- Shows "Good", "Needs improvement", "Poor" counts with 28-day CrUX data
- Best for finding which page groups have systematic CWV issues

## Lab tools (simulated/local)

### Lighthouse (Chrome DevTools / CLI / CI)
```bash
npm install -g lighthouse
lighthouse https://example.com --output html --output-path ./report.html
```
- Use `--throttling-method=simulate` for reproducible scores
- INP not measured in Lighthouse — use TBT (Total Blocking Time) as proxy
- Run in incognito to avoid extension interference

### Chrome DevTools Performance panel
- Record interactions to identify long tasks and INP attribution
- Performance Insights panel: shows LCP, CLS, INP with timeline markers
- Rendering panel → "Layout Shift Regions" highlights shifting elements in real time

### web-vitals Chrome extension
- Badge shows live LCP, INP, CLS values as you browse
- Console logs detailed attribution data
- Useful for quick spot-checks without instrumenting analytics

## Top 9 optimizations (Chrome team recommendations)

### INP
1. **Yield often to break up long tasks** — Use `scheduler.yield()` or
   `setTimeout(0)` to give the browser opportunities between work chunks.
   Any JS task > 50 ms becomes a "long task" that blocks interaction handling.

2. **Avoid unnecessary JavaScript** — Code-split, defer non-critical JS, remove
   unused polyfills. Less JS = fewer long tasks = better INP.

3. **Avoid large rendering updates** — Minimize DOM size, batch DOM writes,
   use `requestAnimationFrame` for visual updates, avoid layout thrashing
   (interleaved reads/writes of layout properties).

### LCP
4. **Make the LCP resource discoverable from HTML source and prioritized** —
   Use `<img src>` or `<img srcset>` (not `data-src`). Add `fetchpriority="high"`
   to the LCP image or its `<link rel="preload">`. Remove `loading="lazy"` from LCP.

5. **Aim for instant navigations** — Implement the View Transitions API for
   client-side navigations. Use speculation rules for prerendering next pages:
   ```html
   <script type="speculationrules">
   { "prerender": [{ "where": { "href_matches": "/products/*" } }] }
   </script>
   ```
   Use `rel="prefetch"` for likely next navigations.

6. **Use a CDN to optimize TTFB** — Serve HTML from an edge CDN geographically
   close to users. Edge compute (e.g., Cloudflare Workers, Vercel Edge) can
   stream HTML early while fetching dynamic data in parallel.
   Target TTFB ≤ 800 ms.

### CLS
7. **Set explicit sizes on content loaded from the page** — Add `width` and
   `height` attributes to all `<img>` and `<video>` elements. Use CSS
   `aspect-ratio` for responsive containers. Reserve space for ads and embeds
   with `min-height`.

8. **Ensure pages are eligible for bfcache** — Avoid `unload` listeners,
   `Cache-Control: no-store`, and unclosed `IndexedDB` transactions.
   bfcache restores eliminate load-time layout shifts entirely.

9. **Avoid layout-inducing CSS animations/transitions** — Animate only
   `transform` and `opacity`. These run on the compositor thread and do not
   cause layout shifts. Never animate `top`, `left`, `margin`, `width`, etc.

## Measuring in CI/CD

```js
// Example: assert LCP in Playwright test
import { onLCP } from 'web-vitals';

test('LCP is under 2.5s', async ({ page }) => {
  await page.goto('/');
  const lcp = await page.evaluate(() => new Promise(resolve => {
    onLCP(metric => resolve(metric.value), { reportAllChanges: false });
  }));
  expect(lcp).toBeLessThan(2500);
});
```

For automated CWV regression testing use Lighthouse CI:
```bash
npm install -g @lhci/cli
lhci autorun --collect.url=https://staging.example.com \
  --assert.assertions.largest-contentful-paint=["warn", {"maxNumericValue": 2500}]
```
