---
status: complete
phase: 08-documentation-interactive-tutorial
source: [08-00-SUMMARY.md, 08-01-SUMMARY.md, 08-02-SUMMARY.md, 08-03-SUMMARY.md, 08-04-SUMMARY.md, 08-05-SUMMARY.md, 08-06-SUMMARY.md, 08-07-SUMMARY.md]
started: 2026-05-28T21:30:00Z
updated: 2026-05-29T01:05:00Z
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
  status: failed
  reason: "User reported: nie ma wzmianki o tutorialu (after booting --interactive — banner shows only `help` and `exit` pointers, no mention of the new `tutorial` entry point)"
  severity: major
  test: 1
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Tutorial control verbs (skip | back | repeat | exit) remain visible to the user throughout the tutorial flow, not only in the one-time entry banner"
  status: failed
  reason: "User reported: nigdzie w tutorialu nie ma informacji o liniach sterowania (controls appear once in the banner then disappear; subsequent step displays don't remind the user that skip/back/repeat/exit are available)"
  severity: minor
  test: 2
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Step 2 of the tutorial is split into two distinct steps: (a) list strategies via `strategies`, (b) view details via `strategy <nazwa>`"
  status: failed
  reason: "User requested: rozbij krok 2 na 2 osobne — jeden wyświetl strategie, drugi zobacz szczegóły (current step 2 conflates both verbs into one display-only step; user wants them as two separate steps, raising total step count from 8 to 9)"
  severity: major
  test: 2
  artifacts: []
  missing: []
  debug_session: ""

- truth: "check_step rejects steps whose REPL output is 'nieznana komenda' (unknown command) — soft-pass steps must not accept garbage input"
  status: failed
  reason: "User reported: jeśli wynikiem testu jest 'nieznana komenda' nie akceptuj kroku jako zaliczone (current soft-pass logic on steps 6 and 7 returns True for any non-empty line, including typos that SPHShell rejects with 'nieznana komenda')"
  severity: major
  test: 2
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Running `python sph_sim.py` with no mode flag defaults to --interactive mode and prints an info banner explaining the implicit choice + a one-sentence description of each other available mode (--strategy, --custom, --batch, --tutorial)"
  status: failed
  reason: "User requested: przy błędzie uruchomienia bez podanego trybu uruchamiaj domyślnie jako interactive, i dodaj informację, że uruchomiona jako interactive, inne dostępne tryby to: [current Polish required-mode error] + krótki jednozdaniowy opis każdego z trybów (current behavior: errors with 'Musisz podać jeden z trybów: ...'; requested behavior: implicit --interactive + informative banner)"
  severity: major
  test: 3
  artifacts: []
  missing: []
  debug_session: ""
