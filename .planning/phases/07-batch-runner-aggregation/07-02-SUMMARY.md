---
phase: 07-batch-runner-aggregation
plan: 02
subsystem: cli
tags: [argparse, batch, seeds, polish-errors, dos-prevention, tdd]

# Dependency graph
requires:
  - phase: 07-batch-runner-aggregation
    provides: "Plan 07-00 scaffolded `tests/test_batch.py` skip-stubs for TestSeedsParser + TestArgsMutex (12 tests greened here) and added the matplotlib/numpy/scipy requirements pin."
provides:
  - "`sphsim.cli.args._parse_seeds_list(s) -> list[int]` module-level converter (grammar v1, RESEARCH §B.3)"
  - "`sphsim.cli.args.MAX_SEEDS = 1000` DoS cap constant (T-7-02-01)"
  - "`--batch` (store_true) + `--seeds` (type=_parse_seeds_list) argparse flags on sph_sim.py"
  - "4 post-parse mutex `p.error` checks (Polish-only — NO English fallback): batch+compare, batch+interactive, batch-without-seeds, seeds-without-batch"
  - "Plan 07-05 (REPL) can `from sphsim.cli.args import _parse_seeds_list` to share grammar — single source of truth"
  - "Plan 07-03 (run_batch orchestrator) consumes `args.batch` + `args.seeds` from argparse Namespace"
affects: [07-03 batch orchestrator, 07-05 REPL batch command, 07-06 phase verification]

# Tech tracking
tech-stack:
  added: []  # stdlib-only (argparse), no new deps
  patterns:
    - "Custom argparse type= converter raising ArgumentTypeError with Polish messages (analog of _parse_phi_list)"
    - "Post-parse p.error() mutex chain for flags that cannot be expressed via add_mutually_exclusive_group without losing Polish-message guarantee"
    - "Free-standing argparse flag (NOT in any mutex group) to ensure post-parse Polish error fires BEFORE argparse English fallback (Warning #8 mitigation)"
    - "DoS-cap constant applied to BOTH grammar branches (single-N AND post-dedup comma-list length)"

key-files:
  created: []
  modified:
    - "sphsim/cli/args.py — adds `_parse_seeds_list` + `MAX_SEEDS=1000` + `--batch`/`--seeds` flags + 4 post-parse Polish mutex checks (+81 lines)"
    - "tests/test_batch.py — greens TestSeedsParser (8 methods) + TestArgsMutex (4 methods); preserves 3 untouched skip-stubs for downstream plans (+108/-9 lines)"

key-decisions:
  - "`--batch` placed OUTSIDE any add_mutually_exclusive_group so the Phase-7 Polish post-parse mutex always fires first (Warning #8 mitigation). Top-level argparse mutex `{--interactive, --strategy, --custom}` (required=True) is unchanged and untouched."
  - "Test invocation for `--batch + --interactive` supplies ONLY `--interactive` (no `--strategy`) so the top-level required=True mutex is satisfied and post-parse Polish check runs. Test asserts Polish substring `'nie działa w trybie --interactive'` — English fallback explicitly NOT accepted."
  - "MAX_SEEDS = 1000 (T-7-02-01 DoS cap) enforced in BOTH branches: single-N before `list(range(...))` allocation, and comma-list AFTER deduplication (so `1,1,1,...` pathological input is rejected at meaningful size, not raw input size)."
  - "`_parse_seeds_list` exported at module level (not nested) so Plan 07-05 REPL can import it for single-source-of-truth grammar parity (CliReplParity invariant)."

patterns-established:
  - "Two-branch grammar parser (comma-detect first, else single-int fallback) returning a deduped preserve-order list — reusable shape for any future N|lista CLI flag."
  - "Polish-error-first ordering: any new mutex involving an argparse-required flag MUST avoid joining the existing add_mutually_exclusive_group; use free-standing flag + post-parse p.error instead, with an explicit code-comment rationale."

requirements-completed: [BATCH-01]  # CLI half only; REPL half completes in Plan 07-05

# Metrics
duration: ~5min
completed: 2026-05-28
---

# Phase 07 Plan 02: CLI Seed-List Parser + Batch Flags Summary

**`_parse_seeds_list` grammar converter (BATCH-01) + `--batch`/`--seeds` argparse flags + 4-way Polish-only post-parse mutex, with 12 GREEN tests on the CLI half (REPL half ships in Plan 07-05).**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-05-28T11:27Z (worktree spawn)
- **Completed:** 2026-05-28T11:32Z
- **Tasks:** 2 / 2 (both `tdd="true"`)
- **Files modified:** 2 (1 production + 1 test)

## Accomplishments

- `sphsim/cli/args.py` gains `_parse_seeds_list(s) -> list[int]` (grammar v1 from RESEARCH §B.3) — single positive integer N expands to `list(range(1, N+1))`; comma-separated list deduplicates preserving first-occurrence order; rejects `0`, negatives, empty, non-int, range-syntax `1..10`, and oversized inputs with Polish `argparse.ArgumentTypeError`.
- `MAX_SEEDS = 1000` constant added (T-7-02-01 DoS prevention) — enforced in BOTH grammar branches (`--seeds 1001` and a 1001-element comma list both rejected at the right size).
- `--batch` (store_true) and `--seeds` (type=_parse_seeds_list) wired into `sph_sim.py --help` — INTENTIONALLY free-standing (NOT in any `add_mutually_exclusive_group`) so the Phase-7 Polish post-parse `p.error` fires BEFORE any argparse English fallback (Warning #8 mitigation).
- 4 post-parse Polish-only mutex checks added after the existing `--compare-agent` block: `--batch + --compare-agent`, `--batch + --interactive`, `--batch without --seeds`, `--seeds without --batch` — each exits with code 2 + Polish message.
- `tests/test_batch.py` greens `TestSeedsParser` (8 direct-unit methods) + `TestArgsMutex` (4 subprocess methods) — 12 tests total. Remaining 3 classes (`TestReplBatch`, `TestDeterminism`, `TestCliReplParity`) preserved as Plan 07-00 skip-stubs for Plans 07-03 / 07-05.
- Phase 1-6 regression preserved (`scripts/regression_check.py` PASS=8/8). Full `unittest discover tests/` reports 194 tests, OK, skipped=10 (3 in test_batch + 7 in test_batch_stats/test_batch_report from Plan 00).

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend sphsim/cli/args.py with _parse_seeds_list + flags + mutex** — `788ea73` (feat)
2. **Task 2: Replace TestSeedsParser + TestArgsMutex skip-stubs with real assertions** — `698b1c2` (test)

_Note: Plan-level type is `execute`, not `tdd`. Per-task `tdd="true"` is in the conventional RED-via-acceptance-criteria-script style (each Task 1 acceptance check IS a RED test before the corresponding implementation paragraph), with Task 2 greening the formal unittest assertions. Conventional commit types `feat` (production code) + `test` (greening tests) reflect what each commit actually contains._

## Files Created/Modified

- `sphsim/cli/args.py` (+81 lines): inserted `MAX_SEEDS` constant + `_parse_seeds_list` function (between `_parse_rho_list` and `parse_args`), `--batch`/`--seeds` add_argument calls (after `--rho` add_argument), and 4 post-parse `p.error` checks (after the existing `--compare-agent` checks).
- `tests/test_batch.py` (+108 / −9 lines): added `import argparse` + `from sphsim.cli.args import _parse_seeds_list, MAX_SEEDS`; replaced 2 `test_placeholder` methods with 12 real assertion-bearing methods across 2 classes; preserved untouched the 3 remaining skip-stubs (TestReplBatch, TestDeterminism, TestCliReplParity).

## Decisions Made

1. **Warning #8 mitigation — `--batch` outside the top-level mutex group.** The existing `mutex = p.add_mutually_exclusive_group(required=True)` covers `{--interactive, --strategy, --custom}`. Including `--batch` there would cause argparse to emit its English `not allowed with argument` error at parse time, pre-empting our Polish `p.error("Flaga --batch nie działa w trybie --interactive ...")`. The plan-mandated solution was implemented verbatim: keep `--batch` free-standing and enforce all 4 batch-related mutex paths in post-parse Polish `p.error` calls. A code comment at the insertion point documents this rationale (`sphsim/cli/args.py:170-172` and `:195-197`).

2. **Test invocation pattern for `--batch + --interactive`.** Supplying both `--strategy naive` AND `--interactive` would fail the top-level required=True mutex with an English error BEFORE the Polish post-parse check could run. Test `TestArgsMutex.test_batch_interactive_mutex` therefore invokes `_run_sph('--interactive', '--batch', '--seeds', '5', '--seed', '42')` — `--interactive` alone satisfies the required=True mutex, leaving the post-parse Polish error as the firing source. Assertion is Polish-substring-only (`'nie działa w trybie --interactive'`); English fallback explicitly NOT accepted.

3. **MAX_SEEDS = 1000 applied post-dedup for comma lists.** A user typing `--seeds 1,1,1,1,...` 50000 times could bypass a raw-length cap but produces a 1-element list after dedup. The cap must therefore apply to `len(result)` (post-dedup), not to `len(raw)` (pre-dedup). This is the implementation chosen — the raw list is iterated for dedup first, then `len(result) > MAX_SEEDS` is checked. For single-N input the check is on `n` itself (before allocation).

4. **`_parse_seeds_list` placed between `_parse_rho_list` and `parse_args`.** Keeps all custom argparse `type=` converters in a contiguous block above the parser construction, matching the existing module organization. `MAX_SEEDS` placed immediately above its function as a module-level constant with a multi-line comment explaining the cap rationale.

## Deviations from Plan

None — plan executed exactly as written. The Warning #8 ordering decision was prescribed in the plan body (Task 1 `<action>` insertion 3), not discovered ad-hoc; same for the test-invocation pattern in Task 2.

## Threat Surface Scan

No new threat surface beyond `<threat_model>` in the plan:
- T-7-02-01 (DoS via oversized `--seeds`): mitigated by `MAX_SEEDS = 1000` in both branches.
- T-7-02-02 (info disclosure via Polish error messages): accepted — no user data leaks beyond the literal value echoed back.
- T-7-02-03 (Unicode whitespace bypass): accepted — `str.strip()` covers ASCII whitespace; non-ASCII would fall through to `int()` ValueError → ArgumentTypeError, which is the correct outcome.

## Known Stubs

None introduced by this plan. Pre-existing skip-stubs in `tests/test_batch.py` for `TestReplBatch`, `TestDeterminism`, `TestCliReplParity` are intentionally preserved for Plans 07-03 / 07-05 per the plan's `requirements-completed: [BATCH-01]` partial — CLI half only.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration.

## Self-Check: PASSED

Verified all claims in this SUMMARY against the worktree:

- `sphsim/cli/args.py` exists with `_parse_seeds_list` (grep: 1 match), `MAX_SEEDS = 1000` (1 match), `'--batch'` (1), `'--seeds'` (1), `p.error` (8 occurrences = 2 pre-existing + 4 new + 2 in comments).
- `tests/test_batch.py` exists with 5 `class Test` declarations, 15 `def test_` methods, exactly 3 `self.skipTest` remaining (TestReplBatch / TestDeterminism / TestCliReplParity placeholders preserved).
- Commits `788ea73` and `698b1c2` both present in `git log` on branch `worktree-agent-adccd791`.
- `python3 -m unittest tests.test_batch`: Ran 15 tests, OK (skipped=3).
- `python3 -m unittest tests.test_batch.TestSeedsParser tests.test_batch.TestArgsMutex -v`: Ran 12 tests, OK, 0 SKIPPED, 0 FAILED.
- `python3 scripts/regression_check.py`: PASS=8/8 (Phase 1-6 baseline preserved).
- `python3 -m unittest discover tests/`: Ran 194 tests, OK (skipped=10).
- All 4 CLI mutex paths exit with code 2 and contain the prescribed Polish substring (no English fallback).

## Next Phase Readiness

- **Plan 07-03 (Wave 2 — run_batch orchestrator)** can now consume `args.batch` (bool) and `args.seeds` (list[int] | None) directly from the argparse Namespace. The orchestrator should branch in `sphsim/cli/main.py` early: `if args.batch: run_batch(args.seeds, args, ...)` else proceed with the single-run path.
- **Plan 07-05 (Wave 4 — REPL `batch` command)** can `from sphsim.cli.args import _parse_seeds_list` to parse the REPL-side `--seeds` argument and guarantee CliReplParity (`TestCliReplParity` becomes greenable once both CLI and REPL paths funnel through the same converter).
- No blockers. Sibling Plan 07-01 (Wave 1, files `sphsim/batch/*` + `tests/test_batch_stats.py`) is parallel-safe with this work — zero file overlap.

---

*Phase: 07-batch-runner-aggregation*
*Plan: 02*
*Completed: 2026-05-28*
