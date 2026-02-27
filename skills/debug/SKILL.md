---
name: debug
description: "End-to-end debugging workflow that triages, reproduces, and fixes bugs across the full stack using multi-agent orchestration. Use when: (1) encountering runtime errors in the API or web app, (2) investigating failed requests or broken user flows, (3) debugging production issues via Sentry/PostHog, (4) tracing data flow across backend and frontend, or (5) the user reports a bug that spans multiple layers."
argument-hint: "[error-description or sentry-issue-url]"
allowed-tools: Bash(git *)
---

<live_context>
**Recent git changes (regression candidates):**
!`git log --oneline -10 2>/dev/null || echo "(not a git repo)"`

**Working tree status:**
!`git status --short 2>/dev/null || echo "(not a git repo)"`
</live_context>

<trigger_examples>
- "Debug why the form submission fails with a 500 error"
- "The dashboard page shows a blank screen after login"
- "API returns 403 but the user should be authorized"
- "Investigate this Sentry issue: PROJECT-123"
- "The form submits but nothing appears in the list"
- "Debug the notification queue — jobs are stuck"
</trigger_examples>

<task>
$ARGUMENTS
</task>

<workflow>
Follow each phase in order. Each one feeds the next.

<phase_1_triage>
Classify the bug before investigating. This determines which agents to dispatch.

1. Read the error description, stack trace, or reproduction steps provided by the user.
2. Determine the affected layers:

| Layer | Signals |
|-------|---------|
| **Frontend** | UI doesn't render, hydration errors, blank pages, console errors, wrong data displayed |
| **API** | HTTP error codes (4xx/5xx), validation failures, timeout, wrong response body |
| **Database** | Missing data, wrong query results, migration issues, connection errors |
| **Queue/Worker** | Jobs stuck, not processing, duplicate execution, Redis connectivity |
| **Infrastructure** | Docker containers down, ports in use, env vars missing |
| **Cross-cutting** | Data flows correctly in one layer but breaks in another |

3. Check for quick context — run these in parallel:

```bash
# Recent changes that might have introduced the bug
git log --oneline -10
git diff HEAD~3 --stat

# Infrastructure health
docker compose ps
```

4. If the user provided a Sentry issue URL or error ID, query Sentry for the full stack trace and event details.
5. If the user mentions production errors, check PostHog error tracking for frequency and user impact.

State the triage result to the user:

> **TRIAGE: [layer(s)]** — Brief description of what appears to be happening.
</phase_1_triage>

<phase_2_execution_mode>
Based on the triage, decide the execution mode:

**SINGLE-LAYER** — The bug is isolated to one layer. Debug directly without dispatching agents.

**MULTI-LAYER** — The bug spans 2+ layers. Act as orchestrator and dispatch specialized debugging agents.

State the decision:

> **EXECUTION MODE: SINGLE-LAYER** — I will investigate and fix this directly.

OR

> **EXECUTION MODE: MULTI-LAYER** — I will dispatch specialized agents to investigate each layer in parallel.
</phase_2_execution_mode>

<phase_3_reproduce>
Reproduce the bug before investigating. Never fix what you can't reproduce.

<reproduction_strategies>

**API bugs** — Use curl or Bash to hit the endpoint directly:
```bash
# Discover the API base URL and endpoints from CLAUDE.md, package.json, or route files
curl -v http://localhost:<port>/<endpoint> | jq .
```

**Frontend bugs** — Use browser automation MCPs:
1. Call `mcp__chrome-devtools__list_pages` or `mcp__plugin_playwright_playwright__browser_tabs` to check current state.
2. Navigate to the affected page and take a screenshot.
3. Check the browser console for errors.
4. Inspect network requests for failed API calls.

**Queue/Worker bugs** — Check Redis and BullMQ state:
```bash
# Check Redis connectivity
redis-cli ping

# Check queue state — discover the dev command from package.json scripts
# e.g., yarn dev, npm run dev, or the relevant workspace command
```

**Database bugs** — Query directly:
```bash
# Discover database credentials and container names from docker-compose.yml or .env
docker compose exec <db-container> psql -U <user> -c "SELECT * FROM ... LIMIT 5"
```

If reproduction fails, add strategic logging and retry. See references/debug-dispatch.md for logging patterns.
</reproduction_strategies>
</phase_3_reproduce>

<phase_4_investigate>
With the bug reproduced, investigate the root cause.

<single_layer_investigation>
Follow the data flow from the error point backward:

1. Read the source code at the error location.
2. Trace inputs — where does the data come from? What transformations happen?
3. Form a hypothesis about the root cause.
4. Test the hypothesis — add logging, inspect state, check the database.
5. If the hypothesis is wrong, form a new one based on what you learned.

Load relevant skills before diving in:
- Load skills matching the technologies used in the project (discover from package.json).
- Common examples: backend framework skills, ORM/database skills, frontend framework skills, queue/worker skills.
- Read CLAUDE.md and package.json to identify the project's tech stack before selecting skills.

When the bug involves library API misuse, version-specific behavior, or unclear method signatures, query Context7 for up-to-date documentation:
1. `mcp__context7__resolve-library-id` — resolve the library name (e.g., "fastify", "drizzle-orm", "bullmq") to its Context7 ID.
2. `mcp__context7__query-docs` — query with the specific API, method, or error message you're investigating.

Use Context7 when:
- The error message references a library API you're unsure about.
- You suspect a breaking change between versions (check the project's package.json for installed versions first).
- The stack trace points to library internals and you need to understand expected behavior.
- You need to verify correct usage patterns for any project dependency.
</single_layer_investigation>

<multi_layer_investigation>
Dispatch specialized agents in parallel. Each agent investigates its layer independently and reports findings.

See references/debug-dispatch.md for the agent prompt templates and dispatch patterns.

<debugging_roles>

| Role | Agent type | Domain | MCPs |
|------|-----------|--------|------|
| Backend debugger | `debugger` | API routes, use cases, DB queries, server hooks | Sentry, PostHog, Context7 |
| Frontend debugger | `debugger` | Pages, components, client state, network | Chrome DevTools, Playwright, Context7 |
| Queue debugger | `debugger` | Job queues, workers, Redis state | Context7 |
| E2E verifier | `playwright-expert` | Reproduce and verify via browser automation | Playwright |

Each debugging agent should use Context7 (`mcp__context7__resolve-library-id` + `mcp__context7__query-docs`) to verify library API usage when the bug involves unclear method signatures, version-specific behavior, or suspected API misuse. Include this instruction in agent prompts — see references/debug-dispatch.md.

</debugging_roles>

<dispatch_rules>
1. Launch layer-specific debuggers in parallel — they investigate independently.
2. Each agent receives: the error description, reproduction steps, relevant file paths, and which skills to load.
3. Each agent reports: root cause hypothesis, evidence (logs, screenshots, stack traces), and suggested fix location.
4. After all agents report, correlate findings — the root cause often lives at the boundary between layers.
5. If agents disagree on the root cause, investigate the boundary between their domains.
</dispatch_rules>

<model_selection>
- Simple, well-scoped investigation (single file, clear error) → `haiku`
- Moderate investigation (multiple files, data flow tracing) → `sonnet`
- Complex cross-cutting investigation (race conditions, auth flows, distributed state) → `opus`
</model_selection>
</multi_layer_investigation>
</phase_4_investigate>

<phase_5_fix>
Implement the minimal fix that addresses the root cause.

<fix_principles>
- Fix the root cause, not the symptom. A 500 error caused by a missing null check needs the null check AND proper error handling upstream.
- Follow existing patterns. Read similar code in the codebase before writing the fix.
- Load the relevant skills before writing the fix (same skills as investigation phase).
- If the fix spans multiple layers, dispatch agents for each layer. See references/debug-dispatch.md for the fix dispatch template.
</fix_principles>

<fix_dispatch>
In MULTI-LAYER mode, the orchestrator decides who fixes what:
1. Identify which files need changes based on investigation findings.
2. Group changes by package/domain.
3. Determine dependency order (shared → api → web).
4. Dispatch fix agents sequentially if there are dependencies, or in parallel if independent.
</fix_dispatch>
</phase_5_fix>

<phase_6_verify>
A fix is not done until it's verified end-to-end.

1. **Re-run the reproduction** — the original error should no longer occur.
2. **Quality gates** — run the project's type checking, linting, and testing commands for every affected package. Discover available commands from package.json scripts (e.g., `tsc`, `lint`, `test`).
3. **Browser verification** (for user-facing bugs) — use Playwright or Chrome DevTools to navigate to the affected page and confirm the fix works visually.
4. **Regression check** — verify the fix doesn't break related functionality. Run the full test suite for affected packages.

If any step fails, return to phase 5 and fix the issue. Re-run all verification steps from the beginning.
</phase_6_verify>
</workflow>

<common_patterns>
Quick reference for the most frequent bugs in this stack. Use these to accelerate triage.

**Frontend → API boundary**
- CORS errors → check server CORS config
- 401/403 → check auth middleware, token expiry, cookie settings
- Wrong data shape → compare shared schema/type definitions with API response

**API → Database boundary**
- "relation does not exist" → migration not applied
- Empty results → wrong query conditions, check WHERE clause
- Connection errors → Docker not running, pool exhausted

**API → Redis/Queue boundary**
- Jobs not processing → worker not started, Redis down, wrong queue name
- Duplicate jobs → missing deduplication, idempotency key
- Stalled jobs → worker crashed without ack, check stall interval

**Frontend rendering**
- Hydration mismatch → server/client content differs, date formatting, conditional rendering
- Blank page → unhandled error in RSC, check error.tsx boundaries
- Infinite loading → API call hanging, missing Suspense boundary
</common_patterns>

<output>
When complete, produce a debug report using the template in [template.md](template.md).

Do not add explanations, caveats, or follow-up suggestions unless the user asks.
</output>
