---
phase: 3
slug: custom-strategy-loader
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-27
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (stdlib only — PROJECT.md constraint) |
| **Config file** | none (test discovery via `python -m unittest discover`) |
| **Quick run command** | `python -m unittest tests.test_loader` |
| **Full suite command** | `python -m unittest discover tests && python scripts/regression_check.py` |
| **Estimated runtime** | ~8 seconds (loader 19 cases ~2s + regression 8 fixtures ~5s + invariant ~1s) |

---

## Sampling Rate

- **After every task commit:** Run `python -m unittest tests.test_loader` (when test_loader.py exists)
- **After every plan wave:** Run `python -m unittest discover tests && python scripts/regression_check.py`
- **Before `/gsd:verify-work`:** Full suite + regression must be green; baseline_v1 8/8 fixtures pass; `verify_phase3.sh` (if planner emits one) returns 0
- **Max feedback latency:** 10 seconds (sub-target — keeps edit-run-edit loop tight)

---

## Per-Task Verification Map

> Planner fills this table during plan creation. Each task in PLAN.md must have an `<automated>` verify command (or be backed by a Wave 0 dependency). Stub structure shown:

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-XX-NN | XX | W | STRAT-0X | T-3-NN / — | {expected secure behavior} | unit / integration / regression | `{command}` | ✅ / ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Expected verification clusters (from RESEARCH.md §Validation Architecture):**
- **Loader unit (D-47 layers 1–4 + D-49 collision + D-38 reload):** ~19 cases in `tests/test_loader.py`
- **CLI integration:** `--custom` mutex + `--param` parsing + main.py early branch + Polish error stderr
- **REPL integration:** `do_custom` + `do_run` + `do_strategies` `[custom]` suffix + `do_help` listing
- **Regression (Phase 1 contract):** 8 baseline fixtures via `scripts/regression_check.py` — must stay green
- **Invariant (Phase 2 contract):** `tests/test_strategy_meta_consistency.py` — unchanged, must stay green
- **Template acceptance (SC #3):** `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json` runs deterministically
- **Security banner (SC #5):** stdout contains `[OSTRZEŻENIE] Ładuję arbitralny kod` before any import side effects

---

## Wave 0 Requirements

- [ ] `tests/test_loader.py` — new file; stubs for all 4 layers of D-47, D-49 collision, D-38 reload, param parser
- [ ] `examples/custom_strategy_template.py` — must be loadable by tests as the canonical template fixture
- [ ] `tests/fixtures/custom_strategies/` (optional, planner's discretion) — minimal `.py` fixtures for error path tests (missing function, bad signature, syntax error, STRATEGY_META malformed)
- [ ] No new framework install — stdlib `unittest` already in use (Phase 2)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Banner format readability (Polish, non-confusing) | STRAT-04 / SC #5 | Subjective UX call | Run `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42`, confirm banner line is single, prefixed `[OSTRZEŻENIE]`, mentions absolute path |
| Template comments are pedagogically clear | STRAT-05 / SC #3 | Reviewer judgement | Read `examples/custom_strategy_template.py` end-to-end; confirm Polish inline comments cover dev/l/s/phi/kappa/rho/h/p, COMMIT/ABSTAIN, STRATEGY_META structure |
| Error messages are actionable in Polish | STRAT-04 / SC #2 | Translation quality + concreteness | Trigger each of 4 D-47 layers via crafted bad-file fixtures; confirm message names the missing function, expected signature, or specific malformation |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (tests/test_loader.py + template + optional fixtures dir)
- [ ] No watch-mode flags (single-shot `unittest` runs only)
- [ ] Feedback latency < 10s (loader-only quick command)
- [ ] `nyquist_compliant: true` set in frontmatter after planner ratifies the Per-Task map

**Approval:** pending (planner to fill Per-Task Verification Map then flip `nyquist_compliant: true`)
