# ts-dev-kit

> 15 specialized agents + 21 curated skills for TypeScript fullstack development

[![npm version](https://img.shields.io/npm/v/@jgamaraalv/ts-dev-kit)](https://www.npmjs.com/package/@jgamaraalv/ts-dev-kit)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)

---

## What's Included

### Agents (15)

| Agent                   | Specialty                                               |
| ----------------------- | ------------------------------------------------------- |
| accessibility-pro       | WCAG 2.1 AA compliance and inclusive design             |
| api-builder             | Fastify 5 REST APIs, validation, auth, rate limiting    |
| code-reviewer           | Code correctness, security, performance reviews         |
| database-expert         | PostgreSQL optimization, schema design, migrations      |
| debugger                | Error investigation, stack traces, systematic diagnosis |
| docker-expert           | Multi-stage builds, Compose, image optimization         |
| multi-agent-coordinator | Orchestrates multiple agents for complex workflows      |
| nextjs-expert           | App Router, RSC, edge functions, server actions         |
| performance-engineer    | Query optimization, caching, bundle reduction           |
| playwright-expert       | E2E tests, cross-browser, visual testing                |
| react-specialist        | Hooks, performance, state management, components        |
| security-scanner        | Vulnerability detection, OWASP, dependency auditing     |
| test-generator          | Unit, integration, E2E test suites                      |
| typescript-pro          | Generics, type inference, conditional types             |
| ux-optimizer            | User flows, form UX, friction reduction                 |

### Skills (21)

| Skill                  | Slug                      | Domain                                            |
| ---------------------- | ------------------------- | ------------------------------------------------- |
| BullMQ                 | `/bullmq`                 | Redis job queues, workers, flows, schedulers      |
| Codebase Adapter       | `/codebase-adapter`       | Adapt plugin to your project on installation      |
| Composition Patterns   | `/composition-patterns`   | React compound components, render props           |
| Conventional Commits   | `/conventional-commits`   | Commit message spec, types, SemVer — with live staged diff |
| Core Web Vitals        | `/core-web-vitals`        | LCP, INP, CLS reference + HTML report generator  |
| Debug                  | `/debug`                  | Full-stack debugging workflow, multi-agent triage |
| Docker                 | `/docker`                 | Dockerfiles, compose, optimization, security      |
| Drizzle ORM            | `/drizzle-pg`             | PostgreSQL ORM schemas, queries, migrations       |
| Execute Task           | `/execute-task`           | Orchestrate agents to implement a task file       |
| Fastify Best Practices | `/fastify-best-practices` | Routes, plugins, hooks, validation                |
| Generate PRD           | `/generate-prd`           | Product Requirements Documents from descriptions  |
| Generate Task          | `/generate-task`          | Break PRD features into agent-ready task files    |
| ioredis                | `/ioredis`                | Redis client, pipelines, Pub/Sub, Cluster         |
| Next.js Best Practices | `/nextjs-best-practices`  | App Router, RSC, data patterns                    |
| OWASP Security Review  | `/owasp-security-review`  | Top 10:2025 vulnerability checklist               |
| PostgreSQL             | `/postgresql`             | Queries, schemas, indexes, JSONB                  |
| React Best Practices   | `/react-best-practices`   | React 19 performance, rendering                   |
| Service Worker         | `/service-worker`         | PWA caching, push notifications                   |
| TanStack Query         | `/tanstack-query`         | React Query v5, caching, SSR/hydration            |
| TypeScript Conventions | `/typescript-conventions` | Strict config, patterns, best practices           |
| UI/UX Guidelines       | `/ui-ux-guidelines`       | Accessibility, layout, forms                      |

---

## Workflow

This is the recommended end-to-end flow — from a blank project to a committed feature:

### 1. Install the plugin

```bash
/plugin marketplace add jgamaraalv/ts-dev-kit
/plugin install ts-dev-kit@ts-dev-kit
```

### 2. Adapt to your project (recommended)

Run once after installing to align agents and skills with your actual stack, package names, paths, and MCPs:

```
/codebase-adapter
```

The skill reads your `package.json`, lockfile, `.claude/agents/`, and MCP config, then surgically patches the plugin's agent and skill files to match your project — without touching any workflow logic.

### 3. Define what to build

Generate a PRD from a description:

```
/generate-prd Add a user notification system that sends emails and in-app alerts
```

Then break it into agent-ready task files:

```
/generate-task
```

This produces structured task files with acceptance criteria, affected packages, quality gate commands, and a suggested agent.

### 4. Execute the task

```
/execute-task tasks/notifications-api.md
```

The skill picks the right execution mode (single-agent or multi-agent), dispatches the appropriate agents, and runs quality gates (typecheck, lint, test) before declaring the task done.

### 5. Commit

```
/conventional-commits
```

The skill pre-injects your staged diff and the last 8 commits so Claude sees the actual changes before suggesting a message — no copy-pasting needed.

---

## Installation

### Method 1: Claude Code Plugin (agents + skills)

```bash
/plugin marketplace add jgamaraalv/ts-dev-kit
/plugin install ts-dev-kit@ts-dev-kit
```

Or via CLI:

```bash
claude plugin install ts-dev-kit --scope user
```

### Method 2: skills.sh (skills only — works with Claude Code, Cursor, Windsurf)

```bash
# Install all skills
npx skills add jgamaraalv/ts-dev-kit

# Install a specific skill
npx skills add jgamaraalv/ts-dev-kit --skill fastify-best-practices

# Install globally
npx skills add jgamaraalv/ts-dev-kit --global
```

> **Note:** skills.sh installs skills only, not agents.

### Method 3: npm

```bash
npm install -g @jgamaraalv/ts-dev-kit
claude --plugin-dir ./node_modules/@jgamaraalv/ts-dev-kit
```

### Method 4: Direct from GitHub

```bash
git clone https://github.com/jgamaraalv/ts-dev-kit.git
claude --plugin-dir ./ts-dev-kit
```

---

## Recommended MCP Servers

Some agents and skills reference external MCP tools for documentation lookup, browser debugging, E2E testing, and web fetching. These are **optional** — skills degrade gracefully without them — but installing them unlocks the full experience.

| MCP Server      | Used by                                          | Purpose                              |
| --------------- | ------------------------------------------------ | ------------------------------------ |
| context7        | Most skills (doc lookup)                         | Query up-to-date library docs        |
| playwright      | playwright-expert, debugger, test-generator      | Browser automation and E2E testing   |
| chrome-devtools | debugger                                         | Frontend debugging, screenshots      |
| firecrawl       | execute-task                                     | Web fetching and scraping            |
| sentry          | debugger, debug skill                            | Error tracking and stack traces      |
| posthog         | debugger                                         | User impact and error frequency      |

### Installing as Claude Code plugins

```bash
claude plugin add context7
claude plugin add playwright
claude plugin add firecrawl
```

### Installing as standalone MCP servers

```bash
# context7 — no API key required
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest

# playwright — no API key required
claude mcp add playwright -- npx -y @playwright/mcp@latest

# firecrawl — requires FIRECRAWL_API_KEY
claude mcp add firecrawl --env FIRECRAWL_API_KEY=your-key -- npx -y firecrawl-mcp
```

> **chrome-devtools** requires Chrome running with remote debugging enabled (`--remote-debugging-port=9222`). Refer to the [Chrome DevTools MCP docs](https://github.com/anthropics/mcp-chrome-devtools) for setup instructions.

---

## Dynamic Context Injection

Several skills use the `!`command`` syntax to pre-inject live data before Claude receives the prompt. This means Claude already has the real context when it starts — no manual copy-pasting required.

| Skill | What gets injected |
| ----- | ------------------ |
| `/conventional-commits` | Staged diff summary, full staged diff, last 8 commit messages |
| `/debug` | Last 10 git commits, working tree status |
| `/codebase-adapter` | Working directory, lockfile, installed agents, MCP servers, `package.json` |

---

## Tech Stack Covered

TypeScript, Fastify 5, Next.js (App Router), React 19, PostgreSQL 16, Redis (ioredis), BullMQ, Drizzle ORM, TanStack Query v5, Docker, Playwright, Service Workers, Core Web Vitals, WCAG 2.1, OWASP Top 10:2025, Tailwind CSS v4

---

## License

[MIT](LICENSE)
