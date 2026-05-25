---
phase: 01-refactoring-foundation
plan: 02
subsystem: sphsim-package
tags: [refactor, package-skeleton, pure-functions, dataclass, stdlib, backwards-compat]

# Dependency graph
requires:
  - phase: 01-01
    provides: regression_check.py oracle + 8 baseline_v1 JSON fixtures (CLI-04 gate)
provides:
  - sphsim/ package skeleton (sphsim/__init__.py, __main__.py, config.py, core/__init__.py)
  - sphsim/config.py — 10 DEFAULT_* constants (single point of override for Phase 5)
  - sphsim/core/model.py — pure functions valuation(), sph_stp() (stdlib-only, no random.*)
  - sphsim/core/device.py — Device dataclass with phase_stats, record_*, net_profit
affects: [01-03, 01-04, 01-05, sphsim-package, backwards-compatibility]

# Tech tracking
tech-stack:
  added: []  # stdlib only — Python 3.7+ typing + dataclasses (D-07 constraint preserved)
  patterns:
    - "Verbatim extraction: identifiers, signatures, algorithm order copied 1:1 from monolith to preserve numerical equivalence (D-08, T-01-04, T-01-05)"
    - "Centralized config: 10 DEFAULT_* in sphsim/config.py is the only override seam for Phase 5 configurable environment (D-04)"
    - "Pure model module: core/model.py has zero side effects, zero random.* calls — safe to import from any layer (D-12)"
    - "YAGNI directory layout: only sphsim/core/ created — strategies/cli/agent/report/batch NOT stubbed (D-02)"
    - "Non-destructive refactor: monolith sph_sim.py untouched, sphsim/ exists parallel to it; regression check still exit 0"

key-files:
  created:
    - "sphsim/__init__.py — package marker with placeholder docstring (Plan 04 will add re-exports per D-16)"
    - "sphsim/__main__.py — `python -m sphsim` placeholder; raises NotImplementedError until Plan 04 wires CLI"
    - "sphsim/config.py — 10 DEFAULT_* constants (NU=250 int, NSUS=20, K0=100, K1=120, F=5, T=1000, KAPPA=0.25 float, ALPHA=1, PHI=[0.1,0.2,0.3,0.4,1.0], RHO=[0.5,0.5,0.7,1.5,3.0]) verbatim from sph_sim.py:39-48"
    - "sphsim/core/__init__.py — empty package marker (Plan 04 will re-export SPHSimulator + Device)"
    - "sphsim/core/model.py — valuation(u,K0,K1) + sph_stp(u,s,nSUS,K0,K1) copied verbatim from sph_sim.py:53-79; 34 LOC; stdlib only (`from typing import Tuple`)"
    - "sphsim/core/device.py — @dataclass Device with 10 fields, __post_init__(phase_stats={}), record_commit/record_delivery/record_failure, net_profit property; copied verbatim from sph_sim.py:84-118; 43 LOC; stdlib only (`from dataclasses import dataclass`)"
  modified: []  # sph_sim.py intentionally NOT touched (CLI-04 invariant: monolith still authoritative)

key-decisions:
  - "sphsim/__init__.py kept as a docstring-only placeholder; full re-exports (SPHSimulator, Device, STRATEGIES) deferred to Plan 04 per D-16 to avoid ImportError before those modules exist"
  - "sphsim/__main__.py raises NotImplementedError instead of silently no-op'ing — fails loud if accidentally invoked before Plan 04"
  - "`from typing import Tuple` kept in model.py even though no return annotations are emitted (verbatim copy from v1.0 has no `-> Tuple[int,int]`); preserved per plan acceptance criterion 'tylko typing' and to mark the module as type-ready for future annotation work without churning imports"
  - "Polish file-level comments added at top of each new module (`# Funkcje modelu — pure ...`, `# Device — autonomiczne urządzenie ...`, `# Parametry domyślne (z dokumentu PROMPT_DLA_AGENTA.txt)`) to satisfy PROJECT.md constraint 'Język: polski w komentarzach'"

patterns-established:
  - "Three-step verbatim extraction rhythm per file: (1) read monolith block, (2) write target file with verbatim body + Polish header comment, (3) run inline `python -c` behavior asserts AND `python3 scripts/regression_check.py` — both must pass before commit"
  - "Plan 01-02 confirms the snapshot oracle from Plan 01-01 is the correct gate for subsequent plans: any algorithmic drift (e.g., reordering sph_stp candidates list, changing phase_stats setdefault schema) would fail regression_check at commit time"

requirements-completed: [CLI-04]

# Metrics
duration: 3m
completed: 2026-05-25
---

# Phase 01 Plan 02: sphsim/ Package Skeleton + Core Pure Modules Summary

**Stand up the `sphsim/` Python package skeleton and extract the three side-effect-free responsibilities from v1.0 monolith — 10 DEFAULT_* constants (`sphsim/config.py`), pure model functions `valuation`/`sph_stp` (`sphsim/core/model.py`), and `Device` dataclass with `phase_stats` + `record_*` + `net_profit` (`sphsim/core/device.py`) — non-destructively: `sph_sim.py` untouched, all 8 baseline_v1 fixtures still match (regression_check exit 0).**

## Performance

- **Duration:** 3m (2m 38s)
- **Started:** 2026-05-25T15:17:22Z
- **Completed:** 2026-05-25T15:20:00Z
- **Tasks:** 2
- **Files modified:** 6 (6 created, 0 modified; sph_sim.py intentionally untouched per CLI-04 invariant)

## Accomplishments
- Established the `sphsim/` package shape that plans 03/04 and phases 4–7 will extend, **without** creating any of the YAGNI stub directories (`strategies/`, `cli/`, `agent/`, `report/`, `batch/`) that D-02 explicitly forbids in this plan — only the two directories that hold code emitted **in this plan** exist on disk.
- Centralized all 10 environment defaults (NU, NSUS, K0, K1, F, T, KAPPA, ALPHA, PHI, RHO) in `sphsim/config.py` as the single override seam for Phase 5, with byte-for-byte type fidelity (NU=250 stays `int`, KAPPA=0.25 stays `float`, PHI is a 5-element list of floats including the trailing `1.0`).
- Extracted both pure functions `valuation(u, K0, K1)` and `sph_stp(u, s, nSUS, K0, K1)` to `sphsim/core/model.py` with the algorithm's candidate list order **preserved verbatim** — this is the key threat-model mitigation (T-01-05): any reorder would change tie-breaking in `if p > best_P` and silently drift a fixture. Behavior asserts in the verification block include both the `valuation(110, 100, float('inf'))` corner case and the `sph_stp(0, 0, 20, 100, 120) == (0, 0)` empty-window case.
- Extracted `Device` dataclass to `sphsim/core/device.py` with all 10 fields, both initialization defaults, `__post_init__(phase_stats={})`, three `record_*` methods using identical `setdefault` schema (`{commits, deliveries, failures, earnings, costs}`), and the `net_profit` property — verified by 8 inline asserts covering each behavior bullet in the plan's `<behavior>` block.
- Confirmed plan 01-01's regression oracle works as the gate it was designed to be: `python3 scripts/regression_check.py` returns exit 0 both after Task 1 and after Task 2, proving the monolith still produces byte-identical JSON output for all 8 baseline_v1 invocations.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create sphsim/ skeleton + config.py with 10 DEFAULT_* constants** — `848ac2e` (feat)
2. **Task 2: Extract valuation, sph_stp, and Device dataclass to sphsim/core/** — `9530042` (feat)

_Plan metadata commit follows this SUMMARY._

## Files Created/Modified
- `sphsim/__init__.py` — Package marker. Polish docstring `"""Pakiet SPH Symulator — refactor v1.0 monolitu sph_sim.py."""` + comment noting Plan 04 will add re-exports per D-16. No top-level imports (would break before Plan 03 emits `strategies/`).
- `sphsim/__main__.py` — `python -m sphsim` placeholder. `raise NotImplementedError("Entry point będzie wpięty w Planie 04")` is intentional — fails loud if someone tries to use it prematurely, instead of silently no-op'ing.
- `sphsim/config.py` — 10 DEFAULT_* constants. Header comment `# Parametry domyślne (z dokumentu PROMPT_DLA_AGENTA.txt)` matches v1.0 monolith convention exactly. Types preserved (int vs float distinction is meaningful for downstream type coercion).
- `sphsim/core/__init__.py` — Empty package marker with a one-line comment noting Plan 04's responsibility for re-exports.
- `sphsim/core/model.py` — 34 LOC. `valuation()` and `sph_stp()` copied verbatim from sph_sim.py:53–79 including the inner `def P_of_x(x)`, the Polish docstring `"""Zwraca (z*, y*) max-izujące P = g(u-x)+x, x=z-y."""`, and the `candidates = [x_min, x_max, K0 - u]` ordering that tie-breaking depends on.
- `sphsim/core/device.py` — 43 LOC. `@dataclass Device` copied verbatim from sph_sim.py:84–118 with all 10 fields, `__post_init__`, three `record_*` methods, and `net_profit` property.

## Decisions Made
- **Polish header comments retained on every new module** (`# Funkcje modelu — pure ...`, `# Device — autonomiczne urządzenie ...`, `# Parametry domyślne ...`) — satisfies PROJECT.md constraint "Język: polski w komentarzach" and gives the next executor / reader a one-line domain anchor at the top of each file. No code-level comments were added beyond what existed in v1.0.
- **`from typing import Tuple` retained in `model.py`** even though the verbatim function signatures from v1.0 carry no return-type annotation. The plan's acceptance criterion explicitly enumerates `typing` as the allowed import, and the import marks the module as ready for future annotation work without churning the import block on the next plan. This is a deliberate non-removal, not an oversight.
- **`sphsim/__main__.py` raises rather than silently no-ops** — discoverability is more valuable than apparent forward-compat at this stage. If someone runs `python -m sphsim` between Plan 02 and Plan 04, they get an explicit "wait, this is not wired yet" instead of a silent exit-0.
- **No re-exports in `sphsim/__init__.py` yet** (per D-16, full export list lives in Plan 04 after `simulator.py` and `strategies/` exist). Adding `from sphsim.core.device import Device` here today would work, but adding it incrementally as each module lands fragments the publication surface across plans; doing it all at once in Plan 04 keeps the public API decision in one commit.

## Deviations from Plan

None — plan executed exactly as written. All 6 files created with verbatim contents from sph_sim.py; no auto-fixes (Rules 1–3) were needed; no architectural questions (Rule 4) arose. The plan was unambiguous and the monolith was clean. `python3` vs `python` shell choice was already documented as a host-specific adaptation in Plan 01-01 SUMMARY (this host has no `python` shim, only `python3`) and the new modules don't shell out, so they inherit no portability concern.

## Issues Encountered

None during planned work. Both tasks compiled and verified on the first run:
- Task 1: All 10 constants matched v1.0 by type and value; `regression_check.py` exit 0; `git diff sph_sim.py` empty.
- Task 2: All 8 behavior asserts (5 valuation cases, 2 sph_stp cases, 5 Device cases) passed on the first run; `regression_check.py` exit 0; `git diff sph_sim.py` still empty.

The verbatim-extraction discipline (read v1.0 source block → write target file → run behavior asserts AND regression check → commit) leaves zero ambiguity at each step. The plan author front-loaded the line-range references (sph_sim.py:39-48, :53-79, :84-118) which made the extraction mechanical.

## User Setup Required

None — Phase 1 is stdlib-only (D-07). No new dependencies, no environment variables, no external services. The new `sphsim/` package imports only `typing.Tuple` and `dataclasses.dataclass`, both stdlib.

## Threat Flags

None. No new trust boundaries introduced — `sphsim/core/model.py` and `sphsim/core/device.py` are pure logic with stdlib-only imports, no network/file/subprocess access, no auth surface. The mitigations from the plan's `<threat_model>` were honored:
- **T-01-04 (config tampering):** Every constant verified against v1.0 by type + value in Task 1 verify command — line `assert c.DEFAULT_NU==250 and ... and c.DEFAULT_RHO==[0.5,0.5,0.7,1.5,3.0]`. Type fidelity (int vs float) preserved.
- **T-01-05 (algorithm tampering):** `sph_stp` candidate list `[x_min, x_max, K0 - u]` (and conditional `K1 - u` append) order preserved verbatim. `regression_check.py` passes — proves no tie-breaking drift across all 8 baseline invocations.

## Next Phase Readiness
- **Plan 01-03 (strategies extraction) unblocked.** `sphsim/config.py` exposes `DEFAULT_K0` for `strategies/incentive.py` to import. `sphsim/core/device.py` exposes the `Device` dataclass that strategy functions take as the first positional arg (`dev`).
- **Plan 01-04 (simulator + CLI wiring) waits on Plan 01-03**, then will: (a) emit `sphsim/core/simulator.py` consuming `valuation`, `sph_stp`, `Device`, `STRATEGIES`; (b) emit `sphsim/cli/{args,main,output}.py`; (c) replace `__init__.py` placeholder with the D-16 re-exports; (d) replace `__main__.py` `NotImplementedError` with `from sphsim.cli.main import main; main()`; (e) finally collapse `sph_sim.py` to a thin shim that delegates to `sphsim.cli.main`.
- **`scripts/regression_check.py` is now the authoritative gate** for every subsequent plan in Phase 1. Each plan 03/04/05 must end with `python3 scripts/regression_check.py` exit 0 — exit 1 or 2 blocks the commit. This invariant survived Plan 02 unchanged (still exit 0 after both task commits).

## Self-Check: PASSED

- `sphsim/__init__.py` — FOUND
- `sphsim/__main__.py` — FOUND
- `sphsim/config.py` — FOUND
- `sphsim/core/__init__.py` — FOUND
- `sphsim/core/model.py` — FOUND
- `sphsim/core/device.py` — FOUND
- Commit `848ac2e` (Task 1) — FOUND in `git log`
- Commit `9530042` (Task 2) — FOUND in `git log`
- `python3 scripts/regression_check.py` → exit 0 (8/8 PASS)
- `git diff sph_sim.py` → empty (monolith untouched)
- All 10 DEFAULT_* values + types match v1.0 (verified inline in Task 1 verify)
- All 8 behavior asserts pass (verified inline in Task 2 verify)
- `wc -l sphsim/core/model.py` = 34 (under ≤80 plan limit, well under ≤150 ROADMAP limit)
- `wc -l sphsim/core/device.py` = 43 (under ≤80 plan limit, well under ≤150 ROADMAP limit)
- `grep -E '^import|^from' sphsim/core/model.py` → only `from typing import Tuple` (stdlib)
- `grep -E '^import|^from' sphsim/core/device.py` → only `from dataclasses import dataclass` (stdlib)

All claimed artefacts and commits verified on disk and in git history.

---
*Phase: 01-refactoring-foundation*
*Completed: 2026-05-25*
