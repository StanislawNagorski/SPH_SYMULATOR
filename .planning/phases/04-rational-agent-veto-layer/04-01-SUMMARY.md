---
phase: 04-rational-agent-veto-layer
plan: 01
subsystem: core-model
tags: [python, dataclass, simulator, veto, agent, sph]

# Dependency graph
requires:
  - phase: 03-custom-strategy-loader
    provides: SPHSimulator with strategy_fn interface + Device dataclass (4 counters)
provides:
  - Device with n_vetoed: int = 0 counter (6th field) and veto_phase_stats dict
  - SPHSimulator.run() with 3-state decision branch (COMMIT|VETO|ABSTAIN) and veto_per_phase + n_vetoed_total in return dict
affects:
  - 04-02-PLAN (RationalAgent wrapper — uses n_vetoed + veto_phase_stats + 'VETO' signal)
  - 04-03-PLAN (output formatters — uses veto_per_phase + n_vetoed_total)
  - 04-06-PLAN (regression_check.py — uses veto_per_phase/n_vetoed_total in JSON)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "3-state decision string enum: COMMIT | VETO | ABSTAIN (elif chain in simulator)"
    - "Per-phase veto aggregation parallel to ic_per_phase (paste-and-modify loop over dev.veto_phase_stats.items())"
    - "Counter field in __post_init__ dict (not field(default_factory=dict)) — consistent with phase_stats pattern"

key-files:
  created:
    - tests/test_device_veto.py
    - tests/test_simulator_veto.py
  modified:
    - sphsim/core/device.py
    - sphsim/core/simulator.py

key-decisions:
  - "D-63: n_vetoed is a proper dataclass field (int=0), veto_phase_stats initialized in __post_init__ as per-instance dict — avoids shared mutable default (T-04-01)"
  - "D-65: VETO branch sets status=DOWN + down_left=1 without n_abstain++ — wrapper increments n_vetoed before returning 'VETO'"
  - "D-64: veto_per_phase aggregated after ic_per_phase loop, both keys always present in return dict (empty dict / 0 when no agent)"
  - "D-67: veto_per_phase and n_vetoed_total added to return dict BEFORE 'history' to preserve history/devices-last convention; existing keys untouched"

patterns-established:
  - "VETO-as-string: wrapper returns 'VETO' string; simulator elif-dispatches it identically to ABSTAIN mechanics but with separate counter"
  - "Always-present new keys: veto_per_phase={} and n_vetoed_total=0 even without agent — JSON parsers can rely on consistent schema"

requirements-completed: [AGENT-04]

# Metrics
duration: 4min
completed: 2026-05-27
---

# Phase 4 Plan 01: Device + Simulator 3-state veto interface — Summary

**Device dataclass extended with n_vetoed counter + veto_phase_stats dict; SPHSimulator.run() gains COMMIT|VETO|ABSTAIN dispatch and veto_per_phase/n_vetoed_total in return dict**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-27T19:09:45Z
- **Completed:** 2026-05-27T19:13:38Z
- **Tasks:** 2
- **Files modified:** 2 source + 2 new test files

## Accomplishments

- Device dataclass has 6th counter field `n_vetoed: int = 0` and `veto_phase_stats = {}` per-instance dict — Plan 02 wrapper can mutate them directly
- SPHSimulator.run() has 3-state decision guard: COMMIT (unchanged), VETO (DOWN without n_abstain++), ABSTAIN-or-default (unchanged)
- simulator.run() return dict always contains `veto_per_phase: {}` and `n_vetoed_total: 0` even without agent — schema stability for downstream formatters
- 41 tests passing (up from 21 pre-phase) — test_strategy_meta_consistency and test_loader remain green

## Task Commits

Each task was committed atomically (TDD: RED → GREEN):

1. **Task 1 RED: Device failing tests** - `5227cd4` (test)
2. **Task 1 GREEN: Device n_vetoed + veto_phase_stats** - `14258fe` (feat)
3. **Task 2 RED: Simulator failing tests** - `de023b9` (test)
4. **Task 2 GREEN: Simulator VETO branch + aggregation** - `c5a1872` (feat)

_TDD: each task has RED commit (failing tests) followed by GREEN commit (implementation)_

## Files Created/Modified

- `sphsim/core/device.py` - Added `n_vetoed: int = 0` field after `n_failed`; added `self.veto_phase_stats = {}` in `__post_init__`
- `sphsim/core/simulator.py` - Changed `else:` to `elif decision == 'VETO':` + new `else:`; added veto_per_phase aggregation loop; added 2 new keys to return dict
- `tests/test_device_veto.py` - 8 unit tests for Device veto fields (TDD RED for Task 1)
- `tests/test_simulator_veto.py` - 11 unit tests for Simulator VETO branch and aggregation (TDD RED for Task 2)

## Decisions Made

- Followed plan exactly per D-63/D-64/D-65 — no implementation choices required beyond what was specified
- `veto_phase_stats` initialized in `__post_init__` (not `field(default_factory=dict)`) to match existing `phase_stats` pattern and avoid shared mutable default (T-04-01 mitigation)
- VETO aggregation inserted after ic_results block and before return, matching parallel structure in PATTERNS.md §4

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation was straightforward paste-and-modify of existing patterns.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02 (RationalAgent wrapper) can immediately use `dev.n_vetoed` and `dev.veto_phase_stats[ph]` mutation pattern
- Plan 02 can return `'VETO'` from wrapper and simulator will handle it correctly
- Plan 03 (output formatters) has `veto_per_phase` and `n_vetoed_total` available in every `simulator.run()` result
- Plan 06 (regression_check.py) needs to add `--no-agent` flag — new keys will appear in JSON output (both are `{}` / `0` without agent)

## Self-Check: PASSED

- All 5 expected files exist (test_device_veto.py, test_simulator_veto.py, device.py, simulator.py, SUMMARY.md)
- All 4 task commits verified in git log (5227cd4, 14258fe, de023b9, c5a1872)
- 41 tests passing (unittest discover tests)

---
*Phase: 04-rational-agent-veto-layer*
*Completed: 2026-05-27*
