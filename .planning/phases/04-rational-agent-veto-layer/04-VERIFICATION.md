---
phase: 04-rational-agent-veto-layer
verified: 2026-05-27T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification: false
---

# Phase 4: Rational Agent veto layer — Verification Report

**Phase Goal:** Wrapper `RationalAgent` weto'uje rekomendacje COMMIT o ujemnym oczekiwanym zysku — dydaktycznie dowodząc warunek motywacyjnej zgodności (incentive compatibility)
**Verified:** 2026-05-27
**Status:** GOAL ACHIEVED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                          | Status     | Evidence                                                                      |
|----|-----------------------------------------------------------------------------------------------|------------|-------------------------------------------------------------------------------|
| 1  | Every strategy (built-in + custom) is default-wrapped in RationalAgent                        | ✓ VERIFIED | `main.py` wraps before SPHSimulator unless `--no-agent`; REPL `do_run` always wraps; custom branch identical. Confirmed: `agent_enabled: True` in JSON without `--no-agent`. |
| 2  | `--no-agent` (CLI) disables agent; without-agent mode in `/compare` shows raw strategy        | ✓ VERIFIED | `args.py` `--no-agent` store_true; `main.py` conditional wrap; `agent_enabled: False`, `n_vetoed_total: 0` confirmed empirically. |
| 3  | Simulation result contains `veto_per_phase: {ph: N}` and `n_vetoed_total` in JSON + human    | ✓ VERIFIED | `simulator.py:146-151` aggregates from `dev.veto_phase_stats`. JSON output confirmed with 28173 vetoes for `phase_prob --probs 1.0,1.0,1.0,1.0,0.0`. Human-readable "VETO przez RationalAgent" section present. |
| 4  | `compare <strategy>` (REPL) / `--compare-agent` (CLI) runs strategy twice and shows delta KPI | ✓ VERIFIED | `run_compare()` in `main.py`; `do_compare()` in `repl.py`; `format_compare()` in `output.py`. JSON `comparison` block with `with_agent/without_agent/delta/agent_helps`. Human table with `Δ (with-no)` column and `✓ TAK / ✗ NIE` verdict. |
| 5  | For demo scenario with high COMMIT rate, `with-agent` has higher `avg_net_profit`             | ✓ VERIFIED | `naive --zeta 0.95 --compare-agent --seed 42` gives `agent_helps: True`, `delta avg_net_profit: +196.83`. 21299 vetoes fired. Empirical proof is decisive. |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact                              | Expected                                    | Status     | Details                                                                     |
|---------------------------------------|---------------------------------------------|------------|-----------------------------------------------------------------------------|
| `sphsim/agent/__init__.py`            | Package entry-point, exports `wrap_with_agent` | ✓ VERIFIED | 4 lines; exports from `rational.py`. Import confirmed in `main.py` and `repl.py`. |
| `sphsim/agent/rational.py`            | `wrap_with_agent` closure factory, E[zysk] formula | ✓ VERIFIED | 57 lines. Formula verbatim from `incentive.py`. Guards D-55/D-57 present. ABSTAIN passthrough. VETO return with `n_vetoed++` and `veto_phase_stats` bookkeeping. |
| `sphsim/core/device.py`               | `n_vetoed: int = 0` + `veto_phase_stats = {}` | ✓ VERIFIED | `n_vetoed` dataclass field, `veto_phase_stats = {}` in `__post_init__`. Both confirmed present. |
| `sphsim/core/simulator.py`            | 3-state decision interface (COMMIT/ABSTAIN/VETO) + veto aggregation | ✓ VERIFIED | `elif decision == 'VETO'` branch at line 69: sets DOWN, does NOT increment `n_abstain`. Post-loop aggregation of `veto_phase_stats` into `veto_per_phase`. Result dict includes `veto_per_phase` and `n_vetoed_total`. |
| `sphsim/cli/args.py`                  | `--no-agent` + `--compare-agent` flags + mutex check | ✓ VERIFIED | Both flags present as `store_true`. Post-parse mutex: `compare_agent and no_agent → error`. `compare_agent and interactive → error`. |
| `sphsim/cli/main.py`                  | `run_compare()` + agent wrap wiring         | ✓ VERIFIED | `run_compare()` function (44 lines). `raw_strategy_fn` snapshot BEFORE wrap prevents double-wrap. Compare branch early-returns before conditional wrap. Both built-in and custom branches wired correctly. |
| `sphsim/cli/repl.py`                  | `do_compare()` command                      | ✓ VERIFIED | `do_compare` at line 226; mirrors `do_run` pattern. `do_help` updated with `compare <nazwa>` line. REPL always wraps in `do_run` (D-58). |
| `sphsim/cli/output.py`                | `format_compare()` + `format_human` VETO section + `format_json` extensions | ✓ VERIFIED | `format_compare()` renders 5×3 table with delta and `✓ TAK / ✗ NIE` verdict. `format_human` dispatches to `format_compare` when `'comparison' in res`. VETO section conditional on `n_vetoed > 0`. `format_json` adds `agent_enabled`, `veto_per_phase`, `n_vetoed_total`. |
| `scripts/regression_check.py`         | D-59 Strategia B: `SKIP_KEYS`, `--no-agent` added at runtime | ✓ VERIFIED | `SKIP_KEYS = ('veto_per_phase', 'n_vetoed_total', 'agent_enabled')`. `run_invocation` appends `--no-agent` to every call. Fixtures unchanged (8/8 confirmed by `regression_check.py` pass). |
| `tests/test_agent.py`                 | 10 unit + integration test cases            | ✓ VERIFIED | 8 unit tests in `TestWrapWithAgent` + 2 integration tests in `TestCLIIntegration`. All pass (123/123 total test suite). |
| `scripts/verify_phase4.sh`            | 21-check phase exit gate                    | ✓ VERIFIED | 21 checks covering all 5 SC + regression + invariants + mutex + REPL + custom. Claimed 21/21. |

---

### Key Link Verification

| From                      | To                              | Via                                        | Status     | Details                                                       |
|---------------------------|----------------------------------|--------------------------------------------|------------|---------------------------------------------------------------|
| `wrap_with_agent`         | `simulator.run()`                | `main.py` wrap before `SPHSimulator()`      | ✓ WIRED    | `strategy_fn = wrap_with_agent(raw_strategy_fn, args.expected_P)` → passed to `SPHSimulator.__init__` |
| `wrap_with_agent`         | `simulator.run()`                | `repl.py do_run` wrap                      | ✓ WIRED    | `strategy_fn = wrap_with_agent(STRATEGIES[name], params.get(...))` |
| `Device.n_vetoed`         | `simulator.run()` result         | `dev.veto_phase_stats` → `veto_per_phase` aggregation | ✓ WIRED | Post-loop loop over `dev.veto_phase_stats` items; `n_vetoed_total` computed. Both in return dict. |
| `veto_per_phase` result   | `format_human` VETO section      | `res.get('veto_per_phase', {})` in `output.py` | ✓ WIRED | VETO section rendered when `n_vetoed > 0`; uses `ic_per_phase` for denominator. |
| `veto_per_phase` result   | `format_json` metrics            | `**{k:v for k,v in res.items() if k not in ('history', 'devices')}` | ✓ WIRED | All result fields including `veto_per_phase`, `n_vetoed_total` included in metrics dict. |
| `run_compare()` result    | `format_compare()`               | `'comparison' in res` dispatch in `format_human` | ✓ WIRED | `format_human` checks `if 'comparison' in res: return format_compare(args, res['comparison'], K1)` |
| `--no-agent` flag         | `format_json` `agent_enabled`    | `not args.no_agent` in `format_json`       | ✓ WIRED    | `'agent_enabled': not args.no_agent` in metrics dict         |
| `raw_strategy_fn` snapshot | `run_compare()` without-agent run | Line 113: snapshot before wrap; line 116: early return | ✓ WIRED | Prevents double-wrap in compare mode; `SPHSimulator(strategy_fn=raw_strategy_fn)` for without-agent run |

---

### Data-Flow Trace (Level 4)

| Artifact          | Data Variable      | Source                                         | Produces Real Data | Status      |
|-------------------|--------------------|------------------------------------------------|--------------------|-------------|
| `format_human`    | `veto_per_phase`   | `simulator.run()` → aggregated from `dev.veto_phase_stats` | Yes — empirically 28173 vetoes observed | ✓ FLOWING |
| `format_compare`  | `comparison.delta` | `run_compare()` computes `res_with[kpi] - res_without[kpi]` for 5 KPIs | Yes — delta avg_net_profit +196.83 observed | ✓ FLOWING |
| `format_json`     | `metrics.agent_enabled` | `not args.no_agent` from parse_args         | Yes — True/False correctly set | ✓ FLOWING |

---

### Behavioral Spot-Checks

| Behavior                                          | Command                                                               | Result                                 | Status |
|---------------------------------------------------|-----------------------------------------------------------------------|----------------------------------------|--------|
| SC#1: agent default-on, JSON has agent_enabled    | `python3 sph_sim.py --strategy naive --zeta 0.5 --seed 42 --json`    | `agent_enabled: True`, fields present  | ✓ PASS |
| SC#2: --no-agent disables, n_vetoed=0             | `python3 sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json` | `agent_enabled: False`, `n_vetoed_total: 0` | ✓ PASS |
| SC#3: veto_per_phase populated, VETO section shown | `python3 sph_sim.py --strategy phase_prob --probs 1.0,1.0,1.0,1.0,0.0 --seed 42` | 28173 vetoes, VETO section in output | ✓ PASS |
| SC#4: comparison JSON block structure             | `python3 sph_sim.py --strategy incentive --expected_P 30 --compare-agent --seed 42 --json` | `comparison.with_agent/without_agent/delta/agent_helps` present | ✓ PASS |
| SC#4: comparison human verdict                    | same, human output                                                     | `✗ NIE` (incentive is idempotent per D-56) | ✓ PASS |
| SC#5: agent_helps==True for naive --zeta 0.95    | `python3 sph_sim.py --strategy naive --zeta 0.95 --compare-agent --seed 42 --json` | `agent_helps: True`, delta +196.83    | ✓ PASS |
| Mutex: --compare-agent + --no-agent              | `python3 sph_sim.py --strategy naive --compare-agent --no-agent`      | Polish error: "wzajemnie wykluczające" | ✓ PASS |
| REPL help contains compare command               | `printf 'help\nexit\n' \| python3 sph_sim.py --interactive`           | `compare <nazwa> ...` line present     | ✓ PASS |
| REPL compare verdict visible                     | `printf 'compare incentive expected_P=30\nexit\n' \| python3 sph_sim.py --interactive` | `✗ NIE` (idempotent, expected) | ✓ PASS |
| Custom strategy + agent default-on               | `python3 sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json` | `agent_enabled: True` | ✓ PASS |
| Custom strategy + --compare-agent                | `python3 sph_sim.py --custom examples/custom_strategy_template.py --compare-agent --seed 42 --json` | `comparison` block present, `agent_helps: True` | ✓ PASS |
| VETO bookkeeping: n_abstain stays 0 during VETO  | Direct unit simulation, 50 T, all-COMMIT strategy with low expected_P | `n_abstain: 0`, `n_vetoed: 100` consistent | ✓ PASS |
| No double-wrap: STRATEGIES registry unchanged    | Identity check after `wrap_with_agent(STRATEGIES['naive'], 100.0)`    | `id(STRATEGIES['naive'])` unchanged    | ✓ PASS |
| D-56 idempotency: incentive + wrapper at same P  | Direct unit call: all phases return same as raw incentive, n_vetoed=0 | 0 vetoes across phases 1-4             | ✓ PASS |
| Regression backwards compat (8/8)                | `python3 scripts/regression_check.py`                                 | `PASS: 8/8`                            | ✓ PASS |
| Full test suite (123/123)                        | `python3 -m unittest discover tests`                                   | `Ran 123 tests in 5.1s OK`             | ✓ PASS |

---

### Requirements Coverage

| Requirement | Phase Plan | Description                                                          | Status       | Evidence                                                     |
|-------------|------------|----------------------------------------------------------------------|--------------|--------------------------------------------------------------|
| AGENT-01    | 04-01/04-02 | Strategia opakowana w RationalAgent, liczy E[zysk] per COMMIT      | ✓ SATISFIED  | `rational.py` formula verified against `incentive.py`. Agent default-on in CLI + REPL. |
| AGENT-02    | 04-01/04-02 | Gdy E[zysk] < 0 → override na ABSTAIN (weto)                       | ✓ SATISFIED  | `if net < 0: return 'VETO'` in wrapper. Simulator handles VETO as DOWN-1-cycle without n_abstain++. |
| AGENT-03    | 04-04       | `--no-agent` flag wyłącza agenta                                    | ✓ SATISFIED  | `store_true` flag in args.py; conditional wrap in main.py both branches. |
| AGENT-04    | 04-01/04-03 | Licznik veto per faza w wyniku                                       | ✓ SATISFIED  | `veto_per_phase` + `n_vetoed_total` in simulator result; rendered in human + JSON. |
| AGENT-05    | 04-04/04-05 | `/compare <strategia>` delta KPI table                              | ✓ SATISFIED  | `do_compare` in REPL, `--compare-agent` in CLI, `format_compare` with 5×3 table. |
| CLI-04      | (carry)     | Backwards compat: v1.0 invocations unchanged                        | ✓ SATISFIED  | `regression_check.py` PASS 8/8. SKIP_KEYS for 3 new fields, fixtures unchanged. |

---

### Anti-Patterns Found

No blockers. Clean scan of all Phase 4 files:

- No `TBD`, `FIXME`, `XXX` markers in any Phase 4 modified file.
- No `TODO`, `HACK`, `PLACEHOLDER`, or "not implemented" markers.
- No stub patterns (`return null`, `return {}`, `return []`).
- No empty handlers or placeholder returns.

---

### Design Notes (not blockers)

**D-64 sparse vs dense `veto_per_phase`:** The CONTEXT D-64 says "preferuj wszystkie fazy z zerami dla spójności wykresu" (prefer all phases with zeros for Phase 6 plot consistency). The actual implementation produces a sparse dict — only phases with `count > 0` appear. When no vetoes occur, the dict is `{}`. This is documented as Claude's Discretion. **Impact on Phase 6:** The plot code will need to handle the sparse dict (fill missing phases with zero). This is a forward-compatibility note, not a Phase 4 deficiency. Phase 6 will simply call `veto_per_phase.get(ph, 0)` per phase.

**SC#5 ROADMAP example vs actual demo:** The ROADMAP says `"(np. incentive --expected_P 30 gdzie strategia rekomenduje COMMIT przy ujemnym zysku)"` as an example for SC#5. However, per D-56, `incentive + wrapper` is idempotent (same formula, same `expected_P` → `n_vetoed = 0`, `delta ≈ 0`). The verify script correctly uses `naive --zeta 0.95` instead, which produces decisive results (`agent_helps: True`, `delta avg_net_profit: +196.83`). The ROADMAP example is illustrative ("np." = "e.g."), not prescriptive. The SC#5 intent — empirical proof that with-agent has higher `avg_net_profit` — is fully satisfied.

**veto_per_phase JSON key type:** Phase data keys in the Python dict are `int` (`{1: N, 2: N}`), but `json.dumps` converts them to strings in JSON output (`{"1": N, "2": N}`). This is standard JSON behavior (JSON keys must be strings). The verify script's type check (`isinstance(m['veto_per_phase'], dict)`) is correct and sufficient. Phase 6 consumers will need to account for string keys when reading from JSON.

**REPL compare uses hardcoded DEFAULT_K1:** `do_compare` in `repl.py` always uses `DEFAULT_K1 = 120` for both simulation runs. The CLI `--compare-agent` branch respects `args.K1`. The difference is only observable when a user sets `--K1` explicitly in CLI. This is consistent with Phase 2/3 REPL design: environment overrides (`--phi`, `--rho`, `--K1`) are deferred to Phase 5.

---

### Human Verification Required

None. All Phase 4 observable truths are verifiable programmatically. The green floor (123/123 tests, 8/8 regression, 21/21 verify script) plus direct behavioral spot-checks cover all SCs.

---

## Summary

**Phase 4: GOAL ACHIEVED**

All 5 ROADMAP Success Criteria are met in the actual source code, not just in SUMMARY claims:

1. **SC#1 VERIFIED** — `wrap_with_agent` is applied before every `SPHSimulator` construction in both CLI (`main.py`) and REPL (`repl.py do_run`), for both built-in and custom strategies. The `--no-agent` escape hatch works correctly.

2. **SC#2 VERIFIED** — `--no-agent` disables the wrapper. `format_json` emits `agent_enabled: false`. `n_vetoed_total: 0`. Regression fixtures remain unchanged (D-59 Strategia B: `SKIP_KEYS` filters 3 new keys at compare time).

3. **SC#3 VERIFIED** — `Device.veto_phase_stats` populated by wrapper closure. `simulator.run()` aggregates to `veto_per_phase` and `n_vetoed_total`. Both appear in JSON metrics and in the `format_human` "VETO przez RationalAgent" section (conditional on `n_vetoed > 0`).

4. **SC#4 VERIFIED** — `run_compare()` (CLI) and `do_compare()` (REPL) both run two deterministic simulations with same seed, compute 5-KPI delta, set `agent_helps` verdict. `format_compare()` renders the 5×3 table with `✓ TAK / ✗ NIE`. The raw-strategy snapshot pattern prevents double-wrapping.

5. **SC#5 VERIFIED** — `naive --zeta 0.95 --compare-agent --seed 42` produces `agent_helps: True` with `delta avg_net_profit: +196.83` and 21299 vetoes. The empirical proof of incentive-compatibility benefit is decisive.

**Critical design properties verified beyond the green floor:**
- 3-state decision interface is honored: VETO branch in simulator does NOT increment `n_abstain` (D-65). Verified via controlled simulation.
- No double-counting: `n_vetoed` is incremented in the wrapper closure, aggregated by simulator post-loop — never double-incremented. Verified end-to-end.
- No double-wrapping: `STRATEGIES` registry always holds unwrapped functions. `raw_strategy_fn` snapshot is taken before conditional wrap. Identity check confirmed.
- D-56 idempotency: `incentive + wrapper` at same `expected_P` produces 0 vetoes. Verified numerically.
- Backwards compatibility: fixtures are original v1.0 format (no Phase 4 keys). `SKIP_KEYS` strategy is correct and clean. `regression_check.py` passes 8/8.

---

_Verified: 2026-05-27_
_Verifier: Claude (gsd-verifier)_
