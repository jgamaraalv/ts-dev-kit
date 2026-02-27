# Debug Agent Dispatch Reference

## Table of contents

- [Investigation agent template](#investigation-agent-template)
- [Fix agent template](#fix-agent-template)
- [Role-specific prompts](#role-specific-prompts)
- [Dispatch examples](#dispatch-examples)
- [Strategic logging patterns](#strategic-logging-patterns)
- [Correlation protocol](#correlation-protocol)

---

## Investigation agent template

The `debugger` agent already includes project context, common errors, debugging commands, strategic logging, and quality gates in its system prompt. The dispatch prompt only needs **bug-specific** information:

```
## Bug description
[What the user reported — error message, behavior, reproduction steps]

## Your investigation scope
[Which layer/files to investigate. Be specific about boundaries.]

## Skills to load
Call the Skill tool before investigating:
- Skill(skill: "[skill-1]")
- Skill(skill: "[skill-2]")

## Reproduction context
[How the bug was reproduced — curl command, browser steps, log output]

## Files to start with
[List specific file paths where the error originates or is likely rooted]

## Report format
When done, report:
- **Root cause hypothesis**: one sentence.
- **Evidence**: what you found that supports the hypothesis.
- **Fix location**: which file(s) and line(s) need to change.
- **Suggested fix**: code diff or description.
- **Confidence**: high / medium / low.
```

### Skill mapping for investigation

The debugger loads skills dynamically based on the bug domain. Include the appropriate skills in the dispatch prompt:

| Bug domain | Skills to load |
|-----------|---------------|
| API/Fastify | `fastify-best-practices` |
| Database | `drizzle-pg`, `postgresql` |
| Frontend/React | `nextjs-best-practices`, `react-best-practices` |
| Queue/Redis | `bullmq`, `ioredis` |
| Security | `owasp-security-review` |

## Fix agent template

After investigation, dispatch the appropriate **specialist agent** (not necessarily the debugger) to implement fixes. Specialist agents already include their domain context and quality gates:

```
## Bug root cause
[One sentence from the investigation phase]

## Your fix scope
[Which files to modify and what the fix should do]

## Existing patterns to follow
[Paste relevant code snippets or file paths showing the codebase conventions]

## Fix requirements
[Specific changes needed — be precise about expected behavior]
```

Use the agent type that matches the fix domain. If ts-dev-kit is installed as a plugin, use the prefixed name (e.g., `ts-dev-kit:api-builder`). Check which agents are available in your context and use the exact registered name:
- API route fix -> `api-builder` (preloads fastify-best-practices)
- Database/query fix -> `database-expert` (preloads drizzle-pg, postgresql)
- Component fix -> `react-specialist` (preloads react-best-practices, composition-patterns)
- Type fix -> `typescript-pro`
- Security fix -> `security-scanner` (preloads owasp-security-review)
- Cross-cutting or unclear -> `debugger` (load skills dynamically)

---

## Role-specific prompts

> **Note:** All agent types below may be prefixed with `ts-dev-kit:` when the plugin is installed in plugin scope (e.g., `ts-dev-kit:debugger`). Check the available agents in your context and use the exact registered name.

### Backend debugger

**Agent type**: `debugger`
**Skills to include**: `fastify-best-practices`, `drizzle-pg`, `postgresql`
**Scope**: Backend source directory — routes, use cases, adapters, plugins, middleware. Discover the path from the project structure.

Investigation focus:
- Read the Fastify route handler at the error location
- Check request validation (Zod schema vs actual payload)
- Trace database queries — use `EXPLAIN ANALYZE` if performance-related
- Check error handling — are errors caught and mapped to proper HTTP codes?
- Inspect middleware/hooks in the request lifecycle

### Frontend debugger

**Agent type**: `debugger`
**Skills to include**: `nextjs-best-practices`, `react-best-practices`
**Scope**: Frontend source directory — pages, components, hooks, contexts, lib. Discover the path from the project structure.

Investigation focus:
- Check the page/component at the error location
- Inspect browser console for client-side errors (use Chrome DevTools or Playwright MCP)
- Check network requests — is the API call correct? Does the response match expectations?
- Verify server vs client rendering — hydration mismatches, missing Suspense boundaries
- Check auth context — is the user authenticated? Are tokens being sent?

MCPs available to the debugger:
- `mcp__chrome-devtools__take_screenshot` — visual state of the page
- `mcp__chrome-devtools__list_console_messages` — browser console errors
- `mcp__chrome-devtools__list_network_requests` — failed API calls
- `mcp__plugin_playwright_playwright__browser_snapshot` — accessibility tree inspection

### Queue debugger

**Agent type**: `debugger`
**Skills to include**: `bullmq`, `ioredis`
**Scope**: Queue/worker source directory — queue definitions, workers, job processors. Discover the path from the project structure.

Investigation focus:
- Check queue configuration (name, connection, default job options)
- Inspect worker concurrency and error handling
- Check Redis connectivity and key patterns
- Look for stalled jobs, failed jobs, or jobs stuck in "waiting"
- Verify job data shape matches worker expectations

### E2E verifier

**Agent type**: `playwright-expert`
**Skills**: none needed (agent has its own testing patterns)
**Scope**: Full application via browser automation

Verification focus:
- Navigate to the affected page
- Perform the user flow that triggers the bug
- Take screenshots before and after
- Check console for errors
- Verify the fix resolves the issue visually

---

## Dispatch examples

### Example 1: API returns 500 on resource creation

```
# Triage: API layer (single-layer)
# No dispatch needed — debug directly

1. curl the endpoint to reproduce
2. Read the route handler and use case
3. Check the database query
4. Fix the root cause
5. Verify with curl + tests
```

### Example 2: Form submits but data doesn't appear in list

```
# Triage: Cross-cutting (frontend -> API -> database)
# Dispatch: MULTI-LAYER

# Wave 1: Parallel investigation
# Use "debugger" or "ts-dev-kit:debugger" depending on scope
Task(
  description: "Debug resource creation API endpoint",
  subagent_type: "debugger",  // or "ts-dev-kit:debugger" if plugin-scoped
  model: "sonnet",
  prompt: """
## Bug description
User submits the creation form successfully (200 response) but the item
doesn't appear in the list page.

## Your investigation scope
Backend only: the POST endpoint and corresponding GET list endpoint.
Check if data reaches the database and if the list query returns it.

## Skills to load
Call the Skill tool before investigating:
- Load skills matching the backend framework and ORM used (discover from package.json)

## Reproduction context
curl -X POST http://localhost:<port>/api/<resource> -H "Content-Type: application/json" \
  -d '{"field":"value"}'
Returns 200, but GET /api/<resource> returns empty array.

## Files to start with
- Discover from the project structure: look for route handlers, use cases, and persistence layers
"""
)

Task(
  description: "Debug resource list page",
  subagent_type: "debugger",  // or "ts-dev-kit:debugger" if plugin-scoped
  model: "sonnet",
  prompt: """
## Bug description
User submits the creation form successfully but the item doesn't appear
in the list page.

## Your investigation scope
Frontend only: the list page. Check the API call and rendering logic.

## Skills to load
Call the Skill tool before investigating:
- Load skills matching the frontend framework used (discover from package.json)

## Reproduction context
Navigate to the list page after submitting the form. The list shows empty or
stale data.

## Files to start with
- Discover from the project structure: look for the list page component and its sub-components
"""
)

# Wave 2: Dispatch fixes using specialist agents matching the fix domain
# e.g., api-builder (or ts-dev-kit:api-builder) for API fix

# Wave 3: E2E verification
Task(
  description: "Verify resource creation flow",
  subagent_type: "playwright-expert",  // or "ts-dev-kit:playwright-expert"
  model: "haiku",
  prompt: """
## Your task
Verify the resource creation flow works end-to-end:
1. Navigate to the creation form
2. Fill in the required fields and submit
3. Verify the new item appears in the list page

## Success criteria
- Form submits successfully
- Item appears in the list within 5 seconds
- No console errors
"""
)
```

### Example 3: Production error from Sentry

```
# Triage: Starts with Sentry context, then investigate

1. Query Sentry for the full stack trace and event details
2. Identify the affected layer from the stack trace
3. Dispatch investigation agent(s) for that layer
4. Dispatch fix agent(s) using the appropriate specialist
5. E2E verification
```

---

## Strategic logging patterns

When investigation needs more visibility, add temporary logging:

```typescript
// Prefix with DEBUG: for easy cleanup after fixing
request.log.debug({ body: request.body, params: request.params }, "DEBUG: incoming request");
request.log.debug({ result }, "DEBUG: query result");

// Outside request context
fastify.log.debug({ config }, "DEBUG: plugin configuration");
```

After fixing, search and remove all `DEBUG:` log lines:
```bash
# Search the backend source directory for temporary debug lines
grep -rn "DEBUG:" <backend-src-dir>/
```

---

## Correlation protocol

When multiple agents investigate the same bug, the orchestrator correlates their findings:

1. Collect each agent's root cause hypothesis and evidence.
2. Check for consistency — do the hypotheses align?
3. If agents agree, proceed with the fix.
4. If agents disagree, look at the boundary:
   - Frontend says "API returns wrong data" + Backend says "query is correct" -> check response serialization.
   - Backend says "data is correct in DB" + Frontend says "list is empty" -> check API response shape vs frontend expectations (Zod schema mismatch).
5. The true root cause is usually at the boundary between layers where one side's assumption doesn't match the other's reality.
