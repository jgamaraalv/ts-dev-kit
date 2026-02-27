# TASK_[N]: [Title]

## Overview
[2-3 sentences describing what this task delivers and why it is a cohesive unit
of work. State the concrete value delivered when this task is merged.]

## Dependencies
- Requires merged: [list of TASK_X titles, or "none"]

## Scope — Files (max 30)

| File | Action | Purpose |
|------|--------|---------|
| `path/to/file.ts` | create | What this file contains |
| `path/to/other.ts` | modify | What changes and why |

**Total: N files**

## Success Criteria

- [ ] 1. [Testable, specific condition — maps to a PRD acceptance criterion]
- [ ] 2. [...]

## Non-functional Requirements

- **Performance**: [specific targets, e.g., "p95 API response < 200ms", "LCP < 2.5s"]
- **Security**: [e.g., "all inputs validated with zod schema", "auth guard on all routes"]
- **Accessibility**: [for frontend tasks: WCAG level and specific requirements]
- **Scalability**: [relevant requirements, or "n/a for this task"]

## Verification Plan

### Baseline Checks (run before making changes)

**Quality gates:**
- `tsc` — record pass/fail
- `lint` — record pass/fail
- `test` — record pass/fail + test count
- `build` — record pass/fail + bundle size (if frontend)

**Domain-specific baseline:**
- [Example — API: `GET /api/resource` — record HTTP status and response time]
- [Example — Frontend: navigate to `/feature-page` — capture screenshot and LCP]
- [Example — Database: record current schema of table `users` (columns + types)]

### Post-change Checks

**Quality gates:** [same commands as baseline — all must pass]

**Feature verification:**
- [ ] [Check mapped 1:1 to success criterion 1 — describe exact verification steps]
- [ ] [Check mapped 1:1 to success criterion 2]

**Performance benchmarks:**
- [metric]: target [value], acceptable range [range]

### MCP Checks

**If browser MCPs available (playwright / chrome-devtools):**
- [Specific pages to navigate and screenshot]
- [Specific user interactions to exercise]
- [Specific performance traces to capture]

**If no browser MCPs available (shell-only fallback):**
- [What to verify via build output, curl, or CLI commands]

## Implementation Notes

[Optional: key constraints, patterns to follow, architectural decisions the
executing agent should know. Reference specific file paths or conventions
discovered from the codebase analysis.]
