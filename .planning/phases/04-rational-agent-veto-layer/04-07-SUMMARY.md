---
phase: 04-rational-agent-veto-layer
plan: "07"
subsystem: testing
tags: [bash, exit-gate, verify-script, phase4, rational-agent, veto-layer, regression, sc-verification]

# Dependency graph
requires:
  - phase: 04-rational-agent-veto-layer
    provides: "wrap_with_agent closure (Plans 01-05) + tests/test_agent.py + regression_check SKIP_KEYS (Plan 06) — all 5 ROADMAP SC implemented"

provides:
  - "scripts/verify_phase4.sh — Phase 4 exit gate, 21 checks, exit 0 on PASS=21/FAIL=0"
  - "Empirical verification of SC #5: agent_helps==True for naive --zeta 0.95 (not incentive per D-56 idempotent caveat)"
  - "Single re-runnable pre-flight oracle for Phase 4 merge readiness"

affects:
  - "any future verify-work flow consuming scripts/verify_phase4.sh"
  - "05-configurable-environment (picks up from Phase 4 complete state)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Mirror verify_phase3.sh structure: shebang + set -euo pipefail + cd $(dirname $0)/.. + PY detection + trap cleanup + PASS/FAIL counters + check() helper"
    - "grep > /dev/null (not grep -q) for SIGPIPE/pipefail safety (D-52 carry-forward)"
    - "{ cmd || true; } | grep pattern for argparse error commands (exit code 2 passthrough)"
    - "json.loads with raw.find('{') for multi-line banner+JSON output (--custom + --compare-agent)"
    - "tail -n +2 to skip [OSTRZEŻENIE] banner when parsing JSON from --custom runs"
    - "SC #5 uses naive --zeta 0.95 (NOT incentive --expected_P 30) per D-56 idempotent caveat"

key-files:
  created:
    - scripts/verify_phase4.sh
  modified: []

key-decisions:
  - "SC #5 demo scenario: naive --zeta 0.95 --compare-agent (not incentive --expected_P 30) — per D-56 incentive wrapper is no-op/idempotent (n_vetoed==0, delta≈0), naive high-COMMIT-rate guarantees veto candidates when E[zysk]<0"
  - "JSON path d['metrics']['agent_enabled'] (not top-level) — normal runs wrap metrics under 'metrics' key; compare runs use top-level 'comparison' key"
  - "21 checks across 10 sections: regression + test suite + SC#1-5 + mutex + REPL + custom"

patterns-established:
  - "verify_phase4.sh section numbering: ── N. Tytuł ── (10 sections) mirrors verify_phase3.sh"
  - "Phase exit gate pattern: bash script exits 0 iff PASS count >= N and FAIL == 0"

requirements-completed: [AGENT-01, AGENT-02, AGENT-03, AGENT-04, AGENT-05]

# Metrics
duration: 5min
completed: 2026-05-27
---

# Phase 4 Plan 07: Phase Exit Gate Summary

**Bash exit gate scripts/verify_phase4.sh with 21 checks across 10 sections verifying all 5 ROADMAP SC + regression + test suite — exits 0 PASS=21/FAIL=0**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-05-27T19:52:03Z
- **Completed:** 2026-05-27T19:57:15Z
- **Tasks:** 1
- **Files modified:** 1 created

## Accomplishments

- Created `scripts/verify_phase4.sh` (192 lines, 21 `check()` invocations, 27 `SC #` comments) mirroring `verify_phase3.sh` structure exactly
- All 21 checks PASS=21/FAIL=0 on first run — Phase 4 empirically verified green
- SC #5 uses `naive --zeta 0.95` (high COMMIT-rate strategy) as demo, not `incentive --expected_P 30` (D-56 idempotent caveat documented in script header)

## Task Commits

1. **Task 1: scripts/verify_phase4.sh — Phase 4 exit gate (21 checks)** - `be6579b` (feat)

## Files Created/Modified

- `scripts/verify_phase4.sh` (192 lines) — 10 sections: (1) regression 8/8, (2) test suite 123+, (3) SC#1 default-wrap, (4) SC#2 --no-agent, (5) SC#3 veto_per_phase JSON+human, (6) SC#4 --compare-agent JSON+human+REPL, (7) SC#5 empirical agent_helps==True, (8) mutex enforcement D-60, (9) REPL 7th command compare, (10) custom strategy D-58 integration

## Decisions Made

- **SC #5 demo scenario**: `naive --zeta 0.95` instead of `incentive --expected_P 30` — Plan CONTEXT.md mentioned incentive as demo but D-56 documents incentive wrapper is idempotent (n_vetoed≈0 because incentive and agent use identical formula). WRN-03 in plan's read_first corrects this. Script is authoritative over CONTEXT.md. Verified: delta avg_net_profit = +196.83 for naive --zeta 0.95, agent_helps==True.
- **JSON path**: `d['metrics']['agent_enabled']` (not top-level `d['agent_enabled']`) — normal runs wrap everything under `metrics`, compare runs use top-level `comparison`. Script uses both correctly based on mode.
- **`tail -n +2` for custom**: `--custom` produces `[OSTRZEŻENIE]` banner on line 1 before JSON; used `tail -n +2` to skip it when piping to Python JSON parser.
- **`raw.find('{')` approach for SC#5**: Used the plan's suggested assertion pattern with `raw.find('{')` to handle any leading text before the JSON brace.

## Deviations from Plan

None — plan executed exactly as written. The plan's `read_first` already documented the SC#5 correction (WRN-03: use `naive --zeta 0.95` not `incentive --expected_P 30`). Implementation followed this guidance precisely.

## Issues Encountered

- None. All checks passed on first run. The careful pre-research of JSON structure and the correct SC#5 demo scenario ensured no iteration was needed.

## Known Stubs

None — all 21 checks perform real subprocess invocations and behavioral assertions.

## Threat Flags

None — verify_phase4.sh is read-only (no file writes), all subprocess commands use literal string arguments (no user-input interpolation), T-04-24/T-04-25/T-04-26 mitigations from plan's threat model are implemented.

## Self-Check

- `test -f scripts/verify_phase4.sh` → FOUND
- `test -x scripts/verify_phase4.sh` → FOUND (executable bit set)
- Commit be6579b exists → FOUND
- `bash scripts/verify_phase4.sh` → PASS=21/FAIL=0 exit 0

## Self-Check: PASSED

## Next Phase Readiness

- Phase 4 is complete and verified — all 5 ROADMAP SC for `04-rational-agent-veto-layer` green
- `scripts/verify_phase4.sh` is the single pre-flight oracle for any future merge of Phase 4 changes
- Phase 5 (configurable environment) can proceed — no blocking concerns

---
*Phase: 04-rational-agent-veto-layer*
*Completed: 2026-05-27*
