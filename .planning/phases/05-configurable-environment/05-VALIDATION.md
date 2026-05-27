---
phase: 5
slug: configurable-environment
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-27
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (stdlib — no pytest) |
| **Config file** | none — discovery via `python -m unittest discover tests/` |
| **Quick run command** | `python -m unittest tests/test_env.py -v` |
| **Full suite command** | `python -m unittest discover tests/ -v && python scripts/regression_check.py` |
| **Estimated runtime** | ~30 seconds (unit + regression) |

---

## Sampling Rate

- **After every task commit:** Run `python -m unittest tests/test_env.py -v`
- **After every plan wave:** Run `python -m unittest discover tests/ -v`
- **Before `/gsd:verify-work`:** Full suite green AND `python scripts/regression_check.py` PASS
- **Max feedback latency:** ~5 seconds for quick run

---

## Per-Task Verification Map

> Plan IDs are placeholders until gsd-planner finalises wave breakdown. Map will be reconciled after PLAN.md emission.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 5-00-01 | 00 | 0 | ENV-01,02,03 | — | N/A (test infra) | scaffold | `test -f tests/test_env.py` | ❌ W0 | ⬜ pending |
| 5-01-01 | 01 | 1 | ENV-01 | — | argparse rejects len != 5 / out-of-range | unit | `python -m unittest tests.test_env.TestPhiRhoParsing -v` | ❌ W0 | ⬜ pending |
| 5-01-02 | 01 | 1 | ENV-01 | — | --phi/--rho values reach SPHSimulator | unit | `python -m unittest tests.test_env.TestPhiRhoFlow -v` | ❌ W0 | ⬜ pending |
| 5-02-01 | 02 | 2 | ENV-02 | — | --valuation {window,step,linear} dispatch | unit | `python -m unittest tests.test_env.TestValuationDispatch -v` | ❌ W0 | ⬜ pending |
| 5-02-02 | 02 | 2 | ENV-02 | — | --K0/--K1 override preset defaults; sph_stp respects preset | integration | `python -m unittest tests.test_env.TestValuationPresets -v` | ❌ W0 | ⬜ pending |
| 5-02-03 | 02 | 2 | ENV-02 (SC-3) | — | 3 presets produce distinguishable KPI on same seed+strategy | integration | `python -m unittest tests.test_env.TestPresetDistinguishability -v` | ❌ W0 | ⬜ pending |
| 5-03-01 | 03 | 3 | ENV-03 (SC-4) | — | format_config_header returns 9-key MD table | unit | `python -m unittest tests.test_env.TestConfigHeader -v` | ❌ W0 | ⬜ pending |
| 5-03-02 | 03 | 3 | ENV-03 | — | format_human output starts with config header | integration | `python -m unittest tests.test_env.TestHumanHeader -v` | ❌ W0 | ⬜ pending |
| 5-04-01 | 04 | 4 | regression | — | v1.0 baseline (`naive --zeta 0.75` etc.) unchanged | regression | `python scripts/regression_check.py` | ✅ exists | ⬜ pending |
| 5-04-02 | 04 | 4 | exit gate | — | verify_phase5.sh covers all 4 ROADMAP SCs | gate | `bash scripts/verify_phase5.sh` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_env.py` — stubs for ENV-01, ENV-02, ENV-03 with the test classes named in the map above
- [ ] `tests/__init__.py` — confirm exists (likely from Phase 1); create if missing
- [ ] `scripts/verify_phase5.sh` — exit-gate script following Phase 4 precedent (PASS=N/FAIL=0)
- [ ] No framework install needed — `unittest` is stdlib

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Polish error messages render correctly in user terminal | D-17 UX | argparse Polish error visibility | Run `python sph_sim.py --phi 0.1,0.2,0.3` and confirm error message is Polish |
| Report header readability in MD viewers | ENV-03 / SC-4 | rendering across markdown viewers | Pipe `python sph_sim.py --strategy naive --zeta 0.75` output into a `.md` file and open in any viewer; confirm table renders |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (`tests/test_env.py`, `scripts/verify_phase5.sh`)
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s for quick run
- [ ] `nyquist_compliant: true` set in frontmatter once gsd-planner has reconciled task IDs

**Approval:** pending — gsd-plan-checker must validate after PLAN.md emission.
