---
phase: 04-rational-agent-veto-layer
plan: 02
subsystem: agent-module
tags: [python, closure, agent, veto, tdd, sph]

# Dependency graph
requires:
  - phase: 04-rational-agent-veto-layer
    plan: 01
    provides: Device.n_vetoed + Device.veto_phase_stats + Simulator VETO branch
provides:
  - sphsim.agent package (sphsim/agent/__init__.py + sphsim/agent/rational.py)
  - wrap_with_agent(strategy_fn, expected_P) -> Callable — closure factory with E[zysk] formula
affects:
  - 04-03-PLAN (CLI main.py/repl.py — imports wrap_with_agent to wrap strategies)
  - 04-05-PLAN (REPL compare command — uses wrap_with_agent)
  - 04-06-PLAN (tests/test_agent.py full suite — Plan 06 extends these tests)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Closure-based pure wrapper: wrap_with_agent returns inner 'wrapped' function with same 8-arg signature"
    - "Verbatim E[zysk] formula from incentive.py:12-17 (D-53 — copy not re-derive)"
    - "Guard-first pattern: phi[idx]>=1.0 or idx>=len(phi) checked before computing total_h (D-57)"
    - "expected_P=None fallback to DEFAULT_K0 (mirror incentive.py:15 style)"

key-files:
  created:
    - sphsim/agent/__init__.py
    - sphsim/agent/rational.py
    - tests/test_agent_init.py
    - tests/test_agent_rational.py
  modified: []

key-decisions:
  - "Closure over class: wrap_with_agent returns pure closure (no class __call__) — stateless per D-57 threat model T-04-05"
  - "expected_P=None default in factory signature with immediate DEFAULT_K0 assignment — mirrors incentive.py:15 exp_P = float(p.get('expected_P', DEFAULT_K0))"
  - "Task 1 and Task 2 GREEN committed together since __init__.py requires rational.py to import from — TDD RED was isolated for __init__.py tests"
  - "22 behavior tests written for rational.py (10 cases from plan + 12 additional sub-cases for thorough coverage)"

# Metrics
duration: 8min
completed: 2026-05-27
---

# Phase 4 Plan 02: sphsim.agent package — wrap_with_agent closure factory — Summary

**sphsim/agent package created with wrap_with_agent closure factory implementing E[zysk] = (1-phi_i)*p_i - kappa - phi_i*rho_i verbatim from incentive.py, with VETO override when net < 0 (AGENT-02)**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-27T19:15:00Z
- **Completed:** 2026-05-27T19:23:00Z
- **Tasks:** 2 (TDD with RED + GREEN commits)
- **Files created:** 4 (2 source + 2 test)

## Accomplishments

- `sphsim/agent/__init__.py` created: Polish docstring, `from sphsim.agent.rational import wrap_with_agent`, `__all__ = ['wrap_with_agent']`
- `sphsim/agent/rational.py` created: `wrap_with_agent(strategy_fn, expected_P=None)` closure factory with:
  - ABSTAIN passthrough (zero E[zysk] computation — D-56 idempotency)
  - Guard D-57: `phi[idx] >= 1.0` or `idx >= len(phi)` → VETO (with n_vetoed++ + veto_phase_stats update)
  - D-55 fallback: `total_h <= 0` → `total_h = 1.0` (no crash on first cycle)
  - E[zysk] formula verbatim from incentive.py:12-17: `net = (1-phi[idx]) * exp_pay - kappa - phi[idx]*rho[idx]`
  - AGENT-02: `net < 0` → VETO (literal threshold, not `<= 0`)
  - `DEFAULT_K0` import from config for `expected_P=None` fallback
- 67 total tests passing (up from 41 pre-plan)
- D-56 idempotency verified: strategy_incentive + wrap_with_agent with same expected_P → n_vetoed == 0

## Task Commits

TDD: RED test commit followed by GREEN implementation commit for Task 1, then test commit for Task 2:

1. **Task 1 RED: failing tests for sphsim.agent package init** - `3af2127` (test)
2. **Task 1+2 GREEN: sphsim/agent package with wrap_with_agent factory** - `7e5c9a9` (feat)
3. **Task 2 tests: full behavior test suite for rational.py** - `d6fde9d` (test)

_Task 1 and Task 2 GREEN were committed together because `sphsim/agent/__init__.py` imports from `sphsim/agent/rational.py` — both files must exist simultaneously for the import to succeed._

## Files Created/Modified

- `sphsim/agent/__init__.py` (NEW) — Package init: Polish docstring, exports wrap_with_agent, __all__
- `sphsim/agent/rational.py` (NEW) — wrap_with_agent closure factory: 8-arg wrapped closure, E[zysk] formula, guards, mutations, DEFAULT_K0 fallback
- `tests/test_agent_init.py` (NEW) — 4 tests for package import, callable check, __all__, docstring
- `tests/test_agent_rational.py` (NEW) — 22 tests covering all 10 behavior cases from plan

## Decisions Made

- Pure closure (no class): `wrap_with_agent` returns an inner `def wrapped(...)` function, not a class instance. Stateless between calls — only captured `expected_P` (immutable float) and `strategy_fn` (callable) per T-04-05 threat mitigation.
- `expected_P=None` default in factory signature with immediate `if expected_P is None: expected_P = DEFAULT_K0` assignment — mirrors incentive.py style and makes the fallback explicit.
- Verbatim formula copy from incentive.py:12-17 (not re-derived) — single mathematical source of truth (D-53/D-54). Divergence: threshold is `net < 0` (agent) vs `net > 0` (incentive strategy).
- `dev.veto_phase_stats.get(dev.phase, 0) + 1` pattern (not defaultdict) — consistent with existing `phase_stats` dict access pattern in simulator.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — `wrap_with_agent` is fully implemented with all guards and mutations. No placeholder values or TODO markers.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes introduced. The closure is purely computational (stdlib only, no I/O).

## Self-Check: PASSED

- `sphsim/agent/__init__.py` exists: YES
- `sphsim/agent/rational.py` exists: YES
- `tests/test_agent_init.py` exists: YES
- `tests/test_agent_rational.py` exists: YES
- Commit `3af2127` (RED) in git log: YES
- Commit `7e5c9a9` (GREEN) in git log: YES
- Commit `d6fde9d` (tests) in git log: YES
- 67 tests passing (`python3 -m unittest discover tests`): YES
- `from sphsim.agent import wrap_with_agent` exits 0: YES
- D-56 idempotency test passes: YES

---
*Phase: 04-rational-agent-veto-layer*
*Completed: 2026-05-27*
