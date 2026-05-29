---
status: resolved
phase: 08-documentation-interactive-tutorial
source: [08-00-SUMMARY.md, 08-01-SUMMARY.md, 08-02-SUMMARY.md, 08-03-SUMMARY.md, 08-04-SUMMARY.md, 08-05-SUMMARY.md, 08-06-SUMMARY.md, 08-07-SUMMARY.md]
resolved_by: [08-08-SUMMARY.md, 08-09-SUMMARY.md, 08-10-SUMMARY.md]
started: 2026-05-28T21:30:00Z
updated: 2026-05-29T11:35:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: From a clean shell, `python sph_sim.py --interactive` boots cleanly, Polish INTRO banner appears, `(sph)` prompt is reachable, `help` lists the `tutorial` command, `exit` quits cleanly.
result: issue
reported: "nie ma wzmianki o tutorialu (after booting --interactive — banner shows only `help` and `exit` pointers, no mention of the new `tutorial` entry point)"
severity: major

### 2. `--tutorial` CLI Flag Entry
expected: `python sph_sim.py --tutorial` enters tutorial mode end-to-end — Polish header `INTERAKTYWNY TUTORIAL SPH SYMULATORA v1.1` appears, sterowanie line lists `skip | back | repeat | exit`, step 1/8 (`baseline`) task description is shown, prompt waits for input.
result: pass
notes: "User passed entry, raised 3 adjacent gaps logged separately (controls visibility throughout tutorial; split step 2 into list+details; reject 'nieznana komenda' as non-pass)."

### 3. REPL `tutorial` Discoverability
expected: Inside `python sph_sim.py --interactive`, `help` shows the line `tutorial — Uruchom interaktywny tutorial v1.1 (≤15 min).`. Typing `tutorial` then enters the same tutorial banner + step 1/8 as test 2.
result: pass
notes: "User passed and raised 1 adjacent gap: default to --interactive when no mode is provided + print info banner listing other modes with one-sentence descriptions."

### 4. Step Verification (✓ zaliczone)
expected: On tutorial step 1 (baseline), type `run naive --zeta 0.75 --seed 42 --no-agent`. After the simulation completes, the REPL prints `✓ zaliczone — krok 1/8` and auto-advances to step 2.
result: pass

### 5. `skip` Control Verb
expected: Type `skip` in the tutorial — the step counter advances (`pominięto — krok N/8` printed) and step N+1's task description appears. Repeat until step 8; on the last skip, prints `pominięto — krok 8/8. Tutorial zakończony.` and tutorial state clears.
result: pass

### 6. `back` Boundary Check
expected: On step 1, type `back` — REPL prints `Już jesteś na pierwszym kroku.` and stays on step 1 (no counter decrement, no crash). After advancing to step 2 (via skip), `back` prints `cofnięto do kroku 1/8` and returns to step 1.
result: pass

### 7. `exit` in Tutorial Preserves REPL
expected: Inside tutorial mode, type `exit` — prints `Tutorial opuszczony na kroku N/8. Stan REPL zachowany ...` AND `Wpisz \`exit\` ponownie żeby zakończyć REPL.`. The REPL stays open at `(sph)` prompt. A second `exit` quits with `Do widzenia.`.
result: pass

### 8. Tutorial Reports Go to Dedicated Namespace
expected: From a clean state, run `python sph_sim.py --tutorial`, complete step 1 with `run naive --zeta 0.75 --seed 42 --no-agent`, then `exit` `exit`. Check `ls reports/` — a `tutorial-<ts>/step-1-baseline/` directory exists with `report.md` inside; NO sibling plain `<ts>/` directory was created.
result: pass

### 9. Polish Mutex Error
expected: Run `python sph_sim.py --tutorial --interactive` — exits with non-zero status and stderr contains the Polish error `Flagi --tutorial i --interactive są wzajemnie wykluczające.` (NOT English "argument --interactive: not allowed with argument").
result: pass

### 10. `docs/PRZEWODNIK.md` Content & Structure
expected: Open `docs/PRZEWODNIK.md` in a Markdown viewer (or `cat`). The Lead (first ~10 lines) mentions `python sph_sim.py --tutorial`. The 5 H2 sections appear in order: `## Szybki start`, `## Interaktywny tutorial`, `## Opis funkcjonalności v1.1`, `## Referencja`, `## Teoria`. The 3 PNG embeds (`assets/decision_distribution_naive.png`, `assets/kpi_timeseries_naive.png`, `assets/batch_aggregate_naive.png`) render as images (not broken-image icons).
result: pass

### 11. PNG Visual Quality
expected: The 3 charts embedded in `docs/PRZEWODNIK.md` (decision distribution bar chart, KPI timeseries line plot, batch aggregate box-plot) look correct — axes labeled, no rendering glitches, content matches the surrounding Polish prose description. (Subjective "looks right" check per 08-VERIFICATION.md manual item.)
result: pass

### 12. `verify_phase8.sh` Exit Gate
expected: Run `bash scripts/verify_phase8.sh`. Output ends with `Phase 8 verification: PASS=34 / FAIL=0`, the line `✓ Phase 8 ready for /gsd:verify-work`, and exit code 0. No leftover `./reports/` directory after the script completes.
result: pass

### 13. ≤15-Minute Onboarding Goal
expected: Starting from a fresh checkout (or `git clone`), a new Polish-speaking user follows `docs/PRZEWODNIK.md` Lead → `python sph_sim.py --tutorial` and completes all 8 steps in ≤15 minutes wall-clock. (Subjective wall-clock check per 08-VERIFICATION.md manual item — the goal-level success criterion for Phase 8.)
result: pass

## Summary

total: 13
passed: 12
issues: 5
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "INTRO banner of `--interactive` mode surfaces the new `tutorial` entry point so new users can discover the ≤15-min onboarding path"
  status: resolved
  reason: "User reported: nie ma wzmianki o tutorialu (after booting --interactive — banner shows only `help` and `exit` pointers, no mention of the new `tutorial` entry point)"
  severity: major
  test: 1
  root_cause: "INTRO string literal in sphsim/cli/repl.py (lines 52–62) was built before Phase 8 added the `tutorial` command and was never updated; mentions only `help` and `exit` pointers."
  artifacts:
    - path: "sphsim/cli/repl.py"
      issue: "INTRO constant lines 52–62 lists only `help` (line 59) and `exit` (line 60) pointers; no `tutorial` pointer. INTRO is bound to cmd.Cmd.intro at line 68 and emitted by cmdloop() on --interactive boot."
  missing:
    - "Insert single Polish line between current line 59 and line 60 of INTRO tuple: `  Wpisz \\`tutorial\\` żeby uruchomić interaktywny tutorial v1.1 (≤15 min).\\n`"
  debug_session: ""

- truth: "Tutorial control verbs (skip | back | repeat | exit) remain visible to the user throughout the tutorial flow, not only in the one-time entry banner"
  status: resolved
  reason: "User reported: nigdzie w tutorialu nie ma informacji o liniach sterowania (controls appear once in the banner then disappear; subsequent step displays don't remind the user that skip/back/repeat/exit are available)"
  severity: minor
  test: 2
  root_cause: "_show_tutorial_step() in sphsim/cli/repl.py prints title + top rule + description + bottom rule then returns — no controls footer. The `Sterowanie: skip | back | repeat | exit` line lives only in the entry banner inside do_tutorial (line 608) and never reappears."
  artifacts:
    - path: "sphsim/cli/repl.py"
      issue: "_show_tutorial_step() at lines 567–581 — missing controls footer print after bottom rule."
    - path: "sphsim/cli/repl.py"
      issue: "Controls string `Sterowanie: skip | back | repeat | exit` is defined only inline at line 608 inside do_tutorial; should be extracted to a module-level constant for DRY reuse."
  missing:
    - "Extract `Sterowanie: skip | back | repeat | exit` into a module-level constant `_TUTORIAL_CONTROLS_LINE` in sphsim/cli/repl.py."
    - "Reuse the constant in do_tutorial banner (line 608) and append one print of the constant after line 581 (bottom rule) in _show_tutorial_step()."
  debug_session: ""

- truth: "Step 2 of the tutorial is split into two distinct steps: (a) list strategies via `strategies`, (b) view details via `strategy <nazwa>`"
  status: resolved
  reason: "User requested: rozbij krok 2 na 2 osobne — jeden wyświetl strategie, drugi zobacz szczegóły (current step 2 conflates both verbs into one display-only step; user wants them as two separate steps, raising total step count from 8 to 9)"
  severity: major
  test: 2
  root_cause: "Scope change (not a bug): current STEP_TASKS[2] intentionally conflates `strategies` listing + `strategy <name>` details via check_step branch `line == 'strategies' or line.startswith('strategy ')`. User wants two separate steps, requiring renumbering 3..8 → 4..9 and total = 9."
  artifacts:
    - path: "sphsim/cli/tutorial.py"
      issue: "STEP_TOPICS (lines 35–44) needs new key 3 'strategy-details'; old 3..8 shift to 4..9. STEP_TASKS (lines 64–187) — split current key 2 into list-only step 2 + new step 3 (details); renumber 3..8 → 4..9 including each TutorialStep.step_num field. TutorialFlow.total (line 207) 8 → 9. check_step (lines 265–323) — add new step 3 branch, tighten step 2 to `line == 'strategies'` only, renumber all other branches."
    - path: "sphsim/cli/repl.py"
      issue: "Hint-set `ts.step in (2, 4, 7)` (line 164) renumbered to `(2, 3, 5, 8)`. Literal strings `~8 kroków` (lines 597, 607) → `~9 kroków`. All other f-strings render `/{ts.total}` dynamically — self-update."
    - path: "scripts/verify_phase8.sh"
      issue: "D2/D4 grep targets `1/8` → `1/9`; D3 currently uses 8 `skip` lines to reach `pominięto — krok 8/8` → needs 9 skips and assertion `pominięto — krok 9/9` (lines 120, 122, 124)."
    - path: "tests/test_tutorial.py"
      issue: "All `/8` literals in step-count assertions → `/9`. test_tutorialflow_defaults asserts tf.total == 9. test_step_topics_keys_and_slugs + test_step_tasks_have_tutorialstep_instances updated for 9 entries with new slug at key 3. test_check_step2_strategies must now FAIL on `strategy incentive` (no longer dual-purpose). Renumber test_check_stepN_* tests 3..8 → 4..9."
    - path: "docs/PRZEWODNIK.md"
      issue: "Sample step heading `[krok 1/8 — Baseline]` (line 59) → `[krok 1/9 — Baseline]`."
  missing:
    - "Split STEP_TOPICS/STEP_TASKS at key 2; insert new key 3 'strategy-details' with Polish copy (title 'Szczegóły strategii', description teaching `strategy incentive`)."
    - "Tighten check_step step 2 verifier to `line == 'strategies'`; add new step 3 verifier `len(tokens) >= 2 and tokens[0] == 'strategy'`."
    - "Renumber STEP_TASKS keys 3..8 → 4..9 + each TutorialStep.step_num; renumber check_step branches; set TutorialFlow.total = 9."
    - "Update repl.py hint-set + `~8 kroków` literals."
    - "Update verify_phase8.sh D2/D3/D4 step-count literals + add extra skip line in D3."
    - "Update test_tutorial.py global `/8` → `/9` literals + restructure step-2 test + add test_check_step3_strategy_details."
    - "Update docs/PRZEWODNIK.md sample step heading."
  debug_session: ""

- truth: "check_step rejects steps whose REPL output is 'nieznana komenda' (unknown command) — soft-pass steps must not accept garbage input"
  status: resolved
  reason: "User reported: jeśli wynikiem testu jest 'nieznana komenda' nie akceptuj kroku jako zaliczone (current soft-pass logic on steps 6 and 7 returns True for any non-empty line, including typos that SPHShell rejects with 'nieznana komenda')"
  severity: major
  test: 2
  root_cause: "SPHShell.default() (repl.py:616) prints `Nieznana komenda: ...` but sets no instance flag, so postcmd cannot distinguish 'user ran a real command' from 'user typed garbage cmd.Cmd refused to parse'. Combined with soft-pass branches in check_step (tutorial.py:309, 315) returning `bool(line)` for any non-empty input, tutorial falsely advances on typos."
  artifacts:
    - path: "sphsim/cli/repl.py"
      issue: "default() at lines 615–621 prints Polish message but does not record that the line was unrecognized."
    - path: "sphsim/cli/repl.py"
      issue: "postcmd at lines 138–149 always calls check_step for non-empty lines, regardless of whether the previous command was a known REPL verb."
    - path: "sphsim/cli/repl.py"
      issue: "__init__ at line 77 initializes only _last_sim_result; no _last_command_unknown attribute exists."
    - path: "sphsim/cli/tutorial.py"
      issue: "Soft-pass steps 6/7 (lines 305–315) return `bool(line)` — any non-empty input passes including unknown commands."
  missing:
    - "Add `self._last_command_unknown = False` to SPHShell.__init__ (repl.py:77)."
    - "Set `self._last_command_unknown = True` in SPHShell.default() (repl.py:616) before printing the Polish error."
    - "In precmd, immediately before returning `line`, reset `self._last_command_unknown = False` (the 'we are about to dispatch a real command' point). This avoids editing every do_* method."
    - "In postcmd, add early-return: `if self._last_command_unknown: self._last_command_unknown = False; return stop` — placed BEFORE check_step invocation."
    - "Optional: add test `test_soft_pass_step_rejects_unknown_command` — drives SPHShell into step 6, feeds garbage, asserts no `✓ zaliczone` and step_num unchanged."
  debug_session: ""

- truth: "Running `python sph_sim.py` with no mode flag defaults to --interactive mode and prints an info banner explaining the implicit choice + a one-sentence description of each other available mode (--strategy, --custom, --batch, --tutorial)"
  status: resolved
  reason: "User requested: przy błędzie uruchomienia bez podanego trybu uruchamiaj domyślnie jako interactive, i dodaj informację, że uruchomiona jako interactive, inne dostępne tryby to: [current Polish required-mode error] + krótki jednozdaniowy opis każdego z trybów (current behavior: errors with 'Musisz podać jeden z trybów: ...'; requested behavior: implicit --interactive + informative banner)"
  severity: major
  test: 3
  root_cause: "Phase 8 Plan 08-02 hardened the no-mode case as a hard error via p.error(...) in args.py (lines 201–202). UAT reveals the desired contract is a graceful informational default — auto-promote to --interactive and surface the other 4 modes as discoverable hints, rather than penalizing with exit 2. Scope change, not a bug."
  artifacts:
    - path: "sphsim/cli/args.py"
      issue: "Post-parse `p.error(...)` block at lines 201–202 — needs to be replaced with auto-set `args.interactive = True` + stderr banner. Comment block at lines 141–145 documenting the hard-error rationale needs updating to reflect informational-default contract. Add `import sys` at top of file."
    - path: "sphsim/cli/main.py"
      issue: "Existing `if args.interactive:` early-branch (line 69) — no change needed; auto-set falls through naturally."
    - path: "tests/test_tutorial.py"
      issue: "test_no_mode_errors_polish (lines 348–357) — flip from asserting exit !=0 + 'Musisz podać' to asserting REPL launches (with stdin 'exit\\n') + stderr contains 'Nie podano trybu' + '--strategy' + '--custom' + '--batch' + '--tutorial'."
    - path: "scripts/verify_phase8.sh"
      issue: "Check C7 (lines 112–113) — flip grep target from 'Musisz podać jeden z trybów' to the new banner string (e.g., 'Nie podano trybu')."
    - path: "scripts/verify_phase3.sh"
      issue: "Lines 155–156 — same grep flip as verify_phase8.sh C7 (Phase 3 check that was retrofitted in Phase 8)."
  missing:
    - "Replace args.py p.error(...) block (lines 201–202) with: set `args.interactive = True` + print stderr banner with informal-respectful Polish copy listing all 4 alternate modes (descriptions pulled verbatim from existing argparse `help=` strings / do_help body)."
    - "Add `import sys` at top of sphsim/cli/args.py (only `argparse` currently imported)."
    - "Update comment block at sphsim/cli/args.py lines 141–145 to reflect new informational-default contract."
    - "Flip test_no_mode_errors_polish to test_no_mode_defaults_to_interactive_with_banner; provide stdin 'exit\\n' so REPL exits cleanly."
    - "Flip verify_phase8.sh C7 grep target and label."
    - "Flip verify_phase3.sh lines 155–156 grep target."
    - "Backwards compat: regression_check.py always uses explicit mode flags — zero regression risk."
  debug_session: ""
