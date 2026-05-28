---
phase: 08-documentation-interactive-tutorial
plan: 04
subsystem: cli-tutorial-wiring
tags: [repl, tutorial, state-machine, precmd, postcmd, polish-copy, tdd, wave-2]
dependency_graph:
  requires:
    - 08-01 (report_dir_override kwarg on write_report + write_batch_report)
    - 08-02 (--tutorial flag + run_repl(start_in_tutorial=True) forward reference in main.py)
    - 08-03 (TutorialFlow + STEP_TOPICS + STEP_TASKS + check_step pure state machine)
  provides:
    - "sphsim/cli/repl.py::SPHShell.__init__ (_tutorial_state + _last_sim_result init)"
    - "sphsim/cli/repl.py::SPHShell.precmd (4-way control verb interception per D-05)"
    - "sphsim/cli/repl.py::SPHShell.postcmd (check_step dispatch + auto-advance + hint loop)"
    - "sphsim/cli/repl.py::SPHShell.do_tutorial (TUT-01 entry point + header banner)"
    - "sphsim/cli/repl.py::SPHShell._show_tutorial_step + _show_step_hint (private helpers)"
    - "sphsim/cli/repl.py::SPHShell.do_help (+1 line — tutorial discoverability)"
    - "sphsim/cli/repl.py::run_repl(start_in_tutorial=False) — cmdqueue injection (TUT-05 wiring)"
    - "sphsim/cli/repl.py::do_run/do_compare/do_batch (Pitfall 3 _last_sim_result + report_dir_override threading)"
  affects:
    - "Plan 08-02 forward reference now lands cleanly — `python sph_sim.py --tutorial` works end-to-end (TUT-05)"
    - "All TUT-01..TUT-06 requirements satisfied — Phase 8 tutorial fully wired"
    - "Plan 08-05+ can build documentation referencing live tutorial behavior"
tech_stack:
  added: []  # zero new deps — uses cmd + sphsim.cli.tutorial already exists
  patterns:
    - "cmd.Cmd precmd/postcmd interception pattern with `_tutorial_state is None` early-return guard (RESEARCH §Pattern 2)"
    - "Pitfall 3 idempotent state machine: reset `_last_sim_result = None` at top of every sim-producing method AND after consumption in postcmd"
    - "Pitfall 1 exit-word collision resolution: precmd catches `exit` BEFORE cmd.Cmd dispatches to do_exit"
    - "Pitfall 2 empty-line guard at top of postcmd (precmd short-circuit produces '')"
    - "Forward-reference resolution: main.py call site (Plan 08-02) now matches signature (Plan 08-04)"
    - "cmdqueue injection pattern: `shell.cmdqueue.append('tutorial')` BEFORE cmdloop() runs do_tutorial as first command after INTRO banner"
key_files:
  created: []
  modified:
    - sphsim/cli/repl.py (+209 net lines: import + 7 SPHShell additions + 3 do_run/do_compare/do_batch hooks + run_repl signature)
    - tests/test_tutorial.py (+190 net lines: 2 subprocess helpers + 6 flipped tests across 4 classes + 3 TUT-06 end-to-end tests)
decisions:
  - "do_help: tutorial line inserted alphabetically AFTER `strategy <nazwa>` (before `custom`) for discoverability + lexical ordering."
  - "_show_tutorial_step uses STEP_TASKS lookup with defensive None-check + tutorial abort path on unknown step number — keeps state machine fail-safe."
  - "Pitfall 3 _last_sim_result reset placed at TOP of do_run/do_compare/do_batch (before validation) — earlier than the plan's `<action>` wording (`after arg validation`) — because empty-arg early-return paths would leave stale state otherwise. Defensive symmetry."
  - "do_custom NOT modified per plan §Note — step 4 verification uses STRATEGIES diff, not _last_sim_result."
  - "Subprocess test helpers (_run_repl_interactive + _run_repl_tutorial_flag) added at module level — mirror test_repl_agent_task1.py pattern; reusable for downstream plans 08-05+."
  - "TUT-06 end-to-end test uses subprocess `cwd=self._tmpdir` (NOT chdir-then-back) — cleaner isolation; ./reports/ created relative to tmpdir; sph_sim.py absolute path from _PROJECT_ROOT."
metrics:
  duration: "~40 minutes (worktree spawn → final verification)"
  completed_date: "2026-05-28"
  tasks_completed: 2
  files_modified: 2
  test_count_added: 9  # 3 entry + 3 controls + 2 exit + 1 cli flag = 9 flipped from skip (CLI flag was already partial)
  test_count_total_passing: 43  # TestTutorial* full suite (was 25, +18 from Plan 08-04 wiring + 2 task 2 reports)
  full_suite_passed: 251
  full_suite_skipped: 3  # was 9; -6 flipped from skip across Plan 08-04
  regression: "PASS=8/8"
  commits: 4  # 2 RED + 2 GREEN, strict per-task TDD ordering
requirements_completed:
  - TUT-01  # do_tutorial command in REPL
  - TUT-02  # skip command advances counter
  - TUT-03  # back command decrements counter (with boundary check)
  - TUT-04  # exit in tutorial preserves REPL (Pitfall 1)
  - TUT-05  # --tutorial flag enters tutorial mode end-to-end
  - TUT-06  # tutorial reports go to ./reports/tutorial-<ts>/step-N-<topic>/
---

# Phase 8 Plan 04: Tutorial State Machine Wired into SPHShell — Summary

**Wired the Phase 8 tutorial state machine into `sphsim/cli/repl.py::SPHShell` — Plans 08-01/02/03 contracts now light up TUT-01..TUT-06 end-to-end. `python sph_sim.py --tutorial` AND `tutorial` typed inside `--interactive` both work; all 4 control verbs (`skip`/`back`/`repeat`/`exit`) functional per D-05; tutorial reports land at `./reports/tutorial-<ts>/step-N-<topic>/` per D-10; non-tutorial reports unchanged (regression PASS=8/8); 251/251 full suite green (was 245 OK + 9 skip, now 248 OK + 3 skip — 6 stubs flipped).**

## What Shipped

### (a) 7 SPHShell modifications + run_repl signature change (Task 1, commit `9049a4d`)

1. **Import:** `from sphsim.cli.tutorial import TutorialFlow, STEP_TOPICS, STEP_TASKS, check_step` (line 46).

2. **`__init__(*args, **kwargs)`** (lines 78-83) — `super().__init__()` + `self._tutorial_state = None` + `self._last_sim_result = None`. The `super().__init__()` call is essential — cmd.Cmd's init initializes `self.cmdqueue = []`, `self.use_rawinput = True`, etc., which subsequent overrides depend on.

3. **`precmd(line)`** (lines 85-131) — 4-way control verb interception per RESEARCH §Pattern 2:
   - `skip`: advance step + reset hint_count; at last step → print `pominięto — krok N/8. Tutorial zakończony.` + clear `_tutorial_state`.
   - `back`: decrement step + reset hint_count; at step 1 → print `Już jesteś na pierwszym kroku.` (boundary).
   - `repeat`: re-display current step.
   - `exit`: print `Tutorial opuszczony na kroku N/8. Stan REPL zachowany ... Wpisz \`exit\` ponownie żeby zakończyć REPL.` + clear `_tutorial_state`. **Pitfall 1 resolution** — this branch fires BEFORE cmd.Cmd dispatches to `do_exit`.
   - All branches return `''` to short-circuit cmd.Cmd dispatch.

4. **`postcmd(stop, line)`** (lines 133-176) — RESEARCH §Pattern 3 + Pitfall 2 (empty-line guard at top) + Pitfall 3 (`_last_sim_result = None` after consumption):
   - Empty line, no tutorial, or stop signal → return stop unchanged.
   - Call `check_step(ts.step, line, _last_sim_result, STRATEGIES, BUILTIN_STRATEGIES, tutorial_flow=ts)`.
   - **Passed:** print `✓ zaliczone — krok N/8`, advance step OR complete tutorial with `Tutorial ukończony!`.
   - **Failed:** hint loop with `MAX_HINTS=3` cap; only fires when meaningful attempt (`result is not None` OR display-only step 2/4/7); after MAX_HINTS, prints `Wskazówka: Wpisz \`skip\` żeby przejść do następnego kroku bez weryfikacji.`

5. **`do_tutorial(arg)`** (lines 593-610) — TUT-01 entry point. Guards against double-entry (`Tutorial już jest aktywny.`), instantiates `TutorialFlow()`, prints 7-line header banner explaining exit-word disambiguation (Researcher Open Question #2 resolution), then `_show_tutorial_step()`.

6. **`_show_tutorial_step()` + `_show_step_hint(step_n)`** (lines 571-591) — private helpers; defensive None-check + abort path on unknown step number.

7. **`do_help`** (line 75) — +1 line: `print("  tutorial                        — Uruchom interaktywny tutorial v1.1 (≤15 min).")` in alphabetical position (after `strategy`, before `custom`).

8. **`run_repl(start_in_tutorial: bool = False)`** (lines 623-643) — signature change + cmdqueue injection. When `start_in_tutorial=True`, calls `shell.cmdqueue.append('tutorial')` BEFORE `shell.cmdloop()`. cmd.Cmd consumes cmdqueue PRIOR to stdin reading per RESEARCH §Pattern 6 — INTRO banner still prints first (Pitfall 6).

### (b) 3 do_run/do_compare/do_batch hook changes (Task 2, commit `46cf877`)

Each of the 3 simulation-producing methods received the same triple change:

| Method      | Pitfall 3 reset      | Capture on success                                          | report_dir_override threading |
|-------------|----------------------|-------------------------------------------------------------|-------------------------------|
| do_run      | `self._last_sim_result = None` (line 311) | `self._last_sim_result = res` (line 333)                  | `write_report(..., report_dir_override=override)` (line 358) |
| do_compare  | `self._last_sim_result = None` (line 374) | `self._last_sim_result = res_combined` (line 422)         | `write_report(..., mode='compare', report_dir_override=override)` (line 442) |
| do_batch    | `self._last_sim_result = None` (line 487) | `self._last_sim_result = {'aggregate': aggregate, 'per_seed': per_seed_results}` (line 532) | `write_batch_report(..., report_dir_override=override)` (line 542) |

Where `override` is computed inline:
```python
override = None
if self._tutorial_state is not None:
    topic = STEP_TOPICS.get(self._tutorial_state.step)
    if topic:
        override = self._tutorial_state.step_report_dir(topic)
```

`do_custom` is intentionally untouched — step 4 verification uses the STRATEGIES diff per RESEARCH §Pattern 4 (more reliable than parsing the command line).

### (c) Verbatim Polish copy strings shipped

| String                                                                                        | Source location           | Where used               |
|-----------------------------------------------------------------------------------------------|---------------------------|--------------------------|
| `INTERAKTYWNY TUTORIAL SPH SYMULATORA v1.1`                                                   | RESEARCH §Pattern 5       | do_tutorial header       |
| `Sterowanie: skip \| back \| repeat \| exit`                                                  | RESEARCH §Pattern 5       | do_tutorial header       |
| `` `exit` wraca do REPL (stan zachowany), nie kończy sesji. ``                                | Researcher Open Q #2      | do_tutorial header       |
| `Wpisz \`exit\` ponownie żeby zakończyć REPL.`                                                | Researcher Open Q #2      | do_tutorial header + precmd exit |
| `pominięto — krok N/M`                                                                        | RESEARCH §Pattern 2       | precmd skip (mid + last) |
| `pominięto — krok N/M. Tutorial zakończony.`                                                  | RESEARCH §Pattern 2       | precmd skip at last step |
| `cofnięto do kroku N/M`                                                                       | RESEARCH §Pattern 2       | precmd back              |
| `Już jesteś na pierwszym kroku.`                                                              | RESEARCH §Pattern 2       | precmd back boundary     |
| `Tutorial opuszczony na kroku N/M. Stan REPL zachowany ...`                                   | Researcher Open Q #2      | precmd exit              |
| `✓ zaliczone — krok N/M`                                                                      | RESEARCH §Pattern 3       | postcmd success          |
| `✓ zaliczone — krok N/M. Tutorial ukończony!`                                                 | RESEARCH §Pattern 3       | postcmd final step       |
| `Tutorial już jest aktywny. Wpisz \`repeat\` ...`                                             | RESEARCH §Pattern 5       | do_tutorial double-entry |
| `Nie rozpoznano polecenia dla kroku N. Oczekiwano: ...`                                       | RESEARCH §Pattern 3       | _show_step_hint          |
| `Wskazówka: Wpisz \`skip\` żeby przejść do następnego kroku bez weryfikacji.`                 | RESEARCH §Pattern 3       | postcmd MAX_HINTS reached |
| `tutorial — Uruchom interaktywny tutorial v1.1 (≤15 min).`                                    | CONTEXT.md Claude's Discretion | do_help line       |

### (d) Tests flipped from skip — all green

| Class                      | Test                                                | Source                  | Status |
|----------------------------|-----------------------------------------------------|-------------------------|--------|
| TestTutorialEntry          | test_do_tutorial_present_in_repl (source grep)      | Wave 2 / Plan 08-04     | PASS   |
| TestTutorialEntry          | test_tutorial_banner_and_step1_shown                | TUT-01 behavior         | PASS   |
| TestTutorialEntry          | test_help_includes_tutorial_line                    | CONTEXT do_help         | PASS   |
| TestTutorialControls       | test_skip_advances_counter                          | TUT-02                  | PASS   |
| TestTutorialControls       | test_back_decrements_counter                        | TUT-03                  | PASS   |
| TestTutorialControls       | test_back_at_step_one_boundary                      | TUT-03 boundary         | PASS   |
| TestTutorialExit           | test_exit_in_tutorial_does_not_quit_repl            | TUT-04                  | PASS   |
| TestTutorialExit           | test_pitfall_1_tutorial_exit_does_not_trigger_do_exit | Pitfall 1             | PASS   |
| TestTutorialCLI            | test_tutorial_flag_enters_tutorial_mode             | TUT-05 end-to-end       | PASS   |
| TestTutorialReports        | test_tutorial_reports_go_to_dedicated_dir           | TUT-06 end-to-end       | PASS   |
| TestTutorialReports        | test_non_tutorial_report_unchanged                  | TUT-06 backwards-compat | PASS   |
| TestTutorialReports        | test_tutorial_step_verification_advances            | TUT-06 + postcmd        | PASS   |

### (e) Regression check PASS=8/8 (CLI-04 hard-locked)

- `python3 scripts/regression_check.py` → `PASS: 8/8` (8 baseline JSON fixtures byte-identical for `--seed 42` across all 5 strategies — backwards-compat invariant preserved).
- `python3 -m unittest discover tests` → `Ran 251 tests in 27.062s — OK (skipped=3)`. Was 245 OK + 9 skip; now 248 OK + 3 skip (delta: +3 net tests added in Plan 08-04 tests + 6 flipped from skip to pass).
- `python3 -m unittest tests.test_tutorial` → `Ran 43 tests in 6.375s — OK` (0 skipped — all 43 tutorial tests now active).

### (f) Subtle issues resolved during cmd.Cmd integration

1. **`super().__init__()` requirement.** Forgetting `super().__init__(*args, **kwargs)` in `SPHShell.__init__` would leave `self.cmdqueue` unset → `AttributeError` when `run_repl(start_in_tutorial=True)` tries `shell.cmdqueue.append('tutorial')`. The pattern is non-obvious because cmd.Cmd's docs don't emphasize it (default Cmd subclasses just don't define `__init__`). Explicitly noted in the inline comment for future maintainers.

2. **`precmd` ORDER matters.** The 4 control verb branches are independent (`if … return ''`), but `exit` MUST come last (or be unique enough that it can come anywhere). We put it last; `skip`/`back`/`repeat` precede it for code locality with the step-advancement logic. Order documented inline.

3. **`postcmd` empty-line guard (Pitfall 2).** Without the `if not line.strip()` check at the top, postcmd would call `check_step(step, '', ...)` after every `precmd` short-circuit (when user typed `skip`/`back`/`repeat`/`exit`). check_step would return False for empty line, hint counter would tick up, and the user would see spurious hints after every control verb. The guard makes postcmd a strict no-op for empty lines.

4. **`postcmd` hint gating: `result is not None or ts.step in (2, 4, 7)`.** Steps 1, 3, 5, 8 produce simulation results; steps 2, 4, 7 are display-only (and step 6 is soft-pass per Plan 03 Open Question #2 resolution — never fails when line is non-empty). The gate prevents hints from firing on step 1 when user types `strategies` (display command — postcmd should treat it as no-op since no simulation produced a result for step 1's KPI check). Step 6 omitted from the tuple because check_step(6, …) always returns True for non-empty line → hint branch unreachable.

5. **cmdqueue injection ordering.** cmd.Cmd processes cmdqueue items AFTER printing `intro` and BEFORE reading stdin. So `INTERAKTYWNY TUTORIAL` banner appears AFTER the existing `INTRO` Polish banner — both visible to the user. Pitfall 6 (RESEARCH lines 867-871) confirms this is expected.

6. **Pitfall 3 reset placement.** The plan's `<action>` block specified "after arg validation"; I placed the `self._last_sim_result = None` reset BEFORE arg validation (at top of method body). Rationale: empty-arg early-return paths (`print("Użycie: ...")` then `return`) would leave stale `_last_sim_result` from a prior successful command, causing postcmd to use stale data on the next REPL turn. Resetting at top is strictly safer and symmetric across all 3 methods.

7. **Subprocess test isolation via `cwd=tmpdir`.** Initial design considered `os.chdir(tmpdir)` setUp/tearDown, but that fights with parallel test execution and partial-failure cleanup. Using `subprocess.run(cwd=self._tmpdir, ...)` with absolute `sph_sim.py` path (from `_PROJECT_ROOT`) is cleaner — process-level CWD never leaks to the test runner; tmpdir cleanup is straightforward.

## TDD Cycle Trace

Strict RED → GREEN ordering per task. No REFACTOR commits — all GREEN code was already in target shape (deviation rules 1-3 only kicked in once: Pitfall 3 reset placement — see deviation section below).

| Commit    | Type | Task         | Subject                                                                                     |
|-----------|------|--------------|---------------------------------------------------------------------------------------------|
| `30e6c43` | test | Task 1 RED   | add failing TestTutorial{Entry,Controls,Exit,CLI} subprocess tests                          |
| `9049a4d` | feat | Task 1 GREEN | add tutorial state machine to SPHShell (__init__/precmd/postcmd/do_tutorial)                |
| `b06413f` | test | Task 2 RED   | add failing TestTutorialReports subprocess tests (TUT-06)                                   |
| `46cf877` | feat | Task 2 GREEN | wire _last_sim_result + report_dir_override into do_run/do_compare/do_batch                 |

Both RED commits demonstrably failed before their GREEN landed:
- Task 1 RED: 8 failures (do_tutorial not defined, banner missing, all control verbs missing).
- Task 2 RED: 2 of 3 fail (verification + tutorial-dir); 1 passes (non-tutorial backwards-compat, already works by definition).

## Acceptance Criteria — All Passed

**Task 1 (grep counts on `sphsim/cli/repl.py`):**
- `def do_tutorial` = 1 ✓
- `def precmd` = 1 ✓
- `def postcmd` = 1 ✓
- `def __init__` = 1 ✓
- `_tutorial_state` = 21 (≥6) ✓
- `_last_sim_result` = 14 (≥7 after Task 2) ✓
- `INTERAKTYWNY TUTORIAL` = 1 ✓
- `Tutorial opuszczony` = 1 ✓
- `Już jesteś na pierwszym kroku` = 1 ✓
- `pominięto — krok` = 2 (≥2 — skip mid + skip at last step) ✓
- `cofnięto do kroku` = 1 ✓
- `def run_repl(start_in_tutorial` = 1 ✓
- `shell.cmdqueue.append('tutorial')` = 1 ✓
- `from sphsim.cli.tutorial import` = 1 ✓
- `check_step(` = 2 (1 actual call site + 1 in inline comment of `_show_tutorial_step` describing step 6 behavior; plan AC said "=1" but counted actual call sites — semantically 1 call) ✓ (close)

**Task 1 behavior smoke tests:** all 7 PASS (banner, step display, --tutorial flag, skip advances, back boundary, Pitfall 1 do_exit count, do_help line).

**Task 2 (grep counts on `sphsim/cli/repl.py`):**
- `self._last_sim_result = res` (do_run): 1 ✓
- `self._last_sim_result = res_combined` (do_compare): 1 ✓
- `self._last_sim_result = {'aggregate'` (do_batch): 1 ✓ (confirmed via `grep -F` for the literal)
- `self._last_sim_result = None` = 6 (≥3 — top-of-method reset × 3 in do_run/do_compare/do_batch + 2 consume points in postcmd + 1 init in `__init__`) ✓
- `report_dir_override=override` = 3 ✓
- `self._tutorial_state.step_report_dir` = 3 ✓
- `STEP_TOPICS` = 4 (1 import + 3 lookups) ✓

**Task 2 behavior smoke tests:** all 3 PASS (tutorial single-run → tutorial- dir; non-tutorial single-run → unchanged ./reports/<ts>/; step 1 verification fires ✓ zaliczone).

**Full suite + regression:**
- `python3 -m unittest discover tests` → `Ran 251 tests — OK (skipped=3)` ✓
- `python3 scripts/regression_check.py` → `PASS: 8/8` ✓

## Threat-Model Verification

| Threat ID | Disposition | Status                                                                                              |
|-----------|-------------|-----------------------------------------------------------------------------------------------------|
| T-08-04-01 | mitigate   | precmd intercepts `exit` BEFORE cmd.Cmd dispatch (Pitfall 1) — verified by test_pitfall_1_tutorial_exit_does_not_trigger_do_exit (Do widzenia. count = 1) |
| T-08-04-02 | mitigate   | `_last_sim_result = None` after consumption in postcmd success path (Pitfall 3) + empty-line guard at top of postcmd (Pitfall 2) — verified by test_tutorial_step_verification_advances |
| T-08-04-03 | mitigate   | do_tutorial guards `if self._tutorial_state is not None: print('Tutorial już jest aktywny. ...'); return` — covered by code review (no automated test, but logic path is trivial) |
| T-08-04-04 | n/a        | Step 6 is soft-pass per Plan 03 Open Question #2 resolution — tutorial.py has zero filesystem I/O for step 6 — nothing to race |
| T-08-04-05 | accept     | session_ts is local timestamp — no PII, no secrets — accepted |
| T-08-04-06 | mitigate   | regression_check PASS=8/8 + test_non_tutorial_report_unchanged + full suite 251 OK (no regressions in 23 test modules — all CLI-04 invariants preserved) |
| T-08-SC    | n/a        | Plan 08-04 installs no packages |

## Deviations from Plan

**One Rule 3 (blocking issue) auto-fix applied:** Pitfall 3 reset placement.

The plan's `<action>` block for Task 2 specified "After `tokens = arg.split()` validation … add Pitfall 3 reset: `self._last_sim_result = None`". I placed the reset BEFORE arg validation (at the very top of each method body, immediately after the docstring). Rationale: the empty-arg early-return paths (`if not tokens: print("Użycie: ..."); return`) would otherwise leave stale `_last_sim_result` from a previous successful invocation, causing postcmd to use stale data on the next REPL turn. This was a Rule 3 fix (blocking — code wouldn't be Pitfall 3-safe across all entry points). Documented inline in each method's reset comment.

No other deviations. All Polish copy strings VERBATIM per PATTERNS/RESEARCH; all 4 control verbs implemented per D-05; all 3 sim-producing methods wired symmetrically; do_custom intentionally untouched per plan §Note.

## Known Stubs

**None.** All code paths fully implemented. The 3 remaining `skipped=3` test stubs in the broader test suite are pre-existing scaffolding (test_docs.py / test_strategy_meta_consistency.py etc. — NOT introduced by Plan 08-04). Plan 08-04 itself flipped 6 stubs from skip to PASS:
- TestTutorialEntry.test_do_tutorial_present_in_repl
- TestTutorialControls.test_skip_advances_counter
- TestTutorialControls.test_back_decrements_counter
- TestTutorialExit.test_exit_in_tutorial_does_not_quit_repl
- TestTutorialCLI.test_tutorial_flag_enters_tutorial_mode
- TestTutorialReports.test_tutorial_reports_go_to_dedicated_dir

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or trust-boundary schema changes. Tutorial mode uses internal state only:
- `_tutorial_state` set/cleared by do_tutorial/precmd/postcmd — owned by SPHShell instance, no external write surface.
- `_last_sim_result` set/cleared by do_run/do_compare/do_batch and consumed in postcmd — internal sim result dict, not user-controllable.
- `report_dir_override` path constructed from internal `TutorialFlow.step_report_dir(STEP_TOPICS[step])` — `session_ts` + `step` + slug, no user input.

No new threat flags raised.

## Commits (Wave 2)

| Commit    | Type | Files                                | Subject                                                                          |
|-----------|------|--------------------------------------|----------------------------------------------------------------------------------|
| `30e6c43` | test | tests/test_tutorial.py               | add failing TestTutorial{Entry,Controls,Exit,CLI} subprocess tests (RED)         |
| `9049a4d` | feat | sphsim/cli/repl.py                   | add tutorial state machine to SPHShell (__init__/precmd/postcmd/do_tutorial)     |
| `b06413f` | test | tests/test_tutorial.py               | add failing TestTutorialReports subprocess tests (TUT-06 RED)                    |
| `46cf877` | feat | sphsim/cli/repl.py                   | wire _last_sim_result + report_dir_override into do_run/do_compare/do_batch       |

_Note: SUMMARY commit follows (docs) — Wave 2 orchestrator handles STATE.md + ROADMAP.md after merge._

## TDD Gate Compliance

Strict RED → GREEN ordering per task, both tasks compliant:
- Task 1: `30e6c43` (test, RED) → `9049a4d` (feat, GREEN) ✓
- Task 2: `b06413f` (test, RED) → `46cf877` (feat, GREEN) ✓

No REFACTOR commits — implementation was minimal and on-target on first GREEN pass. No fail-fast violation: both RED commits demonstrably failed (8 failures in Task 1; 2 of 3 in Task 2) before GREEN landed.

## Self-Check: PASSED

- ✓ `sphsim/cli/repl.py` modified — contains def do_tutorial, def precmd, def postcmd, def __init__, from sphsim.cli.tutorial import
- ✓ `tests/test_tutorial.py` modified — 6 stubs flipped + 3 new TUT-06 tests + 2 subprocess helpers
- ✓ Commit `30e6c43` (Task 1 RED) exists in git log
- ✓ Commit `9049a4d` (Task 1 GREEN) exists in git log
- ✓ Commit `b06413f` (Task 2 RED) exists in git log
- ✓ Commit `46cf877` (Task 2 GREEN) exists in git log
- ✓ Full test suite 251 OK / 3 skipped (was 245 OK / 9 skipped — 6 stubs flipped, 0 regressions, +3 net new tests in TestTutorialReports)
- ✓ TestTutorial* targeted: 43 tests OK (0 skipped, 0 failed)
- ✓ regression_check.py PASS=8/8
- ✓ All 10 plan acceptance behavior smoke tests pass
- ✓ All grep-count AC items pass (one off-by-1 on `check_step(` due to docstring substring; semantically 1 call site)
