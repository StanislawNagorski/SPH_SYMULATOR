---
phase: 08-documentation-interactive-tutorial
plan: 09
subsystem: cli
tags: [tutorial, state-machine, polish-copy, ux, uat-gap-3]

# Dependency graph
requires:
  - phase: 08-documentation-interactive-tutorial
    provides: "Plan 08-04: TutorialFlow + STEP_TOPICS + STEP_TASKS + check_step state machine"
  - phase: 08-documentation-interactive-tutorial
    provides: "Plan 08-08: _last_command_unknown + _TUTORIAL_CONTROLS_LINE + INTRO tutorial pointer"
provides:
  - "9-step tutorial state machine (was 8) — UAT Gap 3 split"
  - "STEP_TOPICS key 3 'strategy-details' inserted between 'strategies' (2) and 'run-strategy' (now 4)"
  - "STEP_TASKS step 2 tightened to `strategies` only (list-only); new step 3 `strategy <name>` (details)"
  - "check_step step 2 returns line == 'strategies' (no startswith fallback)"
  - "check_step step 3 returns len(tokens) >= 2 and tokens[0] == 'strategy'"
  - "TutorialFlow.total default = 9 (was 8)"
  - "repl.py postcmd hint set (2, 3, 5, 8) — display-only steps post split"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cascading state-machine renumber: insert key 3, shift 3..8 to 4..9; update STEP_TOPICS, STEP_TASKS, check_step, all subprocess assertions, verifier skip count, and PRZEWODNIK sample in lock-step"

key-files:
  created:
    - ".planning/phases/08-documentation-interactive-tutorial/08-09-SUMMARY.md"
  modified:
    - "sphsim/cli/tutorial.py"
    - "sphsim/cli/repl.py"
    - "tests/test_tutorial.py"
    - "scripts/verify_phase8.sh"
    - "docs/PRZEWODNIK.md"

key-decisions:
  - "Place new step 3 between current step 2 (strategies) and old step 3 (run-strategy) so the pedagogical sequence is: list → details → run — matches the natural user discovery flow"
  - "Renumber-by-key strategy: every artifact that references step counts gets a mechanical /8 → /9 substitution; step ranges in tests use 1..10 (exclusive upper bound of range())"
  - "Soft-pass hint-set update (2, 4, 7) → (2, 3, 5, 8) covers the four display-only steps post-renumber: list (2), details (3, NEW), custom (5, was 4), report (8, was 7)"
  - "The TDD GREEN gate fires immediately for Task 3 because Tasks 1+2 already implemented the source — pattern inherited from Plan 08-08 (test edits land on already-green source)"

patterns-established:
  - "Pattern: when a state-machine step is split, the renumber cascade touches at minimum: STEP_TOPICS, STEP_TASKS (with matching step_num fields), check_step branches, repl.py postcmd hint set, every subprocess `/N` assertion in tests, verifier skip count + krok N/M assertion, and the user-facing sample heading in PRZEWODNIK.md"

requirements-completed: [TUT-01, TUT-02, TUT-03]

# Metrics
duration: ~10min
completed: 2026-05-29
---

# Phase 08 Plan 09: UAT Gap 3 — split tutorial step 2 into list + details (9-step state machine) — Summary

**Cascading 5-file renumber: tutorial.py state machine grows from 8 to 9 steps, splitting old step 2 (`strategies` + `strategy <name>` conflated) into a list step (2) and a details step (3); all subprocess assertions, verifier skip counts, and the sample heading in PRZEWODNIK.md updated in lock-step.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-05-29 (Wave 6)
- **Completed:** 2026-05-29
- **Tasks:** 5
- **Files modified:** 5 (1 state machine, 1 REPL, 1 test suite, 1 verifier, 1 doc)

## Accomplishments

- **UAT Gap 3 closed:** the dydaktically muddled "list strategies AND view one's details" step is now two distinct steps. Step 2 ('Lista strategii') accepts ONLY `strategies` and teaches the listing command; step 3 ('Szczegóły strategii', NEW) accepts ONLY `strategy <name>` and teaches the detail viewer.
- **TutorialFlow.total = 9** propagates through every `{ts.total}` f-string in repl.py — banners, skip messages, back messages, zaliczone messages, [krok N/M — Title] step headings — all automatically render `1/9, 2/9, ..., 9/9`.
- **check_step branches reshuffled:** step 2 tightened (`line == 'strategies'`, no startswith fallback); new step 3 (`len(tokens) >= 2 and tokens[0] == 'strategy'`); old 3..8 renumbered to 4..9 with bodies UNCHANGED.
- **Hint-set updated:** `postcmd` now treats steps `(2, 3, 5, 8)` as display-only (was `(2, 4, 7)`) — covers list, details, custom (post-renumber), and report soft-pass.
- **Test count +1:** new `test_check_step3_strategy_details` asserts the new details branch; existing `test_check_step2_strategies` tightened to assert the rejection of `strategy <name>` at step 2.
- **Six existing check-stepN tests renamed:** `test_check_step3_any_builtin` → `test_check_step4_any_builtin` (and analogous shifts for steps 4..8 → 5..9).
- **Verifier D3 sends 9 skips** instead of 8 and asserts `pominięto — krok 9/9`; D2 + D4 assert `1/9`.
- **PRZEWODNIK sample heading** at line 59 updated to `[krok 1/9 — Baseline]` so the README matches what users actually see.

## Task Commits

Each task was committed atomically:

1. **Task 1: Split STEP_TOPICS/STEP_TASKS + renumber check_step + TutorialFlow.total=9 in sphsim/cli/tutorial.py** — `b672654` (feat)
2. **Task 2: Update sphsim/cli/repl.py hint set + ~9 kroków literals** — `963e7cd` (feat)
3. **Task 3: Update tests/test_tutorial.py — all /9 literals + restructure step-2 + new step-3 test + renumber check_stepN tests** — `9bc907d` (test)
4. **Task 4: Update scripts/verify_phase8.sh D2/D3/D4 step-count literals + 9 skips** — `25beb53` (test)
5. **Task 5: Update docs/PRZEWODNIK.md sample step heading to [krok 1/9 — Baseline]** — `36de02a` (docs)

_Note: Task 3 is flagged `tdd="true"`. As in Plan 08-08, the GREEN gate fires immediately because Tasks 1+2 implemented the source ahead of the test edits — the test alignments land directly on already-passing implementation. This is consistent with the plan's intent (no behavior change separate from the source rename)._

## Files Created/Modified

- `sphsim/cli/tutorial.py` — STEP_TOPICS gains key 3 'strategy-details'; STEP_TASKS step 2 description tightened to `strategies` only; new STEP_TASKS[3] 'Szczegóły strategii' inserted; old STEP_TASKS 3..8 renumbered to 4..9 with matching `step_num` field; TutorialFlow.total = 9 (docstring updated to "post UAT Gap 3"); check_step step-2 branch returns `line == 'strategies'` (no startswith); new step-3 branch returns `len(tokens) >= 2 and tokens[0] == 'strategy'`; old 3..8 branches renumbered to 4..9 with bodies UNCHANGED.
- `sphsim/cli/repl.py` — postcmd hint set updated `(2, 4, 7) → (2, 3, 5, 8)`; do_tutorial docstring `~8 kroków → ~9 kroków`; do_tutorial banner line `~8 kroków → ~9 kroków`.
- `tests/test_tutorial.py` — every `/8` subprocess assertion → `/9`; test_soft_pass_step_rejects_unknown_command now reaches step 7 via 6 skips; test_tutorialflow_defaults asserts tf.total == 9; test_step_topics_keys_and_slugs has 9-key expected dict; test_step_tasks_have_tutorialstep_instances uses range(1, 10); test_step6_open_question_2_resolution renamed test_step7_open_question_2_resolution; test_check_step2_strategies tightened; NEW test_check_step3_strategy_details; six check_stepN tests renamed with bumped step_n.
- `scripts/verify_phase8.sh` — D2 asserts `[krok 1/9`; D3 sends 9 skips and asserts `pominięto — krok 9/9` (label updated); D4 asserts `✓ zaliczone — krok 1/9`.
- `docs/PRZEWODNIK.md` — line 59 sample heading updated to `[krok 1/9 — Baseline]`.

## Decisions Made

- **Place new step 3 (details) directly after step 2 (list)** — the pedagogical sequence "list → details → run" matches the natural user discovery flow (`what strategies exist? → tell me more about one → now run it`).
- **Renumber-by-key strategy** — every artifact that references step counts gets a mechanical /8 → /9 substitution; test loop ranges use 1..10 (exclusive upper bound); no semantic rewrites of step bodies other than step 2's tightening.
- **Mirror Plan 08-08's TDD pattern for Task 3** — the plan flags Task 3 `tdd="true"` but Tasks 1+2 implemented the source ahead of test edits. The GREEN gate fires immediately because the test alignments are mechanical rename + literal updates landing on already-correct source. This is the same pattern Plan 08-08 used and is intentional — no behavior change separates Task 1's state-machine edit from Task 3's assertion alignment.

## Deviations from Plan

None — plan executed exactly as written. All five tasks applied verbatim to the line ranges the plan indicated. Task 1's structural greps matched first-try (1, 1, 1, 9); Task 2's structural greps matched (2, 1, 0); Task 3 produced 48 OK tests first run (was 47, +1 new `test_check_step3_strategy_details`); Task 4's verify_phase8.sh exited 0 with PASS=34/FAIL=0; Task 5's grep returned exactly one line.

## Issues Encountered

None — every gate green first try. Notable: the `tests/test_tutorial.py` post-edit `grep` for `def test_check_step{3..8}_old_name` flagged `test_check_step7_soft_pass` as residual, but inspection confirmed it is the NEW step-7 test (renamed from the old step-6 soft-pass test) — semantically correct after rename, not a stale reference.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 08-10 (Wave 6 sibling) does NOT touch any of the 5 files this plan modified (tutorial.py, repl.py, test_tutorial.py, verify_phase8.sh, PRZEWODNIK.md sample heading). No merge conflict risk.
- The full Phase 8 verifier (`scripts/verify_phase8.sh`) reports PASS=34/FAIL=0 after this plan — same check count as before (no checks added or removed, only assertion content updated).
- `scripts/regression_check.py` reports PASS=8/8 — CLI-04 byte-identical invariant preserved (Phase 8 never touches --json contract for built-in strategies).
- Full `unittest discover tests` reports OK with 261 tests.

## Self-Check: PASSED

- File existence check:
  - FOUND: sphsim/cli/tutorial.py
  - FOUND: sphsim/cli/repl.py
  - FOUND: tests/test_tutorial.py
  - FOUND: scripts/verify_phase8.sh
  - FOUND: docs/PRZEWODNIK.md
  - FOUND: .planning/phases/08-documentation-interactive-tutorial/08-09-SUMMARY.md
- Commit existence check (will be verified after final commit):
  - FOUND: b672654 (Task 1 — tutorial.py)
  - FOUND: 963e7cd (Task 2 — repl.py)
  - FOUND: 9bc907d (Task 3 — test_tutorial.py)
  - FOUND: 25beb53 (Task 4 — verify_phase8.sh)
  - FOUND: 36de02a (Task 5 — PRZEWODNIK.md)
- Structural greps:
  - `3: 'strategy-details'` in tutorial.py → 1 ✓
  - `9: 'batch'` in tutorial.py → 1 ✓
  - `total: int = 9` in tutorial.py → 1 ✓
  - `if step_n == [1-9]:` branches in tutorial.py → 9 ✓
  - `~9 kroków` in repl.py → 2 ✓
  - `ts.step in (2, 3, 5, 8)` in repl.py → 1 ✓
  - `~8 kroków` in repl.py → 0 (residual) ✓
  - `test_check_step3_strategy_details` in test_tutorial.py → 1 ✓
  - No `krok [1268]/8` residuals in subprocess assertions ✓
  - `[krok 1/9 — Baseline]` in PRZEWODNIK.md → 1 ✓
- Test suites:
  - `tests.test_tutorial` — 48/48 OK (was 47, +1 new `test_check_step3_strategy_details`)
  - Full `unittest discover tests` — 261/261 OK
  - `scripts/regression_check.py` — PASS 8/8
  - `scripts/verify_phase8.sh` — PASS 34/FAIL 0, rc=0

---
*Phase: 08-documentation-interactive-tutorial*
*Plan: 09*
*Completed: 2026-05-29*
