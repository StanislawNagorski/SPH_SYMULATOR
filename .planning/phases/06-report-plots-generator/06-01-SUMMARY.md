---
phase: 06-report-plots-generator
plan: 01
subsystem: simulator
tags: [abstain, per-phase-counter, aggregation, plot-01, mirror-d64, d-65-disjointness, skip-keys]

# Dependency graph
requires:
  - phase: 04-rational-agent
    provides: "Device.veto_phase_stats per-phase counter pattern (D-64) + simulator.run() VETO aggregation block + 'veto_per_phase' return-key — verbatim template Phase 6 mirrors for ABSTAIN"
  - phase: 05-configurable-environment
    provides: "scripts/regression_check.py SKIP_KEYS extension pattern (D-PH5) + comment-block evolution convention (Phase N adds one line, Phase N+1 mirrors)"
  - phase: 06-report-plots-generator
    plan: 00
    provides: "tests/test_simulator_abstain.py — TestSimulatorAbstain skip-stub class replaced by this plan with 3 real test methods"
provides:
  - "Device.abstain_phase_stats dict[int,int] field — initialized in __post_init__, written ONLY in simulator.py ABSTAIN branch"
  - "simulator.run() return dict NEW key 'abstain_per_phase': dict[int,int] aggregated across all devices (parallel to veto_per_phase)"
  - "3 GREEN TestSimulatorAbstain test methods (replacing Plan 00 skip placeholder): key_exists, aggregates_across_devices, veto_does_not_increment_abstain"
  - "scripts/regression_check.py SKIP_KEYS extended with 'abstain_per_phase' + rationale comment paragraph (intermediate — Plan 05 finalizes dedup)"
affects: [06-02-markdown-render, 06-03-plots, 06-04-entry-point-compare, 06-05-verify-script]

# Tech tracking
tech-stack:
  added: []  # zero new packages — stdlib only
  patterns:
    - "Counter aggregation mirror pattern: Phase 6 ABSTAIN block is literal 1:1 copy of Phase 4 VETO block (D-64), structurally identical except no n_*_total counter (UI doesn't show it; plotter sums on the fly per RESEARCH §3c)"
    - "ABSTAIN-branch increment position invariant: dev.abstain_phase_stats[dev.phase] mutated BEFORE dev.status='DOWN' / dev.phase=-1 cleanup — so the key is the decision-time phase (1..F-1), not the sentinel -1"
    - "D-65 disjointness preservation: VETO and ABSTAIN counters are mutually exclusive. VETO branch (simulator.py:70-74) does NOT touch abstain_phase_stats; ABSTAIN branch (else, simulator.py:75-79) does NOT touch veto_phase_stats. Tested explicitly by test_veto_does_not_increment_abstain."
    - "SKIP_KEYS intermediate-vs-final split: Plan 01 (this) adds the entry immediately to keep regression GREEN throughout Waves 1-3; Plan 05 (Wave 4) dedupes the rationale comment block + adds SPHSIM_NO_REPORT=1 to subprocess env passthrough (separate concern)"

key-files:
  created:
    - ".planning/phases/06-report-plots-generator/06-01-SUMMARY.md — this file"
  modified:
    - "sphsim/core/device.py — +1 line in __post_init__: `self.abstain_phase_stats = {}`"
    - "sphsim/core/simulator.py — +9 lines split across 3 sites: ABSTAIN-branch increment (+1) / aggregation block (+6 incl. blank separator) / return-key (+1) / aggregation-block blank-line-above separator (+1)"
    - "tests/test_simulator_abstain.py — full body rewrite: +imports / +2 stub strategies / +3 real test methods, replacing the Plan 00 skip placeholder"
    - "scripts/regression_check.py — extend SKIP_KEYS tuple +1 entry ('abstain_per_phase') + extend Polish rationale comment block by one paragraph (D-PH6 SKIP-EXT)"

key-decisions:
  - "Use Phase 4 D-64 VETO pattern verbatim as the template for ABSTAIN — same Device dataclass field, same simulator aggregation block shape, same return-dict key alignment. Auditing surface is 1:1 line-by-line against existing veto_phase_stats site, which is the lowest-risk way to add a per-phase counter in this codebase."
  - "DO NOT add an n_abstain_total counter parallel to n_vetoed_total. RESEARCH §3c justifies absence: total ABSTAINs are NOT shown anywhere in current UI/CLI output, and the future plotter sums on the fly when needed (Plan 03 PNG renderer). Adding a redundant counter would create a second source of truth for the same data and increase regression surface for no benefit."
  - "Increment position MUST be BEFORE status/down_left cleanup. At the moment of `dev.n_abstain += 1` the dev.phase still holds the decision-time phase (1..F-1). After `dev.status = 'DOWN'` no phase=-1 reassignment happens in the ABSTAIN branch itself, but the convention parallels VETO branch (which also doesn't reassign phase=-1 — that only happens in the COMMIT/failure branch). Tests assert all keys are within [1, F-1]."
  - "SKIP_KEYS extension landed in Plan 01 (this), not deferred to Plan 05. Rationale: between Wave 1 merge and Wave 4 (Plan 05) merge, regression_check.py would FAIL because abstain_per_phase appears in actual output but not in baseline_v1 fixtures. Mitigation = early SKIP_KEYS bump in this same plan, with a marker comment so Plan 05 can dedupe the rationale block cleanly (it's the second regression_check.py edit, separate concern: subprocess env passthrough for report-pollution prophylaxis)."
  - "Test approach mirrors test_agent.py:45-105 shape: module-level _stub_* strategy functions + class with _build_sim helper + per-SC test methods using assertGreater/assertEqual with Polish error messages (PROJECT.md hard convention)."

patterns-established:
  - "Per-phase counter pattern is now THE established way to track decision-stratified counts in sphsim — the next planner reaching for a new dimension (e.g., per-phase n_failed, n_delivered) should follow the same 3-step recipe: Device dataclass field in __post_init__ → branch-local increment with [dev.phase] key → aggregation loop in simulator.run() return dict."
  - "Mirror-pattern naming convention: when adding sibling counter X to existing counter Y, place the new aggregation block IMMEDIATELY BELOW Y's block (same indentation, one blank line above), use parallel `X_per_phase = {}` syntax, and mark the line with comment `# Phase N FEATURE-ID (mirror Y)`. Plan 05's dedup will rely on this marker placement."

requirements-completed: [PLOT-01]

# Metrics
duration: 12min
completed: 2026-05-28
---

# Phase 6 Plan 01: Per-Phase ABSTAIN Aggregation Summary

**`Device.abstain_phase_stats` field + `simulator.run()` aggregation + `result['abstain_per_phase']` return-key — verbatim 1:1 mirror of Phase 4 D-64 `veto_phase_stats` pattern, with 3 GREEN `TestSimulatorAbstain` test methods replacing the Plan 00 skip placeholder.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-05-28
- **Completed:** 2026-05-28
- **Tasks:** 2
- **Files modified:** 4 (device.py, simulator.py, test_simulator_abstain.py, regression_check.py)

## Accomplishments
- Closed RESEARCH §F.13 data gap: PLOT-01 input now exists in `simulator.run()` return dict, ready for Wave 2 Plans 02 (markdown) and 03 (PNG renderer) to consume.
- 3 GREEN unit tests covering the SC matrix: existence, aggregation correctness, D-65 disjointness.
- Regression `8/8 PASS` preserved across the change (SKIP_KEYS intermediate extension in same plan).
- Full test suite still GREEN: 159 tests (was 157 baseline + 3 new tests − 1 placeholder skip now real = +2 net; previously-skipped count dropped 8 → 7).
- Zero behavior change for v1.0 callers (purely additive — same code path for COMMIT, VETO, ABSTAIN branches; only new state mutated in the ABSTAIN branch).

## Task Commits

Each task was committed atomically:

1. **Task 1: Add `abstain_phase_stats` to Device + ABSTAIN-branch increment + aggregation + return-key in simulator** — `fc277db` (feat)
2. **Task 2: Replace `TestSimulatorAbstain` skip stub with 3 real tests + extend `regression_check.py` SKIP_KEYS** — `2fbbd70` (test)

_Note: The orchestrator owns STATE.md / ROADMAP.md update and the merge commit per parallel-executor protocol._

## Exact Diffs

### `sphsim/core/device.py` (+1 line)

```diff
@@ -24,6 +24,7 @@ class Device:
         # Per-phase IC tracking: phase -> {commits, deliveries, failures, earnings, costs}
         self.phase_stats = {}
         self.veto_phase_stats = {}  # {phase: count} — Phase 4 D-64
+        self.abstain_phase_stats = {}  # {phase: count} — Phase 6 PLOT-01 (mirror veto_phase_stats)
```

### `sphsim/core/simulator.py` (+9 lines, 3 sites)

```diff
@@ -74,6 +74,7 @@ class SPHSimulator:
                     dev.down_left = 1
                 else:  # 'ABSTAIN' lub nieznany decision — failsafe (T-04-04)
                     dev.n_abstain += 1
+                    dev.abstain_phase_stats[dev.phase] = dev.abstain_phase_stats.get(dev.phase, 0) + 1  # Phase 6 PLOT-01
                     dev.status = 'DOWN'
                     dev.down_left = 1
 
@@ -152,6 +153,12 @@ class SPHSimulator:
                 veto_per_phase[ph] = veto_per_phase.get(ph, 0) + count
                 n_vetoed_total += count
 
+        # Aggregate per-phase ABSTAIN stats across all devices (Phase 6 PLOT-01)
+        abstain_per_phase = {}
+        for dev in self.devices:
+            for ph, count in dev.abstain_phase_stats.items():
+                abstain_per_phase[ph] = abstain_per_phase.get(ph, 0) + count
+
         return {
             'avg_val_last100':    round(sum(self.history['val'][last100]) / 100, 4),
             'cum_val_total':      round(total_val, 2),
@@ -162,6 +169,7 @@ class SPHSimulator:
             'ic_per_phase':       ic_results,
             'veto_per_phase':     veto_per_phase,
             'n_vetoed_total':     n_vetoed_total,
+            'abstain_per_phase':  abstain_per_phase,   # Phase 6 PLOT-01 (mirror veto_per_phase)
             'history':            self.history,
             'devices':            self.devices,
         }
```

Three sites: (1) ABSTAIN-branch increment at line 77; (2) aggregation block at lines 156–161; (3) return-dict key at line 172.

### `tests/test_simulator_abstain.py`

Full body rewrite — Plan 00 skip placeholder removed, replaced with 3 real test methods + 2 module-level stub strategies + a `_build_sim` helper. File ends with the original `if __name__ == '__main__': unittest.main()` footer.

### `scripts/regression_check.py`

```diff
+# Phase 6 (Strategia B, mirror Phase 4 D-67 + Phase 5 D-PH5): nowy klucz
+# 'abstain_per_phase' (dict per-phase ABSTAIN counts) ignorowany przy compare —
+# fixtures baseline_v1 są oracle dla v1.0 i nie zawierają tego pola. Pole obecne
+# tylko w actual output po Plan 01 rozszerzeniu simulator.run() return dict.
 SKIP_KEYS = (
     'veto_per_phase', 'n_vetoed_total', 'agent_enabled',  # Phase 4 D-67 Strategia B
     'K0', 'phi', 'rho', 'seed', 'valuation',              # Phase 5 ENV-03 (D-PH5 SKIP-EXT, mirroring D-67)
+    'abstain_per_phase',                                  # Phase 6 PLOT-01 (D-PH6 SKIP-EXT, mirroring D-67)
 )
```

## SKIP_KEYS Tuple — Final State After This Plan

```python
SKIP_KEYS = (
    'veto_per_phase', 'n_vetoed_total', 'agent_enabled',  # Phase 4 D-67 Strategia B
    'K0', 'phi', 'rho', 'seed', 'valuation',              # Phase 5 ENV-03 (D-PH5 SKIP-EXT, mirroring D-67)
    'abstain_per_phase',                                  # Phase 6 PLOT-01 (D-PH6 SKIP-EXT, mirroring D-67)
)
```

9 keys total: 3 (Phase 4) + 5 (Phase 5) + 1 (Phase 6 = this plan). Plan 05 (Wave 4) will dedupe the multi-paragraph Polish rationale comment block above this tuple — that is the only follow-up touch expected on regression_check.py SKIP_KEYS section.

## `TestSimulatorAbstain` — 3 GREEN Tests

```text
test_abstain_per_phase_aggregates_across_devices ... ok
test_abstain_per_phase_key_exists_in_result ... ok
test_veto_does_not_increment_abstain ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.003s

OK
```

## `abstain_per_phase` Probe Output

Probe command:
```python
SPHSimulator(nU=250, nSUS=10, F=5, T=100, kappa=1.0, alpha=0,
             phi=[…], rho=[…], strategy_fn=lambda *a,**k:'ABSTAIN',
             params={}, seed=42).run()['abstain_per_phase']
```

Result:
```python
{1: 12386, 2: 44, 4: 30, 3: 40}
```

Total: **12500 ABSTAIN events across 100 cycles × 250 devices = 25000 device-cycles, but ~30% start DOWN and DOWN devices skip the strategy_fn dispatch, so the effective sampling is ~50% device-cycles → 12500 fits**.

Phase 1 dominates because every device returning to UP from DOWN starts at `dev.phase = 1` (simulator.py:42), and since all strategies return ABSTAIN here, no device advances through phases — they bounce DOWN immediately, recycle, ABSTAIN at phase 1 again. The tiny non-zero counts for phases 2/3/4 come from devices that started in those phases on cycle 0 (random init at simulator.py:23). This is the expected analytical signature.

## Decisions Made
See `key-decisions:` in frontmatter — 5 decisions documenting:
1. Verbatim D-64 mirror as risk-minimization principle.
2. NO `n_abstain_total` parallel counter (RESEARCH §3c — UI doesn't show it).
3. Increment-before-cleanup position invariant (decision-time phase semantics).
4. Same-plan SKIP_KEYS extension (avoid intermediate regression FAIL between Wave 1 and Wave 4).
5. test_agent.py:45-105 shape as the test template.

## Deviations from Plan

None — plan executed exactly as written.

All four verification scripts from the plan's `<verification>` block pass:
- `SPHSIM_NO_REPORT=1 python -m unittest tests.test_simulator_abstain -v` → 3 tests, OK
- `SPHSIM_NO_REPORT=1 python -m unittest discover tests/` → 159 tests, OK (skipped=7)
- `SPHSIM_NO_REPORT=1 python scripts/regression_check.py` → PASS 8/8
- Direct probe → `abstain_per_phase: {1: 12386, 2: 44, 4: 30, 3: 40}` non-empty dict ✓

All 9 acceptance criteria for Task 1 met:
- `abstain_phase_stats` appears 1× in device.py ✓
- `abstain_phase_stats` appears 2× in simulator.py (1 increment + 1 aggregation read) ✓
- `abstain_per_phase` appears 3× in simulator.py (1 init / 1 set-via-get / 1 return-key) ✓
- Device sentinel: `Device(id=0, phase=1, status='UP').abstain_phase_stats == {}` ✓
- End-to-end probe returns non-empty `abstain_per_phase` ✓
- `n_abstain += 1` still appears 1× (VETO branch unchanged — D-65) ✓
- ABSTAIN aggregation block appears AFTER VETO aggregation in simulator.py ✓
- Phase 5 subset (`test_env` + `test_agent`) → 36 tests OK ✓

All 9 acceptance criteria for Task 2 met:
- 3 test methods present (`grep -cE` matches all 3) ✓
- 2 stub strategies defined (`_stub_always_abstain`, `_stub_always_veto`) ✓
- 0 remaining `skipTest` calls in test_simulator_abstain.py ✓
- `'abstain_per_phase'` present in scripts/regression_check.py SKIP_KEYS tuple ✓
- `Phase 6 PLOT-01 (D-PH6 SKIP-EXT` marker comment present ✓
- `regression_check.py` exits 0 with `PASS: 8/8` ✓
- Full discover: 159 tests OK, no Phase 5 regressions ✓
- No `./reports/` directory created during discover (Plan 00 conftest+__init__ env-var enforcement holds) ✓

## Issues Encountered

None.

## Known Stubs

None — `tests/test_simulator_abstain.py` no longer contains any `skipTest` or placeholder. The Plan 00 1-test skip class has been fully replaced by 3 real GREEN tests. No new stubs introduced anywhere else in this plan.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

**Wave 2 (Plans 02 + 03) can now proceed in parallel:**
- Plan 02 (markdown render — `format_md_abstain_section`) has `result['abstain_per_phase']` available as a dict[int,int] for the decision-distribution table (sekcja 4).
- Plan 03 (PNG renderer — `plots_decision_distribution`) has the third bar group (COMMIT/ABSTAIN/VETO per faza) data available; matplotlib install + render code is Plan 03's owned scope.
- Wave 3 (Plans 04 + 05) depend transitively but are not blocked by intermediate state — SKIP_KEYS already extended here.

**No blockers, no concerns.** Regression 8/8 GREEN, full suite GREEN, data shape matches RESEARCH §F.13 expectation, D-65 disjointness verified by explicit test.

**Suggested next commit context for orchestrator merge:** `feat(06-01): wave 1 — abstain_per_phase aggregation + TestSimulatorAbstain + SKIP_KEYS intermediate` (matches PLAN.md `<output>` suggestion).

## Self-Check: PASSED

Verified all claimed artifacts and commits exist:
- `sphsim/core/device.py` modified (1 line added) — FOUND
- `sphsim/core/simulator.py` modified (9 lines added across 3 sites) — FOUND
- `tests/test_simulator_abstain.py` fully rewritten — FOUND
- `scripts/regression_check.py` SKIP_KEYS extended — FOUND
- Commit `fc277db` (Task 1 — feat) — FOUND in `git log`
- Commit `2fbbd70` (Task 2 — test) — FOUND in `git log`

---
*Phase: 06-report-plots-generator*
*Plan: 01*
*Completed: 2026-05-28*
