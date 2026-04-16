# Codebase Concerns

**Analysis Date:** 2025-01-31

---

## Tech Debt

**Hardcoded, non-configurable core model parameters:**
- Issue: `DEFAULT_K0` (100), `DEFAULT_F` (5), `DEFAULT_PHI` ([0.1,0.2,0.3,0.4,1.0]), and `DEFAULT_RHO` ([0.5,0.5,0.7,1.5,3.0]) are fixed constants with no CLI exposure. Any experiment requiring a different failure-probability vector or repair-cost structure requires editing source code directly.
- Files: `sph_sim.py` lines 39–48, `main()` lines 313–319
- Impact: Reproducibility risk — two researchers running "the same" simulation may get different results if one patched the source. The academic optimisation task (`PROMPT_DLA_AGENTA.txt`) lists all five arrays as model parameters yet none are tuneable from the command line.
- Fix approach: Add `--phi`, `--rho`, `--K0`, `--F` CLI arguments parsed as comma-separated floats/ints and pass them through to `SPHSimulator.__init__`.

**`avg_val_last100` silently wrong when `T < 100`:**
- Issue: The summary computation at line 265 always divides by the literal `100`, but the slice `slice(-100, None)` on a list shorter than 100 elements returns fewer than 100 items, yielding a deflated average with no warning.
- Files: `sph_sim.py` lines 263–265
- Impact: Any run with `--T 50` (e.g., for a quick smoke test) produces a silently incorrect KPI that is half the true value.
- Fix approach: Replace hardcoded `/ 100` with `/ len(self.history['val'][last100])`.

**`ABSTAIN` sends device to DOWN — undocumented side effect:**
- Issue: Lines 222–224 put an ABSTAIN device into DOWN status for one cycle. This is a deliberate model choice (device "maintenance"), but it is not mentioned in the module docstring or any inline comment, and the `PROMPT_DLA_AGENTA.txt` specification does confirm this. Any strategy author reading only the code can easily miss it.
- Files: `sph_sim.py` lines 221–224
- Impact: Strategy designers may be unaware that ABSTAIN has a cost (one cycle of downtime), distorting their expected-value calculations.
- Fix approach: Add an inline comment at lines 221–224 referencing the model specification. Consider a `DECISION_OUTCOMES` dict or constant block at module level.

**`alpha ≤ 0` silently collapses to uniform weighting:**
- Issue: The `h` lambda (line 171) uses `if alpha > 0` — values of `alpha < 0` (passed via `--alpha -1`) fall into the else-branch and return the constant `1.0` instead of raising an error or computing `i ** alpha`.
- Files: `sph_sim.py` line 171
- Impact: A user passing a negative alpha receives no error and silently runs with uniform phase weighting, potentially invalidating their experiment.
- Fix approach: Add a validation guard after `parse_args()`: `if args.alpha < 0: raise ValueError("--alpha must be ≥ 0")`.

**`phi` and `rho` arrays not length-validated against `F`:**
- Issue: `DEFAULT_PHI` and `DEFAULT_RHO` each have exactly 5 entries matching `DEFAULT_F = 5`. If `F` were ever changed (in source), no assertion or runtime check verifies that the arrays remain consistent in length.
- Files: `sph_sim.py` lines 47–48, 163–168
- Impact: Silent out-of-bounds fallback (`phi[idx] if idx < len(self.phi) else 1.0` at line 210) masks the inconsistency and forces the last-phase failure probability onto all phases beyond the array length.
- Fix approach: Add `assert len(phi) == F and len(rho) == F` inside `SPHSimulator.__init__`.

---

## Known Bugs

**`strategy_incentive` uses stale zero vector on cycle 0:**
- Symptoms: During the very first cycle, `l_prev = [0, 0, 0, 0]`, so `total_h = 0`. The guard `if total_h <= 0: total_h = 1.0` corrects division but assigns `exp_pay = (h(dev.phase) / 1.0) * expected_P`, i.e., it treats *every* device as if it is the sole provider. For 250 devices this massively inflates the expected payment and causes all of them to COMMIT in cycle 1, producing a large spike that can destabilise the SUS buffer early.
- Files: `sph_sim.py` lines 128–133
- Trigger: Any run with `--strategy incentive`.
- Workaround: Pass a warm-up period or cap `exp_pay` at `expected_P / nU`.

**`sph_stp` integer grid search may miss the true optimum for non-integer K0/K1:**
- Symptoms: The candidate list at lines 69–76 only examines `K0 - u` and `K1 - u` rounded to neighbours `{int(xc)-1, int(xc), int(xc)+1}`. If K0 or K1 are non-integer (possible if the CLI were extended), the exact breakpoint is not evaluated and `best_x` may be suboptimal.
- Files: `sph_sim.py` lines 68–78
- Trigger: Currently latent (K0 and K1 are always integers at default values), but would manifest if `--K0` were added as a float CLI argument.

**`probs` string parsing has no error handling:**
- Symptoms: `strategy_phase_prob` splits `p.get('probs', ...)` by comma and converts with `float()`. A malformed CLI value such as `--probs 0.9,bad,0.5` raises an unguarded `ValueError` with no user-friendly message.
- Files: `sph_sim.py` lines 117–119
- Trigger: `python sph_sim.py --strategy phase_prob --probs 0.9,bad,0.5`
- Workaround: Wrap in try/except and print usage hint.

---

## Security Considerations

**No input validation on numeric CLI arguments:**
- Risk: Values such as `--nU -1`, `--nSUS 0`, `--T 0`, or `--kappa -5` are accepted without validation and lead to either `ZeroDivisionError` (e.g., `/ max(total_dec, 1)` saves most cases but not all) or nonsensical simulation results.
- Files: `sph_sim.py` `parse_args()` lines 278–303, `main()` lines 305–319
- Current mitigation: `max(total_dec, 1)` at line 254 guards one division. All other divisions are unguarded.
- Recommendations: Add `argparse` range constraints (`type=lambda x: max(1, int(x))`) or a dedicated `validate_args(args)` function after `parse_args()`.

---

## Performance Bottlenecks

**Full history retained in memory for all T cycles:**
- Problem: `self.history` stores six separate Python lists each with T entries (default 1000, but configurable up to any value). All device objects are also held in memory for the full run.
- Files: `sph_sim.py` lines 182, 256–261, 273
- Cause: Design choice for post-hoc analysis, but no streaming or ring-buffer option is provided.
- Improvement path: For large T (e.g., `--T 100000`), replace full history with a rolling window of the last 100 entries since only `last100` is used in the final metrics.

**O(nU × T) inner loop is pure Python:**
- Problem: The main simulation loop at lines 190–261 iterates over all `nU` devices per cycle, calling strategy functions, updating dataclasses, and doing arithmetic — entirely in CPython with no vectorisation.
- Files: `sph_sim.py` lines 190–261
- Cause: Readability-first academic implementation.
- Improvement path: Acceptable for current defaults (nU=250, T=1000 ≈ 250,000 iterations). Would require NumPy vectorisation for parameter sweeps across thousands of configurations.

---

## Fragile Areas

**`sph_stp` "best_x" guard assumes symmetric return contract:**
- Files: `sph_sim.py` lines 58–79
- Why fragile: The function returns `(best_x, 0)` when `best_x >= 0` (deposit to SUS) and `(0, -best_x)` when negative (withdraw from SUS). This encoding is implicit — any caller that misunderstands the `(z, y)` sign convention will silently corrupt buffer state.
- Safe modification: Add a docstring explicitly stating the return convention and unit test both the deposit and withdrawal branches.
- Test coverage: Zero tests exist for this function.

**`strategy_phase_prob` silently truncates missing phase probabilities:**
- Files: `sph_sim.py` lines 117–120
- Why fragile: If `--probs` supplies fewer values than there are active phases (e.g., `--probs 0.9,0.7`), `idx >= len(probs)` evaluates to `prob = 0.0`, silently preventing COMMIT for all higher phases with no warning to the user.
- Safe modification: Validate `len(probs) >= F - 1` in `parse_args` or at strategy entry.

**Device phase initialisation uses `F - 1` as upper bound:**
- Files: `sph_sim.py` line 178
- Why fragile: `random.randint(1, F - 1)` produces phases 1..4, which is correct when `F=5`. If `F` were changed to 3, devices could start in the terminal failure-certain phase (3), creating immediate DOWN cascades at t=0.
- Safe modification: Initialise to `random.randint(1, max(1, F - 2))` or document the constraint `F ≥ 3`.

---

## Scaling Limits

**Single fixed random seed produces single deterministic trajectory:**
- Current capacity: One run per seed. Confidence intervals require multiple seeds.
- Limit: The `PROMPT_DLA_AGENTA.txt` baseline table shows single-point metrics (e.g., `avg_val=92.00`) — without variance estimates, strategy comparisons may be dominated by seed-specific noise.
- Scaling path: Add a `--n_runs N` argument that aggregates results across `N` seeds and reports mean ± std.

**No batch/sweep mode:**
- Current capacity: One strategy run per invocation.
- Limit: Comparing all 5 strategies with a grid of parameters requires external shell scripting.
- Scaling path: Add a `--sweep` mode or provide a companion `sweep.py` script that invokes the simulator programmatically and outputs a comparison table.

---

## Test Coverage Gaps

**Zero test coverage:**
- What's not tested: All functions (`valuation`, `sph_stp`), all five strategy functions, `SPHSimulator.__init__`, `SPHSimulator.run`, CLI parsing, and JSON output format.
- Files: `sph_sim.py` (entire file)
- Risk: Any refactoring of `sph_stp`, `valuation`, or the payment distribution logic (lines 237–244) can silently break the simulation's mathematical correctness with no safety net.
- Priority: High — core model functions (`valuation`, `sph_stp`) are pure functions with clear mathematical definitions and are trivially unit-testable.

**`sph_stp` edge case `x_min > x_max` untested:**
- What's not tested: The early-return `return 0, 0` at line 66 is triggered when `s > u + (nSUS - s)` — a valid physical state (SUS is full and more providers than the buffer can absorb). There are no tests confirming this path returns correctly.
- Files: `sph_sim.py` lines 63–66
- Risk: If this branch is reached in a live run, the `z, y = 0, 0` return is correct but the buffer update `self.s = max(0, self.s + 0 - 0)` is a no-op, which is likely correct — but it has never been verified.
- Priority: Medium.

**`valuation` interval semantics untested:**
- What's not tested: The boundary values `u = K0 - 1`, `u = K0`, `u = K1`, `u = K1 + 1`, and the `K1 = inf` branch.
- Files: `sph_sim.py` lines 53–56
- Risk: An off-by-one error in the `K0 ≤ u ≤ K1` window directly drives all consumer valuation KPIs.
- Priority: High.

---

## Missing Critical Features

**No plotting or visualisation:**
- Problem: The `history` dict is populated each cycle but the only output mode is a terminal table or JSON dump. No time-series chart of `val`, `sus`, or `providers` is produced.
- Blocks: Visual comparison of strategy convergence, which is the primary deliverable of the academic task.
- Files: `sph_sim.py` lines 182, 322–358

**`K0` not exposed as a CLI argument:**
- Problem: `K0` is hardcoded to `DEFAULT_K0 = 100` in `main()` at line 314 (`K0=DEFAULT_K0`). The `valuation` function accepts it as a parameter and could support it, but there is no `--K0` flag.
- Blocks: Any experiment where the minimum service threshold differs from 100.
- Files: `sph_sim.py` line 314

---

*Concerns audit: 2025-01-31*
