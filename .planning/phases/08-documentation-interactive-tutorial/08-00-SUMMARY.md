---
phase: "08"
plan: "00"
subsystem: test-infrastructure
tags: [scaffolding, test-stubs, wave-0, docs-placeholder, verify-skeleton]
dependency_graph:
  requires: []
  provides:
    - tests/test_tutorial.py (TUT-01..TUT-06 stub classes)
    - tests/test_docs.py (DOC-01, DOC-02, EX-01 stub classes)
    - docs/.gitkeep (docs/ directory tracked in git)
    - docs/assets/.gitkeep (docs/assets/ directory tracked in git)
    - scripts/verify_phase8.sh (Phase 8 exit-gate skeleton)
  affects:
    - tests/ (2 new test modules, all stubs)
    - docs/ (new directory tree)
    - scripts/ (new verify script)
tech_stack:
  added: []
  patterns:
    - "@unittest.skip with reason pointing at delivery wave"
    - "self.fail() stub body so decorator removal fails loudly"
    - "verify_phase7.sh top/bottom matter template adapted for Phase 8"
key_files:
  created:
    - tests/test_tutorial.py
    - tests/test_docs.py
    - docs/.gitkeep
    - docs/assets/.gitkeep
    - scripts/verify_phase8.sh
  modified: []
decisions:
  - "All stubs use @unittest.skip + self.fail() — removal of decorator gives loud failure, not silent green (T-08-00-02 mitigation)"
  - "PNG_MAGIC constant defined at module level in test_docs.py for Wave 3 reuse"
  - "verify_phase8.sh placeholder line clearly marks insertion point for Plan 07"
metrics:
  duration: "~5 minutes"
  completed_date: "2026-05-28T17:15:00Z"
  tasks_completed: 2
  files_created: 5
  files_modified: 0
---

# Phase 8 Plan 00: Wave 0 Scaffolding — Test Stubs + docs/ + verify_phase8.sh Summary

Wave 0 scaffolding: 9 @unittest.skip test stubs across 2 new modules (TUT-01..TUT-06, DOC-01/02/EX-01), docs/ + docs/assets/ directory placeholders, and executable verify_phase8.sh skeleton (PASS=0/FAIL=0 exit 0) — all delivered without touching sphsim/ source.

## What Was Built

### Task 1: Test stubs + docs/ placeholders (commit d6cc985)

**5 files created:**

1. `tests/test_tutorial.py` — 5 test classes covering TUT-01..TUT-06:
   - `TestTutorialEntry` (TUT-01): `test_do_tutorial_present_in_repl` — skip: Wave 2 plan 08-04
   - `TestTutorialControls` (TUT-02 + TUT-03): `test_skip_advances_counter`, `test_back_decrements_counter` — skip: Wave 2 plan 08-04
   - `TestTutorialExit` (TUT-04): `test_exit_in_tutorial_does_not_quit_repl` — skip: Wave 2 plan 08-04
   - `TestTutorialCLI` (TUT-05): `test_tutorial_flag_enters_tutorial_mode` — skip: Wave 1 plan 08-02 / Wave 2 plan 08-04
   - `TestTutorialReports` (TUT-06): `test_tutorial_reports_go_to_dedicated_dir` — skip: Wave 1 plan 08-01 / Wave 2 plan 08-04

2. `tests/test_docs.py` — 3 test classes covering DOC-01, DOC-02, EX-01:
   - `TestPrzewodnik` (DOC-01): `test_przewodnik_exists_with_required_sections` — skip: Wave 3 plan 08-06
   - `TestAssets` (DOC-02): `test_assets_pngs_present_and_valid` — skip: Wave 3 plan 08-05
   - `TestExamplesAudit` (EX-01): `test_examples_in_przewodnik_match_uat_sources` — skip: Wave 3 plan 08-06
   - `PNG_MAGIC = b'\x89PNG\r\n\x1a\n'` constant defined at module level

3. `docs/.gitkeep` — empty placeholder, directory tracked in git for Wave 3 content
4. `docs/assets/.gitkeep` — empty placeholder, directory tracked in git for Wave 3 PNG assets

**Verification:** `python3 -m unittest tests.test_tutorial tests.test_docs` → `OK (skipped=9)`

### Task 2: verify_phase8.sh skeleton (commit 3622d75)

**1 file created:**

5. `scripts/verify_phase8.sh` — executable skeleton (chmod +x):
   - Adapted from verify_phase7.sh top matter (lines 1-56) + bottom matter (lines 185-195)
   - All `/tmp/p7_` → `/tmp/p8_` (trap + check() log)
   - All `Phase 7` → `Phase 8` text substitutions
   - Header comment updated for Phase 8 scope
   - Placeholder: `# === Phase 8 checks land here in Plan 07 (verify_phase8 final assembly) ===`
   - No check() invocations — Plan 07 owns that content

**Verification:** `bash scripts/verify_phase8.sh` → PASS=0 / FAIL=0, exit 0

## Stub Taxonomy

| Class | Requirements | Skip Reason |
|-------|-------------|-------------|
| TestTutorialEntry | TUT-01 | Wave 2 — plan 08-04 |
| TestTutorialControls | TUT-02, TUT-03 | Wave 2 — plan 08-04 |
| TestTutorialExit | TUT-04 | Wave 2 — plan 08-04 |
| TestTutorialCLI | TUT-05 | Wave 1 (08-02) + Wave 2 (08-04) |
| TestTutorialReports | TUT-06 | Wave 1 (08-01) + Wave 2 (08-04) |
| TestPrzewodnik | DOC-01 | Wave 3 — plan 08-06 |
| TestAssets | DOC-02 | Wave 3 — plan 08-05 |
| TestExamplesAudit | EX-01 | Wave 3 — plan 08-06 |

## Verification Results

- All 9 test stubs: @unittest.skip with reason, self.fail() body — `python3 -m unittest discover tests` exits 0 (OK, skipped=9)
- No regressions: full test suite still green (existing 21 modules + 2 new all-skipped)
- verify_phase8.sh: `bash scripts/verify_phase8.sh` exits 0, PASS=0 / FAIL=0
- sphsim/ not touched: `git diff HEAD~2 -- sphsim/ | wc -l` = 0

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

All stubs in this plan are intentional scaffolding — by design. Each is tracked above with the downstream wave/plan that will replace it with real assertions.

## Self-Check: PASSED

- FOUND: tests/test_tutorial.py
- FOUND: tests/test_docs.py
- FOUND: docs/.gitkeep
- FOUND: docs/assets/.gitkeep
- FOUND: scripts/verify_phase8.sh
- FOUND: commit d6cc985 (Task 1)
- FOUND: commit 3622d75 (Task 2)
