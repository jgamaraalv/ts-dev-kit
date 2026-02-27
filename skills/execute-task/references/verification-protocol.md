# Verification Protocol

Every task runs a before/after verification cycle: capture baseline → make changes → verify no regressions and improvements achieved.

## MCP detection

At the start of verification planning, detect which testing MCPs are available by checking for their tool prefixes:

| MCP | Tool prefix | Use for |
|-----|-------------|---------|
| Playwright | `mcp__plugin_playwright_playwright__*` | Visual verification, interaction testing, screenshots |
| Chrome DevTools | `mcp__chrome-devtools__*` | Performance traces, network analysis, console checks |
| Neither | — | Shell-only checks (curl, CLI commands, build output) |

Use ToolSearch to confirm availability before including MCP-based checks in the plan.

## Domain-specific test catalog

### Frontend tasks

**With browser MCPs (playwright or chrome-devtools):**
1. Navigate to each affected page/route.
2. Capture screenshots of key states (idle, loading, error, success).
3. Measure performance:
   - Chrome DevTools: `performance_start_trace` → interact → `performance_stop_trace` → `performance_analyze_insight`.
   - Playwright: `browser_navigate` with timing, `browser_take_screenshot`.
4. Verify interactive elements: click buttons, fill forms, check navigation flows.
5. Check browser console for errors or warnings.

**Without browser MCPs:**
1. Run build and record bundle size (`ls -la` on build output).
2. Run lint and type checking.
3. Run existing test suite and record pass/fail counts.

### Backend tasks

**API endpoint testing:**
1. Identify affected endpoints from the task scope.
2. Record baseline responses via curl:
   ```bash
   curl -s -w "\nHTTP %{http_code} | %{time_total}s" <endpoint>
   ```
3. After changes, re-run identical requests and compare status codes, response shapes, and timing.

**With Postman/API MCPs (if available):**
- Use the MCP to send structured requests and validate response schemas.

### Database tasks

1. Record current schema state for affected tables (e.g., `\d+ table_name` in psql).
2. After migration, verify schema matches expectations.
3. Run sample queries to verify data integrity.

### Shared/library tasks

1. Run type checking across all dependent packages.
2. Run tests in all packages that import the changed code.
3. Verify no new type errors introduced downstream.

## Baseline capture protocol

1. Run standard quality gates first: lint, build, test — record pass/fail and counts.
2. Run domain-specific checks from the catalog above.
3. Store results in a structured format for comparison:

```
Baseline:
- lint: pass
- build: pass (bundle: 245KB)
- tests: 42 passed, 0 failed
- page /receive: screenshot captured, LCP 1.2s
- GET /api/resource: 200, 45ms
```

## Post-change verification protocol

1. Re-run every baseline check with identical parameters.
2. Build the comparison table:

| Check | Baseline | After | Delta | Status |
|-------|----------|-------|-------|--------|
| lint | pass | pass | — | ok |
| build | pass (245KB) | pass (238KB) | -7KB | improved |
| tests | 42 pass | 45 pass | +3 | improved |
| LCP /receive | 1.2s | 0.9s | -0.3s | improved |
| GET /api/resource | 200, 45ms | 200, 42ms | -3ms | ok |

3. Status classification:
   - **ok**: no change or negligible change.
   - **improved**: measurable improvement.
   - **regression**: measurable degradation — must be fixed before task completion.

4. If regressions exist, fix and re-verify until clean.

## Results file

When the task document specifies a results file path, create a markdown file at that path containing:
1. Summary of changes made.
2. Full comparison table.
3. Key improvements highlighted.
4. Any regressions that were found and how they were resolved.
