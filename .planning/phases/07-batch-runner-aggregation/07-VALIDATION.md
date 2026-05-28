---
phase: 7
slug: batch-runner-aggregation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-28
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `07-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (stdlib — consistent with Phases 1–6) |
| **Config file** | none — `python -m unittest discover tests/` |
| **Quick run command** | `SPHSIM_NO_REPORT=1 python -m unittest tests/test_batch.py tests/test_batch_stats.py tests/test_batch_report.py -v` |
| **Full suite command** | `SPHSIM_NO_REPORT=1 python -m unittest discover tests/ -v` |
| **Estimated runtime** | ~3s quick / ~20s full (172 prior tests + ~15 new in Phase 7) |

---

## Sampling Rate

- **After every task commit:** `SPHSIM_NO_REPORT=1 python -m unittest tests/test_batch*.py -v`
- **After every plan wave:** `SPHSIM_NO_REPORT=1 python -m unittest discover tests/ -v && SPHSIM_NO_REPORT=1 python scripts/regression_check.py`
- **Before `/gsd:verify-work`:** Full suite green + regression PASS=8/8 + `scripts/verify_phase7.sh` PASS≥30 / FAIL=0
- **Max feedback latency:** ~3 seconds (quick) — well under stall-detection threshold

---

## Per-Task Verification Map

| Req ID | Behavior | Test Type | Automated Command | File Exists | Status |
|--------|----------|-----------|-------------------|-------------|--------|
| BATCH-01 | `--seeds 10` parses to `[1..10]` | unit | `python -m unittest tests.test_batch.TestSeedsParser.test_single_n` | ❌ W0 | ⬜ pending |
| BATCH-01 | `--seeds 1,5,42` parses to `[1,5,42]` | unit | `python -m unittest tests.test_batch.TestSeedsParser.test_list` | ❌ W0 | ⬜ pending |
| BATCH-01 | `--seeds 0` raises ArgumentTypeError | unit | `python -m unittest tests.test_batch.TestSeedsParser.test_reject_zero` | ❌ W0 | ⬜ pending |
| BATCH-01 | `--seeds 1,1,2` deduplicates | unit | `python -m unittest tests.test_batch.TestSeedsParser.test_dedup` | ❌ W0 | ⬜ pending |
| BATCH-01 | `--batch` without `--seeds` → argparse error | unit | `python -m unittest tests.test_batch.TestArgsMutex.test_batch_requires_seeds` | ❌ W0 | ⬜ pending |
| BATCH-01 | `/batch <strategia> --seeds N` in REPL runs e2e | integration | `python -m unittest tests.test_batch.TestReplBatch.test_e2e` | ❌ W0 | ⬜ pending |
| BATCH-01 | `--batch + --compare-agent` → argparse error | unit | `python -m unittest tests.test_batch.TestArgsMutex.test_batch_compare_mutex` | ❌ W0 | ⬜ pending |
| BATCH-02 | mean/std correct on known 5-element sample | unit | `python -m unittest tests.test_batch_stats.TestAggregate.test_known_values` | ❌ W0 | ⬜ pending |
| BATCH-02 | 95% CI for N=10 matches hand-calc with `scipy.stats.t.ppf` | unit | `python -m unittest tests.test_batch_stats.TestAggregate.test_ci_against_manual` | ❌ W0 | ⬜ pending |
| BATCH-02 | N=1 degenerate: std=0, CI lower/upper = None | unit | `python -m unittest tests.test_batch_stats.TestAggregate.test_n1_degenerate` | ❌ W0 | ⬜ pending |
| BATCH-02 | 95% CI synthetic coverage on N=100 normals | unit | `python -m unittest tests.test_batch_stats.TestAggregate.test_ci_coverage` | ❌ W0 | ⬜ pending |
| BATCH-03 | Batch report.md contains "Wyniki per seed" with N rows | integration | `python -m unittest tests.test_batch_report.TestBatchReport.test_per_seed_table` | ❌ W0 | ⬜ pending |
| BATCH-03 | Batch report.md contains "Agregat statystyczny" 5×7 table | integration | `python -m unittest tests.test_batch_report.TestBatchReport.test_aggregate_table` | ❌ W0 | ⬜ pending |
| BATCH-03 | Batch report.md emits explicit "bije baseline" verdict | integration | `python -m unittest tests.test_batch_report.TestBatchReport.test_baseline_verdict` | ❌ W0 | ⬜ pending |
| BATCH-03 | Batch report.md links `![](batch_aggregate.png)` | unit | `python -m unittest tests.test_batch_report.TestBatchReport.test_png_link` | ❌ W0 | ⬜ pending |
| PLOT-04 | `batch_aggregate.png` exists, non-zero, valid PNG header | integration | `python -m unittest tests.test_batch_report.TestBatchPlots.test_png_exists` | ❌ W0 | ⬜ pending |
| PLOT-04 | Boxplot has 5 subplot panels | unit | `python -m unittest tests.test_batch_report.TestBatchPlots.test_5_panels` | ❌ W0 | ⬜ pending |
| BATCH-det | Same seed list twice → byte-identical per-seed KPIs | integration | `python -m unittest tests.test_batch.TestDeterminism.test_byte_identical` | ❌ W0 | ⬜ pending |
| BATCH-parity | CLI `--batch` and REPL `/batch` produce identical reports | integration | `python -m unittest tests.test_batch.TestCliReplParity.test_identical_output` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_batch.py` — TestSeedsParser (~7), TestArgsMutex (~3), TestReplBatch (~2), TestDeterminism (~1), TestCliReplParity (~1)
- [ ] `tests/test_batch_stats.py` — TestAggregate (~5 cases)
- [ ] `tests/test_batch_report.py` — TestBatchReport (~4) + TestBatchPlots (~2)
- [ ] `scripts/verify_phase7.sh` — exit gate, ≥30 `check()` invocations covering 5 SCs + 4 REQ-IDs + regression + REPL + opt-out (pattern verbatim from `verify_phase6.sh`)
- [ ] Framework install: **none** — `unittest` stdlib; `scipy`, `numpy`, `matplotlib` already installed (researcher verified runtime: scipy 1.16.3, numpy 2.3.5)
- [ ] `requirements.txt` — new file pinning `matplotlib`, `numpy`, `scipy` (Phase 7 introduces stats dep formally)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual sanity of `batch_aggregate.png` (5-panel boxplot readable, no overlap, Polish labels render) | PLOT-04 | Pixel-level image diff is brittle across matplotlib versions; humans verify legibility | Run `python -m sphsim --batch --strategy naive --seeds 10`, open the generated PNG, confirm 5 subplots visible with KPI names as titles and non-degenerate whiskers |
| Polish character rendering in MD report (KPI labels, baseline verdict copy) | BATCH-03 | Encoding bugs slip past ASCII-only test asserts | Open generated batch report MD and confirm `średnia`, `odchylenie`, `bije baseline` render correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s (quick suite)
- [ ] `nyquist_compliant: true` set in frontmatter (after Wave 0 lands)

**Approval:** pending
