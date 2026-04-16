# Architecture

**Analysis Date:** 2025-01-31

## Pattern Overview

**Overall:** Single-file simulation script with a procedural/OOP hybrid pattern.

**Key Characteristics:**
- All logic lives in one Python file (`sph_sim.py`, 363 lines) — no modules, no packages
- Strategy pattern: 5 interchangeable decision functions registered in a `STRATEGIES` dict
- `SPHSimulator` class encapsulates full simulation state and the time-loop
- CLI (argparse) is the sole entry point; JSON output mode enables machine-readable results
- Domain is a multi-agent service mediation model (game theory / econometrics)

## Layers

**Constants Layer:**
- Purpose: Define default simulation parameters derived from the academic paper
- Location: `sph_sim.py` lines 39–48
- Contains: `DEFAULT_NU`, `DEFAULT_NSUS`, `DEFAULT_K0`, `DEFAULT_K1`, `DEFAULT_F`, `DEFAULT_T`, `DEFAULT_KAPPA`, `DEFAULT_ALPHA`, `DEFAULT_PHI`, `DEFAULT_RHO`
- Depends on: Nothing
- Used by: `main()`, `SPHSimulator.__init__`

**Model Functions Layer:**
- Purpose: Pure mathematical functions representing the economic model
- Location: `sph_sim.py` lines 53–79
- Contains:
  - `valuation(u, K0, K1)` — consumer valuation function g(u); returns K0 if u in [K0, K1], else 0
  - `sph_stp(u, s, nSUS, K0, K1)` — SPH-STP buffer policy optimizer; returns `(z*, y*)` that maximize total payment `P = g(u-x) + x`
- Depends on: Nothing (pure functions)
- Used by: `SPHSimulator.run()`

**Device Model Layer:**
- Purpose: Represent a single autonomous device (agent) with mutable state
- Location: `sph_sim.py` lines 84–99
- Contains: `Device` dataclass with fields: `id`, `phase` (1..F-1 when UP, -1 when DOWN), `status` ('UP'|'DOWN'), `down_left`, `earnings`, `costs`, `n_commit`, `n_abstain`, `n_delivered`, `n_failed`; computed property `net_profit`
- Depends on: `dataclass` from stdlib
- Used by: `SPHSimulator.__init__`, `SPHSimulator.run()`

**Strategy Layer:**
- Purpose: Pluggable decision functions — each receives device state + environment state and returns `'COMMIT'` or `'ABSTAIN'`
- Location: `sph_sim.py` lines 104–157
- Contains:
  - `strategy_naive(dev, l, s, phi, kappa, rho, h, p)` — random COMMIT with probability `zeta`
  - `strategy_threshold(dev, l, s, phi, kappa, rho, h, p)` — COMMIT only if `dev.phase <= max_phase`
  - `strategy_phase_prob(dev, l, s, phi, kappa, rho, h, p)` — per-phase probability list
  - `strategy_incentive(dev, l, s, phi, kappa, rho, h, p)` — COMMIT when expected net profit > 0
  - `strategy_adaptive(dev, l, s, phi, kappa, rho, h, p)` — probability based on SUS buffer level `s`
  - `STRATEGIES` dict mapping name → function
- Depends on: `random`, `Device` state, model constants
- Used by: `SPHSimulator.run()` via `self.strategy_fn`

**Simulation Engine Layer:**
- Purpose: Orchestrate the T-cycle simulation loop, applying strategy decisions and model mechanics
- Location: `sph_sim.py` lines 162–273, class `SPHSimulator`
- Contains: `__init__` (initialize devices, buffer, history), `run()` (main loop returning metrics dict)
- Depends on: `Device`, all strategy functions, `valuation()`, `sph_stp()`
- Used by: `main()`

**CLI / Output Layer:**
- Purpose: Parse arguments, construct simulator, format and print results
- Location: `sph_sim.py` lines 278–363, functions `parse_args()` and `main()`
- Contains: argparse setup with strategy selection + environment overrides; human-readable table output and `--json` machine output mode
- Depends on: `SPHSimulator`, `STRATEGIES`, stdlib `argparse`, `json`
- Used by: OS (invoked via `python sph_sim.py`)

## Data Flow

**Simulation Cycle (per tick t):**

1. `main()` builds `SPHSimulator` with chosen strategy function and params
2. `sim.run()` enters the T-cycle loop
3. For each device: if DOWN, decrement `down_left`; if UP, call `strategy_fn(dev, l_prev, s, ...)` → `'COMMIT'` or `'ABSTAIN'`
4. COMMIT devices: pay cost `kappa`; with probability `phi[phase]` → failure (pay `rho[phase]`, go DOWN); else → join `providers[]` list
5. ABSTAIN devices: go DOWN for 1 cycle (no cost)
6. After all device decisions: `u = len(providers)` passed to `sph_stp(u, s, nSUS, K0, K1)` → `(z, y)` buffer transfer amounts
7. `svc_to_cons = u - z + y`; `P_total = valuation(svc_to_cons, K0, K1) + z - y`
8. Payment distributed to providers proportional to `h(phase) = phase^alpha`; each provider advances phase `i → i+1`
9. Buffer updated: `s = max(0, s + z - y)`; `l_prev = l_curr` (provider counts per phase)
10. Metrics appended to `self.history`

**Output Path:**
- `sim.run()` returns dict with scalar metrics + `history` dict + `devices` list
- `main()` formats as human-readable table or JSON depending on `--json` flag

**State Management:**
- All mutable state lives inside `SPHSimulator` instance and individual `Device` objects
- `self.s` — current SUS buffer occupancy (integer, 0..nSUS)
- `self.history` — dict of lists, one entry per cycle, for post-run analysis
- `l_prev` — provider counts per phase from previous cycle (fed to strategy functions as context)
- No global mutable state; `random.seed(seed)` ensures reproducibility

## Key Abstractions

**Strategy Function Signature:**
- Purpose: Uniform interface for all COMMIT/ABSTAIN decision rules
- Signature: `fn(dev: Device, l: List[int], s: int, phi: List[float], kappa: float, rho: List[float], h: Callable, p: dict) -> str`
- Examples: `strategy_naive`, `strategy_incentive` (all in `sph_sim.py` lines 104–157)
- Pattern: Strategy pattern — selected at CLI parse time, stored as `self.strategy_fn`, called once per UP device per cycle

**SPH-STP Optimizer (`sph_stp`):**
- Purpose: Compute optimal buffer transfer amounts to maximize total payment
- Location: `sph_sim.py` lines 58–79
- Pattern: Candidate-point search over integer `x = z - y` in feasible range `[-s, min(u, nSUS-s)]`; returns `(z, 0)` if net transfer positive else `(0, -x)`

**Device Lifecycle:**
- UP → COMMIT → (success) → UP phase+1 | (failure) → DOWN 1 cycle → UP phase 1
- UP → ABSTAIN → DOWN 1 cycle → UP phase 1
- Phase 5 (F-1 = 4, but φ_5=1.0) always fails if COMMIT → strategy functions guard with `if phi[idx] >= 1.0: return 'ABSTAIN'`

## Entry Points

**CLI Entry Point:**
- Location: `sph_sim.py` lines 305–362, `main()` guarded by `if __name__ == '__main__'`
- Triggers: `python sph_sim.py --strategy <name> [options]`
- Responsibilities: Argument parsing → simulator construction → run → output formatting

**Programmatic Entry Point:**
- Location: `sph_sim.py` lines 162–273, `SPHSimulator` class
- Triggers: Direct instantiation from external Python code or test harnesses
- Responsibilities: Full simulation lifecycle; returns results dict from `run()`

## Error Handling

**Strategy:** Minimal — rely on Python defaults and argparse validation.

**Patterns:**
- `argparse` enforces `--strategy` choice from `STRATEGIES.keys()` — invalid strategies rejected at parse time
- `K1 = float('inf') if args.K1 < 0 else args.K1` — sentinel value handles unbounded valuation case
- `max(total_dec, 1)` guards division by zero in `delivery_ratio` calculation
- `if x_min > x_max: return 0, 0` in `sph_stp` handles infeasible buffer state
- No explicit exception handling or logging of errors

## Cross-Cutting Concerns

**Logging:** None — `--verbose` flag prints sampled cycle stats to stdout via `print()`
**Validation:** argparse type enforcement only; no runtime invariant checks on simulation state
**Reproducibility:** `random.seed(seed)` called once in `SPHSimulator.__init__`; default seed=42
**Randomness:** Only stdlib `random` module used (no numpy)
**Language:** Polish — all user-facing strings, comments, variable names (metryki, cykli, etc.) are in Polish

---

*Architecture analysis: 2025-01-31*
