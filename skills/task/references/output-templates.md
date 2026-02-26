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

### Verification results (baseline vs post-change)
| Check | Baseline (before) | Result (after) | Delta | Status |
|-------|-------------------|----------------|-------|--------|
| lint | [pass/fail] | [pass/fail] | — | [ok/regression] |
| build | [pass/fail (size)] | [pass/fail (size)] | [delta] | [ok/improved/regression] |
| tests | [count] | [count] | [delta] | [ok/improved/regression] |
| [domain-specific check] | [baseline value] | [post-change value] | [delta] | [ok/improved/regression] |

Include every check from the verification plan. This section is always present.

### Skills loaded
List every skill called across all roles.

### MCPs used
List every MCP called across all roles, or "none".
```

In SINGLE-ROLE mode, skip the "Roles executed" table — use the role completion report format directly.
