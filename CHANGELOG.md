# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
