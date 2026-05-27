---
phase: 05-configurable-environment
plan: 04
subsystem: testing
tags: [regression, shell-script, exit-gate, skip-keys, phase5]

# Dependency graph
requires:
  - phase: 05-03
    provides: format_json env block extended with K0/phi/rho/seed/valuation keys
  - phase: 05-00
    provides: verify_phase5.sh skeleton with check() helper and PASS/FAIL counters
provides:
  - regression_check.py SKIP_KEYS extended with 5 Phase 5 env keys (PASS: 8/8 restored)
  - verify_phase5.sh fully fleshed with 21 check() invocations covering all 4 ROADMAP SCs
affects: [gsd:verify-work, 06-report-plots-generator]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SKIP_KEYS Strategia B: extend tuple to tolerate new JSON keys vs baseline_v1 fixtures (no regeneration)"
    - "SC-scoped check() sections: each ROADMAP SC gets dedicated echo banner + per-sub-check invocations"
    - "K0/K1 parameter selection for preset distinguishability: K0=50 K1=70 ensures window!=step!=linear at avg_providers~67"

key-files:
  created:
    - .planning/phases/05-configurable-environment/05-04-SUMMARY.md
  modified:
    - scripts/regression_check.py
    - scripts/verify_phase5.sh

key-decisions:
  - "D-PH5 SKIP-EXT (Strategia B mirror D-67): add K0/phi/rho/seed/valuation to SKIP_KEYS instead of regenerating fixtures"
  - "SC#3 uses K0=50 K1=70 to ensure window!=step distinguishability (default K0=100 yields avg_providers~67<<K0, both return 0)"

patterns-established:
  - "Phase exit gate pattern: 7 numbered sections with echo banners, check() per sub-criterion, PASS/FAIL summary"
  - "SKIP_KEYS extension: commented tuple with phase/ticket annotations for audit trail"

requirements-completed: [ENV-01, ENV-02, ENV-03]

# Metrics
duration: 18min
completed: 2026-05-27
---

# Phase 5 Plan 04: SKIP_KEYS Extension + verify_phase5.sh Exit Gate Summary

**SKIP_KEYS extended with 5 Phase 5 env keys (PASS: 8/8 restored) and verify_phase5.sh fleshed with 21 check() invocations covering all 4 ROADMAP SCs + REPL Pitfall 2 + regression + test suite (PASS=21/FAIL=0)**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-05-27T00:00:00Z
- **Completed:** 2026-05-27
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Extended `SKIP_KEYS` in `regression_check.py` with 5 Phase 5 env keys (`K0`, `phi`, `rho`, `seed`, `valuation`) restoring PASS: 8/8 baseline contract
- Fleshed out `scripts/verify_phase5.sh` with 21 check() invocations covering all 4 ROADMAP Phase 5 SCs + regression + test suite + REPL Pitfall 2
- Phase 5 exit gate exits 0 with `PASS=21 / FAIL=0` — Phase 5 is ready for `/gsd:verify-work`

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend SKIP_KEYS in regression_check.py** - `0b48d37` (chore)
2. **Task 2: Flesh out scripts/verify_phase5.sh** - `80f2200` (feat)

## Files Created/Modified

- `scripts/regression_check.py` - SKIP_KEYS tuple extended with 5 Phase 5 env keys; Polish rationale comment added above definition
- `scripts/verify_phase5.sh` - Placeholder banner replaced with 21 check() invocations across 7 sections covering SC #1-4 + regression + test suite + REPL Pitfall 2

## Decisions Made

- **D-PH5 SKIP-EXT**: Mirroring Phase 4 D-67 Strategia B — extend `SKIP_KEYS` tuple with `K0, phi, rho, seed, valuation` rather than regenerating baseline_v1 fixtures. The new env-block keys appear only in actual output after Plan 03 `format_json` extension; fixtures are oracle for v1.0 field behavior only.
- **SC#3 K0=50 K1=70**: The default K0=100 K1=120 yields avg_providers ≈ 67 (below K0), causing both `window(u<K0)=0` and `step(u<K0)=0` → indistinguishable. Using K0=50 K1=70 places avg_providers (~67) above K0 (50) and near K1 (70), producing: window=37.0, step=50.0, linear=46.95 — all pairwise distinct.

## SC #3 KPI Proof (window/step/linear distinguishability)

Parameters: `--strategy naive --zeta 0.5 --no-agent --seed 42 --K0 50 --K1 70`

| Preset | avg_val_last100 |
|--------|----------------|
| window | 37.0 |
| step   | 50.0 |
| linear | 46.95 |

All three values are pairwise distinct: `window != step` (37.0 ≠ 50.0), `step != linear` (50.0 ≠ 46.95), `window != linear` (37.0 ≠ 46.95).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SC#3 check used default K0=100 which makes window==step indistinguishable**
- **Found during:** Task 2 (verify_phase5.sh implementation) — first run of the script
- **Issue:** With default K0=100, avg_providers ≈ 67 < K0, so both `window(u<K0)=0` and `step(u<K0)=0`, causing `assert w != s` to fail with `window=2.0 == step=2.0`
- **Fix:** Added `--K0 50 --K1 70` to SC#3 check invocations so avg_providers (≈67) falls in range [K0=50, K1=70], making all three presets produce distinct KPI values
- **Files modified:** scripts/verify_phase5.sh (SC#3 check body)
- **Verification:** SC#3 check now passes with window=37.0, step=50.0, linear=46.95
- **Committed in:** 80f2200 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in check parameters)
**Impact on plan:** Fix necessary for SC#3 correctness; no scope creep. The underlying preset implementation (simulator.py, model.py) is correct — the issue was the test parameters, not the implementation.

## verify_phase5.sh check() invocation counts

| SC | Count | Criteria |
|----|-------|---------|
| SC #1 | 7 occurrences (4 check() invocations) | length reject, range reject, rho negative reject, accept |
| SC #2 | 9 occurrences (6 check() invocations) | window/step/linear accept, foobar reject, K0 override, K0+K1 |
| SC #3 | 4 occurrences (1 check() invocation) | pairwise KPI assert inline python -c |
| SC #4 | 8 occurrences (5 check() invocations) | section header, table header, 9 labels, JSON env keys, legacy banner |
| REPL Pitfall 2 | 2 check() invocations | run + compare fake_args defused |
| Regression | 1 check() invocation | PASS: 8/8 via SKIP_KEYS |
| Test suite | 2 check() invocations | discover + test_env.py specifically |
| **Total** | **21 check() invocations** | PASS=21 / FAIL=0 |

## SKIP_KEYS diff (regression_check.py)

Before:
```python
SKIP_KEYS = ('veto_per_phase', 'n_vetoed_total', 'agent_enabled')
```

After:
```python
# Phase 5 (Strategia B, mirror Phase 4 D-67): pięć nowych kluczy w env bloku
# (K0, phi, rho, seed, valuation) ignorowane przy compare z baseline_v1 fixtures —
# fixtures są oracle dla zachowania v1.0 i nie zawierają tych pól. Pola obecne
# tylko w actual output po Plan 03 rozszerzeniu format_json env block.
SKIP_KEYS = (
    'veto_per_phase', 'n_vetoed_total', 'agent_enabled',  # Phase 4 D-67 Strategia B
    'K0', 'phi', 'rho', 'seed', 'valuation',              # Phase 5 ENV-03 (D-PH5 SKIP-EXT, mirroring D-67)
)
```

## Issues Encountered

None — all REPL Pitfall 2 defenses (fake_args with phi/rho/K0/valuation) were already in place from Plan 03. The only issue was SC#3 parameter selection (documented as deviation above).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 5 is complete: regression PASS 8/8, verify_phase5.sh PASS=21/FAIL=0, 149 tests green
- Ready for `/gsd:verify-work` to confirm Phase 5 gate
- Phase 6 (Report + plots generator) can reuse `format_config_header()` from output.py (already provides the MD table function)
- `format_json` env block already includes all 9 configuration fields for Phase 6 consumption

---

## Self-Check: PASSED

- `scripts/regression_check.py` — PASS: 8/8 ✓
- `scripts/verify_phase5.sh` — PASS=21 / FAIL=0 ✓
- `tests/` — 149 tests OK ✓
- Commit `0b48d37` exists (Task 1) ✓
- Commit `80f2200` exists (Task 2) ✓

---
*Phase: 05-configurable-environment*
*Completed: 2026-05-27*
