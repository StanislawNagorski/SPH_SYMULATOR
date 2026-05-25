---
phase: 02-interactive-cli-shell
plan: 03
subsystem: cli-repl
tags: [cli, repl, cmd-cmd, readline, strategies, baseline-kpi, D-15, D-17, D-18, D-19, D-20, D-21, D-22, D-29, D-30, D-31, D-32, D-33]
requirements_completed:
  - CLI-01
  - CLI-02
  - CLI-03
  - STRAT-01
  - STRAT-02
dependency_graph:
  requires:
    - "Plan 02-01 (STRATEGY_META in 5 strategy modules — description, params, baseline_kpi)"
    - "Plan 02-02 (--interactive flag in mutex group with --strategy in sphsim/cli/args.py)"
  provides:
    - "sphsim/cli/repl.py — SPHShell(cmd.Cmd) + run_repl() public entry-point"
    - "REPL with 4 commands (help, exit, strategies, strategy <nazwa>) without slash prefix (D-17)"
    - "Foundation for Phase 3 (custom strategy loader will add do_custom to SPHShell)"
    - "Foundation for Phase 4 (Rational Agent comparison) — REPL is the natural surface"
  affects:
    - "sphsim/cli/main.py (early branch dispatches to run_repl when args.interactive)"
tech_stack:
  added: []
  patterns:
    - "stdlib-only cmd.Cmd subclass with do_* methods for command dispatch"
    - "Lazy import of repl from main.py — keeps one-shot CLI startup unaffected"
    - "Dynamic STRATEGY_META access via importlib.import_module (mirrors Phase 3 custom-loader contract)"
    - "readline history file with silent OSError handling (sandboxed-env robustness)"
key_files:
  created:
    - "sphsim/cli/repl.py (149 lines, stdlib only: cmd + readline + importlib + os + atexit)"
  modified:
    - "sphsim/cli/main.py (+4 lines: early `if args.interactive: ... return` branch)"
decisions:
  - "Applied D-15/D-17/D-18/D-19/D-20/D-21/D-22/D-29/D-30/D-31/D-32/D-33 verbatim — no semantic deviation"
  - "Claude's Discretion (D-33 area): do_EOF prints empty line then delegates to do_exit — single source of truth for goodbye text"
  - "Claude's Discretion: param format `name: type = default!r — description` (zeta: float = 0.5 — Frakcja COMMIT (0..1)) — readable mirror of argparse signature"
  - "Claude's Discretion: section order in `strategy <name>` = description → params → baseline_kpi (top-down, baseline at bottom)"
  - "Rule 2 extension: OSError caught (not just FileNotFoundError) on readline.read_history_file and write_history_file — robustness for sandboxed/restricted environments where ~/.sphsim_history is not writable. D-19 contract (silent first-run) preserved as a strict subset of this broader handling."
metrics:
  duration_seconds: 298
  completed: "2026-05-25T17:53:47Z"
  tasks_total: 2
  tasks_completed: 2
  files_created: 1
  files_modified: 1
  commits: 2
---

# Phase 2 Plan 3: Interactive REPL (SPHShell) Summary

**One-liner:** `sphsim/cli/repl.py` implements `SPHShell(cmd.Cmd)` with 4 slash-free commands (`help`, `exit`, `strategies`, `strategy <nazwa>`) using stdlib `cmd` + `readline`; `sphsim/cli/main.py` dispatches to `run_repl()` via an early `if args.interactive` branch, while the one-shot `--strategy` path stays byte-identical and Phase 1 regression still passes 8/8.

## What Was Built

### New file: `sphsim/cli/repl.py` (149 lines)

A single, self-contained module exposing two public symbols:

1. **`SPHShell(cmd.Cmd)`** — subclass of `cmd.Cmd` with:
   - `prompt = 'sph> '` (D-22, trailing space, no ANSI)
   - `intro = INTRO` — the 9-line Polish welcome banner verbatim from D-21 (3 separator lines of 62 `=` chars + 4 content lines including authors `Stanisław Nagórski, Mikołaj Rutkowski` + 2 instruction lines)
   - `do_help(arg)` — override of `cmd.Cmd`'s auto-help; prints 4 Polish command descriptions (CLI-02)
   - `do_exit(arg) -> True` — prints `Do widzenia.` and signals cmdloop to stop (CLI-03)
   - `do_EOF(arg) -> True` — handles Ctrl+D: emits empty line then delegates to `do_exit` (Claude's Discretion: single source of truth for goodbye text)
   - `do_strategies(arg)` — iterates `STRATEGIES.keys()` (live registry, no copy), dynamically `importlib.import_module(f'sphsim.strategies.{name}')` per row, reads `STRATEGY_META['description']`, prints D-29 verbatim table with names padded to 12 chars and em-dash separator (STRAT-01)
   - `do_strategy(arg)` — three branches per D-31/D-32:
     - empty arg → D-32 usage hint
     - unknown name → D-31 error with live `STRATEGIES.keys()` list (Phase 3 custom strategies will appear automatically)
     - valid name → prints `Opis:` + `Parametry:` (one line per param formatted as `name: type = default!r — description`) + `Baseline KPI:` (only if `baseline_kpi is not None` — D-26)
   - `default(line)` — override; prints `Nieznana komenda: '{line}'. Wpisz 'help' żeby zobaczyć dostępne komendy.` (D-30)

2. **`run_repl()`** — top-level entry-point:
   - Tries `readline.read_history_file('~/.sphsim_history')`; silently swallows `FileNotFoundError` (D-19) and also broader `OSError` (Rule 2 — sandbox robustness)
   - Registers `atexit` handler `_write_history_silent` (which also swallows `OSError`)
   - Calls `SPHShell().cmdloop()`

Stdlib-only imports: `cmd`, `importlib`, `os`, `readline` (side-effect for line editing on POSIX), `atexit`, plus `from sphsim.strategies import STRATEGIES`.

### Modified file: `sphsim/cli/main.py` (+4 lines)

Inserted immediately after `args = parse_args()` (line 10):

```python
    if args.interactive:
        from sphsim.cli.repl import run_repl
        run_repl()
        return
```

The lazy `from sphsim.cli.repl import run_repl` inside the branch keeps the one-shot path's startup cost unchanged — `readline`/`cmd` are NOT imported when invoking `python sph_sim.py --strategy X ...`. All lines 15-33 (K1 normalization, params dict, SPHSimulator construction, `format_human`/`format_json` output) are byte-identical to the pre-edit version, only shifted down 4 lines.

## Verification Results

### End-to-end REPL flows (all 9 from Task 1 `<verify>` + 10 from plan `<verification>`)

| # | Flow | Expected | Result |
|---|------|----------|--------|
| 1 | `echo exit \| python sph_sim.py --interactive` | exit 0, intro banner + `Do widzenia.` | PASS |
| 2 | `printf '' \| python sph_sim.py --interactive` (EOF) | exit 0, `Do widzenia.` via `do_EOF` | PASS |
| 3 | `printf 'help\nexit\n' \| ...` | `help` lists 4 commands including `strategy <nazwa>` | PASS |
| 4 | `printf 'strategies\nexit\n' \| ...` | 5 rows: `naive`/`threshold`/`phase_prob`/`incentive`/`adaptive` with em-dash + Polish descriptions | PASS (5 strategy rows matched on `^  (name) +— `) |
| 5 | `printf 'strategy naive\nexit\n' \| ...` | `Opis:` + `zeta: float = 0.5 — Frakcja COMMIT (0..1)` + `naive --zeta 0.75 → avg_val_last100 = 92.0` | PASS |
| 6 | `printf 'strategy threshold\nexit\n' \| ...` | `Opis:` + `max_phase: int = 3 — Max faza COMMIT`, NO `Baseline KPI:` section | PASS (params=1, baseline=0) |
| 7 | `printf 'strategy random\nexit\n' \| ...` | `Strategia 'random' nie istnieje. Dostępne: naive, threshold, phase_prob, incentive, adaptive.` (D-31) | PASS |
| 8 | `printf 'strategy\nexit\n' \| ...` | `Użycie: strategy <nazwa>. Wpisz 'strategies' żeby zobaczyć listę.` (D-32) | PASS |
| 9 | `printf 'srategies\nexit\n' \| ...` | `Nieznana komenda: 'srategies'. Wpisz 'help' żeby zobaczyć dostępne komendy.` (D-30) | PASS |
| 10 | `python scripts/regression_check.py` | `PASS: 8/8`, exit 0 (CLI-04 backwards compat) | PASS |

### One-shot path preservation

```
$ python3 sph_sim.py --strategy naive --zeta 0.5 --seed 42 --json
{
  "strategy": "naive",
  ...
}
$ python3 scripts/regression_check.py --verbose
[1/8] 01-naive-zeta-0.5 -> OK
[2/8] 02-threshold-max-phase-3 -> OK
[3/8] 03-phase-prob-default -> OK
[4/8] 04-incentive-expected-P-100 -> OK
[5/8] 05-adaptive-s-target-10 -> OK
[6/8] 06-naive-zeta-0.4-custom-env -> OK
[7/8] 07-phase-prob-custom-kappa-alpha -> OK
[8/8] 08-naive-zeta-0.75-baseline -> OK
PASS: 8/8
```

### Grep-based acceptance criteria (all 16 from Task 1 + 4 from Task 2)

| Check | Expected | Got |
|-------|----------|-----|
| `grep -c 'class SPHShell(cmd.Cmd)' sphsim/cli/repl.py` | 1 | 1 |
| `grep -c "prompt = 'sph> '" sphsim/cli/repl.py` | 1 | 1 |
| `grep -c 'def run_repl' sphsim/cli/repl.py` | 1 | 1 |
| `grep -c 'def do_help' sphsim/cli/repl.py` | 1 | 1 |
| `grep -c 'def do_exit' sphsim/cli/repl.py` | 1 | 1 |
| `grep -c 'def do_EOF' sphsim/cli/repl.py` | 1 | 1 |
| `grep -c 'def do_strategies' sphsim/cli/repl.py` | 1 | 1 |
| `grep -c 'def do_strategy' sphsim/cli/repl.py` | 1 | 1 |
| `grep -c 'def default' sphsim/cli/repl.py` | 1 | 1 |
| `grep -c 'expanduser' sphsim/cli/repl.py` | ≥1 | 1 |
| `grep -c 'sphsim_history' sphsim/cli/repl.py` | ≥1 | 1 |
| `grep -c 'FileNotFoundError' sphsim/cli/repl.py` | ≥1 | 2 |
| `grep -c 'Autorzy: Stanisław Nagórski, Mikołaj Rutkowski' sphsim/cli/repl.py` | 1 | 1 |
| `grep -c 'importlib' sphsim/cli/repl.py` | ≥1 | 4 |
| `test ! -f sphsim/cli/session.py` (D-33 YAGNI) | absent | absent |
| `test ! -f sphsim/cli/strategy_browser.py` (D-33 YAGNI) | absent | absent |
| `grep -c 'if args.interactive' sphsim/cli/main.py` | 1 | 1 |
| `grep -c 'from sphsim.cli.repl import run_repl' sphsim/cli/main.py` | 1 | 1 |
| `grep -c 'run_repl()' sphsim/cli/main.py` | 1 | 1 |
| `grep -c 'return' sphsim/cli/main.py` | ≥1 | 1 |

## Decisions Made

All `<decisions>` from `02-CONTEXT.md` applied verbatim. The three Claude's Discretion items were resolved as follows:

1. **`do_EOF` mechanics:** print `''` (empty line) then `return self.do_exit(arg)` — single source of truth for the goodbye string. Eliminates duplication; if a future phase changes the goodbye text, only `do_exit` needs editing.
2. **`strategy <name>` section order:** description → params → baseline_kpi (top-down, preferred direction per Claude's Discretion guidance). Baseline at the bottom keeps it consistent across naive (with baseline) and other 4 (without baseline — section simply omitted).
3. **Param formatting:** `  {name}: {type.__name__} = {default!r} — {desc}` chosen for one-line readability. The `!r` ensures strings show quotes (e.g. `probs: str = '0.9,0.7,0.5,0.3,0.0'`) while floats/ints render naturally (`zeta: float = 0.5`).

## Deviations from Plan

### Rule 2 — Auto-add missing critical functionality

**1. [Rule 2 - Robustness] Broaden `OSError` handling in `run_repl()` history I/O**

- **Found during:** Task 2 end-to-end verification (the `<verify>` block in Task 1 invokes `python sph_sim.py --interactive`, which only works after Task 2's wiring; running it surfaced the issue).
- **Issue:** The plan specified `except FileNotFoundError` for the read path and an unprotected `atexit.register(lambda: readline.write_history_file(...))` for the write path. In sandboxed/restricted environments (CI containers, MCP-restricted shells, read-only home directories), `readline.read_history_file` raises `PermissionError: [Errno 1] Operation not permitted` — which is a subclass of `OSError` but NOT of `FileNotFoundError`. The original spec would have crashed before reaching `Do widzenia.`, breaking every documented verify command.
- **Fix:** Added a second `except OSError: pass` clause on the read path (D-19's `FileNotFoundError` contract is preserved as a strict subset). The `atexit` write was refactored from a bare lambda into a top-level helper `_write_history_silent()` that also catches `OSError`, so a failed write never propagates into Python's atexit error stream.
- **Files modified:** `sphsim/cli/repl.py` (run_repl + new `_write_history_silent` helper, ~10 lines)
- **Commit:** `2016000`
- **Why Rule 2 (not Rule 1):** The plan's `FileNotFoundError`-only handling is technically correct for the documented contract (first-run). The fix expands the contract to cover real-world conditions the plan didn't anticipate — restricted-permission environments. Without it, no verify command works end-to-end in the agent's sandboxed shell. The change is purely additive (D-19 semantics preserved; broader OSError silently swallowed is a strict superset).

No other deviations. Plan executed exactly as written otherwise.

## Auth Gates

None.

## Known Stubs

None. Every code path is wired:
- `args.interactive == True` → `run_repl()` is invoked
- `args.interactive == False` → unchanged one-shot path (already wired in Phase 1)
- `strategies` command → reads live `STRATEGIES.keys()` + dynamic `STRATEGY_META['description']`
- `strategy <name>` → reads live `STRATEGY_META['params']` + optional `baseline_kpi`

No placeholder text, no "coming soon", no hardcoded empty data. Future phases (Phase 3 custom loader, Phase 4 compare) will add methods to `SPHShell` — that's natural growth, not a stub.

## Threat Flags

None. The change is a pure CLI/REPL surface addition:
- No new network endpoints
- No auth paths
- File access limited to `~/.sphsim_history` (text file in user's home, single-app namespace; read+write only on user's own machine)
- No schema changes at trust boundaries
- `importlib.import_module(f'sphsim.strategies.{name}')` — the f-string is gated by the prior `if name not in STRATEGIES` check, so only names from a closed allow-list reach `import_module`. (Phase 3 will add custom strategies to `STRATEGIES`, at which point the loader's separate sandbox/trust review applies — that's Phase 3 scope.)

## Requirements Closed

- **CLI-01:** `python sph_sim.py --interactive` launches the REPL with the D-21 intro banner and `sph> ` prompt.
- **CLI-02:** `help` prints the 4-command Polish list (verified via end-to-end flow).
- **CLI-03:** `exit` and Ctrl+D both terminate cleanly with `Do widzenia.` (single source of truth via `do_EOF` → `do_exit`).
- **STRAT-01:** `strategies` shows the 5-row aligned table sourced from `STRATEGY_META['description']` (single source of truth from Plan 02-01).
- **STRAT-02:** `strategy <name>` shows description + params (formatted with type + default) + baseline_kpi (only for naive — D-26 compliance verified via test 5 vs test 6).

## File Sizes

| File | Lines | Status |
|------|-------|--------|
| `sphsim/cli/repl.py` | 149 | created |
| `sphsim/cli/main.py` | 33 (was 30; +3 net after 4-line insert and existing blank line shift) | modified |

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Implement SPHShell + run_repl in sphsim/cli/repl.py | `25c6e47` |
| 2 | Wire --interactive in main.py + sandbox-robust history (Rule 2 fix) | `2016000` |

## Self-Check: PASSED

- FOUND: `sphsim/cli/repl.py` (149 lines, SPHShell + run_repl + _write_history_silent)
- FOUND: `sphsim/cli/main.py` (33 lines, with `if args.interactive` early branch)
- FOUND: commit `25c6e47` in git log (feat(02-03): implement SPHShell REPL...)
- FOUND: commit `2016000` in git log (feat(02-03): wire --interactive in main.py...)
- ABSENT (D-33 YAGNI): `sphsim/cli/session.py`, `sphsim/cli/strategy_browser.py`
- VERIFIED: 10/10 end-to-end flows from `<verification>` PASS
- VERIFIED: 20/20 grep-based acceptance criteria across both tasks PASS
- VERIFIED: `python scripts/regression_check.py` exits 0 with `PASS: 8/8` (CLI-04 backwards compat preserved per D-28)
- VERIFIED: file footprint matches plan — only `sphsim/cli/repl.py` (new) and `sphsim/cli/main.py` (4-line insert) touched
