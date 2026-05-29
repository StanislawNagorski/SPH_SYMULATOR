---
phase: 08-documentation-interactive-tutorial
plan: 08
subsystem: cli
tags: [repl, tutorial, polish-copy, cmd-cmd, ux]

# Dependency graph
requires:
  - phase: 08-documentation-interactive-tutorial
    provides: "Plan 08-04: TutorialFlow + check_step state machine + SPHShell precmd/postcmd plumbing"
provides:
  - "INTRO banner advertises `tutorial` command (Gap 1: discoverability)"
  - "Per-step controls footer `Sterowanie: skip | back | repeat | exit` (Gap 2: visibility)"
  - "_TUTORIAL_CONTROLS_LINE module-level constant — DRY across banner + step display"
  - "_last_command_unknown flag plumbed through __init__/precmd/postcmd/default (Gap 4)"
  - "Soft-pass steps 6/7 reject `Nieznana komenda` typos (Gap 4 regression)"
affects: [08-09, 08-10]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single-flag boolean for cross-method state (default→postcmd via _last_command_unknown)"
    - "Module-level constant for repeated UX literals (DRY in single-file scope)"

key-files:
  created: []
  modified:
    - "sphsim/cli/repl.py"
    - "tests/test_tutorial.py"

key-decisions:
  - "Reset _last_command_unknown in precmd's final `return line` branch only (the dispatch exit point) — control verbs return '' and skip postcmd via the existing top guard, so they don't need the reset"
  - "Keep the new INTRO pointer literal inline (not extracted to a constant) — matches the inline style of the existing help/exit pointer lines"
  - "Place the new controls footer in _show_tutorial_step BEFORE the existing soft-pass explainer comment so the comment continues to describe step-6 check_step semantics, untouched"

patterns-established:
  - "Pattern A: Defer cross-method REPL signals through a single boolean attribute rather than parsing stdout — keeps default() the only writer and postcmd the only reader/clearer"
  - "Pattern B: Extract repeated user-facing literals to a module-level constant once they appear in ≥2 print sites within the same file"

requirements-completed: [TUT-01, TUT-02]

# Metrics
duration: ~12min
completed: 2026-05-29
---

# Phase 08 Plan 08: Gap-closure for tutorial discoverability, controls visibility, and typo rejection — Summary

**Three small, related repl.py edits that together fix UAT Gaps 1+2+4 — INTRO now advertises `tutorial`, every step display shows the four control verbs, and typos no longer auto-pass soft-pass steps 6/7.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-05-29T08:50:00Z (approx.)
- **Completed:** 2026-05-29T08:59:43Z
- **Tasks:** 2
- **Files modified:** 2 (1 source, 1 test)

## Accomplishments

- **Gap 1 closed:** `python sph_sim.py --interactive` boot banner now contains a third pointer line `  Wpisz \`tutorial\` żeby uruchomić interaktywny tutorial v1.1 (≤15 min).` between the existing `help` and `exit` pointers. New users discover the ≤15-min onboarding path immediately on first banner.
- **Gap 2 closed:** Module-level `_TUTORIAL_CONTROLS_LINE = "Sterowanie: skip | back | repeat | exit"` constant defined once, reused in BOTH the do_tutorial entry banner AND the _show_tutorial_step footer. Users see the four control verbs on every step display, not just the one-time entry banner.
- **Gap 4 closed:** `_last_command_unknown` flag plumbed through SPHShell's __init__/precmd/postcmd/default. cmd.Cmd.default() now flags every unrecognised line; postcmd short-circuits check_step BEFORE soft-pass steps 6/7 falsely accept the garbage as a valid attempt. Locked in by new regression test.

## Task Commits

Each task was committed atomically:

1. **Task 1: INTRO banner pointer + _TUTORIAL_CONTROLS_LINE constant + controls footer + _last_command_unknown plumbing** — `cab7bfc` (fix)
2. **Task 2: Add test_soft_pass_step_rejects_unknown_command + green** — `c76ce02` (test)

_Note: this plan is not flagged `type: tdd` at plan level; Task 2 carries `tdd="true"` and runs the GREEN gate immediately because Task 1 already implemented the source fix (per plan's RED→GREEN order note)._

## Files Created/Modified

- `sphsim/cli/repl.py` — INTRO gains a tutorial pointer line; new `_TUTORIAL_CONTROLS_LINE` module-level constant; `_show_tutorial_step` prints the controls footer; `__init__` initialises `self._last_command_unknown = False`; `precmd` resets the flag before the dispatch `return line`; `postcmd` short-circuits check_step when the flag is set; `default()` sets the flag before the Polish error print.
- `tests/test_tutorial.py` — new `TestTutorialControls.test_soft_pass_step_rejects_unknown_command` subprocess test: drives the REPL through 5 skips to reach step 6, types `tojesttypo`, asserts `Nieznana komenda` shown, `✓ zaliczone — krok 6/8` NOT shown, and `[krok 6/8` still on screen.

## Decisions Made

- **Reset the flag in precmd's dispatch-exit branch only.** The plan instructed placement before the final `return line` at the bottom of precmd, not before the four `return ''` short-circuit branches for skip/back/repeat/exit. Rationale: control verbs never reach cmd.Cmd dispatch (precmd consumes them) and postcmd's existing top guard `if not line.strip() or self._tutorial_state is None or stop: return stop` already filters them out — the reset would be dead code on those paths.
- **Keep the INTRO tutorial pointer as an inline literal, not a constant.** Matches the inline style of the existing help/exit pointer lines in the INTRO tuple. The DRY win only justified extraction for the controls line, which appears in two distinct print sites.
- **Place controls footer BEFORE the existing soft-pass explainer comment.** The comment describes check_step semantics for step 6 — keeping it adjacent to the display code preserves its context, while the footer print fits naturally after the bottom rule.

## Deviations from Plan

None — plan executed exactly as written. All four edits in Task 1 applied verbatim to the line ranges the plan indicated, and the Task 2 test method body matches the verbatim outline from the plan's `<action>` block.

A trivial documentation observation, not a deviation: the plan's verify block claims `_last_command_unknown` should appear in "exactly 4 source locations" but actually appears in 5 code lines (init=1, precmd reset=1, postcmd read=1, postcmd reset=1, default set=1) plus one comment reference. The plan's "4 logical sites" is correct (init, precmd, postcmd guard, default), but postcmd's guard naturally has two lines (read + reset). All semantic intent is met; no behavioral change to flag.

## Issues Encountered

None — Task 1's structural greps matched first-try (1, 3, 6), regression_check.py reported PASS=8/8, verify_phase8.sh exited rc=0 with PASS=34/FAIL=0, and the new Task 2 regression test passed first-run because Task 1 already implemented the underlying fix.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 08-09 (Wave 5 sibling) can land independently: it does NOT touch repl.py, only sphsim/cli/tutorial.py + scripts/verify_phase8.sh + step-count literals. No merge conflict risk.
- Plan 08-10 (Wave 5 sibling) can land independently: it touches docs/PRZEWODNIK.md + sphsim/cli/args.py error wording + scripts/verify_phase3.sh assertions. No file overlap with 08-08.
- The full Phase 8 verifier (`scripts/verify_phase8.sh`) reports PASS=34/FAIL=0 after this plan's commits — no new check additions or assertion changes were needed in 08-08 (08-09/08-10 own those).

## Self-Check: PASSED

- File existence check:
  - FOUND: sphsim/cli/repl.py
  - FOUND: tests/test_tutorial.py
  - FOUND: .planning/phases/08-documentation-interactive-tutorial/08-08-SUMMARY.md
- Commit existence check:
  - FOUND: cab7bfc (Task 1)
  - FOUND: c76ce02 (Task 2)
- Structural greps (Task 1 verify block):
  - `tutorial\` żeby uruchomić interaktywny tutorial` → 1 ✓
  - `_TUTORIAL_CONTROLS_LINE` → 3 ✓
  - `_last_command_unknown` → 6 (5 code + 1 comment; 4 logical sites — see Decisions)
- Behavioral smoke tests:
  - INTRO banner contains `Wpisz \`tutorial\`` line ✓
  - `tutorial` command renders `Sterowanie: skip | back | repeat | exit` twice (banner + step 1 display) ✓
  - New regression test `test_soft_pass_step_rejects_unknown_command` passes ✓
- Test suites:
  - `tests.test_tutorial` — 47/47 OK (was 46, +1 new)
  - `tests.test_tutorial + tests.test_docs` — 55/55 OK
  - `scripts/regression_check.py` — PASS 8/8
  - `scripts/verify_phase8.sh` — PASS 34/FAIL 0, rc=0

---
*Phase: 08-documentation-interactive-tutorial*
*Plan: 08*
*Completed: 2026-05-29*
