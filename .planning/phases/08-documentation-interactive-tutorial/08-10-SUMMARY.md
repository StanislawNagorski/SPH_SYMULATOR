---
phase: 08-documentation-interactive-tutorial
plan: 10
subsystem: cli
tags: [argparse, polish-copy, ux, uat-gap-5, discoverability, repl]

# Dependency graph
requires:
  - phase: 08-documentation-interactive-tutorial
    provides: "Plan 08-02: Polish post-parse `Musisz podać jeden z trybów` contract (replaced here)"
  - phase: 08-documentation-interactive-tutorial
    provides: "Plan 08-09: ~9 kroków literal sweep (banner --tutorial line uses '~9 kroków')"
provides:
  - "Bare `python sph_sim.py` (no mode flag) auto-promotes to args.interactive=True + boots REPL"
  - "7-line Polish stderr banner listing the 4 alternate modes (--interactive, --strategy, --custom, --batch, --tutorial) before REPL INTRO"
  - "Plan 08-02 hard-error contract (`Musisz podać jeden z trybów` + exit 2) replaced repository-wide"
  - "verify_phase8.sh C7 + verify_phase3.sh D-44 retro check both flipped to grep `Nie podano trybu` (stdin-fed `echo exit` to exit REPL)"
  - "tests/test_tutorial.py::TestTutorialCLI::test_no_mode_defaults_to_interactive_with_banner (replaces test_no_mode_errors_polish)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Informational-default CLI contract: bare invocation auto-promotes to most-likely mode + prints stderr discovery banner instead of exit 2 (discoverability over penalty)"
    - "Verifier `echo exit | $PY sph_sim.py` pattern for asserting REPL-boot behavior without hanging on stdin"

key-files:
  created:
    - ".planning/phases/08-documentation-interactive-tutorial/08-10-SUMMARY.md"
  modified:
    - "sphsim/cli/args.py"
    - "tests/test_tutorial.py"
    - "scripts/verify_phase8.sh"
    - "scripts/verify_phase3.sh"

key-decisions:
  - "Banner emitted to stderr (not stdout) so JSON consumers using --strategy mode are never affected and the banner is visually separated from the REPL INTRO that prints to stdout"
  - "Banner printed BEFORE the REPL boots so users see the discovery hint above the INTRO banner — informational first, then functional"
  - "argparse parser.error() avoided entirely on no-mode path — calling p.error() would exit(2); instead we set args.interactive=True and fall through to return args, letting main.py's existing `if args.interactive:` branch boot run_repl()"
  - "regression_check.py UNCHANGED — all 8 strategies always invoked with explicit `--strategy` flag, so auto-promotion path is never exercised by the JSON byte-identity baseline (CLI-04 invariant preserved)"

patterns-established:
  - "Auto-promote to safe default + stderr discovery banner: applicable to any future CLI add where no flag is given but the most-likely mode is obvious (REPL boot)"
  - "Cross-script verifier flip: when contract changes, sweep BOTH the phase-specific verifier (verify_phase8.sh) AND the earlier-phase retro verifier (verify_phase3.sh) in the same commit to keep retro coverage honest"

requirements-completed: [CLI-01, CLI-02]

# Metrics
duration: ~12 min
completed: 2026-05-29
---

# Phase 8 Plan 10: UAT Gap 5 — No-Mode Auto-Promote with Polish Discovery Banner Summary

**Bare `python sph_sim.py` now auto-promotes to --interactive and prints a 7-line Polish stderr banner listing the 4 alternate modes — replacing the Plan 08-02 hard-error contract (`Musisz podać jeden z trybów:` → exit 2) with discoverability-first UX across args.py, the test_no_mode test, verify_phase8 C7, and verify_phase3 D-44 retro.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-05-29T09:11Z (approx, after worktree branch check)
- **Completed:** 2026-05-29T09:23:54Z
- **Tasks:** 3 / 3
- **Files modified:** 4

## Accomplishments

- Replaced `p.error("Musisz podać jeden z trybów: …")` in sphsim/cli/args.py with `args.interactive = True` + 7-line Polish stderr banner.
- Added `import sys` to args.py (needed for `file=sys.stderr`).
- Updated the Plan 08-02 rationale comment block (lines 141–146) to reflect the informational-default contract.
- Flipped tests/test_tutorial.py::TestTutorialCLI::test_no_mode_errors_polish → test_no_mode_defaults_to_interactive_with_banner: asserts rc==0, banner header `Nie podano trybu` on stderr, all 4 flag names on stderr, INTRO `Symulator Strategii` on stdout.
- Flipped scripts/verify_phase8.sh C7 grep target to `Nie podano trybu` with `echo exit |` REPL exit pattern; updated label to "(UAT Gap 5)".
- Flipped scripts/verify_phase3.sh lines 155–156 to the same `Nie podano trybu` target + same stdin-feed pattern; updated retro check label.
- Verified: all 261 tests pass under `python -m unittest discover tests`, verify_phase8.sh PASS=34/0, verify_phase3.sh PASS=20/0, regression_check.py PASS 8/8.

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace p.error no-mode block with auto-promote + Polish stderr banner in sphsim/cli/args.py** — `df3779d` (feat)
2. **Task 2: Flip test_no_mode_errors_polish → test_no_mode_defaults_to_interactive_with_banner in tests/test_tutorial.py** — `89a1bd1` (test)
3. **Task 3: Flip verify_phase8.sh C7 + verify_phase3.sh retro grep target to 'Nie podano trybu'** — `64ec057` (fix)

## Files Created/Modified

- `sphsim/cli/args.py` — Added `import sys`; rewrote Plan 08-02 rationale comment block; replaced `p.error("Musisz podać jeden z trybów: …")` block (lines 201–202) with `args.interactive = True` + 7-line `print(..., file=sys.stderr)` banner listing 4 alternate modes.
- `tests/test_tutorial.py` — Replaced `test_no_mode_errors_polish` (asserted exit != 0 + `Musisz podać jeden z trybów`) with `test_no_mode_defaults_to_interactive_with_banner` (asserts rc==0 + stderr banner + 4 flag names + stdout INTRO via `_run_sph(input='exit\n')`).
- `scripts/verify_phase8.sh` — C7 (lines 112–113) label and grep target flipped: `Musisz podać jeden z trybów` → `Nie podano trybu`; added `echo exit |` pipe to exit the REPL cleanly.
- `scripts/verify_phase3.sh` — D-44 retro check (lines 155–156) label and grep target flipped: `Musisz podać jeden z trybów` → `Nie podano trybu`; added `echo exit |` pipe.

## Decisions Made

- **Banner copy uses `~9 kroków` for --tutorial line** — matches the Plan 08-09 step-count sweep already on disk. Plan 08-10 depends on 08-09 specifically so this literal stays consistent.
- **Banner indentation = 2 spaces + flag, then 3-space gap to description** — chosen to align visually with how argparse `help=` lays out options in the auto-generated --help text. Lines stay under 100 columns.
- **`echo exit |` (not `printf 'exit\n'`)** in verifier piping — shorter, POSIX-equivalent, and consistent with the bash idioms already used elsewhere in verify_phase8.sh categories D and F.
- **Existing post-parse mutex checks (compare-agent, batch, tutorial mutex) UNCHANGED** — they only fire when their specific flags are set, so the no-mode auto-promotion path is orthogonal and cannot collide.

## Deviations from Plan

None — plan executed exactly as written.

The plan-level structural grep expectation "grep -c 'Nie podano trybu' scripts/verify_phase8.sh → 1" actually returns 2 (likewise for verify_phase3.sh) because both scripts have the literal on TWO consecutive lines per check: once in the check description label, once in the `grep -F` target. This is consistent with how the original `Musisz podać jeden z trybów` literal also appeared twice per script (label + grep). All other verify steps PASS, contract is satisfied. Treating as a benign expectation-count nit, not a real deviation.

## Issues Encountered

None — Tasks 1, 2, 3 executed in sequence without rework.

## TDD Gate Compliance

Task 2 was marked `tdd="true"`. Plan ordering (Task 1 implementation, then Task 2 test) means the new test passed on first run rather than going through a RED-fail-then-GREEN cycle. The new test does still exercise the new behavior end-to-end (subprocess against the live REPL with stdin-fed `exit`), so the GREEN gate is honest. The commit chain shows:

- `df3779d` feat(08-10) — implementation (Task 1)
- `89a1bd1` test(08-10) — test flip (Task 2 GREEN)
- `64ec057` fix(08-10) — verifier flip (Task 3)

The `test()` commit follows the `feat()` commit by design here because this is a contract-replacement plan (test had to be flipped to match the new contract, not driven from a failing red).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- UAT Gap 5 closed — bare invocation no longer hostile to new users.
- All Phase 8 wave-7 work in this worktree is complete; 4 modified files reflect the new contract consistently with zero `Musisz podać jeden z trybów` literals remaining anywhere in the repo (verified by `grep -r "Musisz podać jeden z trybów"` returning empty).
- Ready for orchestrator to merge into main and continue with remaining UAT gap closures or Phase 8 verification refresh.

## Self-Check: PASSED

Verified before finalizing summary:
- `[ -f sphsim/cli/args.py ]` FOUND — args.py modified, contains `import sys`, `args.interactive = True`, `Nie podano trybu`; zero `Musisz podać jeden z trybów`.
- `[ -f tests/test_tutorial.py ]` FOUND — contains `test_no_mode_defaults_to_interactive_with_banner` (count=1), zero `test_no_mode_errors_polish`.
- `[ -f scripts/verify_phase8.sh ]` FOUND — contains `Nie podano trybu` (count=2: label+grep), zero `Musisz podać jeden z trybów`.
- `[ -f scripts/verify_phase3.sh ]` FOUND — contains `Nie podano trybu` (count=2: label+grep), zero `Musisz podać jeden z trybów`.
- `git log --oneline | grep df3779d` FOUND — Task 1 commit present.
- `git log --oneline | grep 89a1bd1` FOUND — Task 2 commit present.
- `git log --oneline | grep 64ec057` FOUND — Task 3 commit present.
- `python -m unittest discover tests` → `Ran 261 tests in 28.690s` + `OK`.
- `bash scripts/verify_phase8.sh` → `Phase 8 verification: PASS=34 / FAIL=0`.
- `bash scripts/verify_phase3.sh` → `Phase 3 verification: PASS=20 / FAIL=0`.
- `python scripts/regression_check.py` → `PASS: 8/8`.

---
*Phase: 08-documentation-interactive-tutorial*
*Completed: 2026-05-29*
