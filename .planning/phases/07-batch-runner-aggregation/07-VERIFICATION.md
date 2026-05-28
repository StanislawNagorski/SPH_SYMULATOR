---
phase: 7
slug: batch-runner-aggregation
date: 2026-05-28
status: passed
sc_pass: 5/5
req_pass: 4/4
pitfalls_defused: 7/7
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 7: Batch runner + aggregation — Verification Report

**Phase Goal:** Użytkownik może uruchomić tę samą strategię dla wielu seedów i otrzymać raport z agregacją statystyczną (mean/std/CI) oraz box-plotami KPI.
**Verified:** 2026-05-28
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

Codebase delivers Phase 7's promise end-to-end. A user invoking `python sph_sim.py --strategy <name> --batch --seeds N` (CLI) or `batch <name> --seeds N|list` (REPL) drives `sphsim/batch/runner.py::run_batch`, which sequentially invokes `SPHSimulator(...).run()` per seed (deterministic reseed in `__init__`), then `sphsim/batch/stats.py::aggregate_kpis` produces mean/std/min/max/95% CI via `scipy.stats.t.interval(0.95, df=n-1)`. `sphsim/report/batch_markdown.py::render_batch_report` emits a 7-section MD report with per-seed table (N rows × 6 cols), aggregate table (5 KPI × 7 cols), boxplot link, and baseline-beating verdict driven by `BASELINE_PATH` (Phase 6 single source of truth — zero hardcoded 92.0). `sphsim/report/plots.py::plot_batch_aggregate` writes a real 1800×480 RGBA PNG with `plt.subplots(1, 5, ...)` (5 panels — not a single grouped boxplot). Both `--no-agent` and default-agent branches in `sphsim/cli/main.py` route through `run_batch`. All 4-way mutex checks (`--batch` vs `--compare-agent`/`--interactive`/missing `--seeds`/`--seeds` without `--batch`) emit Polish error messages with exit code 2. Exit gate `scripts/verify_phase7.sh` reports **PASS=32 / FAIL=0** (≥30 threshold). Full test suite green at 205/205 (33 Phase-7 tests in `tests/test_batch{,_stats,_report}.py`). Regression `scripts/regression_check.py` returns 8/8.

---

## Success Criteria

| SC# | Description | Source Anchor | Behavioral Proof | Status |
|-----|-------------|---------------|------------------|--------|
| 1 | `--batch --seeds N` (CLI) / `/batch <name> --seeds N` (REPL); `--seeds 1,5,42,100` explicit list | `sphsim/cli/args.py:79-132` (`_parse_seeds_list` + `MAX_SEEDS=1000`); `sphsim/cli/args.py:173-176` (`--batch`+`--seeds` flags); `sphsim/cli/args.py:198-205` (4-way post-parse mutex); `sphsim/cli/repl.py:319-404` (`SPHShell.do_batch`); `sphsim/cli/main.py:92-102`,`148-159` (batch early branch both builtin+custom) | `--batch --seeds 5 --no-agent` → 5-seed range expansion (`[1..5]`), aggregate produced; `--batch --seeds 1,5,42 --no-agent` → explicit list, N=3 aggregate. `_parse_seeds_list('1,1,2')` → `[1, 2]` (dedup). `--seeds 0` exits 2 with `--seeds: N musi być dodatnie (> 0); podano: 0.`. `--seeds 1001` exits 2 with `przekracza limit 1000`. `--batch` without `--seeds` exits 2 with `Flaga --batch wymaga --seeds`. `--seeds 3` without `--batch` exits 2 with `--seeds wymaga --batch`. REPL `batch naive --seeds 3` produces report + banner | ✓ VERIFIED |
| 2 | Batch MD report contains per-seed table (1 row/seed: seed + 5 KPI) and aggregate section (mean/std/min/max/95% CI) per KPI | `sphsim/report/batch_markdown.py:81-97` (`_render_per_seed_table`); `:100-121` (`_render_aggregate_table` with 5 KPI × 7 cols incl. N) | Live report inspection: per-seed table has 5 rows (header `\| Seed \| avg_val_last100 \| cum_val_total \| avg_net_profit \| delivery_ratio \| avg_providers_l100 \|` + 5 data rows). Aggregate table: `\| KPI \| mean \| std \| min \| max \| 95% CI \| N \|` + 5 KPI rows. CI emits `(lower, upper)` for N≥2 and `n/a (N=1)` via `AggregateStat.ci_str` for N=1 | ✓ VERIFIED |
| 3 | `batch_aggregate.png` with 5-KPI box-plots generated and linked in report | `sphsim/report/plots.py:122-173` (`plot_batch_aggregate` with `plt.subplots(1, 5, figsize=(15,4), dpi=120)`); `sphsim/report/__init__.py:208-212` (`write_batch_report` invokes it); `sphsim/report/batch_markdown.py:124-129` (link section) | `file reports/batch_<ts>/batch_aggregate.png` → `PNG image data, 1800 x 480, 8-bit/color RGBA, non-interlaced` (82 KB — real matplotlib output, not 1×1 stub). MD report contains line `![Box-ploty 5 KPI dla N seedów](batch_aggregate.png)` (relative path, GitHub/VSCode-compatible). Exit gate check PASS for size > 10 KB and PNG signature `\x89PNG` | ✓ VERIFIED |
| 4 | Batch works with RationalAgent (default) and `--no-agent` (for statistical comparison) | `sphsim/batch/runner.py:55-57` (conditional `wrap_with_agent` based on `args.no_agent`); `sphsim/cli/main.py:148-159` (built-in branch); `sphsim/cli/main.py:91-102` (custom branch); `sphsim/cli/repl.py:382-391` (REPL fake_args with `no_agent=False`) | `--batch --seeds 5 --no-agent` → report header line `\| Tryb agenta \| wyłączony (\`--no-agent\`) \|`. Default `--batch --seeds 3` (no `--no-agent` flag) → report header line `\| Tryb agenta \| włączony (domyślnie) \|`. Different mean/CI values across both modes confirm wrapper is active in default and bypassed with `--no-agent` | ✓ VERIFIED |
| 5 | Batch report clearly indicates whether strategy beats baseline `naive --zeta 0.75` (whether 95% CI for `avg_val_last100` > 92) | `sphsim/report/batch_markdown.py:132-162` (`_render_baseline_beating` reads `BASELINE_PATH`); `sphsim/cli/output.py:203-257` (`format_batch_summary` reads `BASELINE_PATH`); `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` (canonical baseline source) | Live report verdict line: `✗ NIE — CI_lower=1.76 ≤ baseline=92.0`. Synthetic N=1 case with mean=100.0 → `✓ TAK — mean=100.00 > baseline=92.0` followed by `*N=1: brak CI, werdykt na podstawie pojedynczego punktu.*` disclaimer. `grep -v BASELINE_PATH sphsim/cli/output.py \| grep -c '92.0'` returns **0** — zero hardcoded baseline literals (Plan-checker BLOCKER #1 mitigation verified) | ✓ VERIFIED |

**Score:** 5/5 truths verified

---

## Requirement Coverage

| REQ-ID | Description | Implementation Files | Test Coverage | Status |
|--------|-------------|----------------------|---------------|--------|
| BATCH-01 | User can run `/batch <strategy> --seeds N` or `--seeds 1,2,3,...` for multi-seed simulation | `sphsim/cli/args.py:79-132,173-176,198-205` (parser + flags + mutex); `sphsim/batch/runner.py` (orchestrator); `sphsim/cli/main.py:92-102,148-159` (CLI branches); `sphsim/cli/repl.py:319-404` (REPL command) | `tests/test_batch.py::TestSeedsParser` (8 tests: single N, list, dedup, reject 0/neg/empty/non-int/oversized); `TestArgsMutex` (3 tests); `TestDeterminism` (2 tests); `TestReplBatch` (2 tests); `TestCliReplParity` (2 tests) — **17 tests green** | ✓ SATISFIED |
| BATCH-02 | Batch results aggregated: mean, std, min/max, 95% CI per KPI | `sphsim/batch/stats.py:30-140` (`KPIS` tuple + `AggregateStat` dataclass + `aggregate_kpis` with `scipy.stats.t.interval` + ddof=1 sample std + N=1 guard + zero-variance N≥2 guard) | `tests/test_batch_stats.py::TestAggregateKpis` (3 tests); `TestCIComputation` (1 synthetic 95% coverage); `TestN1Degenerate` (2 tests: field values + no RuntimeWarning); `TestEmptyInput` (1 test: ValueError on N=0); `TestStatsDeterminism` (1 test) — **9 tests green** | ✓ SATISFIED |
| BATCH-03 | Batch MD report contains per-seed table + aggregate statistics section | `sphsim/report/batch_markdown.py:28-162` (`render_batch_report` + 6 sub-renderers); `sphsim/report/__init__.py:156-230` (`write_batch_report` orchestrator with mkdir/exception isolation/opt-out) | `tests/test_batch_report.py::TestBatchReport` (5 tests: per-seed table, aggregate table, baseline verdict N≥2 + N=1, PNG link); plus exit-gate checks for header/rows/aggregate KPI count — **7 tests green** | ✓ SATISFIED |
| PLOT-04 | Batch mode generates additional `batch_aggregate.png` with box-plots of KPI | `sphsim/report/plots.py:122-173` (`plot_batch_aggregate` with 5-subplot 1×5 grid + per-KPI individual Y-axes + matplotlib Agg backend + close-in-finally); `sphsim/report/__init__.py:207-212` (invocation from `write_batch_report`) | `tests/test_batch_report.py::TestBatchPlots` (2 tests: 5-panel mock assertion + actual PNG file size sanity) — **2 tests green** within `test_batch_report.py`'s 7 total | ✓ SATISFIED |

**Coverage:** 4/4 REQ-IDs satisfied

---

## Pitfall Defusal

RESEARCH §H lists 7 pitfalls (not 10 — verification context mis-stated count; verifier honors the actual RESEARCH content). All 7 mitigations present in code.

| # | Pitfall (RESEARCH §H) | Mitigation in code | Status |
|---|-----------------------|--------------------|--------|
| 1 | matplotlib state leak between figures (PLOT-04) | `sphsim/report/plots.py:155-173` — `plt.subplots(...)` wrapped in `try: ... fig.savefig(path) finally: plt.close(fig)` | ✓ DEFUSED |
| 2 | REPL state contamination across `/batch` invocations | `sphsim/cli/repl.py:319-404` — `do_batch` uses only local variables, rebuilds `fake_args` from `DEFAULT_*` constants each call, no `self.*` instance state | ✓ DEFUSED |
| 3 | Floating-point determinism if numpy version differs | `sphsim/batch/stats.py:118-128` — zero-variance guard for `sem=0` returns degenerate `(mean, mean)` CI instead of NaN-NaN (which would break dataclass equality); `requirements.txt` pins `numpy>=2.3.0` and `scipy>=1.16.0`; tests use `assertAlmostEqual` semantics where appropriate | ✓ DEFUSED |
| 4 | `--no-agent` baseline semantics for SC #5 | `sphsim/report/batch_markdown.py:140` — verdict header hardcodes `naive --zeta 0.75` reference text; baseline always read from same `BASELINE_PATH` fixture regardless of batch agent mode | ✓ DEFUSED |
| 5 | File path collisions if two batches run in same directory | `sphsim/report/__init__.py:190-198` — mkdir collision-retry loop with `-N` suffix on `Path('reports') / f'batch_{ts}'` (mirrors Phase 6 `_resolve_report_dir` pattern) | ✓ DEFUSED |
| 6 | scipy/numpy NEW dependency — explicit signal | `requirements.txt` exists at repo root with `matplotlib>=3.10.0`, `numpy>=2.3.0`, `scipy>=1.16.0` (Phase 7 closeout per RESEARCH recommendation) | ✓ DEFUSED |
| 7 | Custom strategy `expected_P` propagation in batch+REPL | `sphsim/cli/repl.py:390` — `expected_P=params.get('expected_P', DEFAULT_K0)` in `do_batch` fake_args; `sphsim/batch/runner.py:57` — `wrap_with_agent(raw_strategy_fn, args.expected_P)` uses `args.expected_P` | ✓ DEFUSED |

**Defused:** 7/7

---

## Plan-Checker Spot Checks

| Concern | Check | Result |
|---------|-------|--------|
| Plan 03: `format_batch_summary` reads `BASELINE_PATH` (not hardcoded 92.0) | `grep -v BASELINE_PATH sphsim/cli/output.py \| grep -c '92.0'` | **0** ✓ |
| Plan 04: N=1 verdict emits explicit disclaimer | `grep '*N=1: brak CI' sphsim/report/batch_markdown.py` | Line 161: `disclaimer = "*N=1: brak CI, werdykt na podstawie pojedynczego punktu.*"` ✓ |
| Plan 04: `plot_batch_aggregate` uses `plt.subplots(1, 5, ...)` | `grep 'subplots(1, 5' sphsim/report/plots.py` | Line 155: `fig, axes = plt.subplots(1, 5, figsize=(15, 4), dpi=120)` ✓ |
| Plan 05: REPL `do_help` shows `batch` AFTER `compare` | `grep -n 'print("  \(compare\|batch\)' sphsim/cli/repl.py` | Line 71 (`compare`) then Line 72 (`batch`) — correct order ✓ |
| Plan 06: ROADMAP says "7 plans" + "7/7 Complete" | `.planning/ROADMAP.md:218,258` | Line 218: `**Plans**: 7 plans`; Line 258: `\| 7. Batch runner + aggregation \| 7/7 \| Complete \| 2026-05-28 \|` ✓ |
| Plan 06: STATE has completed_phases=7 / total_plans=32 / percent=100 | `.planning/STATE.md` frontmatter | `completed_phases: 7`, `total_plans: 32`, `percent: 100` ✓ |

All 6 plan-checker concerns hold.

---

## Exit Gate Result

### `scripts/verify_phase7.sh` summary

```
=== Phase 7: Batch runner + aggregation — verification ===
Interpreter: python3 (Python 3.14.3)

── 1. Regression backwards compat ──
[PASS] Regression: scripts/regression_check.py PASS=8/8
[PASS] ./reports/ NIE zaśmiecone po regression run

── 2. Full test suite (Phase 1-7) ──
[PASS] Unittest discover tests/ — 205 total green
[PASS] tests/test_batch_stats.py — 9 GREEN
[PASS] tests/test_batch.py — 17 GREEN
[PASS] tests/test_batch_report.py — 7 GREEN

── 3-7. SC #1..5 behavioral ── all PASS
── 8. REPL Pitfall regressions ── all PASS (3)
── 9. Mutex (4-way) ── all PASS (3)
── 10. Opt-out SPHSIM_NO_REPORT=1 ── PASS
── 11. Determinism ── PASS

════════════════════════════════════════
  Phase 7 verification: PASS=32 / FAIL=0
════════════════════════════════════════
✓ Phase 7 ready for /gsd:verify-work
```

Threshold required: ≥30 `check()` invocations. Actual: 32. ✓

### Full test suite (`SPHSIM_NO_REPORT=1 python3 -m unittest discover tests/`)

```
Ran 205 tests in 21.895s
OK
```

Phase 7 tests breakdown:
- `tests/test_batch_stats.py` — 9 tests (BATCH-02 stats module)
- `tests/test_batch.py` — 17 tests (BATCH-01 parser/mutex/orchestrator/REPL/parity)
- `tests/test_batch_report.py` — 7 tests (BATCH-03 + PLOT-04)
- **Phase 7 total: 33 tests, all green**
- Phase 1-6 invariants preserved: **205 total = 33 new + 172 pre-existing, all green**

Warnings noted (NOT failures):
- 5× `PendingDeprecationWarning: vert: bool will be deprecated` from `matplotlib.boxplot(vert=True, ...)` in `plot_batch_aggregate`. Pending (not deprecated yet) — non-blocking; documented as future cleanup (`orientation='vertical'` migration when matplotlib promotes the warning to `DeprecationWarning`).

### Regression (`SPHSIM_NO_REPORT=1 python3 scripts/regression_check.py`)

```
PASS: 8/8
```

Phase 1 baseline preserved end-to-end through Phase 7 changes. CLI-04 backwards compatibility intact.

---

## Verdict

**PASSED** — All 5 ROADMAP success criteria verified by source anchor + live behavioral proof; all 4 REQ-IDs satisfied with substantive test coverage (33 Phase-7 tests + 172 inherited); all 7 RESEARCH pitfalls defused in code; exit gate green at PASS=32/FAIL=0 (≥30 threshold); full suite green at 205/205; Phase 1 regression baseline 8/8 preserved. No human verification items identified — all behaviors are programmatically observable. No gaps. No deferred items. Phase 7 closes Milestone v1.1 Agent CLI.

---

_Verified: 2026-05-28_
_Verifier: Claude (gsd-verifier, Opus 4.7)_
