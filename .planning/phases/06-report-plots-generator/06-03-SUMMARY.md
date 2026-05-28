---
phase: 06-report-plots-generator
plan: 03
subsystem: report
tags: [matplotlib, agg-backend, plot-01, plot-02, png-rendering, headless, pitfall-1, pitfall-5, pitfall-7, parallel-wave-2]

# Dependency graph
requires:
  - phase: 06-report-plots-generator
    plan: 01
    provides: "abstain_per_phase return-key from sim.run() — PLOT-01 third bar group (without this Plan 01 data gap, PLOT-01 only renders 2 of 3 decision categories)"
  - phase: 06-report-plots-generator
    plan: 00
    provides: "tests/test_plots.py — TestPlots + TestPlotDimensions skip-stub classes replaced by this plan with 6 real GREEN tests (4+2)"
provides:
  - "sphsim/report/plots.py — first matplotlib surface in the entire repo, Agg backend pinned at module load (lines 13-15 — `import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt`)"
  - "plot_decision_distribution(ic_per_phase, veto_per_phase, abstain_per_phase, path) — PLOT-01 grouped bar chart COMMIT/ABSTAIN/VETO per faza (4 phases), figsize=(8,5) dpi=120, hex colors #2E7D32/#757575/#C62828, Polish labels"
  - "plot_kpi_timeseries(history, T, path) — PLOT-02 twin-axis line chart avg_val + avg_providers per cykl, figsize=(10,5) dpi=120, shaded last-100 window via axvspan(max(1,T-99), T) alpha=0.15"
  - "6 GREEN unit tests: TestPlots (4) + TestPlotDimensions (2) replacing Plan 00 skip-placeholders — PNG existence + size>1KB + magic-byte signature + Pillow dim probe (auto-skip if Pillow missing)"
affects: [06-04-entry-point-compare, 06-05-verify-script]

# Tech tracking
tech-stack:
  added:
    - "matplotlib 3.10.7 (slopcheck [OK], 22-year package, 30M+ weekly DLs, RESEARCH §P legitimacy audit) — first third-party dep beyond stdlib in this repo (PROJECT.md key decision)"
    - "numpy 2.3.5 (transitive dep of matplotlib — used only for `np.arange(len(phases))` in PLOT-01 bar offsets; no direct API exposure to callers)"
  patterns:
    - "Backend-pin invariant: `matplotlib.use('Agg')` MUST appear textually BEFORE the first `import matplotlib.pyplot as plt` ANYWHERE in the codebase. Verified clean slate (grep matplotlib/pyplot sphsim/ tests/ → 0 results) so Plan 03 is the canonical first surface. Any future matplotlib usage in other modules MUST import via `from sphsim.report.plots import ...` (which forces correct backend) or repeat the same 3-line preamble. Pitfall 1 mitigation — without Agg, macOS opens GUI window in headless context (CI/SSH crash)."
    - "Figure close discipline: EVERY plot function MUST wrap savefig in `try: ... fig.savefig(path) finally: plt.close(fig)`. Verified by grep count = 2 (one per function). Pitfall 5 mitigation — without close, matplotlib's global figure registry leaks fig objects, OOMs after ~100 test runs. The try/finally guarantees close even if savefig raises (e.g. read-only filesystem)."
    - "Font fallback rcParams set at MODULE level (line 19): `plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'sans-serif']`. Runs once at import time, before any plot call. Pitfall 7 mitigation — DejaVu Sans (matplotlib default on macOS/Linux) supports all Polish glyphs ą ę ł ń ó ś ź ż; Liberation Sans is fallback for Linux minimal installs where DejaVu may be missing."
    - "Defensive empty-input semantics: PLOT-01 falls back to phases [1,2,3,4] when ALL three input dicts are empty (still emits valid PNG — never crashes). PLOT-02 silent-returns when `history` is empty OR missing `'val'`/`'providers'` keys (caller — Plan 04 write_report — is expected to log Polish disclaimer on stderr). This is symmetric to Phase 4 simulator's defensive contract."
    - "Filesystem boundary: ONLY `fig.savefig(path)` writes to disk — zero `Path.mkdir()` / `Path.write_text()` / `Path.write_bytes()` calls (verified grep count 0). The caller (Plan 04 write_report) owns directory creation; plots.py treats `path` as a fully-resolved leaf file location."
    - "Test PNG validation triad: (a) `path.exists()`, (b) `path.stat().st_size > 1000` bytes (any real matplotlib PNG at dpi=120 figsize=(8,5) is ≥27KB; 1KB is safe floor), (c) PNG magic-byte header `b'\\x89PNG\\r\\n\\x1a\\n'` — stdlib-only (no Pillow required). Pillow dim probe is OPTIONAL TestPlotDimensions test — auto-skips with `unittest.skipTest` if PIL not importable."
    - "File-disjointness with Plan 02 (parallel Wave 2): Plan 03 owns ONLY `sphsim/report/plots.py` (NEW) and `tests/test_plots.py` (MODIFIED). Zero touches to `sphsim/report/__init__.py`, `markdown.py`, `tests/test_report.py`, `sphsim/cli/main.py`, or `sphsim/cli/repl.py`. Worktree merge with Plan 02 has no overlap surface."

key-files:
  created:
    - "sphsim/report/plots.py — 119 LoC, matplotlib Agg backend pin + 2 plot functions + try/finally close discipline + Polish labels"
    - ".planning/phases/06-report-plots-generator/06-03-SUMMARY.md — this file"
  modified:
    - "tests/test_plots.py — 47 → 151 LoC; Plan 00 stub bodies replaced with 6 real test methods (4 in TestPlots, 2 in TestPlotDimensions); added module-level `_PNG_MAGIC` constant + `_build_fake_decision_data()` + `_build_fake_history(T)` helpers; added `tempfile` import"

key-decisions:
  - "matplotlib.use('Agg') pinned at module load (lines 13-15) — not in a function-level deferred init. Rationale: backend can ONLY be set BEFORE any pyplot import, period. Lazy initialization would push the contract onto every caller and break the moment some future module imports pyplot first. Verified clean repo (zero existing matplotlib references) makes this safe — Plan 03 IS the first surface."
  - "PNG validation via stdlib magic-byte check (no Pillow REQUIRED). TestPlots core tests (4) use only `path.exists() + stat().st_size > 1000 + read(8) == b'\\x89PNG\\r\\n\\x1a\\n'` — exactly the trinity that proves matplotlib wrote a real PNG without depending on Pillow. The Pillow dim probe in TestPlotDimensions is OPTIONAL (auto-skips on ImportError) and only verifies cosmetic figsize×dpi math (≥1000×500 px for figsize=(10,5) dpi=120). RESEARCH §N.4 endorsed this layering."
  - "Defensive PLOT-01 fallback to phases [1,2,3,4] when all input dicts empty. Rationale: a phase-0 / pre-aggregation run should still produce a 'shape valid PNG' for downstream pipeline integration tests rather than crashing. Tested explicitly by `test_decision_distribution_handles_empty_inputs` — empty dicts in, 4-bar chart out (all bars height=0), PNG > 1 KB. Symmetric to simulator's empty-run robustness contract."
  - "Defensive PLOT-02 silent-skip on empty/incomplete history. Rationale: cleaner separation of concerns — plots.py renders what's given; write_report (Plan 04) is the layer that logs disclaimers on stderr when KPI data is missing. Tested by `test_kpi_timeseries_silent_skip_on_empty_history` — empty dict + missing-'providers' dict both produce zero PNG (no crash, no partial file)."
  - "Module-level rcParams font fallback set ONCE at import (not in each plot fn). Rationale: it's an idempotent process-global mutation; setting per-call adds N redundant assignments per test run. Module-load convention is matplotlib idiomatic (cf. matplotlib gallery examples)."
  - "File size T-scaling assertion (test_kpi_timeseries_size_scales_with_T) instead of literal byte threshold. Rationale: PNG size depends on matplotlib version + compression level + platform fonts. Asserting `size_long > size_short` is a structural invariant (more data points → more PNG bytes after RLE/deflate) that holds across matplotlib versions, whereas an absolute threshold like '>50 KB' would be brittle. Sample observed: T=100 → ~25KB, T=1000 → ~112KB."

requirements-completed: [PLOT-01, PLOT-02]

# Metrics
duration: 18min
completed: 2026-05-28
---

# Phase 6 Plan 03: matplotlib PNG Renderer (PLOT-01 + PLOT-02) Summary

Implementacja nowego modułu `sphsim/report/plots.py` — pierwszej powierzchni matplotlib w całym repozytorium. Zawiera dwie funkcje generujące PNG (PLOT-01 grouped bar chart decyzji per faza + PLOT-02 twin-axis line chart KPI w czasie), oba z `Agg` backendem przypiętym przed importem `pyplot` (Pitfall 1 — headless safety) i dyscypliną `try/finally + plt.close(fig)` (Pitfall 5 — memory-leak prophylaxis). 6 testów GREEN zastępuje placeholdery Plan 00.

## What Was Built

### sphsim/report/plots.py (NEW, 119 LoC)

**Backend pin (lines 13-15 — MUST be first matplotlib statements):**

```python
import matplotlib
matplotlib.use('Agg')          # MUST be before pyplot import — Pitfall 1
import matplotlib.pyplot as plt
```

Plus `plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'sans-serif']` na linii 19 (Pitfall 7 — Polish glyph fallback).

**plot_decision_distribution(ic_per_phase, veto_per_phase, abstain_per_phase, path):**

- Grouped bar chart 3 grup × N faz (sorted union kluczy z 3 dictów; fallback `[1,2,3,4]` przy pustych inputach)
- Colors: COMMIT=#2E7D32 (zielony), ABSTAIN=#757575 (szary), VETO=#C62828 (czerwony)
- figsize=(8,5), dpi=120
- Polish labels: xlabel='Faza urządzenia', ylabel='Liczba decyzji', title='Rozkład decyzji per faza', xticks=[f'Faza {p}' for p in phases]
- Grid axis='y', linestyle='--', alpha=0.4 (RESEARCH §B.9)
- try/finally + plt.close(fig)

**plot_kpi_timeseries(history, T, path):**

- Twin-axis line chart: ax1 (lewa, niebieska #1565C0) = avg_val; ax2 = ax1.twinx() (prawa, pomarańczowa #EF6C00) = avg_providers
- figsize=(10,5), dpi=120, linewidth=0.8, alpha=0.85
- Shaded last-100 window: `ax1.axvspan(max(1, T-99), T, alpha=0.15, color='grey')`
- Polish labels + suptitle 'Przebieg KPI w czasie symulacji (zaznaczone ostatnie 100 cykli)'
- Silent-return on empty history / missing 'val'/'providers' keys (defensive contract — write_report logs warning)
- try/finally + plt.close(fig)

### tests/test_plots.py (MODIFIED, 47 → 151 LoC)

Plan 00 placeholdery (`self.skipTest('Wave 2 — Plan 03 ...')`) zamienione na 6 rzeczywistych testów:

**TestPlots (4 tests GREEN):**

| Test | What it asserts |
|------|-----------------|
| test_decision_distribution_creates_valid_png | PLOT-01: PNG istnieje + size > 1 KB + magic header `\x89PNG\r\n\x1a\n` |
| test_kpi_timeseries_creates_valid_png | PLOT-02: ten sam trio |
| test_decision_distribution_handles_empty_inputs | empty dicts → fallback faz [1..4], wciąż PNG > 1 KB (no crash) |
| test_kpi_timeseries_silent_skip_on_empty_history | empty history + missing 'providers' → silent return (no PNG, no crash) |

**TestPlotDimensions (2 tests GREEN):**

| Test | What it asserts |
|------|-----------------|
| test_kpi_timeseries_size_scales_with_T | PNG dla T=1000 ma WIĘCEJ bajtów niż dla T=100 (no truncation, fidelity preserved) |
| test_kpi_timeseries_dimensions_via_pillow_optional | width≥1000 height≥500 (figsize=(10,5) dpi=120); auto-skip jeśli Pillow brak |

Module helpers: `_PNG_MAGIC = b'\x89PNG\r\n\x1a\n'`, `_build_fake_decision_data()`, `_build_fake_history(T=1000)`.

## Verification Results

```
=== 1. test_plots verbose ===
Ran 6 tests in 0.375s
OK
(0 skipped — Pillow 12.0.0 present)

=== 2. full suite ===
Ran 163 tests in 7.133s
OK (skipped=5)

=== 3. regression check (scripts/regression_check.py) ===
PASS: 8/8

=== 4. backend ===
backend OK: Agg
```

**Sample PNG sizes (smoke run with 1000-cycle synthetic data):**

| File | Size |
|------|------|
| decision_distribution.png | 27 531 bytes (~27 KB) |
| kpi_timeseries.png        | 112 015 bytes (~112 KB) |

## Files Touched (Strict Disjointness with Plan 02)

| File | Status | Lines |
|------|--------|-------|
| `sphsim/report/plots.py` | NEW | 119 |
| `tests/test_plots.py`    | MODIFIED | +112 / -7 |

**NOT touched by Plan 03** (Plan 02 + Plan 04 territory — verified):

- `sphsim/report/__init__.py` (Plan 02 creates; Plan 04 modifies to add `write_report`)
- `sphsim/report/markdown.py` (Plan 02 owns)
- `tests/test_report.py` (Plan 02 owns)
- `sphsim/cli/main.py` / `sphsim/cli/repl.py` (Plan 04 owns wiring)

Note: `sphsim/report/` directory was created by Plan 03 (no `__init__.py`) — Python 3.14 namespace package import semantics handle this until Plan 02 lands its `__init__.py`. The directory creation itself does not conflict with Plan 02; Plan 02 will simply add `__init__.py` inside it.

## Pitfalls Addressed

| Pitfall | Mitigation | Verification |
|---------|------------|--------------|
| 1 — matplotlib GUI backend on macOS/SSH | `matplotlib.use('Agg')` on line 14, BEFORE pyplot import on line 15 | `python3 -c "import sphsim.report.plots; import matplotlib; assert matplotlib.get_backend()=='Agg'"` → OK |
| 5 — matplotlib memory leak (figures not closed) | EVERY plot fn wraps savefig in `try/finally` + `plt.close(fig)` | `grep -c 'plt\.close(fig)' sphsim/report/plots.py` = 2 |
| 7 — Polish character font fallback | `plt.rcParams['font.sans-serif'] = ['DejaVu Sans', ...]` at module load | Live test: title `'Rozkład decyzji per faza'` renders without FontWarning; PNG ~27.5 KB confirms no font-missing-glyph artifacts |

## Threat Model Status

Wszystkie 4 threats z `<threat_model>` planu adresowane:

| Threat ID | Status | Note |
|-----------|--------|------|
| T-6-03-01 (matplotlib mem leak) | mitigated | `grep -c plt.close(fig)` = 2 (jeden per funkcja) |
| T-6-03-02 (headless GUI crash) | mitigated | Agg backend pin verified runtime |
| T-6-03-03 (PNG EXIF metadata) | accepted | matplotlib version is public; no PII/secrets |
| T-6-03-04 (savefig path symlink) | accepted | same trust model as v1.0; caller controls path |
| T-6-03-SC (supply chain pip install) | mitigated | matplotlib pre-audited RESEARCH §P, slopcheck [OK] |

## Suggested Commit Message (already used)

```
feat(06-03): wave 2 — plots.py matplotlib Agg + 2 PNG renderers + PLOT-01/02 tests
```

(Actual commits used per-task split: `feat(06-03): add sphsim/report/plots.py — ...` + `test(06-03): replace Plan 00 skip stubs with TestPlots(4) + TestPlotDimensions(2) GREEN`.)

## Deviations from Plan

None — plan executed exactly as written.

The plan's `<verify>` block referenced `python -c` (no `3`); local environment has `python3` only (`/opt/homebrew/bin/python3`, Python 3.14.3) — `python` is unavailable in PATH. All verification commands were run with `python3` (consistent with existing scripts' shebangs `#!/usr/bin/env python3` per `scripts/regression_check.py` and `scripts/generate_baseline.py`). This is a runtime interpreter alias mismatch only; no code or test change required.

## Commits

| Hash | Type | Subject |
|------|------|---------|
| 9e4e948 | feat | add sphsim/report/plots.py — matplotlib Agg backend + PLOT-01 + PLOT-02 |
| 7398a8e | test | replace Plan 00 skip stubs with TestPlots(4) + TestPlotDimensions(2) GREEN |

## Self-Check: PASSED

- `sphsim/report/plots.py` — exists (119 LoC, matplotlib.use('Agg') line 14 before pyplot line 15)
- `tests/test_plots.py` — exists (151 LoC, 6 test methods, helpers + `_PNG_MAGIC` present)
- Commit 9e4e948 — present in `git log --oneline`
- Commit 7398a8e — present in `git log --oneline`
- 6/6 test_plots tests GREEN (0 skipped)
- 163/163 full suite OK (skipped=5)
- regression_check.py PASS 8/8
- matplotlib backend == 'Agg'
- Plan 02 files untouched (sphsim/report/__init__.py, markdown.py, tests/test_report.py — none exist or modified by Plan 03)
