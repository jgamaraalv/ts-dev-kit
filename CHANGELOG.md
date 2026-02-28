# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.0.0] - 2026-02-28

### Changed

- Expand `/typescript-conventions` skill with 7 new sections: Interface vs Type, Unions and Literal Types, Discriminated Unions, Type Narrowing, Generics, Mapped & Template Literal Types, and Intersection Types — previously covered only strict mode, branded types, imports, error handling, naming, and anti-patterns
- Expand `/typescript-conventions` anti-patterns from 3 to 10 entries — adds narrowing, broad unions, shallow readonly, enum misuse, unconstrained generics, conflicting intersections, and missing exhaustiveness checks
- Update `/typescript-conventions` skill description to reflect new coverage areas (type definitions, type narrowing, discriminated unions, generics)
- Replace ASCII hyphens with em dashes in error handling section for consistency

### Added

- `.firecrawl` to `.gitignore`

### BREAKING CHANGE

- `/typescript-conventions` skill description changed — projects that match skills by description string may need to update their matching logic to account for the expanded trigger list (now includes type definitions, type narrowing, discriminated unions, generics)

## [5.0.0] - 2026-02-28

### Changed

- Standardize all 15 reference and workflow skills to use semantic XML tags (`<rules>`, `<quick_reference>`, `<examples>`, `<anti_patterns>`, `<gotchas>`, `<constraints>`, `<references>`, `<workflow>`, `<output>`) — previously only 7 workflow skills used XML tags while 15 reference skills used plain markdown headings
- Skills with multi-step workflows (`owasp-security-review`, `ui-ux-guidelines`) now use `<workflow>` with numbered `<phase_N_name>` tags matching the pattern established by `debug`, `execute-task`, and `generate-prd`

### BREAKING CHANGE

- All skill SKILL.md files now wrap content sections in XML tags. Custom forks or overrides that parse skill files by markdown heading structure may need updating to account for the new XML tag wrappers.

## [4.0.0] - 2026-02-27

### Added

- Publish `multi-agent-coordinator` agent to the npm package — previously only available locally in `.claude/agents/`, now shipped in `agents/` with all other agents
- Publish `nextjs-expert` agent to the npm package — rewritten as repository-agnostic (no hardcoded paths, commands, or project-specific conventions); discovers project structure dynamically
- Add `agent-memory/nextjs-expert/` persistent memory directory
- Add worktree isolation support to `/execute-task` dispatch protocol: new decision tree in `rule_3_execution_order`, new dispatch step for `isolation: "worktree"` on parallel agents with overlapping files, new anti-pattern #5 ("never dispatch parallel agents on overlapping files without worktree isolation"), new self-check item
- Add worktree isolation dispatch example to `/execute-task` agent-dispatch reference with concrete `isolation: "worktree"` Task() calls and guidance on when NOT to use isolation
- Add `isolation` field to `multi-agent-coordinator` dispatch plan output format — parallel tasks that touch overlapping files now include `isolation: worktree`
- Add worktree isolation rule to `multi-agent-coordinator` planning guidelines

### Changed

- Agent count in published `agents/` directory: 13 → 15 (now matches the "15 agents" stated in all manifests)
- Agent memory count: 13 → 14 directories (added nextjs-expert; multi-agent-coordinator excluded as planner-only)
- CLAUDE.md content layout updated to reflect correct agent-memory count (14) and exclusion list (only multi-agent-coordinator)

### BREAKING CHANGE

- All 15 agents are now published in the npm package. Projects that relied on the previous 13-agent subset and have custom agent overrides for `multi-agent-coordinator` or `nextjs-expert` may experience conflicts with the newly published versions.

## [3.3.0] - 2026-02-27

### Added

- `/execute-task` orchestrator anti-patterns section: 4 explicit rules (never fix errors inline, never guess-loop configs, never announce parallel without delivering it, never write application code as orchestrator) with a pre-send self-check checklist
- `/execute-task` agent-dispatch rules 5–6: parallel dispatch enforcement ("parallel means parallel") and mandatory Context7-before-config policy

### Changed

- `/execute-task` Context7 guidance upgraded from optional recommendation to **mandatory** for all config and versioned API files — must query docs before writing any configuration
- `/execute-task` parallel dispatch rule now includes CRITICAL annotation: announcing N parallel agents requires exactly N Task() calls in the same message
- `/execute-task` quality gate failure handling: orchestrator must dispatch a specialist agent to fix errors instead of fixing inline (prevents context exhaustion and mid-task compaction)

## [3.2.0] - 2026-02-27

### Added

- Cross-scope agent name resolution: `/execute-task` and `/debug` dispatch protocols now detect whether agents are registered with a plugin prefix (`ts-dev-kit:agent-name`) and use the correct `subagent_type` automatically
- `/yolo` Phase 1.5 — Ensure plugin availability: when ts-dev-kit is installed as a plugin, copies agents, skills, and agent-memory into the project before mounting the devcontainer so they're accessible inside the container
- `/codebase-adapter` scope-aware discovery: phase 2 now searches agents and skills across project scope (`.claude/`), plugin scope (`node_modules/`), and personal scope (`~/.claude/`)

### Fixed

- Agent memory paths in all 13 agents now use dynamic resolution (`agent-memory/<name>/` at project root first, fallback to `.claude/agent-memory/<name>/`) instead of a hardcoded `.claude/` prefix
- `/core-web-vitals` visualize script path no longer hardcoded to `~/.claude/skills/` — now discovers the correct path across all installation scopes

## [3.1.3] - 2026-02-27

### Fixed

- `/yolo` firewall script: revert to strict upstream reference (`set -euo pipefail`, no fallbacks) — remove `exec > >(tee ...)` that caused VS Code to hang with "Unable to resolve resource", remove `|| true` fallbacks that masked failures, remove `| tee` from `postStartCommand`; keep only the `sort -u` dedup fix for duplicate DNS IPs
- `/yolo` SKILL.md: document critical anti-patterns (process substitution logging, loose error handling, piped postStartCommand)

## [3.1.2] - 2026-02-27

### Fixed

- `/yolo` firewall script: deduplicate DNS results with `sort -u` in `resolve_domain()` to prevent `ipset add` failure on duplicate IPs (root cause: `marketplace.visualstudio.com` returns the same IP twice)

## [3.1.1] - 2026-02-27

### Fixed

- `/yolo` firewall script: add resilient fallback for Docker Desktop environments where `ipset` kernel module is unavailable — falls back to iptables-only rules, `getent` DNS resolution, and direct GitHub domain resolution; full diagnostic log at `/tmp/firewall-init.log`

## [3.1.0] - 2026-02-27

### Added

- `/yolo` skill: devcontainer setup and launch workflow for running Claude Code with `--dangerously-skip-permissions` in a secure, sandboxed environment — detects existing devcontainer, checks Docker status, scaffolds the Claude Code reference `.devcontainer/` (Dockerfile, firewall, config), starts Docker if needed, and opens VS Code to launch the container
- Dynamic context injection to `/yolo`: project root, devcontainer presence, Docker daemon status, Docker and VS Code installation are pre-injected before Claude receives the prompt

## [3.0.1] - 2026-02-27

### Fixed

- Normalize `repository.url` in `package.json` to `git+https://` format as required by npm

## [3.0.0] - 2026-02-27

### Added

- `/codebase-adapter` skill: surgically adapts plugin agent/skill files to the host project on installation — updates domain area tables, skill maps, MCP references, quality gate commands, and package names without touching workflow logic
- `/core-web-vitals` skill: LCP, INP, CLS reference covering thresholds, field vs lab tooling, diagnosis guides, and optimization patterns; includes `scripts/visualize.py` for generating interactive HTML reports from metric values or Lighthouse JSON output
- `/debug` skill: end-to-end debugging workflow with multi-layer triage, single/multi-layer execution modes, and agent dispatch templates for backend, frontend, queue, and E2E layers
- `/generate-prd` skill: produces structured Product Requirements Documents from feature descriptions or user stories
- `/generate-task` skill: breaks PRD features into granular, agent-ready task files with acceptance criteria, affected packages, and quality gate commands
- Dynamic context injection (`!`command`` syntax) to `/conventional-commits`: staged diff summary, full staged diff (up to 300 lines), and recent commit log are pre-injected before Claude receives the prompt
- Dynamic context injection to `/debug`: last 10 git commits and working tree status are pre-injected at invocation time to accelerate triage
- Dynamic context injection to `/codebase-adapter`: working directory, detected lockfile, installed agents, configured MCP servers, and `package.json` are pre-injected to reduce manual discovery
- `allowed-tools` frontmatter to `/conventional-commits`, `/debug`, `/codebase-adapter`, and `/core-web-vitals` — whitelists the shell commands needed for dynamic injection and script execution
- `scripts/` subdirectory convention for skills that bundle executable tools (Python, bash)

### Changed

- Renamed skill `/task` → `/execute-task` (update any project references or task files that invoke this command)

### Breaking Changes

- `/task` slash command removed; use `/execute-task` instead

## [2.3.0] - 2026-02-26

### Added

- `/tanstack-query` skill: TanStack Query v5 (React Query) reference covering `useQuery`, `useMutation`, `useInfiniteQuery`, `QueryClient`, SSR/hydration with Next.js, optimistic updates, cache invalidation, and TypeScript patterns

## [2.2.0] - 2026-02-26

### Changed

- Enforce mandatory agent delegation in all `/execute-task` execution modes — tasks are always dispatched to specialized agents; direct implementation by the orchestrator is no longer permitted

## [2.1.0] - 2026-02-25

### Added

- Baseline capture phase to `/execute-task`: records the state of quality gates before any changes
- Post-change verification phase to `/execute-task`: re-runs quality gates after the fix and diffs against baseline to confirm no regressions were introduced

## [2.0.0] - 2026-02-24

### Changed

- Make all 15 agents fully repository-agnostic: agents now discover project conventions dynamically from `CLAUDE.md`, `package.json`, and the codebase — no hardcoded paths, package names, or workspace commands remain in any agent definition

### Breaking Changes

- Any project-specific overrides embedded directly in agent files are no longer applied; configure project context in your project's `CLAUDE.md` instead

## [1.2.1] - 2026-02-24

### Fixed

- Sync plugin manifest versions (`marketplace.json`, `plugin.json`) with package version

## [1.2.0] - 2026-02-24

### Changed

- Simplify agent frontmatter: remove redundant `tools`, `model`, and `memory` fields (now inherited by default)
- Replace hex color codes with named colors across all 15 agent definitions
- Normalize markdown formatting (table alignment, section spacing, code block syntax)

## [1.1.0] - 2026-02-23

### Changed

- Rewrite multi-agent-coordinator to be fully repository-agnostic (removes all project-specific conventions; discovers conventions dynamically from the codebase)
- Add mandatory codebase discovery step before plan generation
- Simplify and streamline agent definition (cleaner output format, focused planning guidelines)

## [1.0.3] - 2026-02-23

### Changed

- Rewrite multi-agent-coordinator as planner-only pattern (no longer dispatches subagents directly; produces structured dispatch plans for the caller to execute)
- Reduce multi-agent-coordinator tools from Read/Write/Edit/Bash/Grep/Glob/Task to Read/Grep/Glob

### Added

- Color field to all 15 agent definitions for visual identification in Claude Code UI
- `.gitignore` to exclude `.claude` directory

## [1.0.0] - 2026-02-21

### Added

- 15 specialized agents for TypeScript fullstack development
  - accessibility-pro, api-builder, code-reviewer, database-expert, debugger
  - docker-expert, multi-agent-coordinator, nextjs-expert, performance-engineer
  - playwright-expert, react-specialist, security-scanner, test-generator
  - typescript-pro, ux-optimizer
- 14 curated skills with reference documentation
  - bullmq, composition-patterns, conventional-commits, docker, drizzle-pg
  - fastify-best-practices, ioredis, nextjs-best-practices, owasp-security-review
  - postgresql, react-best-practices, service-worker, typescript-conventions
  - ui-ux-guidelines
- Orchestration template for project-specific quality gates
- Plugin manifests for Claude Code marketplace
- Compatible with skills.sh for cross-agent installation
