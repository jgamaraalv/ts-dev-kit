# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
