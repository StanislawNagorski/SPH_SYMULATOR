---
phase: 8
slug: documentation-interactive-tutorial
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-28
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `08-RESEARCH.md § Validation Architecture (Nyquist)`.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (stdlib — already in use across phases 1–7) |
| **Config file** | none (discover via `python -m unittest discover tests`) |
| **Quick run command** | `SPHSIM_NO_REPORT=1 python -m unittest tests.test_tutorial tests.test_docs` |
| **Full suite command** | `SPHSIM_NO_REPORT=1 python -m unittest discover tests` |
| **Estimated runtime** | ~30 seconds full suite |

---

## Sampling Rate

- **After every task commit:** Run `SPHSIM_NO_REPORT=1 python -m unittest tests.test_tutorial tests.test_docs`
- **After every plan wave:** Run `SPHSIM_NO_REPORT=1 python -m unittest discover tests`
- **Before `/gsd:verify-work`:** Full suite must be green AND `bash scripts/verify_phase8.sh` exits 0
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 8-XX-NN | TBD | 0 | TUT-01 | — | tutorial entry guarded against re-entry | unit | `python -m unittest tests.test_tutorial.TestTutorialEntry` | ❌ W0 | ⬜ pending |
| 8-XX-NN | TBD | 0 | TUT-02 | — | `skip` advances step counter, never auto-runs | unit | `python -m unittest tests.test_tutorial.TestTutorialControls` | ❌ W0 | ⬜ pending |
| 8-XX-NN | TBD | 0 | TUT-03 | — | `back` decrements without resetting REPL state (D-08) | unit | `python -m unittest tests.test_tutorial.TestTutorialControls` | ❌ W0 | ⬜ pending |
| 8-XX-NN | TBD | 0 | TUT-04 | — | `exit` in tutorial drops to bare REPL, NOT process exit | unit | `python -m unittest tests.test_tutorial.TestTutorialExit` | ❌ W0 | ⬜ pending |
| 8-XX-NN | TBD | 0 | TUT-05 | — | `--tutorial` flag dispatches `run_repl(start_in_tutorial=True)` and respects 5-way mutex | integration | `python -m unittest tests.test_tutorial.TestTutorialCLI` | ❌ W0 | ⬜ pending |
| 8-XX-NN | TBD | 0 | TUT-06 | — | D-10: reports land under `./reports/tutorial-<ts>/step-N-<topic>/` via base-dir override; default behavior unchanged | integration | `python -m unittest tests.test_tutorial.TestTutorialReports` | ❌ W0 | ⬜ pending |
| 8-XX-NN | TBD | 0 | DOC-01 | — | `docs/PRZEWODNIK.md` exists with all D-11 sections (Lead, Quickstart, Walkthrough, Reference, Theory) | structural | `python -m unittest tests.test_docs.TestPrzewodnik` | ❌ W0 | ⬜ pending |
| 8-XX-NN | TBD | 0 | DOC-02 | — | `docs/assets/*.png` (decision_distribution_naive, kpi_timeseries_naive, batch_aggregate_naive) present + valid PNG headers | structural | `python -m unittest tests.test_docs.TestAssets` | ❌ W0 | ⬜ pending |
| 8-XX-NN | TBD | N | EX-01 | — | every fenced code block in PRZEWODNIK.md is parseable (matches a verify_phase*.sh or 08-UAT.md example) | structural | `python -m unittest tests.test_docs.TestExamplesAudit` | ❌ W0 | ⬜ pending |
| 8-XX-NN | TBD | N | GATE-01 | — | `scripts/verify_phase8.sh` checks PRZEWODNIK sections + assets + `--tutorial` flag + tutorial smoke (printf-piped) | integration | `bash scripts/verify_phase8.sh` | ❌ W0 | ⬜ pending |

*Plan IDs and task IDs are filled in by the planner. Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_tutorial.py` — test stubs for TUT-01..TUT-06
- [ ] `tests/test_docs.py` — test stubs for DOC-01, DOC-02, EX-01
- [ ] `tests/conftest.py` — shared `temp_reports_dir` and `repl_with_stdin(commands)` fixtures (if not present from phases 2/3)
- [ ] `docs/` directory (Wave 0 placeholder or Wave 1)
- [ ] `docs/assets/` directory
- [ ] `scripts/verify_phase8.sh` (mirror of verify_phase{1,3..7}.sh idiom) — phase-exit gate
- [ ] No new framework install — `unittest` is stdlib

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ≤15-minute onboarding budget (Phase goal) | Goal-level | Wall-clock timing varies per user; not stable in CI | Walk through `--tutorial` end-to-end on a fresh checkout, stopwatch ≤15 min including reading PRZEWODNIK Lead + Quickstart |
| Polish tone calibration (informal-respectful) | D-11 / D-12 prose | Style judgement — automated only checks presence of section headers, not voice | Reviewer (Polish speaker) reads tutorial output + PRZEWODNIK.md and confirms tone matches existing REPL messages (Phase 2 D-30 style) |
| Tutorial step verification UX feel (D-04 forgiving shape-match) | D-04 / D-07 | Whether hints feel helpful vs nagging is subjective | Reviewer intentionally fat-fingers each step's command (`run incentve`, `batch naive --seedz 5`) and confirms hint copy is helpful, not punishing |
| `docs/assets/*.png` visual quality | D-14 | PNG byte-determinism is automated; "does this chart look right" is human | Reviewer opens each PNG, confirms axes/labels/title are readable and match what the tutorial step describes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (tests/test_tutorial.py, tests/test_docs.py, docs/, scripts/verify_phase8.sh)
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s (full suite)
- [ ] `nyquist_compliant: true` set in frontmatter after Wave 0 complete

**Approval:** pending
