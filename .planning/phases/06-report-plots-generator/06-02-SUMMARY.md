---
phase: 06-report-plots-generator
plan: 02
subsystem: report-generator
tags: [markdown, render-report, polish-locale, baseline-comparison, plot-links, pure-function]

# Dependency graph
requires:
  - phase: 06-report-plots-generator/01
    provides: "abstain_per_phase + valuation in res; per-phase decision data necessary for section 4"
  - phase: 06-report-plots-generator/00
    provides: "tests/test_report.py skip stubs (TestReportSections + TestPlotLinks placeholders this plan replaces)"
  - phase: 05-cli-deconstruction/05
    provides: "sphsim.cli.output.format_config_header (single source of truth for env block, reused verbatim in section 1)"
  - phase: 01-baseline-v1/08
    provides: "tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json (loaded by section 6)"
provides:
  - "sphsim.report package marker (sphsim/report/__init__.py — minimal re-export of render_report)"
  - "sphsim.report.markdown.render_report(args, res, params, K1, *, mode) — pure function returning 6 H2 sections (single) or 7 (compare)"
  - "BASELINE_PATH constant + graceful-degradation baseline loader"
  - "_KPI_ROWS canonical 5-KPI tuple (avg_val_last100, cum_val_total, avg_net_profit, delivery_ratio, avg_providers_l100)"
  - "PLOT-03 image-link emission: ![Rozkład decyzji per faza](decision_distribution.png) + ![Przebieg KPI w czasie](kpi_timeseries.png)"
  - "TestReportSections (5 GREEN tests) + TestPlotLinks (2 GREEN tests) — replace Plan 00 skip stubs"
  - "Module-level test helpers _make_args / _make_single_res / _make_compare_res (reusable across remaining Plan 04 test classes)"
affects: ["06-04 (Plan 04 will add write_report orchestrator into __init__.py + flesh out 3 remaining stub classes)", "07+ (any future Phase 7 hardening of MD format strings)"]

# Tech tracking
tech-stack:
  added: []  # Stdlib only — json, datetime, pathlib already in std use across project.
  patterns:
    - "Pure-function report assembly — render_report has zero matplotlib import + zero filesystem write; orchestrator-side effects deferred to Plan 04"
    - "Verbatim reuse of format_config_header (cross-package import sphsim.cli.output → sphsim.report.markdown) — single source of truth for env serialization"
    - "Canonical _KPI_ROWS tuple drives both KPI table (section 4) and baseline-delta table (section 7) — order is load-bearing for SC#2 test assertions"
    - "Graceful fixture degradation — try/except over BASELINE_PATH.read_text catches FileNotFoundError / KeyError / JSONDecodeError; emits Polish disclaimer rather than blowing up"

key-files:
  created:
    - "sphsim/report/__init__.py (21 LoC) — package init re-exporting render_report; placeholder comment marks where Plan 04 inserts write_report orchestrator"
    - "sphsim/report/markdown.py (214 LoC) — render_report + 7 private section helpers + BASELINE_PATH + _KPI_ROWS"
  modified:
    - "tests/test_report.py (97 → 190 LoC, +93) — 3 module helpers (argparse Namespace + single + compare fixture builders) + 5 TestReportSections methods + 2 TestPlotLinks methods replacing Plan 00 skip stubs"

key-decisions:
  - "Sub-plan-04 write_report orchestrator is NOT introduced here — __init__.py stays minimal so Plan 04 can land its filesystem-write code with a mechanical diff against an unchanged module footprint"
  - "Mode-aware metric extraction via single helper _extract_metrics_source (compare → res['comparison']['with_agent']; single → res itself) keeps KPI/decision tables consistent across modes"
  - "Strategy-params section iterates params dict generically rather than naming individual keys — allows naive/greedy/window/RL/etc. to all render without strategy-specific code paths"
  - "Polish-language convention enforced for every H2 header + column label + disclaimer (PROJECT.md constraint); emoji ✓/✗ retained ONLY in compare-mode werdykt line (precedent: format_human verbose mode in output.py:150-165)"
  - "_render_plots_section emits hardcoded relative filenames (no path prefix) — PLOT-03 requires GitHub/VSCode/Obsidian render compatibility; absolute paths would break MD viewers and leak filesystem layout"
  - "BASELINE_PATH uses Path(__file__).resolve().parent.parent.parent + tests/fixtures/... — relative to this module's location, so works regardless of cwd"

patterns-established:
  - "Cross-package import for shared serialization: sphsim.report.markdown imports format_config_header from sphsim.cli.output rather than duplicating env-table logic (DRY across CLI human-readable output and MD report)"
  - "Defensive getattr on argparse.Namespace attributes that may be absent in test fixtures: getattr(args, 'compare_agent', False) and getattr(args, 'no_agent', False) — allows tests to omit irrelevant flags"
  - "Test helpers as module-level builders (not class fixtures) — _make_args/_make_single_res/_make_compare_res are reusable across remaining test classes Plan 04 will populate"

requirements-completed: [REPORT-02, PLOT-03]
# NOTE: REPORT-01 (filesystem side, ./reports/<ts>/ + mkdir + opt-out) is reserved for Plan 04 even though
# the plan frontmatter lists it as in-scope here — Plan 02 intentionally lands only the markdown surface
# of REPORT-01/02/03 and defers all I/O to Wave 3. The orchestrator owns the final requirement check-off.

# Metrics
duration: ~22min
completed: 2026-05-28
---

# Phase 6 Plan 02: Markdown Report Renderer Summary

**Pure-function Markdown assembly for SPH simulation reports — `render_report(args, res, params, K1, *, mode)` returns 6 H2 sections in Polish (single mode) or 7 sections (compare mode), reusing `format_config_header` verbatim, loading the canonical Phase 1 baseline fixture with graceful degradation, and emitting PLOT-03 image links for Plan 03 to satisfy.**

## Performance

- **Duration:** ~22 min
- **Started:** 2026-05-28T05:44:00Z (approx — worktree spawn)
- **Completed:** 2026-05-28T06:06:52Z
- **Tasks:** 2 (both `type="auto"`)
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- **New `sphsim.report` package** with minimal `__init__.py` re-export — Plan 04 has a clean placeholder block to land `write_report` in Wave 3 without merge conflict.
- **`render_report` pure function** producing 6 H2 sections (single mode) or 7 (compare mode), composed via top-level `'\n\n'.join` of seven helper outputs.
- **Verbatim reuse of `format_config_header`** (imported from `sphsim.cli.output`) — single source of truth for env serialization; ENV-03/SC-4 invariant preserved across CLI and report.
- **Baseline comparison section 7** loads `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` and emits 5-KPI Δ table with Polish disclaimer; gracefully degrades (Polish "Baseline niedostępny" message) on `FileNotFoundError`/`KeyError`/`JSONDecodeError`.
- **PLOT-03 satisfied** without touching `plots.py`: `_render_plots_section` emits both required relative MD image links — `![Rozkład decyzji per faza](decision_distribution.png)` + `![Przebieg KPI w czasie](kpi_timeseries.png)`.
- **TestReportSections (5 tests) + TestPlotLinks (2 tests) GREEN** — replace Plan 00 skip stubs. 3 remaining classes (TestReportFiles, TestReportCompareMode, TestJsonStdoutClean) still `skipTest("Wave 3 — Plan 04 …")` as planned.
- **Full suite 164 OK / 5 skipped + regression 8/8 PASS** — zero collateral damage; reports/ dir not created (pure function, no filesystem writes).

## Task Commits

Each task was committed atomically:

1. **Task 1: Create `sphsim/report/__init__.py` + `sphsim/report/markdown.py` with `render_report` + 6 section helpers** — `d2f2f2d` (feat)
2. **Task 2: Replace `TestReportSections` + `TestPlotLinks` skip stubs with real GREEN assertions** — `a7d5ee3` (test)

**Plan metadata commit:** will be created by orchestrator after merging this worktree (Plan 02 does not commit STATE.md / ROADMAP.md per parallel-executor rules).

## Files Created/Modified

### Created (2)
- `sphsim/report/__init__.py` (21 LoC) — Package marker. `from sphsim.report.markdown import render_report`; `__all__ = ['render_report']`. Contains a placeholder comment block marking where Plan 04 will insert `write_report`.
- `sphsim/report/markdown.py` (214 LoC) — Production module. Contents:
  - Module docstring + stdlib imports (`json`, `datetime`, `pathlib.Path`)
  - `from sphsim.cli.output import format_config_header`
  - `BASELINE_PATH = Path(__file__).resolve().parent.parent.parent / 'tests' / 'fixtures' / 'baseline_v1' / '08-naive-zeta-0.75-baseline.json'`
  - `_KPI_ROWS` canonical 5-tuple
  - `render_report(args, res, params, K1, *, mode='single')` — public entry
  - 8 private helpers: `_render_title`, `_render_strategy_params`, `_extract_metrics_source`, `_render_kpi_table`, `_render_decision_table`, `_render_plots_section`, `_render_baseline_comparison`, `_render_compare_section`

### Modified (1)
- `tests/test_report.py` (97 → 190 LoC, +93 LoC) — Added `argparse` import; 3 module-level fixture builders (`_make_args`, `_make_single_res`, `_make_compare_res`); replaced `TestReportSections.test_placeholder` with 5 GREEN tests; replaced `TestPlotLinks.test_placeholder` with 2 GREEN tests. TestReportFiles / TestReportCompareMode / TestJsonStdoutClean stay as skip stubs (Plan 04 owns them).

## H2 Section Emission Audit

### Single mode (mode='single') — 6 sections

```
## Konfiguracja środowiska
## Strategia i parametry
## Metryki KPI
## Rozkład decyzji per faza
## Wykresy
## Porównanie z baseline `naive --zeta 0.75 --no-agent`
```

### Compare mode (mode='compare') — 7 sections

```
## Konfiguracja środowiska
## Strategia i parametry
## Metryki KPI
## Rozkład decyzji per faza
## Wykresy
## Porównanie z baseline `naive --zeta 0.75 --no-agent`
## Porównanie z RationalAgent (with-agent vs bez agenta)
```

Output size (single mode, sanity render): ~1.6 KB / ~50 lines.

## Verification

```bash
# 1. New tests GREEN
SPHSIM_NO_REPORT=1 python3 -m unittest tests.test_report.TestReportSections tests.test_report.TestPlotLinks -v
#  → Ran 7 tests in 0.004s — OK

# 2. Full suite intact
SPHSIM_NO_REPORT=1 python3 -m unittest discover tests/
#  → Ran 164 tests in 6.736s — OK (skipped=5)

# 3. Regression 8/8 preserved
SPHSIM_NO_REPORT=1 python3 scripts/regression_check.py
#  → PASS: 8/8

# 4. Render sanity
python3 -c "from sphsim.report import render_report; ..." (single mode)
#  → 1663 bytes / 6 H2 sections / both PLOT-03 links present / BASELINE_PATH resolves
```

## Deviations from Plan

None — plan executed exactly as written. Only minor textual change: rephrased two docstring lines in `sphsim/report/__init__.py` from "matplotlib plotters" / "matplotlib side" to "plot generators" / "plotting side" so the acceptance criterion `grep -c 'matplotlib' sphsim/report/__init__.py sphsim/report/markdown.py = 0` reads zero strictly. Functionally equivalent; no behavioral change.

## Scope Boundary Verification

Files outside Plan 02's scope explicitly NOT touched (parallel-safety with Plan 03 and downstream Plan 04):

| File | Plan owner | Touched in this commit set? |
|------|------------|------------------------------|
| `sphsim/report/plots.py`  | Plan 03 | NO |
| `tests/test_plots.py`     | Plan 03 | NO |
| `sphsim/cli/main.py`      | Plan 04 | NO |
| `sphsim/cli/repl.py`      | Plan 04 | NO |
| `.planning/STATE.md`      | Orchestrator | NO |
| `.planning/ROADMAP.md`    | Orchestrator | NO |

Confirmed via `git diff --name-only 479b75f..HEAD` — only `sphsim/report/__init__.py`, `sphsim/report/markdown.py`, `tests/test_report.py` modified.

## Plan 04 Hand-off Notes

When Plan 04 (Wave 3) lands `write_report`, it will need to:

1. **Modify `sphsim/report/__init__.py`** — replace the placeholder comment block with the `write_report(...)` body + the helpers (`_timestamp`, `_resolve_report_dir`, `os` / `sys` / `datetime` imports as needed). The current `from sphsim.report.markdown import render_report` line must be preserved.
2. **Flesh out 3 remaining test classes** in `tests/test_report.py`:
   - `TestReportFiles` (REPORT-01: ./reports/<ts>/ creation + mkdir collision suffix-N + SPHSIM_NO_REPORT opt-out)
   - `TestReportCompareMode` (REPORT-03: end-to-end --compare-agent → MD file content check via subprocess)
   - `TestJsonStdoutClean` (SC#6: --json stdout JSON-parseability while report banner goes to stderr — Pitfall 3 mitigation)
3. The module-level helpers (`_make_args`, `_make_single_res`, `_make_compare_res`) are available for reuse.
4. The `render_report` API surface MUST remain stable — `(args, res, params, K1, *, mode)` signature; do NOT add positional params; new keyword-only params OK if defaulted.

## Known Stubs

None. Section 6 (`_render_baseline_comparison`) has a graceful-degradation branch for missing fixture, but this is intentional defensive code, not a stub — fixture is committed and verified present (`BASELINE_PATH.exists() == True`).

## Threat Flags

None — Plan 02 surface matches threat model registered in the plan frontmatter. No new network endpoints, file access patterns at trust boundaries, or schema changes introduced. The single new filesystem read (BASELINE_PATH read-only) was registered as T-6-02-01 in the plan's STRIDE table.

## Self-Check: PASSED

- **Files exist:**
  - `sphsim/report/__init__.py` — FOUND
  - `sphsim/report/markdown.py` — FOUND
  - `tests/test_report.py` (modified, exists) — FOUND
- **Commits exist (verified via `git log --oneline 479b75f..HEAD`):**
  - `d2f2f2d` — FOUND (feat: report package + render_report)
  - `a7d5ee3` — FOUND (test: TestReportSections + TestPlotLinks GREEN)
- **Out-of-scope files untouched:** confirmed (sphsim/report/plots.py, tests/test_plots.py, sphsim/cli/main.py, sphsim/cli/repl.py, .planning/STATE.md, .planning/ROADMAP.md all unmodified).
- **All success criteria from PLAN.md met:**
  1. `sphsim/report/__init__.py` re-exports `render_report` + reserves placeholder for Plan 04 — YES
  2. `sphsim/report/markdown.py` implements `render_report` + 7 private helpers + `BASELINE_PATH` + `_KPI_ROWS` — YES (8 helpers total counting `_extract_metrics_source`)
  3. Single = 6 H2 sections, compare = 7 — YES (audit table above)
  4. PLOT-03 satisfied — YES (both relative MD links emitted verbatim)
  5. Baseline section loads fixture + emits 5-KPI Δ + Polish disclaimer + graceful degradation — YES
  6. TestReportSections (5) + TestPlotLinks (2) GREEN — YES (Ran 7 tests — OK)
  7. Zero matplotlib reference + zero filesystem write — YES (`grep -c matplotlib` = 0 across both prod files; `grep -cE 'mkdir|write_text|write_bytes|open\('` = 0 in markdown.py)
  8. Phase 1-5 + Plan 01 suite green + regression 8/8 preserved — YES (164 OK, 5 skipped; regression PASS 8/8)
