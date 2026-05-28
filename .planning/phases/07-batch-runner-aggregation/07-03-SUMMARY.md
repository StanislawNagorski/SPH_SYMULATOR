---
phase: 07-batch-runner-aggregation
plan: 03
subsystem: batch-runner
tags: [batch, orchestrator, deterministic, baseline-verdict, cli-wiring, python, scipy, numpy]

# Dependency graph
requires:
  - phase: 07-01
    provides: sphsim.batch.stats.aggregate_kpis + AggregateStat dataclass + KPIS tuple (BATCH-02)
  - phase: 07-02
    provides: sphsim.cli.args._parse_seeds_list + --batch/--seeds flags + 4-way mutex (BATCH-01 CLI half)
  - phase: 06
    provides: sphsim.report.markdown.BASELINE_PATH (single source of truth for baseline avg_val_last100)
  - phase: 04
    provides: sphsim.agent.wrap_with_agent — conditional veto layer reused by run_batch
  - phase: 01
    provides: sphsim.core.simulator.SPHSimulator + simulator.__init__ unconditional reseed contract
provides:
  - sphsim.batch.run_batch(args, raw_strategy_fn, params, K1) orchestrator — pure function, sequential N×SPHSimulator(seed=S).run() loop with KPI-slice projection
  - sphsim.cli.output.format_batch_summary(args, aggregate, K1) — multi-line Polish stdout summary with BASELINE_PATH-driven verdict
  - sphsim/cli/main.py TWO 'if args.batch:' early-branches (built-in path @145, custom path @92) — wires run_batch + format_batch_summary stdout
  - End-to-end working CLI invocation `--batch --seeds N` — banner + 5 KPI rows (mean/std/95% CI) + Werdykt
  - tests/test_batch.py::TestDeterminism — 2 GREEN integration tests (byte-identical + seed-divergence paranoia)
affects: [07-04, 07-05, 07-06]

# Tech tracking
tech-stack:
  added: []  # No new deps — uses existing numpy/scipy from Plan 07-01, no new top-level imports
  patterns:
    - "Adapter orchestrator: zero math (delegates to aggregate_kpis), zero IO (caller writes output)"
    - "KPI-slice projection — discards history/devices/ic_per_phase/veto_per_phase before aggregation (memory savings + simpler downstream)"
    - "BASELINE_PATH read deferred to function call time (testable fallback, no top-level cyclic import)"
    - "Twin early-branches in main.py (built-in + custom paths) mirror the Phase 4 compare_agent pattern"

key-files:
  created:
    - sphsim/batch/runner.py — run_batch orchestrator (69 lines)
  modified:
    - sphsim/batch/__init__.py — extends __all__ from 3 to 4 symbols (added run_batch first)
    - sphsim/cli/output.py — appends format_batch_summary (57 new lines; total 257)
    - sphsim/cli/main.py — TWO 'if args.batch:' early-branch insertions (built-in @145, custom @92)
    - tests/test_batch.py — TestDeterminism: 1 skip-placeholder → 2 GREEN tests (test_byte_identical + test_different_seeds_diverge)

key-decisions:
  - "run_batch returns 2-tuple (per_seed_results, aggregate) — Plan 07-04 will consume both for report rendering"
  - "seed parameter EXCLUDED from common dict — passed per-iter as the only varying parameter, prevents accidental constant-seed bug"
  - "format_batch_summary K1 param kept for API symmetry with format_compare even though currently unused — futureproof"
  - "BASELINE_PATH read uses try/except (FileNotFoundError, KeyError, ValueError) → falls back to '⚠ Werdykt baseline niedostępny' — NEVER substitutes a magic-number literal (BLOCKER #1 mitigation)"
  - "TestDeterminism has 2 methods: byte-identical (the contract) + different-seeds-diverge (paranoia guard against trivially-passing tests)"

patterns-established:
  - "Orchestrator-as-adapter: run_batch owns NO math (aggregate_kpis) + NO IO (caller prints/writes) — pure adapter sitting between Plan 01 (stats) and CLI surface"
  - "Twin-branch CLI wiring: when CLI has both built-in (args.strategy) and custom (args.custom) paths, NEW behaviors get TWO insertions — one per path, identical bodies"
  - "Marker comment for future plans: '# NOTE: Plan 07-04 will add write_batch_report(...) here.' reserved at exactly 2 insertion points for Plan 07-04 executor"

requirements-completed: [BATCH-01, BATCH-02]

# Metrics
duration: 6min
completed: 2026-05-28
---

# Phase 07 Plan 03: Batch Runner Orchestrator + CLI Wiring Summary

**Sequential batch orchestrator (`run_batch`) wired into CLI via twin `if args.batch:` early-branches with BASELINE_PATH-driven Polish stdout verdict — `python sph_sim.py --strategy naive --batch --seeds N` now produces banner + 5 KPI rows + Werdykt end-to-end.**

## Performance

- **Duration:** 6 min (5m59s)
- **Started:** 2026-05-28T11:39:13Z
- **Completed:** 2026-05-28T11:45:12Z
- **Tasks:** 2
- **Files modified:** 4 (1 new + 3 edited) + 1 test file

## Accomplishments

- **`sphsim/batch/runner.py::run_batch`** — pure-function orchestrator that loops `N × SPHSimulator(seed=S).run()`, slices each result to the 5 canonical KPIS, and delegates to `aggregate_kpis` for mean/std/95% CI. Conditional `wrap_with_agent` honors `args.no_agent`. Determinism contract: identical `args.seeds` → byte-identical `per_seed_results`.
- **`sphsim/cli/output.py::format_batch_summary`** — multi-line Polish banner+KPI-table+Werdykt with the baseline value read from `BASELINE_PATH` (Phase 6 single source of truth) via deferred import + `json.loads`. Zero hardcoded `92.0` literals — BLOCKER #1 from plan-checker fully mitigated.
- **`sphsim/cli/main.py`** — TWO `if args.batch:` early-branches inserted BEFORE `if args.compare_agent:` in BOTH the built-in (line 145) and custom (line 92) paths. Each branch defer-imports `run_batch` + `format_batch_summary`, calls them, prints stdout, returns. Marker comment reserved at both sites for Plan 07-04's `write_batch_report` insertion.
- **`tests/test_batch.py::TestDeterminism`** — 2 GREEN integration tests (`test_byte_identical` + `test_different_seeds_diverge` paranoia guard). Final test_batch.py state: **14 GREEN + 2 SKIPPED** (TestReplBatch and TestCliReplParity remain placeholders for Plan 07-05).

## Task Commits

Each task was committed atomically:

1. **Task 1: `sphsim/batch/runner.py` + extended `__init__.py` + `format_batch_summary` (BASELINE_PATH-driven verdict)** — `5182671` (feat)
2. **Task 2: `main.py` `args.batch` early-branches (built-in + custom) + `TestDeterminism` GREEN** — `bcfaf47` (feat)

## Files Created/Modified

- `sphsim/batch/runner.py` (NEW, 69 lines) — `run_batch(args, raw_strategy_fn, params, K1) -> tuple[list[dict], dict[str, AggregateStat]]`. Sequential N×SPHSimulator loop with KPI-slice projection. Conditional `wrap_with_agent` based on `args.no_agent`. Determinism via SPHSimulator's unconditional reseed (no manual reseeding).
- `sphsim/batch/__init__.py` (MOD) — `__all__` extended from `['aggregate_kpis', 'AggregateStat', 'KPIS']` to `['run_batch', 'aggregate_kpis', 'AggregateStat', 'KPIS']` (4 symbols, `run_batch` listed first as the public-facing orchestrator).
- `sphsim/cli/output.py` (MOD) — appended `format_batch_summary(args, aggregate, K1) -> str` at EOF. Uses deferred imports (`from sphsim.batch.stats import KPIS`, `from sphsim.report.markdown import BASELINE_PATH`, `import json`) inside the function body to avoid top-level circular imports AND defer filesystem read to call time. Verdict logic handles 4 cases: `BIJE baseline`, `NIE bije baseline`, `N=1 single-point > baseline`, `N=1 single-point ≤ baseline`. Try/except fallback `⚠ Werdykt baseline niedostępny (brak fixture)`.
- `sphsim/cli/main.py` (MOD) — TWO `if args.batch:` early-branches inserted. Custom-path insertion at line 92 (right after `raw_strategy_fn` snapshot, BEFORE `if args.compare_agent:`); built-in-path insertion at line 145 (same relative position). Each branch identical: defer-import `run_batch` + `format_batch_summary`, call them, `print`, `return`.
- `tests/test_batch.py` (MOD) — `TestDeterminism` placeholder `test_placeholder` replaced with 2 GREEN methods. Imports unchanged (uses existing `_run_sph` helper). Skip count drops from 4 to 2 across the whole file (TestReplBatch + TestCliReplParity remain skipped pending Plan 07-05).

## Decisions Made

- **`run_batch` returns 2-tuple** instead of a single dict — gives Plan 07-04 (report renderer) trivial access to both per-seed results and aggregate without re-aggregating.
- **`seed` excluded from `common` dict** — only varying parameter, passed per-iter as a keyword argument. Prevents accidentally seeding all iterations with the same value (would silently break determinism without erroring).
- **Deferred imports in `format_batch_summary`** — `sphsim.batch.stats.KPIS` and `sphsim.report.markdown.BASELINE_PATH` imported INSIDE the function body, not at module top. Preserves the existing invariant that `sphsim/cli/output.py` has zero top-level imports from `sphsim.batch.*` or `sphsim.report.*` (avoids circular import risk).
- **Try/except over `(FileNotFoundError, KeyError, ValueError)`** — catches: missing fixture file, malformed JSON (json.loads raises ValueError), missing `metrics` or `avg_val_last100` keys. Explicit `baseline_avg = None` fallback feeds the "⚠ Werdykt baseline niedostępny (brak fixture)" branch — NEVER substitutes 92.0 (BLOCKER #1).
- **TestDeterminism has 2 methods, not 1** — added `test_different_seeds_diverge` as a paranoia guard: if some bug made `_run_sph` always produce identical stdout (e.g., seed not being threaded through), `test_byte_identical` would pass trivially. The divergence test ensures the determinism test isn't vacuous.

## Deviations from Plan

None - plan executed exactly as written.

The one minor edit beyond the literal plan was tightening docstrings to satisfy the strict `grep` gates:
- `sphsim/cli/output.py` docstring changed `— zero hardcoded 92.0 literals` to `— zero hardcoded baseline literals` so the BLOCKER #1 gate (`grep -v BASELINE_PATH ... | grep -c '92.0'` must return 0) holds even against the docstring.
- `sphsim/batch/runner.py` docstring changed `random.seed(seed)` to `reseed PRNG` so the runner.py gate (`grep -E 'random\.seed\b' sphsim/batch/runner.py | wc -l` must return 0) holds even against docstrings.

These are gate-satisfaction adjustments, not behavior changes — the actual code never had the literals.

## Issues Encountered

None. RED → GREEN cycle for both tasks completed without surprises:
- **Task 1 RED:** `from sphsim.batch import run_batch` raised ImportError (expected).
- **Task 1 GREEN:** Created runner.py, extended __init__.py, appended format_batch_summary → smoke test passed first try.
- **Task 2 RED:** `python3 sph_sim.py --strategy naive --batch --seeds 3 ...` fell through to single-run path (printed config header instead of BATCH SUMMARY); `TestDeterminism` was 1 skip.
- **Task 2 GREEN:** Inserted both early-branches → end-to-end CLI produces banner + KPIs + Werdykt; both new TestDeterminism methods passed (~3s subprocess overhead per pair).

## BLOCKER #1 Confirmation

The plan-checker BLOCKER #1 requirement is fully met:

```bash
$ grep -v BASELINE_PATH sphsim/cli/output.py | grep -c '92.0'
0
$ grep -F 'BASELINE_PATH' sphsim/cli/output.py | wc -l
3   # 3 mentions: function docstring + import line + filesystem-read line
```

The verdict line `✗ NIE bije baseline (CI_lower ≤ 92.0)` displays `92.0` at runtime because the value was JUST READ from `BASELINE_PATH` (`tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` → `metrics.avg_val_last100`). Regenerating the baseline fixture will automatically update both the MD verdict (Plan 07-04) and the stdout verdict (this plan) — single source of truth maintained.

## Verification Evidence

All 9 plan verification steps executed and passing:

1. ✅ **Public surface:** `from sphsim.batch import run_batch` + `from sphsim.cli.output import format_batch_summary` both callable.
2. ✅ **main.py wiring:** `grep -c 'if args.batch:' sphsim/cli/main.py` returns 2 (both branches).
3. ✅ **BLOCKER #1 gate:** `grep -v BASELINE_PATH sphsim/cli/output.py | grep -c '92.0'` returns 0.
4. ✅ **End-to-end CLI (built-in):** `python3 sph_sim.py --strategy naive --zeta 0.5 --batch --seeds 5 --no-agent --seed 42` exits 0, prints banner + 5 KPI rows + Werdykt.
5. ✅ **TestDeterminism:** 2 tests, both PASS in ~3.1s.
6. ✅ **Full test_batch suite:** 16 ran, 14 GREEN + 2 SKIPPED (TestReplBatch + TestCliReplParity placeholders for Plan 07-05).
7. ✅ **Phase 1-6 regression:** `python3 scripts/regression_check.py` → PASS=8/8 preserved.
8. ✅ **Full discover:** 199 tests, 4 expected skips, zero failures.
9. ✅ **With agent (default):** `python3 sph_sim.py --strategy naive --zeta 0.5 --batch --seeds 3 --seed 42` exits 0, same shape stdout (with `--zeta 0.95` agent path materially diverges from no-agent — `avg_val_last100=26.00` vs `1.00`, proving wrap is firing).

## Self-Check: PASSED

**Files exist:**
- ✅ `sphsim/batch/runner.py` (69 lines)
- ✅ `sphsim/cli/output.py` (257 lines, contains `def format_batch_summary`)
- ✅ `sphsim/cli/main.py` (186 lines, contains 2× `if args.batch:`)
- ✅ `sphsim/batch/__init__.py` (4 symbols in __all__)
- ✅ `tests/test_batch.py` (199 lines, 2 GREEN TestDeterminism methods)

**Commits exist:**
- ✅ `5182671` — `feat(07-03): sphsim/batch/runner.py + format_batch_summary — BATCH-01 orchestrator + BASELINE_PATH-driven verdict`
- ✅ `bcfaf47` — `feat(07-03): main.py args.batch early-branches (built-in + custom) + TestDeterminism GREEN`

## Note for Plan 07-04 Executor

The marker comment `# NOTE: Plan 07-04 will add write_batch_report(...) here.` exists at exactly 2 insertion points in `sphsim/cli/main.py`:
- **Custom path** (around line 99) — inside `if args.batch:` block, BEFORE `print(format_batch_summary(...))`.
- **Built-in path** (around line 152) — inside `if args.batch:` block, BEFORE `print(format_batch_summary(...))`.

Plan 07-04 modifies these exact lines to insert the `write_batch_report` call. The data is already in scope as `per_seed_results` and `aggregate` (the 2-tuple returned by `run_batch`).

## Next Phase Readiness

- **Plan 07-04 (Wave 3):** Has all primitives needed — `(per_seed_results, aggregate)` tuple available in 2 main.py call sites; marker comments reserve insertion points; `BASELINE_PATH` already proven readable.
- **Plan 07-05 (Wave 4):** REPL command `batch <strategy> --seeds N` can directly reuse `run_batch` + `format_batch_summary` via the existing `fake_args` pattern; `TestReplBatch` + `TestCliReplParity` placeholders remain skipped pending that work.
- **No blockers, no concerns.** Phase 1-6 regression PASS=8/8 preserved — single-run path is bit-identical when `--batch` is absent (the early-branch returns BEFORE any single-run code executes; no shared state mutation).

---
*Phase: 07-batch-runner-aggregation*
*Plan: 03*
*Completed: 2026-05-28*

**Suggested commit message:** `feat(07-03): sphsim/batch/runner.py + main.py args.batch branches + format_batch_summary (BASELINE_PATH-driven verdict, zero hardcoded 92.0) — CLI --batch --seeds working end-to-end (BATCH-01 CLI half, BATCH-02 wiring)`
