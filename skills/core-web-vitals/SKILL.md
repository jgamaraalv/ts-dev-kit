---
name: core-web-vitals
description: "Core Web Vitals reference for measuring, diagnosing, and improving LCP, INP, and CLS. Use when: (1) auditing page performance against Google's thresholds, (2) implementing the web-vitals JS library for field monitoring, (3) diagnosing slow LCP, high INP, or layout shifts, (4) choosing between field and lab measurement tools, (5) optimizing specific metrics with the Chrome team's top recommendations, (6) explaining what each metric measures to non-technical stakeholders, or (7) generating a visual CWV report from metric values or a Lighthouse JSON file."
allowed-tools: Bash(python3 *)
---

# Core Web Vitals

The three stable Core Web Vitals, each measured at the **75th percentile** of
real page loads (segmented by mobile and desktop):

| Metric | Measures | Good | Needs Improvement | Poor |
|--------|----------|------|-------------------|------|
| **LCP** — Largest Contentful Paint | Loading | ≤ 2.5 s | 2.5–4.0 s | > 4.0 s |
| **INP** — Interaction to Next Paint | Interactivity | ≤ 200 ms | 200–500 ms | > 500 ms |
| **CLS** — Cumulative Layout Shift | Visual stability | ≤ 0.1 | 0.1–0.25 | > 0.25 |

A page **passes** Core Web Vitals only if all three metrics meet "Good" at the 75th percentile.

## Quick setup: measure all three in the field

```bash
npm install web-vitals
```

```js
import { onCLS, onINP, onLCP } from 'web-vitals';

function sendToAnalytics(metric) {
  const body = JSON.stringify(metric);
  (navigator.sendBeacon && navigator.sendBeacon('/analytics', body)) ||
    fetch('/analytics', { body, method: 'POST', keepalive: true });
}

onCLS(sendToAnalytics);
onINP(sendToAnalytics);
onLCP(sendToAnalytics);
```

Each callback receives `{ name, value, rating, delta, id, navigationType }`.
`rating` is `"good"`, `"needs-improvement"`, or `"poor"`.

> The `web-vitals` library handles bfcache restores, prerendered pages, iframe
> aggregation, and other edge cases that raw PerformanceObserver does not.

## Tools matrix

| Tool | Type | LCP | INP | CLS | Notes |
|------|------|-----|-----|-----|-------|
| Chrome User Experience Report (CrUX) | Field | ✓ | ✓ | ✓ | 28-day rolling window of real users |
| PageSpeed Insights | Field + Lab | ✓ | ✓ | ✓ | Field = CrUX data; Lab = Lighthouse |
| Search Console CWV report | Field | ✓ | ✓ | ✓ | Groups URLs by template |
| Chrome DevTools Performance panel | Field + Lab | ✓ | ✓ | ✓ | Local profiling, interaction tracing |
| Lighthouse | Lab | ✓ | TBT* | ✓ | CI integration; INP → use TBT as proxy |

*Lighthouse uses **Total Blocking Time (TBT)** as a lab proxy for INP. TBT
correlates with INP but does not replace field measurement.

## Supporting metrics (non-Core but diagnostic)

- **FCP** (First Contentful Paint) — diagnoses render-blocking resources upstream of LCP
- **TTFB** (Time to First Byte) — server response time; directly affects LCP
- **TBT** (Total Blocking Time) — lab proxy for INP; identifies long tasks

## When to read reference files

| Reference | Read when… |
|-----------|-----------|
| [references/lcp.md](references/lcp.md) | LCP > 2.5 s, diagnosing slow image/text load, preload/CDN questions |
| [references/inp.md](references/inp.md) | INP > 200 ms, slow click/key/tap response, long task investigations |
| [references/cls.md](references/cls.md) | CLS > 0.1, elements jumping on scroll or load, font/image shift |
| [references/tools.md](references/tools.md) | Setting up monitoring, using DevTools/Lighthouse/PSI, top-9 optimization checklist |

## Generate a visual report

When the user provides metric values or a Lighthouse JSON file, generate an interactive HTML report and open it in the browser:

To locate the script, find `scripts/visualize.py` relative to this skill's directory. The path depends on how ts-dev-kit is installed:
- **Project scope**: `skills/core-web-vitals/scripts/visualize.py` or `.claude/skills/core-web-vitals/scripts/visualize.py`
- **Personal scope**: `~/.claude/skills/core-web-vitals/scripts/visualize.py`
- **Plugin scope**: resolve via `node_modules/@jgamaraalv/ts-dev-kit/skills/core-web-vitals/scripts/visualize.py`

Use `find` or `ls` to discover the actual path, then run:

```bash
# From manual values (replace SCRIPT_PATH with the discovered path)
python3 SCRIPT_PATH/visualize.py \
  --lcp 2.1 --inp 180 --cls 0.05 \
  --url https://example.com

# From a Lighthouse JSON output
python3 SCRIPT_PATH/visualize.py \
  --lighthouse lighthouse-report.json

# Custom output path, no auto-open
python3 SCRIPT_PATH/visualize.py \
  --lcp 3.8 --inp 420 --cls 0.12 \
  --output cwv-report.html --no-open
```

The script (`scripts/visualize.py`) requires only Python 3 stdlib — no packages to install.
It outputs a self-contained HTML file with color-coded metric cards, a visual progress bar showing where each value falls on the Good/Needs Improvement/Poor scale, and an overall PASS/FAIL/NEEDS IMPROVEMENT verdict.

## Metric lifecycle

Metrics progress through: **Experimental → Pending → Stable**.
All three current Core Web Vitals (LCP, CLS, INP) are **Stable**.
INP replaced FID (First Input Delay) in March 2024.
Changes to stable metrics follow an annual cadence with advance notice.
