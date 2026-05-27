---
phase: 05-configurable-environment
plan: "03"
subsystem: output-formatting
tags: [env-03, config-header, format-human, format-json, repl, pitfall-2, sc-4]
dependency_graph:
  requires: ["05-02"]
  provides: ["format_config_header", "format_human-with-header", "format_json-env-extended", "repl-pitfall2-fix"]
  affects: ["sphsim/cli/output.py", "sphsim/cli/repl.py", "tests/test_env.py"]
tech_stack:
  added: []
  patterns: ["prepend-not-replace", "fake-args-namespace-extension", "tdd-red-green"]
key_files:
  created: []
  modified:
    - sphsim/cli/output.py
    - sphsim/cli/repl.py
    - tests/test_env.py
    - tests/test_output_veto.py
decisions:
  - "format_config_header placed before format_compare() (line 25) — reusable helper Phase 6 can call directly"
  - "format_human lines initialised with [header, ''] — empty string provides visual breathing room before SPH SYMULATOR banner"
  - "test_output_veto._make_args extended with K0/phi/rho/seed/valuation (Rule 1 fix — pre-existing test helpers required updating)"
metrics:
  duration: "~10 minutes"
  completed: "2026-05-27"
  tasks_completed: 2
  files_modified: 4
---

# Phase 5 Plan 03: ENV-03 Config Header Summary

**One-liner:** Reusable `format_config_header()` MD-table helper prepended always-on into `format_human`; JSON env extended with 5 keys; REPL Pitfall 2 defused at both `do_run` and `do_compare` fake_args sites.

## What Was Built

### Task 1 — format_config_header + format_human prepend + format_json env extension (TDD RED → GREEN)

**RED gate commit:** `3b1824d` — `test(05-03): add failing TestConfigHeader tests (RED gate)`
**GREEN gate commit:** `2d803cd` — `feat(05-03): add format_config_header + prepend in format_human + extend format_json env (GREEN gate)`

**sphsim/cli/output.py changes:**

1. Added `format_config_header(args, K0, K1, phi, rho) -> str` (new function, ~20 lines):
   - Returns 9-row Polish MD table: `## Konfiguracja środowiska` + `| Parametr | Wartość |` header + separator + rows for nU, T, κ (kappa), α (alpha), K0, K1, φ (phi), ρ (rho), seed
   - K1=float('inf') renders as `∞` Unicode glyph (not `inf`)
   - phi/rho formatted as `', '.join(f'{v:.2f}' for v in phi)` per RESEARCH §D.11

2. `format_human()` — replaced `lines = []` initialisation with:
   ```python
   lines = [format_config_header(args, args.K0, K1, args.phi, args.rho), '']
   ```
   Config header prepended always-on (no flag gating). SC-4 satisfied.

3. `format_json()` — extended env block from 6 to 11 keys:
   - Before: `nU, nSUS, K1, T, kappa, alpha`
   - After: `nU, nSUS, K0, K1, T, kappa, alpha, phi, rho, seed, valuation`

### Task 2 — REPL fake_args Pitfall 2 fix + TestHumanHeader

**Commit:** `b80a2ae` — `feat(05-03): extend REPL fake_args at do_run+do_compare; implement TestHumanHeader; fix test_output_veto _make_args`

**sphsim/cli/repl.py changes:**

`do_run` fake_args (lines 219-224) — 5 new fields added:
```python
phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window', seed=42,
```

`do_compare` fake_args (lines 284-291) — identical 5 fields added.

No new imports needed — DEFAULT_K0, DEFAULT_PHI, DEFAULT_RHO already imported at lines 32-35.

**tests/test_env.py — TestHumanHeader (3 integration tests):**
- `test_human_output_starts_with_config_header`: first non-empty stdout line is `## Konfiguracja środowiska`
- `test_human_output_contains_full_table`: stdout contains all 9 row labels
- `test_human_output_preserves_legacy_sections`: stdout contains `SPH SYMULATOR` AND `METRYKI` (proves prepend, not replace)

**tests/test_output_veto.py — Rule 1 fix:**
- `_make_args` factory extended with `K0=100, phi=[...], rho=[...], seed=42, valuation='window'`
- Required because `format_human` now calls `format_config_header(args, args.K0, ...)` — existing minimal Namespace lacked these fields

## Test Results

```
python3 -m unittest tests.test_env.TestConfigHeader -v → 5/5 PASS
python3 -m unittest tests.test_env.TestHumanHeader -v  → 3/3 PASS
python3 -m unittest tests.test_env -v                  → 26/26 PASS
python3 -m unittest discover tests/ -v                 → 149/149 PASS
grep -c skipTest tests/test_env.py                     → 0 (all 7 classes have real tests)
grep -c 'phi=DEFAULT_PHI' sphsim/cli/repl.py           → 4 (≥2 requirement met)
grep -c 'K0=DEFAULT_K0' sphsim/cli/repl.py             → 4 (≥2 requirement met)
```

## CLI Verification

```
python3 sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 | head -3
→ ## Konfiguracja środowiska
→
→ | Parametr | Wartość |

python3 sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json | python3 -c "..."
→ JSON env keys: ['nU', 'nSUS', 'K0', 'K1', 'T', 'kappa', 'alpha', 'phi', 'rho', 'seed', 'valuation']

printf 'run naive zeta=0.5\nexit\n' | python3 sph_sim.py --interactive | grep -c 'Konfiguracja'
→ 1 (REPL do_run Pitfall 2 defused)

printf 'compare naive zeta=0.5\nexit\n' | python3 sph_sim.py --interactive | grep -c 'PORÓWNANIE'
→ 1 (REPL do_compare Pitfall 2 defused)
```

## Commits

| Hash | Message |
|------|---------|
| `3b1824d` | test(05-03): add failing TestConfigHeader tests (RED gate) |
| `2d803cd` | feat(05-03): add format_config_header + prepend in format_human + extend format_json env (GREEN gate) |
| `b80a2ae` | feat(05-03): extend REPL fake_args at do_run+do_compare; implement TestHumanHeader; fix test_output_veto _make_args |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_output_veto._make_args missing ENV-03 fields**
- **Found during:** Task 2 verification (full test suite run)
- **Issue:** `tests/test_output_veto.py` `_make_args` factory produced Namespace without `K0`, `phi`, `rho`, `seed`, `valuation`. After `format_human` was changed to prepend `format_config_header(args, args.K0, ...)`, all 8 `TestFormatHumanVetoSection` and `TestFormatJsonExtension` tests raised `AttributeError: 'Namespace' object has no attribute 'K0'`
- **Fix:** Added `K0=100, phi=[0.1,0.2,0.3,0.4,1.0], rho=[0.5,0.5,0.7,1.5,3.0], seed=42, valuation='window'` to `_make_args` defaults
- **Files modified:** `tests/test_output_veto.py`
- **Commit:** `b80a2ae`

## Known Intermediate State

**regression_check.py is currently RED** — this is documented and expected. The `format_json` env block now contains 5 new keys (`K0, phi, rho, seed, valuation`) that are not in the baseline fixtures and not yet listed in `SKIP_KEYS`. Plan 04 (Wave 4) owns the regression remediation via SKIP_KEYS extension. Do NOT attempt to patch fixtures or `regression_check.py` here.

## Known Stubs

None — all 7 test_env classes have real implementations (skipTest count = 0).

## Threat Flags

None — no new attack surface. phi/rho values are validated `list[float]` by Plan 01 converters; `f'{v:.2f}'` produces only `[0-9.\-]` characters (no MD injection vector). Seed exposure in output is intentional reproducibility metadata (T-5-03-INFO disposition: accept).

## Self-Check: PASSED

All modified files exist on disk. All 3 commits verified in git log.

| Item | Status |
|------|--------|
| sphsim/cli/output.py | FOUND |
| sphsim/cli/repl.py | FOUND |
| tests/test_env.py | FOUND |
| tests/test_output_veto.py | FOUND |
| .planning/phases/05-configurable-environment/05-03-SUMMARY.md | FOUND |
| commit 3b1824d | FOUND |
| commit 2d803cd | FOUND |
| commit b80a2ae | FOUND |
