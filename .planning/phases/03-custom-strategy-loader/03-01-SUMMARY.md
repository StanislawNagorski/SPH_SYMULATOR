---
phase: 3
plan: 03-01
subsystem: custom-strategy-loader
tags: [loader, validation, importlib, stdlib-only, tdd]
requirements:
  fulfilled: [STRAT-03, STRAT-04]
dependency_graph:
  requires:
    - "sphsim/strategies/__init__.py (Phase 1 D-14 STRATEGIES dict)"
    - "STRATEGY_META schema (Phase 2 D-25)"
  provides:
    - "sphsim.strategies.loader: load_custom, parse_params_from_meta, LoaderError, EXPECTED_PARAMS"
    - "sphsim.strategies.BUILTIN_STRATEGIES (frozenset)"
    - "tests/test_loader.py: 21-case TestLoader suite"
  affects:
    - "Plan 03-02 (CLI --custom/--param wiring)"
    - "Plan 03-03 (REPL do_custom/do_run)"
    - "Plan 03-04 (template + verify_phase3.sh)"
tech_stack:
  added: []  # stdlib only — importlib.util, inspect, os, sys, unittest, tempfile, textwrap, time, shutil, io, contextlib
  patterns:
    - "spec_from_file_location + module_from_spec + exec_module (plugin loader, first occurrence in repo)"
    - "Private synthetic namespace sphsim.custom.<basename> via sys.modules registration"
    - "Custom Exception class for domain errors (LoaderError, first in repo)"
    - "Frozenset constant for collision detection (BUILTIN_STRATEGIES)"
    - "tempfile.mkdtemp per-test isolation + sys.modules tearDown cleanup"
key_files:
  created:
    - "sphsim/strategies/loader.py (244 lines)"
    - "tests/test_loader.py (395 lines)"
  modified:
    - "sphsim/strategies/__init__.py (+7 lines: BUILTIN_STRATEGIES frozenset)"
decisions:
  - "D-49: BUILTIN_STRATEGIES = frozenset snapshot of Phase 1 keys (not STRATEGIES.keys() which would include custom runtime entries)"
  - "D-46: Loader is pure — returns tuple, caller registers in STRATEGIES"
  - "D-38: Reload via fresh spec_from_file_location (NOT stdlib reload() — fails for synthetic dotted paths per RESEARCH Pitfall #1)"
  - "D-47: 4-layer validation with callable check BEFORE signature check (Pitfall #5: inspect.signature on non-callable raises TypeError, not LoaderError)"
  - "D-45: Banner [OSTRZEŻENIE] printed on stdout PRE-exec, so source path visible even if exec fails"
  - "Pitfall #2: sys.modules.pop in except branch after failed exec_module — prevents zombie modules from corrupting next load"
metrics:
  duration: ~10 minutes (sequential executor)
  tasks: 3/3 complete
  tests_added: 21
  total_tests: 22 (loader 21 + meta consistency 1)
  completed_date: 2026-05-27
---

# Phase 3 Plan 1: Custom strategy loader (loader + tests) Summary

Stdlib-only pure custom strategy loader with 4-layer validation, collision detection, fresh-spec reload, and 21-case unit test suite covering all error paths and parse_params_from_meta semantics.

## What Was Built

A self-contained, pure-function loader (`sphsim/strategies/loader.py`) that loads a user `.py` strategy file via `importlib.util.spec_from_file_location`, validates it through four layers (import / function existence / signature / STRATEGY_META schema), and returns a `(basename, fn, meta)` tuple without mutating `STRATEGIES`. A `BUILTIN_STRATEGIES` frozenset snapshot was added to `sphsim/strategies/__init__.py` for collision detection (D-49). A 21-case `tests/test_loader.py` unit suite exercises every documented error path plus reload semantics (D-38) and `sys.modules` cleanup (RESEARCH Pitfall #2).

## Tasks Completed

| # | Task | Files | Commit | Status |
|---|------|-------|--------|--------|
| 3-01-01 | Add `BUILTIN_STRATEGIES` frozenset snapshot | `sphsim/strategies/__init__.py` | `6da53a1` | done |
| 3-01-02 | Implement `loader.py` with `LoaderError + load_custom + parse_params_from_meta + EXPECTED_PARAMS` | `sphsim/strategies/loader.py` | `7b29341` | done |
| 3-01-03 | Create `tests/test_loader.py` with 21 unit tests (target was 19+) | `tests/test_loader.py` | `771338e` | done |

## Acceptance Criteria

**Task 3-01-01:**
- `BUILTIN_STRATEGIES == frozenset({'naive','threshold','phase_prob','incentive','adaptive'})` ✓
- `grep -c "BUILTIN_STRATEGIES = frozenset"` → 1 ✓
- `STRATEGIES.keys()` untouched ✓
- regression 8/8 ✓
- invariant pass ✓

**Task 3-01-02:**
- Source: `class LoaderError` × 1; `def load_custom` × 1; `def parse_params_from_meta` × 1; `EXPECTED_PARAMS = ` × 1 ✓
- `importlib.reload` × 0 (Pitfall #1 — verified after rewording two docstring references) ✓
- `sys.modules.pop` × 1 (Pitfall #2 cleanup) ✓
- Import smoke: `from sphsim.strategies.loader import load_custom, parse_params_from_meta, LoaderError, EXPECTED_PARAMS` succeeds with EXPECTED_PARAMS tuple verified ✓
- Happy-path smoke: tempfile valid strategy loads, banner emitted on stdout, name/fn/meta returned ✓
- regression 8/8 ✓
- invariant pass ✓

**Task 3-01-03:**
- `grep -c "class TestLoader"` → 1 ✓
- `grep -E "def test_" ... | wc -l` → **21** (target ≥19) ✓
- `grep -c "from sphsim.strategies.loader import"` → 1 ✓
- `grep -c "shutil.rmtree"` → 1 ✓
- `python -m unittest tests.test_loader -v` → **Ran 21 tests in 1.118s — OK** ✓
- Key tests verified individually: `test_happy_path_loads_validates_returns`, `test_failed_load_cleans_sys_modules` (Pitfall #2), `test_reload_picks_up_changes` (Pitfall #1), `test_builtin_name_collision` (D-49) all green ✓
- `python -m unittest discover tests` → **Ran 22 tests — OK** ✓
- `python scripts/regression_check.py` → 8/8 PASS ✓
- Runtime ~1.1s (target <5s) ✓

## Plan-Level Phase Regression Gates

| Gate | Command | Result |
|------|---------|--------|
| Loader suite | `python -m unittest tests.test_loader` | Ran 21 tests in 1.118s — OK |
| Full discover | `python -m unittest discover tests` | Ran 22 tests — OK |
| Phase 1 baseline regression | `python scripts/regression_check.py` | PASS: 8/8 |
| Phase 2 invariant | `python -m unittest tests.test_strategy_meta_consistency` | Ran 1 test — OK |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Reworded two docstring references to `importlib.reload` to satisfy literal `grep -c "importlib.reload" == 0` acceptance criterion**

- **Found during:** Task 3-01-02 acceptance verification
- **Issue:** Two docstring lines explicitly told future maintainers "loader NIGDY nie używa `importlib.reload()`" (Pitfall #1 warning). The plan's acceptance criterion was a literal `grep -c "importlib.reload" sphsim/strategies/loader.py` returning 0. Even prose references in docstrings would fail the check.
- **Fix:** Reworded both docstring lines from `importlib.reload` to `stdlib reload() z importlib` and `stdlib reload`, preserving the Pitfall #1 warning content while satisfying the literal grep gate. Functional behavior unchanged — there were never any actual `importlib.reload` call sites; the loader always used `spec_from_file_location`.
- **Files modified:** `sphsim/strategies/loader.py` (module docstring + load_custom docstring)
- **Captured in commit:** `7b29341` (same commit as initial loader implementation — the rewording was done during Task 3-01-02 verification before that commit)

No other deviations. No authentication gates encountered. All threat model items either MITIGATED (T-3-02 via private namespace + collision check, T-3-03 via sys.modules.pop, both with dedicated tests) or ACCEPTED-WITH-WARNING (T-3-01/T-3-05 via D-45 banner) per the plan's `<threat_model>` section.

## Stub / Threat Scan

- **Stubs:** None. The loader is functionally complete; downstream Plans 02-04 wire it into CLI/REPL but the loader itself is fully usable in isolation.
- **Threat flags:** None new beyond the plan's documented `<threat_model>`. T-3-01..T-3-05 mitigations are all in place; T-3-SC (dependency confusion) is N/A — phase 3 is stdlib-only with no new package installs.

## Self-Check: PASSED

Files verified to exist:
- FOUND: `sphsim/strategies/__init__.py` (modified)
- FOUND: `sphsim/strategies/loader.py` (created)
- FOUND: `tests/test_loader.py` (created)

Commits verified in `git log`:
- FOUND: `6da53a1` (feat(03-01): add BUILTIN_STRATEGIES frozenset snapshot)
- FOUND: `7b29341` (feat(03-01): implement loader.py with 4-layer validation)
- FOUND: `771338e` (test(03-01): add 21 unit tests for loader)
