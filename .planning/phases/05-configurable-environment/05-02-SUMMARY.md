---
phase: "05-configurable-environment"
plan: "02"
subsystem: "cli/model/simulator"
tags: ["env-params", "valuation-presets", "sph-stp", "sc-3", "pitfall-1"]
dependency_graph:
  requires: ["05-01"]
  provides: ["ENV-02", "SC-2", "SC-3"]
  affects: ["sphsim/cli/args.py", "sphsim/core/model.py", "sphsim/core/simulator.py", "sphsim/cli/main.py", "tests/test_env.py"]
tech_stack:
  added: []
  patterns: ["argparse-choices", "preset-dispatch-in-valuation", "sph-stp-closure-threading"]
key_files:
  created: []
  modified:
    - "sphsim/cli/args.py"
    - "sphsim/core/model.py"
    - "sphsim/core/simulator.py"
    - "sphsim/cli/main.py"
    - "tests/test_env.py"
    - "tests/test_main_agent_integration.py"
decisions:
  - "Use preset='window' string dispatch inside valuation() itself (not a valuation_fn callable) — simplest, backward-compat, testable in isolation"
  - "TestPresetDistinguishability uses --zeta 0.75 (avg_providers≈105>K0=100); --zeta 0.5 from plan behavior block gives avg_providers≈67<K0 so window==step numerically, defeating SC-3 purpose"
  - "valuation_preset='window' placed before seed=42 in SPHSimulator.__init__ kwarg order as specified"
metrics:
  duration: "~12 minutes"
  completed: "2026-05-27"
  tasks_completed: 4
  files_changed: 6
---

# Phase 5 Plan 02: ENV-02 --valuation/--K0 flags + preset dispatch Summary

ENV-02 fully delivered: `--K0` (float, default 100) and `--valuation` (choices window/step/linear, default window) flags with full propagation from `args → SPHSimulator → sph_stp → valuation`, defusing Pitfall 1 (P_of_x closure now threads preset). SC-3 enforced: window=92.0, step=93.0, linear=87.5167 (pairwise distinct, seed=42, naive zeta=0.75).

## Tasks Completed

| Task | Name | Commit | Files Changed |
|------|------|--------|---------------|
| 1 | Add --K0 and --valuation flags to args.py | a588f09 | sphsim/cli/args.py |
| 2 RED | Add failing TestValuationDispatch tests | cb2357c | tests/test_env.py |
| 2 GREEN | Extend valuation() + sph_stp() with preset dispatch | 460ada1 | sphsim/core/model.py |
| 3 | Thread valuation_preset through SPHSimulator and main.py | f0eb719 | sphsim/core/simulator.py, sphsim/cli/main.py, tests/test_main_agent_integration.py |
| 4 | Add TestValuationPresets + TestPresetDistinguishability | d475195 | tests/test_env.py |

## Files Modified — Changes Detail

### sphsim/cli/args.py (Task 1)
- Import line extended: added `DEFAULT_K0` alongside `DEFAULT_K1`
- `--K0` flag added after `--K1`: `type=float, default=DEFAULT_K0, help='Dolny próg waluacji K0 (def 100)'`
- `--valuation` flag added after `--rho`: `choices=['window', 'step', 'linear'], default='window'`
- Env-param block order: `--nU, --nSUS, --K1, --K0 (NEW), --phi, --rho, --valuation (NEW), --T, --kappa, --alpha, --seed`
- No mutex changes; both flags are orthogonal env params

### sphsim/core/model.py (Task 2 GREEN)
- `valuation(u, K0, K1)` → `valuation(u, K0, K1, preset='window')` with 3 branches:
  - `step`: `return float(K0) if u >= K0 else 0.0` (no upper bound)
  - `linear`: guard for `K1==inf or K1<=0`; else `float(K0) * min(float(u), float(K1)) / float(K1)`
  - `window` (default fallthrough): existing two-line body preserved verbatim
- Polish docstring added to `valuation()`
- `sph_stp(u, s, nSUS, K0, K1)` → `sph_stp(u, s, nSUS, K0, K1, preset='window')`
- **Pitfall 1 fix**: `P_of_x(x)` now calls `valuation(u - x, K0, K1, preset)` — preset reaches inner closure
- Updated docstring on `sph_stp`

### sphsim/core/simulator.py (Task 3)
- Constructor: `valuation_preset='window'` added as second-to-last kwarg (before `seed=42`)
- `self.valuation_preset = valuation_preset` stored after `self.phi, self.rho`
- Line ~80: `sph_stp(u, self.s, self.nSUS, self.K0, self.K1, self.valuation_preset)` — STP optimiser uses preset
- Line ~82: `valuation(svc_to_cons, self.K0, self.K1, self.valuation_preset)` — P_total calculation
- Line ~105: `valuation(svc_to_cons, self.K0, self.K1, self.valuation_preset)` — cycle history
- `grep -c 'self.valuation_preset' simulator.py` = 4 (1 init + 3 thread-throughs)

### sphsim/cli/main.py (Task 3)
- `run_compare` common dict: `K0=DEFAULT_K0` → `K0=args.K0`; added `valuation_preset=args.valuation`
- custom branch `SPHSimulator(...)`: same replacement
- builtin branch `SPHSimulator(...)`: same replacement
- `grep -c 'K0=DEFAULT_K0' main.py` = 0 (no leftover hard-codes)
- `grep -c 'K0=args.K0' main.py` = 3
- `grep -c 'valuation_preset=args.valuation' main.py` = 3

### tests/test_env.py (Tasks 2 RED + 4)

**TestValuationDispatch** (Task 2 — 7 methods):
- `test_window_default_K0_K1`: `valuation(110, 100, 120)` == 100.0
- `test_window_outside_range`: `valuation(80,...)` == 0.0; `valuation(130,...)` == 0.0
- `test_step_above_threshold`: `valuation(130, 100, 120, 'step')` == 100.0 (no upper cap)
- `test_step_below_threshold`: `valuation(80, 100, 120, 'step')` == 0.0
- `test_linear_ramp`: `valuation(60, 100, 120, 'linear')` ≈ 50.0 (assertAlmostEqual places=4)
- `test_linear_inf_K1_fallback`: `valuation(150, 100, inf, 'linear')` == 100.0 (step semantics)
- `test_sph_stp_threads_preset`: P_of_x(step) ≠ P_of_x(window) for u=150 — proves Pitfall 1 fixed

**TestValuationPresets** (Task 4 — 3 integration methods):
- `test_window_preset_matches_baseline`: `--valuation window --zeta 0.75` → 92.0 exactly
- `test_K0_override_changes_kpi`: `--K0 80` reaches simulator, returns numeric KPI
- `test_K1_override_with_valuation`: `--K0 100 --K1 200` exits 0 with valid JSON

**TestPresetDistinguishability** (Task 4 — 1 SC-3 critical method):
- `test_three_presets_give_distinct_kpi`: window=92.0, step=93.0, linear=87.5167 — pairwise distinct

## Test Results

```
python -m unittest tests.test_env.TestValuationDispatch -v   → 7 tests OK
python -m unittest tests.test_env.TestValuationPresets -v    → 3 tests OK
python -m unittest tests.test_env.TestPresetDistinguishability -v → 1 test OK
python -m unittest discover tests/ -v → Ran 143 tests in ~6s  OK (skipped=2)
python scripts/regression_check.py → PASS: 8/8
```

Remaining 2 skips: `TestConfigHeader` and `TestHumanHeader` — Plan 03 (Wave 3) responsibility.

## SC-3 Evidence — Pairwise-Distinct KPI Values

Invocation: `python sph_sim.py --strategy naive --zeta 0.75 --no-agent --seed 42 --json --valuation <preset>`

| Preset | avg_val_last100 | avg_providers_l100 |
|--------|-----------------|--------------------|
| window | 92.0            | 105.03             |
| step   | 93.0            | 105.03             |
| linear | 87.5167         | 105.03             |

All three values are pairwise distinct: 92.0 ≠ 93.0 ≠ 87.5167 (SC-3 satisfied).

Note: step > window because step has no upper bound penalty (u > K1 still pays K0), while window returns 0 for u > K1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed fake_args in test_main_agent_integration.py missing K0/valuation**
- **Found during:** Task 3
- **Issue:** `test_run_compare_returns_comparison_block` builds a `fake_args = argparse.Namespace(...)` without `K0` or `valuation` attributes. After Task 3's changes to `run_compare()`, this caused `AttributeError: Namespace has no attribute 'K0'` — 1 test error.
- **Fix:** Added `K0=DEFAULT_K0, valuation='window'` to the Namespace in `tests/test_main_agent_integration.py:124`.
- **Files modified:** `tests/test_main_agent_integration.py`
- **Commit:** f0eb719

**2. [Rule 1 - Bug] TestPresetDistinguishability uses --zeta 0.75 instead of --zeta 0.5**
- **Found during:** Task 4 investigation
- **Issue:** Plan `<behavior>` specifies `--zeta 0.5`, but with zeta=0.5, avg_providers ≈ 67 < K0=100. For both window and step presets, `valuation(67, 100, 120)` = 0.0 — they're numerically identical and assertNotEqual would always fail (window_kpi == step_kpi == 2.0). This defeats SC-3 even with Pitfall 1 correctly fixed.
- **Fix:** Used `--zeta 0.75` as specified in RESEARCH §B.7: "avg providers ≈ 105" for the distinguishability proof. RESEARCH explicitly states `--zeta 0.75` is the valid invocation for SC-3.
- **Files modified:** `tests/test_env.py` (TestPresetDistinguishability)
- **Commit:** d475195

## Pitfall 1 Defused

The critical landmine from RESEARCH §F.15 is fixed:

```python
# BEFORE (Pitfall 1 — sph_stp silently fell back to window):
def P_of_x(x):
    return valuation(u - x, K0, K1) + x  # always window preset!

# AFTER (Pitfall 1 fixed — preset threads into closure):
def P_of_x(x):
    return valuation(u - x, K0, K1, preset) + x  # uses caller's preset
```

Proof: `test_sph_stp_threads_preset` verifies that `P_of_x` values differ between step and window presets for u=150, K0=100, K1=120.

## Regression Check

`python scripts/regression_check.py` → **PASS: 8/8**

v1.0 baseline preservation: `--valuation window` (default) + `DEFAULT_K0=100` produces bit-identical output to all 8 fixtures. No invocation in `INVOCATIONS` uses `--valuation`, `--K0`, `--phi`, or `--rho`, so all 8 are unaffected by defaults.

## Known Stubs

None. All stubs introduced by this plan are fully implemented.

Remaining `skipTest` calls in `tests/test_env.py`:
- `TestConfigHeader.test_placeholder` — Plan 03 (Wave 3)
- `TestHumanHeader.test_placeholder` — Plan 03 (Wave 3)

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries. All changes are pure Python function dispatch (stdlib only, no new packages).

## Self-Check: PASSED

| Item | Status |
|------|--------|
| sphsim/cli/args.py | FOUND |
| sphsim/core/model.py | FOUND |
| sphsim/core/simulator.py | FOUND |
| sphsim/cli/main.py | FOUND |
| tests/test_env.py | FOUND |
| 05-02-SUMMARY.md | FOUND |
| Commit a588f09 (args.py --K0/--valuation) | FOUND |
| Commit cb2357c (RED gate tests) | FOUND |
| Commit 460ada1 (GREEN gate model.py) | FOUND |
| Commit f0eb719 (simulator + main.py) | FOUND |
| Commit d475195 (integration tests SC-3) | FOUND |
