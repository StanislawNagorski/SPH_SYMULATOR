---
phase: 02-interactive-cli-shell
plan: 01
subsystem: strategies-metadata
tags: [strategies, metadata, D-24, D-25, D-26, STRAT-01, STRAT-02]
requires:
  - Phase 1 (sphsim/strategies/*.py — refactored modules)
provides:
  - STRATEGY_META top-level constant in 5 strategy modules
  - Single source of truth for description, params, baseline_kpi
  - Foundation for Plan 03 (REPL `strategies`/`strategy <name>`) and Plan 04 (invariant test)
affects:
  - sphsim/strategies/naive.py
  - sphsim/strategies/threshold.py
  - sphsim/strategies/phase_prob.py
  - sphsim/strategies/incentive.py
  - sphsim/strategies/adaptive.py
tech-stack:
  added: []
  patterns:
    - "Metadata-near-code: STRATEGY_META lives next to strategy_<name> in the same module"
    - "Tuple-of-4 params (name, type, default, description) mirroring argparse"
key-files:
  created: []
  modified:
    - sphsim/strategies/naive.py
    - sphsim/strategies/threshold.py
    - sphsim/strategies/phase_prob.py
    - sphsim/strategies/incentive.py
    - sphsim/strategies/adaptive.py
decisions:
  - "Applied D-24 verbatim: STRATEGY_META dict with exactly 3 keys (description, params, baseline_kpi)"
  - "Applied D-25 verbatim: params as list of 4-tuples (name, type, default, description) with real Python type objects"
  - "Applied D-26 verbatim: only naive has baseline_kpi populated (avg_val_last100 = 92.0 float); other 4 = None"
  - "Strategy functions kept untouched — STRATEGY_META added as second top-level export"
metrics:
  duration_seconds: 116
  completed_date: "2026-05-25"
  tasks_completed: 1
  files_modified: 5
  commits: 1
---

# Phase 2 Plan 1: Strategy Metadata (STRATEGY_META) Summary

**One-liner:** Each of the 5 built-in strategy modules now exports a `STRATEGY_META` dict (description + params tuples + baseline_kpi) matching the D-24/D-25/D-26 contract, with `naive` carrying the v1.0 baseline (`avg_val_last100 = 92.0`) and the other four set to `None`.

## What Was Built

A single top-level constant `STRATEGY_META` was added to each of the 5 strategy modules under `sphsim/strategies/`, placed immediately after the existing `strategy_<name>(...)` function. The strategy functions themselves were not modified — Phase 1 verbatim behavior is preserved (regression_check.py 8/8 PASS).

### Per-file content

| File | description | params | baseline_kpi |
|------|-------------|--------|--------------|
| naive.py | `'COMMIT z prawdopodobieństwem zeta'` | `[('zeta', float, 0.5, 'Frakcja COMMIT (0..1)')]` | `{'invocation': 'naive --zeta 0.75', 'avg_val_last100': 92.0, 'source': 'PROJECT.md / v1.0 results'}` |
| threshold.py | `'COMMIT tylko dla faz <= max_phase'` | `[('max_phase', int, 3, 'Max faza COMMIT')]` | `None` |
| phase_prob.py | `'COMMIT z P(commitów) per faza'` | `[('probs', str, '0.9,0.7,0.5,0.3,0.0', 'P(COMMIT) per faza, po przecinku')]` | `None` |
| incentive.py | `'COMMIT gdy E[zysk_netto] > 0'` | `[('expected_P', float, 100.0, 'Oczek. płatność')]` | `None` |
| adaptive.py | `'COMMIT zależnie od poziomu bufora SUS'` | `[('s_target', int, 10, 'Próg SUS')]` | `None` |

`description` values match D-29 verbatim (single source of truth for the future REPL `strategies` table). `params` tuples mirror argparse defaults in `sphsim/cli/args.py:41-46` exactly (D-25 invariant — to be codified by Plan 04 automated test).

## Verification

All inline `python -c` assertions from `<acceptance_criteria>` were executed and passed:

- 5 of 5 files contain exactly one `STRATEGY_META = {` line each (grep count = 1 per file).
- `set(M.keys()) == {'description', 'params', 'baseline_kpi'}` for every module.
- `naive.STRATEGY_META['baseline_kpi']['avg_val_last100']` is the float `92.0` and `isinstance(..., float)` is True.
- All 4 non-naive strategies have `baseline_kpi is None`.
- Every `params[0]` is a 4-tuple where `p[0]` is `str`, `p[1]` is `type`, `p[3]` is `str` (D-25 shape).
- `strategy_naive` import still works — function preserved.
- `python3 scripts/regression_check.py` exited 0 with `PASS: 8/8` — D-28 Phase 1 backwards compat preserved.

## Decisions Made

- Used D-24/D-25/D-26 verbatim (no Claude's-discretion deviation).
- Inserted `STRATEGY_META` after the strategy function (not before) so the file reads "function first, metadata sidecar" — consistent across all 5 files for symmetry.
- No new imports added; `float`, `int`, `str` are builtins (no `from typing import` needed).
- `sphsim/strategies/__init__.py` registry was NOT modified — registry still exports only `STRATEGIES` dict; `STRATEGY_META` is imported per-module by future REPL code via `importlib.import_module(f'sphsim.strategies.{name}')` as documented in 02-CONTEXT.md Integration Points.

## Deviations from Plan

None — plan executed exactly as written.

## Requirements Closed

- **STRAT-01** (lista strategii z opisem): description field in each STRATEGY_META is the single source of truth for the future `strategies` REPL command (Plan 03).
- **STRAT-02** (szczegóły strategii: parametry + baseline KPI): params + baseline_kpi fields in each STRATEGY_META are the single source of truth for the future `strategy <name>` REPL command (Plan 03).

Note: full UI surfacing of these requirements occurs in Plan 03 (REPL implementation). Plan 01 provides the data contract; Plan 03 consumes it.

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Add STRATEGY_META to 5 strategy files | `a92e731` |

## Self-Check: PASSED

- FOUND: sphsim/strategies/naive.py (modified, STRATEGY_META present, baseline_kpi populated)
- FOUND: sphsim/strategies/threshold.py (modified, STRATEGY_META present, baseline_kpi None)
- FOUND: sphsim/strategies/phase_prob.py (modified, STRATEGY_META present, baseline_kpi None)
- FOUND: sphsim/strategies/incentive.py (modified, STRATEGY_META present, baseline_kpi None)
- FOUND: sphsim/strategies/adaptive.py (modified, STRATEGY_META present, baseline_kpi None)
- FOUND: commit a92e731 in git log
- VERIFIED: `python3 scripts/regression_check.py` exits 0, PASS 8/8
