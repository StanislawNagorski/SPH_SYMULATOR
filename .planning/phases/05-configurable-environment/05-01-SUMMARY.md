---
phase: 05-configurable-environment
plan: "01"
subsystem: cli/args + cli/main + tests
tags: [ENV-01, argparse, phi, rho, type-converter, Polish-errors, D-17, regression]
dependency_graph:
  requires: ["05-00"]
  provides: ["05-02", "05-03"]
  affects: ["sphsim/cli/args.py", "sphsim/cli/main.py", "tests/test_env.py"]
tech_stack:
  added: []
  patterns:
    - "argparse type= converter function (first use in codebase)"
    - "module-level validator with ArgumentTypeError + Polish error strings"
key_files:
  modified:
    - sphsim/cli/args.py
    - sphsim/cli/main.py
    - tests/test_env.py
    - tests/test_main_agent_integration.py
decisions:
  - "DEFAULT_PHI/DEFAULT_RHO kept in main.py import (Plan 03 will use them for REPL fake_args)"
  - "type= converters at module level above parse_args() — introduces argparse ArgumentTypeError pattern for first time in codebase"
  - "3 SPHSimulator sites all use args.phi/args.rho — default via argparse preserves bit-identical v1.0 behavior"
metrics:
  duration: "~15 min"
  completed: "2026-05-27T21:02:24Z"
  tasks_completed: 3
  files_modified: 4
---

# Phase 05 Plan 01: ENV-01 --phi/--rho CLI Converters and Plumbing Summary

**One-liner:** Argparse type= converters for --phi/--rho with verbatim Polish error messages (D-17) threaded into all 3 SPHSimulator call sites; baseline bit-identical (PASS 8/8).

## What Was Built

Delivered ENV-01: `--phi p1,p2,p3,p4,p5` and `--rho r1,r2,r3,r4,r5` CLI flags with argparse `type=` validation and end-to-end flow into SPHSimulator constructor at all call sites.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add _parse_phi_list/_parse_rho_list converters + --phi/--rho flags | 1dcaa68 | sphsim/cli/args.py |
| 2 | Thread args.phi/args.rho through main.py at 3 call sites | a2435fb | sphsim/cli/main.py |
| 3 | Replace TestPhiRhoParsing + TestPhiRhoFlow skip stubs with real tests | 011b701 | tests/test_env.py, tests/test_main_agent_integration.py |

## Files Modified

### sphsim/cli/args.py

**Lines added/changed:**

1. Import line (line 29) extended: added `DEFAULT_PHI, DEFAULT_RHO`
2. Two module-level converter functions inserted before `def parse_args()` (~44 new lines):
   - `_parse_phi_list(s: str) -> list` — validates len=5, each val in [0.0, 1.0]; Polish errors: "Nieprawidłowy format", "dokładnie 5", "poza zakresem"
   - `_parse_rho_list(s: str) -> list` — validates len=5, each val >= 0.0; Polish errors: "Nieprawidłowy format", "dokładnie 5", "ujemne"
3. Two `add_argument` blocks inserted after `--K1`, before `--T` in `parse_args()`:
   - `--phi p1,..,p5` with `type=_parse_phi_list, default=DEFAULT_PHI`
   - `--rho r1,..,r5` with `type=_parse_rho_list, default=DEFAULT_RHO`

**Polish error substrings (D-17):**
- Wrong format: "Nieprawidłowy format --phi: ..."
- Wrong length: "--phi wymaga dokładnie 5 wartości ..."
- Out of range: "--phi[N]=v poza zakresem [0, 1]. ..."
- Negative rho: "--rho[N]=v jest ujemne. ..."

### sphsim/cli/main.py

**Lines changed — 3 sites replaced:**

1. `run_compare()` common dict (line 28 area): `phi=DEFAULT_PHI, rho=DEFAULT_RHO` → `phi=args.phi, rho=args.rho`
2. Custom-strategy SPHSimulator call (line 94 area): same substitution
3. Built-in-strategy SPHSimulator call (line 130 area): same substitution

Each site received a Polish comment: `# Phase 5 ENV-01: phi/rho z args (default = DEFAULT_PHI/DEFAULT_RHO via argparse).`

**Design choice:** `DEFAULT_PHI, DEFAULT_RHO` import kept in main.py — they are still needed indirectly as argparse defaults, and Plan 03 will use them for REPL fake_args; removing them would be premature cleanup.

### tests/test_env.py

**Test methods added:**

`TestPhiRhoParsing` (5 methods — unit via sys.argv swap + subprocess):
- `test_phi_default_when_flag_absent` — args.phi == DEFAULT_PHI when flag absent
- `test_phi_parses_valid_list` — "0.05,0.15,0.25,0.35,0.95" → [0.05, 0.15, 0.25, 0.35, 0.95]
- `test_phi_wrong_length_exit_2` — 3-value list → exit 2 + "dokładnie 5" in stderr
- `test_phi_out_of_range_exit_2` — value 1.5 → exit 2 + "poza zakresem" in stderr
- `test_rho_negative_exit_2` — negative value → exit 2 + "ujemne" in stderr

`TestPhiRhoFlow` (2 methods — integration via subprocess + JSON):
- `test_phi_reaches_simulator` — custom phi + --json → exit 0, avg_val_last100 is a number
- `test_baseline_unchanged_without_phi` — default run → avg_val_last100 == 92.0 (baseline v1.0)

**5 classes still skipping** (Plans 02/03): TestValuationDispatch, TestValuationPresets, TestPresetDistinguishability, TestConfigHeader, TestHumanHeader.

## Verification Results

```
python -m unittest tests.test_env.TestPhiRhoParsing tests.test_env.TestPhiRhoFlow -v
  → Ran 7 tests: OK

python -m unittest discover tests/
  → Ran 135 tests: OK (skipped=5)

python scripts/regression_check.py
  → PASS: 8/8

python sph_sim.py --help | grep phi/rho
  → --phi p1,..,p5  Profile awarii φ (5 liczb w [0,1], ...)
  → --rho r1,..,r5  Koszty naprawy ρ (5 liczb ≥ 0, ...)

python sph_sim.py --strategy naive --zeta 0.5 --phi 0.05,0.15,0.25,0.35,0.95 --no-agent --seed 42 --json
  → OK avg_val= 14.0  (changed from 92.0 — confirms phi reached simulator)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_main_agent_integration.py fake_args missing phi/rho attributes**
- **Found during:** Task 3 (full test suite run)
- **Issue:** `TestRunCompareFunction.test_run_compare_returns_comparison_block` constructs a `fake_args = argparse.Namespace(...)` and calls `run_compare()` directly. After Task 2 replaced `phi=DEFAULT_PHI, rho=DEFAULT_RHO` with `phi=args.phi, rho=args.rho` in `run_compare()`, this test's fake_args lacked the `phi` and `rho` attributes, causing `AttributeError`.
- **Fix:** Added `phi=DEFAULT_PHI, rho=DEFAULT_RHO` to the `fake_args` Namespace in the test (DEFAULT_PHI and DEFAULT_RHO were already imported in the test file, confirming the omission was unintentional).
- **Files modified:** tests/test_main_agent_integration.py
- **Commit:** included in 011b701

## Known Stubs

None — all 7 implemented test methods produce real assertions with no placeholder values. The 5 remaining skip classes in test_env.py are intentional deferred stubs (Plans 02/03), not this plan's responsibility.

## Threat Flags

No new security-relevant surfaces introduced beyond what the plan's threat model documents. The `_parse_phi_list`/`_parse_rho_list` converters handle all T-5-01 mitigations (non-numeric, wrong length, out-of-range, negative). T-5-01-OVF (inf/nan) handled implicitly: `float('inf')` fails the `0.0 <= v <= 1.0` check; `float('nan')` fails the same check.

## Self-Check: PASSED

Files created/modified confirmed to exist:
- sphsim/cli/args.py: FOUND (contains `_parse_phi_list`, `_parse_rho_list`, `--phi`, `--rho`)
- sphsim/cli/main.py: FOUND (phi=args.phi count=3, rho=args.rho count=3)
- tests/test_env.py: FOUND (TestPhiRhoParsing + TestPhiRhoFlow implemented, 5 skipTest remaining)
- tests/test_main_agent_integration.py: FOUND (fake_args includes phi/rho)

Commits confirmed:
- 1dcaa68: Task 1 - args.py converters
- a2435fb: Task 2 - main.py threading
- 011b701: Task 3 - test_env.py implementation + bug fix
