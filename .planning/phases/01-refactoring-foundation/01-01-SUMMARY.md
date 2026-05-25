---
phase: 01-refactoring-foundation
plan: 01
subsystem: testing
tags: [regression, fixtures, snapshot, stdlib, subprocess, baseline]

# Dependency graph
requires:
  - phase: bootstrap
    provides: sph_sim.py v1.0 monolith (433 lines) — authoritative pre-refactor source
provides:
  - 8 committed JSON fixtures in tests/fixtures/baseline_v1/ (authoritative oracle for CLI-04)
  - scripts/generate_baseline.py (deterministic fixture regenerator, stdlib only)
  - scripts/regression_check.py (8-invocation diff runner used by plans 02-05, exit 0/1/2 semantics)
  - tests/fixtures/baseline_v1/MANIFEST.txt (peer-review slug → command map)
affects: [01-02, 01-03, 01-04, 01-05, refactoring, sphsim-package, backwards-compatibility]

# Tech tracking
tech-stack:
  added: []  # stdlib only (subprocess, json, pathlib, argparse) — no new packages by D-07 constraint
  patterns:
    - "Snapshot-fixture regression: pure-stdlib script + committed JSON oracle (D-08)"
    - "Single source of truth INVOCATIONS list: regression_check imports from generate_baseline (DRY)"
    - "Deterministic JSON dumps: sort_keys=True + indent=2 + trailing newline → bit-identical regen, clean git diffs"
    - "Exit-code semantics: 0=pass, 1=regression, 2=runtime-error (subprocess / I/O / parse)"

key-files:
  created:
    - "scripts/generate_baseline.py — regenerates fixtures by running 8 D-09 invocations on sph_sim.py"
    - "scripts/regression_check.py — deep-diffs current --json output vs committed fixtures (exact equality)"
    - "tests/fixtures/baseline_v1/01-naive-zeta-0.5.json — fixture #1"
    - "tests/fixtures/baseline_v1/02-threshold-max-phase-3.json — fixture #2"
    - "tests/fixtures/baseline_v1/03-phase-prob-default.json — fixture #3"
    - "tests/fixtures/baseline_v1/04-incentive-expected-P-100.json — fixture #4"
    - "tests/fixtures/baseline_v1/05-adaptive-s-target-10.json — fixture #5"
    - "tests/fixtures/baseline_v1/06-naive-zeta-0.4-custom-env.json — fixture #6"
    - "tests/fixtures/baseline_v1/07-phase-prob-custom-kappa-alpha.json — fixture #7"
    - "tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json — fixture #8, avg_val_last100=92.0 (PROJECT.md baseline)"
    - "tests/fixtures/baseline_v1/MANIFEST.txt — slug → human-readable command (8 entries)"
    - ".gitignore — __pycache__/ + standard OS/editor artefakty"
  modified: []  # sph_sim.py intentionally NOT touched

key-decisions:
  - "Slug convention: zero-padded index + dash-separated params (01-naive-zeta-0.5 ... 08-naive-zeta-0.75-baseline)"
  - "Fixtures pretty-printed (indent=2) and sort_keys=True for deterministic git diffs"
  - "Exact-equality float comparison in regression_check (no math.isclose) — fixtures and current run share interpreter and seed; any drift is a real regression"
  - "regression_check.py imports INVOCATIONS from generate_baseline.py (DRY single source of truth)"

patterns-established:
  - "Snapshot oracle for backwards-compatibility refactors: stdlib subprocess + committed JSON + exact-equality diff (no pytest, no float tolerance, no extra deps)"
  - "Phase 1 plans 02–05 invoke `python3 scripts/regression_check.py` as the CLI-04 gate after every refactor step; exit != 0 blocks merge"

requirements-completed: [CLI-04]

# Metrics
duration: 4m
completed: 2026-05-25
---

# Phase 01 Plan 01: Baseline Fixtures + Regression Oracle Summary

**8-invocation JSON snapshot of pre-refactor sph_sim.py v1.0 plus stdlib-only deep-diff regression runner (`scripts/regression_check.py`) that returns exit 0 on the current monolith — authoritative CLI-04 oracle for plans 02–05.**

## Performance

- **Duration:** 4m (3m 36s)
- **Started:** 2026-05-25T15:10:09Z
- **Completed:** 2026-05-25T15:13:45Z
- **Tasks:** 2
- **Files modified:** 12 (12 created, 0 modified; sph_sim.py intentionally untouched)

## Accomplishments
- Captured authoritative v1.0 baseline BEFORE any refactor (D-11 ordering invariant satisfied — fixtures encode pre-refactor truth and will catch any drift introduced by plans 02–05).
- Confirmed numerical baseline from PROJECT.md / Raport.pdf: fixture `08-naive-zeta-0.75-baseline.json` reports `avg_val_last100 = 92.0`, exactly the `naive --zeta 0.75` baseline cited in the milestone spec.
- Built a reusable, stdlib-only diff runner with three-tier exit codes (0 pass / 1 regression / 2 runtime error) that plans 02–05 can wire into their own verification blocks without adding pytest, math.isclose tolerances, or any new dependency.
- Established the DRY invariant: `INVOCATIONS` lives in one place (`generate_baseline.py`) and is imported by `regression_check.py` — if anyone edits the 8 D-09 invocations the change is visible in a single file in `git diff`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create generate_baseline.py + generate 8 fixtures** — `5652a64` (test)
2. **Task 2: Create regression_check.py + confirm exit 0 on pre-refactor monolith** — `de55865` (test)

_Plan metadata commit follows this SUMMARY._

## Files Created/Modified
- `scripts/generate_baseline.py` — Deterministic fixture regenerator. Runs the 8 D-09 invocations against `sph_sim.py`, parses `--json` stdout, writes `<slug>.json` with `sort_keys=True, indent=2`, and writes `MANIFEST.txt`. Stdlib only.
- `scripts/regression_check.py` — Re-runs the same 8 invocations and deep-diffs each output against the committed fixture. Imports `INVOCATIONS` from `generate_baseline.py` (DRY). Supports `--verbose` for per-invocation OK/FAIL lines. Exit 0/1/2 semantics.
- `tests/fixtures/baseline_v1/01-naive-zeta-0.5.json` through `08-naive-zeta-0.75-baseline.json` — Eight authoritative v1.0 snapshots, `--seed 42 --json`.
- `tests/fixtures/baseline_v1/MANIFEST.txt` — One line per fixture: `<slug>.json | <full python sph_sim.py command>` for peer review.
- `.gitignore` — Excludes `__pycache__/` (emitted by the `regression_check.py → generate_baseline.py` cross-module import) plus standard OS/editor artefacts.

## Decisions Made
- **Slug convention** chosen by Claude (D-83 discretion): zero-padded index + dash-separated descriptive params, matching the `<files>` list in PLAN.md verbatim so the verification block could `ls` for exact 10 artefacts without ambiguity.
- **Trailing newline + LF + `sort_keys=True`** in `json.dumps` so 2× regen produces bit-identical bytes (confirmed via `shasum` comparison across two runs).
- **Exact equality (no `math.isclose`)** in `deep_diff` — fixtures and current run share interpreter, seed, and code path; any float drift is a real regress, never measurement noise. This is the harshest possible CLI-04 gate, which is what plans 02–05 need.
- **`INVOCATIONS` lives in `generate_baseline.py` only**, imported by `regression_check.py` via `sys.path.insert(0, ...)` + `from generate_baseline import INVOCATIONS`. Avoids two-list drift, satisfies D-13/D-14-style DRY discipline applied to scripts.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Added `.gitignore` to suppress `__pycache__/` from cross-module import**
- **Found during:** Task 2 (running `regression_check.py` post-implementation)
- **Issue:** `regression_check.py` imports `INVOCATIONS` from `generate_baseline.py` (DRY requirement in PLAN.md task action). The first invocation creates `scripts/__pycache__/` which appears as untracked in `git status` — the executor protocol forbids leaving generated runtime output untracked, and committing the bytecode cache directory would be wrong.
- **Fix:** Added `.gitignore` covering `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`, plus standard OS (`.DS_Store`, `Thumbs.db`) and editor (`*.swp`, `*.swo`) artefacts. No `.gitignore` existed in the repo previously.
- **Files modified:** `.gitignore` (created)
- **Verification:** `git status --short` clean after both `generate_baseline.py` and `regression_check.py` runs.
- **Committed in:** `de55865` (Task 2 commit — directly caused by Task 2's import pattern)

**2. [Adaptation] Used `python3` instead of `python` for runtime invocations**
- **Found during:** Task 1 (first `python scripts/generate_baseline.py` call)
- **Issue:** No `python` shim on this macOS host (`/usr/bin/python` does not exist by default on darwin 25). Only `python3` (Homebrew, Python 3.14.3) is on PATH. The PLAN.md verification commands and acceptance criteria use `python ...` in user-facing examples.
- **Fix:** Used `python3` directly in all execution / verification commands. **Inside the scripts themselves** the subprocess invocations use `sys.executable` (the running interpreter, whichever it is), so the scripts themselves are completely interpreter-agnostic — users running `python scripts/...` on a host with a `python` shim will get identical behaviour. No code change needed; only the shell commands used during this plan's verification differ from the literal text in PLAN.md.
- **Files modified:** None (verification-time only)
- **Verification:** `python3 scripts/generate_baseline.py` and `python3 scripts/regression_check.py` both succeed; `sys.executable` ensures subprocess uses the same interpreter.
- **Committed in:** N/A (no code change)

---

**Total deviations:** 1 auto-fixed (Rule 3 blocking) + 1 verification-shell adaptation
**Impact on plan:** No scope creep. The `.gitignore` is a one-time hygiene fix the project needs anyway; the `python3` shell usage is host-specific and the scripts remain portable via `sys.executable`.

## Issues Encountered

None during planned work. All eight invocations executed cleanly on the first run, all 8 fixtures had the expected shape (`strategy`, `strategy_params`, `env`, `metrics` with `avg_val_last100`, `cum_val_total`, `avg_net_profit`, `delivery_ratio`, `avg_providers_l100`, `sus_final`, `ic_per_phase`), and `regression_check.py` returned exit 0 on first run against the same monolith.

## User Setup Required

None — Phase 1 is stdlib-only (D-07 / PROJECT.md constraint). No environment variables, no external services, no installs.

## Next Phase Readiness
- **Plans 02–05 unblocked.** They can now refactor `sph_sim.py` into the `sphsim/` package (per D-01 through D-16) and verify backwards compatibility after each step by running:
  ```
  python3 scripts/regression_check.py
  ```
  Exit 0 = no regression; exit 1 = at least one of the 8 baseline invocations now produces different JSON; exit 2 = the refactor broke subprocess invocation or JSON output.
- **Critical reminder for plan 02+:** The `random.seed(seed)` invariant called out in `01-CONTEXT.md` (`<code_context>` → Established Patterns) is now numerically enforced by these fixtures. Any change to the order of `random.*` calls in `SPHSimulator.__init__` or `run()` will trigger a regression. This is the intended behaviour — that's exactly the kind of subtle bug fixture-based regression catches.
- **No blockers.** `sph_sim.py` is untouched (`git diff sph_sim.py` is empty), the working tree is clean, and the package layout decisions from CONTEXT (`sphsim/`, `core/`, `strategies/`, `cli/`) are ready to be applied in plan 01-02.

## Self-Check: PASSED

- `scripts/generate_baseline.py` — FOUND
- `scripts/regression_check.py` — FOUND
- `tests/fixtures/baseline_v1/01-naive-zeta-0.5.json` — FOUND
- `tests/fixtures/baseline_v1/02-threshold-max-phase-3.json` — FOUND
- `tests/fixtures/baseline_v1/03-phase-prob-default.json` — FOUND
- `tests/fixtures/baseline_v1/04-incentive-expected-P-100.json` — FOUND
- `tests/fixtures/baseline_v1/05-adaptive-s-target-10.json` — FOUND
- `tests/fixtures/baseline_v1/06-naive-zeta-0.4-custom-env.json` — FOUND
- `tests/fixtures/baseline_v1/07-phase-prob-custom-kappa-alpha.json` — FOUND
- `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` — FOUND
- `tests/fixtures/baseline_v1/MANIFEST.txt` — FOUND
- `.gitignore` — FOUND
- Commit `5652a64` (Task 1) — FOUND in `git log`
- Commit `de55865` (Task 2) — FOUND in `git log`

All claimed artefacts and commits verified on disk and in git history. `python3 scripts/regression_check.py` returns exit 0. `git diff sph_sim.py` is empty.

---
*Phase: 01-refactoring-foundation*
*Completed: 2026-05-25*
