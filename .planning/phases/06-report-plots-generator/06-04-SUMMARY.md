---
phase: 06-report-plots-generator
plan: 04
subsystem: report-generator
tags: [orchestrator, write-report, side-effect, opt-out, stderr-banner, format-json-filter, repl-wiring, compare-mode-threading]

# Dependency graph
requires:
  - phase: 06-report-plots-generator/02
    provides: "sphsim.report.markdown.render_report — pure-function MD assembler (6 sections + optional 7th)"
  - phase: 06-report-plots-generator/03
    provides: "sphsim.report.plots.plot_decision_distribution + plot_kpi_timeseries — matplotlib Agg PNG generators"
  - phase: 06-report-plots-generator/00
    provides: "tests/test_report.py 3 remaining skip stubs (TestReportFiles, TestReportCompareMode, TestJsonStdoutClean) — Plan 04 replaces them"
  - phase: 05-cli-deconstruction/05
    provides: "sphsim.cli.main with custom + compare branches; sphsim.cli.repl do_run + do_compare; sphsim.cli.output.format_json env block"
provides:
  - "sphsim.report.__init__.write_report(args, res, params, K1, *, mode) — side-effecting orchestrator (mkdir + plot + render + write) with exception isolation + SPHSIM_NO_REPORT opt-out"
  - "sphsim.report._timestamp + _resolve_report_dir + _extract_plot_source private helpers (collision retry; mode-aware plot source extraction)"
  - "5 entry-point wirings: main.py × 4 (custom-compare, custom-single, built-in-compare, built-in-single) + repl.py × 2 (do_run, do_compare); banner emitted on sys.stderr by callers"
  - "main.py:run_compare + repl.py:do_compare return dict extended with '_with_agent_full' private key (full res_with carrying history for compare-mode PLOT-02)"
  - "sphsim.cli.output.format_json filter extended with `not k.startswith('_')` — strips _with_agent_full from JSON metrics block; SC#6 stdout cleanliness + regression baseline equality preserved"
  - "TestReportFiles (3 tests) + TestReportCompareMode (2 tests) + TestJsonStdoutClean (2 tests) = 7 new GREEN tests (replaces 3 skip stubs)"
  - "Sample reports generated end-to-end during human-verify checkpoint (single + compare runs visible under ./reports/<ts>/)"
affects: ["06-05 (Plan 05 verify_phase6.sh exit-gate consumes write_report + banner + opt-out semantics)", "Future Phase 7+ hardening of report side-effects"]

# Tech tracking
tech-stack:
  added: []  # Stdlib only — os, sys, pathlib.Path, datetime; matplotlib already imported by Plan 03 plots.py.
  patterns:
    - "Side-effect orchestrator wrapping pure renderers — write_report is the ONLY function in sphsim/report/ that touches the filesystem; render_report + plot_* remain pure (return string / write to path arg)"
    - "Banner-on-stderr (Pitfall 3) — write_report itself does NOT print the banner; callers (main.py/repl.py) print 'Raport zapisany do:' on sys.stderr after receiving Path. This keeps banner emission a CALLER decision (REPL doesn't need it, JSON mode wants stdout untouched)"
    - "Exception isolation envelope (Pitfall 6 + RESEARCH §C.7) — entire write_report body wrapped in outer try/except + inner try/except per filesystem op; failures log Polish '[OSTRZEŻENIE]' on stderr and return None; report side-effect NEVER kills CLI"
    - "Underscore-prefix private key contract — _with_agent_full threaded from run_compare/do_compare into write_report (gives compare-mode access to full res_with with history); format_json strips top-level '_*' keys to preserve SC#6 JSON cleanliness + regression equality"
    - "Opt-out via env var (Pitfall 4) — SPHSIM_NO_REPORT=1 → early-return None; no banner, no mkdir, no side-effect. THE opt-out mechanism (no --no-report CLI flag per SC#1 'bez żadnych flag, zawsze')"
    - "Test pollution prophylaxis — every test class that invokes write_report does setUp(chdir to tempfile.mkdtemp) + tearDown(chdir back + shutil.rmtree); test-time SPHSIM_NO_REPORT popped from environ so write_report actually creates files"

key-files:
  created: []
  modified:
    - "sphsim/report/__init__.py (21 → 153 LoC, +132) — write_report orchestrator body + _timestamp + _resolve_report_dir + _extract_plot_source helpers; preserves render_report re-export"
    - "sphsim/cli/main.py (144 → 168 LoC, +24) — top-level `import sys` (was shadowed by local imports → Rule 1 bug fix); top-level `from sphsim.report import write_report`; run_compare return dict adds '_with_agent_full'; 4 wire sites (run_compare-custom, custom-single, built-in-compare, built-in-single) each followed by stderr banner"
    - "sphsim/cli/repl.py (335 → 352 LoC, +17) — `from sphsim.report import write_report`; do_run fake_args extended with `json=False, compare_agent=False` + write_report call after sim.run(); do_compare fake_args extended with `json=False, compare_agent=True` + res_combined adds '_with_agent_full' + write_report call after build"
    - "sphsim/cli/output.py (190 → 200 LoC, +10) — format_json non-comparison branch metrics dict-comp extended with `and not k.startswith('_')`; preserves regression baseline equality"
    - "tests/test_report.py (190 → 361 LoC, +171) — TestReportFiles (3 tests with setUp/tearDown tempdir + env-pop), TestReportCompareMode (2 tests), TestJsonStdoutClean (2 tests) replace 3 skip stubs; module-level `import shutil, tempfile`"

key-decisions:
  - "Banner emission is CALLER responsibility, not write_report's. Rationale: REPL might choose different wording ('Raport porównawczy zapisany do:'); JSON mode needs banner; some future test/CI invocations might want None semantics without text. write_report returns Path; caller decides what to print."
  - "Outer try/except envelope around the entire write_report body. Rationale: Pitfall 6 + RESEARCH §C.7 mandate that the report side-effect must NEVER crash the CLI. The inner per-op try/except still narrows blame (which file failed), but the outer catch-all is a defense-in-depth against unexpected interpreter-level errors during message formatting."
  - "_with_agent_full carries the FULL res_with (with history + devices), not just history. Rationale: future evolution may want with-agent IC tables / per-phase analysis from PNGs; passing the full dict is no bigger memory-wise (Python passes references) and keeps the contract simple. format_json strips top-level '_*' so JSON output is unchanged."
  - "fake_args extension adds BOTH json=False AND compare_agent. Rationale: defensive consistency (Pitfall 6); json=False is required because markdown.py never reads it but Phase 5 audit recommended uniform fake_args shape; compare_agent (True in do_compare, False in do_run) is read by markdown._render_strategy_params to label the 'Tryb agenta' row."
  - "Test setUp uses os.chdir(tempfile.mkdtemp()) rather than monkey-patching Path('reports'). Rationale: write_report uses relative Path('reports') internally — chdir is the simplest cwd-based override that works without touching production code; tearDown(shutil.rmtree) guarantees no leftover state."

# Metrics
metrics:
  duration: "~25 minutes (single executor wave 3, no checkpoint blocking)"
  completed: 2026-05-28
  tasks_completed: 2  # 2 auto tasks + 1 human-verify checkpoint (surfaced, awaits user)
  files_modified: 5
  files_created: 0
  loc_delta: +354  # sum across 5 modified files
  tests_added: 7   # 3 + 2 + 2 new tests replacing 3 skip stubs
  tests_total_module: 14
  tests_total_suite: 172
---

# Phase 6 Plan 04: write_report Orchestrator Wiring Summary

**One-liner:** Side-effecting `write_report(args, res, params, K1, *, mode)` orchestrator landed in `sphsim/report/__init__.py` (132 LoC added) with `SPHSIM_NO_REPORT=1` opt-out + full exception isolation + stderr-only banner emission; wired at 5 entry-points (main.py × 4, repl.py × 2) with `_with_agent_full` private-key threading for compare-mode PLOT-02 history access; `format_json` filter strips underscore-prefixed top-level keys; 7 new GREEN tests replace Plan 00 skip stubs (TestReportFiles + TestReportCompareMode + TestJsonStdoutClean).

## What Got Built

### `sphsim/report/__init__.py` final shape (153 LoC)

Public surface:
- `write_report(args, res, params, K1, *, mode='single'|'compare') -> Path | None` — orchestrator (mkdir + plot × 2 + render + write); returns Path on success, None on opt-out / mkdir-fail / render-fail. Never raises.
- `render_report(args, res, params, K1, *, mode)` — re-export from `sphsim.report.markdown` (Plan 02 contract preserved).

Private helpers:
- `_timestamp()` → `'%Y%m%d-%H%M%S'` (fs-safe Windows; lex-sortable).
- `_resolve_report_dir(base=None)` → mkdir `./reports/<ts>/` with `-N` collision retry (RESEARCH §C.7).
- `_extract_plot_source(res, mode)` → mode-aware dict picker; in compare mode prefers `_with_agent_full` (with history) over `comparison.with_agent` (without).

Defense in depth (Pitfall 6 + RESEARCH §C.7):
1. Opt-out env var check at function entry (returns None silently).
2. Outer try/except envelope around entire body (last-resort catch-all).
3. Inner try/except around each filesystem op (mkdir + 2× savefig + 1× write_text) — failures emit Polish `[OSTRZEŻENIE]` to stderr.
4. Markdown failure returns None (caller should NOT print banner for incomplete report).

### 5 entry-point wirings

**`sphsim/cli/main.py`** (4 wire sites):

| # | Location                       | mode      | Banner                                    |
| - | ------------------------------ | --------- | ----------------------------------------- |
| 1 | custom-branch `--compare-agent`| compare   | "Raport porównawczy zapisany do: ..."     |
| 2 | custom-branch single-run       | single    | "Raport zapisany do: ..."                 |
| 3 | built-in-branch `--compare-agent`| compare | "Raport porównawczy zapisany do: ..."     |
| 4 | built-in-branch single-run     | single    | "Raport zapisany do: ..."                 |

Diff summary per site: `report_dir = write_report(args, res, params, K1, mode=...)` + `if report_dir: print(..., file=sys.stderr)` inserted between `res = sim.run()` (or `res = run_compare(...)`) and the existing `print(format_human/format_json...)` call.

**Critical Rule 1 bug found + fixed in this task:** `main()` had two local `import sys` lines (one inside `if args.param and not args.custom:`, one inside `if args.custom:`). Because Python infers `sys` as function-local from ANY assignment in the function body, the built-in single-run banner (line 162, no local `import sys` executed before it) hit `UnboundLocalError: cannot access local variable 'sys'`. Fix: promoted `import sys` to top-level (line 6) + removed both local imports. Single fix; verified by smoke test passing afterward.

**`sphsim/cli/repl.py`** (2 wire sites):

| # | Location          | mode      | fake_args extension                    | Banner                                    |
| - | ----------------- | --------- | -------------------------------------- | ----------------------------------------- |
| 1 | `do_run`          | single    | `+json=False, compare_agent=False`     | "Raport zapisany do: ..."                 |
| 2 | `do_compare`      | compare   | `+json=False, compare_agent=True`      | "Raport porównawczy zapisany do: ..."     |

`do_compare`'s `res_combined` now carries `_with_agent_full: res_with` alongside the existing `comparison: comparison_block`.

### `_with_agent_full` threading (3 sites — resolution to RESEARCH §N.1)

1. `sphsim/cli/main.py:run_compare()` return dict — adds `'_with_agent_full': res_with`.
2. `sphsim/cli/repl.py:do_compare()` res_combined build — adds `'_with_agent_full': res_with`.
3. `sphsim/report/__init__.py:_extract_plot_source()` consumer — `res.get('_with_agent_full') or res.get('comparison', {}).get('with_agent', {})`.

Why: `run_compare` strips `history` from `comparison.with_agent` (dict-comp at main.py:42-43). But `plot_kpi_timeseries` needs `history.val + history.providers`. Solution: thread the full `res_with` via an underscore-prefixed private key; consumer prefers it, falls back to comparison block (silent PNG skip).

### `sphsim/cli/output.py` format_json filter (1-token addition)

Before: `**{k: v for k, v in res.items() if k not in ('history', 'devices')}`
After:  `**{k: v for k, v in res.items() if k not in ('history', 'devices') and not k.startswith('_')}`

This strips `_with_agent_full` (and any future underscore-prefixed private keys) from the JSON metrics block, preserving SC#6 stdout cleanliness AND regression baseline equality (`PASS: 8/8` confirmed).

### `tests/test_report.py` test classes (14 total, all GREEN)

| Class                    | Tests | Plan | Status |
| ------------------------ | ----- | ---- | ------ |
| TestReportFiles          | 3     | 04   | GREEN (NEW) |
| TestReportSections       | 5     | 02   | GREEN (preserved) |
| TestReportCompareMode    | 2     | 04   | GREEN (NEW) |
| TestPlotLinks            | 2     | 02   | GREEN (preserved) |
| TestJsonStdoutClean      | 2     | 04   | GREEN (NEW) |

Plan 04 added: file existence + opt-out + collision retry + compare-mode section + with-agent PNG threading + subprocess JSON cleanliness + underscore-key strip.

## End-to-End Smoke Test Results

| Command                                                                                         | Result                                                                                |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `python3 sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42`                          | exit=0; 3 files in `./reports/<ts>/`; banner "Raport zapisany do: ..." on stderr      |
| `python3 sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json | json.loads(...)` | stdout pure JSON (4 keys); banner on stderr; report still generated                   |
| `python3 sph_sim.py --strategy naive --zeta 0.5 --compare-agent --seed 42`                     | exit=0; 3 files + section 7 with delta table; kpi_timeseries.png 186 KB (history OK)  |
| `printf 'run naive zeta=0.5\nexit\n' | python3 sph_sim.py --interactive`                       | exit=0; banner on stderr; reports/<ts>/ created                                       |
| `printf 'compare naive zeta=0.5\nexit\n' | python3 sph_sim.py --interactive`                  | exit=0; banner "Raport porównawczy zapisany do: ..." on stderr; section 7 present     |
| `SPHSIM_NO_REPORT=1 python3 sph_sim.py ...`                                                    | exit=0; NO ./reports/ directory created                                               |
| `SPHSIM_NO_REPORT=1 python3 scripts/regression_check.py`                                       | PASS: 8/8 (baseline equality preserved by `not k.startswith('_')` filter)             |
| `SPHSIM_NO_REPORT=1 python3 -m unittest discover tests/`                                       | Ran 172 tests, OK                                                                     |
| `SPHSIM_NO_REPORT=1 python3 -m unittest tests.test_report -v`                                  | Ran 14 tests in 0.75s, OK (0 skipped, 0 failed)                                       |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] UnboundLocalError on `sys` in main.py:162**
- **Found during:** Task 1, first smoke test of built-in single-run after wiring write_report.
- **Issue:** `main()` had local `import sys` inside `if args.param and not args.custom:` (line 66) and inside `if args.custom:` (line 71). Python sees ANY `import sys` in the function body and treats `sys` as local for the entire function scope. Built-in single-run banner at line 162 used `sys.stderr` without hitting either local import → `UnboundLocalError: cannot access local variable 'sys' where it is not associated with a value`.
- **Fix:** Promoted `import sys` to module top-level (line 6); removed both local `import sys` lines; preserved the comment explaining why.
- **Files modified:** `sphsim/cli/main.py` (single edit in addition to the planned Task 1 edits).
- **Commit:** included in Task 1 commit `4392989`.
- **Verification:** End-to-end smoke `python3 sph_sim.py --strategy naive ... --json` exits 0 with valid JSON on stdout and banner on stderr.

### No other deviations

All other Task 1/2 changes matched the plan verbatim. format_json filter extended exactly as specified. `_with_agent_full` threaded at the 3 specified sites. fake_args extensions match `json=False` + `compare_agent=<bool>` per RESEARCH §E.14 audit.

## Threat Flags

None. The Phase 6 surface introduced by this plan (filesystem write to `./reports/<ts>/`, env var `SPHSIM_NO_REPORT` read) is exactly the surface specified in the plan's `<threat_model>`. No new network endpoints, no new auth paths, no new schema changes at trust boundaries.

## Suggested Commit Message

Already committed:
- Task 1: `feat(06-04): write_report orchestrator + 5 entry-points wired` (4392989)
- Task 2: `test(06-04): replace 3 skip stubs with 7 GREEN tests (REPORT-01/03 + SC#6)` (ee6e6f9)

Final SUMMARY commit suggestion:
```
docs(06-04): summarize wave 3 — write_report wiring + 7 new GREEN tests
```

## Manual Checkpoint Outcome

**Status:** SURFACED (USER VERIFICATION REQUIRED). Per orchestrator instructions, executor surfaced the checkpoint with absolute paths to two sample reports (one single-run, one compare-mode) and the 3 visual checks. Executor did NOT block. Orchestrator gates final phase-completion on user's confirmation of:

1. PNG inline rendering in GitHub/VSCode/Obsidian.
2. Polish glyph rendering in PNG labels (DejaVu Sans fallback).
3. Section 7 "Porównanie z RationalAgent" delta table correctness.

Sample report paths recorded above (Checkpoint Details section). Awaiting user "approved" / specific issue report.

## Self-Check: PASSED

Verified post-implementation:
- FOUND: `sphsim/report/__init__.py` (153 LoC) with `write_report` callable.
- FOUND: `sphsim/cli/main.py` contains `from sphsim.report import write_report` (1×) + 4× `write_report(` invocations.
- FOUND: `sphsim/cli/repl.py` contains `from sphsim.report import write_report` (1×) + 2× `write_report(` invocations.
- FOUND: `sphsim/cli/output.py` contains `not k.startswith('_')` filter (1×).
- FOUND: `tests/test_report.py` 14/14 tests GREEN (Ran 14 tests, OK).
- FOUND: Commit `4392989` (feat 06-04 orchestrator) in `git log --oneline`.
- FOUND: Commit `ee6e6f9` (test 06-04 replace stubs) in `git log --oneline`.
- FOUND: 0 skip stubs remaining: `grep -c 'skipTest("Wave' tests/test_report.py` = 0.
- FOUND: regression PASS 8/8.
- FOUND: full suite 172/172 OK.
- FOUND: opt-out (SPHSIM_NO_REPORT=1) verified — no ./reports/ created.
- FOUND: JSON stdout cleanliness — `json.loads(stdout)` succeeds.
- FOUND: sample reports for human-verify checkpoint generated and paths surfaced.
