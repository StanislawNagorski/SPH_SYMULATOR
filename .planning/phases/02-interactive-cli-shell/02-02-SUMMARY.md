---
phase: 02-interactive-cli-shell
plan: 02
subsystem: cli-args
tags: [cli, argparse, mutex, interactive, backwards-compat]
requirements_completed:
  - CLI-01
dependency_graph:
  requires:
    - "sphsim/cli/args.py (Phase 1 — refactored argparse setup)"
    - "sphsim/strategies (Phase 1 — STRATEGIES dict for choices)"
  provides:
    - "args.interactive boolean attribute (consumed by Plan 03)"
    - "args.strategy (None when --interactive used)"
    - "Mutex enforcement: exactly one of --interactive | --strategy"
  affects:
    - "sphsim/cli/main.py (Plan 03 will add early branch `if args.interactive: run_repl(); return`)"
tech_stack:
  added: []
  patterns:
    - "argparse add_mutually_exclusive_group(required=True) — two-mode entry-point"
key_files:
  created: []
  modified:
    - "sphsim/cli/args.py"
decisions:
  - "D-23: docstring header lists both authors (Stanisław Nagórski, Mikołaj Rutkowski) — brand consistency between REPL intro and --help"
  - "D-27: --interactive | --strategy as add_mutually_exclusive_group(required=True) — two clear modes, no mixing"
  - "D-28: --strategy moved out of top-level required=True; mutex group's required=True takes over; backwards compat preserved (all 8 fixtures still parse)"
metrics:
  duration_seconds: 104
  completed: "2026-05-25T17:44:19Z"
  tasks_total: 1
  tasks_completed: 1
  files_modified: 1
---

# Phase 2 Plan 2: Add --interactive Flag in Mutex Group Summary

`sphsim/cli/args.py` now exposes `--interactive` (boolean) and `--strategy` as members of a required mutually exclusive group, enforcing exactly one of the two flags at parse time while preserving the Phase 1 baseline regression suite (8/8 fixtures pass).

## What Was Built

A minimal but precise refactor of `parse_args()` in `sphsim/cli/args.py`:

1. **Mutex group (D-27/D-28).** `--strategy` was previously a top-level `required=True` argument. It now lives inside `p.add_mutually_exclusive_group(required=True)` together with `--interactive` (boolean `action='store_true'`). The group itself carries the `required=True` semantics, so the validation contract is:
   - Exactly one of `--interactive` or `--strategy` MUST be present.
   - Both flags simultaneously → argparse error: `argument --strategy: not allowed with argument --interactive` (exit 2).
   - Neither flag → argparse error: `one of the arguments --interactive --strategy is required` (exit 2).
   - `--strategy` retains its `choices=list(STRATEGIES.keys())` validation and Polish `help=` text.

2. **Docstring housekeeping (D-23).** Module header line changed from `Autor: Mikołaj Rutkowski` to `Autorzy: Stanisław Nagórski, Mikołaj Rutkowski` (plural, both authors). This brings `args.py` in line with the REPL intro authors block introduced in Plan 03.

No other argparse calls (`--zeta`, `--max_phase`, `--probs`, `--s_target`, `--expected_P`, `--nU`, `--nSUS`, `--K1`, `--T`, `--kappa`, `--alpha`, `--seed`, `--json`, `--verbose`) were touched. No new imports.

## Diff Summary

- 1 file changed: `sphsim/cli/args.py` (+6 / −3)
  - Line 4: docstring author line updated (D-23)
  - Lines 38–42: `p.add_argument('--strategy', required=True, ...)` (1 line) replaced with `mutex = p.add_mutually_exclusive_group(required=True)` plus two `mutex.add_argument(...)` calls for `--interactive` and `--strategy` (4 lines after blank-formatting → net +3 source lines for the argparse change, plus the 1-line docstring edit).

## Verification Results

| Check | Result |
|-------|--------|
| `grep -c 'Autorzy: Stanisław Nagórski, Mikołaj Rutkowski' sphsim/cli/args.py` | 1 |
| `grep -c 'Autor: Mikołaj Rutkowski' sphsim/cli/args.py` | 0 |
| `grep -c 'add_mutually_exclusive_group(required=True)' sphsim/cli/args.py` | 1 |
| `grep -c -- "--interactive'" sphsim/cli/args.py` | 1 |
| `grep -c "'--strategy', required=True" sphsim/cli/args.py` | 0 |
| `python3 sph_sim.py --interactive --strategy naive` | exit 2 — `not allowed with argument --interactive` |
| `python3 sph_sim.py` (no flags) | exit 2 — `one of the arguments --interactive --strategy is required` |
| `python3 sph_sim.py --strategy naive --zeta 0.5 --seed 42 --json` | exit 0, valid JSON on stdout |
| `python3 scripts/regression_check.py --verbose` | **PASS: 8/8** (exit 0) — CLI-04 preserved |
| `parse_args()` with `--strategy naive` | `ns.interactive=False, ns.strategy='naive'` |
| `parse_args()` with `--interactive` | `ns.interactive=True, ns.strategy=None` |

## Regression Check Output

```
[1/8] 01-naive-zeta-0.5 -> OK
[2/8] 02-threshold-max-phase-3 -> OK
[3/8] 03-phase-prob-default -> OK
[4/8] 04-incentive-expected-P-100 -> OK
[5/8] 05-adaptive-s-target-10 -> OK
[6/8] 06-naive-zeta-0.4-custom-env -> OK
[7/8] 07-phase-prob-custom-kappa-alpha -> OK
[8/8] 08-naive-zeta-0.75-baseline -> OK
PASS: 8/8
regression exit=0
```

All 8 Phase 1 baseline fixtures still match byte-for-byte. The mutex refactor is invisible to existing `--strategy X ...` invocations because (a) `--strategy` retains its `choices=` validation, and (b) the mutex group's `required=True` semantics accept any single-flag invocation that uses `--strategy` alone.

## Deviations from Plan

None — plan executed exactly as written. No bugs, no missing critical functionality, no blocking issues, no architectural changes. Single-task plan, single commit.

## Auth Gates

None.

## Known Stubs

None. `args.interactive` is a real boolean attribute on the parsed namespace and will be consumed by Plan 03 (which adds the `if args.interactive: run_repl(); return` branch in `sphsim/cli/main.py`). The CLI surface itself is fully wired: both error cases (mutex violation, required-mutex violation) produce real argparse errors with correct exit codes.

## Threat Flags

None. This change is a pure argparse-layer refactor: no new network endpoints, no auth paths, no file access, no schema changes at trust boundaries. The mutex group narrows the accepted CLI surface (rejects previously-undefined inputs like "no flag" and "both flags"), which is a strict reduction in attack surface relative to the prior contract.

## Commits

- `b5e2ba6` — `feat(02-02): add --interactive flag in mutex group with --strategy`

## Self-Check: PASSED

- `sphsim/cli/args.py` exists and contains the expected changes.
- Commit `b5e2ba6` exists in the worktree branch's git log.
- All 11 verification checks (grep counts + argparse exit codes + namespace assertions + 8/8 regression fixtures) pass.
