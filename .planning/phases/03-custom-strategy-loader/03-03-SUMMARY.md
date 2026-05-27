---
phase: 3
plan: 03-03
subsystem: custom-strategy-loader
tags: [repl, cmd-shell, custom-strategy, dispatch-namespace, integration, wave-2]
requirements:
  fulfilled: [STRAT-03, STRAT-04]
dependency_graph:
  requires:
    - "sphsim.strategies.loader (Plan 03-01 — load_custom, parse_params_from_meta, LoaderError)"
    - "sphsim.strategies.BUILTIN_STRATEGIES (Plan 03-01 frozenset snapshot)"
    - "sphsim.strategies.STRATEGIES (Phase 1 D-14 mutable registry)"
    - "sphsim.core.simulator.SPHSimulator (Phase 1 interface — unchanged)"
    - "sphsim.cli.output.format_human (Phase 1 — args-like Namespace contract)"
    - "sphsim.config.DEFAULT_* (Phase 1 env constants — used until Phase 5 override)"
    - "sphsim.cli.repl.SPHShell (Phase 2 — extended with 2 new methods + 3 modified)"
  provides:
    - "SPHShell.do_custom(arg) — REPL command `custom <ścieżka> [k=v ...]` loads and registers custom strategy with D-38 reload semantics"
    - "SPHShell.do_run(arg) — REPL command `run <nazwa> [k=v ...]` runs built-in or custom strategy via DEFAULT env params and format_human output"
    - "SPHShell.do_help — 6-command listing with 32-char padded em-dash separator"
    - "SPHShell.do_strategies — D-50 dispatch namespace + ` [custom]` suffix for non-builtin"
    - "SPHShell.do_strategy — D-50 dispatch namespace (sphsim.strategies vs sphsim.custom)"
  affects:
    - "Plan 03-04 (template + verify_phase3.sh — needs REPL flow operational for end-to-end UAT)"
    - "Phase 4 (RationalAgent compare) — may extend do_run wrapper"
    - "Phase 5 (Configurable env) — will override hardcoded seed=42 + DEFAULT_* in do_run"
tech_stack:
  added: []  # stdlib only — argparse, sys added to top of repl.py
  patterns:
    - "Reload detection via sys.modules membership check BEFORE load_custom (D-38; preserves was_loaded flag from being clobbered by loader's sys.modules write)"
    - "Dispatch namespace by BUILTIN_STRATEGIES membership: sphsim.strategies.<name> for builtin, sphsim.custom.<name> for custom (D-46/D-50)"
    - "Fabricated argparse.Namespace for format_human reuse — REPL has no argparse parsing of env params, so Namespace built inline from DEFAULT_* constants (D-41)"
    - "LoaderError → stdout one-liner with early return (do_custom + do_run + parse_params_from_meta error paths; D-48 REPL never crashes)"
    - "32-char padding for help listing to align em-dash across variable-length command signatures (CONVENTIONS.md §Formatting)"
key_files:
  created: []
  modified:
    - "sphsim/cli/repl.py (+119 lines: 2 new methods, 3 modified methods, 9 new imports across 2 import groups)"
decisions:
  - "D-38: reload detection via `'sphsim.custom.<basename>' in sys.modules` BEFORE load_custom; was_loaded flag captured BEFORE loader writes (loader registers fresh module overwriting any prior entry)"
  - "D-41: SPHSimulator built with full DEFAULT_* env (nU/nSUS/K0/K1/F/T/kappa/alpha/phi/rho) + hardcoded seed=42; format_human invoked via fabricated argparse.Namespace(strategy=name, nU/nSUS/T/kappa/alpha, verbose=False)"
  - "D-42: verbatim error messages — `Użycie: run <nazwa> [param=wartość ...]. Wpisz 'strategies' żeby zobaczyć dostępne.` for no-args; `Strategia '<name>' nie istnieje. Dostępne: <live STRATEGIES.keys()>.` for unknown"
  - "D-43: positional parsing via arg.split() — first token = path/name, remainder = k=v tokens; paths with spaces NOT supported (academic project edge case)"
  - "D-46: STRATEGIES[name] = fn registration in do_custom (caller does mutation, loader stays pure)"
  - "D-50: dispatch namespace `ns = 'sphsim.strategies' if name in BUILTIN_STRATEGIES else 'sphsim.custom'` applied in do_strategies + do_strategy + do_run meta lookup; ` [custom]` suffix appended after description in do_strategies for non-builtin"
  - "Top-level imports preferred over lazy: 9 new symbols imported at module top (argparse, sys, BUILTIN_STRATEGIES, load_custom/parse_params_from_meta/LoaderError, SPHSimulator, format_human, 10 DEFAULT_*) — REPL already has readline/atexit overhead at startup, consistency with Phase 2 import pattern"
  - "Hardcoded seed=42 in do_run: deliberate Phase 3 scope boundary — Phase 5 will add config.DEFAULT_SEED or --seed REPL flag; current behavior gives deterministic single-shot runs per session"
  - "do_run does not echo banner ([OSTRZEŻENIE]) — that's loader's responsibility, fires only during do_custom path; do_run on already-loaded custom strategies skips re-exec"
metrics:
  duration: "~10 minutes (sequential executor)"
  tasks: 2/2 complete
  files_modified: 1
  lines_added: ~119
  completed_date: 2026-05-27
---

# Phase 3 Plan 03: REPL integration of custom strategy loader — Summary

Extends SPHShell from 4 to 6 commands by adding `do_custom` (load + register + reload-aware verb) and `do_run` (DEFAULT-env SPHSimulator + format_human dispatch), then modifies `do_help` / `do_strategies` / `do_strategy` to render the new commands, suffix non-builtin entries with ` [custom]`, and route metadata lookups through the BUILTIN_STRATEGIES dispatch namespace.

## What Was Built

The REPL gained two new commands and three modified ones, completing the D-41 deferred work from Phase 2:

- **`custom <ścieżka> [k=v ...]`** — splits the argument string positionally (D-43), captures `was_loaded` via `'sphsim.custom.<basename>' in sys.modules` BEFORE invoking the Wave 1 loader (D-38; loader registers a fresh module that would clobber the membership check if done after), calls `load_custom` then `parse_params_from_meta`, surfaces any `LoaderError` as a single Polish stdout line with early return (D-48 — REPL never crashes), registers `STRATEGIES[name] = fn` in the caller (D-46), and prints either `Załadowano custom strategię 'X'.` or `Przeładowano custom strategię 'X'.` depending on the prior membership.
- **`run <nazwa> [k=v ...]`** — emits D-42 verbatim messages for no-args / unknown-name paths (using live `STRATEGIES.keys()` so custom strategies show up after `custom`), routes the meta lookup via D-50 dispatch namespace (`sphsim.strategies.<name>` for builtin, `sphsim.custom.<name>` for custom), parses params, builds `SPHSimulator(nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, ..., strategy_fn=STRATEGIES[name], params=params, seed=42)` with the full DEFAULT_* env from `sphsim/config.py`, runs the simulation, and dispatches to `format_human` via a fabricated `argparse.Namespace(strategy=name, nU/nSUS/T/kappa/alpha, verbose=False)`.
- **`do_help`** — now lists 6 commands (help / exit / strategies / strategy / custom / run) with 32-char padding to align em-dash across the variable-length signatures.
- **`do_strategies`** — branches per name: builtin keeps the Phase 2 listing as-is, custom imports from `sphsim.custom.<name>` and appends ` [custom]` after the description.
- **`do_strategy`** — gains a single-line dispatch (`ns = 'sphsim.strategies' if name in BUILTIN_STRATEGIES else 'sphsim.custom'`) before the existing description/params/baseline_kpi rendering.

The CLI one-shot path (`--strategy` / `--custom`) is untouched — Plan 03-02 wired that independently against the same Wave 1 loader. The Phase 1 regression fixtures (8/8) and the Phase 2 invariant test remain green.

## Tasks Completed

| # | Task | Files | Commit | Status |
|---|------|-------|--------|--------|
| 3-03-01 | Add `argparse`/`sys`/`BUILTIN_STRATEGIES`/loader/SPHSimulator/format_human/DEFAULT_* imports + `do_custom` + `do_run` to SPHShell | `sphsim/cli/repl.py` | `fc44944` | done |
| 3-03-02 | Modify `do_help` (6 commands w/ 32-char padding), `do_strategies` (D-50 dispatch + `[custom]` suffix), `do_strategy` (D-50 dispatch namespace) | `sphsim/cli/repl.py` | `3fe5cfb` | done |

## Acceptance Criteria

### Task 3-03-01

- Source grep `def do_custom` → 1 ✓
- Source grep `def do_run` → 1 ✓
- Source grep `from sphsim.strategies.loader import` → 1 ✓
- Source grep `from sphsim.cli.output import format_human` → 1 ✓
- Source grep `from sphsim.config import` → 1 ✓
- Source contains `Załadowano custom` ≥ 1 (×2: comment + print) ✓
- Source contains `Przeładowano custom` ≥ 1 (×2: comment + print) ✓
- Source contains `Użycie: run <nazwa>` ✓
- Source contains `Użycie: custom <ścieżka>` ✓
- Source contains `argparse.Namespace` ✓
- Source contains `STRATEGIES[name] = fn` ✓
- Behavior: `custom /tmp/repl_smoke.py` → `Załadowano custom strategię 'repl_smoke'.` ✓
- Behavior: second `custom /tmp/repl_smoke.py` → `Przeładowano custom strategię 'repl_smoke'.` ✓
- Behavior: `run naive zeta=0.7` → `SPH SYMULATOR | Strategia: NAIVE` block, full KPI table ✓
- Behavior: `run repl_smoke` (after custom load) → `SPH SYMULATOR | Strategia: REPL_SMOKE` block ✓
- Behavior: `run` (no args) → `Użycie: run <nazwa> [param=wartość ...]. Wpisz 'strategies' żeby zobaczyć dostępne.` ✓
- Behavior: `run nieznana` → `Strategia 'nieznana' nie istnieje. Dostępne: naive, threshold, phase_prob, incentive, adaptive, repl_smoke.` ✓
- Behavior: `custom /tmp/nope_does_not_exist.py` → `Plik nie istnieje: /tmp/nope_does_not_exist.py` + REPL continues to next prompt (no crash) ✓
- Regression: `python3 scripts/regression_check.py` → PASS 8/8 ✓
- Tests: `python3 -m unittest discover tests` → Ran 22 tests, OK ✓

### Task 3-03-02

- Source grep `custom <ścieżka> [k=v ...]` ≥ 1 (×2: docstring header + do_help line) ✓
- Source grep `run <nazwa> [k=v ...]` ≥ 1 (×2: docstring header + do_help line) ✓
- Source grep `if name in BUILTIN_STRATEGIES:` ≥ 1 ✓
- Source grep `sphsim.custom.{name}` ≥ 1 ✓
- Source grep `[custom]` ≥ 1 (×3: comment + suffix string + docstring) ✓
- Source grep `ns = 'sphsim.strategies' if name in BUILTIN_STRATEGIES else 'sphsim.custom'` ≥ 1 (×2: do_strategy + do_run) ✓
- Behavior: `help` shows 6 indented command lines (help/exit/strategies/strategy/custom/run) ✓
- Behavior: `help` mentions `custom <ścieżka>` and `run <nazwa>` ✓
- Behavior: `strategies` before any custom load shows 5 builtin entries with NO `[custom]` suffix ✓
- Behavior: `strategies` after `custom /tmp/repl_smoke.py` shows `repl_smoke  — r [custom]` (suffix verbatim) ✓
- Behavior: `strategy naive` → `Opis: COMMIT z prawdopodobieństwem zeta` + params section ✓
- Behavior: `strategy repl_smoke` after load → `Opis: r` + params section (dispatch namespace works) ✓
- Regression: `python3 scripts/regression_check.py` → PASS 8/8 ✓
- Tests: `python3 -m unittest discover tests` → Ran 22 tests, OK ✓

## Plan-Level Phase Regression Gates

| Gate | Command | Result |
|------|---------|--------|
| Loader suite | `python3 -m unittest tests.test_loader` | Ran 21 tests — OK |
| Meta consistency invariant | `python3 -m unittest tests.test_strategy_meta_consistency` | Ran 1 test — OK |
| Full discover | `python3 -m unittest discover tests` | Ran 22 tests in 1.117s — OK |
| Phase 1 baseline regression | `python3 scripts/regression_check.py` | PASS: 8/8 |
| REPL Smoke 1 (custom + reload + run + run no-args + run nieznana) | `printf "custom ...\n..." \| python3 sph_sim.py --interactive` | All 6 grep assertions green |
| REPL Smoke 2 (help + strategies pre/post custom + strategy dispatch) | `printf "help\nstrategies\ncustom ...\n..." \| python3 sph_sim.py --interactive` | All 4 grep assertions green |
| REPL fail-safe | `printf "custom /tmp/nope.py\nexit\n" \| python3 sph_sim.py --interactive` | "Plik nie istnieje" printed; REPL continues to next prompt without crash |

## Deviations from Plan

None. Plan executed exactly as written. No Rule 1/2/3 auto-fixes triggered, no Rule 4 architectural decisions surfaced, no authentication gates encountered.

The only adjustment within the planned scope: the plan suggested a `verb = "Przeładowano" if was_loaded else "Załadowano"` then a single `print(f"{verb} custom ...")` — I rewrote that as an explicit `if/else` with two separate `print` calls so that the literal substrings `Załadowano custom` and `Przeładowano custom` appear verbatim in source code (satisfying the strict `grep -c` acceptance criteria). Behavior is identical; the rewrite is purely cosmetic-for-grep.

## Threat Surface Scan

No new security-relevant surface introduced beyond what's documented in the plan's `<threat_model>`:

- **T-3-01** (Tampering / Elevation — `custom <path>` → exec_module) — ACCEPTED-WITH-WARNING, inherited from Plan 03-01; the REPL surfaces the loader's `[OSTRZEŻENIE]` banner in the transcript (visible at line 1 of every successful custom load).
- **T-3-02** (Tampering — sys.modules pollution / namespace bleed) — MITIGATED via the BUILTIN_STRATEGIES dispatch in do_strategies/do_strategy/do_run; custom modules live in `sphsim.custom.<name>` and never collide with `sphsim.strategies.<name>`.
- **T-3-09** (Spoofing — user patches STRATEGIES directly) — ACCEPTED; academic project, REPL is user-facing, not a security boundary.
- **T-3-10** (Information Disclosure — custom strategy can read sibling files) — ACCEPTED; banner D-45 warns, sandbox is out of scope per D-36.
- **T-3-11** (DoS — `run` with DEFAULT_T=1000 × nU=250 = 250k iterations) — ACCEPTED; Ctrl+C from `cmd.Cmd` cmdloop returns control to the prompt.
- **T-3-SC** (Dependency confusion) — N/A; stdlib only.

## Known Stubs

None. The REPL now supports the full edit-run-edit iteration loop end-to-end:

1. User writes `~/mystrat.py` with `strategy_mystrat` + `STRATEGY_META`.
2. `python sph_sim.py --interactive` → `custom ~/mystrat.py [k=v ...]` (banner + register + sticky in STRATEGIES).
3. `strategies` shows `mystrat — <desc> [custom]`.
4. `strategy mystrat` shows the full meta panel (description, params with types + defaults, baseline_kpi if set).
5. `run mystrat [k=v ...]` runs the full T=1000 simulation against DEFAULT env, prints the human-readable KPI table.
6. Iterate: edit file → `custom ~/mystrat.py` again → `Przeładowano...` → `run mystrat`.
7. `exit` clears the registration (D-37 sticky-only-in-session).

The only deferred capability is per-session env override (`--phi`, `--rho`, `--K1`, `--T`, `--seed`) — explicitly Phase 5 scope per the plan's `<objective>` and the deferred-items section of 03-CONTEXT.md.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. The REPL uses stdlib only and reads no environment variables.

## Next Phase Readiness

Wave 2 of Phase 3 is complete (Plans 03-02 and 03-03 both green; both depend only on Plan 03-01's Wave 1 loader). Plan 03-04 (Wave 3 — template `examples/custom_strategy_template.py` + `scripts/verify_phase3.sh` phase exit gate) can begin: it needs the REPL custom path operational for end-to-end UAT, which this plan provides.

## Self-Check: PASSED

Files verified to exist on disk:

- FOUND: `sphsim/cli/repl.py` (modified — ~270 lines, 6 commands)

Commits verified in `git log --oneline`:

- FOUND: `fc44944` (feat(03-03): add do_custom + do_run to SPHShell)
- FOUND: `3fe5cfb` (feat(03-03): modify do_help (6 commands), do_strategies ([custom] suffix + dispatch ns), do_strategy (dispatch ns))

Behavioral checks: both smoke transcripts captured at `/tmp/repl_out.txt` and `/tmp/repl_mod.txt` show all 10 expected output strings present. Regression 8/8, full discover 22/22 OK, loader 21/21 OK, invariant 1/1 OK.

---
*Phase: 03-custom-strategy-loader*
*Completed: 2026-05-27*
