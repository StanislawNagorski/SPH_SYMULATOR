---
phase: 3
plan: 03-02
subsystem: custom-strategy-loader
tags: [cli, argparse, mutex, custom-strategy, integration, wave-2]
requirements:
  fulfilled: [STRAT-03]
dependency_graph:
  requires:
    - "sphsim.strategies.loader (Plan 03-01 — load_custom, parse_params_from_meta, LoaderError)"
    - "sphsim.strategies.BUILTIN_STRATEGIES (Plan 03-01 frozenset snapshot)"
    - "sphsim.core.simulator.SPHSimulator (Phase 1 interface — unchanged)"
    - "sphsim.cli.output.format_human / format_json (Phase 1 — unchanged)"
    - "sphsim.config.DEFAULT_* (Phase 1 env constants — used as placeholder for Phase 5 env override)"
  provides:
    - "CLI flag --custom <path> as third member of required mutex group (D-44)"
    - "CLI flag --param k=v repeatable, outside mutex (D-39, action='append', default=[])"
    - "main.py early branch: if args.custom → load_custom → parse_params_from_meta → register → SPHSimulator → format_*"
    - "Graceful Polish stderr warning for --param without --custom"
    - "Polish stderr + sys.exit(1) on LoaderError (both load and param-parse layers)"
  affects:
    - "Plan 03-03 (REPL do_custom/do_run — separate, also depends_on 03-01)"
    - "Plan 03-04 (template + verify_phase3.sh — needs --custom flow operational)"
tech_stack:
  added: []  # stdlib only — no new packages
  patterns:
    - "Second early-branch in main.py mirroring args.interactive pattern from Phase 2"
    - "Lazy imports inside early-branch (loader + sys) — built-in flow has zero extra cost"
    - "args.strategy = name quick-fix so format_human/format_json render custom name correctly"
    - "argparse choices frozen at parse-time via BUILTIN_STRATEGIES snapshot (D-50)"
    - "Graceful stderr warning (not error) when --param given without --custom (D-39 Claude's Discretion)"
key_files:
  created: []
  modified:
    - "sphsim/cli/args.py (+8 lines: --custom mutex member, --param outside mutex, BUILTIN_STRATEGIES import, --strategy choices switched)"
    - "sphsim/cli/main.py (+39 lines: graceful --param warning + full args.custom early branch)"
decisions:
  - "D-44: --custom is third member of `--interactive | --strategy | --custom` mutex group (required=True)"
  - "D-50: --strategy choices switched from list(STRATEGIES.keys()) to list(BUILTIN_STRATEGIES) — argparse freezes built-in listing at parse time; custom strategies are reachable only via --custom in one-shot CLI"
  - "D-39: --param uses action='append', default=[], metavar='K=V'; validation deferred to loader.parse_params_from_meta"
  - "D-46: caller (main.py) does STRATEGIES[name] = strategy_fn registration; loader stays pure"
  - "D-45: banner [OSTRZEŻENIE] emitted by loader on stdout PRE-exec — main.py does NOT duplicate"
  - "Claude's Discretion: --param without --custom prints Polish stderr warning ('Flaga --param ignorowana — działa tylko z --custom.') and continues built-in flow (graceful, not fatal)"
  - "Claude's Discretion: args.strategy = name set BEFORE format_* so output 'Strategia: SMOKE_CUSTOM' renders correctly in human + JSON"
metrics:
  duration: "~10 minutes (sequential executor)"
  tasks: 2/2 complete
  files_modified: 2
  lines_added: ~47
  completed_date: 2026-05-27
---

# Phase 3 Plan 02: CLI integration of custom strategy loader — Summary

Wires `--custom <path>` and `--param k=v` into the one-shot CLI by extending the argparse mutex group and adding a second early-branch in `main()` that delegates to the Wave 1 loader for path validation, STRATEGY_META-driven param typing, runtime STRATEGIES registration, simulation with DEFAULT env, and existing format_*/JSON output dispatch.

## What Was Built

The CLI now accepts a third mutex-group member `--custom <path>` (alongside `--interactive` and `--strategy`) and an out-of-mutex repeatable `--param k=v` flag. When `--custom` is invoked, `main()` lazy-imports the Wave 1 loader, runs `load_custom(args.custom)` (which prints the `[OSTRZEŻENIE]` banner on stdout before any exec), runs `parse_params_from_meta(args.param, meta, name)` for typed conversion, registers the strategy at `STRATEGIES[name] = strategy_fn` (D-46), sets `args.strategy = name` for downstream formatting, builds `SPHSimulator` with `DEFAULT_*` env constants (Phase 5 will override), runs the simulation, and dispatches to `format_human`/`format_json` exactly as the built-in flow does. `LoaderError` at either layer is caught and surfaced as a single Polish one-liner on stderr with `sys.exit(1)`. As a graceful safeguard, `--param` given without `--custom` emits a Polish stderr warning and continues into the built-in `--strategy` flow without aborting.

The CLI listing is now bounded by `BUILTIN_STRATEGIES` (D-50): `--strategy` choices are frozen at parse time to the five Phase 1 names, so the only way to reach a custom strategy in one-shot CLI is `--custom <path>`. REPL listing (Wave 3 / Plan 03) will still see custom strategies live via `STRATEGIES.keys()`.

## Tasks Completed

| # | Task | Files | Commit | Status |
|---|------|-------|--------|--------|
| 3-02-01 | Add `--custom` to mutex + `--param` outside mutex + switch `--strategy` choices to `BUILTIN_STRATEGIES` | `sphsim/cli/args.py` | `9a73307` | done |
| 3-02-02 | Wire `if args.custom:` early branch in `main.py` — load + parse + register + simulate + format | `sphsim/cli/main.py` | `cf2f451` | done |

## Acceptance Criteria

### Task 3-02-01

- Source grep `mutex.add_argument('--custom'` → 1 ✓
- Source grep `p.add_argument('--param'` → 1 ✓
- Source grep `choices=list(BUILTIN_STRATEGIES)` → 1 ✓
- Source grep `from sphsim.strategies import STRATEGIES, BUILTIN_STRATEGIES` → 1 ✓
- `parse_args` returns `a.custom='foo.py' and a.param=[] and a.strategy is None and a.interactive is False` when invoked with `--custom foo.py` ✓
- `--param zeta=0.7 --param max_phase=3` accumulates correctly via `action='append'` ✓
- Mutex enforcement: `--custom foo.py --strategy naive` → argparse "not allowed with argument" ✓
- `--help` text contains "Ścieżka do pliku .py z custom strategią" and "Parametr custom strategii" ✓
- Regression 8/8 still pass ✓
- Meta consistency invariant pass ✓
- Loader 21-test suite pass ✓

### Task 3-02-02

- Source grep `if args.custom:` → 1 ✓
- Source grep `from sphsim.strategies.loader import` → 1 ✓
- Source grep `load_custom(args.custom)` → 1 ✓
- Source grep `STRATEGIES[name] = strategy_fn` → 1 ✓ (D-46 caller registration)
- Source grep `Flaga --param ignorowana` → 1 ✓ (graceful warning)
- Source grep `args.strategy = name` → 1 ✓ (quick-fix for format_*)
- Smoke happy path: `--custom /tmp/smoke_custom.py --seed 42 --json` exits 0, banner on stdout (line 1), valid JSON with `strategy='smoke_custom'` (lines 2+) ✓
- Smoke determinism: same seed → identical output across two invocations ✓
- Missing file: `--custom /tmp/nope.py` exits 1, stderr `"Plik nie istnieje: /tmp/nope.py"` ✓
- Param error: declared `foo` only, user passes `--param bar=2` → exits 1, stderr `"Nieznany parametr 'bar' dla strategii 'smoke_custom'. Dostępne: foo."` ✓
- `--param` without `--custom`: `--strategy naive --param zeta=0.7` exits 0, stderr warning "Flaga --param ignorowana — działa tylko z --custom.", stdout is valid JSON (built-in flow runs) ✓
- Builtin collision: `--custom /tmp/naive.py` exits 1, stderr `"Nazwa 'naive' koliduje z wbudowaną strategią. Zmień nazwę pliku."` ✓
- Mutex enforcement: `--custom foo.py --strategy naive` → argparse error "not allowed with argument" ✓
- Regression 8/8 still pass ✓
- Full discover 22 tests pass ✓

## Plan-Level Phase Regression Gates

| Gate | Command | Result |
|------|---------|--------|
| Loader suite | `python3 -m unittest tests.test_loader` | Ran 21 tests in 1.120s — OK |
| Meta consistency invariant | `python3 -m unittest tests.test_strategy_meta_consistency` | Ran 1 test — OK |
| Full discover | `python3 -m unittest discover tests` | Ran 22 tests in 1.122s — OK |
| Phase 1 baseline regression | `python3 scripts/regression_check.py` | PASS: 8/8 |
| Integration smoke (happy) | `python3 sph_sim.py --custom /tmp/smoke_custom.py --seed 42 --json` | exit 0, banner+JSON, deterministic |
| Integration smoke (missing) | `python3 sph_sim.py --custom /tmp/nope.py --seed 42` | exit 1, Polish stderr "Plik nie istnieje" |
| Integration smoke (param error) | `python3 sph_sim.py --custom /tmp/smoke.py --param bar=2 ...` | exit 1, Polish stderr "Nieznany parametr 'bar'" |
| Integration smoke (param w/o custom) | `python3 sph_sim.py --strategy naive --param zeta=0.7 ...` | exit 0, warning on stderr, built-in JSON on stdout |
| Mutex enforcement | `python3 sph_sim.py --custom foo.py --strategy naive` | argparse exit 2, "not allowed with argument" |
| Builtin collision | `python3 sph_sim.py --custom /tmp/naive.py --seed 42` | exit 1, "Nazwa 'naive' koliduje..." |

## Deviations from Plan

None. Plan executed exactly as written. No Rule 1/2/3 auto-fixes triggered, no Rule 4 architectural decisions surfaced, no authentication gates encountered. All decision references in PLAN.md (D-39, D-44, D-45, D-46, D-50) implemented verbatim. The Claude's Discretion call for `args.strategy = name` quick-fix was anticipated and explicitly listed in the PLAN action — implemented as planned.

## Threat Surface Scan

No new security-relevant surface introduced beyond the Wave 1 loader's documented `<threat_model>`:

- T-3-01 (Tampering / Elevation via `--custom <path>` → exec_module) — already MITIGATED in Plan 03-01 via D-45 banner and 4-layer validation; Plan 02 only wires the string flag through argparse. No new attack surface.
- T-3-06 (Tampering — `--param` injection to built-in) — MITIGATED in Plan 02 via explicit graceful-warn-and-ignore branch (`if args.param and not args.custom`); built-in `--strategy` flow never consumes `args.param`.
- T-3-07/T-3-08 (Repudiation/DoS) — ACCEPTED in Plan 03-01; unchanged in Plan 02.
- T-3-SC (Dependency confusion) — N/A (stdlib only, no new packages).

## Known Stubs

None. Both modified files (`args.py`, `main.py`) are functionally complete. The `--custom` flow loads, validates, registers, simulates, and formats output end-to-end. The only "deferred" aspect is env-param override (`--phi`, `--rho`, `--K1` non-default values for custom flow) which is explicit Phase 5 scope per D-CONTEXT and the plan's `<objective>` ("Phase 5 doda override env") — this is a documented future-plan boundary, not a stub.

## Self-Check: PASSED

Files verified to exist on disk:

- FOUND: `sphsim/cli/args.py` (modified — 65 lines)
- FOUND: `sphsim/cli/main.py` (modified — 72 lines)

Commits verified in `git log --oneline`:

- FOUND: `9a73307` (feat(03-02): add --custom to mutex + --param outside mutex in args.py)
- FOUND: `cf2f451` (feat(03-02): wire --custom early branch in main.py — load+parse+register+simulate)

Full discover green: `Ran 22 tests in 1.122s — OK`. Regression 8/8: `PASS: 8/8`. Five integration smoke scenarios (happy / missing / param-error / param-without-custom / builtin-collision / mutex / determinism) all behave per success criteria.
