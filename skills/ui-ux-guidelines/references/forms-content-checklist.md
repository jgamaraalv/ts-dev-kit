# Forms, Content & Pre-Delivery Checklist

Rules for forms, content handling, navigation, dark mode, locale, and hydration. Includes the pre-delivery checklist. Loaded by the dispatch hub for form reviews and final delivery checks.

---

## Forms

- Inputs need `autocomplete` attribute and meaningful `name`
- Use correct `type` (`email`, `tel`, `url`, `number`, `search`) and `inputmode` for virtual keyboards
- Never block paste (`onPaste` + `preventDefault`)
- Labels must be clickable: use `htmlFor` matching `id`, or wrap control in `<label>`
- Disable spellcheck on emails, codes, and usernames: `spellCheck={false}`
- Checkboxes/radios: label and control share a single hit target (no dead zones)
- Submit button stays enabled until request starts; show spinner during request
- Errors inline next to fields; focus the first error field on submit
- Placeholders end with `…` and show an example pattern (e.g., `"Ex: nome@email.com…"`)
- Use `autocomplete="off"` on non-auth fields where password manager triggers are unwanted
- Warn before navigation with unsaved changes (`beforeunload` event or router guard)

---

## Content Handling

- Text containers must handle long content: use `truncate`, `line-clamp-*`, or `break-words`
- Flex children that contain text need `min-w-0` to allow text truncation to work
- Always handle empty states — never render broken UI for empty strings or arrays
- User-generated content: design and test for short, average, and very long inputs

---

## Navigation & State

- URL reflects state — filters, tabs, pagination, and expanded panels belong in query params
- Links must use `<a>`/`<Link>` to support Cmd/Ctrl+click and middle-click
- Deep-link all stateful UI — if it uses `useState`, consider URL sync via `nuqs` or similar
- Destructive actions require a confirmation modal or undo window — never immediate execution

---

## Dark Mode & Theming

- Set `color-scheme: dark` on `<html>` for dark themes (fixes scrollbar and native input appearance)
- `<meta name="theme-color">` must match the page background color
- Native `<select>` elements need explicit `background-color` and `color` for Windows dark mode

---

## Locale & i18n

- Dates and times: use `Intl.DateTimeFormat` — never hardcode date formats
- Numbers and currency: use `Intl.NumberFormat` — never hardcode number/currency formats
- Detect language via `Accept-Language` header or `navigator.languages` — not by IP geolocation

---

## Hydration Safety

- Controlled inputs with `value` need `onChange` (or use `defaultValue` for uncontrolled)
- Date/time rendering: guard against hydration mismatch between server and client
- `suppressHydrationWarning` only where truly necessary (e.g., system clock, browser extensions)

---

## Content & Copy

- Active voice: "Install the CLI" not "The CLI will be installed"
- Sentence case for headings (e.g., "Configure notifications")
- Numerals for counts: "8 items" not "eight items"
- Specific button labels: "Save API Key" not "Continue"
- Error messages include the fix or next step — not just the problem description
- Second person ("you"); avoid first person ("I")
- Use `&` over "and" where space is constrained

---

## Pre-Delivery Checklist

Before delivering UI code, verify all items below.

### Visual Quality

- [ ] No emojis used as icons (SVG only)
- [ ] All icons from a consistent icon set (Lucide for this project)
- [ ] Brand logos verified from Simple Icons
- [ ] Hover states do not cause layout shift
- [ ] Theme colors used directly (e.g., `bg-primary`), not wrapped in `var()`

### Forms

- [ ] All inputs have `autocomplete` and meaningful `name`
- [ ] Correct `type` and `inputmode` on inputs
- [ ] Paste is not blocked
- [ ] All labels are clickable (`htmlFor` or wrapping)
- [ ] Submit button disabled + spinner during request
- [ ] Errors shown inline; first error focused on submit

### Light/Dark Mode

- [ ] Light mode text meets 4.5:1 contrast minimum
- [ ] Glass/transparent elements are visible in light mode
- [ ] Borders visible in both light and dark modes
- [ ] Both modes tested before delivery
- [ ] `color-scheme` set on `<html>` for dark themes

### Layout

- [ ] Floating elements have proper spacing from viewport edges
- [ ] No content hidden behind fixed navbars
- [ ] Responsive at 375px, 768px, 1024px, 1440px
- [ ] No horizontal scroll on mobile
- [ ] Safe area insets applied for full-bleed layouts

### Typography & Copy

- [ ] `…` (U+2026) used instead of `...` (three dots)
- [ ] Loading states end with `…`
- [ ] `font-variant-numeric: tabular-nums` on number columns
- [ ] `text-wrap: balance` on headings
- [ ] Error messages include the next step, not just the problem

### i18n & Hydration

- [ ] Dates use `Intl.DateTimeFormat`
- [ ] Numbers/currency use `Intl.NumberFormat`
- [ ] Controlled inputs have `onChange`; date/time rendering guarded against hydration mismatch
