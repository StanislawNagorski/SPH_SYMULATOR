---
phase: 08-documentation-interactive-tutorial
verified: 2026-05-29T09:51:39Z
status: passed
score: 15/15 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 10/10
  pass_type: gap-closure
  gap_source: 08-UAT.md (5 UAT gaps + d32de87 diag)
  gaps_closed:
    - "Gap 1 — INTRO banner mentions tutorial pointer"
    - "Gap 2 — per-step controls footer prints 'Sterowanie: skip | back | repeat | exit' on every step display"
    - "Gap 3 — tutorial split from 8 → 9 steps (Lista strategii vs Szczegóły strategii)"
    - "Gap 4 — soft-pass steps 7/8 reject typos that SPHShell.default() prints as 'Nieznana komenda'"
    - "Gap 5 — bare `python sph_sim.py` (no mode flag) auto-promotes to --interactive with Polish stderr discovery banner"
  gaps_remaining: []
  regressions: []
evidence_files:
  - sphsim/cli/repl.py
  - sphsim/cli/tutorial.py
  - sphsim/cli/args.py
  - sphsim/cli/main.py
  - sphsim/report/__init__.py
  - docs/PRZEWODNIK.md
  - docs/assets/decision_distribution_naive.png
  - docs/assets/kpi_timeseries_naive.png
  - docs/assets/batch_aggregate_naive.png
  - scripts/verify_phase8.sh
  - scripts/verify_phase3.sh
  - scripts/gen_tutorial_assets.sh
  - tests/test_tutorial.py
  - tests/test_docs.py
probes_executed:
  - command: "bash scripts/verify_phase8.sh"
    result: "PASS=34 / FAIL=0, exit 0"
  - command: "bash scripts/verify_phase3.sh"
    result: "PASS=20 / FAIL=0, exit 0"
  - command: "bash scripts/verify_phase4.sh"
    result: "PASS=21 / FAIL=0, exit 0"
  - command: "bash scripts/verify_phase5.sh"
    result: "PASS=21 / FAIL=0, exit 0"
  - command: "bash scripts/verify_phase6.sh"
    result: "PASS=40 / FAIL=0, exit 0"
  - command: "bash scripts/verify_phase7.sh"
    result: "PASS=32 / FAIL=0, exit 0"
  - command: "bash scripts/verify_phase1.sh"
    result: "FAIL SC#2 (module line-limit); KNOWN DEBT — pre-existing, out of Phase 8 scope (user-approved)"
  - command: "SPHSIM_NO_REPORT=1 python3 -m unittest discover tests"
    result: "Ran 261 tests in 29.168s OK (0 skipped, 0 failed)"
  - command: "python3 scripts/regression_check.py"
    result: "PASS: 8/8 (CLI-04 byte-identical baseline preserved)"
  - command: "printf 'exit\\n' | SPHSIM_NO_REPORT=1 python3 sph_sim.py --interactive"
    result: "INTRO banner contains 'Wpisz `tutorial` żeby uruchomić interaktywny tutorial v1.1 (≤15 min).' — Gap 1 fixed"
  - command: "printf 'tutorial\\nexit\\nexit\\n' | SPHSIM_NO_REPORT=1 python3 sph_sim.py --interactive | grep -c 'Sterowanie: skip | back | repeat | exit'"
    result: "2 (banner + krok 1 display); skip+skip variant yields 4 — Gap 2 fixed"
  - command: "printf 'tutorial\\n[9 skips]\\nexit\\n' | SPHSIM_NO_REPORT=1 python3 sph_sim.py --interactive | grep 'pominięto — krok 9/9'"
    result: "MATCH — Gap 3 (9-step split) fixed"
  - command: "printf 'tutorial\\n[6 skips]\\ntojesttypo\\nexit\\nexit\\n' | SPHSIM_NO_REPORT=1 python3 sph_sim.py --interactive"
    result: "[krok 7/9] still on screen + 'Nieznana komenda' printed + NO '✓ zaliczone — krok 7/9' — Gap 4 fixed"
  - command: "echo exit | python3 sph_sim.py 2>/tmp/p10err.log"
    result: "rc=0; stderr contains 'Nie podano trybu' + 4 alternate flag names — Gap 5 fixed"
  - command: "printf 'tutorial\\nexit\\nexit\\n' | SPHSIM_NO_REPORT=1 python3 sph_sim.py --interactive | grep -c 'INTERAKTYWNY TUTORIAL'"
    result: "1 — CR-01 banner-once regression still passes"
human_verification:
  - test: "≤15-minute new-user onboarding wall-clock check"
    expected: "Walk through `python sph_sim.py --tutorial` end-to-end on a fresh checkout; stopwatch should read ≤15 minutes including PRZEWODNIK.md Lead+Quickstart reading. Note: now 9 steps (was 8) — re-budget if borderline."
    why_human: "Wall-clock timing varies per user and is not stable in CI. Cannot be programmatically verified without an actual human-in-the-loop onboarding session."
  - test: "Polish tone calibration (informal-respectful)"
    expected: "Reader confirms tutorial output, PRZEWODNIK.md prose, and the NEW Gap 5 discovery banner ('Nie podano trybu — uruchamiam tryb interaktywny ...') all match existing REPL message tone (Phase 2 D-30 style — `Wpisz`, `uruchom`, no `Proszę`)."
    why_human: "Voice/register is a style judgement; automated checks verify only string presence, not register quality."
  - test: "Forgiving-shape-match (D-04) hint UX feel post-renumber"
    expected: "Reviewer intentionally fat-fingers each step's command (e.g., `run incentve`, `strategy bogus`, `batch naive --seedz 5`) and confirms hint copy is helpful, not punishing. NOTE: per 08-REVIEW.md WR-03, step 3 (`strategy <name>`) currently accepts ANY name including bogus ones — reviewer should observe the dual 'nie istnieje' + '✓ zaliczone' message and decide whether it feels confusing."
    why_human: "Subjective evaluation of whether hints feel helpful vs. nagging — not a property automatable assertions can capture."
  - test: "docs/assets/*.png visual quality"
    expected: "Reviewer opens each of the 3 PNGs and confirms axes/labels/title are readable and match what the tutorial step describes."
    why_human: "PNG magic bytes are automated (DOC-02); 'does this chart look right' is human."
known_debt:
  - id: "PRE-EX-01"
    issue: "verify_phase1.sh SC#2 fails on 150-line module limit"
    files:
      - "sphsim/cli/repl.py = 696 lines (limit 150)"
      - "sphsim/cli/tutorial.py = 348 lines (limit 150)"
      - "sphsim/cli/output.py = 257 lines (limit 150)"
      - "sphsim/cli/args.py = 243 lines (limit 150)"
      - "sphsim/cli/simulator.py = 175 lines (limit 150)"
      - "sphsim/report/__init__.py = 292 lines (limit 150)"
      - "sphsim/strategies/loader.py = 244 lines (limit 150)"
    decision: "Pre-existing, user-explicitly-approved to continue. Out of Phase 8 scope. Recorded for milestone-closeout retrospective only."
  - id: "REVIEW-WR-01"
    issue: "Gap 5 banner lists --interactive as alternate mode while already running it (5 entries, comment says 4); alignment column drifts"
    files: ["sphsim/cli/args.py:204-215"]
    severity: "warning (08-REVIEW.md)"
    decision: "Cosmetic/pedagogical — does NOT block Gap 5 success criterion. Banner still contains all 4 actually-alternate flag names + the 'Nie podano trybu' header per the contract."
  - id: "REVIEW-WR-02"
    issue: "_last_command_unknown not reset on control-verb branches of precmd — stale True can leak across postcmd early-return; functional impact null today but fragile"
    files: ["sphsim/cli/repl.py:104-147, 152-160"]
    severity: "warning (08-REVIEW.md)"
    decision: "Latent bug only. No observable misbehavior in current code paths (check_step(1, 'tutorial', ...) returns False anyway). Recommend centralized reset at top of precmd in milestone-closeout."
  - id: "REVIEW-WR-03"
    issue: "Step 3 (strategy-details) check_step accepts ANY name including bogus — produces dual 'Strategia <bogus> nie istnieje' + '✓ zaliczone — krok 3/9' messages"
    files: ["sphsim/cli/tutorial.py:295-296"]
    severity: "warning (08-REVIEW.md)"
    decision: "Confirmed live (see human_verification item #3). Does NOT block Gap 3 success criterion (step 3 → step 4 advance works for valid input). Pedagogical drift — recommend tightening to `tokens[1] in strategies_keys` in milestone-closeout."
  - id: "REVIEW-IN-01"
    issue: "Stale step-number comments still reference pre-split 8-step contract: repl.py:610 says 'step 6 jest soft-pass' (now step 7); tutorial.py:6 + :255 say '(1..8)' (now 1..9)"
    files: ["sphsim/cli/repl.py:610", "sphsim/cli/tutorial.py:6", "sphsim/cli/tutorial.py:255"]
    severity: "info (08-REVIEW.md)"
    decision: "Comments only — zero runtime impact. Recommend refresh in milestone-closeout cleanup."
  - id: "REVIEW-IN-02"
    issue: "verify_phase8.sh D3 sends 10 skips for a 9-step tutorial; 10th skip lands as 'Nieznana komenda: skip' but the grep still finds 'krok 9/9' so the check passes"
    files: ["scripts/verify_phase8.sh:122"]
    severity: "info (08-REVIEW.md)"
    decision: "Cosmetic — verifier still PASS=34/0. Drop one skip in milestone-closeout cleanup."
---

# Phase 8: Documentation + Interactive Tutorial — Gap-Closure Verification Report

**Phase Goal:** Nowy użytkownik (student/prowadzący) bez znajomości projektu potrafi w ≤15 minut: (1) przeczytać polski przewodnik `docs/PRZEWODNIK.md` z opisem wszystkich CLI/REPL commands i flag, (2) uruchomić w REPL tryb `tutorial` (lub `python sph_sim.py --tutorial`) i przejść krok-po-kroku przez wszystkie zdolności v1.1 (strategies → custom → agent → env → report → batch) z opcją `skip` per krok, inspirowany scenariuszami z `scripts/uat_*.sh` / `verify_phase*.sh`.

**Verified:** 2026-05-29T09:51:39Z
**Status:** passed (with 4 human verification items deferred to manual VALIDATION)
**Re-verification:** YES — gap-closure pass after 5 UAT gaps surfaced in d32de87 diag (08-UAT.md). Previous initial verification 2026-05-28T19:17:58Z was passed/10-of-10; this pass re-validates against the gap-closure surface plus 5 new gap-closure must-haves added on top of the original 10.

---

## Goal Achievement

### Observable Truths (must-haves) — 10 original + 5 gap-closure

| #   | Truth                                                                                                                                          | Status     | Evidence                                                                                                                                                                                                                                                                                                                                                              |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `docs/PRZEWODNIK.md` exists with all D-11 sections (Lead → Quickstart → Tutorial → Walkthrough → Reference → Theory)                          | VERIFIED   | File exists (259 lines). 7 H2 sections present including `## Szybki start (60 sekund)`, `## Interaktywny tutorial`, `## Opis funkcjonalności v1.1`, `## Referencja`, `## Teoria (krótki opis)`. Sample step heading on line 59 now reads `[krok 1/9 — Baseline]` (was 1/8). verify_phase8.sh A1-A7 PASS.                                                                |
| 2   | REPL `tutorial` command launches the interactive walkthrough (TUT-01)                                                                          | VERIFIED   | `sphsim/cli/repl.py::do_tutorial` at line 624; subprocess test `printf 'tutorial\n…'` shows `INTERAKTYWNY TUTORIAL SPH SYMULATORA v1.1` + `[krok 1/9 — Baseline]`. verify_phase8.sh D1/D2 PASS.                                                                                                                                                                  |
| 3   | `python sph_sim.py --tutorial` CLI flag enters tutorial mode (TUT-05)                                                                          | VERIFIED   | `sphsim/cli/args.py:196` declares `--tutorial`; `sphsim/cli/main.py:65-68` 4th early branch calls `run_repl(start_in_tutorial=True)`. 5-way mutex enforced with verbatim Polish errors. verify_phase8.sh C1-C7 + D7 PASS.                                                                                                                                              |
| 4   | Tutorial covers all 7 v1.1 capability categories (now in 9 steps — was 8; UAT Gap 3 added Lista/Szczegóły strategii split)                     | VERIFIED   | `sphsim/cli/tutorial.py::STEP_TOPICS` defines 9 topics: baseline, strategies, strategy-details, run-strategy, custom, compare, env, report, batch. Subprocess skip walk confirms all 9 steps visited 1→9→`pominięto — krok 9/9. Tutorial zakończony.`                                                                                                                  |
| 5   | Control verbs work: `skip` advances, `back` decrements, `repeat` re-shows, `exit` returns to bare REPL without quitting                        | VERIFIED   | `sphsim/cli/repl.py::precmd` at lines 104-147 implements all 4 verbs returning `''` to short-circuit cmd.Cmd dispatch. CR-01 fix: `emptyline()` override at line 90 prevents banner re-display (count==1 confirmed live).                                                                                                                                              |
| 6   | Tutorial reports land at `./reports/tutorial-<ts>/step-N-<topic>/` (TUT-06); non-tutorial reports unchanged                                    | VERIFIED   | `sphsim/report/__init__.py::write_report` + `write_batch_report` accept `report_dir_override` kwarg. verify_phase8.sh E1+E2 PASS. Regression check 8/8 confirms byte-identical baseline.                                                                                                                                                                              |
| 7   | 3 canonical PNG assets exist with valid magic bytes (DOC-02)                                                                                   | VERIFIED   | `docs/assets/decision_distribution_naive.png` (28843 B), `kpi_timeseries_naive.png` (224654 B), `batch_aggregate_naive.png` (67829 B). All carry `\x89PNG\r\n\x1a\n`. verify_phase8.sh B1-B3 PASS.                                                                                                                                                                    |
| 8   | Every fenced code block in PRZEWODNIK.md cites a real UAT test or verify_phaseN.sh source (D-12, EX-01)                                       | VERIFIED   | tests.test_docs.TestExamplesAudit PASS — all `# Z 08-UAT.md test #N` annotations + `# Z verify_phase1.sh` references resolve.                                                                                                                                                                                                                                          |
| 9   | `scripts/verify_phase8.sh` phase exit gate passes (GATE-01)                                                                                    | VERIFIED   | Ran live this pass: **PASS=34 / FAIL=0, exit 0**. 7 categories (A: 7, B: 3, C: 7, D: 7, E: 2, F: 5, G: 3) all green AFTER gap-closure (D2/D3/D4 now assert 1/9, 9/9, 1/9 literals + 9 skips; C7 asserts 'Nie podano trybu').                                                                                                                                            |
| 10  | No cross-phase regressions: Phases 3-7 verify scripts still pass + full unittest discover green + regression check byte-identical             | VERIFIED   | verify_phase{3..7}.sh all exit 0 (PASS counts: 20, 21, 21, 40, 32). Full suite: **261 tests OK / 0 skipped** (was 259 pre-gap-closure; +2 new gap-closure tests: `test_check_step3_strategy_details`, `test_no_mode_defaults_to_interactive_with_banner` replaced `test_no_mode_errors_polish`, and `test_soft_pass_step_rejects_unknown_command`). regression_check.py PASS=8/8. |
| **GAP-CLOSURE MUST-HAVES (5 new)** |                                                                                                                              |            |                                                                                                                                                                                                                                                                                                                                                                       |
| 11  | (Gap 1) INTRO banner of `--interactive` mode surfaces the `tutorial` entry point so new users discover the ≤15-min onboarding path           | VERIFIED   | `sphsim/cli/repl.py:60` adds `"  Wpisz \`tutorial\` żeby uruchomić interaktywny tutorial v1.1 (≤15 min).\n"` between the existing `help` (line 59) and `exit` (line 61) pointer lines. Spot-check `printf 'exit\n' | python sph_sim.py --interactive` shows the line in INTRO output.                                                                       |
| 12  | (Gap 2) Tutorial control verbs (skip | back | repeat | exit) remain visible throughout the flow — `Sterowanie: skip | back | repeat | exit` prints on every step display, not only the entry banner | VERIFIED   | Module-level constant `_TUTORIAL_CONTROLS_LINE = "Sterowanie: skip | back | repeat | exit"` at `repl.py:68`. Used in 3 source locations: definition + `do_tutorial` banner f-string (line 636) + `_show_tutorial_step` footer (line 609). Spot-check: 1-skip yields 2 occurrences (banner + step 1 display); 2-skip yields 4 (banner + krok 1 + krok 2 + krok 3). |
| 13  | (Gap 3) Tutorial step 2 split into two distinct steps: new step 2 (`Lista strategii`) accepts ONLY `strategies`; new step 3 (`Szczegóły strategii`) accepts `strategy <name>` — total step count 9 (was 8) | VERIFIED   | `sphsim/cli/tutorial.py::STEP_TOPICS` has 9 keys (1..9) with new key 3 'strategy-details'; STEP_TASKS has 9 entries; `TutorialFlow.total = 9` at line 221; `check_step` has 9 distinct branches; step 2 returns `line == 'strategies'`; step 3 returns `len(tokens) >= 2 and tokens[0] == 'strategy'`. Live: `strategies` on step 2 → `✓ zaliczone — krok 2/9`; `strategy incentive` on step 3 → `✓ zaliczone — krok 3/9`. |
| 14  | (Gap 4) `check_step` rejects steps whose REPL output was `Nieznana komenda` — soft-pass steps 7/8 must not accept garbage input              | VERIFIED   | `_last_command_unknown` flag plumbed through 4 sites: `__init__` (line 87), `precmd` reset before dispatch `return line` (line 146), `postcmd` short-circuit guard (lines 158-160), `default()` set (line 649). Live spot-check: `tojesttypo` on step 7 → `Nieznana komenda` printed + `[krok 7/9` still on screen + NO `✓ zaliczone — krok 7/9`. Regression test `test_soft_pass_step_rejects_unknown_command` PASS. |
| 15  | (Gap 5) Bare `python sph_sim.py` (no mode flag) auto-promotes to `--interactive` AND prints Polish stderr discovery banner listing the 4 alternate modes | VERIFIED   | `sphsim/cli/args.py:208` sets `args.interactive = True`; lines 209-215 print 7-line Polish banner to `file=sys.stderr` containing 'Nie podano trybu — uruchamiam tryb interaktywny (REPL).' + 'Dostępne tryby:' + 5 indented mode lines. Live: `echo exit | python sph_sim.py` exits rc=0; stderr has all 4 actually-alternate flag names (`--strategy`, `--custom`, `--batch`, `--tutorial`). Regression test `test_no_mode_defaults_to_interactive_with_banner` PASS. |

**Score:** 15/15 truths verified

### Required Artifacts (Levels 1-3: exists, substantive, wired)

| Artifact                                  | Expected                                                                                                                | Status     | Details                                                                                                                                                                                                                                                                                                                                                |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sphsim/cli/tutorial.py`                  | 9-step pure state machine: TutorialFlow + STEP_TOPICS(9 keys) + STEP_TASKS(9 entries) + check_step(9 branches)          | VERIFIED   | 348 lines. STEP_TOPICS has key 3 'strategy-details'; key 9 'batch'. TutorialFlow.total=9. check_step has 9 `if step_n == N:` branches confirmed by grep. Step 2 tightened to `line == 'strategies'`; step 3 accepts `tokens[0] == 'strategy' and len(tokens) >= 2`. Zero `sphsim.*` imports (circular-import safe).                                          |
| `sphsim/cli/repl.py`                      | SPHShell with INTRO+tutorial pointer + _TUTORIAL_CONTROLS_LINE constant + per-step footer + _last_command_unknown flag | VERIFIED   | 696 lines. INTRO line 60 has tutorial pointer. `_TUTORIAL_CONTROLS_LINE` at line 68 (3 references confirmed: definition + line 609 + line 636). `_last_command_unknown` at 4 logical sites (init=87, precmd reset=146, postcmd guard=158, default set=649). hint set at line 188 `(2, 3, 5, 8)` (was (2,4,7)). `~9 kroków` at lines 625+635. |
| `sphsim/cli/args.py`                      | --tutorial flag + 5-way Polish mutex + Gap 5 auto-promote with Polish stderr banner                                     | VERIFIED   | 243 lines. `import sys` at line 28. Mutex group at line 156. Post-parse no-mode block lines 207-215: sets `args.interactive = True` + prints 7-line Polish banner to stderr with 'Nie podano trybu' header. Zero `Musisz podać jeden z trybów` literals remain anywhere in the file.                                                              |
| `sphsim/cli/main.py`                      | 4th early branch for --tutorial; existing `if args.interactive:` branch unchanged (auto-promote falls through naturally) | VERIFIED   | 203 lines. Lines 65-68 dispatch to `run_repl(start_in_tutorial=True)` before --interactive. Auto-promote path lands on existing line 69 `if args.interactive:` branch — wired correctly.                                                                                                                                                              |
| `sphsim/report/__init__.py`               | write_report + write_batch_report accept report_dir_override kwarg; WR-06 guard against empty/cwd                       | VERIFIED   | 292 lines. Regression PASS=8/8 confirms no behavior change for default branch.                                                                                                                                                                                                                                                                       |
| `docs/PRZEWODNIK.md`                      | Polish user guide; sample step heading updated to `[krok 1/9 — Baseline]`                                              | VERIFIED   | 259 lines. Line 59 reads `[krok 1/9 — Baseline]` (was 1/8). 7 H2 sections present. Lead points at `--tutorial`. 3 `assets/X.png` embeds.                                                                                                                                                                                                                |
| `docs/assets/*.png` (3 files)             | Canonical deterministic PNG assets                                                                                       | VERIFIED   | All 3 PNGs present and valid (`\x89PNG\r\n\x1a\n` magic bytes confirmed); sizes 28.8KB / 224.7KB / 67.8KB.                                                                                                                                                                                                                                              |
| `scripts/verify_phase8.sh`                | Phase exit gate ≥33 check() invocations; D2/D3/D4 updated to /9 contract; C7 asserts 'Nie podano trybu'                | VERIFIED   | 177 lines, 34 check() invocations. Live run: PASS=34/FAIL=0, exit 0. D2=`[krok 1/9`, D3=9 skips + `pominięto — krok 9/9` (sends 10 skips per IN-02, harmless), D4=`✓ zaliczone — krok 1/9`, C7=`Nie podano trybu`.                                                                                                                                |
| `scripts/verify_phase3.sh`                | Retro check at line 156 asserts 'Nie podano trybu' instead of 'Musisz podać jeden z trybów'                            | VERIFIED   | Line 156 grep target flipped to `Nie podano trybu`; uses `echo exit |` stdin pattern. verify_phase3.sh exits 0, PASS=20.                                                                                                                                                                                                                              |
| `tests/test_tutorial.py`                  | TUT-01..TUT-06 active tests + CR-01 + 3 new gap-closure tests + renumbered step tests                                  | VERIFIED   | 865 lines, 48 test methods. `test_soft_pass_step_rejects_unknown_command`, `test_check_step3_strategy_details`, `test_no_mode_defaults_to_interactive_with_banner` all present and PASS individually. All check_step3..8 tests renamed to 4..9. Every `/8` literal in subprocess assertions flipped to `/9`. Zero `test_no_mode_errors_polish` references. |
| `tests/test_docs.py`                      | DOC-01, DOC-02, EX-01 active tests                                                                                       | VERIFIED   | 8 test methods, all green per full discover.                                                                                                                                                                                                                                                                                                            |

### Key Link Verification (Level 3: wiring)

| From                                                                | To                                                                       | Via                                                                | Status   | Details                                                                                                                                                                                                                  |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------ | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sphsim/cli/repl.py::INTRO`                                         | user reading first banner of --interactive boot                          | cmd.Cmd.intro emitted by cmdloop()                                  | WIRED    | Live: `printf 'exit\n' \| python sph_sim.py --interactive` shows `Wpisz \`tutorial\` żeby uruchomić interaktywny tutorial v1.1 (≤15 min).` between help and exit pointer lines.                                          |
| `sphsim/cli/repl.py::_show_tutorial_step`                           | user seeing controls reminder on every step display                       | `print(_TUTORIAL_CONTROLS_LINE)` after bottom rule (line 609)        | WIRED    | Live spot-check yields 2 occurrences for 1-skip session, 4 for 2-skip — matches banner + per-step display.                                                                                                                |
| `sphsim/cli/repl.py::SPHShell.default`                              | `sphsim/cli/repl.py::SPHShell.postcmd`                                   | `self._last_command_unknown` flag short-circuits check_step          | WIRED    | Live: typo on soft-pass step 7 results in `Nieznana komenda` + no `✓ zaliczone` advance. Regression test passes.                                                                                                          |
| `sphsim/cli/args.py::parse_args` (no-mode branch)                   | `sphsim/cli/main.py::main()` (`if args.interactive:` branch)              | `args.interactive = True` set in args.py; existing main.py branch catches | WIRED    | Live: `echo exit \| python sph_sim.py` boots REPL (stdout INTRO banner) + stderr discovery banner; rc=0.                                                                                                                  |
| `sphsim/cli/tutorial.py::STEP_TOPICS`                               | `sphsim/cli/tutorial.py::STEP_TASKS`                                     | key parity — every int key 1..9 in TOPICS appears in TASKS         | WIRED    | `test_step_topics_keys_and_slugs` + `test_step_tasks_have_tutorialstep_instances` pass. range(1, 10) over both.                                                                                                            |
| `sphsim/cli/tutorial.py::check_step`                                | `sphsim/cli/repl.py::SPHShell.postcmd`                                   | step_n routes to per-step branch (1..9)                             | WIRED    | 9 `if step_n == N:` branches confirmed by grep; live step-3 advance + step-4 hint path both observed.                                                                                                                  |
| `sphsim/cli/repl.py::SPHShell.postcmd`                              | `sphsim.cli.tutorial.check_step` for steps 1..9                          | function call with STRATEGIES + BUILTIN_STRATEGIES + _last_sim_result | WIRED    | Step 1 verification fires `✓ zaliczone — krok 1/9` after `run naive zeta=0.75` returns KPI ≥80. Confirmed live in verify_phase8.sh D4.                                                                                  |
| `sphsim/cli/repl.py::do_run/do_compare/do_batch`                    | `sphsim/report/__init__.py::write_report/write_batch_report`             | `report_dir_override=self._tutorial_state.step_report_dir(topic)`    | WIRED    | verify_phase8.sh E1+E2 PASS. Regression 8/8 confirms default branch unchanged.                                                                                                                                          |
| `docs/PRZEWODNIK.md`                                                | `docs/assets/*.png`                                                      | 3 `![Alt](assets/X.png)` markdown image links                       | WIRED    | All 3 image paths resolve; PNGs valid (magic-byte-verified).                                                                                                                                                              |

### Data-Flow Trace (Level 4)

| Artifact                                            | Data Variable                | Source                                                                  | Produces Real Data                                            | Status   |
| --------------------------------------------------- | ---------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------- | -------- |
| `SPHShell.postcmd` (tutorial verification)          | `self._last_sim_result`      | populated by `do_run`/`do_compare`/`do_batch` on success path           | Yes — live: tutorial step 1 reads `avg_val_last100` from real `SPHSimulator.run()` output | FLOWING  |
| `SPHShell.postcmd` (Gap 4 short-circuit)            | `self._last_command_unknown` | populated by `SPHShell.default()` when cmd.Cmd cannot dispatch the line | Yes — live: typo on step 7 results in no advance, flag observed via behavior | FLOWING  |
| `TutorialFlow.step_report_dir(topic)`               | `session_ts` + `step` + `topic` | `datetime.now().strftime(...)` + STEP_TOPICS lookup                     | Yes — verify_phase8.sh E1 confirms physical dir created       | FLOWING  |
| `args.parse_args` (Gap 5 banner)                    | stderr print stream         | `print(..., file=sys.stderr)` of static Polish strings                  | Yes — live: 7 banner lines on stderr captured to /tmp/p10err.log | FLOWING  |
| `docs/PRZEWODNIK.md` Walkthrough commands           | UAT test text                | `.planning/phases/07.1-comprehensive-uat/08-UAT.md` (per D-12)          | Yes — EX-01 audit passes                                       | FLOWING  |
| `docs/assets/*.png`                                 | matplotlib renders           | `gen_tutorial_assets.sh` → `sph_sim.py --strategy naive --seed 42`     | Yes — committed deterministic PNGs                              | FLOWING  |

### Behavioral Spot-Checks (Gap-Closure Specific)

| Behavior                                                                              | Command                                                                                                                        | Result                                                                                | Status |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- | ------ |
| Gap 1: INTRO banner mentions tutorial                                                 | `printf 'exit\n' \| python sph_sim.py --interactive 2>&1 \| grep -F 'Wpisz `tutorial`'`                                          | MATCH (1 line)                                                                         | PASS   |
| Gap 2: per-step controls footer for 1-skip session                                    | `printf 'tutorial\nexit\nexit\n' \| python sph_sim.py --interactive 2>&1 \| grep -c 'Sterowanie: skip'`                          | 2 (banner + krok 1 display)                                                            | PASS   |
| Gap 2: per-step controls footer for 2-skip session                                    | `printf 'tutorial\nskip\nskip\nexit\nexit\n' \| python sph_sim.py --interactive 2>&1 \| grep -c 'Sterowanie: skip'`              | 4 (banner + krok 1 + krok 2 + krok 3)                                                  | PASS   |
| Gap 3: 9-step state machine total                                                     | `printf 'tutorial\n[9×skip]\nexit\n' \| python sph_sim.py --interactive 2>&1 \| grep 'pominięto — krok 9/9'`                     | MATCH `⤼ pominięto — krok 9/9. Tutorial zakończony.`                                  | PASS   |
| Gap 3: step 2 → step 3 advance via `strategies` → `strategy incentive`                | `printf 'tutorial\nskip\nstrategies\nstrategy incentive\nexit\nexit\n' \| python sph_sim.py --interactive`                       | `✓ zaliczone — krok 2/9` then `✓ zaliczone — krok 3/9` then `[krok 4/9 — Inna strategia]` | PASS   |
| Gap 4: typo on soft-pass step 7 rejected                                              | `printf 'tutorial\n[6×skip]\ntojesttypo\nexit\nexit\n' \| python sph_sim.py --interactive`                                       | `[krok 7/9 — Override środowiska]` + `Nieznana komenda: 'tojesttypo'` + NO `✓ zaliczone — krok 7/9` | PASS   |
| Gap 5: bare invocation auto-promotes                                                  | `echo exit \| python sph_sim.py 2>/tmp/p10err.log; echo rc=$?`                                                                  | `rc=0`; stderr has 'Nie podano trybu' + `--strategy` + `--custom` + `--batch` + `--tutorial`; stdout has INTRO + `Do widzenia.` | PASS   |
| CR-01 (regression from initial verification): tutorial banner shown exactly once     | `printf 'tutorial\nexit\nexit\n' \| python sph_sim.py --interactive 2>&1 \| grep -c 'INTERAKTYWNY TUTORIAL'`                    | 1                                                                                      | PASS   |

### Probe Execution

| Probe                                              | Command                                                       | Result                                                  | Status |
| -------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------- | ------ |
| Phase 8 exit gate                                  | `bash scripts/verify_phase8.sh`                              | PASS=34 / FAIL=0, exit 0                                | PASS   |
| Phase 3 exit gate (cross-phase)                    | `bash scripts/verify_phase3.sh`                              | PASS=20 / FAIL=0, exit 0                                | PASS   |
| Phase 4 exit gate (cross-phase)                    | `bash scripts/verify_phase4.sh`                              | PASS=21 / FAIL=0, exit 0                                | PASS   |
| Phase 5 exit gate (cross-phase)                    | `bash scripts/verify_phase5.sh`                              | PASS=21 / FAIL=0, exit 0                                | PASS   |
| Phase 6 exit gate (cross-phase)                    | `bash scripts/verify_phase6.sh`                              | PASS=40 / FAIL=0, exit 0                                | PASS   |
| Phase 7 exit gate (cross-phase)                    | `bash scripts/verify_phase7.sh`                              | PASS=32 / FAIL=0, exit 0                                | PASS   |
| Phase 1 exit gate (cross-phase)                    | `bash scripts/verify_phase1.sh`                              | FAIL SC#2 (module line-limit) — KNOWN DEBT pre-existing | KNOWN-DEBT (out of Phase 8 scope, user-approved) |
| CLI-04 byte-identical regression                   | `python3 scripts/regression_check.py`                        | PASS: 8/8                                               | PASS   |
| Full unittest discover                             | `SPHSIM_NO_REPORT=1 python3 -m unittest discover tests`      | Ran 261 tests OK (0 skipped, 0 failed)                  | PASS   |

**Probe totals:** 168 cross-phase check() invocations across Phases 3-7 + 261 tests + 8 regression fixtures — all green. Phase 1's SC#2 line-limit failure is pre-existing technical debt, user-explicitly-approved, and out of Phase 8 scope per orchestrator instructions.

### Requirements Coverage Matrix

Phase 8 introduces no new REQUIREMENTS.md REQ-IDs; instead it uses validation-level IDs from `08-VALIDATION.md` and the tutorial EXERCISES the 27 v1.1 REQ-IDs (Phases 1-7).

| Requirement | Source             | Description                                                                                       | Status | Evidence                                                                                                                                                                                                                |
| ----------- | ------------------ | ------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TUT-01      | 08-VALIDATION.md   | Tutorial entry guarded against re-entry                                                            | MET    | `do_tutorial` checks `if self._tutorial_state is not None`. TestTutorialEntry classes pass. Gap 1 (08-08) added INTRO discoverability without breaking re-entry guard.                                                |
| TUT-02      | 08-VALIDATION.md   | `skip` advances step counter, never auto-runs                                                      | MET    | `precmd` lines 110+ advance step on skip; never invokes simulator. Gap 3 (08-09) updated to total=9; D3 9-skip walk reaches `pominięto — krok 9/9`.                                                                  |
| TUT-03      | 08-VALIDATION.md   | `back` decrements without resetting REPL state                                                     | MET    | TestTutorialControls.test_back_decrements_counter + test_back_at_step_one_boundary PASS; D5 PASS.                                                                                                                       |
| TUT-04      | 08-VALIDATION.md   | `exit` in tutorial drops to bare REPL, NOT process exit                                            | MET    | D6 PASS (`Tutorial opuszczony`).                                                                                                                                                                                         |
| TUT-05      | 08-VALIDATION.md   | `--tutorial` flag dispatches `run_repl(start_in_tutorial=True)` and respects 5-way mutex          | MET    | TestTutorialCLI 9/9 PASS; verify_phase8.sh C1-C7 + D7 PASS.                                                                                                                                                              |
| TUT-06      | 08-VALIDATION.md   | Reports land under `./reports/tutorial-<ts>/step-N-<topic>/` via base-dir override                | MET    | TestTutorialReports 3/3 PASS; verify_phase8.sh E1+E2 PASS.                                                                                                                                                               |
| DOC-01      | 08-VALIDATION.md   | `docs/PRZEWODNIK.md` exists with all D-11 sections                                                | MET    | 259 lines, ≥5 H2 sections, Lead points at `--tutorial`. TestPrzewodnik PASS; verify_phase8.sh A1-A7 PASS.                                                                                                                |
| DOC-02      | 08-VALIDATION.md   | `docs/assets/*.png` (3 PNGs) present + valid PNG headers                                          | MET    | All 3 PNGs >1KB with `\x89PNG` magic bytes. TestAssets PASS; verify_phase8.sh B1-B3 PASS.                                                                                                                                |
| EX-01       | 08-VALIDATION.md   | Every fenced code block in PRZEWODNIK.md is parseable                                              | MET    | TestExamplesAudit PASS.                                                                                                                                                                                                  |
| GATE-01     | 08-VALIDATION.md   | `scripts/verify_phase8.sh` exit gate PASS                                                          | MET    | 34 check() invocations across 7 categories; live run PASS=34/FAIL=0 exit 0 AFTER gap-closure literal updates.                                                                                                            |
| **Exercised via tutorial** |     |                                                                                                   |        |                                                                                                                                                                                                                          |
| CLI-04      | REQUIREMENTS.md    | v1.0 backwards-compat                                                                              | EXERCISED | Tutorial step 1 anchors baseline; regression_check.py PASS=8/8 hard-locks invariant.                                                                                                                                  |
| STRAT-01/02 | REQUIREMENTS.md    | strategies browser                                                                                 | EXERCISED | Tutorial step 2 (`strategies`) — NOW LIST-ONLY post-Gap 3.                                                                                                                                                              |
| STRAT-02    | REQUIREMENTS.md    | strategies browser (details)                                                                       | EXERCISED | NEW Tutorial step 3 (`strategy <name>`) post-Gap 3 split. Test test_check_step3_strategy_details PASS.                                                                                                                  |
| STRAT-03/04/05 | REQUIREMENTS.md | custom loader                                                                                       | EXERCISED | Tutorial step 5 (was 4) post-renumber.                                                                                                                                                                                   |
| AGENT-01..05 | REQUIREMENTS.md   | rational agent                                                                                     | EXERCISED | Tutorial step 6 (was 5) post-renumber.                                                                                                                                                                                   |
| ENV-01/02/03 | REQUIREMENTS.md   | configurable env                                                                                   | EXERCISED | Tutorial step 7 (was 6) post-renumber — soft-pass; Gap 4 now rejects typos here.                                                                                                                                       |
| REPORT-01..03 + PLOT-01..03 | REQUIREMENTS.md | report + plots always                                                                          | EXERCISED | Tutorial step 8 (was 7) post-renumber.                                                                                                                                                                                  |
| BATCH-01..03 + PLOT-04 | REQUIREMENTS.md | batch runner                                                                                       | EXERCISED | Tutorial step 9 (was 8) post-renumber.                                                                                                                                                                                  |
| CLI-01 (REQ-ID, see Plan 10) | REQUIREMENTS.md | User may launch interactive mode                                                                | MET    | Gap 5 makes bare invocation also boot --interactive (auto-promote). Existing `--interactive` flag still works.                                                                                                          |
| CLI-02 (REQ-ID, see Plan 10) | REQUIREMENTS.md | `help` lists commands                                                                            | MET    | INTRO banner now also points at `tutorial` (Gap 1) so help+tutorial+exit are all discoverable from first banner.                                                                                                       |

**Coverage assessment:** All 10 Phase 8 validation-level IDs MET. Gap-closure satisfies all 5 UAT-discovered gaps. All 27 v1.1 REQ-IDs from Phases 1-7 are exercised by at least one tutorial step. No orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none in Phase 8 gap-closure modified files) | — | TBD/FIXME/XXX/TODO/HACK debt markers | — | Zero debt markers across all 10 Phase 8 gap-closure source/script/doc/test files (verified by grep on `TBD|FIXME|XXX` and `TODO|HACK|PLACEHOLDER`). The phase ships with no unresolved debt markers introduced by the gap-closure pass. |

### Gap-Closure Resolution Summary (UAT → Code)

| UAT Test | Gap | Resolution Commits | Verified Live |
| -------- | --- | ------------------ | ------------- |
| 08-UAT.md Test #1 | Gap 1: INTRO banner mentions tutorial pointer | `cab7bfc` (08-08 Task 1 EDIT 1) | `printf 'exit\n' | python sph_sim.py --interactive` shows `Wpisz \`tutorial\` żeby uruchomić ...` |
| 08-UAT.md Test #2 | Gap 2: per-step controls footer + DRY constant | `cab7bfc` (08-08 Task 1 EDITs 2+3) | 2 occurrences for 1-skip; 4 for 2-skip |
| 08-UAT.md Test #2 | Gap 3: step 2 split into 2+3 (total = 9) | `b672654`+`963e7cd`+`9bc907d`+`25beb53`+`36de02a` (08-09 Tasks 1-5) | `pominięto — krok 9/9` reached; step 3 `Szczegóły strategii` rendered |
| 08-UAT.md Test #2 | Gap 4: soft-pass typo rejection via `_last_command_unknown` | `cab7bfc` (08-08 Task 1 EDIT 4) + `c76ce02` (test) | `tojesttypo` on step 7 → `Nieznana komenda` + no advance |
| 08-UAT.md Test #3 | Gap 5: bare `sph_sim.py` auto-promotes + Polish banner | `df3779d`+`89a1bd1`+`64ec057` (08-10 Tasks 1-3) | `echo exit | python sph_sim.py` → rc=0, stderr banner with 4 alternate flags |

All 5 UAT gaps from the diagnose pass (d32de87) now have resolution evidence in the codebase AND end-to-end live verification.

### Human Verification Required

Four wall-clock and UX-quality items remain for manual VALIDATION (per 08-VALIDATION.md §Manual-Only Verifications), updated to reflect the post-gap-closure surface (9 steps instead of 8; new Gap 5 banner; Gap 4 hint behavior).

#### 1. ≤15-minute new-user onboarding wall-clock check (now 9 steps)

**Test:** Walk through `python sph_sim.py --tutorial` end-to-end on a fresh checkout. Start a stopwatch when launching; stop when the tutorial prints `✓ zaliczone — krok 9/9. Tutorial ukończony!` (or `pominięto — krok 9/9. Tutorial zakończony.`).
**Expected:** Total elapsed time ≤15 minutes including reading PRZEWODNIK.md Lead+Quickstart.
**Why human:** Wall-clock timing varies per user and is not stable in CI; cannot be programmatically verified.
**Goal-backward plausibility (this verifier):** Still PASS. Content density: ~32 words/step × 9 steps ≈ 290 words (vs ~260 previously). At 200 wpm Polish reading: ~1.45 min content reading. Simulator runs ~1-2 sec each. Per-step user time: 60-90 sec. Total: 9-14 min. Headroom for PRZEWODNIK Lead+Quickstart ~2-3 min. The ≤15-min budget is achievable but slightly tighter than the 8-step version — needs single human confirmation.

#### 2. Polish tone calibration (informal-respectful) — now includes Gap 5 discovery banner

**Test:** Reader (Polish speaker) reads tutorial output + PRZEWODNIK.md + the new Gap 5 discovery banner (`Nie podano trybu — uruchamiam tryb interaktywny ...`) and confirms tone matches existing REPL messages (Phase 2 D-30 style — `Wpisz`, `uruchom`, no `Proszę`).
**Expected:** Informal-respectful register; no shift to overly formal or overly casual.
**Why human:** Style judgement; automated only checks string presence, not voice quality.

#### 3. Forgiving-shape-match (D-04) hint UX feel post-renumber + WR-03 dual-message check

**Test:** Reviewer intentionally fat-fingers each step's command (e.g., `run incentve` on step 1, `strategy bogus` on step 3, `batch naive --seedz 5` on step 9) and confirms hint copy is helpful, not punishing. Additionally, observe the WR-03 dual message on step 3 with `strategy bogus`: `Strategia 'bogus' nie istnieje. Dostępne: ...` followed immediately by `✓ zaliczone — krok 3/9`.
**Expected:** Hint emitted is informative; `MAX_HINTS=3` then `Wskazówka: Wpisz \`skip\`` fallback feels appropriate. Reviewer decides whether the step-3 dual-message (08-REVIEW.md WR-03) is acceptable for v1.1 or must be tightened.
**Why human:** Whether hints feel helpful vs nagging is subjective; whether the contradictory step-3 messages confuse new users is a UX judgment.

#### 4. PNG visual quality

**Test:** Reviewer opens each of `docs/assets/decision_distribution_naive.png`, `kpi_timeseries_naive.png`, `batch_aggregate_naive.png` and confirms axes/labels/title are readable and match what the tutorial step describes.
**Expected:** Charts match the canonical baseline (naive --zeta 0.75 --seed 42).
**Why human:** PNG byte-determinism is automated (DOC-02); "does this chart look right" is human.

### Goal-Backward Gap Analysis

| Question                                                            | Answer                                                                                                                                                                                                                                                                                |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Are all 5 UAT-surfaced gaps resolved?                              | YES. Each gap has codebase evidence (commit chain) AND end-to-end live verification (subprocess spot-check). See "Gap-Closure Resolution Summary" table.                                                                                                                              |
| Is the 15-minute estimate still plausible after the 8→9 split?     | YES. Adds ~1 min content + ~1 min interaction. Total 9-14 min, still within budget. Needs single human confirmation.                                                                                                                                                                  |
| Are all 7 v1.1 capability categories exercised in the 9 steps?     | YES. STEP_TOPICS post-split: baseline (CLI-04), strategies+strategy-details (STRAT-01/02), run-strategy (STRAT-02), custom (STRAT-03..05), compare (AGENT-01..05), env (ENV-01..03), report (REPORT-01..03 + PLOT-01..03), batch (BATCH-01..03 + PLOT-04).                            |
| Did the gap-closure introduce any cross-phase regressions?          | NO. Phases 3-7 verify scripts still PASS. Full 261-test suite green. Regression check 8/8 byte-identical.                                                                                                                                                                              |
| Does the gap-closure preserve CLI-04 backwards-compat?              | YES. regression_check.py PASS=8/8 byte-identical for all 5 baseline strategies with --seed 42. Auto-promote path (Gap 5) is never triggered by explicit-flag invocations.                                                                                                              |
| Are there orphaned tests or stale literal references after Gap 3? | Mostly NO — but **REVIEW-IN-01** flags stale comment references (`step 6 jest soft-pass` at repl.py:610, `(1..8)` at tutorial.py:6+:255). Comments only — zero runtime impact, recorded as known debt for milestone-closeout cleanup.                                                |
| Were any UAT gap-closure must-haves missed?                         | NO. All 5 must-haves (Gaps 1-5) plus all 10 original must-haves are VERIFIED.                                                                                                                                                                                                          |

### Gaps Summary

**No blocker or warning gaps remain that block goal achievement.** All 15 must-haves (10 original + 5 gap-closure) verified through three artifact levels (exists, substantive, wired) plus Level-4 data-flow trace where applicable. Every UAT-surfaced gap has corresponding codebase evidence AND live behavioral confirmation.

The 08-REVIEW.md gap-closure pass logged 3 WARNINGS (WR-01 banner self-listing, WR-02 _last_command_unknown leak, WR-03 step-3 bogus-name accept) + 5 INFO items (IN-01..IN-05). None of these block the Phase 8 goal. They are explicitly classified as quality/polish issues for milestone-closeout cleanup and recorded in the `known_debt` frontmatter section above. The two most user-visible (WR-01 banner cosmetic + WR-03 step-3 dual message) are surfaced into Human Verification Item #2 and #3 so a Polish-speaking reviewer can decide whether they warrant immediate fix or v1.2 deferral.

Pre-existing known debt: `verify_phase1.sh SC#2` line-limit failure across 7 sphsim modules is OUT OF SCOPE for this gap-closure pass (user-explicitly-approved per orchestrator context) and recorded as `known_debt: PRE-EX-01`.

### Overall Verdict

**STATUS: passed** with 4 human verification items deferred to manual VALIDATION (wall-clock + UX-feel + visual). The gap-closure delivers all 5 UAT-requested behaviors AND preserves all original Phase 8 must-haves:

- **Discoverability:** INTRO banner advertises `tutorial`; bare invocation auto-promotes to --interactive with stderr discovery banner; controls footer prints on every tutorial step.
- **Pedagogical clarity:** Tutorial split from 8 to 9 steps separating "list strategies" from "view one's details", matching natural discovery flow.
- **Input hygiene:** Soft-pass steps 7/8 reject `Nieznana komenda` typos via `_last_command_unknown` flag — no more false `✓ zaliczone` on garbage.
- **Cross-phase integrity:** All Phases 3-7 verifiers + full 261-test suite + CLI-04 regression baseline still green. Zero debt markers in any modified file.

The phase ships with 3 documented WARNING-level review findings (WR-01/02/03 in 08-REVIEW.md) tracked as `known_debt` for milestone-closeout — none of them block the Phase 8 goal as observed end-to-end in this verification pass.

### Recommended Next Step

**Proceed to milestone v1.1 closeout.** Phase 8 (gap-closure pass) is complete; with all 8 phases verified (Phases 1-7 initially + Phase 8 initial 2026-05-28 + Phase 8 gap-closure 2026-05-29), the milestone is ready for `/gsd:complete-milestone` after human verification items #1–4 are confirmed by a Polish-speaking reviewer doing one fresh-checkout walkthrough. The known-debt items (REVIEW-WR-01/02/03, REVIEW-IN-01/02, PRE-EX-01 line-limit) should be triaged at milestone-closeout: WR-03 (step-3 bogus-name accept) is the most user-visible and recommended for a small follow-up plan before v1.1 release; WR-01 cosmetic and IN-01 stale comments are good first-issues for milestone cleanup; PRE-EX-01 line-limit is a v1.2 refactor candidate.

---

_Verified: 2026-05-29T09:51:39Z_
_Verifier: Claude (gsd-verifier, goal-backward stance, gap-closure re-verification)_
_Re-verification: YES — gap-closure pass after 5 UAT gaps surfaced in d32de87 diag. Previous initial verification 2026-05-28T19:17:58Z. Both passes report `status: passed` with the same 4 human verification items (wall-clock + tone + UX-feel + PNG visual)._
