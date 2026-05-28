---
phase: 07-batch-runner-aggregation
plan: 01
subsystem: batch-stats
tags: [wave-1, BATCH-02, aggregate_kpis, scipy-t-interval, dataclass, tdd-green]
requires:
  - "07-00 (test stubs + requirements.txt — provides 5 skip-stubs in tests/test_batch_stats.py)"
provides:
  - "sphsim/batch/ sub-package (public surface: aggregate_kpis, AggregateStat, KPIS)"
  - "sphsim.batch.stats.aggregate_kpis (pure-function math kernel for BATCH-02)"
  - "sphsim.batch.stats.AggregateStat (dataclass — mean/std/min/max/ci_lower/ci_upper/n + ci_str() helper)"
  - "sphsim.batch.stats.KPIS (canonical 5-tuple, order-locked against markdown.py::_KPI_ROWS)"
affects: []
tech-stack:
  added:
    - "scipy.stats.t.interval (CI via t-Student dla df=n-1, RESEARCH §D.6/§D.7)"
    - "numpy.std(ddof=1) (sample std, NIE population)"
    - "dataclasses.dataclass + typing.Optional (consistent z sphsim/core/device.py pattern)"
  patterns:
    - "Sub-package layout mirroring sphsim/agent/__init__.py (PATTERNS §1 — module docstring + import + __all__)"
    - "@dataclass with Optional[float] fields for degenerate N=1 case (PATTERNS §2b)"
    - "assertAlmostEqual(places=4) for float comparisons (Pitfall 3, BLAS variance)"
    - "warnings.catch_warnings() + simplefilter('error') for runtime warning detection"
key-files:
  created:
    - "sphsim/batch/__init__.py (4 lines — sub-package entry, re-exports 3 symbols)"
    - "sphsim/batch/stats.py (140 lines — full BATCH-02 math kernel)"
  modified:
    - "tests/test_batch_stats.py (60 → 197 lines — 5 skip-stubs replaced by 9 GREEN tests)"
decisions:
  - "Zero-variance edge handling (Rule 1): when N≥2 but all values identical → sem=0 → scipy.stats.t.interval returns (NaN, NaN). Fix: collapse CI to point (mean, mean). Caught by TestStatsDeterminism (cum_val_total constant in fixture)."
  - "Plan hand-calc value std≈0.2953 was a typo; runtime ground truth is numpy.std(ddof=1) = 0.302765 for canonical 10-element sample. Tests assert ground truth, not plan typo."
  - "ci_str() returns 'n/a (N=k)' (not 'n/a (N=1)' hardcoded) — generalizes to any future degenerate path while still passing N=1 test verbatim."
metrics:
  tasks_completed: 2
  files_created: 2
  files_modified: 1
  tests_added: 9 (all GREEN — was 5 SKIPPED, now 9 PASS)
  baseline_test_delta: "184 → 188 total (+4 net), 12 → 7 SKIPPED (-5), 172 → 181 PASSED (+9)"
  commits:
    - "aa9c3ca feat(07-01): sphsim/batch/stats.py — aggregate_kpis (BATCH-02) + AggregateStat dataclass"
    - "6e5e7f7 test(07-01): green 9 tests for aggregate_kpis (BATCH-02) + zero-variance CI guard"
completed: 2026-05-28
---

# Phase 7 Plan 01: aggregate_kpis (BATCH-02) Statistical Aggregation Summary

Landed pure-function statistical aggregation kernel (`aggregate_kpis` + `AggregateStat` dataclass + `KPIS` canonical tuple) under `sphsim/batch/`; greened 9 test methods across 5 classes in `tests/test_batch_stats.py`; scipy.stats.t.interval drives 95% CI for N≥2, numpy.std(ddof=1) enforces sample-std semantics, N=1 and zero-variance edges guarded against NaN flooding.

## Files Created / Modified

| File                                    | Lines | Role                                                                                            |
| --------------------------------------- | ----- | ----------------------------------------------------------------------------------------------- |
| `sphsim/batch/__init__.py`              | 4     | NEW — sub-package entry, re-exports `aggregate_kpis`, `AggregateStat`, `KPIS` (3 symbols)       |
| `sphsim/batch/stats.py`                 | 140   | NEW — pure-function math kernel; KPIS tuple + AggregateStat dataclass + aggregate_kpis function |
| `tests/test_batch_stats.py`             | 197   | MOD — 5 skip-stubs replaced by 9 assertion-bearing tests (60 → 197 lines)                       |

## Public Surface of `sphsim.batch` (3 symbols, ready for Plan 07-03)

```python
from sphsim.batch import aggregate_kpis, AggregateStat, KPIS

# KPIS — canonical tuple, order-locked against markdown.py::_KPI_ROWS:
#   ('avg_val_last100', 'cum_val_total', 'avg_net_profit', 'delivery_ratio', 'avg_providers_l100')

# AggregateStat — dataclass with fields:
#   mean: float, std: float (ddof=1), min: float, max: float,
#   ci_lower: Optional[float], ci_upper: Optional[float], n: int
#   + ci_str(fmt='{:.2f}') -> str helper

# aggregate_kpis(per_seed_kpis: list[dict[str, float]]) -> dict[str, AggregateStat]
#   Raises ValueError dla N=0; returns 5-key dict (== KPIS) dla N≥1.
```

Plan 07-03 (Wave 2) will add `run_batch` to `__all__` — this plan deliberately leaves the re-export at 3 symbols.

## KPIS Order Confirmation

Runtime probe: `python -c "from sphsim.batch.stats import KPIS; from sphsim.report.markdown import _KPI_ROWS; assert KPIS == tuple(r[0] for r in _KPI_ROWS); print('OK')"` — **PASSES**.

The 5-tuple `('avg_val_last100', 'cum_val_total', 'avg_net_profit', 'delivery_ratio', 'avg_providers_l100')` matches `markdown.py::_KPI_ROWS` column 0 verbatim. Plan 07-04 (raport batch) can iterate `for kpi in KPIS:` without reordering.

## Test Count Delta

| Metric          | Before (after 07-00) | After (this plan) | Delta |
| --------------- | -------------------- | ----------------- | ----- |
| Total tests     | 184                  | 188               | +4    |
| PASSED          | 172                  | 181               | +9    |
| SKIPPED         | 12                   | 7                 | -5    |
| FAILED          | 0                    | 0                 | 0     |
| Phase 6 regression_check.py | PASS=8/8 | PASS=8/8 | unchanged |

Net contribution: +9 GREEN tests, -5 SKIPPED placeholders. Remaining 7 SKIPPED are intentional Wave 2/3/4 stubs (tests/test_batch.py × 5, tests/test_batch_report.py × 2).

## N=1 Edge — No RuntimeWarning

Manual probe (verbatim from plan §verification step 5):

```bash
python3 -W error -c "from sphsim.batch.stats import aggregate_kpis, KPIS; \
  r = aggregate_kpis([{k: 42.0 for k in KPIS}]); \
  assert r['avg_val_last100'].std == 0.0 and r['avg_val_last100'].ci_lower is None"
```

**Result: OK** — no exception raised under `-W error` (which converts all warnings to exceptions). The N=1 guard (line 106-112 of stats.py) fires BEFORE any call to `values.std(ddof=1)`, so numpy's RuntimeWarning never escapes.

`TestN1Degenerate.test_n1_no_warning` enforces this contract programmatically via `warnings.catch_warnings()` + `warnings.simplefilter('error')`.

## Deviations from Plan

### Rule 1 (Bug fix) — Zero-variance CI handling

**Found during:** Task 2 (TestStatsDeterminism)
**Issue:** When N≥2 but all per-seed values for a single KPI are identical, `values.std(ddof=1)` returns 0.0, so `sem = 0.0/sqrt(n) = 0.0`. Calling `scipy.stats.t.interval(0.95, df, loc=mean, scale=0.0)` returns `(NaN, NaN)`. Because `NaN != NaN`, the resulting `AggregateStat` dataclass fails equality comparison against an identical instance, breaking the determinism contract for any input where any KPI is constant across seeds (e.g., `cum_val_total=92000.0` for all 10 seeds in the canonical fixture).
**Fix:** Added explicit `if sem == 0.0:` branch (sphsim/batch/stats.py:116-122) that collapses CI to `(mean, mean)` — mathematically correct point interval for zero-variance sample, and equality-safe (no NaN). Plan threat model T-7-01-01 says stats is pure-transform; this fix preserves purity.
**Files modified:** `sphsim/batch/stats.py` (added 7 lines for the sem==0 branch + 2 lines docstring update)
**Commit:** `6e5e7f7`

### Rule 1 (Test data fix) — Plan hand-calc typo

**Found during:** Task 2 (TestAggregateKpis.test_known_values first run)
**Issue:** Plan §interfaces line 138 quotes "std (ddof=1) ≈ 0.302765..." (correct) BUT plan Task 2 §action line 295 instructs `self.assertAlmostEqual(result['avg_val_last100'].std, 0.2953, places=3)`. The two values are inconsistent. Runtime numpy.std(ddof=1) on the canonical 10-element sample returns 0.3027650354097502 — matching line 138's value, NOT line 295's assertion.
**Fix:** Test asserts `0.302765` (places=4) — the runtime ground truth, which also matches the plan's own §interfaces hand-calc.
**Files modified:** `tests/test_batch_stats.py` (3 lines: assertion + docstring + comment)
**Commit:** `6e5e7f7`

No Rule 2/3/4 deviations. No architectural changes. No CLAUDE.md violations.

## Threat Model Status

| Threat ID  | Disposition | Outcome                                                                                                                                  |
| ---------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| T-7-01-01  | accept      | aggregate_kpis is pure-function, in-memory list-comp over 5N floats. N=10^7 ≈ 400 MB worst case — large but not catastrophic. CLI parser (Plan 07-02) enforces upper bound. |
| T-7-01-02  | accept      | ValueError message is generic Polish ("pusta lista — nic do agregowania"), does not echo input shape or any data.                        |

Zero new threat flags discovered. Stats module remains a leaf node in dependency graph (no IO, no fork, no disk read/write, no remote calls).

## Authentication Gates

None — purely local module creation, no remote service interaction, no API keys, no auth flows.

## Known Stubs

None. All N=1 / N=0 paths return real values or raise proper exceptions; no `TODO`, `FIXME`, or `coming soon` markers in production code. The string `"placeholder"` in stats.py:111 is a comment fragment describing the design choice for N=1 std value (`std = 0.0` as a "sensowny placeholder" — not a code stub).

## Suggested Phase-Level Commit Message (for orchestrator metadata commit)

```
feat(07-01): sphsim/batch/stats.py — aggregate_kpis (BATCH-02) + AggregateStat dataclass + 9 GREEN tests
```

## TDD Gate Compliance

Plan 07-01 is `type: execute` (Wave 1, GREEN phase for BATCH-02). RED gate inherited from Plan 07-00 (`139aa20 test(07-00): scaffold Phase 7 stub containers` — landed before any GREEN commit in this plan).

GREEN gate sequence verified:
- RED (inherited): `139aa20 test(07-00): scaffold ...` — 5 skip-stubs for test_batch_stats.py
- GREEN (Task 1): `aa9c3ca feat(07-01): sphsim/batch/stats.py ...` — implementation lands
- GREEN (Task 2): `6e5e7f7 test(07-01): green 9 tests ...` — tests assert real behavior

No REFACTOR commit (none needed — Task 2 absorbed the zero-variance Rule 1 fix into the GREEN commit, keeping the cycle clean).

## Self-Check

- `[ -f sphsim/batch/__init__.py ]` → FOUND
- `[ -f sphsim/batch/stats.py ]` → FOUND
- `[ -f tests/test_batch_stats.py ]` → FOUND
- `git log | grep aa9c3ca` → FOUND (Task 1 commit)
- `git log | grep 6e5e7f7` → FOUND (Task 2 commit)
- `python3 -c "from sphsim.batch import aggregate_kpis, AggregateStat, KPIS"` → OK
- `python3 -m unittest tests.test_batch_stats` → Ran 9 tests, OK (0 SKIPPED, 0 FAILED)
- `python3 -m unittest discover tests/` → Ran 188 tests, OK (skipped=7)
- `python3 scripts/regression_check.py` → PASS=8/8
- KPIS == tuple(r[0] for r in _KPI_ROWS) → True

## Self-Check: PASSED
