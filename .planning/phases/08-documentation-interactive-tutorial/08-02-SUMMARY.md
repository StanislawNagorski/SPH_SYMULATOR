---
phase: 08-documentation-interactive-tutorial
plan: 02
subsystem: cli
tags: [cli, argparse, tutorial, mutex, polish-errors, tdd]
requires:
  - 08-00  # Wave 0 scaffolding (test stubs + verify_phase8.sh skeleton)
provides:
  - "--tutorial CLI flag (D-02, TUT-05)"
  - "5-way post-parse Polish mutex (tutorial × interactive/strategy/custom/batch/compare-agent)"
  - "Polish required-mode error (replaces argparse English fallback)"
  - "4th early branch in main.py dispatching --tutorial to run_repl(start_in_tutorial=True)"
affects:
  - sphsim/cli/args.py (mutex group required=True → required=False, +5 Polish post-parse checks, +1 required-mode check)
  - sphsim/cli/main.py (4th early branch — tutorial)
  - tests/test_tutorial.py::TestTutorialCLI (8 real tests flipped from @skip)
tech-stack:
  added: []  # zero new deps — stdlib argparse only
  patterns:
    - "Free-standing flag + post-parse Polish p.error (Phase 7 BATCH-01 pattern extended to 5-way)"
    - "Mutex group required=False + Polish required-mode replacement"
    - "Forward-reference call site (run_repl signature lands in Plan 08-04)"
    - "TDD RED→GREEN for argparse-layer tests; structural test (4th branch) verified via grep + full suite green"
key-files:
  created: []
  modified:
    - sphsim/cli/args.py
    - sphsim/cli/main.py
    - tests/test_tutorial.py
decisions:
  - "Polish required-mode replacement: changed mutex group required=True → required=False AND added post-parse `Musisz podać jeden z trybów:` check because argparse enforces required=True BEFORE post-parse code runs (would leak English error for `--tutorial` alone since --tutorial is outside the group)."
  - "Forward reference accepted: main.py calls `run_repl(start_in_tutorial=True)` at Wave 1 — this signature lands in Plan 08-04. End-to-end runtime test (`test_tutorial_flag_enters_tutorial_mode`) stays @unittest.skip until Plan 04 lands; argparse layer is independently verifiable via the 8 flipped tests."
  - "No no-op stub `def run_repl(start_in_tutorial=False)` added in repl.py — that would be premature; Plan 08-04 owns repl.py changes entirely."
metrics:
  duration_min: ~9
  completed_date: "2026-05-28"
  tasks_completed: 2
  files_modified: 3
  tests_added: 7  # 1 RED commit added 8 methods; 1 already existed as @skip (kept)
  commits: 3
---

# Phase 08 Plan 02: --tutorial CLI Flag + 5-Way Mutex Summary

**One-liner:** Add `--tutorial` flag wired as a 5th mutex member via the Phase-7-style post-parse Polish p.error pattern, plus the 4th early branch in main.py dispatching to `run_repl(start_in_tutorial=True)` (forward reference to Plan 08-04).

## What Shipped

### (a) `sphsim/cli/args.py` changes

1. **Declaration** — `--tutorial` added as free-standing `store_true` flag in the same "INTENTIONALLY free-standing" comment block as `--batch` and `--seeds`, with Polish help text `Uruchom interaktywny tutorial v1.1 (≤15 min)`.
2. **Mutex group relaxation** — `mutex = p.add_mutually_exclusive_group(required=True)` → `required=False`. Reason: argparse enforces `required=True` BEFORE post-parse code runs; leaving it `True` would trip the English "one of the arguments --interactive --strategy --custom is required" error when invoking `python sph_sim.py --tutorial` alone (since `--tutorial` is intentionally NOT in the group).
3. **Polish required-mode check** — prepended to post-parse block:
   ```python
   if not (args.interactive or args.strategy or args.custom or args.batch or args.tutorial):
       p.error("Musisz podać jeden z trybów: --interactive, --strategy, --custom, --batch lub --tutorial.")
   ```
4. **5 tutorial-conflict checks** inserted before the existing `--batch/--seeds` checks, verbatim per PATTERNS.md lines 193-201:
   - `Flagi --tutorial i --interactive są wzajemnie wykluczające.`
   - `Flaga --tutorial nie działa z --strategy (użyj trybu tutorial interaktywnie).` (uses `getattr(args, 'strategy', None)` per PATTERNS line 207)
   - `Flaga --tutorial nie działa z --custom.`
   - `Flagi --tutorial i --batch są wzajemnie wykluczające.`
   - `Flagi --tutorial i --compare-agent są wzajemnie wykluczające.`

### (b) `sphsim/cli/main.py` changes

4th early branch inserted IMMEDIATELY BEFORE the `--interactive` branch:
```python
if args.tutorial:
    from sphsim.cli.repl import run_repl
    run_repl(start_in_tutorial=True)
    return
```
Branch order is now: `tutorial → interactive → batch → compare-agent → one-shot`. Deferred import mirrors the existing `--interactive` pattern (not hoisted — PATTERNS line 239-241).

### (c) 8 TestTutorialCLI tests passing, 1 still skipped

`tests/test_tutorial.py::TestTutorialCLI` flipped from a single broad `@unittest.skip` to 8 real test methods + 1 still-skipped end-to-end test:

| Test method | Purpose | Status |
|---|---|---|
| `test_tutorial_flag_parses_without_error` | `--tutorial --help` exits 0; `--help` in stdout | PASS |
| `test_tutorial_plus_interactive_errors_polish` | `--tutorial --interactive` → Polish mutex | PASS |
| `test_tutorial_plus_strategy_errors_polish` | `--tutorial --strategy naive` → Polish mutex | PASS |
| `test_tutorial_plus_custom_errors_polish` | `--tutorial --custom <path>` → Polish mutex | PASS |
| `test_tutorial_plus_batch_errors_polish` | `--tutorial --batch --seeds 5` → Polish mutex | PASS |
| `test_tutorial_plus_compare_agent_errors_polish` | `--tutorial --compare-agent` → Polish mutex | PASS |
| `test_existing_cli_unchanged_baseline_works` | `--strategy naive --seed 42 --json --no-agent` still works | PASS |
| `test_no_mode_errors_polish` | `python sph_sim.py` → Polish `Musisz podać jeden z trybów:` | PASS |
| `test_tutorial_flag_enters_tutorial_mode` | End-to-end tutorial banner (subprocess) | SKIP — Plan 08-04 |

### (d) Regression PASS=8/8 (CLI-04 preserved)

- `python3 scripts/regression_check.py` → `PASS: 8/8`
- `tests.test_args_agent_flags` → 9 OK (all 4 existing mutex contracts preserved)
- Full suite: `python3 -m unittest discover tests` → `Ran 222 tests in 23.6s — OK (skipped=9)`

### (e) Subtleties encountered

1. **`required=True` → `required=False` was non-optional.** Without this change, the test `python sph_sim.py --tutorial` would have leaked argparse's English "one of the arguments ... is required" error — directly violating the Polish-error invariant inherited from Phase 7. The fix is twofold: relax the group AND add a Polish post-parse check that exactly one mode is selected. Both are required; either alone leaves a contract hole.
2. **`test_args_agent_flags` continues to pass without modification** — the existing 4-way mutex contract (compare-agent/no-agent, compare-agent/interactive, batch combinations) is untouched. The 4 existing checks fire BEFORE the new tutorial checks; their order is preserved.
3. **`Musisz podać jeden z trybów:` appears twice in args.py source** — once in the explanatory comment (line 145), once in the actual `p.error` call (line 202). The acceptance criterion `grep -c "Musisz podać jeden z trybów"` outputs `2` instead of `1`, but the spirit (one actual `p.error` call site exists) is satisfied.
4. **`run_repl(start_in_tutorial=True)` appears twice in main.py source** — once in the explanatory comment (line 61) explaining the forward reference, once in the actual call (line 67). Same pattern; one actual call site.
5. **Forward reference contract:** `main.py` at Wave 1 calls `run_repl(start_in_tutorial=True)` — invoking `python sph_sim.py --tutorial` end-to-end would raise `TypeError: run_repl() got an unexpected keyword argument 'start_in_tutorial'` at RUNTIME (not import time). This is acceptable because (a) the args.py + main.py wiring is independently testable via subprocess argparse tests, (b) Plan 04 lands the signature change in Wave 2 before any test invokes `--tutorial` end-to-end, (c) the end-to-end test stays `@unittest.skip` until Plan 04.
6. **MVP+TDD gate behavior:** Task 1 followed RED→GREEN; Task 2 had no test flip per the plan's explicit `<action>` instruction (the only end-to-end test is owned by Plan 04, and Task 2's behavior is verified via grep + full-suite-green-after-edit). This matches the plan's explicit design — Task 2 is wiring, not new testable surface beyond Task 1.

## Deviations from Plan

None — plan executed exactly as written. All 5 Polish strings VERBATIM per PATTERNS.md. All acceptance criteria met (the two `grep -c == 1` criteria became `== 2` because of explanatory comments containing the same string, but the actual call sites are unique — semantically equivalent).

## Threat Model — Mitigations Applied

- **T-08-02-01 (Tampering, mutex invariant):** Mitigated. `tests.test_args_agent_flags` (9 tests) continues to pass; `regression_check.py` PASS=8/8.
- **T-08-02-02 (Information Disclosure, English error leakage):** Mitigated. `required=True` → `required=False` + Polish `Musisz podać jeden z trybów:` check converts the required-mode error from English to Polish (Test 8 verifies).
- **T-08-02-03 (DoS, TypeError when --tutorial invoked before Plan 04):** Accepted per plan — documented in main.py inline comment; end-to-end test stays `@skip` until Plan 04 lands.
- **T-08-SC (Tampering, npm/pip):** N/A — Plan 08-02 installs no packages.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or trust-boundary schema changes. Strictly argparse-layer mutex extension + main.py branch routing.

## Commits (Wave 1, branch `worktree-agent-a674f9c0`)

| Commit | Type | Subject |
|---|---|---|
| `91b9a27` | test | add failing tests for --tutorial flag + 5-way mutex (RED) |
| `fe62aa3` | feat | add --tutorial flag + 5-way post-parse Polish mutex (GREEN) |
| `406bb66` | feat | add 4th early branch in main.py for --tutorial |

## Known Stubs

None — no hardcoded empty/placeholder values introduced. All new code paths are fully wired at the argparse layer; the `run_repl(start_in_tutorial=True)` call site is a deliberate forward reference (Plan 08-04) — documented in main.py inline comment and tracked in T-08-02-03.

## TDD Gate Compliance

Task 1: RED (`91b9a27` test commit) → GREEN (`fe62aa3` feat commit) → no REFACTOR needed (code is minimal and clean). Gates correctly sequenced.

Task 2: Per plan's explicit `<action>` instruction, no test file flip — verification relies on grep + full-suite-green-after-edit (`406bb66`). This is consistent with the plan's forward-reference design (the only end-to-end test for this branch is owned by Plan 08-04).

## Self-Check: PASSED

- `sphsim/cli/args.py` modified: FOUND (commit `fe62aa3`)
- `sphsim/cli/main.py` modified: FOUND (commit `406bb66`)
- `tests/test_tutorial.py` modified: FOUND (commit `91b9a27`)
- All 3 commits exist in `git log`: FOUND
- Full test suite: 222 OK / 9 skipped
- Regression: PASS=8/8
- All 5 Polish error strings present verbatim: VERIFIED via grep
- Mutex group `required=False`: VERIFIED (line 147)
- 4th early branch order tutorial→interactive: VERIFIED (lines 65 → 69)
