# Agent Dispatch Reference

## Agent prompt template

Project agents (`.claude/agents/`) already include project context, workflow, principles, quality gates, and output format in their system prompt. The dispatch prompt only needs **task-specific** information:

```
## Your task
[Specific task scope — what to build, what files to create/modify]

## Existing patterns to follow
[Paste relevant code snippets, file paths, or describe the patterns the agent should match]

## Success criteria
[What "done" looks like — be specific]
```

For agents that load skills dynamically (debugger, performance-engineer), also include:

```
## Skills to load
Call the Skill tool before starting:
- Skill(skill: "[skill-1]")
- Skill(skill: "[skill-2]")
```

### Preloaded skills by agent

Agents with preloaded skills (via `skills` frontmatter) do NOT need Skill() calls for their primary domain. Only include Skill() calls for additional skills beyond what the agent already has:

| Agent | Preloaded skills | Dynamic skills (add when needed) |
|-------|-----------------|----------------------------------|
| api-builder | fastify-best-practices | drizzle-pg, postgresql (if DB-heavy) |
| react-specialist | react-best-practices, composition-patterns | nextjs-best-practices (if page-level) |
| database-expert | drizzle-pg, postgresql | — |
| docker-expert | docker | — |
| security-scanner | owasp-security-review | — |
| ux-optimizer | ui-ux-guidelines | — |
| accessibility-pro | ui-ux-guidelines | — |
| debugger | (none) | Load based on bug domain |
| performance-engineer | (none) | Load based on optimization domain |
| code-reviewer | (none) | Read-only agent, no Write/Edit |
| test-generator | (none) | fastify-best-practices (for API tests) |
| typescript-pro | (none) | — |
| playwright-expert | (none) | — |

> **Note:** When ts-dev-kit is installed as a plugin, agent names are prefixed with the plugin namespace (e.g., `ts-dev-kit:api-builder` instead of `api-builder`). Always check the available agents in your context and use the full registered name as `subagent_type`.

### Agent tool restrictions

| Agent | Restriction |
|-------|------------|
| code-reviewer | `disallowedTools: Write, Edit` — review only, cannot modify code |
| All others | Full tool access (inherited from parent) |

Plan accordingly: if a review finds issues, dispatch a separate agent to fix them.

## Model selection

Choose the model for each agent based on task complexity:

| Complexity | Model | Examples |
|-----------|-------|---------|
| Simple | `haiku` | Adding a type, writing a small utility, updating config, barrel file exports |
| Moderate | `sonnet` | Implementing a feature within a single domain, writing tests, building a component |
| Complex | `opus` | Cross-cutting concerns, architectural decisions, novel implementations requiring deep reasoning |

All agents default to `sonnet`. Override with the Task tool's `model` parameter when needed.

## Dispatch example

```
// Use the agent name as registered in your context.
// Project-scoped: "api-builder". Plugin-scoped: "ts-dev-kit:api-builder".
Task(
  description: "Build resource API routes",
  subagent_type: "api-builder",  // or "ts-dev-kit:api-builder" if plugin-scoped
  model: "sonnet",
  prompt: """
## Your task
Create REST endpoints for the [feature name]:
- POST /api/<resource> — create a new resource
- GET /api/<resource>/:id — get resource details
- PATCH /api/<resource>/:id — update resource

## Existing patterns to follow
Discover from the codebase:
- Route structure: look for existing route handlers and follow the same pattern
- Shared schemas: look for existing schema/type definitions in shared packages
- Use case pattern: look for existing use case or service implementations

## Success criteria
- All endpoints respond with correct status codes
- Request/response validated with shared schemas
- Endpoints follow the project's routing conventions
"""
)
```

## Dispatch with worktree isolation

When parallel agents touch overlapping files (e.g., both modify a shared barrel export or the same config), add `isolation: "worktree"` to each Task() call. Each agent gets an isolated copy of the repository, preventing edit conflicts.

```
// Two agents that both touch shared/src/index.ts — dispatch in parallel with worktree isolation
Task(
  description: "Add user schema and migration",
  subagent_type: "database-expert",
  model: "sonnet",
  isolation: "worktree",
  prompt: """
## Your task
Create the users table schema and migration...

## Success criteria
- Schema exported from shared package
- Migration runs cleanly
"""
)

Task(
  description: "Add notification schema and migration",
  subagent_type: "database-expert",
  model: "sonnet",
  isolation: "worktree",
  prompt: """
## Your task
Create the notifications table schema and migration...

## Success criteria
- Schema exported from shared package
- Migration runs cleanly
"""
)
```

After both agents complete, review the worktree results. If both modified the same file (e.g., a barrel export), manually merge the additions into the main working directory.

**When NOT to use worktree isolation:**
- Agents touch completely separate files → plain parallel dispatch (no isolation overhead).
- One agent depends on the other's output → sequential dispatch (await the blocker first).

## Agent type resolution

Before dispatching, resolve the agent type for each role:

1. **Resolve the agent name for the current scope.** Agents may be registered with a plugin prefix depending on how ts-dev-kit is installed:
   - **Project scope** (`.claude/agents/`): short name — e.g., `api-builder`
   - **Plugin scope**: prefixed — e.g., `ts-dev-kit:api-builder`
   Check which agents are available in your context and use the exact registered name as `subagent_type`.
2. **Use a built-in agent type** — if the Task tool has a matching built-in type (e.g., `typescript-pro`, `performance-engineer`, `security-scanner`), use it directly.
3. **Create an ad-hoc specialist** — if no existing agent matches, use `subagent_type: "general-purpose"` and embed the full specialist definition in the prompt.

### Ad-hoc specialist prompt structure

When no matching agent exists, the prompt must be fully self-contained — `general-purpose` has no pre-loaded domain knowledge, project context, or skills:

```
You are a [specialist title] working on this project.

Your expertise: [specific technologies, frameworks, and techniques].

## Before writing any code
1. Read CLAUDE.md and relevant package.json files to understand the project structure, conventions, and available commands.
2. Call the Skill tool to load domain skills:
   - Skill(skill: "[skill-1]")
   - Skill(skill: "[skill-2]")

## Project context
Discover from CLAUDE.md and package.json:
- Project structure (monorepo layout, key directories, packages)
- Technologies and versions (frameworks, libraries, language settings)
- Import conventions (named vs default, module system)
- Code style (formatter config, linting rules)
[add more context specific to the task if known]

## Library documentation lookup
When you need to verify API signatures or version-specific behavior, use Context7:
1. `mcp__context7__resolve-library-id` — resolve the library name to its ID.
2. `mcp__context7__query-docs` — query the specific API or pattern.

## Your task
[task details]

## Existing patterns to follow
[code snippets or file references]

## Success criteria
[what "done" looks like]

## Quality gates
Run the project's type checking, linting, testing, and build commands for every package you touched. Discover available commands from package.json scripts. Fix failures before reporting done.

## Output
Report when done:
- Summary: one sentence of what was done.
- Files: each file created/modified.
- Quality gates: pass/fail for each.
```

## Key constraints

1. **Subagents cannot spawn other subagents.** All dispatch happens from the main session.
2. **Agent prompts should be concise and task-specific.** Project agents already include project context, conventions, principles, and quality gates in their system prompt. Only include information the agent doesn't already have.
3. **Ad-hoc prompts must be fully self-contained.** The `general-purpose` agent has no project context, so the prompt must include everything: role, project context, conventions, skills to load, quality gates, and output format.
4. **Review each agent's output before dispatching dependents.** If an agent failed or produced unexpected results, dispatch a fix agent — do NOT fix inline in the orchestrator.
5. **Parallel means parallel.** When dispatching independent agents, include ALL Task() calls in a single message. If you announce "dispatching 3 agents in parallel", there must be exactly 3 Task() tool calls in that message. Never sequentialize independent work.
6. **Context7 before config.** Before writing or modifying ANY configuration file for a versioned tool, query Context7 to verify the correct syntax for the installed version. Do not guess-loop config variations.
