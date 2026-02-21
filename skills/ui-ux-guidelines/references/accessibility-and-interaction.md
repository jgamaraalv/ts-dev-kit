# Accessibility & Interaction Reference

Rules for accessible, touch-friendly interfaces. Loaded by the dispatch hub when reviewing accessibility or interaction code.

---

## Accessibility (CRITICAL)

### Focus & Keyboard

- `focus-states` — Visible focus rings on all interactive elements; use `:focus-visible` over `:focus`
- `keyboard-nav` — Tab order matches visual order; interactive elements need `onKeyDown`/`onKeyUp` handlers
- `focus-within` — Use `:focus-within` for compound controls (e.g., search with icon)
- `scroll-margin` — `scroll-margin-top` on heading anchors to avoid content hidden behind fixed headers
- `heading-hierarchy` — `<h1>`--`<h6>` hierarchical; include skip link for main content

### ARIA & Semantics

- `aria-labels` — `aria-label` for icon-only buttons; `aria-hidden="true"` for decorative icons
- `aria-live` — Async updates (toasts, loading, validation) need `aria-live="polite"`
- `semantic-first` — Use semantic HTML (`<button>`, `<a>`, `<label>`, `<table>`) before reaching for ARIA
- `color-contrast` — Minimum 4.5:1 ratio for normal text; color must not be the only indicator

### Form Accessibility

- `form-labels` — Use `<label>` with `htmlFor` or wrapping control on all inputs
- Checkboxes/radios: label and control share a single hit target (no dead zones)

---

## Touch & Interaction (CRITICAL)

### Touch Targets

- `touch-target-size` — Minimum 44x44px touch targets
- `touch-action` — Add `touch-action: manipulation` to interactive elements (prevents double-tap zoom delay)
- `tap-highlight` — Set `-webkit-tap-highlight-color` intentionally (don't leave as default)

### Click & Hover

- `hover-vs-tap` — Use click/tap for primary interactions, never hover-only
- `cursor-pointer` — Add `cursor-pointer` to all clickable elements
- `loading-buttons` — Disable button during async operations; show loading state
- `error-feedback` — Clear error messages placed near the problem field

### Containment & Drag

- `overscroll` — Add `overscroll-behavior: contain` in modals, drawers, and sheets
- `drag-ux` — During drag operations: disable text selection, use `inert` on dragged elements
- `autofocus` — Use `autoFocus` sparingly — desktop only, single primary input; avoid on mobile

---

## Anti-patterns to Flag

- `user-scalable=no` or `maximum-scale=1` — disables zoom (accessibility violation)
- `outline-none` / `outline: 0` without a `:focus-visible` replacement
- `<div>` or `<span>` with click handlers — use `<button>` or `<a>`
- Icon-only buttons without `aria-label`
- Form inputs without associated labels
- `autoFocus` without clear justification on mobile

---

## Interaction Review Checklist

- [ ] All clickable elements have `cursor-pointer`
- [ ] Hover states provide clear visual feedback without layout shift
- [ ] Transitions are smooth (150--300ms)
- [ ] Focus states visible for keyboard navigation (`:focus-visible`)
- [ ] Destructive actions have confirmation modal or undo
- [ ] All images have descriptive alt text (or `alt=""` for decorative)
- [ ] Async updates (toasts, validation) use `aria-live="polite"`
- [ ] Interactive elements have keyboard handlers
