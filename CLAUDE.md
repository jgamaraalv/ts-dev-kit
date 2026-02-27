# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ts-dev-kit is a **Claude Code plugin** (not a traditional app/library) that ships 15 specialized agents and 22 curated skills for TypeScript fullstack development. It is published to npm as `@jgamaraalv/ts-dev-kit` and distributed as markdown files — there is no build step, no TypeScript compilation, and no test suite.

## Common Commands

```bash
# Publish to npm
npm publish --access public

# Verify what gets published
npm pack --dry-run

# Version bump (update package.json, plugin.json, marketplace.json in sync)
# All three manifests must have matching versions
```

There are no build, lint, or test commands — this is a content-only package.

## Architecture

### Content Layout

```
.claude/
  agents/          ← 15 agent definitions (markdown, YAML frontmatter)
  skills/          ← 22 skill directories (symlinked from skills/)
  settings.local.json  ← Permission allowlist for Claude Code

.claude-plugin/
  plugin.json      ← Claude Code plugin manifest
  marketplace.json ← Marketplace listing metadata

agents/            ← Published copy of .claude/agents (included in npm package)
agent-memory/      ← 13 persistent memory directories (one per agent, excluded: multi-agent-coordinator, nextjs-expert)
skills/            ← 22 skill directories (each has SKILL.md + optional references/ and scripts/)
```

### Agent Definitions (`.claude/agents/*.md`)

Each agent is a single markdown file with YAML frontmatter:

```yaml
---
name: agent-name
color: named-color       # Visual identification in Claude Code UI
description: "..."
skills:                  # Optional — skills loaded when agent is invoked
  - skill-slug
---
```

Body contains: role description, core principles, workflow steps, quality gates, output format, and a reference to `agent-memory/<name>/MEMORY.md`.

### Skill Definitions (`skills/<name>/`)

Each skill directory contains:
- `SKILL.md` — main content with YAML frontmatter (`name`, `description`, optional `argument-hint`, optional `allowed-tools`)
- `references/` — deep-dive sub-files linked from SKILL.md
- `scripts/` — optional executables Claude can run (Python, bash) for visual output or automation

Skills are invoked via slash commands (e.g., `/fastify-best-practices`, `/drizzle-pg`). Patterns within skills are ranked by impact: CRITICAL, HIGH, MEDIUM, LOW.

### Key Design Decisions

- **Markdown-driven**: All agents and skills are plain markdown. Changes take effect immediately — no compilation needed.
- **Repository-agnostic agents**: Agents discover project conventions dynamically from the target project's CLAUDE.md, package.json, and codebase. They contain no hardcoded project paths.
- **Planner pattern**: `multi-agent-coordinator` returns structured dispatch plans for the caller to execute — it never implements code or dispatches subagents itself.
- **Agent memory**: Each agent has a persistent memory file at `agent-memory/<name>/MEMORY.md` (max 200 lines). Memory is project-scoped and version-controlled.

## Versioning & Release

Follows [Semantic Versioning](https://semver.org/) and [Keep a Changelog](https://keepachangelog.com/) format in `CHANGELOG.md`.

**Three manifests must stay in sync on every release:**
1. `package.json` → `version`
2. `.claude-plugin/plugin.json` → `version`
3. `.claude-plugin/marketplace.json` (if it contains a version field)

## Tech Stack Covered by Skills

TypeScript, Fastify 5, Next.js (App Router), React 19, PostgreSQL 16, Redis (ioredis), BullMQ, Drizzle ORM, TanStack Query v5, Docker, Playwright, Service Workers, Core Web Vitals, WCAG 2.1, OWASP Top 10:2025, Tailwind CSS v4.

## Dynamic Context Injection

Several skills use the `!`command`` syntax to pre-inject live data before Claude receives the prompt. Skills that do this declare `allowed-tools` in their frontmatter to whitelist the shell commands they run:

| Skill | Injected context |
|-------|-----------------|
| `/conventional-commits` | `git diff --cached`, `git log --oneline -8` |
| `/debug` | `git log --oneline -10`, `git status --short` |
| `/codebase-adapter` | `pwd`, lockfile, `.claude/agents/`, `.claude/settings.json`, `package.json` |
| `/yolo` | `pwd`, `.devcontainer/devcontainer.json`, `docker info`, `command -v docker`, `command -v code` |
