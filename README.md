# ts-dev-kit

> 15 specialized agents + 14 curated skills for TypeScript fullstack development

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

### Skills (14)

| Skill                  | Slug                      | Domain                                       |
| ---------------------- | ------------------------- | -------------------------------------------- |
| BullMQ                 | `/bullmq`                 | Redis job queues, workers, flows, schedulers |
| Composition Patterns   | `/composition-patterns`   | React compound components, render props      |
| Conventional Commits   | `/conventional-commits`   | Commit message spec, types, SemVer           |
| Docker                 | `/docker`                 | Dockerfiles, compose, optimization, security |
| Drizzle ORM            | `/drizzle-pg`             | PostgreSQL ORM schemas, queries, migrations  |
| Fastify Best Practices | `/fastify-best-practices` | Routes, plugins, hooks, validation           |
| ioredis                | `/ioredis`                | Redis client, pipelines, Pub/Sub, Cluster    |
| Next.js Best Practices | `/nextjs-best-practices`  | App Router, RSC, data patterns               |
| OWASP Security Review  | `/owasp-security-review`  | Top 10:2025 vulnerability checklist          |
| PostgreSQL             | `/postgresql`             | Queries, schemas, indexes, JSONB             |
| React Best Practices   | `/react-best-practices`   | React 19 performance, rendering              |
| Service Worker         | `/service-worker`         | PWA caching, push notifications              |
| TypeScript Conventions | `/typescript-conventions` | Strict config, patterns, best practices      |
| UI/UX Guidelines       | `/ui-ux-guidelines`       | Accessibility, layout, forms                 |

---

## Installation

### Method 1: skills.sh (works with Claude Code, Cursor, Windsurf)

```bash
# Install all skills
npx skills add jgamaraalv/ts-dev-kit

# List available skills
npx skills add jgamaraalv/ts-dev-kit --list

# Install a specific skill
npx skills add jgamaraalv/ts-dev-kit --skill fastify-best-practices

# Install globally
npx skills add jgamaraalv/ts-dev-kit --global
```

> **Note:** skills.sh installs skills only, not agents.

### Method 2: Claude Code Plugin (agents + skills)

```bash
/plugin marketplace add jgamaraalv/ts-dev-kit
/plugin install ts-dev-kit@ts-dev-kit
```

Or via CLI:

```bash
claude plugin install ts-dev-kit --scope user
```

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

## Customizing for Your Project

This kit ships with a project orchestration template at `docs/rules/orchestration.md.template`. It defines quality gates, workspace commands, and dependency ordering that you can adapt to your own monorepo or project.

To use it:

1. Copy the template into your project:
   ```bash
   cp node_modules/ts-dev-kit/docs/rules/orchestration.md.template \
      .claude/rules/orchestration.md
   ```
2. Open `.claude/rules/orchestration.md` and replace the `@myapp/*` placeholders with your actual workspace package names.
3. Update the dependency graph to match your monorepo structure.
4. Adjust the quality gate commands to match your project's tooling (e.g., swap `yarn` for `pnpm` or `npm`).

---

## Tech Stack Covered

TypeScript, Fastify 5, Next.js (App Router), React 19, PostgreSQL, Redis (ioredis), BullMQ, Drizzle ORM, Docker, Playwright, WCAG 2.1

---

## License

[MIT](LICENSE)
