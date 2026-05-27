---
phase: 04-rational-agent-veto-layer
plan: 04
subsystem: cli-integration
tags: [python, cli, argparse, agent, wrap_with_agent, run_compare, tdd, sph]

# Dependency graph
requires:
  - phase: 04-rational-agent-veto-layer
    plan: 02
    provides: wrap_with_agent(strategy_fn, expected_P) closure factory
  - phase: 04-rational-agent-veto-layer
    plan: 03
    provides: format_human comparison branch + format_compare + format_json with comparison dispatch
provides:
  - sphsim/cli/args.py with --no-agent + --compare-agent flags and post-parse mutex enforcement
  - sphsim/cli/main.py with wrap_with_agent integration (both branches) + run_compare function
  - run_compare(args, raw_strategy_fn, name, params, K1) -> dict with 'comparison' block
affects:
  - 04-05-PLAN (repl.py do_compare — uses same raw_strategy_fn pattern)
  - 04-06-PLAN (regression_check.py — now needs --no-agent in each invocation)
  - 04-07-PLAN (final integration tests — SC #1-5 all reachable via --compare-agent)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Snapshot raw_strategy_fn BEFORE any wrap (T-04-13 mitigation): raw_strategy_fn = strategy_fn BEFORE if not args.no_agent"
    - "Compare branch early-return in main() BEFORE conditional wrap step — guards against double-wrap in compare path"
    - "run_compare: 2x SPHSimulator with identical seed (deterministic comparison, Claude's Discretion D-Claude's-Discretion)"
    - "args.compare_agent + early-return pattern: dispatch to run_compare then format and return — no fall-through to single-run path"
    - "post-parse mutex via p.error() (argparse hard error, exit 2) — Polish messages per PROJECT.md constraint"

key-files:
  created:
    - tests/test_args_agent_flags.py
    - tests/test_main_agent_integration.py
  modified:
    - sphsim/cli/args.py
    - sphsim/cli/main.py

key-decisions:
  - "6-step linear execution sequence in main() (a-f): parse → resolve strategy → snapshot raw → compare branch (early-return) → conditional wrap → build+run — order is load-bearing, not interchangeable"
  - "wrap_with_agent imported at module top (not inside conditionals) — cleaner import, no ImportError risk at runtime"
  - "run_compare placed as top-level function ABOVE main() — callable from tests without invoking main(); also allows future reuse by repl.py"
  - "Both --custom and built-in branches share the same (c)→(d)→(e)→(f) logic — no divergence between branches for agent wrap"
  - "T=200 in unit test for run_compare (not default T=2000) — faster tests without sacrificing coverage of 5 KPI keys"

patterns-established:
  - "Raw strategy snapshot pattern: capture before wrap, pass to run_compare — prevents double-wrap in compare path"
  - "args.no_agent / args.compare_agent boolean flag check pattern in main() branches"

requirements-completed: [AGENT-01, AGENT-03, AGENT-05]

# Metrics
duration: 15min
completed: 2026-05-27
---

# Phase 4 Plan 04: CLI Integration — --no-agent + --compare-agent + run_compare — Summary

**argparse extended with --no-agent + --compare-agent flags (post-parse Polish mutex), main.py restructured with raw-strategy snapshot + wrap_with_agent default-on + run_compare (2x SPHSimulator, 5 KPI delta) for --compare-agent mode**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-27T19:16:00Z
- **Completed:** 2026-05-27T19:31:56Z
- **Tasks:** 2 (both TDD with RED + GREEN commits)
- **Files modified:** 2 source + 2 test files created

## Accomplishments

- `sphsim/cli/args.py` extended with `--no-agent` (store_true, default False, outside mutex, D-58) and `--compare-agent` (store_true, default False, outside mutex, D-60) flags, with post-parse hard mutex checks via `p.error()` (Polish messages, exit 2), and `--expected_P` help text updated to `[incentive|agent]` (D-54)
- `sphsim/cli/main.py` restructured with 6-step linear sequence: raw strategy snapshot before wrap → compare early-return → conditional `wrap_with_agent` → standard single-run — both `--custom` and built-in branches follow identical logic
- New `run_compare(args, raw_strategy_fn, name, params, K1)` function: runs 2x SPHSimulator with same seed (deterministic), computes 5-KPI delta, returns `{'comparison': {'with_agent': {...}, 'without_agent': {...}, 'delta': {...}, 'agent_helps': bool}}`
- T-04-13 mitigated: `raw_strategy_fn` snapshot captured before any wrap call — `run_compare` always receives the pure strategy, preventing double-wrap in compare path
- 113 tests passing (was 79 before plan, +34 new: 9 for args flags + 7 for main integration + 18 from plan 05 which ran in parallel wave)

## Task Commits

Both tasks used TDD: RED (failing tests) → GREEN (implementation).

Task 1: sphsim/cli/args.py
1. **Task 1 RED — failing tests for args flags** - `d4f42cf` (test)
2. **Task 1 GREEN — --no-agent + --compare-agent + mutex** - `6ff6687` (feat)

Task 2: sphsim/cli/main.py
3. **Task 2 RED — failing tests for main wrap + run_compare** - `71a1394` (test)
4. **Task 2 GREEN — wrap integration + run_compare** - `f9790bc` (feat)

## Files Created/Modified

- `sphsim/cli/args.py` — Added: `--no-agent` flag, `--compare-agent` flag (both store_true outside mutex group), post-parse mutex checks with `p.error()` (Polish error messages), updated `--expected_P` help text
- `sphsim/cli/main.py` — Added: `from sphsim.agent import wrap_with_agent` top-level import; new `run_compare` function; restructured `main()` with 6-step linear sequence replacing the old 2-branch structure
- `tests/test_args_agent_flags.py` (NEW) — 9 tests: flag recognition, default values, mutex exit-2 checks, help text content
- `tests/test_main_agent_integration.py` (NEW) — 7 tests: 5 subprocess integration tests + 2 unit tests for run_compare (existence + comparison block structure)

## Decisions Made

- 6-step linear sequence (a-f) in main() chosen over per-branch inline wrapping — eliminates double-wrap risk in compare path (T-04-13), makes the execution order explicit and auditable
- `run_compare` at module level (not inside main) — testable in isolation without subprocess, importable by repl.py (plan 05) if needed
- TDD RED committed separately from GREEN for traceability — each RED tests EXACTLY the missing behavior (3 failures + 1 import error for Task 2)
- Identical wrap logic applied to both `--custom` and built-in branches — no code divergence (D-58 applies equally to both)

## Deviations from Plan

None — plan executed exactly as written. The 6-step sequence from the `<action>` block was followed verbatim. No Rule 1/2/3 triggers.

## Known Stubs

None — `run_compare` fully implemented with live data from SPHSimulator.run(); `wrap_with_agent` comes from plan 02 with full E[zysk] formula. No placeholder values.

## Threat Flags

None — no new network endpoints, auth paths, or file access patterns introduced. CLI-only changes, stdlib only.

## Self-Check: PASSED

- `sphsim/cli/args.py` exists with --no-agent and --compare-agent: YES
- `sphsim/cli/main.py` exists with run_compare function: YES
- `tests/test_args_agent_flags.py` exists (9 tests): YES
- `tests/test_main_agent_integration.py` exists (7 tests): YES
- Commit `d4f42cf` (RED Task 1) in git log: YES
- Commit `6ff6687` (GREEN Task 1) in git log: YES
- Commit `71a1394` (RED Task 2) in git log: YES
- Commit `f9790bc` (GREEN Task 2) in git log: YES
- 113 tests passing (`python3 -m unittest discover tests`): YES
- `--compare-agent --json` gives top-level 'comparison' key: YES
- `--no-agent --json` gives `agent_enabled: false, n_vetoed_total: 0`: YES
- `--custom` without `--no-agent` gives `agent_enabled: true`: YES

---
*Phase: 04-rational-agent-veto-layer*
*Completed: 2026-05-27*
