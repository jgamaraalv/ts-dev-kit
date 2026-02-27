---
name: execute-task
description: "Executes a task, either from a TASK_N.md file or a free-form description. Use when: (1) implementing a task from a TASK_N.md file, (2) the user provides a task file path or says 'execute this task', 'implement TASK_02', or 'run this task', (3) the user describes a task directly without a document. Accepts a file path or a free-form description — if the task document is missing required sections (scope, success criteria, verification plan), automatically calls /generate-tasks to produce it before executing."
argument-hint: "[task-md-file-path | task-description]"
---

<trigger_examples>
- "Execute TASK_02"
- "Implement docs/features/search/TASK_01.md"
- "Run this task"
- "Execute the task"
- "Implement the search feature"
- "Build the user creation flow end-to-end"
- "Add the notifications endpoint to the API"
</trigger_examples>

<task>
$ARGUMENTS
</task>

<workflow>
Follow each phase in order. Each one feeds the next.

<phase_0_intake>
Resolve the input and ensure the task document is complete before executing.

**Step 1 — Determine input type:**
- If `$ARGUMENTS` looks like a file path (ends in `.md`, or starts with `/`, `./`, `docs/`, or contains a directory separator): read the file.
- Otherwise: treat it as a free-form task description — skip to Step 3.

**Step 2 — Validate the task document:**
A task document is ready for execution when it contains ALL of:
- `## Scope — Files` with at least one file entry
- `## Success Criteria` with at least one testable criterion
- `## Verification Plan` with baseline and post-change checks

If all required sections are present → proceed to phase 1.

**Step 3 — Generate the task document:**
If the document is missing any required section, OR the input was a free-form description:

1. Inform the user:
   > **Task document incomplete.** Generating a structured task document via `/generate-tasks` before proceeding.
2. Call `Skill(skill: "generate-tasks")` passing the original input as context.
3. After generation, note the path of the saved `TASK_N.md` file.
4. Read the generated file and confirm all required sections are present.
5. Resume execution using the generated document — continue to phase 1.
</phase_0_intake>

<phase_1_context_analysis>
Before writing any code, build a mental model of the task scope.

1. Read the resolved task document fully (path determined in phase 0).
2. Read the project CLAUDE.md and root package.json — understand project structure, available commands, and dependency graph.
3. Search the codebase for existing patterns — use Grep/Glob to find related files, similar implementations, and reusable code relevant to the task's file scope.
4. Identify the affected packages/directories from the task's "Scope — Files" section.
</phase_1_context_analysis>

<phase_2_role_assignment>
Determine the full execution context: role persona, domain area, domain technologies, project context, required skills, and available MCPs.

<domain_areas>
Map the task to one or more domain areas AND sub-areas. Sub-areas determine the specialist agent type and skill set.

**Backend**
| Sub-area | Agent type | When | Key skills |
|----------|-----------|------|------------|
| Database | `database-expert` | Schema design, migrations, complex queries, indexes | drizzle-pg, postgresql |
| Endpoints | `api-builder` | Routes, validation, handlers, API contracts | fastify-best-practices |
| Queues | `general-purpose` | Job processing, workers, schedulers | bullmq, ioredis |
| Security | `security-scanner` | Auth flows, RBAC, input sanitization | owasp-security-review |

**Frontend**
| Sub-area | Agent type | When | Key skills |
|----------|-----------|------|------------|
| Components | `react-specialist` | Component architecture, hooks, state management, composition | react-best-practices, composition-patterns |
| Pages/routing | `general-purpose` | Pages, layouts, data fetching, RSC boundaries | nextjs-best-practices |
| UI/UX | `ux-optimizer` | User flows, form UX, friction reduction | ui-ux-guidelines |
| Accessibility | `accessibility-pro` | WCAG compliance, keyboard nav, screen readers | — |
| Performance | `performance-engineer` | Core Web Vitals, bundle size, re-renders | react-best-practices |

**Shared packages** — `typescript-pro` or `general-purpose` (shared types, schemas, utilities)

**Cross-cutting specialists** (use alongside any domain)
| Agent type | When |
|-----------|------|
| `test-generator` | Writing test suites, improving coverage |
| `debugger` | Investigating errors, stack traces |
| `docker-expert` | Dockerfiles, compose, container config |
| `code-reviewer` | Post-implementation review |
| `playwright-expert` | E2E browser tests |

A single task may require agents from multiple sub-areas. For example, "add a new resource endpoint with list UI" needs `database-expert` (schema) + `api-builder` (route) + `react-specialist` (component).
</domain_areas>

<domain_technologies>
Read the relevant package.json to identify installed packages and their versions. Use the actual versions found — do not assume.
</domain_technologies>

<role_persona>
Compose a role persona that combines the domain sub-area, project context, technologies, and task nature.

<examples>
- "You are a database specialist working with [ORM] and [database] on schema design for [brief project description from CLAUDE.md]"
- "You are a React component architect specialized in composition patterns, hooks, and state management with [React version] and [UI library]"
- "You are a [framework] API developer building REST endpoints with validation and type-safe request/response contracts"
- "You are a frontend performance engineer optimizing Core Web Vitals and bundle size for a [framework] application"
- "You are a queue specialist designing job flows with [queue library] and retry strategies"
</examples>

Discover the actual technologies and versions from package.json. Describe the project based on CLAUDE.md or README.
</role_persona>

<required_skills>
Call the Skill tool for each relevant skill before writing any code or dispatching agents. Skills inject domain-specific rules and best practices.

Identify the required skills from the domain area, then call each one:

```
Skill(skill: "fastify-best-practices")
Skill(skill: "drizzle-pg")
Skill(skill: "postgresql")
```

<skill_map>
Match skills to the sub-area identified in domain_areas:

**Backend sub-areas:**
- Database → /drizzle-pg, /postgresql
- Endpoints → /fastify-best-practices
- Queues → /bullmq, /ioredis
- Security → /owasp-security-review

**Frontend sub-areas:**
- Components → /react-best-practices, /composition-patterns
- Pages/routing → /nextjs-best-practices
- UI/UX → /ui-ux-guidelines
- Performance → /react-best-practices

**Cross-cutting** → combine skills from each sub-area involved.
</skill_map>

In ALL execution modes: include explicit Skill() call instructions in each subagent prompt (see references/agent-dispatch.md). The orchestrator does not need to load skills itself — agents load them before writing code.
</required_skills>

<available_mcps>
Identify MCPs that can assist execution:
- context7 — query up-to-date library documentation (see below)
- playwright — test frontend in the browser, take screenshots, verify UI
- chrome-devtools — inspect pages, debug network requests, check console
- firecrawl — fetch external documentation or references from the web

**Context7 usage — MANDATORY for config and versioned APIs**: Many tools have breaking config changes across minor versions. **Before writing or modifying ANY configuration file** for versioned tools (OTel collector, Prometheus, Grafana, Loki, Tempo, Docker Compose, Drizzle, Fastify, Next.js, Redis, BullMQ, Nginx, etc.), you MUST query Context7 first to verify the correct syntax for the installed version. Do NOT try variations blindly — guess-looping config fixes wastes context and compounds errors.

1. `mcp__context7__resolve-library-id` — resolve the library name (e.g., "fastify", "drizzle-orm", "next", "react", "bullmq") to its Context7 ID.
2. `mcp__context7__query-docs` — query with the specific API, config key, or pattern you need.

This applies to ALL roles: orchestrator, dispatched agents, and ad-hoc specialists. Check the project's package.json for installed versions first. In MULTI-ROLE mode, include these Context7 instructions in each agent prompt so agents query docs themselves before writing config.
</available_mcps>
</phase_2_role_assignment>

<phase_2b_multi_role_decomposition>
When a task spans multiple domains, decompose it into separate roles with isolated execution contexts.

<when_to_decompose>
Decompose into multiple roles when ANY of these apply:
1. The task touches 2+ packages or major directories (e.g., shared code + backend + frontend).
2. The task involves distinct skill sets (e.g., database schema design + frontend UI).
3. The changes in one domain are large enough to benefit from a focused agent.

Do not decompose if:
1. The task is small and contained within a single package.
2. The cross-package changes are trivial (e.g., adding one type to shared and importing it).
</when_to_decompose>

<decomposition_rules>
<rule_1_define_roles_independently>
Each role gets its own persona, skill set, context files, and success criteria.

<example>
Role A: Database specialist (sub-area: Database). Agent: database-expert (or ts-dev-kit:database-expert if plugin-scoped). Task: design schema + migration for the new feature. Skills: drizzle-pg, postgresql.
Role B: API endpoint developer (sub-area: Endpoints). Agent: api-builder (or ts-dev-kit:api-builder). Task: build REST routes consuming the new schema. Skills: fastify-best-practices.
Role C: Component architect (sub-area: Components). Agent: react-specialist (or ts-dev-kit:react-specialist). Task: build the result card and list components. Skills: react-best-practices, composition-patterns.
Role D: Page builder (sub-area: Pages/routing). Agent: general-purpose (ad-hoc). Task: wire components into the search results page with data fetching. Skills: nextjs-best-practices.
Role E: TypeScript library developer. Agent: typescript-pro (or ts-dev-kit:typescript-pro). Task: add shared schemas and types. Skills: none extra.
</example>
</rule_1_define_roles_independently>

<rule_2_dispatch_agents>
For each role, spawn a specialized subagent via the Task tool.

**Selecting the agent type:**
1. **Resolve the agent name for the current scope.** Agents may be registered under different names depending on how ts-dev-kit is installed:
   - **Project scope** (`.claude/agents/`): short name — e.g., `database-expert`
   - **Plugin scope**: prefixed with the plugin namespace — e.g., `ts-dev-kit:database-expert`
   Before dispatching, check which agents are available in your context. If you see agents with a `ts-dev-kit:` prefix, use the prefixed name as `subagent_type`. If agents are available by short name, use the short name.
2. If a matching agent exists (in any scope), use its resolved name as `subagent_type`.
3. If no matching agent exists, use `general-purpose` as `subagent_type` and embed the full role definition directly in the prompt — this creates an ad-hoc specialist without needing a .md file.

**Ad-hoc agent creation** — when `subagent_type: "general-purpose"` is used as a specialist surrogate, the prompt must include:
- **Role persona**: who the agent is and what it specializes in.
- **Domain expertise**: specific technologies, frameworks, and versions.
- **Project context**: how this sub-area fits into the project (discover from CLAUDE.md and package.json).
- **Constraints**: patterns to follow, files to reference, conventions to match.
- **Skills to load**: explicit `Skill(skill: "...")` calls for domain-specific rules.

<example_adhoc_agent>
Task(
  description: "Implement notification worker",
  subagent_type: "general-purpose",
  model: "sonnet",
  prompt: """
You are a queue specialist working on this project.

Your expertise: Redis-backed job queues, workers, flow producers, retry strategies, rate limiting, and graceful shutdown.

## Before writing any code
1. Read CLAUDE.md and relevant package.json files to understand the project structure and conventions.
2. Call the Skill tool to load these domain skills:
   - Skill(skill: "bullmq")
   - Skill(skill: "ioredis")

## Your task
[task details...]

## Project context
Discover from the codebase:
- Redis connection configuration (search for Redis imports)
- Existing queue/worker patterns (search for queue or worker files)
- Import conventions (check existing code for named vs default imports)
[...]
"""
)
</example_adhoc_agent>

Each agent prompt must follow the template in references/agent-dispatch.md. The agent must be able to complete its work independently.
</rule_2_dispatch_agents>

<rule_3_execution_order>
Decide the execution order based on file conflicts and dependencies:
- **Parallel**: roles touch independent files with no data dependency → launch multiple Task calls in one message. **CRITICAL: "parallel" means sending ALL independent Task() calls in a SINGLE assistant message. If you announce "dispatching 3 agents in parallel" you MUST include exactly 3 Task() tool calls in that same message. Announcing parallel dispatch and then sending only 1 Task() is a violation of this protocol.**
- **Sequential**: one role's output is another's input → await the blocker first.
- **Worktree isolation**: roles touch overlapping files but are otherwise independent → set `isolation: "worktree"` on the Task tool. Each agent gets an isolated copy of the repository; the worktree is auto-cleaned if the agent makes no changes.

**Decision tree for overlapping files:**
1. Do the agents have a data dependency (one needs the other's output)? → **Sequential**.
2. Are the agents logically independent but touch some of the same files (e.g., both modify a shared barrel export, or both edit the same config)? → **Worktree isolation** — dispatch in parallel with `isolation: "worktree"` on each Task() call, then merge results.
3. Do the agents touch completely separate files? → **Parallel** (no isolation needed).
</rule_3_execution_order>

<rule_4_model_selection>
Choose the model for each dispatched agent based on task complexity:
- **haiku**: simple, well-defined tasks — adding a type, writing a small utility, updating config, barrel file exports.
- **sonnet**: moderate tasks — implementing a feature within a single domain, writing tests, building a component.
- **opus**: complex tasks — cross-cutting concerns, architectural decisions, novel implementations requiring deep reasoning.

Set the `model` parameter on the Task tool call accordingly.
</rule_4_model_selection>
</decomposition_rules>

<dispatch_pattern>
The main session acts as the orchestrator:
1. Analyze the task and define roles (this phase).
2. Create TaskCreate entries for each role to track progress.
3. Dispatch the first wave of agents (those with no blockers).
4. When a blocking agent completes, dispatch the next wave.
5. After all agents complete, run the final quality gates.
6. Produce the completion report (see template.md).

Constraints:
1. Subagents cannot spawn other subagents. All dispatch happens from the main session.
2. Each agent prompt must be fully self-contained — do not assume agents have conversation history.
3. Review each agent's output before dispatching dependents.
</dispatch_pattern>

<execution_mode_decision>
At the end of phase 2, make an explicit execution mode decision and state it to the user:

> **EXECUTION MODE: SINGLE-ROLE** — Single domain. I will dispatch 1-2 focused agents for implementation.

OR

> **EXECUTION MODE: MULTI-ROLE** — Multiple domains. I will dispatch specialized agents across domains via the Task tool.

OR

> **EXECUTION MODE: PLAN** — The task is highly complex. I will enter plan mode to design a structured implementation plan before executing.

**CRITICAL: In ALL execution modes, the orchestrator (main session) NEVER writes application code directly.** All implementation — components, hooks, pages, routes, services, tests — is delegated to agents via the Task tool. The orchestrator's role is: context gathering, agent dispatch, output review, integration glue (under 15 lines), and quality gates.

The difference between SINGLE-ROLE and MULTI-ROLE is decomposition complexity, NOT whether agents are used:
- **SINGLE-ROLE**: simpler decomposition (1-2 agents, same domain). Use when the task is contained within one package or domain.
- **MULTI-ROLE**: complex decomposition (3+ agents, multiple domains). Use when the task spans packages or skill sets.

Use PLAN mode when:
- The task has 4+ distinct roles or implementation phases.
- The scope is large enough that context window management becomes a concern.
- The task benefits from upfront architectural planning before any code is written.

In PLAN mode: use EnterPlanMode to design the full plan. Once the user approves it, exit plan mode and execute phases sequentially as orchestrator, with context cleanup between major phases when needed.
</execution_mode_decision>
</phase_2b_multi_role_decomposition>

<phase_3_task_analysis>
Read the task document and load the criteria defined there. These are binding requirements for this execution.

1. Extract from the task document:
   - **Success criteria** — exact conditions for task completion
   - **Baseline checks** — what to run/capture BEFORE changes
   - **Post-change checks** — what to verify AFTER changes
   - **Performance benchmarks** — specific metrics with targets
   - **Non-functional requirements** — scoped to this task's domain
   - **Scope — Files** — the exact list of files to create or modify

   State them to the user:
   > **Task loaded:** [task title]
   > - Dependencies: [list or "none"]
   > - Files in scope: N files
   > - Success criteria: [count] criteria
   > - Baseline checks: [list]
   > - Post-change checks: [list]
   > - Performance targets: [list or "none defined"]

2. For questions about project libraries, use Context7 (`mcp__context7__resolve-library-id` → `mcp__context7__query-docs`) to query up-to-date documentation. If anything is ambiguous, ask the user before proceeding.

3. Check MCP availability — use ToolSearch to detect which browser MCPs are available (playwright, chrome-devtools, or neither), then confirm against the task's "MCP Checks" section.

4. Plan the implementation order from the task's file scope — build dependencies before dependents:
   shared types → database schema → API layer → UI components → pages → tests.

5. Confirm the verification plan with the user:
   > **Verification plan:**
   > - Baseline checks: [from task doc]
   > - MCPs available: [detected list or "none — shell-only"]
   > - Post-change checks: [from task doc]
</phase_3_task_analysis>

<phase_3b_baseline_capture>
**MANDATORY.** Run the verification plan before writing any code to establish the baseline for comparison. Do NOT skip this phase.

**Step 1: Standard quality gates** — run and record results (pass/fail, counts, bundle sizes).
Discover the exact commands from package.json scripts for each affected package.

**Step 2: MCP-based checks** — follow this decision tree in order:

1. Use ToolSearch to confirm which browser MCPs are available (playwright, chrome-devtools, or neither).
2. **If browser MCPs are available AND the task touches frontend pages:**
   a. Check if the dev server is running (attempt to navigate to `localhost` or the configured URL).
   b. **If dev server is accessible:** navigate to each affected page, capture screenshots of key states, and measure performance (LCP, load time). Use Chrome DevTools traces or Playwright screenshots as appropriate.
   c. **If dev server is NOT accessible:** ask the user whether to start it or skip visual checks. Do NOT silently skip — the user must confirm.
3. **If no browser MCPs are available:** note it explicitly and proceed with shell-only checks (build output, bundle sizes).
4. **Backend tasks:** execute requests to affected endpoints (via curl or available API MCPs) and record response status, payload shape, and timing.
5. **Database tasks:** record current schema state for affected tables.

**Step 3: Store baseline** — all values captured here are compared against post-change results in phase 5b.

When visual/performance checks are skipped, state the reason:
> **Baseline captured.** MCP-based visual checks skipped — [reason: no browser MCPs available | dev server not running (user confirmed skip) | no frontend pages affected].

The orchestrator ALWAYS runs baseline capture before dispatching any agents, regardless of execution mode.
</phase_3b_baseline_capture>

<phase_4_execution>
**CRITICAL: The orchestrator (main session) NEVER writes application code.** All implementation is dispatched to agents via the Task tool. The orchestrator may only write trivial glue (under 15 lines total): barrel file exports, small wiring imports, or config one-liners.

Before dispatching, check the execution mode decision from phase 2 to determine decomposition complexity.

<agent_dispatch_protocol>
This protocol applies to ALL execution modes (SINGLE-ROLE, MULTI-ROLE, and PLAN).

As orchestrator, your responsibilities are: context gathering, agent dispatch, output review, integration glue, and quality gates. You do NOT write application code (components, hooks, pages, routes, services, tests).

**Dispatch steps:**
1. Create TaskCreate entries for each role to track progress.
2. For each role, dispatch a specialized agent via the Task tool with a self-contained prompt. Set the `model` parameter according to rule_4_model_selection.
3. **Launch independent agents in parallel — this means multiple Task() calls in a SINGLE message.** Do NOT sequentialize independent agents. If you have 3 independent tasks, your message must contain 3 Task() tool calls. Launch dependent agents sequentially (wait for blockers to complete first).
4. **For parallel agents that touch overlapping files**, add `isolation: "worktree"` to each Task() call. This gives each agent an isolated copy of the repository, preventing edit conflicts. Worktrees are auto-cleaned when the agent makes no changes.
5. Each agent runs its own quality gates before reporting completion. Review the agent's output and gate results before dispatching dependents.
6. After all agents complete, proceed to phase 5 for the final cross-package quality gates.

For the agent prompt template and dispatch details, see references/agent-dispatch.md.

**Self-check:** If you find yourself creating application files (routes, components, services, hooks, tests, pages), STOP and delegate to an agent instead.
</agent_dispatch_protocol>

<build_order>
Instruct agents to work from micro to macro — build dependencies before dependents:
1. Shared code first — new constants, types, schemas, or enums needed by multiple packages go in the shared/common package.
2. Check for reuse — before creating a helper, hook, component, or utility, search the codebase for existing code that can be used or extended.
3. Implement the core change — build the feature/fix in the target package.
4. Wire it together — connect the pieces across packages if needed.

Decision tree (include in agent prompts when relevant):
- Is this code used by multiple modules? YES → Create in the shared/common package.
- Is this code used by multiple modules? NO → Is this component multi-file? YES → Create folder with index.tsx + related files. NO → Single file, co-located with usage.
</build_order>
</phase_4_execution>

<phase_5_quality_gates>
A task is not done until all quality gates pass. Run them in order for every affected package. If any gate fails, fix the issue and re-run all gates from the beginning.

Discover the available commands from package.json scripts for each affected package. Common gates:

1. Type checking — run the project's typecheck command (e.g., `tsc`, `typecheck`)
2. Linting — run the project's lint command (e.g., `lint`, `eslint`)
3. Tests (if available) — run the project's test command (e.g., `test`, `vitest`)
4. Build — run the project's build command (e.g., `build`)
5. Self-check — review your changes against the success criteria from the task document.

For monorepos, run these for each affected workspace/package. Discover the workspace command pattern from CLAUDE.md or the root package.json (e.g., `yarn workspace <name> <script>`, `pnpm --filter <name> <script>`, `npm -w <name> <script>`, `turbo run <script> --filter=<name>`).

If a gate fails:
- Read the error output carefully.
- **CRITICAL: Dispatch an agent to fix the errors — do NOT fix them inline in the orchestrator session.** Fixing errors inline exhausts the context window and triggers compaction mid-task. Dispatch a `debugger` agent (for investigation) or the appropriate specialist agent (e.g., `typescript-pro` for type errors, `api-builder` for route errors) to fix the issues. The orchestrator's role is to read the error, decide which agent can fix it, and dispatch — never to edit application code itself.
- Re-run all gates from step 1, since a fix may introduce new issues.
- Repeat until all gates pass cleanly.
</phase_5_quality_gates>

<phase_5b_post_change_verification>
After all quality gates pass, re-run the verification plan from phase 3b and compare against baseline.

1. Re-run every check from phase 3b with identical parameters.
2. Compare each result against baseline:
   - **Quality gates**: must remain passing. New failures = regression.
   - **Visual checks** (if MCPs available): compare screenshots for unintended changes.
   - **Performance** (if MCPs available): compare metrics against task-defined benchmarks. Regressions > 10% must be investigated.
   - **API responses**: compare status codes and payload shapes. Breaking changes = regression.
3. Build the comparison table (see template.md for format).

If any regression is found, fix it, re-run phase 5 quality gates, then re-run this phase. Repeat until clean.
</phase_5b_post_change_verification>

<phase_6_documentation>
After all quality gates pass, review whether the changes require documentation updates:

- CLAUDE.md — new commands, architecture changes, dependency graph updates, new conventions.
- Existing docs — new environment variables, setup steps, API contract changes.

Only update documentation directly affected by the changes. Do not create new documentation files unless the changes introduce a new package or major feature with no existing docs.
</phase_6_documentation>

<orchestrator_anti_patterns>
## Orchestrator Anti-Patterns — NEVER do these

These are recurring mistakes. Violating any of these rules degrades execution quality and wastes context.

### 1. Never fix errors in the main thread
When quality gates (tsc/lint/test/build) fail during execution, **dispatch an isolated agent** to fix them. Do NOT attempt fixes in the main orchestrator session. Fixing inline exhausts the context window and triggers compaction mid-task, losing critical execution state.

### 2. Never guess-loop config fixes
When a tool or config isn't working (e.g., OTel collector pipeline, Prometheus scraping, Docker networking, Drizzle config, Fastify plugin options), use **Context7 immediately** to query the library docs for the installed version. Do NOT try variations blindly. Query with `mcp__context7__resolve-library-id` + `mcp__context7__query-docs` **before** touching any config file.

### 3. Never announce parallel dispatch without delivering it
If you announce "dispatching 3 agents in parallel", your message MUST contain exactly 3 Task() tool calls. Announcing parallel dispatch and then only sending 1 Task() is a protocol violation. Count your Task() calls before sending. If agents are independent, they go in the SAME message.

### 4. Never write application code as orchestrator
The orchestrator reads, analyzes, dispatches, reviews, and runs quality gates. It does NOT write components, hooks, routes, services, migrations, tests, or any application logic. The only code the orchestrator may write is trivial integration glue (under 15 lines): barrel exports, small wiring imports, or config one-liners.

### 5. Never dispatch parallel agents on overlapping files without worktree isolation
When two or more agents run in parallel and touch any of the same files (shared barrel exports, config files, common modules), they will produce edit conflicts. Always set `isolation: "worktree"` on each Task() call so each agent works on an isolated copy of the repository. Skip isolation only when agents touch completely separate files.

### Self-check before sending each message
Before sending any message during execution, verify:
- [ ] Am I about to write application code? → STOP, dispatch an agent instead.
- [ ] Am I about to modify a config without querying docs? → STOP, use Context7 first.
- [ ] Did I announce N parallel agents? → Count my Task() calls. Are there N? If not, add the missing ones.
- [ ] Am I dispatching parallel agents that touch the same files? → Add `isolation: "worktree"` to each Task() call.
- [ ] Did a quality gate fail? → STOP, dispatch a specialist agent to fix it.
</orchestrator_anti_patterns>
</workflow>

<output>
When complete, produce the completion report including the baseline vs post-change comparison table. See template.md for the exact format.

Do not add explanations, caveats, or follow-up suggestions unless the user explicitly asks. The report is the final output.
</output>
