---
name: generate-task
description: "Breaks a PRD into ordered, production-ready engineering tasks ready for execution by /execute-task. Use when: (1) converting a PRD document into executable engineering tasks, (2) planning feature delivery as a sequence of mergeable, self-contained pull requests, (3) the user says 'generate tasks', 'break down this PRD', 'create tasks from PRD', 'plan the implementation tasks', or 'task breakdown'. Each generated task document embeds its own success criteria, baseline checks, post-change tests, performance benchmarks, and non-functional requirements — making it directly executable by /execute-task."
argument-hint: "[prd-file-path | task-without-context | epic-task | big-task]"
---

<prd>
$ARGUMENTS
</prd>

<workflow>
Follow each phase in order.

<phase_1_read_prd>
Read the PRD document fully. Extract and organize:
- Functional requirements — numbered, atomic conditions
- Acceptance criteria — how feature completion is verified
- Non-functional requirements — performance, security, accessibility, scalability targets
- Scope — what is included and what is explicitly excluded
- User journeys — key flows and their steps
- Success metrics and KPIs
</phase_1_read_prd>

<phase_2_analyze_codebase>
Before decomposing tasks, understand the target project:
1. Read CLAUDE.md and root package.json — project structure, package manager, tech stack, key directories.
2. Identify where implementation units live — backend routes, frontend pages, shared types, database schemas, tests.
3. Search for patterns similar to the feature being built — use Grep/Glob to find related files and establish co-location conventions.
4. List the domain areas the feature touches — database, API, shared, frontend, tests, config.
</phase_2_analyze_codebase>

<phase_3_identify_implementation_units>
Map every PRD requirement to concrete implementation units. An implementation unit is any atomic change: a new schema, a route, a component, a migration, a shared type, a test file, a config entry, an i18n key.

For each unit, identify:
- **File path** (exact, following codebase conventions)
- **Action**: create or modify
- **Domain**: database | api | shared | frontend | test | config | docs
- **Dependencies**: which other units must exist first

**Standard dependency ordering** (lower layers before higher):
1. Shared types, constants, i18n keys, env variables
2. Database migrations and schema updates
3. API routes, handlers, validation schemas
4. Shared hooks, utilities, helper functions
5. UI components (atoms → molecules → organisms)
6. Pages and routes composing components
7. Tests (unit, integration, E2E)
8. Config and infrastructure changes
9. Documentation updates

**Orphan-free rule** — every consumer of a resource must be in the same task as its producer OR in a later task that explicitly depends on the producer's task:
- New i18n key + every component using that key → same task (or key in TASK_N, component in TASK_M where M > N and TASK_M depends on TASK_N)
- New database column + migration that adds it → same task
- New shared type + every immediate consumer → same task
- New component + the page that renders it → same task (unless page is intentionally deferred to a later task)
</phase_3_identify_implementation_units>

<phase_4_group_into_tasks>
Group implementation units into tasks. Apply these rules in order:

**Rule 1 — 30-file limit**: a task may create or modify at most 30 files. If a natural group exceeds this, split on domain boundaries (data layer, API layer, UI layer, test layer).

**Rule 2 — Production-ready delivery**: every task, when merged in order, must leave the application in a runnable state — no broken imports, unresolved references, orphaned i18n keys, or missing migrations.

**Rule 3 — Forward dependency only**: if TASK_N requires output from TASK_M, then M < N. No task may depend on a later task.

**Rule 4 — Mergeable without breaking**: use feature flags, graceful degradation, or empty-state handling so earlier tasks don't expose incomplete UX to end users.

**Rule 5 — Clear value delivery**: each task must deliver a demonstrable increment — a working endpoint, a rendered component, a passing test suite. Avoid tasks with no visible or testable outcome.

**Recommended grouping** (adapt per feature):
1. **Foundation** — shared types, constants, i18n keys, env variables
2. **Data layer** — database schema, migrations, ORM models
3. **API layer** — routes, handlers, validation schemas, error codes
4. **Core UI** — reusable components, hooks, state management
5. **Feature pages** — pages and routes composing the core UI
6. **Tests & polish** — comprehensive test suites, accessibility audit, performance tuning
7. **Documentation** — CLAUDE.md updates, API docs, migration guides

Split tasks at domain boundaries when a group would exceed 30 files.
</phase_4_group_into_tasks>

<phase_5_define_verification_criteria>
For each task, derive its verification criteria from the PRD. These become binding requirements embedded in the task document and executed by /execute-task.

**Success criteria** — select PRD acceptance criteria that apply to this task's scope. Write them as testable assertions:
- "POST /api/resource returns 201 with the created resource payload" (not "API works")
- "Page renders the empty state at 1440px without console errors" (not "page looks right")
- "Migration runs cleanly on an empty database" (not "migration works")

**Baseline checks** — what to capture BEFORE making changes:
- Standard quality gates: tsc, lint, test, build (pass/fail and counts)
- Domain-specific: API endpoints (HTTP status + timing), pages (screenshot + LCP), schema state (table columns and types)

**Post-change checks** — what to verify AFTER changes, mapped 1:1 to each success criterion.

**Performance benchmarks** — from PRD NFRs or domain defaults:
- API endpoints: p95 response time target
- Frontend pages: LCP target, bundle size delta
- Database queries: execution time target

**Non-functional requirements** — scope PRD NFRs to this task's domain:
- Database task → data integrity, migration rollback safety, index strategy
- API task → input validation coverage, auth guard presence, rate limiting
- Frontend task → WCAG compliance level, responsive breakpoints, keyboard navigation
</phase_5_define_verification_criteria>

<phase_6_generate_task_documents>
Generate a document for each task using the template from [template.md](template.md).

Before saving, validate each document:
- [ ] File count ≤ 30
- [ ] No file path appears in more than one task
- [ ] Every success criterion is testable (specific, measurable outcome)
- [ ] Every "create" file has its consumer in the same or a later task
- [ ] Task N's dependencies all have numbers < N
- [ ] Baseline checks include at minimum: tsc, lint, test, build

Fix any violation before saving.
</phase_6_generate_task_documents>
</workflow>

<output>
Save each task document to:
```
[project-root]/docs/features/[FEATURE_NAME]/TASK_[TASK_NUMBER].md
```

After saving all tasks, print a summary table:

| Task | Title | Files | Depends on | Key deliverable |
|------|-------|-------|------------|-----------------|
| TASK_01 | ... | N files | none | ... |
| TASK_02 | ... | N files | TASK_01 | ... |
</output>
