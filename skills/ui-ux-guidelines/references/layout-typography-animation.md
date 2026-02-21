# Layout, Typography & Animation Reference

Rules for performance, responsive layout, typography, color, and animation. Loaded by the dispatch hub when reviewing visual and performance aspects.

---

## Performance (HIGH)

- `image-optimization` — Use `srcset` and `loading="lazy"` for below-fold images
- `image-priority` — Above-fold critical images: `priority` (Next.js) or `fetchpriority="high"`
- `reduced-motion` — Respect `prefers-reduced-motion` media query
- `content-jumping` — Reserve space for async content (skeleton, min-height)
- `virtualize-lists` — Large lists (>50 items): virtualize (`virtua`, `content-visibility: auto`)
- `no-layout-reads` — No layout reads in render (`getBoundingClientRect`, `offsetHeight`, `offsetWidth`, `scrollTop`)
- `batch-dom` — Batch DOM reads/writes; avoid interleaving reads and writes
- `controlled-inputs` — Prefer uncontrolled inputs; controlled inputs must be cheap per keystroke
- `preconnect` — Add `<link rel="preconnect">` for CDN and asset domains
- `font-preload` — Critical fonts: `<link rel="preload" as="font">` with `font-display: swap`

---

## Layout & Responsive (HIGH)

- `horizontal-scroll` — Ensure all content fits viewport width; no overflow-x
- `z-index-management` — Define a z-index scale (10, 20, 30, 50); avoid magic numbers
- `safe-areas` — Full-bleed layouts need `env(safe-area-inset-*)` for notches and home indicators
- `flex-grid-layout` — Prefer flex/grid over JS measurement for layout
- `overflow-x` — Use `overflow-x-hidden` on containers to fix content overflow causing scrollbars
- `readable-font-size` — Minimum 16px body text on mobile

### Spacing & Containers

- Floating elements have proper spacing from viewport edges
- No content hidden behind fixed navbars — account for header height
- Use same `max-w-*` across pages for consistent container widths
- Responsive at 375px, 768px, 1024px, 1440px

---

## Typography & Color (MEDIUM)

- `line-length` — Limit to 65--75 characters per line (`max-w-prose`)
- `font-pairing` — Match heading and body font personalities (serif+sans, display+neutral)
- `ellipsis` — Use `…` (U+2026), never `...` (three dots)
- `curly-quotes` — Use `"` `"` (curly quotes), not straight `"`
- `nbsp` — Non-breaking spaces for units and brand names: `10&nbsp;MB`, `⌘&nbsp;K`
- `loading-text` — Loading states end with `…`: `"Carregando…"`, `"Salvando…"`
- `tabular-nums` — Use `font-variant-numeric: tabular-nums` for number columns and comparisons
- `heading-wrap` — Use `text-wrap: balance` or `text-pretty` on headings (prevents widows)

### Light/Dark Mode Contrast

| Rule                      | Do                                  | Don't                                   |
| ------------------------- | ----------------------------------- | --------------------------------------- |
| **Glass card light mode** | Use `bg-white/80` or higher opacity | Use `bg-white/10` (too transparent)     |
| **Text contrast light**   | Use `#0F172A` (slate-900) for text  | Use `#94A3B8` (slate-400) for body text |
| **Muted text light**      | Use `#475569` (slate-600) minimum   | Use gray-400 or lighter                 |
| **Border visibility**     | Use `border-gray-200` in light mode | Use `border-white/10` (invisible)       |

---

## Animation (MEDIUM)

- `duration-timing` — Use 150--300ms for micro-interactions; ease-out for entrances
- `transform-performance` — Animate `transform` and `opacity` only; never `width`/`height`
- `loading-states` — Show skeleton screens or spinners for content loading
- `no-transition-all` — Never `transition: all` — list properties explicitly
- `transform-origin` — Set correct `transform-origin` for scale/rotate animations
- `svg-transforms` — SVG: apply transforms on a `<g>` wrapper with `transform-box: fill-box; transform-origin: center`
- `interruptible` — Animations must be interruptible — respond to user input mid-animation

---

## Style Selection (MEDIUM)

- `style-match` — Match visual style to product type (minimalism for SaaS, playful for consumer)
- `consistency` — Apply the same style system across all pages
- `no-emoji-icons` — Use SVG icons (Lucide, Heroicons); never use emojis as UI icons

### Icons & Visual Elements

| Rule                       | Do                                              | Don't                                  |
| -------------------------- | ----------------------------------------------- | -------------------------------------- |
| **No emoji icons**         | Use SVG icons (Heroicons, Lucide, Simple Icons) | Use emojis as UI icons                 |
| **Stable hover states**    | Use color/opacity transitions on hover          | Use scale transforms that shift layout |
| **Correct brand logos**    | Use official SVG from Simple Icons              | Guess or use incorrect logo paths      |
| **Consistent icon sizing** | Fixed viewBox 24x24 with `w-6 h-6`              | Mix different icon sizes randomly      |

---

## Charts & Data (LOW)

- `chart-type` — Match chart type to data relationship (trend -> line, comparison -> bar, part-of-whole -> pie)
- `color-guidance` — Use accessible, colorblind-safe palettes for data series
- `data-table` — Provide a table alternative to charts for accessibility
