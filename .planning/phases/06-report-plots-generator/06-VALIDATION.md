---
phase: 6
slug: report-plots-generator
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-28
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `06-RESEARCH.md` Section H (Validation Architecture).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (stdlib — zgodnie z Phases 1-5) |
| **Config file** | none — testy odpalane przez `python -m unittest discover tests/` |
| **Quick run command** | `SPHSIM_NO_REPORT=1 python -m unittest tests/test_report.py tests/test_simulator_abstain.py -v` |
| **Full suite command** | `SPHSIM_NO_REPORT=1 python -m unittest discover tests/ -v` |
| **Estimated runtime** | ~3 s (quick) / ~15 s (full) |

---

## Sampling Rate

- **After every task commit:** Run quick command above
- **After every plan wave:** Run full suite + `SPHSIM_NO_REPORT=1 python scripts/regression_check.py`
- **Before `/gsd:verify-work`:** Full suite green + regression PASS=8/8 + `scripts/verify_phase6.sh` PASS≥20 / FAIL=0
- **Max feedback latency:** ~3 s for quick loop

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 6-00-01 | 00 | 0 | scaffolding | unit (stubs) | `python -m unittest tests.test_report -v` | ❌ W0 | ⬜ pending |
| 6-00-02 | 00 | 0 | scaffolding | unit (stubs) | `python -m unittest tests.test_simulator_abstain -v` | ❌ W0 | ⬜ pending |
| 6-01-XX | 01 | 1 | PLOT-01 data gap (abstain_per_phase) | unit | `python -m unittest tests.test_simulator_abstain -v` | ✅ after W0 | ⬜ pending |
| 6-02-XX | 02 | 2 | REPORT-01, REPORT-02 (markdown.py) | integration | `python -m unittest tests.test_report.TestReportSections -v` | ✅ after W0 | ⬜ pending |
| 6-03-XX | 03 | 2 | PLOT-01, PLOT-02, PLOT-03 (plots.py) | integration | `python -m unittest tests.test_report.TestPlots tests.test_report.TestPlotLinks -v` | ✅ after W0 | ⬜ pending |
| 6-04-XX | 04 | 3 | REPORT-03 + CLI/REPL wiring (`write_report` entry) | integration | `python -m unittest tests.test_report.TestReportCompareMode -v` | ✅ after W0 | ⬜ pending |
| 6-05-XX | 05 | 4 | regression + verify_phase6.sh gate | integration | `SPHSIM_NO_REPORT=1 python scripts/regression_check.py && scripts/verify_phase6.sh` | ✅ exists (extend) / ❌ new script | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Note:* Exact task IDs (`6-01-XX` etc.) will be filled by the planner. This table establishes the COVERAGE CONTRACT — every SC has at least one automated assertion.

---

## Requirement → Test Coverage Map

| Req ID | Behavior | Test Class | Coverage Type |
|--------|----------|-----------|---------------|
| REPORT-01 | Single-run creates `./reports/<ts>/report.md` + 2 PNG | `TestReportFiles` | integration |
| REPORT-01 | `SPHSIM_NO_REPORT=1` env var disables generation | `TestReportFiles` | unit |
| REPORT-01 | mkdir collision adds `-N` suffix | `TestReportFiles` | unit |
| REPORT-02 | `report.md` contains 6 section headers (Konfiguracja, Strategia, KPI, Rozkład decyzji, Przebieg KPI, Baseline) | `TestReportSections` | integration |
| REPORT-02 | KPI table contains 5 named rows | `TestReportSections` | unit |
| REPORT-02 | Baseline comparison row present for default env | `TestReportSections` | integration |
| REPORT-03 | Compare mode (`--compare-agent`) adds section 7 with delta KPI | `TestReportCompareMode` | integration |
| PLOT-01 | `decision_distribution.png` exists + non-zero size | `TestPlots` | integration |
| PLOT-01 | `abstain_per_phase` aggregation correct (12-phase scenario) | `TestSimulatorAbstain` | unit |
| PLOT-02 | `kpi_timeseries.png` exists + non-zero size | `TestPlots` | integration |
| PLOT-02 | history T=1000 not truncated in PNG (Pillow dim check) | `TestPlots` | unit |
| PLOT-03 | `report.md` contains relative MD image links `![...](decision_distribution.png)` | `TestPlotLinks` | unit |
| SC#6 regression | All 8 baseline invocations still PASS (SKIP_KEYS extended) | regression harness | integration |
| SC#6 JSON | `--json` stdout still parses as JSON (no banner contamination on stdout) | `TestJsonStdoutClean` | unit |

---

## Wave 0 Requirements

- [ ] `tests/test_report.py` — stub classes for REPORT-01, REPORT-02, REPORT-03, PLOT-01, PLOT-02, PLOT-03 (~12 cases)
- [ ] `tests/test_simulator_abstain.py` — stub classes for `abstain_per_phase` aggregation (~3 cases)
- [ ] `tests/conftest.py` OR base `setUp` — sets `os.environ['SPHSIM_NO_REPORT'] = '1'` so test runs don't pollute `./reports/`
- [ ] `.gitignore` entry: `reports/` (so accidental local runs don't taint commits)
- [ ] Framework install: **none** — `unittest` is stdlib; `matplotlib` already installed locally (verified RESEARCH.md). CI install line may be needed (`pip install matplotlib`) — discuss-phase decides if `requirements.txt` is created.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PNG renders correctly in GitHub/VSCode/Obsidian (SC#4) | REPORT-03 / PLOT-03 | Cross-renderer visual check; automated cannot verify visual fidelity | Open `reports/<latest>/report.md` in GitHub web UI, VSCode preview, Obsidian — both PNGs should display inline with no broken-image icon |
| Polish glyphs render in PNG titles/labels | PLOT-01, PLOT-02 | matplotlib font fallback; automated check only verifies file size | Open `decision_distribution.png` — labels "Faza 1", "Faza 2"... should show Polish characters cleanly |

---

## Validation Sign-Off

- [ ] All tasks have automated verify command OR Wave 0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all stub-test dependencies (`test_report.py`, `test_simulator_abstain.py`)
- [ ] No watch-mode flags (unittest is run-once)
- [ ] Feedback latency < 5s for quick loop
- [ ] `SPHSIM_NO_REPORT=1` enforced in `conftest.py` AND `regression_check.py` env passthrough
- [ ] `nyquist_compliant: true` set in frontmatter once W0 stubs land

**Approval:** pending
