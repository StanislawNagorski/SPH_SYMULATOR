---
phase: 07-batch-runner-aggregation
plan: 04
subsystem: report-renderer
tags: [batch, markdown, matplotlib, boxplot, baseline-verdict, ci-fallback, python, scipy, numpy, mock]

# Dependency graph
requires:
  - phase: 07-01
    provides: sphsim.batch.stats.aggregate_kpis + AggregateStat dataclass + KPIS tuple (BATCH-02)
  - phase: 07-03
    provides: sphsim.batch.run_batch orchestrator + main.py args.batch early-branches with reserved marker comments at TWO insertion points (custom ~line 99, built-in ~line 152)
  - phase: 06
    provides: sphsim.report.markdown.BASELINE_PATH + _KPI_ROWS + write_report orchestrator pattern + sphsim.report.plots Agg backend + Polish font fallback
  - phase: 04
    provides: sphsim.cli.output.format_config_header (single source of truth for env serialization, reused verbatim in Section 2 of batch report)
provides:
  - sphsim.report.batch_markdown.render_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list) -> str — pure 7-section MD assembler
  - sphsim.report.plots.plot_batch_aggregate(per_seed_kpis, path) — 5-subplot (1×5) boxplot PNG generator with plt.close-in-finally
  - sphsim.report.write_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list) -> Path | None — exception-isolated orchestrator producing reports/batch_<ts>/{report.md, batch_aggregate.png}
  - sphsim/cli/main.py both batch branches (built-in + custom) now invoke write_batch_report + print Polish stderr banner; Plan 03 TODO markers removed
  - tests/test_batch_report.py — 7 GREEN tests (5 TestBatchReport incl. test_baseline_verdict_n1 + 2 TestBatchPlots incl. mocked test_5_panels); was 2 SKIPPED placeholders
affects: [07-05, 07-06]

# Tech tracking
tech-stack:
  added: []  # No new deps — reuses Phase 6 matplotlib + numpy/scipy stack
  patterns:
    - "Pure-function MD renderer with section composition list (mirror Phase 6 render_report shape)"
    - "1×5 subplot grid via plt.subplots(1, 5, ...) — load-bearing positional args (Warning #6 mock contract)"
    - "BASELINE_PATH-driven verdict with N=1 fallback + explicit Polish disclaimer (Warning #7 mitigation)"
    - "4-layer exception isolation in write_batch_report (outer + mkdir + plot + MD)"
    - "Mock-based test of subplot grid shape via unittest.mock.patch('sphsim.report.plots.plt.subplots', wraps=...)"

key-files:
  created:
    - sphsim/report/batch_markdown.py — render_batch_report + 6 private helpers (158 lines)
    - .planning/phases/07-batch-runner-aggregation/07-04-SUMMARY.md — this file
  modified:
    - sphsim/report/plots.py — appended plot_batch_aggregate (+55 lines; total 175 lines)
    - sphsim/report/__init__.py — appended write_batch_report + extended __all__ (+82 lines; total 235 lines)
    - sphsim/cli/main.py — TWO 'if args.batch:' branches now call write_batch_report (TODO markers gone in both)
    - tests/test_batch_report.py — 2 skip-stub classes replaced with 7 GREEN tests (215 lines)

key-decisions:
  - "render_batch_report is a NEW pure function, not an extension of render_report (Phase 6) — batch layout (per-seed table + aggregate + boxplot) differs structurally from single-run layout (KPI/decisions/timeseries)"
  - "_render_baseline_beating reads BASELINE_PATH (Phase 6 single source of truth) via deferred json.loads — ZERO hardcoded 92.0 literals (BLOCKER #1 + Warning #7 compliance)"
  - "N=1 path emits BOTH verdict glyph (✓/✗) AND explicit Polish disclaimer '*N=1: brak CI, werdykt na podstawie pojedynczego punktu.*' — Warning #7 mitigation: readers cannot mistake an N=1 single-point verdict for statistical inference"
  - "test_5_panels uses unittest.mock.patch('sphsim.report.plots.plt.subplots', wraps=real_plt.subplots) — Warning #6 mitigation: directly asserts (nrows, ncols) == (1, 5) instead of relying on PNG-width-byte proxy that would be fragile against dpi/font/matplotlib-version changes"
  - "write_batch_report is a separate entrypoint from write_report — symmetric API but different signature (list[dict] + aggregate vs single res); avoids polluting write_report with mode='batch' branch"

patterns-established:
  - "Pure-function MD renderers (no IO) — caller orchestrator (write_batch_report) handles fs side effects. Plan 07-05 REPL command will reuse render_batch_report directly via fake_args."
  - "5-subplot (1×5) grid for KPIs spanning 5 orders of magnitude — single grouped boxplot would compress delivery_ratio (~0.79) to invisibility next to cum_val_total (~92000)"
  - "Mock-with-wraps pattern for asserting library-call shape while still executing the real call — preserves output artifacts while making structural contracts testable"

requirements-completed: [BATCH-03, PLOT-04]

# Metrics
duration: 7min
completed: 2026-05-28
---

# Phase 07 Plan 04: Batch Report Renderer + Boxplot PNG Summary

**Batch report MD (7 Polish-language sections) + 1×5 boxplot PNG grid + exception-isolated write_batch_report orchestrator — `python sph_sim.py --strategy naive --batch --seeds N` now produces `./reports/batch_<ts>/{report.md, batch_aggregate.png}` with baseline-beating verdict (N≥2 CI-based + N=1 mean + disclaimer fallback).**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-05-28T11:49:14Z
- **Completed:** 2026-05-28T11:56:41Z
- **Tasks:** 2 (both TDD: pre-existing skip-stubs satisfied the RED state)
- **Files modified:** 5 (1 new + 4 edited)

## Accomplishments

- **`sphsim/report/batch_markdown.py::render_batch_report`** — pure function composing 7 Polish-language MD sections (Title, Konfiguracja, Strategia, Per-seed table, Agregat, Wykresy, Werdykt). Reuses `format_config_header`, `BASELINE_PATH`, and `_KPI_ROWS` from Phase 6 — single source of truth. `_render_baseline_beating` handles both N≥2 (CI_lower comparison) and N=1 (mean comparison + explicit Polish disclaimer `*N=1: brak CI, werdykt na podstawie pojedynczego punktu.*`) per Warning #7.
- **`sphsim/report/plots.py::plot_batch_aggregate`** — 5-subplot (1×5) boxplot PNG generator. Each KPI gets its own Y-axis because 5 KPIs span 5 orders of magnitude (delivery_ratio ~0.79, cum_val_total ~92000). `plt.subplots(1, 5, figsize=(15, 4), dpi=120)` — the `(1, 5)` positional args are the assertable contract for Warning #6. `plt.close(fig)` in finally prevents FD leak.
- **`sphsim/report/write_batch_report`** — exception-isolated orchestrator producing `./reports/batch_<ts>/{report.md, batch_aggregate.png}`. Honors `SPHSIM_NO_REPORT=1` opt-out (Phase 6 contract). 4-layer try/except: outer (last-resort) + mkdir (collision-retry with `-N` suffix) + plot (continue on failure) + MD render (return None on failure). Deferred imports inside try blocks to avoid circular import risk. `__all__` extended to include `'write_batch_report'`.
- **`sphsim/cli/main.py`** — BOTH built-in (line ~145) and custom (line ~92) `args.batch` early-branches now invoke `write_batch_report` BEFORE `format_batch_summary`, and print `'Raport batchowy zapisany do: <path>/report.md'` to `sys.stderr` when `report_dir` is non-None. Plan 03 TODO markers (`# NOTE: Plan 07-04 will add write_batch_report(...) here.`) are removed at both sites.
- **`tests/test_batch_report.py`** — 2 skip-stub classes replaced with 7 GREEN tests:
  * `TestBatchReport` (5): `test_per_seed_table`, `test_aggregate_table`, `test_baseline_verdict` (✓ TAK + ✗ NIE branches), `test_baseline_verdict_n1` (Warning #7 — both verdict glyph + literal disclaimer string), `test_png_link`.
  * `TestBatchPlots` (2): `test_png_exists` (signature + ≥10KB), `test_5_panels` (Warning #6 — mocked `plt.subplots` asserts `(nrows, ncols) == (1, 5)`).

## Task Commits

Each task was committed atomically:

1. **Task 1: Create `batch_markdown.py` + extend `plots.py` + extend `__init__.py`** — `741f4fb` (feat)
2. **Task 2: Wire `write_batch_report` into `main.py` + green `test_batch_report.py`** — `763a2f7` (feat)

## Files Created/Modified

- `sphsim/report/batch_markdown.py` (NEW, 158 lines) — `render_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list) -> str` + 6 private helpers (`_render_title`, `_render_strategy_params`, `_render_per_seed_table`, `_render_aggregate_table`, `_render_boxplot_section`, `_render_baseline_beating`). Imports `BASELINE_PATH` + `_KPI_ROWS` from `sphsim.report.markdown` (no duplication of Phase 6 constants). `_render_baseline_beating` reads baseline_avg via `json.loads(BASELINE_PATH.read_text())` and dispatches on `val_stat.ci_lower is None`: N≥2 → CI-based verdict; N=1 → mean-based verdict + Polish disclaimer.
- `sphsim/report/plots.py` (MOD, +55 lines; total 175) — appended `plot_batch_aggregate(per_seed_kpis, path)` at EOF. Reuses module-top Agg backend + DejaVu Sans font fallback (Polish diacritic support). `KPI_LABELS` list with 5 (key, polish_multiline_label) tuples. `plt.subplots(1, 5, figsize=(15, 4), dpi=120)` — positional contract. Try/finally with `plt.close(fig)`. Defensive empty-input guard returns early without writing.
- `sphsim/report/__init__.py` (MOD, +82 lines; total 235) — `__all__` extended from `['write_report', 'render_report']` to `['write_report', 'render_report', 'write_batch_report']`. Appended `write_batch_report` after `write_report`. Pattern mirrors `write_report` exactly: opt-out env var check → outer try/except → mkdir with collision retry → plot (continue on failure) → MD render (return None on failure) → return report_dir.
- `sphsim/cli/main.py` (MOD) — TWO 4-line insertions replacing Plan 03 TODO markers in both `args.batch` early-branches. Each insertion: deferred import `from sphsim.report import write_batch_report` → call `write_batch_report(args, per_seed_results, aggregate, params, K1, args.seeds)` → conditional stderr banner. Order: `write_batch_report` → stderr banner → `print(format_batch_summary(...))` to stdout (matches Phase 6 compare-branch pattern).
- `tests/test_batch_report.py` (MOD, ~58 → 215 lines) — preserved Plan 00 header (sys.path bootstrap + `_run_sph` subprocess helper). Added top-level imports: `argparse`, `shutil`, `tempfile`, `unittest.mock.patch`, and the three new Phase 7 modules (`sphsim.batch.stats`, `sphsim.report.batch_markdown`, `sphsim.report.plots`, `sphsim.report`). Added helpers `_make_args`, `_make_per_seed_results`, `_make_per_seed_results_high`, `_make_per_seed_results_low`. Both classes use setUp/tearDown with tempdir + chdir + SPHSIM_NO_REPORT pop (PATTERNS §2l).

## Decisions Made

- **`render_batch_report` is a NEW module, not an extension of `render_report`** — batch layout (per-seed N×6 table + aggregate 5×7 table + boxplot link + baseline-beating verdict) differs structurally from single-run layout (KPI 5×3 + decisions per-phase + timeseries + baseline comparison). Branching `render_report` on `mode='batch'` would scatter batch-specific logic across `_render_decision_table`, `_render_kpi_table`, etc. A clean separate module is more maintainable.
- **`_render_baseline_beating` reads `BASELINE_PATH` via deferred `json.loads`** — single source of truth with Phase 6 (`sphsim/report/markdown.py:21-25`). Zero hardcoded 92.0 literals: changing the baseline fixture file auto-updates ALL verdicts (Plan 03 stdout summary + Plan 04 MD report). BLOCKER #1 mitigation + Warning #7 mitigation both rely on this.
- **N=1 fallback emits BOTH verdict glyph AND Polish disclaimer** (Warning #7) — without the disclaimer, an N=1 ✓ TAK could be misread as statistical inference. With `*N=1: brak CI, werdykt na podstawie pojedynczego punktu.*`, the limitation is explicit. The disclaimer is asserted as a verbatim substring in `test_baseline_verdict_n1`.
- **`test_5_panels` uses `unittest.mock.patch` with `wraps=...`** (Warning #6) — `wraps=real_plt.subplots` keeps the real function executing (figure created, PNG written) while recording the call args. The patch target is `'sphsim.report.plots.plt.subplots'` (namespace where the name is LOOKED UP), not `'matplotlib.pyplot.subplots'` (where it's DEFINED) — classic Python mock idiom. The assertion `(nrows, ncols) == (1, 5)` accepts both positional and kwarg forms via `args[i] if len(args) > i else kwargs.get(...)`.
- **`write_batch_report` is a separate entrypoint from `write_report`** — symmetric API (same shape, same exception isolation, same opt-out) but different signature (`per_seed_results`, `aggregate`, `seeds_list` instead of `res`). Branching `write_report` on `mode='batch'` would pollute the single-run path with batch-specific argument handling. Single-responsibility wins.
- **5-subplot (1×5) grid, not 1 grouped boxplot** — 5 KPIs span 5 orders of magnitude (`avg_val_last100`~92, `cum_val_total`~92000, `delivery_ratio`~0.79). Single Y-axis would compress `delivery_ratio` to invisibility. Per-KPI subplots give each metric its own scale and a percent formatter for `delivery_ratio`. Verified visually in RESEARCH §F.13.
- **Helpers `_make_per_seed_results_high` / `_make_per_seed_results_low`** added to test file (not in plan) — without dedicated high/low generators, `test_baseline_verdict` would need inline dict literals for both verdict branches, hurting readability. The high variant uses avg_val_last100≈95.0 (>baseline 92.0) and low variant uses ≈50.0 — both clearly outside the noise band of `_make_per_seed_results`'s 92.0+0.5i values which sit right at the boundary.

## Deviations from Plan

None — plan executed exactly as written.

The one deliberate addition is the test-helper variants `_make_per_seed_results_high` / `_make_per_seed_results_low` to keep `test_baseline_verdict` readable. These are pure test-fixture builders, not behavior changes. The base `_make_per_seed_results` helper remains exactly as specified in the plan.

A `PendingDeprecationWarning` for matplotlib's `vert: bool` keyword (will be replaced by `orientation`) surfaces during `boxplot` calls. This is a future matplotlib API change, not a current bug — explicitly out of scope for this plan. Tracked for Phase 7 plan-06 verify script if needed.

**Total deviations:** 0
**Impact on plan:** None.

## Issues Encountered

- **Worktree HEAD was behind main on agent startup** — branch `worktree-agent-ac91e8ec` was at commit `643fc85` ("Feedback zajacia") but main was at `7d0440b` (Plan 07-03 merge). Resolved per worktree branch check instructions via `git reset --hard main`. No work lost (the divergent commits were stale pre-Phase-7 user commits already committed to main).
- **Initial `SyntaxWarning` for `\``** — first draft of `batch_markdown.py` module docstring used `\`<strategia>\`` (escaped backticks) which triggered `SyntaxWarning: "\`" is an invalid escape sequence`. Fixed by switching to plain quotes in the docstring (backticks don't need escaping in Python strings; the `\` was a no-op that Python flagged). Caught by the smoke test, fixed before Task 1 commit.

## BLOCKER #1 + Warning #6 + Warning #7 Confirmation

```bash
# BLOCKER #1: zero hardcoded 92.0 literals in batch_markdown.py
$ grep -v BASELINE_PATH sphsim/report/batch_markdown.py | grep -c '92.0'
0
# Single mention of baseline path constant in import
$ grep -F 'from sphsim.report.markdown import BASELINE_PATH' sphsim/report/batch_markdown.py | wc -l
1

# Warning #6: test_5_panels uses mock-based assertion on plt.subplots
$ grep -F "patch('sphsim.report.plots.plt.subplots'" tests/test_batch_report.py | wc -l
1
$ grep -F "(nrows, ncols), (1, 5)" tests/test_batch_report.py | wc -l
1

# Warning #7: N=1 disclaimer literal present in both production code AND test
$ grep -F 'N=1: brak CI, werdykt na podstawie pojedynczego punktu' sphsim/report/batch_markdown.py | wc -l
1
$ grep -F 'N=1: brak CI, werdykt na podstawie pojedynczego punktu' tests/test_batch_report.py | wc -l
1
```

All three plan-checker mitigations fully satisfied.

## Verification Evidence

All 11 plan verification steps executed and passing:

1. **Public surface importable:** `from sphsim.report.batch_markdown import render_batch_report`, `from sphsim.report.plots import plot_batch_aggregate`, `from sphsim.report import write_batch_report` — all succeed; `'write_batch_report' in sphsim.report.__all__` is True.
2. **main.py wiring:** `grep -c 'write_batch_report' sphsim/cli/main.py` returns 4 (2 imports + 2 calls); `grep -c '# NOTE: Plan 07-04' sphsim/cli/main.py` returns 0.
3. **End-to-end CLI (no-agent, N=5):** `SPHSIM_NO_REPORT='' python3 sph_sim.py --strategy naive --zeta 0.5 --batch --seeds 5 --no-agent --seed 42` exits 0, prints `'Raport batchowy zapisany do: reports/batch_<ts>/report.md'` to stderr, then `=== BATCH SUMMARY ===` + 5 KPI rows + Werdykt to stdout.
4. **Per-file artifacts:** `report.md` + `batch_aggregate.png` both present in `reports/batch_<ts>/`; PNG signature `\x89PNG\r\n\x1a\n` confirmed; all 6 section headers (`## Konfiguracja środowiska`, `## Strategia i parametry`, `## Wyniki per seed`, `## Agregat statystyczny`, `## Wykresy`, `## Werdykt: bije baseline …`) present + the Title line; PNG link `(batch_aggregate.png)` present in MD.
5. **With agent (default) batch:** `SPHSIM_NO_REPORT='' python3 sph_sim.py --strategy naive --zeta 0.5 --batch --seeds 3 --seed 42` produces same banner — wrap_with_agent path also produces report.
6. **All 7 tests GREEN:** `Ran 7 tests in 0.206s — OK`.
7. **N=1 verdict test isolated:** `tests.test_batch_report.TestBatchReport.test_baseline_verdict_n1` — PASS (Warning #7 mitigation verified).
8. **5-panels mocked assertion:** `tests.test_batch_report.TestBatchPlots.test_5_panels` — PASS (Warning #6 mitigation verified).
9. **Opt-out works:** `SPHSIM_NO_REPORT=1 python3 sph_sim.py ... --batch ...` produces no files; `reports/` directory empty.
10. **Phase 1-6 regression:** `SPHSIM_NO_REPORT=1 python3 scripts/regression_check.py` → `PASS: 8/8` preserved.
11. **Full discover:** `Ran 204 tests in 17.548s — OK (skipped=2)` — only `TestReplBatch` + `TestCliReplParity` remain skipped (Plan 07-05 placeholders).

## Self-Check: PASSED

**Files exist:**
- `sphsim/report/batch_markdown.py` (158 lines) — contains `def render_batch_report`
- `sphsim/report/plots.py` (175 lines) — contains `def plot_batch_aggregate`
- `sphsim/report/__init__.py` (235 lines) — contains `def write_batch_report` + `__all__` listing it
- `sphsim/cli/main.py` (192 lines) — 2× `from sphsim.report import write_batch_report` + 2× `write_batch_report(args, ...)`
- `tests/test_batch_report.py` (215 lines) — 7 `def test_` methods across `TestBatchReport` + `TestBatchPlots`
- `.planning/phases/07-batch-runner-aggregation/07-04-SUMMARY.md` — this file

**Commits exist:**
- `741f4fb` — `feat(07-04): batch_markdown (N=1 disclaimer) + plot_batch_aggregate (1×5) + write_batch_report`
- `763a2f7` — `feat(07-04): main.py batch branches call write_batch_report + 7 GREEN tests`

## Threat Flags

None — Plan 04 introduces only filesystem writes under `./reports/batch_<ts>/` (the `_timestamp()` helper produces fs-safe 15-char ASCII strings; no user-controlled path data flows in). Threat register T-7-04-01/02/03 all addressed by existing patterns (Phase 6 `_timestamp` audit + `plt.close-in-finally` + try/except around `BASELINE_PATH` read).

## Next Phase Readiness

- **Plan 07-05 (Wave 4, REPL parity):** Has all primitives — `render_batch_report` is a pure function callable via `fake_args` from REPL; `write_batch_report` accepts the same args as the CLI path. The 2 remaining test skips (`TestReplBatch`, `TestCliReplParity`) can be greened by reusing the same `_make_args` + `_make_per_seed_results` helpers established in this plan.
- **Plan 07-06 (Wave 5, exit gate):** `scripts/verify_phase7.sh` can grep the produced `report.md` for all 6 H2 headers + PNG link + verdict glyphs; the PNG signature check is straightforward; baseline verdict for `naive --zeta 0.5 --batch --seeds 10` should reliably emit `✗ NIE bije baseline` (this strategy clearly fails — `avg_val_last100 ≈ 2.8 ≪ 92.0`). Use `--zeta 0.95` or `oracle` strategy for ✓ TAK verdicts in regression-test scenarios.
- **No blockers, no concerns.** All Phase 7 production code outside Plan 07-05's REPL command is now wired end-to-end; single-run path remains bit-identical when `--batch` is absent (early-branch returns BEFORE any single-run code; no shared state mutation).

---
*Phase: 07-batch-runner-aggregation*
*Plan: 04*
*Completed: 2026-05-28*

**Suggested commit message:** `feat(07-04): batch_markdown (N=1 disclaimer) + plot_batch_aggregate (1×5 subplot grid) + write_batch_report — BATCH-03 raport MD + PLOT-04 boxplot PNG + SC#5 baseline verdict + 7 GREEN tests`
