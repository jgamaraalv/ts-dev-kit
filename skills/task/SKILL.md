---
name: task
description: "Use this skill when the user wants to implement a new task in the project. Covers feature development, refactoring, bug fixes, and any code change that requires context analysis, role assignment, and structured execution. For changes under ~30 lines in a single file, implement directly without this workflow."
argument-hint: "[task-description or task-md-file-path]"
---

<trigger_examples>
- "Implement the search feature"
- "Build the user creation flow end-to-end"
- "Refactor the auth module to use shared schemas"
- "Add the notifications endpoint to the API"
- "Fix the pagination bug"
- "Execute this task"
</trigger_examples>

<workflow>
Follow each phase in order. Each one feeds the next.

<phase_1_context_analysis>
Before writing any code, build a mental model of the task scope.

1. Read the project CLAUDE.md and root package.json — understand the project structure, available commands, and dependency graph.
2. Search the codebase for existing patterns — use Grep/Glob to find related files, similar implementations, and reusable code.
3. Identify the affected packages/directories — determine which parts of the project will be touched and in what order.
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

In SINGLE-ROLE mode: call each skill yourself before starting phase 4.
In MULTI-ROLE mode: include explicit Skill() call instructions in each subagent prompt (see references/agent-dispatch.md).
</required_skills>

<available_mcps>
Identify MCPs that can assist execution:
- context7 — query up-to-date library documentation (see below)
- playwright — test frontend in the browser, take screenshots, verify UI
- chrome-devtools — inspect pages, debug network requests, check console
- firecrawl — fetch external documentation or references from the web

**Context7 usage**: When the task involves library APIs, version-specific patterns, or unfamiliar method signatures, use Context7 to query current documentation before writing code:
1. `mcp__context7__resolve-library-id` — resolve the library name (e.g., "fastify", "drizzle-orm", "next", "react", "bullmq") to its Context7 ID.
2. `mcp__context7__query-docs` — query with the specific API, pattern, or feature you need.
Check the project's package.json for installed versions first. In MULTI-ROLE mode, include these instructions in each agent prompt so agents can query docs themselves.
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
Role A: Database specialist (sub-area: Database). Agent: database-expert. Task: design schema + migration for the new feature. Skills: drizzle-pg, postgresql.
Role B: API endpoint developer (sub-area: Endpoints). Agent: api-builder. Task: build REST routes consuming the new schema. Skills: fastify-best-practices.
Role C: Component architect (sub-area: Components). Agent: react-specialist. Task: build the result card and list components. Skills: react-best-practices, composition-patterns.
Role D: Page builder (sub-area: Pages/routing). Agent: general-purpose (ad-hoc). Task: wire components into the search results page with data fetching. Skills: nextjs-best-practices.
Role E: TypeScript library developer. Agent: typescript-pro. Task: add shared schemas and types. Skills: none extra.
</example>
</rule_1_define_roles_independently>

<rule_2_dispatch_agents>
For each role, spawn a specialized subagent via the Task tool.

**Selecting the agent type:**
1. Check if a project agent exists in `.claude/agents/` that matches the sub-area (see domain_areas table above for the mapping).
2. If a matching agent exists, use its name as `subagent_type` (e.g., `database-expert`, `api-builder`, `react-specialist`).
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
- **Parallel**: roles touch independent files with no data dependency → launch multiple Task calls in one message.
- **Sequential**: one role's output is another's input → await the blocker first.
- **Worktree isolation**: roles touch overlapping files but are otherwise independent → set `isolation: "worktree"` on the Task tool.
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
6. Produce the completion report (see references/output-templates.md).

Constraints:
1. Subagents cannot spawn other subagents. All dispatch happens from the main session.
2. Each agent prompt must be fully self-contained — do not assume agents have conversation history.
3. Review each agent's output before dispatching dependents.
</dispatch_pattern>

<execution_mode_decision>
At the end of phase 2, make an explicit execution mode decision and state it to the user:

> **EXECUTION MODE: SINGLE-ROLE** — I will implement all changes directly.

OR

> **EXECUTION MODE: MULTI-ROLE** — I will act as orchestrator, dispatching specialized agents via the Task tool.

OR

> **EXECUTION MODE: PLAN** — The task is highly complex. I will enter plan mode to design a structured implementation plan before executing.

Use PLAN mode when:
- The task has 4+ distinct roles or implementation phases.
- The scope is large enough that context window management becomes a concern.
- The task benefits from upfront architectural planning before any code is written.

In PLAN mode: use EnterPlanMode to design the full plan. Once the user approves it, exit plan mode and execute phases sequentially as MULTI-ROLE orchestrator, with context cleanup between major phases when needed.

Follow this decision in phase 4. In MULTI-ROLE and PLAN modes, delegate application code to agents — your job is dispatch, review, integration, and quality gates.
</execution_mode_decision>
</phase_2b_multi_role_decomposition>

<phase_3_task_analysis>
1. Extract task-defined criteria — scan the task document for explicit:
   - **Success criteria** (checklists, acceptance conditions)
   - **Initial/baseline tests** (to run BEFORE changes, for comparison)
   - **Post-change tests** (to run AFTER changes, for verification)
   - **Performance benchmarks** (bundle size, API call counts, Lighthouse metrics)

   Look for section names like: "Initial Tests", "Before Changes", "Baseline", "Post-Change Tests", "After Changes", "Success Criteria", "Acceptance Criteria", "Functionality Tests", "Performance Tests".

   If found, state them to the user:
   > **Task-defined criteria found:**
   > - Success criteria: [list]
   > - Baseline tests (before changes): [list or "none"]
   > - Post-change tests (after changes): [list or "none"]

   These are binding requirements that extend the default quality gates. Do not skip them.

2. Understand the request — identify what is being asked, which files will be created or modified, and what the expected outcome is.
3. Define success criteria — combine the task's own criteria (from step 1) with your analysis. Task-defined criteria take priority over defaults.
4. For questions about project libraries, use Context7 (`mcp__context7__resolve-library-id` → `mcp__context7__query-docs`) to query up-to-date documentation. If anything is ambiguous, ask the user before proceeding.
5. Check for helpful MCPs — does the task involve browser testing, external docs?
6. Plan the implementation order — determine which changes must happen first (e.g., types before lib before hooks before components before pages).
7. Generate the verification plan — build a before/after test plan combining task-defined criteria with automatic checks based on domain and available MCPs. See references/verification-protocol.md for the full protocol.
   - Detect available testing MCPs (playwright, chrome-devtools, or none).
   - Map the task domain to checks: frontend → visual + performance, backend → API responses, database → schema state.
   - Always include standard quality gates (lint, build, test) as baseline.
   - Present the plan:
     > **Verification plan:**
     > - Baseline checks: [list]
     > - MCPs for verification: [list or "none available — shell-only checks"]
     > - Post-change checks: [list]
</phase_3_task_analysis>

<phase_3b_baseline_capture>
Run the verification plan before writing any code to establish the baseline for comparison.

1. Run standard quality gates and record results (pass/fail, counts, bundle sizes).
2. Run domain-specific checks from the verification plan:
   - **Frontend**: if playwright/chrome-devtools MCPs are available, navigate to affected pages, capture screenshots, and measure performance (LCP, load time). Otherwise, record build output and bundle sizes.
   - **Backend**: execute requests to affected endpoints (via curl or available API MCPs) and record response status, payload shape, and timing.
   - **Database**: record current schema state for affected tables.
3. Store all baseline values — these are compared against post-change results in phase 5b.

If testing MCPs are not available, skip those checks and note it:
> **Baseline captured.** MCP-based visual/performance checks skipped — no browser MCPs available.

In MULTI-ROLE mode, the orchestrator runs baseline capture before dispatching any agents.
</phase_3b_baseline_capture>

<phase_4_execution>
Before writing any code, check the execution mode decision from phase 2.

**MULTI-ROLE → Follow <multi_role_orchestration> below.**
**SINGLE-ROLE → Follow <single_role_implementation> below.**

<multi_role_orchestration>
As orchestrator, dispatch agents, review their output, and verify integration. Do not implement application code yourself.

You may write code directly only for trivial glue (under 15 lines total):
- Adding an export line to a barrel file
- Adding a small schema to the shared package that multiple agents need
- Wiring an import in a top-level file after agents complete

Everything else should be delegated to an agent. For the agent prompt template and dispatch details, see references/agent-dispatch.md.

Dispatch steps:
1. Create TaskCreate entries for each role.
2. For each role, dispatch a specialized agent via the Task tool with a self-contained prompt. Set the `model` parameter according to rule_4_model_selection.
3. Launch independent agents in parallel. Launch dependent agents sequentially.
4. Each agent runs its own quality gates before reporting completion. Review the agent's output and gate results before dispatching dependents.
5. After all agents complete, proceed to phase 5 for the final cross-package quality gates.

If you find yourself creating application files (routes, components, services, hooks, tests) while in MULTI-ROLE mode, delegate to an agent instead.
</multi_role_orchestration>

<single_role_implementation>
Think through each step before acting. Share your reasoning at key decision points.

<build_order>
Work from micro to macro — build dependencies before dependents:
1. Shared code first — new constants, types, schemas, or enums needed by multiple packages go in the shared/common package (discover its location from the project structure).
2. Check for reuse — before creating a helper, hook, component, or utility, search the codebase for existing code that can be used or extended.
3. Implement the core change — build the feature/fix in the target package.
4. Wire it together — connect the pieces across packages if needed.

Decision tree:
- Is this code used by multiple modules? YES → Create in the shared/common package.
- Is this code used by multiple modules? NO → Is this component multi-file? YES → Create folder with index.tsx + related files. NO → Single file, co-located with usage.
</build_order>

If you created any temporary files or scripts for iteration, remove them at the end.
</single_role_implementation>
</phase_4_execution>

<phase_5_quality_gates>
A task is not done until all quality gates pass. Run them in order for every affected package. If any gate fails, fix the issue and re-run all gates from the beginning.

Discover the available commands from package.json scripts for each affected package. Common gates:

1. Type checking — run the project's typecheck command (e.g., `tsc`, `typecheck`)
2. Linting — run the project's lint command (e.g., `lint`, `eslint`)
3. Tests (if available) — run the project's test command (e.g., `test`, `vitest`)
4. Build — run the project's build command (e.g., `build`)
5. Self-check — review your changes against the success criteria defined in phase 3.

For monorepos, run these for each affected workspace/package. Discover the workspace command pattern from CLAUDE.md or the root package.json (e.g., `yarn workspace <name> <script>`, `pnpm --filter <name> <script>`, `npm -w <name> <script>`, `turbo run <script> --filter=<name>`).

If a gate fails:
- Read the error output carefully.
- Fix the root cause (do not suppress or ignore errors).
- Re-run all gates from step 1, since a fix may introduce new issues.
- Repeat until all gates pass cleanly.
</phase_5_quality_gates>

<phase_5b_post_change_verification>
After all quality gates pass, re-run the verification plan from phase 3b and compare against baseline.

1. Re-run every check from phase 3b with identical parameters.
2. Compare each result against baseline:
   - **Quality gates**: must remain passing. New failures = regression.
   - **Visual checks** (if MCPs available): compare screenshots for unintended changes.
   - **Performance** (if MCPs available): compare metrics. Regressions > 10% must be investigated.
   - **API responses**: compare status codes and payload shapes. Breaking changes = regression.
3. Build the comparison table (see references/output-templates.md for format).

If any regression is found, fix it, re-run phase 5 quality gates, then re-run this phase. Repeat until clean.
</phase_5b_post_change_verification>

<phase_6_documentation>
After all quality gates pass, review whether the changes require documentation updates:

- CLAUDE.md — new commands, architecture changes, dependency graph updates, new conventions.
- Existing docs — new environment variables, setup steps, API contract changes.

Only update documentation directly affected by the changes. Do not create new documentation files unless the changes introduce a new package or major feature with no existing docs.
</phase_6_documentation>
</workflow>

<output>
When complete, produce the completion report including the baseline vs post-change comparison table. See references/output-templates.md for the exact format.

If the task document specifies a results file path, also create the comparison report at that path.

Do not add explanations, caveats, or follow-up suggestions unless the user explicitly asks. The report is the final output.
</output>

<task>
{{task}}
</task>
