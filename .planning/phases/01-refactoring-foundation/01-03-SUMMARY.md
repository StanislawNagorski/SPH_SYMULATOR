---
phase: 01-refactoring-foundation
plan: 03
subsystem: sphsim-strategies
tags: [refactor, strategies, registry, plain-functions, stdlib, backwards-compat]

# Dependency graph
requires:
  - phase: 01-01
    provides: regression_check.py oracle + 8 baseline_v1 JSON fixtures (CLI-04 gate)
  - phase: 01-02
    provides: sphsim/config.py (DEFAULT_K0=100 for strategy_incentive); sphsim/core/device.py (Device dataclass used in smoke tests)
provides:
  - sphsim/strategies/ subpackage with 5 plain-function strategy modules (one file per strategy per D-03)
  - sphsim/strategies/__init__.py — STRATEGIES registry dict (5 entries, mutable per D-14, key order preserved from v1.0)
  - StrategyFn type alias (Callable[..., str]) — public contract Phase 3 custom loader will validate against (D-13)
affects: [01-04, 01-05, 03-custom-strategy-loader, sphsim-package, backwards-compatibility]

# Tech tracking
tech-stack:
  added: []  # stdlib only — typing.Callable, no new deps (Phase 1 D-07 constraint preserved)
  patterns:
    - "One-file-per-strategy layout (D-03): each strategy is ~8-19 LOC; mirrors what Phase 3 custom-loader users will produce"
    - "Plain-function strategies (D-13): no Protocol/ABC/inheritance; signature `(dev, l, s, phi, kappa, rho, h, p) -> str` is the entire public contract"
    - "Mutable STRATEGIES dict (D-14): Phase 3 custom loader will inject keys at runtime — no MappingProxyType or frozen wrapper"
    - "Verbatim extraction discipline continued from Plan 02: function bodies copied byte-for-byte from sph_sim.py:123-176, only physical location changes"
    - "Non-destructive refactor: monolith sph_sim.py still untouched after this wave; sphsim/strategies/ exists parallel, regression_check still exit 0"

key-files:
  created:
    - "sphsim/strategies/naive.py — strategy_naive copied verbatim from sph_sim.py:123-126; imports random; 9 LOC"
    - "sphsim/strategies/threshold.py — strategy_threshold copied verbatim from sph_sim.py:128-131; no random import needed; 8 LOC"
    - "sphsim/strategies/phase_prob.py — strategy_phase_prob copied verbatim from sph_sim.py:133-139; imports random; 12 LOC"
    - "sphsim/strategies/incentive.py — strategy_incentive copied verbatim from sph_sim.py:141-153; imports DEFAULT_K0 from sphsim.config (D-04 cross-link); 18 LOC"
    - "sphsim/strategies/adaptive.py — strategy_adaptive copied verbatim from sph_sim.py:155-168; imports random; 19 LOC"
    - "sphsim/strategies/__init__.py — STRATEGIES dict (5 entries, key order naive→threshold→phase_prob→incentive→adaptive verbatim from sph_sim.py:170-176) + StrategyFn = Callable[..., str] type alias; 19 LOC"
  modified: []  # sph_sim.py intentionally NOT touched (CLI-04 invariant: monolith still authoritative, plan 01-04 will perform cutover)

key-decisions:
  - "5 separate strategy files (D-03 compliance) — even threshold (8 LOC) gets its own file rather than a shared utilities module; pattern must match what Phase 3 custom loader will accept (single .py with one strategy function)"
  - "incentive.py imports DEFAULT_K0 from sphsim.config (not a literal 100) — this is the only cross-package import in the subpackage; codifies D-04 (centralized constants are the single override seam for Phase 5)"
  - "STRATEGIES dict key order preserved exactly: naive, threshold, phase_prob, incentive, adaptive — argparse `choices=` listing order in --help would visibly change if reordered, violating CLI-04 (backwards compat surface includes help text)"
  - "No __all__ in sphsim/strategies/__init__.py — v1.0 monolith also lacks __all__; STRATEGIES dict itself is the public contract surface, no need to enumerate twice"
  - "StrategyFn = Callable[..., str] exported alongside STRATEGIES — Phase 3 custom loader will type-check user functions against this alias; making it available now lets downstream code annotate without re-inventing"

patterns-established:
  - "Per-strategy file is ~8-19 LOC: the strategy body itself is small, so DRY (e.g., shared `_check_up(dev)` helper) would harm readability more than it would save lines. Each file stands alone — readable as a self-contained reference for users writing custom strategies in Phase 3."
  - "Polish header comment at top of each module documenting domain intent (`# Strategia X: COMMIT gdy ...`) — consistent with v1.0 monolith convention (sph_sim.py:122-155 section headers) and PROJECT.md constraint ('Język: polski w komentarzach')."
  - "Verify-before-commit ritual: each task runs (1) inline `python3 -c '...'` introspection asserts (signatures, callability, mutability), (2) `python3 scripts/regression_check.py` exit 0, (3) `git diff sph_sim.py` empty — only then `git commit`."

requirements-completed: [CLI-04]

# Metrics
duration: 4m
completed: 2026-05-25
---

# Phase 01 Plan 03: Strategies Extraction + STRATEGIES Registry Summary

**Extracted all 5 strategy functions from the v1.0 monolith into one-file-per-strategy modules under `sphsim/strategies/` and assembled the `STRATEGIES` registry dict (mutable, key-order preserved) in `sphsim/strategies/__init__.py` — all verbatim from `sph_sim.py:123-176`, with `incentive.py` correctly importing `DEFAULT_K0` from `sphsim.config`; monolith untouched, all 8 baseline_v1 fixtures still byte-identical (`regression_check.py` exit 0).**

## Performance

- **Duration:** 4m
- **Started:** 2026-05-25T15:22:00Z (worktree branch ready)
- **Completed:** 2026-05-25T15:24:55Z
- **Tasks:** 2
- **Files modified:** 6 (6 created, 0 modified; `sph_sim.py` intentionally untouched per CLI-04 invariant)

## Accomplishments
- Stood up the `sphsim/strategies/` subpackage with the **one-file-per-strategy** layout that D-03 mandates and that Phase 3 (custom loader) will mirror — `naive.py`, `threshold.py`, `phase_prob.py`, `incentive.py`, `adaptive.py`, each holding exactly one `def strategy_<name>(dev, l, s, phi, kappa, rho, h, p)` copied byte-for-byte from `sph_sim.py:123-168`.
- Locked the `(dev, l, s, phi, kappa, rho, h, p) -> str` signature as the public contract via D-13 — no `Protocol`, no ABC, no inheritance; the signature itself is the only thing Phase 3 custom strategies will be validated against. `inspect.signature` introspection asserts pin this in the verify command.
- Wired the only cross-package dependency in `incentive.py`: `from sphsim.config import DEFAULT_K0`. This is the literal default `exp_P = float(p.get('expected_P', DEFAULT_K0))` from `sph_sim.py:150` — verbatim semantics, but now the source-of-truth is the centralized config module instead of a module-local constant. Smoke test `from sphsim.config import DEFAULT_K0; assert DEFAULT_K0 == 100` confirmed the Plan 02 dependency was satisfied before extraction.
- Built `STRATEGIES` dict in `sphsim/strategies/__init__.py` with the **exact key order** from `sph_sim.py:170-176` (`naive, threshold, phase_prob, incentive, adaptive`) — this order is part of the v1.0 CLI surface (argparse `choices=` listing in `--help`), so any reordering would visibly break backwards compat. Dict left mutable per D-14 so Phase 3 custom loader can `STRATEGIES['custom_name'] = loaded_fn` at runtime — explicit verify test confirms mutability and round-trip add/remove works.
- Confirmed the regression oracle from Plan 01-01 still acts as a gate: `python3 scripts/regression_check.py` returns exit 0 (8/8 PASS) **both** after Task 1 and after Task 2, proving the monolith still produces byte-identical JSON output for all 8 baseline_v1 invocations — the new `sphsim/strategies/` subpackage exists parallel but is not yet wired into the monolith (cutover happens in Plan 01-04).

## Task Commits

Each task was committed atomically:

1. **Task 1: Extract 5 strategy functions to sphsim/strategies/** — `3c9239e` (feat)
2. **Task 2: Build STRATEGIES registry in sphsim/strategies/__init__.py** — `f52b52b` (feat)

_Plan metadata commit (this SUMMARY) follows._

## Files Created/Modified
- `sphsim/strategies/naive.py` — 9 LOC. `import random` + `strategy_naive(dev, l, s, phi, kappa, rho, h, p)` copied verbatim from `sph_sim.py:123-126`. Polish header `# Strategia naive: COMMIT z prawdopodobieństwem zeta.`
- `sphsim/strategies/threshold.py` — 8 LOC. Pure logic, no `random` import needed. `strategy_threshold` verbatim from `sph_sim.py:128-131`. Polish header `# Strategia threshold: COMMIT tylko jeśli dev.phase <= max_phase.`
- `sphsim/strategies/phase_prob.py` — 12 LOC. `import random` + `strategy_phase_prob` verbatim from `sph_sim.py:133-139`. Default `'0.9,0.7,0.5,0.3,0.0'` string preserved exactly (parsing happens inside the function — same `[float(x) for x in str(...).split(',')]` chain).
- `sphsim/strategies/incentive.py` — 18 LOC. `from sphsim.config import DEFAULT_K0` (the only cross-package import in the subpackage) + `strategy_incentive` verbatim from `sph_sim.py:141-153`. Order of operands in the `net = (1 - phi[idx]) * exp_pay - kappa - phi[idx] * rho[idx]` line preserved — any reorder could change floating-point rounding and silently drift fixtures (T-01-06 mitigation).
- `sphsim/strategies/adaptive.py` — 19 LOC. `import random` + `strategy_adaptive` verbatim from `sph_sim.py:155-168`. The three SUS-buffer-threshold branches (`< tgt` → 0.9, `< tgt*2` → 0.5, else → 0.2) preserved in exact order.
- `sphsim/strategies/__init__.py` — 19 LOC. `from typing import Callable` + 5 strategy imports + `StrategyFn = Callable[..., str]` type alias + `STRATEGIES = {'naive': ..., 'threshold': ..., 'phase_prob': ..., 'incentive': ..., 'adaptive': ...}`. No `__all__` (v1.0 also lacks it).

## Decisions Made
- **Polish header comments on every new strategy file** (`# Strategia naive: ...`, `# Strategia threshold: ...`, etc.) — satisfies PROJECT.md constraint "Język: polski w komentarzach" and gives Phase 3 custom-strategy authors a working template to copy. Mirrors the v1.0 monolith convention (`# STRATEGIE` section header at `sph_sim.py:120-122`).
- **`from sphsim.config import DEFAULT_K0` in `incentive.py`, not a hardcoded `100` literal** — codifies D-04 (centralized config is the single override seam for Phase 5). Mechanically, the v1.0 monolith had `DEFAULT_K0` as a module-local constant at line 41 and the strategy at line 150 referenced it by name; preserving the name-based reference (now via cross-package import) is the closest possible verbatim reproduction.
- **`StrategyFn = Callable[..., str]` exported from `__init__.py`** — D-13 allows it as optional, but exporting now (rather than lazily in Phase 3) means downstream code (Plan 04 simulator, Phase 3 loader) can annotate against a stable alias without inventing a new one. `Callable[..., str]` instead of `Callable[[Any, list, int, list, float, list, Callable, dict], str]` is intentional: structural typing on `**kwargs`-style positional args is more permissive and avoids over-constraining custom strategies that might want to ignore arguments.
- **STRATEGIES dict left mutable, no MappingProxyType wrapper** — D-14 explicitly designates Phase 3 will mutate the dict at runtime. Verify test `STRATEGIES['test_custom'] = lambda dev,l,s,phi,kappa,rho,h,p: 'COMMIT'; assert 'test_custom' in STRATEGIES; del STRATEGIES['test_custom']` confirms write-and-delete works without exception.
- **No `_check_up(dev)` helper for the `if dev.status != 'UP': return 'ABSTAIN'` guard** — DRY would consolidate this 2-line pattern that appears in all 5 strategies, but the action note explicitly forbade it ("DRY tutaj zaszkodziłoby — każda strategia to mały plik, czytelność wygrywa"). Each strategy file is self-contained and readable end-to-end, which matters because they serve as templates for Phase 3 user-written strategies.

## Deviations from Plan

None — plan executed exactly as written. All 6 files created with verbatim contents from `sph_sim.py:123-176`; no auto-fixes (Rules 1–3) were needed; no architectural questions (Rule 4) arose. The Plan 02 dependency on `sphsim/config.py:DEFAULT_K0 = 100` was satisfied on the first import (verified inline before extraction began). All inline behavior asserts (signatures, DOWN→ABSTAIN, threshold COMMIT logic, naive determinism under fixed seed, registry mutability, type-alias export) passed on the first run, and `python3 scripts/regression_check.py` returned exit 0 (8/8 PASS) after each task commit.

## Issues Encountered

None during planned work. Both tasks compiled and verified on the first run. The verbatim-extraction discipline established in Plan 02 (read v1.0 source block → write target file → run behavior asserts AND regression check → commit) carried over without friction. The plan author front-loaded the source line ranges (`sph_sim.py:123-126`, `:128-131`, `:133-139`, `:141-153`, `:155-168`, `:170-176`) which made the extraction mechanical and reviewable line-by-line.

The only minor "host adaptation" carried forward from prior plans: `python3` is the available shell command on this machine (no `python` shim), but the new modules don't shell out, so they inherit no portability concern.

## User Setup Required

None — Phase 1 is stdlib-only (D-07). No new dependencies, no environment variables, no external services. The new `sphsim/strategies/` modules import only `random` (stdlib) and `typing.Callable` (stdlib), plus the cross-package import `from sphsim.config import DEFAULT_K0` (also pure-Python stdlib internally).

## Threat Flags

None. No new trust boundaries introduced beyond those already declared in the plan's `<threat_model>`. The mitigations were honored:
- **T-01-06 (strategy signature tampering):** Verify command introspects via `inspect.signature` and asserts `list(sig.parameters.keys()) == ['dev','l','s','phi','kappa','rho','h','p']` for every entry in `STRATEGIES` — any signature drift would fail the commit. This is the contract Phase 3 custom loader will validate against.
- **T-01-07 (random.random() ordering):** Strategies still call `random.random()` (in `naive`, `phase_prob`, `adaptive`), but the monolith continues to use its **own** module-local strategy functions (the new package is parallel, not yet imported by `sph_sim.py`). Therefore the call sequence the monolith generates is unchanged — `regression_check.py` exit 0 proves it. The cutover in Plan 01-04 will require careful preservation of `random.seed(seed)` ordering with respect to the new strategy call sites.
- **T-01-08 (STRATEGIES mutability elevation):** Mutability is intentional per D-14 (Phase 3 custom loader). Risk of accidental overwrite of `'naive'` at runtime is accepted for this academic project.
- **T-01-SC (package installs):** N/A — no installs in Phase 1.

## Next Phase Readiness

- **Plan 01-04 (simulator + CLI wiring + monolith cutover) is unblocked.** The package now provides:
  - `from sphsim.strategies import STRATEGIES` — dict ready to feed `argparse.add_argument('--strategy', choices=list(STRATEGIES.keys()))` in `sphsim/cli/args.py`.
  - `from sphsim.strategies import StrategyFn` — type alias the upcoming `SPHSimulator.__init__(strategy_fn: StrategyFn, ...)` can annotate against.
  - All 5 strategy functions importable individually (Plan 04 can validate that the package and monolith versions produce identical decisions for the same inputs, as a pre-cutover safety check).
- **Plan 04 cutover sequence preview:** (a) emit `sphsim/core/simulator.py` consuming `valuation`, `sph_stp`, `Device`, `STRATEGIES`; (b) emit `sphsim/cli/{args,main,output}.py`; (c) populate `sphsim/__init__.py` with D-16 re-exports; (d) replace `sphsim/__main__.py` `NotImplementedError` with `from sphsim.cli.main import main; main()`; (e) collapse `sph_sim.py` to a thin shim that delegates to `sphsim.cli.main`. **Critical invariant for Plan 04:** the order of `random.*` calls inside `SPHSimulator.__init__` and `SPHSimulator.run` must be preserved exactly — refactoring into the new module must not interleave a new `random.*` call (e.g., for logging) or `regression_check.py` will fail at the cutover commit.
- **Phase 3 (custom strategy loader) is unblocked at the registry level:** `STRATEGIES` is mutable, the signature contract `(dev, l, s, phi, kappa, rho, h, p) -> str` is stable and introspectable, and the five built-in strategy files now serve as concrete templates that Phase 3 docs can point to.
- **`scripts/regression_check.py` remains the authoritative gate** for the rest of Phase 1. Each plan must end with exit 0; exit 1 or 2 blocks the commit. This invariant survived Plan 03 unchanged.

## Self-Check: PASSED

- `sphsim/strategies/naive.py` — FOUND
- `sphsim/strategies/threshold.py` — FOUND
- `sphsim/strategies/phase_prob.py` — FOUND
- `sphsim/strategies/incentive.py` — FOUND
- `sphsim/strategies/adaptive.py` — FOUND
- `sphsim/strategies/__init__.py` — FOUND
- Commit `3c9239e` (Task 1) — FOUND in `git log`
- Commit `f52b52b` (Task 2) — FOUND in `git log`
- `python3 scripts/regression_check.py` → exit 0 (8/8 PASS) after each task
- `git diff sph_sim.py` → empty (monolith untouched)
- `from sphsim.strategies import STRATEGIES` → 5 entries in v1.0 key order
- All 5 strategy signatures match `(dev, l, s, phi, kappa, rho, h, p)` (verified inline)
- `from sphsim.strategies import StrategyFn` → resolves
- `STRATEGIES['custom_name'] = fn` succeeds, `del STRATEGIES['custom_name']` succeeds (mutability verified)
- `wc -l sphsim/strategies/*.py` → max 19 LOC (well under ≤30 plan limit, ≤150 ROADMAP limit)
- `grep -E 'class |Protocol|ABC|@abstractmethod' sphsim/strategies/*.py` → empty (D-13 plain-function compliance)

All claimed artefacts and commits verified on disk and in git history.

---
*Phase: 01-refactoring-foundation*
*Completed: 2026-05-25*
