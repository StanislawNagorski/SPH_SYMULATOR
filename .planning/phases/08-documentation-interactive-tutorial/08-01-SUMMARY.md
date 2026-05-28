---
phase: 08-documentation-interactive-tutorial
plan: 01
subsystem: report
tags: [report, tutorial, kwarg, backwards-compat, tdd, pathlib]

requires:
  - phase: 06-report-plots-generator
    provides: write_report orchestrator (REPORT-01..03) + _resolve_report_dir collision-retry
  - phase: 07-batch-runner
    provides: write_batch_report orchestrator (BATCH-03+PLOT-04) + aggregate_kpis
  - phase: 08-00
    provides: TestTutorialReports skeleton (TUT-06 stub) + verify_phase8.sh skeleton
provides:
  - write_report report_dir_override keyword-only kwarg (D-10)
  - write_batch_report report_dir_override keyword-only kwarg (D-10)
  - Override branch uses mkdir(parents=True, exist_ok=True) — tutorial retry-safe
  - Default branch (None) byte-identical to v1.1.7 — regression_check PASS=8/8 preserved
  - Pitfall 4 enforced: SPHSIM_NO_REPORT=1 wins over override (env-var check first)
affects:
  - 08-04 (plan 04 will thread TutorialFlow.step_report_dir through do_run/do_tutorial)

tech-stack:
  added: []
  patterns:
    - "D-10 override pattern: optional keyword-only kwarg, exist_ok=True on override branch, exist_ok=False on default branch"
    - "Pitfall 4 ordering: env-var opt-out check MUST precede any path-resolution logic"

key-files:
  created: []
  modified:
    - sphsim/report/__init__.py
    - tests/test_tutorial.py

key-decisions:
  - "report_dir_override is keyword-only (after *) — matches existing `mode=` convention; positional call raises TypeError"
  - "Override branch uses mkdir(parents=True, exist_ok=True) — tutorial caller can retry the same step without collision"
  - "Default branch (None) keeps _resolve_report_dir collision-retry (suffix -N) untouched — regression_check.py invariant preserved byte-for-byte"
  - "SPHSIM_NO_REPORT=1 check stays FIRST in both functions (Pitfall 4) — env-var opt-out wins over any override path; verified in tests"
  - "write_batch_report has INDEPENDENT mkdir block (does NOT call _resolve_report_dir); override bypass replicates the same pattern inline (Pitfall 5)"
  - "Original test_tutorial_reports_go_to_dedicated_dir subprocess test stays skipped — plan 08-04 owns the wiring"

patterns-established:
  - "D-10 override pattern: signature has keyword-only kwarg with None default; body checks kwarg presence right after env-var opt-out; override branch is exist_ok=True; default branch is unchanged"

requirements-completed:
  - TUT-06

duration: ~25min
completed: 2026-05-28
---

# Phase 8 Plan 01: write_report + write_batch_report `report_dir_override` Summary

**Added optional keyword-only `report_dir_override` to both report writers — enabling tutorial mode (plan 08-04) to land reports at `./reports/tutorial-<ts>/step-N-<topic>/` without polluting the default `./reports/<ts>/` namespace; default behavior byte-identical to v1.1.7 (regression_check PASS=8/8).**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-05-28T19:20:00Z (worktree spawn)
- **Completed:** 2026-05-28T17:28:16Z
- **Tasks:** 2 (both TDD: RED → GREEN)
- **Files modified:** 2

## Accomplishments

- `write_report` extended with `report_dir_override=None` keyword-only kwarg — override branch writes to caller-supplied path with `mkdir(parents=True, exist_ok=True)`; default branch unchanged.
- `write_batch_report` extended with the same kwarg — added `*` keyword-only marker (was missing); override branch identical semantics; inline batch_<ts>/ mkdir untouched in default branch (Pitfall 5).
- 7 new D-10 unit tests in `tests/test_tutorial.py::TestTutorialReports` (4 for `write_report`, 3 for `write_batch_report`) — all GREEN.
- Backwards-compat hard-locked: `regression_check.py` PASS=8/8 (8 baseline JSON fixtures still byte-identical for `--seed 42` across all 5 strategies).
- Full `python3 -m unittest discover tests` green: 221/221 OK (skipped=9 unchanged from baseline 9 — 1 still-skipped TUT-06 subprocess test for plan 08-04, 8 pre-existing scaffolding skips).

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1 RED — write_report report_dir_override test** — `a373c24` (test)
2. **Task 1 GREEN — write_report report_dir_override impl** — `639a0ec` (feat)
3. **Task 2 RED — write_batch_report report_dir_override test** — `f1b9ba2` (test)
4. **Task 2 GREEN — write_batch_report report_dir_override impl** — `0021d5b` (feat)

_Note: SUMMARY commit follows (docs)._

## Files Created/Modified

- `sphsim/report/__init__.py` — modified: both function signatures + module docstring + override-branch logic in both bodies (+52 / -21 single + +48 / -30 batch lines net).
- `tests/test_tutorial.py` — modified: imports (`tempfile`, `shutil`, `argparse`, `inspect`, `Path`), fixtures (`_make_args`, `_make_single_res`, `_make_per_seed_results`), 7 new D-10 tests in `TestTutorialReports` + setUp/tearDown (tempdir + SPHSIM_NO_REPORT pop pattern). Original `test_tutorial_reports_go_to_dedicated_dir` kept `@unittest.skip` pointing at plan 08-04 (subprocess wiring).

## Tests Added

### `tests/test_tutorial.py::TestTutorialReports`

| Test | Asserts |
|------|---------|
| `test_report_dir_override_creates_path_and_writes_files` | `write_report(..., report_dir_override=Path('reports/tutorial-test/step-1-baseline'))` returns that exact path; report.md + decision_distribution.png + kpi_timeseries.png exist there; no `./reports/<ts>/` sibling created |
| `test_report_dir_override_keyword_only` | `inspect.signature(write_report)['report_dir_override'].kind == KEYWORD_ONLY`; default is `None` |
| `test_report_dir_override_default_none_unchanged_behavior` | Default branch (no override kwarg) still writes to `./reports/<ts>/`; no "tutorial" leakage |
| `test_sphsim_no_report_wins_over_override` | `SPHSIM_NO_REPORT=1` + override → returns `None`, override path NOT created (Pitfall 4) |
| `test_batch_report_dir_override_creates_path_and_writes_files` | `write_batch_report(..., report_dir_override=Path('reports/tutorial-test/step-8-batch'))` returns that path; report.md + batch_aggregate.png exist; no `./reports/batch_<ts>/` sibling created |
| `test_batch_report_dir_override_keyword_only` | `inspect.signature(write_batch_report)['report_dir_override'].kind == KEYWORD_ONLY`; default `None` |
| `test_batch_sphsim_no_report_wins_over_override` | Batch env-var opt-out wins (Pitfall 4 batch version) |

## Verification Results

| Check | Command | Result |
|-------|---------|--------|
| write_report signature has keyword-only override | `inspect.signature(write_report).parameters['report_dir_override'].kind == KEYWORD_ONLY` | ✓ OK |
| write_batch_report signature has keyword-only override | `inspect.signature(write_batch_report).parameters['report_dir_override'].kind == KEYWORD_ONLY` | ✓ OK |
| `grep -c 'report_dir_override=None' sphsim/report/__init__.py` | — | 3 (≥1 required) |
| `grep -c 'if report_dir_override is not None:' sphsim/report/__init__.py` | — | 1 (now 2 — see note) |
| `grep -c 'report_dir.mkdir(parents=True, exist_ok=True)' sphsim/report/__init__.py` | — | 1 (now 2 — see note) |
| test_report regression | `SPHSIM_NO_REPORT=1 python3 -m unittest tests.test_report` | Ran 14 tests · OK |
| test_batch_report regression | `SPHSIM_NO_REPORT=1 python3 -m unittest tests.test_batch_report` | Ran 7 tests · OK |
| Full discover | `SPHSIM_NO_REPORT=1 python3 -m unittest discover tests` | Ran 221 tests · OK (skipped=9) |
| Backwards-compat byte-identical | `python3 scripts/regression_check.py` | **PASS: 8/8** |
| Original TUT-06 subprocess test still skipped | `python3 -m unittest -v tests.test_tutorial.TestTutorialReports.test_tutorial_reports_go_to_dedicated_dir` | skipped ('Wave 2 — plan 08-04 wires...') |

**Note on grep counts (`if report_dir_override is not None:` / `report_dir.mkdir(parents=True, exist_ok=True)`):** Plan AC specified "≥1"; actual count is 2 each (one occurrence in each of `write_report` + `write_batch_report` after Task 2 landed). Plan AC was written from Task 1's vantage-point only — Task 2 doubled the occurrences, which is the intended symmetric pattern. Both grep checks still pass the "≥1" threshold.

## SPHSIM_NO_REPORT=1 Opt-Out Precedence (Pitfall 4) — Confirmed

Both `write_report` and `write_batch_report` check `os.environ.get('SPHSIM_NO_REPORT') == '1'` and `return None` BEFORE evaluating `report_dir_override`. Two dedicated tests (`test_sphsim_no_report_wins_over_override` + `test_batch_sphsim_no_report_wins_over_override`) verify that passing an override path while the env-var is set yields `None` AND the override path is NOT created on disk. CI and `regression_check.py` (which set `SPHSIM_NO_REPORT=1` themselves) continue to suppress all report side-effects regardless of any future caller passing an override.

## TDD Gate Compliance

All 4 commits follow strict RED → GREEN ordering per task:

- Task 1: `a373c24` (test, RED) → `639a0ec` (feat, GREEN) ✓
- Task 2: `f1b9ba2` (test, RED) → `0021d5b` (feat, GREEN) ✓

No REFACTOR commits — implementation was minimal and clean on first GREEN pass. No fail-fast violation (RED commits demonstrably failed before GREEN landed; transcript captured TypeError on missing kwarg + AssertionError on missing signature entry).

## Deviations from Plan

**None — plan executed exactly as written.**

The single nuance worth noting (not a deviation): `write_batch_report` lacked a `*` keyword-only marker entirely (its 6 positional args ended at `seeds_list`). The plan explicitly anticipated this ("add the `*` keyword-only marker if not present; add the new kwarg after") so adding `*, report_dir_override=None` was on-plan. This preserves backwards-compat for the existing 1 internal caller (`sphsim/cli/main.py` + `sphsim/cli/repl.py` — both invoke `write_batch_report` with 6 positional args, no kwargs) — none of those callers needed modification.

## Known Stubs

**None.** Both kwargs are real implementations wired into the function body. The only remaining `@unittest.skip` in the modified scope is `test_tutorial_reports_go_to_dedicated_dir` (subprocess end-to-end TUT-06) which explicitly defers to plan 08-04 — that plan will flip the skip and wire `_tutorial_state` into `do_run`. This is by design per the plan's `<action>` block ("Keep the existing tests `test_tutorial_reports_go_to_dedicated_dir` as a placeholder ... for now; Plan 04 will flip it.").

## Threat Surface Scan

No new network endpoints, auth paths, or untrusted file access patterns introduced. `report_dir_override` is constructed by internal tutorial code (plan 08-03 will provide `TutorialFlow.step_report_dir`) from `timestamp + step_number + topic_slug` — not user input. Threat T-08-01-01 (path traversal) accepted in plan; threats T-08-01-02 (backwards-compat) and T-08-01-03 (DoS via opt-out bypass) mitigated and verified by tests + regression_check.

No new threat flags raised.

## Self-Check: PASSED

- ✓ `sphsim/report/__init__.py` exists and contains both signatures with `report_dir_override`
- ✓ `tests/test_tutorial.py` exists with 7 D-10 tests
- ✓ Commit `a373c24` (Task 1 RED) exists in git log
- ✓ Commit `639a0ec` (Task 1 GREEN) exists in git log
- ✓ Commit `f1b9ba2` (Task 2 RED) exists in git log
- ✓ Commit `0021d5b` (Task 2 GREEN) exists in git log
- ✓ Full test suite 221/221 OK
- ✓ regression_check.py PASS=8/8

## Next Steps (for plan 08-02 onward)

Plan 08-02 adds the `--tutorial` CLI flag (TUT-05 wiring half).
Plan 08-03 builds the `TutorialFlow` class with `step_report_dir(step_n, topic_slug) -> Path`.
Plan 08-04 threads `TutorialFlow.step_report_dir` through `do_run` / `do_tutorial` in `repl.py`, passing the result as `report_dir_override=...` to `write_report` / `write_batch_report` — at which point `test_tutorial_reports_go_to_dedicated_dir` flips from skip to GREEN.

This plan provides the SURGICAL minimum surface needed by 08-04: two kwargs, zero behavior change in any existing call site, no caller modifications.
