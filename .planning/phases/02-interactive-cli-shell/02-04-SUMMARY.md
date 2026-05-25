---
phase: 02-interactive-cli-shell
plan: 04
subsystem: tests-invariants
tags: [tests, invariant, D-25, STRAT-02, stdlib-only]
requirements_completed:
  - STRAT-02
dependency_graph:
  requires:
    - "Plan 02-01 (STRATEGY_META in 5 strategy modules)"
    - "Plan 02-02 (--interactive | --strategy mutex group)"
  provides:
    - "Automated test that fails on any future argparse↔STRATEGY_META drift"
    - "tests/ package with __init__.py marker (foundation for any future test files)"
  affects:
    - "scripts/regression_check.py (unaffected — Phase 1 8/8 still PASS)"
tech_stack:
  added: []
  patterns:
    - "Monkey-patch ArgumentParser.parse_args to capture parser instance (Option C from plan <interfaces>)"
    - "sys.path bootstrap at module top for dual-mode execution (unittest discovery + direct script)"
    - "Tuple unpack with len-check for clearer diagnostics on malformed STRATEGY_META"
key_files:
  created:
    - tests/__init__.py
    - tests/test_strategy_meta_consistency.py
  modified: []
decisions:
  - "Used Option C from plan <interfaces>: monkey-patch ArgumentParser.parse_args + controlled sys.argv = ['x', '--strategy', 'naive'] to satisfy mutex"
  - "Added sys.path bootstrap (sys.path.insert at project root) so test runs via both `python -m unittest ...` AND `python tests/test_strategy_meta_consistency.py` per acceptance criteria"
  - "Stdlib-only (D-18 constraint): unittest, importlib, argparse, sys, os, unittest.mock.patch — zero new dependencies"
  - "Single test method asserting all 15 contract points (5 strategies × {dest, type, default}) in one pass — failures produce per-strategy/per-param diagnostic messages"
metrics:
  duration_seconds: 163
  completed: "2026-05-25T17:52:00Z"
  tasks_total: 1
  tasks_completed: 1
  files_created: 2
  files_modified: 0
  commits: 1
---

# Phase 2 Plan 4: STRATEGY_META ↔ argparse Invariant Test Summary

**One-liner:** Codified D-25 as a stdlib-unittest test in `tests/test_strategy_meta_consistency.py` that captures the live `ArgumentParser` via monkey-patch and asserts every `STRATEGY_META['params']` tuple matches its argparse counterpart on name, type, and default — turning the previously aspirational invariant into a red/green signal.

## What Was Built

Two files created under `tests/`:

1. **`tests/__init__.py`** — empty marker so `tests/` is treated as a package by both `pytest` and `python -m unittest`. Required for the `tests.test_strategy_meta_consistency` dotted module path to resolve.

2. **`tests/test_strategy_meta_consistency.py`** — single-file stdlib unittest test:
   - Module-level `_capture_parser()` helper using Option C from the plan's `<interfaces>` section:
     1. Save the original `argparse.ArgumentParser.parse_args` method.
     2. `patch.object(ArgumentParser, 'parse_args', capture)` where `capture` stashes `self` into a dict, then calls the original.
     3. Substitute `sys.argv = ['x', '--strategy', 'naive']` so the mutex group from Plan 02 doesn't raise.
     4. Call `from sphsim.cli.args import parse_args; parse_args()` inside the `with patch(...)` block.
     5. Return the captured `ArgumentParser` instance for `_actions` introspection.
   - Class `TestStrategyMetaConsistency(unittest.TestCase)` with one method:
     `test_strategy_meta_matches_argparse(self)`. For each strategy in
     `STRATEGIES.keys()`:
     - `importlib.import_module(f'sphsim.strategies.{name}')`, assert it has `STRATEGY_META` dict with a `'params'` list.
     - For each `(pname, ptype, pdefault, pdesc)` tuple in `params`:
       - `assertIn(pname, actions_by_dest)` → catches missing-in-argparse.
       - `assertIs(action.type, ptype)` → catches type-mismatch (identity check on the type callable).
       - `assertEqual(action.default, pdefault)` → catches default-mismatch.
       - `assertIsInstance(pdesc, str)` → STRATEGY_META hygiene (description must be string).
   - Diagnostic messages match the formats specified in the plan `<interfaces>` block (e.g. `naive/zeta: STRATEGY_META default=0.6, argparse default=0.5`).
   - `if __name__ == '__main__': unittest.main()` for direct execution.

A `sys.path` bootstrap (`os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))`) at module top ensures direct script execution works (without it, `python tests/test_strategy_meta_consistency.py` only has `tests/` on `sys.path` and `import sphsim` fails with `ModuleNotFoundError`). This was a Rule 3 auto-fix during execution — see Deviations.

## Verification Results

| Check | Result |
|-------|--------|
| `test -f tests/__init__.py` | PASS (empty file, 0 bytes) |
| `test -f tests/test_strategy_meta_consistency.py` | PASS |
| `grep -c 'class TestStrategyMetaConsistency'` | 1 |
| `grep -c '^import unittest'` | 1 |
| `grep -c 'import pytest'` (expect 0) | 0 |
| `grep -c 'STRATEGY_META'` | 17 |
| `grep -c 'parse_args\|_actions'` | 11 |
| `python3 -m unittest tests.test_strategy_meta_consistency -v` | exit 0, `OK` |
| `python3 tests/test_strategy_meta_consistency.py` | exit 0, `OK` |
| `python3 scripts/regression_check.py` | exit 0, `PASS: 8/8` |

### Assertions exercised

Per Phase 2 state (Plan 01 + Plan 02), the test exercises **20 assertions** across 5 strategies:
- 5 × dest membership (`assertIn`) — name match between STRATEGY_META and argparse.
- 5 × type identity (`assertIs`) — type callable identity (e.g. `float is float`).
- 5 × default equality (`assertEqual`) — default value equality.
- 5 × description string check (`assertIsInstance`) — hygiene.

(Plan called for "15 assertions" counting only the 3 core invariant checks per strategy; the 4th per-strategy `assertIsInstance` for description type is hygiene-only and out-of-scope of D-25 but is cheap and useful for clearer failures if anyone breaks the tuple shape — see Deviations Rule 2 below.)

### Sanity-check (optional verification, performed and reverted)

To confirm the test would catch a real D-25 violation, I temporarily mutated `sphsim/strategies/naive.py` STRATEGY_META `zeta` default `0.5 → 0.6`. The test failed with the exact diagnostic message specified in the plan:

```
AssertionError: 0.5 != 0.6 : naive/zeta: STRATEGY_META default=0.6, argparse default=0.5
```

Source was reverted; final state has `0.5` (matches argparse). The test correctly distinguishes between "missing-in-argparse" (assertIn), "type-mismatch" (assertIs), and "default-mismatch" (assertEqual) error classes.

## Decisions Made

- **Option C from plan `<interfaces>`** (monkey-patch + controlled `sys.argv`) chosen over Option A (re-build parser inline — duplicates contract) and Option B (capture parser via mock side_effect — same idea but cleaner with `patch.object` context manager). Zero changes to production code.
- **Stdlib only** (D-18 constraint extended to tests, per plan must_haves): `unittest`, `importlib`, `argparse`, `sys`, `os`, `unittest.mock.patch`. No pytest imports.
- **Module-level `_capture_parser()` helper** (not a class method) — keeps the monkey-patch logic separate from the assertion logic, makes the test method body focus on the invariant.
- **`assertIs` for type** (identity, not equality) per plan `<interfaces>`: type callable must be the very same object (`float`, not "looks like float"). This is the right check because argparse stores the type callable verbatim.
- **`sys.argv = ['x', '--strategy', 'naive']`** — chose `naive` as the canonical "valid mutex member" because it is the baseline strategy (PROJECT.md / v1.0). Any of the 5 strategies would work; `naive` is the most universally meaningful pick.
- **Polish docstring + English code identifiers** per project convention (CONTEXT.md `<code_context>` Established Patterns).
- **Single test method** rather than `subTest` per-strategy or one method per strategy. Reasoning: D-25 is one invariant; a single failure should not mask other failures (Python unittest reports the first assertion failure per test method, but in practice a single param mutation produces one failure with a clear message naming the strategy and field). For future scalability (Phase 3 custom loader would add strategies dynamically), `subTest` could be added then — YAGNI now (D-33).

## Deviations from Plan

### Rule 3 - Blocking Issue: sys.path bootstrap for direct execution

**Found during:** Task 1 verification (`python tests/test_strategy_meta_consistency.py` step).

**Issue:** Direct script execution failed with `ModuleNotFoundError: No module named 'sphsim'` because when run as `python tests/test_strategy_meta_consistency.py`, only `tests/` is on `sys.path` — not the project root. This blocked the plan's stated acceptance criterion "`python tests/test_strategy_meta_consistency.py` exits 0 (runnable directly via unittest.main())".

**Fix:** Added a 4-line `sys.path` bootstrap at the top of `tests/test_strategy_meta_consistency.py`:
```python
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
```
This is a no-op when run via `python -m unittest ...` from the project root (root already on `sys.path`), and is the canonical idiom for self-contained test scripts. Pure stdlib — no new imports beyond `os` (which is stdlib).

**Files modified:** `tests/test_strategy_meta_consistency.py` (added 4 lines + 1 import).
**Commit:** Folded into the single Task 1 commit (`ff6ff22`).

### Rule 2 - Missing Critical Hygiene: description type check

**Found during:** Writing the test body — realized that if someone breaks the tuple shape (e.g., changes `('zeta', float, 0.5, 'desc')` to `('zeta', float, 0.5)` — 3-tuple — or to `('zeta', float, 0.5, None)`), the existing 3 assertions would not catch the description regression and would only fail later when `do_strategy` in the REPL (Plan 03) tries to use the description.

**Fix:** Added `len(tup) == 4` assertion (with explicit error message naming the bad tuple) and `assertIsInstance(pdesc, str)` per param. This catches malformed STRATEGY_META at test time rather than runtime in the REPL. Strict invariant per D-25 (which specifies the 4-tuple shape).

**Files modified:** `tests/test_strategy_meta_consistency.py` (~6 lines).
**Commit:** Folded into Task 1 commit (`ff6ff22`).

## Auth Gates

None.

## Known Stubs

None. The test exercises real STRATEGY_META data and real argparse setup. No mocks, no placeholders, no TODOs.

## Threat Flags

None. The test introduces no new network endpoints, no file I/O at trust boundaries, no schema changes. `unittest.mock.patch` is used as a context manager scoped to a single function call (`parse_args()`) and the patch is unwound automatically; `sys.argv` is saved and restored in a `try/finally`. The monkey-patch surface is narrow and stdlib-only.

## Requirements Closed

- **STRAT-02** (szczegóły strategii: parametry + baseline KPI) — second-layer protection now in place. Plan 03 surfaces STRATEGY_META data to the user via `strategy <name>` REPL command; Plan 04 (this) guarantees the data shown reflects the real argparse contract. Any future drift between `STRATEGY_META['params']` and `add_argument` calls produces a red test before reaching the user.

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | test(02-04): codify D-25 invariant — STRATEGY_META ↔ argparse consistency | `ff6ff22` |

## Self-Check: PASSED

- FOUND: tests/__init__.py (empty package marker, 0 bytes)
- FOUND: tests/test_strategy_meta_consistency.py (~172 lines, single TestCase, stdlib-only)
- FOUND: commit `ff6ff22` in worktree branch git log (`git log --oneline | head -3`)
- VERIFIED: `python3 -m unittest tests.test_strategy_meta_consistency` exit 0 (OK)
- VERIFIED: `python3 tests/test_strategy_meta_consistency.py` exit 0 (OK, runs `unittest.main()`)
- VERIFIED: `python3 scripts/regression_check.py` exit 0 (PASS: 8/8 — Phase 1 regression untouched)
- VERIFIED: sanity-check mutation `0.5 → 0.6` produced the expected diagnostic failure message, then was reverted; final source matches `(name, type, default, description) = ('zeta', float, 0.5, 'Frakcja COMMIT (0..1)')`
