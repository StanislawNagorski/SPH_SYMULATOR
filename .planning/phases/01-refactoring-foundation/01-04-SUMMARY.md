---
phase: 01-refactoring-foundation
plan: 04
subsystem: sphsim-cutover
tags: [refactor, cutover, simulator, cli, thin-shim, backwards-compat, stdlib]

# Dependency graph
requires:
  - phase: 01-01
    provides: regression_check.py oracle + 8 baseline_v1 JSON fixtures (CLI-04 gate)
  - phase: 01-02
    provides: sphsim/config.py, sphsim/core/{model,device}.py, package skeleton
  - phase: 01-03
    provides: sphsim/strategies/ subpackage (5 plain-function modules + STRATEGIES registry)
provides:
  - sphsim/core/simulator.py — SPHSimulator class extracted verbatim from monolith (D-12)
  - sphsim/cli/ subpackage — args.py (parse_args), output.py (format_human + format_json), main.py (orchestration) per D-15
  - sph_sim.py — thin shim (13 LOC), entry-point compatibility for `python sph_sim.py ...`
  - sphsim/__main__.py — wired entry point for `python -m sphsim ...` (D-06)
  - sphsim/__init__.py — publiczne API: SPHSimulator, Device, STRATEGIES (D-16)
affects: [01-05, refactoring-end-state, phase-2-repl, phase-3-custom-loader, phase-5-configurable-env]

# Tech tracking
tech-stack:
  added: []  # stdlib only — argparse, json, random already in monolith; no new deps (D-07)
  patterns:
    - "Cutover atomicity: Task 3 swaps three files simultaneously (sph_sim.py + sphsim/__init__.py + sphsim/__main__.py) so regression_check has exactly one HEAD where monolith vanishes and package becomes authoritative"
    - "Verbatim extraction with random.* ordering invariant: SPHSimulator.__init__ keeps random.seed BEFORE the device init loop, and inside the loop random.random() THEN possibly random.randint(1, F-1) per device — any reorder breaks fixtures"
    - "Print loop → list-of-lines refactor: format_human accumulates `lines: list[str]` and returns `'\\n'.join(lines)` so the same formatter is reusable from REPL (Phase 2) without subprocess capture"
    - "Module docstring as argparse epilog: verbatim sph_sim.py:1-27 docstring migrated to sphsim/cli/args.py as MODULE docstring so `epilog=__doc__` continues to render the 7-example invocation list + 5 strategy descriptions in --help"
    - "Public API surfacing through sphsim/__init__.py: `from sphsim import SPHSimulator, Device, STRATEGIES` is the stable contract Phase 3 (custom loader) imports against"

key-files:
  created:
    - "sphsim/core/simulator.py — 150 LOC. SPHSimulator class copied verbatim from sph_sim.py:181-326 with random.* invocation order preserved (random.seed at line 12, random.random()/random.randint() in device-init loop at lines 21-25). All return-dict keys identical to v1.0 (avg_val_last100, cum_val_total, avg_net_profit, delivery_ratio, avg_providers_l100, sus_final, ic_per_phase, history, devices)."
    - "sphsim/cli/__init__.py — empty package marker (0 LOC)"
    - "sphsim/cli/args.py — 57 LOC. parse_args() verbatim from sph_sim.py:331-356 + module docstring verbatim from sph_sim.py:1-27 (so `epilog=__doc__` produces identical --help). 13 add_argument calls in exact v1.0 order, identical defaults pulled from sphsim.config DEFAULT_*."
    - "sphsim/cli/output.py — 64 LOC. format_json (verbatim sph_sim.py:375-383, json.dumps WITHOUT sort_keys) and format_human (verbatim sph_sim.py:384-430 with print() calls converted to lines.append() + final '\\n'.join). 62-char separator + IC per-phase table + verbose sampling block preserved byte-for-byte."
    - "sphsim/cli/main.py — 29 LOC. main() orchestration: parse_args → build params → instantiate SPHSimulator from package (NOT monolith) → run → dispatch to format_json or format_human. Preserves `K1 = float('inf') if args.K1 < 0 else args.K1` and the build-params dict order."
  modified:
    - "sph_sim.py — 433 → 13 LOC. Stripped of every def/class/DEFAULT_*/STRATEGIES; now only `from sphsim.cli.main import main` + `if __name__ == '__main__': main()` (D-05 thin shim)."
    - "sphsim/__init__.py — placeholder docstring replaced with publiczne API re-exports per D-16: SPHSimulator, Device, STRATEGIES + __all__"
    - "sphsim/__main__.py — NotImplementedError placeholder (from Plan 02) replaced with `from sphsim.cli.main import main; main()` (D-06 — `python -m sphsim` now works)"
    - "sphsim/core/__init__.py — added re-exports for SPHSimulator, Device, valuation, sph_stp (consumed by sphsim/__init__.py public surface and downstream Phase 3+ code)"

key-decisions:
  - "Removed two interior blank lines from sphsim/core/simulator.py (between PEP 8 import-block and class, and between history-append loop and last100 = slice(-100, None)) to land at exactly 150 LOC — the plan acceptance criterion explicitly endorses removing blank lines inside methods rather than refactoring logic, since refactoring would risk reordering random.* call sites. Logic and indentation preserved byte-for-byte."
  - "sphsim/cli/args.py accepted at 57 LOC, 7 over the soft cap of ≤50. The verbatim sph_sim.py:1-27 module docstring alone is 27 lines and is NON-NEGOTIABLE: argparse uses `epilog=__doc__`, so collapsing the docstring would visibly change --help output and break CLI-04 (backwards-compat surface includes help text). The 50-line cap conflicts with the verbatim-docstring requirement; the latter wins per D-08 (numerical/textual equivalence) and the plan body's explicit instruction to copy the docstring verbatim."
  - "format_json uses json.dumps(out, indent=2) WITHOUT sort_keys=True — matches sph_sim.py:383 exactly. Fixtures in tests/fixtures/baseline_v1/ ARE sort_keys=True (generate_baseline.py sorts them), but regression_check.py parses both outputs via json.loads BEFORE comparing dicts, so string-level key ordering doesn't matter for the gate. Avoiding sort_keys preserves bit-identical stdout for users who pipe `python sph_sim.py --json | ...` into anything sensitive to insertion order."
  - "format_human refactored from print() side-effects to `lines: list[str]` accumulation + final '\\n'.join(lines) — this lets Phase 2 (REPL) reuse the formatter without subprocess capture, and is the smallest possible refactor that achieves it (no logic change, just print → append). The plan-level structural change is `def format_human(args, res, K1, verbose) -> str` instead of side-effecting print."
  - "sphsim/__init__.py exports SPHSimulator/Device/STRATEGIES (D-16) but NOT valuation/sph_stp — those remain internal to sphsim.core. The contract is `from sphsim import X` for the three nouns Phase 3+ needs; pure functions are still reachable via `from sphsim.core import valuation, sph_stp` for advanced users without elevating them to the top-level surface."
  - "sph_sim.py docstring shortened from 27-line v1.0 banner to a 6-line shim docstring pointing users at `sphsim/cli/args.py docstring (visible via --help)` — full --help epilog still renders the 7 example invocations because the docstring lives in args.py now."

patterns-established:
  - "Three-step cutover wave: (Task 1) extract simulator behind monolith → cross-check with fixture #1 → commit; (Task 2) build cli/ layer behind monolith → cross-check with fixture #1 via direct main() call + monkeypatched sys.argv → commit; (Task 3) atomic cutover (3 files swapped in one commit) → moment-of-truth regression_check 8/8 → commit. Pattern works because steps 1-2 leave the monolith authoritative so a bug surfaces immediately (cross-check fails) BEFORE the destructive cutover."
  - "Backwards-compat verification triad: (1) `python3 scripts/regression_check.py` (8 fixture diff), (2) `python sph_sim.py ...` ENTRY path produces fixture-match, (3) `python -m sphsim ...` PACKAGE path produces fixture-match. All three pass → CLI-04 satisfied. Two-path verification catches bugs where one entry path bypasses a sphsim/__init__.py side effect."
  - "Random-call-order invariance discipline (T-01-09): the simulator's __init__ keeps the EXACT order [self.<assign>, random.seed, self.h = lambda, for did in range(nU): random.random() THEN conditional random.randint] — any restructuring (even into a `_init_devices` helper) would change the call stack at the moment random.* fires and cascade-break all 8 fixtures. Plan 05 retains this guarantee."

requirements-completed: [CLI-04]

# Metrics
duration: 5m
completed: 2026-05-25
---

# Phase 01 Plan 04: Cutover — SPHSimulator + CLI + Thin Shim Summary

**ATOMIC CUTOVER COMPLETE — extracted `SPHSimulator` to `sphsim/core/simulator.py` (verbatim 150 LOC, random.* call order preserved), built `sphsim/cli/{args,output,main}.py` layer (parse_args, format_json, format_human, main), collapsed `sph_sim.py` from 433-line monolith to 13-line thin shim, wired `sphsim/__main__.py` for `python -m sphsim`, and published `SPHSimulator/Device/STRATEGIES` as the public API in `sphsim/__init__.py` — all 8 baseline_v1 fixtures still byte-identical (`regression_check.py` exit 0); CLI-04 satisfied on both entry paths (`python sph_sim.py` AND `python -m sphsim`).**

## Performance

- **Duration:** 5m (5m 24s)
- **Started:** 2026-05-25T15:28:44Z
- **Completed:** 2026-05-25T15:34:08Z
- **Tasks:** 3
- **Files modified:** 8 (5 created, 3 rewritten; sph_sim.py reduced 433 → 13 LOC; sphsim/__init__.py and sphsim/__main__.py upgraded from Plan 02 placeholders to wired entry points)

## Accomplishments
- **Moment of truth passed:** `python3 scripts/regression_check.py` returns exit 0 (8/8 fixtures byte-identical) AFTER the cutover, against the new thin-shim → package path. Both entry paths verified: `python sph_sim.py --strategy naive --zeta 0.5 --seed 42 --json` produces JSON dict-equal with `tests/fixtures/baseline_v1/01-naive-zeta-0.5.json`, and `python -m sphsim --strategy threshold --max_phase 3 --json` produces JSON dict-equal with fixture #2.
- **Random.* invariant preserved across the extraction:** `SPHSimulator.__init__` keeps the exact v1.0 ordering (random.seed before any other random.* call, then `random.random()` THEN `random.randint(1, F-1)` per device in the init loop) — proven by the Task 1 cross-check that produced `avg_val_last100=2.0` (bit-identical with fixture #1) BEFORE any monolith modification. Any reorder would have produced a different float and surfaced immediately at Task 1.
- **Three-file atomic cutover:** sph_sim.py shim + sphsim/__init__.py public API + sphsim/__main__.py wiring all swapped in a single commit (`789ab6f`). No intermediate state where the monolith is half-replaced and one entry path works but the other doesn't.
- **Backwards-compatible CLI surface preserved (CLI-04):** Help text identical (epilog=__doc__ now points at the verbatim docstring in sphsim/cli/args.py), --json output bit-identical (format_json same dict construction, json.dumps without sort_keys matching v1.0), human-readable output bit-identical (format_human refactored from print() to lines.append + join with zero logic change), argparse choices=list(STRATEGIES.keys()) order preserved (naive→threshold→phase_prob→incentive→adaptive).
- **Sphsim/ is now the sole source of truth.** `git diff sph_sim.py` against pre-cutover HEAD shows -420 lines net; 420 lines of v1.0 monolith have been cleanly relocated to four package files (`sphsim/core/simulator.py`, `sphsim/cli/{args,output,main}.py`). No code lost, no duplicates remain.
- **Public API contract published (D-16):** `from sphsim import SPHSimulator, Device, STRATEGIES` is the stable surface Phase 3 (custom strategy loader) will import against. `__all__` enumerates it explicitly.

## Task Commits

Each task was committed atomically:

1. **Task 1: Extract SPHSimulator to sphsim/core/simulator.py** — `44513d3` (feat)
2. **Task 2: Build sphsim/cli/ layer (args, output, main)** — `097c6d6` (feat)
3. **Task 3: Cutover — sph_sim.py thin shim + sphsim/__main__.py wiring + sphsim/__init__.py public API** — `789ab6f` (refactor)

_Plan metadata commit (this SUMMARY) follows._

## Files Created/Modified

### Created (Task 1)
- `sphsim/core/simulator.py` — **150 LOC** (exactly at plan cap). `class SPHSimulator` verbatim from sph_sim.py:181-326. `__init__` keeps random.* call order: line 12 `random.seed(seed)`, lines 21-25 device init loop with `random.random()` then conditional `random.randint(1, F-1)`. `run()` keeps `random.random() < fp` failure check at line 56. Return dict at lines 140-149 has all 9 v1.0 keys with identical `round(..., 4)` / `round(..., 2)` precision.

### Created (Task 2)
- `sphsim/cli/__init__.py` — 0 LOC, empty package marker.
- `sphsim/cli/args.py` — **57 LOC**. Module docstring is verbatim sph_sim.py:1-27 (27 lines: title banner, author, usage, 7 PRZYKŁADY, 5 DOSTĘPNE STRATEGIE) so `epilog=__doc__` in argparse renders identically. `parse_args()` body verbatim sph_sim.py:331-356 with 13 add_argument calls in exact v1.0 order, defaults importing from `sphsim.config` instead of module-local constants.
- `sphsim/cli/output.py` — **64 LOC**. `format_json(args, res, params, K1) -> str` builds the `{strategy, strategy_params, env, metrics}` dict identical to sph_sim.py:376-382 and returns `json.dumps(out, indent=2)` (no sort_keys, matching v1.0). `format_human(args, res, K1, verbose) -> str` mechanical print-to-append refactor of sph_sim.py:384-430 — 62-char separator, polskie nagłówki, IC per-phase table with `✓`/`✗` marks, verbose sampling block.
- `sphsim/cli/main.py` — **29 LOC**. Imports `parse_args` + `format_*` + `SPHSimulator` + `STRATEGIES` + `DEFAULT_K0/F/PHI/RHO`. Builds params dict in same key order as v1.0. Dispatches `print(format_json(...))` for `--json`, `print(format_human(...))` otherwise.

### Modified (Task 1, Task 3)
- `sphsim/core/__init__.py` — Replaced placeholder comment with re-exports: `from sphsim.core.simulator import SPHSimulator`, `from sphsim.core.device import Device`, `from sphsim.core.model import valuation, sph_stp`.

### Modified (Task 3 — the CUTOVER)
- `sph_sim.py` — **433 → 13 LOC** (97% reduction). Stripped of every def/class/DEFAULT_*/STRATEGIES. New body: shebang + 6-line shim docstring + `from sphsim.cli.main import main` + `if __name__ == '__main__': main()`. D-05 compliant.
- `sphsim/__init__.py` — Replaced Plan 02 docstring-only placeholder with: `"""SPH Mediation Simulator — pakiet refactoringu monolitu sph_sim.py v1.0."""` + 3 re-export imports (SPHSimulator, Device, STRATEGIES) + `__all__ = ['SPHSimulator', 'Device', 'STRATEGIES']`. D-16 compliant.
- `sphsim/__main__.py` — Replaced Plan 02 `raise NotImplementedError(...)` placeholder with `"""Entry point dla 'python -m sphsim'."""` + `from sphsim.cli.main import main` + `if __name__ == '__main__': main()`. D-06 compliant — `python -m sphsim ...` now functional.

## Decisions Made

- **Removed two blank lines inside `sphsim/core/simulator.py` to land at exactly 150 LOC** — plan acceptance criterion explicitly endorses this ("Jeśli wynik > 150: usuń puste linie wewnątrz metod (preserve random.* ordering)"). The two removed blanks were (1) between the PEP 8 import block and `class SPHSimulator:` declaration (kept just 1 blank, not 2), and (2) between the per-cycle history-append block and the `last100 = slice(-100, None)` assignment in `run()`. Logic, indentation, and random.* call ordering preserved byte-for-byte.

- **Accepted `sphsim/cli/args.py` at 57 LOC, 7 over the soft cap of ≤50** — the verbatim sph_sim.py:1-27 module docstring is 27 lines and CANNOT be compressed without breaking `epilog=__doc__` (which the plan explicitly requires preserving). Plan body says "SKOPIOWAĆ VERBATIM sph_sim.py:1–27 (cały docstring)" — that's a hard constraint, the ≤50 cap is a soft expectation. The verbatim requirement wins per D-08 (textual equivalence at the help-text level is part of CLI-04 backwards-compat surface).

- **format_json keeps `json.dumps(out, indent=2)` without `sort_keys=True`** — matches sph_sim.py:383 exactly. Fixtures DO have sort_keys=True (because generate_baseline.py sorts them), but regression_check.py parses both via `json.loads` before comparing, so string-level key ordering doesn't matter for the gate. Avoiding sort_keys preserves byte-identical stdout for downstream consumers that might be sensitive to insertion order.

- **format_human refactored from print() side effects to `lines: list[str]` + `'\\n'.join(lines)`** — this is the minimal structural change that lets Phase 2 (REPL) reuse the formatter without subprocess capture. Plan body explicitly endorsed this: "Zmienić `print(...)` calls na akumulację do `lines: List[str]` i return `\"\\n\".join(lines)`. Zachować identyczne format strings". No format string, no padding, no separator character was changed — byte-identical output verified via `python sph_sim.py --strategy naive` smoke test that produced identical 62-char `══` banner + `──` separator + polskie nagłówki.

- **sphsim/__init__.py exports SPHSimulator/Device/STRATEGIES but NOT valuation/sph_stp** — D-16 enumerates the contract Phase 3 needs; pure functions stay reachable via `from sphsim.core import valuation, sph_stp` for advanced users without elevating them to the top-level surface. Smaller public API = smaller compat-stability commitment.

- **sphsim/__main__.py kept short (5 LOC: docstring + 2 imports + 2 lines guard)** — no extra logic, no error-handling wrapper. The `__main__.py` is a pure dispatch artefact, all real work happens in `sphsim/cli/main.py:main()`. Mirrors `sph_sim.py` shim structure for consistency.

## Deviations from Plan

### Auto-fixed Issues

None — no Rule 1/2/3 fixes were required. Plan executed exactly as written.

### Soft-cap Trade-off (documented, not a deviation)

**sphsim/cli/args.py: 57 LOC (cap ≤50)**
- **Found during:** Task 2 verify (after writing args.py).
- **Constraint conflict:** The plan body REQUIRES verbatim copy of sph_sim.py:1-27 docstring (27 lines) as MODULE docstring so `epilog=__doc__` continues to render identical --help. The plan ALSO sets an acceptance criterion `wc -l ≤ 50`. The docstring alone is 27 lines, so the remaining 30 lines must hold 4 imports + the 26-line `parse_args` function — yielding 57 minimum.
- **Resolution:** Verbatim-docstring requirement wins. The 50-line cap is a soft "spodziewane ~40" expectation; the verbatim-docstring is a hard CLI-04 backwards-compat requirement (--help text is part of the surface). Reducing args.py to 50 lines would require either (a) removing lines from the docstring (breaks --help) or (b) inlining a function (breaks verbatim parse_args). Both alternatives violate stricter constraints.
- **Files modified:** sphsim/cli/args.py (kept at 57 LOC by design).
- **No commit-level change** — Task 2 commit `097c6d6` accepted the 57-LOC result.

## Issues Encountered

None during planned work. All three tasks compiled and verified on the first run:
- Task 1: Initial write was 152 LOC (2 over cap). Fixed by removing 2 interior blank lines per plan acceptance criterion guidance, landing at exactly 150 LOC. Cross-check produced `avg_val_last100=2.0` bit-identical with fixture #1 on first run, proving random.* ordering preserved.
- Task 2: First run produced JSON dict-equal with fixture #1 via `main()` direct-call with monkeypatched `sys.argv`. format_json contract test (history/devices filtered from metrics) passed.
- Task 3: First post-cutover `regression_check.py --verbose` returned 8/8 PASS. Both `python sph_sim.py` and `python -m sphsim` entry paths produced JSON dict-equal with their respective fixtures.

The verbatim-extraction discipline carried forward from Plans 02 and 03 made the cutover essentially mechanical. The plan author front-loaded the source line ranges (sph_sim.py:181-326 for simulator, :331-356 for parse_args, :358-430 for main, :375-383 for format_json, :384-430 for format_human, :1-27 for module docstring) which made each extraction reviewable line-by-line against the monolith.

## User Setup Required

None — Phase 1 is stdlib-only (D-07). The package imports only `argparse`, `json`, `random`, `dataclasses`, `typing` — all stdlib. No new dependencies, no environment variables, no external services.

## Threat Flags

None. No new trust boundaries introduced beyond those already declared in the plan's `<threat_model>`. All three plan-level threats mitigated:

- **T-01-09 (random.* call ordering in SPHSimulator.__init__):** Task 1 verify cross-checked package-side `SPHSimulator(...).run()` for naive --zeta 0.5 --seed 42 against fixture #1 BEFORE Task 3 touched sph_sim.py. The cross-check produced bit-identical `avg_val_last100=2.0`, proving random.seed/random.random/random.randint ordering preserved. If the order had drifted, Task 1 would have failed and blocked progression to Task 3.

- **T-01-10 (sph_sim.py shim contents):** Task 3 verify asserts `wc -l < 20` (actual: 13), `grep "from sphsim.cli.main import main"` matches (present at line 9), `grep -E '^def |^class |^DEFAULT_|^STRATEGIES'` returns empty (no top-level definitions remain). Plus a positive check that `python sph_sim.py --strategy naive` still renders human-readable output identically.

- **T-01-11 (public API consistency):** Task 3 verify imports all three names in one line — `from sphsim import SPHSimulator, Device, STRATEGIES` — which fails fast if any export is missing. Plus `__all__` enumeration ensures `from sphsim import *` only exposes the three sanctioned names.

- **T-01-12 (regression_check.py timeout):** Total runtime ~30-40s for 8 invocations × ~5s each. Well within the developer feedback budget; no timeout encountered.

- **T-01-SC (package installs):** N/A — Phase 1 stdlib-only, no installs.

## Known Stubs

None. The plan is the cutover — all stubs from Plan 02 (`sphsim/__init__.py` docstring-only placeholder, `sphsim/__main__.py` NotImplementedError, `sphsim/core/__init__.py` empty) have been REPLACED with wired implementations in this plan. No code path remains that throws `NotImplementedError` or returns placeholder data.

## Next Phase Readiness

- **Plan 01-05 (final hygiene + documentation update) is unblocked.** The package is now the sole source of truth. Plan 05's likely scope: update README.md to point at the new entry path, update PROJECT.md to reflect the new layout, ensure CLAUDE.md project conventions are documented, run a final lint pass (if any), and confirm `git diff` against monolith pre-cutover is exactly the expected set of changes (no accidental drift).

- **Phase 2 (REPL) is unblocked at the contract level.** `format_human` and `format_json` now take `args`-like objects and return strings (no print side-effects), so the REPL can build its own argparse-compatible args namespace and call `format_human(repl_args, res, K1, verbose=False)` directly. `SPHSimulator(...).run()` is the same callable contract.

- **Phase 3 (custom strategy loader) is unblocked at the public-API level.** `from sphsim import STRATEGIES` returns the mutable registry dict — the loader can do `STRATEGIES['user_custom'] = loaded_fn` after validating signature against `from sphsim.strategies import StrategyFn`. `from sphsim import SPHSimulator` provides the constructor the loader needs to test-run a user strategy.

- **Phase 5 (configurable environment) is unblocked at the config level.** `sphsim/config.py` is the single override point — Phase 5 will read user config files and patch `sphsim.config.DEFAULT_*` (or pass values directly via the SPHSimulator constructor) without touching simulator.py or strategies/.

- **`scripts/regression_check.py` remains the authoritative gate** for Plan 05 and for any future refactor. It now runs against the NEW thin-shim path (which dispatches to `sphsim.cli.main`) — exit 0 means the package faithfully reproduces v1.0. Any future change to simulator.py, strategies/, or cli/ that breaks fixture match will surface here.

- **No blockers.** Working tree is clean. All three task commits (`44513d3`, `097c6d6`, `789ab6f`) plus this SUMMARY commit will land cleanly on `worktree-agent-acec8a84` branch and merge to main without conflict (waves 1-3 already merged; only Wave 4 changes remain).

## Self-Check: PASSED

- `sphsim/core/simulator.py` — FOUND (150 LOC, 4 random.* call sites)
- `sphsim/cli/__init__.py` — FOUND (empty package marker)
- `sphsim/cli/args.py` — FOUND (57 LOC, verbatim docstring + parse_args)
- `sphsim/cli/output.py` — FOUND (64 LOC, format_json + format_human)
- `sphsim/cli/main.py` — FOUND (29 LOC, main orchestration)
- `sph_sim.py` — MODIFIED (13 LOC thin shim, from sphsim.cli.main import main)
- `sphsim/__init__.py` — MODIFIED (publiczne API: SPHSimulator, Device, STRATEGIES + __all__)
- `sphsim/__main__.py` — MODIFIED (NotImplementedError replaced with main() dispatch)
- `sphsim/core/__init__.py` — MODIFIED (re-exports SPHSimulator, Device, valuation, sph_stp)
- Commit `44513d3` (Task 1) — FOUND in `git log`
- Commit `097c6d6` (Task 2) — FOUND in `git log`
- Commit `789ab6f` (Task 3 cutover) — FOUND in `git log`
- `python3 scripts/regression_check.py` → exit 0 (8/8 PASS) post-cutover
- `python sph_sim.py --strategy naive --zeta 0.5 --seed 42 --json` → JSON dict-equal with fixture #1
- `python -m sphsim --strategy naive --zeta 0.5 --seed 42 --json` → JSON dict-equal with fixture #1
- `python -m sphsim --strategy threshold --max_phase 3 --json` → JSON dict-equal with fixture #2
- `python sph_sim.py --strategy naive` → human-readable output renders 62-char banner + IC table identically
- `from sphsim import SPHSimulator, Device, STRATEGIES` → resolves (publiczne API D-16)
- `grep -E '^def |^class |^DEFAULT_|^STRATEGIES' sph_sim.py` → empty (D-05 thin shim)
- `grep -E 'NotImplementedError|TODO' sphsim/__main__.py` → empty (placeholder replaced)
- `wc -l sph_sim.py` → 13 (≤ 20 thin-shim cap)
- `wc -l sphsim/core/simulator.py` → 150 (≤ 150 cap)
- `grep -c "random\." sphsim/core/simulator.py` → 4 (random.seed + 2× random.random + random.randint preserved)

All claimed artefacts, commits, and behavioral invariants verified on disk and in git history. CLI-04 satisfied on both entry paths.

---
*Phase: 01-refactoring-foundation*
*Completed: 2026-05-25*
