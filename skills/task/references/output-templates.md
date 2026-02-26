# Output Templates

## Role completion report

Each role (whether a dispatched subagent or a single-role execution) produces this report:

```
Summary: one sentence of what was done.
Files: list each file path created/modified/deleted.
Skills loaded: list each Skill() call made during execution.
MCPs used: list each MCP called, or "none".
Quality gates: pass/fail for each gate (tsc, lint, test, build).
```

## Final orchestrator report (MULTI-ROLE only)

When all roles are complete and all quality gates pass:

```
## Task complete

Summary: one sentence describing the overall outcome.

### Roles executed
| Role | Sub-area | Agent type | Ad-hoc? | Status | Summary |
|------|----------|-----------|---------|--------|---------|
| [role name] | [sub-area] | [subagent_type] | yes/no | pass/fail | [one-line summary] |

### Aggregated files
List every file created/modified/deleted across all roles.

### Quality gates (final)
- tsc: pass/fail (per package)
- lint: pass/fail (per package)
- test: pass/fail (count)
- build: pass/fail (per package)

### Task-defined test results
If the task document defined tests, report results here:
| Test | Baseline (before) | Result (after) | Delta |
|------|-------------------|----------------|-------|
| [test name] | [baseline value] | [post-change value] | [improvement or regression] |

If no task-defined tests existed, omit this section.

### Skills loaded
List every skill called across all roles.

### MCPs used
List every MCP called across all roles, or "none".
```

In SINGLE-ROLE mode, skip the "Roles executed" table — use the role completion report format directly.
