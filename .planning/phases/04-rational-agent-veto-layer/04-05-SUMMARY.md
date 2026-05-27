---
phase: 04-rational-agent-veto-layer
plan: 05
subsystem: cli-repl
tags: [python, repl, agent, compare, veto, tdd, sph]

# Dependency graph
requires:
  - phase: 04-02
    provides: wrap_with_agent closure factory
  - phase: 04-03
    provides: format_human comparison branch + format_compare renderer
provides:
  - SPHShell.do_run wraps strategy in wrap_with_agent (D-58 agent default-on in REPL)
  - SPHShell.do_compare — 7th command: 2x SPHSimulator, delta KPI table, verdict (D-61, AGENT-05)
  - do_help updated with compare line
  - Module + class docstrings updated to 7 commands
affects:
  - 04-06-PLAN (full test suite — REPL compare integration coverage)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "do_compare parallelizes do_run: same dispatch, parse, env params — differs only in 2x simulator build + comparison dict assembly"
    - "wrap_with_agent default-on in REPL run: params.get('expected_P', DEFAULT_K0) as agent param source (D-54)"
    - "format_human dispatcher: res_combined = {'comparison': ...} triggers format_compare early return (Plan 03)"
    - "fake_args.no_agent=False: defensive compatibility with format_json (T-04-20)"

key-files:
  created:
    - tests/test_repl_agent_task1.py
    - tests/test_repl_agent_task2.py
  modified:
    - sphsim/cli/repl.py

key-decisions:
  - "do_run: STRATEGIES[name] captured as raw_strategy_fn then wrapped — preserves original for potential future use; wrapped fn passed to SPHSimulator"
  - "do_compare: seed=42 hardcoded for both runs (identical to do_run) — deterministic comparison across sessions (Claude's Discretion per 04-CONTEXT.md)"
  - "comparison dict assembled inline in do_compare (not delegated to helper) — same pattern as main.py run_compare; REPL-specific env params (DEFAULT_*) differ from CLI args"
  - "TDD: RED commits separate per task, GREEN combined implementation per task"

requirements-completed: [AGENT-01, AGENT-05]

# Metrics
duration: ~10min
completed: 2026-05-27
---

# Phase 4 Plan 05: REPL wrap_with_agent + do_compare command — Summary

**SPHShell extended to 7 commands: do_run now wraps every strategy in wrap_with_agent (agent default-on per D-58), new do_compare runs simulator twice to render delta KPI table with Polish verdict (D-61, AGENT-05)**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-05-27T19:30:00Z
- **Completed:** 2026-05-27T19:40:00Z
- **Tasks:** 2 (TDD: RED + GREEN each)
- **Files created:** 2 test files
- **Files modified:** 1 (sphsim/cli/repl.py)

## Accomplishments

- `sphsim/cli/repl.py` modified with:
  - New import: `from sphsim.agent import wrap_with_agent`
  - Module docstring updated: "7 komend bez prefiksu '/'" + compare bullet
  - Class docstring updated: "7 komend bez slasha"
  - `do_run` wraps strategy: `strategy_fn = wrap_with_agent(STRATEGIES[name], params.get('expected_P', DEFAULT_K0))` before SPHSimulator build (D-58 agent default-on)
  - `fake_args` in `do_run` gains `no_agent=False` (defensive T-04-20 mitigation)
  - `do_help` adds: `compare <nazwa> [k=v ...] — Porównaj strategię z i bez RationalAgent (delta KPI).`
  - New `do_compare(self, arg)` method (~50 lines): validates input, dispatches D-50 namespace, runs 2x SPHSimulator (same seed=42), builds comparison dict, renders via format_human dispatcher
- 113 tests passing (79 pre-plan, +18 new + 16 from concurrent plan 04-04 wave)

## Task Commits

TDD: RED test commits followed by GREEN implementation commits.

1. **Task 1 RED: failing tests for do_run wrap + do_help + docstring** - `7987556` (test)
2. **Task 1 GREEN: do_run wrap + do_help compare + docstring bump** - `844f9a5` (feat)
3. **Task 2 RED: failing tests for do_compare** - `3a56d43` (test)
4. **Task 2 GREEN: do_compare — 2x SPHSimulator + delta render** - `a9b15a0` (feat)

## Files Created/Modified

- `sphsim/cli/repl.py` (MODIFIED) — wrap_with_agent import + do_run wrap + fake_args.no_agent + do_help compare line + do_compare method + docstring bump
- `tests/test_repl_agent_task1.py` (NEW) — 7 tests: 5 source assertions + 2 behavioral (help shows compare, run no crash)
- `tests/test_repl_agent_task2.py` (NEW) — 11 tests: 7 source assertions + 4 behavioral (no-args, unknown, incentive delta, custom)

## Decisions Made

- `do_compare` does not delegate to a separate helper function — the full logic is inline (~50 lines), consistent with `do_run` inline pattern. Avoids creating a private helper that would only be used once.
- `params.get('expected_P', DEFAULT_K0)` as `expected_P` for both `do_run` wrap and `do_compare` wrap — D-54 single source of truth for agent's `expected_P` in REPL context (no `args.expected_P` flag available in REPL).
- Both simulation runs in `do_compare` use `seed=42` (hardcoded, identical to `do_run`) — deterministic comparison across REPL sessions.
- `raw_strategy_fn = STRATEGIES[name]` named variable preserves clarity: `sim_with` uses `wrap_with_agent(raw_strategy_fn, ...)`, `sim_without` uses `raw_strategy_fn` directly.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — `do_compare` fully implements 2x simulation + delta KPI + verdict rendering. No placeholder values or TODO markers.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes. REPL handles user string input through existing `parse_params_from_meta` validation layer (T-04-17 mitigation).

## Self-Check: PASSED

- `sphsim/cli/repl.py` has `from sphsim.agent import wrap_with_agent`: YES
- `sphsim/cli/repl.py` has `wrap_with_agent(STRATEGIES[name]`: YES
- `sphsim/cli/repl.py` has `def do_compare`: YES
- `sphsim/cli/repl.py` has `compare <nazwa>` in do_help: YES
- `sphsim/cli/repl.py` has `no_agent=False` in fake_args: YES
- `sphsim/cli/repl.py` has `7 komend` in docstring: YES
- `sphsim/cli/repl.py` has `sim_with = SPHSimulator`: YES
- `sphsim/cli/repl.py` has `sim_without = SPHSimulator`: YES
- `sphsim/cli/repl.py` has `'comparison'` key: YES
- `sphsim/cli/repl.py` has `agent_helps`: YES
- `sphsim/cli/repl.py` has `wrap_with_agent(raw_strategy_fn`: YES
- Commit `7987556` (Task 1 RED) in git log: YES
- Commit `844f9a5` (Task 1 GREEN) in git log: YES
- Commit `3a56d43` (Task 2 RED) in git log: YES
- Commit `a9b15a0` (Task 2 GREEN) in git log: YES
- 113 tests passing: YES
- Task 1 verify (help+run): OK
- Task 2 verify (4 inline tests): OK

---
*Phase: 04-rational-agent-veto-layer*
*Completed: 2026-05-27*
