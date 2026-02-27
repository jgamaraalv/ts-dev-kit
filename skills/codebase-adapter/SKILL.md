---
name: codebase-adapter
description: "Adapts ts-dev-kit plugin files to the host project where it is installed. Use when: (1) installing ts-dev-kit in a new project for the first time, (2) project tech stack or structure has changed, (3) agents reference wrong paths, unavailable skills, or missing MCPs, (4) the user says 'adapt the plugin', 'configure ts-dev-kit for this project', 'sync plugin to this codebase', or 'update plugin context'. Surgically edits specific sections in plugin skills and agent definitions — domain area tables, skill/MCP references, quality gate commands, project paths, and package names — without touching any workflow logic, execution protocols, or dispatch patterns."
disable-model-invocation: true
argument-hint: "[optional: path to project root — defaults to current directory]"
allowed-tools: Bash(ls *), Bash(cat *), Bash(node *), Bash(python3 *)
---

<system>
You are a plugin configuration specialist. You adapt specific, well-defined sections in ts-dev-kit's skill and agent files to match the host project — making them accurate and immediately useful without touching any workflow, phase logic, or behavioral patterns.
</system>

<context>
**User-provided path:** $ARGUMENTS

**Pre-injected project snapshot (verify in phase 2 — do not skip discovery):**

Working directory: !`pwd`

Lockfile detected: !`ls bun.lock pnpm-lock.yaml yarn.lock package-lock.json 2>/dev/null | head -1 || echo "none"`

Agents installed: !`ls .claude/agents/ 2>/dev/null | tr '\n' ' ' || echo "(not found)"`

MCP servers configured: !`python3 -c "import json; s=json.load(open('.claude/settings.json')); print(', '.join(s.get('mcpServers',{}).keys()) or '(none)')" 2>/dev/null || echo "(not found)"`

package.json:
!`cat package.json 2>/dev/null || echo "(not found)"`
</context>

<boundaries>
**You MAY edit:**
- `<domain_areas>` table in `execute-task` — agent names and key skills per sub-area
- `<skill_map>` in `execute-task` — which skills map to which sub-areas
- `<available_mcps>` in `execute-task` — only MCPs actually configured in this project
- `skills:` frontmatter list in agent definitions
- Quality gate command examples in agent bodies (e.g., `yarn workspace @myapp/api test`)
- Project path references in agent bodies (e.g., `apps/api/src/routes/`)
- Package name references in agent bodies (e.g., `@myapp/api`, `@myapp/shared`)
- Tech-specific import/version notes in agent bodies (Zod v3 vs v4, ESM flag)
- Workspace command pattern in `generate-task` (e.g., `yarn workspace <name>` → `pnpm --filter <name>`)

**You MUST NOT change:**
- Any `<phase_*>` logic or step sequences
- Dispatch protocols, decomposition rules, execution mode decisions
- Core agent principles, role descriptions, or behavior narratives
- Output template formats or section headers
- Skill descriptions or their trigger conditions
- XML tag structures (`<workflow>`, `<domain_areas>`, `<skill_map>`, etc.)
</boundaries>

<workflow>

<phase_1_locate_plugin>
Find the plugin root. Try in order:
1. `skills/execute-task/SKILL.md` exists in current directory → user is inside the ts-dev-kit repo.
2. `node_modules/@jgamaraalv/ts-dev-kit/` → installed via npm.
3. Search upward and in siblings for a directory containing `plugin.json` with `"name": "ts-dev-kit"`.

Store the resolved plugin root. All edits in phases 3–5 use paths relative to it.
</phase_1_locate_plugin>

<phase_2_project_discovery>
Determine the target project root (`$ARGUMENTS` if provided, otherwise current working directory).

Discover with Read, Glob, Grep — verify everything, assume nothing.

**Package manager** — detect from lockfile: `bun.lock` → bun, `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `package-lock.json` → npm.

**Monorepo** — check for `workspaces` in `package.json`, `pnpm-workspace.yaml`, or `turbo.json`. Record workspace names and their paths.

**Tech stack** — read `package.json` dependencies in root and each workspace:
- HTTP framework: Fastify, Express, Hono, Elysia, or none
- ORM/DB: Drizzle, Prisma, Kysely + database type (PostgreSQL, MySQL, SQLite)
- Frontend: Next.js (detect App Router via `app/` directory), Vite + React, or none
- Validation: Zod (check version — v3 imports `from "zod"`, v4 imports `from "zod/v4"`), Valibot
- Queue: BullMQ, or none
- Cache: ioredis, @upstash/redis, or none
- Testing: Vitest or Jest; Playwright or Cypress
- Docker: check for `Dockerfile` or `docker-compose.yml`

**Project paths** (verify with Glob — record exact paths):
- Backend source root (e.g., `apps/api/src/`, `src/`)
- Routes/handlers directory
- DB schema + migrations directory
- DB client file (search for database connection setup)
- Redis client file (search for Redis instantiation)
- Frontend source root (e.g., `apps/web/`, `src/`)
- Shared package: directory path and package name (e.g., `packages/shared/`, `@acme/shared`)

**Quality gates** — read `scripts` from each workspace's `package.json`:
- typecheck, lint, test, build command names
- Compose the full run command per workspace (e.g., `pnpm --filter @acme/api typecheck`)

**Available skills** — list directories in `[plugin-root]/skills/`

**Available agents** — list files in `[plugin-root]/.claude/agents/`

**Available MCPs** — read `.claude/settings.json` in project root (and `~/.claude/settings.json` as fallback). Extract `mcpServers` keys.
</phase_2_project_discovery>

<phase_3_adapt_execute_task>
Edit `[plugin-root]/skills/execute-task/SKILL.md`.

**`<domain_areas>` block (lines between the opening and closing tags)**

Rebuild the Backend and Frontend tables:
- "Agent type" column: only include agents whose `.md` file exists in `[plugin-root]/.claude/agents/`
- "Key skills" column: only include skills whose directory exists in `[plugin-root]/skills/` AND are relevant to the discovered tech stack
- Remove rows for sub-areas with no matching tech (e.g., remove "Queues" row if BullMQ is absent; remove "Pages/routing" row if no frontend framework is detected)
- Keep the "When" column text unchanged
- Keep the surrounding narrative text and the Cross-cutting specialists table unchanged

**`<skill_map>` block**

Update each sub-area's skill list:
- Remove skills not present in `[plugin-root]/skills/`
- Remove skills not relevant to discovered tech (e.g., remove `/bullmq` if BullMQ not installed)
- Keep the exact slash-command format (e.g., `/drizzle-pg`, `/fastify-best-practices`)

**`<available_mcps>` block**

Replace the bullet list with only MCPs found in `mcpServers`. Keep the same format: `- [name] — [one-line purpose]`. If context7 is configured, always keep its usage instructions below the list intact.

**`<required_skills>` example block**

Update the example `Skill()` calls to reflect the project's actual primary backend skills (e.g., replace `fastify-best-practices` if Fastify is not the framework).
</phase_3_adapt_execute_task>

<phase_4_adapt_agents>
For each file in `[plugin-root]/.claude/agents/`:

**`skills:` frontmatter list**
Remove skills not installed in `[plugin-root]/skills/` or not relevant to the discovered tech stack. Do not add skills not already listed. If all skills remain valid, skip this file.

**Quality gate command examples**
Find patterns like `yarn workspace @myapp/api test` or `yarn workspace @myapp/api tsc`. Replace with the actual workspace run command composed in phase 2. Use real workspace package names where known.

**Project path references**
Find and replace generic placeholder paths with actual discovered paths:
| Placeholder | Replace with |
|-------------|-------------|
| `apps/api/src/` | actual backend source root |
| `apps/api/src/routes/` | actual routes directory |
| `apps/api/src/lib/db.ts` | actual DB client file path |
| `apps/api/src/lib/redis.ts` | actual Redis client file path |
| `packages/shared/src/` | actual shared package source path |

**Package name references**
Replace placeholder names with actual package names:
| Placeholder | Replace with |
|-------------|-------------|
| `@myapp/api` | actual API workspace package name |
| `@myapp/shared` | actual shared workspace package name |

**Tech-specific notes**
- Zod import: update to match discovered version (`from "zod"` for v3, `from "zod/v4"` for v4)
- ESM flag: match `"type": "module"` presence in the workspace's `package.json`

Skip any agent where none of the above patterns are found — do not force edits.
</phase_4_adapt_agents>

<phase_5_adapt_generate_task>
Edit `[plugin-root]/skills/generate-task/SKILL.md`.

Find the workspace command pattern example (text like `yarn workspace <name> <script>`, `pnpm --filter <name> <script>`). Replace all occurrences with the actual package manager syntax discovered in phase 2. Use `<name>` and `<script>` as placeholders where the real values would vary.
</phase_5_adapt_generate_task>

<phase_6_update_claude_md>
Append a "## Claude Code Workflow Architecture" section to the project's `CLAUDE.md` (located at the project root). If `CLAUDE.md` does not exist, create it with only this section. If the section already exists, replace it in-place with the updated version.

Use the data already gathered in phases 1–2 to fill in the values:

**Agent count** — count `.md` files in the project's `.claude/agents/` directory (this includes both plugin-installed agents and any locally defined agents).

**Skill count** — count directories in the project's `.claude/skills/` directory (this includes both plugin-installed skills and any locally defined skills).

**agent-memory** — check whether `agent-memory/` exists at the project root. If it does, count its subdirectories and note which agents are excluded (agents without a matching subdirectory).

**Paths** — use the actual plugin-root-relative paths discovered in phase 2 (e.g., real `skills/`, `agents/`, `.claude/` locations).

Generate the section using this template, substituting bracketed placeholders with real values:

```markdown
## Claude Code Workflow Architecture

### Content Layout

\`\`\`
.claude/
  agents/          ← [AGENT_COUNT] agent definitions (markdown, YAML frontmatter)
  skills/          ← [SKILL_COUNT] skill directories (symlinked from skills/)
  settings.local.json  ← Permission allowlist for Claude Code

.claude-plugin/
  plugin.json      ← Claude Code plugin manifest
  marketplace.json ← Marketplace listing metadata

agents/            ← Published copy of .claude/agents (included in npm package)
[AGENT_MEMORY_LINE]
skills/            ← [SKILL_COUNT] skill directories (each has SKILL.md + optional references/ and scripts/)
\`\`\`

### Agent Definitions (\`.claude/agents/*.md\`)

Each agent is a single markdown file with YAML frontmatter:

\`\`\`yaml
---
name: agent-name
color: named-color       # Visual identification in Claude Code UI
description: "..."
skills:                  # Optional — skills loaded when agent is invoked
  - skill-slug
---
\`\`\`

Body contains: role description, core principles, workflow steps, quality gates, output format, and a reference to \`agent-memory/<name>/MEMORY.md\`.

### Skill Definitions (\`skills/<name>/\`)

Each skill directory contains:
- \`SKILL.md\` — main content with YAML frontmatter (\`name\`, \`description\`, optional \`argument-hint\`, optional \`allowed-tools\`)
- \`references/\` — deep-dive sub-files linked from SKILL.md
- \`scripts/\` — optional executables Claude can run (Python, bash) for visual output or automation
```

Where `[AGENT_MEMORY_LINE]` is:
- If `agent-memory/` exists: `agent-memory/      ← [SUBDIR_COUNT] persistent memory directories (one per agent[EXCLUSION_NOTE])`
  - `[EXCLUSION_NOTE]` = `, excluded: [list agents without a subdirectory]` if any are missing, otherwise omit
- If `agent-memory/` does not exist: omit that line entirely
</phase_6_update_claude_md>

<phase_7_report>
Produce the completion report using the template in [template.md](template.md).
</phase_7_report>

</workflow>
