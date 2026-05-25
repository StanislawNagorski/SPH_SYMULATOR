---
phase: 02-interactive-cli-shell
verified: 2026-05-25T18:04:11Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "REPL UX with empty-line input (WR-01 from REVIEW.md)"
    expected: "Pressing Enter on a blank prompt should be a no-op (not re-run the previous command). Currently `cmd.Cmd` default re-executes the last non-empty command — confirmed via behavioural test (`printf 'strategies\\n\\n\\nexit\\n' | python3 sph_sim.py --interactive` re-prints the strategies table 3 times). This is observably surprising UX for students."
    why_human: "Whether this is acceptable Phase 2 behaviour or a blocker is a UX-policy decision (not a contract violation). ROADMAP Success Criteria do not require emptyline to be a no-op. Project owner must decide: accept-as-is (cmd.Cmd default) OR add a 2-line override in repl.py before shipping."
  - test: "Interactive readline line-editing and history persistence on real terminal"
    expected: "User can navigate history with up/down arrows; new sessions reuse `~/.sphsim_history`; line editing (left/right, backspace) works as expected."
    why_human: "readline behaviour is terminal-coupled — automated stdin-piped tests bypass the line-editing layer entirely. Only an interactive TTY session can confirm history navigation works for the real user."
  - test: "Visual layout of intro banner and strategies table on a real 80-col terminal"
    expected: "All Polish diacritics render correctly; em-dash separator displays as `—`; 62-char `=` separators fit within an 80-column terminal; table columns align readably."
    why_human: "Encoding rendering and visual alignment depend on terminal font, locale, and column width — these cannot be verified from stdout capture alone."
---

# Phase 2: Interactive CLI shell — Verification Report

**Phase Goal:** Użytkownik może uruchomić tryb interaktywny i wewnątrz REPL'a przeglądać dostępne strategie z ich opisami, parametrami i baseline KPI.
**Verified:** 2026-05-25T18:04:11Z
**Status:** human_needed (5/5 contract truths VERIFIED; 3 UX/visual items routed to human)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `python sph_sim.py --interactive` launches REPL with Polish intro inviting user to type `help` | VERIFIED | Stdout of `echo "exit" \| python3 sph_sim.py --interactive` contains the 9-line D-21 banner verbatim (`MEDIACJA TRANSFERU PŁATNYCH USŁUG`, `v1.1 (tryb interaktywny)`, `Wpisz \`help\` żeby zobaczyć dostępne komendy.`) and the prompt is `sph> ` (no `/` prefix, D-17 honored). |
| 2 | `help` displays 4 commands (`help`, `exit`, `strategies`, `strategy <nazwa>`) with Polish descriptions | VERIFIED | `printf "help\nexit\n" \| python3 sph_sim.py --interactive` produced: `Dostępne komendy:` followed by 4 padded rows — `help` / `exit` / `strategies` / `strategy <nazwa>` — each with a Polish one-line description. Matches `repl.py:46-52`. |
| 3 | `strategies` displays a table of 5 built-in strategies (name + one-line description) | VERIFIED | `printf "strategies\nexit\n" \| ...` produced 5-row table: `naive`, `threshold`, `phase_prob`, `incentive`, `adaptive` each with em-dash separator and Polish description sourced from each module's `STRATEGY_META['description']`. Verified the names are padded to 12 chars (D-29 verbatim). |
| 4 | `strategy <name>` (for each of the 5) displays parameters, signature, and baseline KPI; `strategy naive` shows `naive --zeta 0.75 → avg_val_last100 = 92.0` | VERIFIED | All 5 strategies executed: `strategy naive` → `Opis: COMMIT z prawdopodobieństwem zeta` + `zeta: float = 0.5 — Frakcja COMMIT (0..1)` + `Baseline KPI:` + literal `naive --zeta 0.75 → avg_val_last100 = 92.0`. `strategy threshold/phase_prob/incentive/adaptive` each show their `Opis:` + `Parametry:` line and DO NOT show `Baseline KPI:` (D-26 — only naive has baseline). |
| 5 | `exit` or `Ctrl+D` ends the session with a clean goodbye | VERIFIED | `echo "exit" \| ...` → final stdout line is `Do widzenia.` and process exits 0. `printf '' \| ...` (EOF / Ctrl+D simulated) → blank line then `Do widzenia.` and process exits 0. `do_EOF` delegates to `do_exit` via `return self.do_exit(arg)` (single source of truth, `repl.py:61-65`). |

**Score:** 5/5 ROADMAP Success Criteria verified.

### Plan-Level Must-Have Truths

All four PLAN.md `must_haves.truths` lists were checked against the codebase. No discrepancies found; details below.

| Source plan | Must-have truth | Status | Evidence |
|---|---|---|---|
| 02-01 | Each of 5 strategy files exports STRATEGY_META with exactly 3 keys (`description`, `params`, `baseline_kpi`) | VERIFIED | `grep -c "STRATEGY_META = {" sphsim/strategies/*.py` → 1 for each of the 5 files. Inline Python introspection confirmed `set(M.keys()) == {'description','params','baseline_kpi'}` for all five. |
| 02-01 | Only naive has `baseline_kpi.avg_val_last100 = 92.0` as float | VERIFIED | `python3 -c "...naive STRATEGY_META..."` → `{'invocation': 'naive --zeta 0.75', 'avg_val_last100': 92.0, 'source': '...'}`, `type=float`, value `92.0`. |
| 02-01 | Other 4 strategies have `baseline_kpi = None` | VERIFIED | Iterated all 4 modules; assertion `STRATEGY_META['baseline_kpi'] is None` held for `threshold`, `phase_prob`, `incentive`, `adaptive`. |
| 02-01 | STRATEGY_META `params` mirror argparse defaults exactly | VERIFIED | `python3 -m unittest tests.test_strategy_meta_consistency -v` → `OK` (1 test, 20 assertions: dest + type + default + description hygiene × 5 strategies). |
| 02-01 | Strategy functions untouched (Phase 1 verbatim preserved) | VERIFIED | `python3 scripts/regression_check.py --verbose` → `PASS: 8/8`. All 8 baseline fixtures match byte-for-byte. |
| 02-02 | `--interactive` is in `add_mutually_exclusive_group(required=True)` with `--strategy` | VERIFIED | `sphsim/cli/args.py:38-42`: `mutex = p.add_mutually_exclusive_group(required=True); mutex.add_argument('--interactive', action='store_true', ...); mutex.add_argument('--strategy', choices=..., ...)`. |
| 02-02 | Mutex violations error correctly | VERIFIED | `python3 sph_sim.py --interactive --strategy naive` → exit 2 with `argument --strategy: not allowed with argument --interactive`. `python3 sph_sim.py` (no flags) → exit 2 with `one of the arguments --interactive --strategy is required`. |
| 02-02 | All Phase 1 invocations still parse + run identically | VERIFIED | `regression_check.py` PASS 8/8. |
| 02-02 | Docstring updated to `Autorzy: Stanisław Nagórski, Mikołaj Rutkowski` (plural) | VERIFIED | `grep -c "Autorzy: Stanisław Nagórski, Mikołaj Rutkowski" sphsim/cli/args.py` → 1. |
| 02-03 | REPL uses `cmd.Cmd` stdlib (no new dependencies) | VERIFIED | `repl.py:15-21` imports only stdlib (`cmd`, `importlib`, `os`, `readline`, `atexit`) + `from sphsim.strategies import STRATEGIES`. No `requirements.txt` change. |
| 02-03 | `readline` history with silent FileNotFoundError on first run | VERIFIED | `repl.py:140-145` catches both `FileNotFoundError` (D-19) and broader `OSError` (Rule 2 sandbox robustness deviation, documented in 02-03-SUMMARY.md). |
| 02-03 | `main.py` early branch `if args.interactive: run_repl(); return` before one-shot code | VERIFIED | `sphsim/cli/main.py:11-14` exactly matches the spec; lazy import via `from sphsim.cli.repl import run_repl` inside the branch. |
| 02-03 | YAGNI: no `session.py`, `strategy_browser.py`, etc. (D-33) | VERIFIED | `ls sphsim/cli/session.py` → `No such file or directory`. Same for `strategy_browser.py`. |
| 02-04 | Test file uses only stdlib (`unittest`), no pytest | VERIFIED | `grep -c 'import pytest' tests/test_strategy_meta_consistency.py` → 0. Imports: `unittest`, `importlib`, `argparse`, `os`, `sys`, `unittest.mock.patch` — all stdlib. |
| 02-04 | Test runnable via `python -m unittest tests.test_strategy_meta_consistency` AND direct `python tests/test_strategy_meta_consistency.py` | VERIFIED | Both invocations exited 0 (sys.path bootstrap at `test_strategy_meta_consistency.py:27-29` makes direct execution work). |
| 02-04 | Test fails with diagnostic message on argparse↔STRATEGY_META drift | VERIFIED (per Plan 04 SUMMARY's sanity-check) | Plan 04 SUMMARY records that mutating `naive.py` STRATEGY_META `zeta` default `0.5 → 0.6` produced the exact specified diagnostic `AssertionError: 0.5 != 0.6 : naive/zeta: STRATEGY_META default=0.6, argparse default=0.5`. Source was reverted (test currently passes). |

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `sphsim/strategies/naive.py` | STRATEGY_META with baseline_kpi populated | VERIFIED | 22 lines; STRATEGY_META at line 12 with `{description, params, baseline_kpi}`; baseline_kpi = `{'invocation': 'naive --zeta 0.75', 'avg_val_last100': 92.0, 'source': '...'}`. Wired: imported transitively via `sphsim.strategies.__init__.STRATEGIES`. |
| `sphsim/strategies/threshold.py` | STRATEGY_META, baseline_kpi=None | VERIFIED | 17 lines; STRATEGY_META at line 11; baseline_kpi=None. |
| `sphsim/strategies/phase_prob.py` | STRATEGY_META, baseline_kpi=None | VERIFIED | 21 lines; STRATEGY_META at line 15; baseline_kpi=None. |
| `sphsim/strategies/incentive.py` | STRATEGY_META, baseline_kpi=None | VERIFIED | 27 lines; STRATEGY_META at line 21; baseline_kpi=None. |
| `sphsim/strategies/adaptive.py` | STRATEGY_META, baseline_kpi=None | VERIFIED | 28 lines; STRATEGY_META at line 22; baseline_kpi=None. |
| `sphsim/cli/args.py` | parse_args with mutex group + author plural | VERIFIED | 60 lines; mutex group at lines 38-42; docstring author plural line 4. |
| `sphsim/cli/repl.py` | SPHShell + run_repl, ≥80 lines | VERIFIED | 149 lines (exceeds min_lines:80). All 9 required methods present: `do_help`, `do_exit`, `do_EOF`, `do_strategies`, `do_strategy`, `default` + `intro`, `prompt`, `run_repl`. |
| `sphsim/cli/main.py` | Early `if args.interactive` branch | VERIFIED | 33 lines; branch at 11-14 with lazy import + early return. |
| `tests/test_strategy_meta_consistency.py` | TestStrategyMetaConsistency unittest, ≥50 lines | VERIFIED | 172 lines (exceeds min_lines:50). Single TestCase with monkey-patch capture + per-strategy assertions. |
| `tests/__init__.py` | Empty package marker | VERIFIED | Present, 0 bytes (intentional). |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `sphsim/strategies/*.py` STRATEGY_META | `sphsim/cli/args.py` argparse defaults | Mirrored 4-tuples | WIRED | `tests/test_strategy_meta_consistency.py` codifies this invariant; passes 20/20 assertions. |
| `sphsim/strategies/naive.py` | `PROJECT.md` baseline | `STRATEGY_META['baseline_kpi']['avg_val_last100'] = 92.0` | WIRED | Visible in REPL output `naive --zeta 0.75 → avg_val_last100 = 92.0`. |
| `sphsim/cli/args.py` mutex group | `sphsim/cli/main.py` early branch | `args.interactive` boolean | WIRED | `args.py:39` sets `action='store_true'`; `main.py:11` reads `args.interactive` and dispatches; mutex enforced (exit 2 on violation). |
| `sphsim/cli/main.py` | `sphsim/cli/repl.run_repl` | Lazy import inside `if args.interactive` | WIRED | `main.py:12 from sphsim.cli.repl import run_repl`; one-shot path imports never trigger readline/cmd. |
| `sphsim/cli/repl.py` `do_strategy` | `sphsim.strategies.<name>.STRATEGY_META` | `importlib.import_module` | WIRED | `repl.py:94 mod = importlib.import_module(f'sphsim.strategies.{name}')` → reads `meta = mod.STRATEGY_META`. Verified by observing live REPL output for all 5 strategies. |
| `sphsim/cli/repl.py` `do_strategies` | STRATEGIES.keys() + STRATEGY_META | Iteration + dynamic import | WIRED | `repl.py:71-75` iterates `STRATEGIES.keys()`; output table proves 5 rows pulled from live registry + per-module STRATEGY_META. |
| `sphsim/cli/repl.py` | `~/.sphsim_history` | `readline.read_history_file` / `write_history_file` | WIRED | `repl.py:24, 140-149` — file path expanded, atexit-registered writer, OSError-tolerant. |

### Data-Flow Trace (Level 4)

The REPL renders dynamic data; verifying data actually flows from STRATEGY_META → user output:

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `repl.py` `do_strategies` table | `description` per row | `mod.STRATEGY_META['description']` via `importlib.import_module` | YES — 5 rows, 5 Polish descriptions printed live (not hardcoded; verified by reading STRATEGY_META dicts and observing matching REPL output) | FLOWING |
| `repl.py` `do_strategy <naive>` baseline section | `baseline['invocation']`, `baseline['avg_val_last100']` | `naive.py STRATEGY_META['baseline_kpi']` (a populated dict) | YES — literal `92.0` from `naive.py:19` (float, not string) renders as `avg_val_last100 = 92.0` in REPL stdout | FLOWING |
| `repl.py` `do_strategy <threshold/phase_prob/incentive/adaptive>` baseline section | (skipped) | `STRATEGY_META['baseline_kpi'] is None` → no section printed | YES — D-26 honored; `Baseline KPI:` header absent from output (confirmed for all 4 non-naive strategies) | FLOWING (correctly skipped) |
| `repl.py` `do_strategy <name>` params lines | `param_name`, `param_type.__name__`, `default`, `desc` | `STRATEGY_META['params']` tuples | YES — verified `zeta: float = 0.5 — Frakcja COMMIT (0..1)` for naive; `probs: str = '0.9,0.7,0.5,0.3,0.0' — P(COMMIT) per faza, po przecinku` for phase_prob (quoted via `!r` formatter); all 5 strategies render their param tuple | FLOWING |

### Behavioral Spot-Checks

| # | Behavior | Command | Result | Status |
|---|---|---|---|---|
| 1 | Help command lists 4 commands in Polish | `printf "help\nexit\n" \| python3 sph_sim.py --interactive` | Stdout contains all 4 command names and 4 Polish descriptions | PASS |
| 2 | Strategies table sources from STRATEGY_META | `printf "strategies\nexit\n" \| python3 sph_sim.py --interactive` | Stdout shows 5 padded rows with em-dash + Polish descriptions matching each module's STRATEGY_META['description'] | PASS |
| 3 | strategy naive shows literal baseline `naive --zeta 0.75 → avg_val_last100 = 92.0` | `printf "strategy naive\nexit\n" \| python3 sph_sim.py --interactive \| grep "avg_val_last100 = 92.0"` | Match found | PASS |
| 4 | strategy threshold has NO `Baseline KPI:` section (D-26) | `printf "strategy threshold\nexit\n" \| python3 sph_sim.py --interactive \| grep -c "Baseline KPI:"` | 0 matches | PASS |
| 5 | Unknown strategy returns D-31 polite Polish error | `printf "strategy random\nexit\n" \| ...` | Stdout: `Strategia 'random' nie istnieje. Dostępne: naive, threshold, phase_prob, incentive, adaptive.` | PASS |
| 6 | Missing argument returns D-32 usage hint | `printf "strategy\nexit\n" \| ...` | Stdout: `Użycie: strategy <nazwa>. Wpisz 'strategies' żeby zobaczyć listę.` | PASS |
| 7 | Unknown command returns D-30 error | `printf "srategies\nexit\n" \| ...` | Stdout: `Nieznana komenda: 'srategies'. Wpisz 'help' żeby zobaczyć dostępne komendy.` | PASS |
| 8 | `exit` produces `Do widzenia.` and clean exit | `echo "exit" \| python3 sph_sim.py --interactive; echo $?` | Stdout ends `Do widzenia.`; exit code 0 | PASS |
| 9 | Ctrl+D (EOF) produces `Do widzenia.` and clean exit | `printf '' \| python3 sph_sim.py --interactive; echo $?` | Stdout ends with empty line + `Do widzenia.`; exit code 0 | PASS |
| 10 | Mutex group rejects `--interactive --strategy X` | `python3 sph_sim.py --interactive --strategy naive; echo $?` | Exit code 2, stderr: `argument --strategy: not allowed with argument --interactive` | PASS |
| 11 | Mutex group rejects no-flag invocation | `python3 sph_sim.py; echo $?` | Exit code 2, stderr: `one of the arguments --interactive --strategy is required` | PASS |
| 12 | One-shot path unaffected (CLI-04 backwards compat) | `python3 sph_sim.py --strategy naive --zeta 0.5 --seed 42 --json` | Valid JSON with `"strategy": "naive"`, exit 0 | PASS |
| 13 | Phase 1 regression suite (8 fixtures) | `python3 scripts/regression_check.py --verbose` | `PASS: 8/8`, exit 0 | PASS |
| 14 | STRATEGY_META ↔ argparse invariant | `python3 -m unittest tests.test_strategy_meta_consistency -v` | `Ran 1 test in 0.003s — OK`, exit 0 | PASS |
| 15 | Test runs as direct script too | `python3 tests/test_strategy_meta_consistency.py` | `OK`, exit 0 | PASS |

### Requirements Coverage

| Requirement | Source plan | Description | Status | Evidence |
|---|---|---|---|---|
| CLI-01 | 02-02, 02-03 | Użytkownik może uruchomić tryb interaktywny przez `python sph_sim.py --interactive` (REPL) | SATISFIED | Spot-check #1, #8, #9; mutex correctly required (#10, #11); `args.py:39 --interactive` + `main.py:11 if args.interactive: run_repl(); return`. |
| CLI-02 | 02-03 | Użytkownik może wpisać `/help` i otrzymać listę wszystkich komend z opisem po polsku — **D-17 override removes `/`** | SATISFIED (D-17 override) | Spot-check #1: `help` (no slash, per D-17) prints 4 commands in Polish. ROADMAP SC2 explicitly waives `/` prefix. |
| CLI-03 | 02-03 | Użytkownik może wpisać `/exit` lub użyć `Ctrl+D` — **D-17 override removes `/`** | SATISFIED (D-17 override) | Spot-checks #8, #9. Both `exit` and EOF produce `Do widzenia.` and exit 0. |
| STRAT-01 | 02-01, 02-03 | `/strategies` shows 5 built-in strategies — **D-17 override removes `/`** | SATISFIED (D-17 override) | Spot-check #2. Live registry; per-row source from STRATEGY_META['description']. |
| STRAT-02 | 02-01, 02-03, 02-04 | `/strategy <name>` shows params, signature, baseline KPI — **D-17 override removes `/`** | SATISFIED (D-17 override) | Spot-checks #3, #4. Plan 04's automated test (#14) guarantees no drift between displayed values and argparse defaults. |

**Orphan check:** REQUIREMENTS.md Phase 2 distribution lists exactly `CLI-01, CLI-02, CLI-03, STRAT-01, STRAT-02` (5 IDs). All 5 are claimed by at least one plan's `requirements:` field (02-01: STRAT-01, STRAT-02; 02-02: CLI-01; 02-03: all 5; 02-04: STRAT-02). No orphans, no extras.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| (none) | (none) | TBD/FIXME/XXX | – | grep across all 8 Phase-2 modified files returned 0 hits |
| (none) | (none) | TODO/HACK/PLACEHOLDER | – | grep across all 8 Phase-2 modified files returned 0 hits |
| (none) | (none) | placeholder/coming soon/not yet implemented | – | grep across all 8 files returned 0 hits |
| `repl.py` (broader) | – | Empty return / stub | – | Every `do_*` method has real implementation: prints to stdout, dispatches via importlib, returns boolean as required by `cmd.Cmd` |
| `main.py` | – | Hardcoded data | – | `args.interactive` reads real argparse boolean; `run_repl()` invokes real cmdloop; no static returns |

No debt markers. No stubs. All wiring carries real data.

### Probe Execution

| Probe | Command | Result | Status |
|---|---|---|---|
| `scripts/regression_check.py` (Phase 1 backwards-compat oracle, explicitly required by the verifier brief) | `python3 scripts/regression_check.py --verbose` | All 8 fixtures OK, `PASS: 8/8`, exit 0 | PASS |
| `tests.test_strategy_meta_consistency` (STRATEGY_META ↔ argparse invariant) | `python3 -m unittest tests.test_strategy_meta_consistency -v` | `Ran 1 test in 0.003s — OK`, exit 0 | PASS |

No additional probes declared by PLAN/SUMMARY files. The project does not use the conventional `scripts/*/tests/probe-*.sh` layout.

### Human Verification Required

(Detailed format for project owner — these items do NOT block phase status but should be reviewed before students consume the build.)

#### 1. emptyline UX (WR-01 from code review)

**Test:** Run interactive REPL, type `strategies`, press Enter 3× on empty prompt.
**Expected (current behaviour):** Strategies table re-prints 3 more times (cmd.Cmd default — last command re-runs on blank input).
**Why human:** This is observably surprising — students may interpret it as a hang or loop. ROADMAP Success Criteria don't mandate emptyline behaviour, and 02-CONTEXT.md doesn't discuss it. A 2-line fix (`def emptyline(self): return False`) would make blank input a no-op. Decision is UX policy, not a contract violation. **Recommended:** apply the fix before Phase 3 (where students will be exploring the REPL more heavily).

#### 2. Interactive terminal session

**Test:** Run `python sph_sim.py --interactive` in a real terminal. Use up/down arrow keys to navigate history. Quit, restart, verify history persists.
**Expected:** Arrow-key history navigation works; `~/.sphsim_history` is created/updated; previous-session entries appear in current session.
**Why human:** Automated stdin-piped tests bypass the readline line-editing layer entirely. Only an interactive TTY can confirm history navigation, editing, and Ctrl+C behaviour.

#### 3. Visual rendering of Polish + banner

**Test:** Open a real terminal, run `python sph_sim.py --interactive`, observe banner.
**Expected:** All Polish diacritics render (`ą ł ó ś ż ń ę`); em-dash `—` displays as a single horizontal bar (not `??` or `—`); 62-char `=` separators fit cleanly within 80 columns.
**Why human:** Encoding/font rendering is terminal-dependent and can't be verified from captured stdout alone.

### Gaps Summary

No contract gaps. All 5 ROADMAP Success Criteria are observably true in the codebase. All 5 phase-mapped requirements are satisfied (with the D-17 override on `/` prefix, which is documented in the ROADMAP SC text and the phase CONTEXT). Backwards-compat oracle (regression_check.py) remains green at 8/8. The D-25 invariant is codified as automated test and passes 20 assertions. No debt markers, no TODOs, no stubs, no orphaned artifacts, no extra modules (D-33 YAGNI honored).

The three items routed to `human_needed` are all UX/visual quality questions that automated grep + stdin-piped tests cannot answer:
1. **WR-01 emptyline behaviour** — code review surfaced this; observably true via behavioural test; UX-policy decision required.
2. **Interactive readline session** — terminal-coupled, not stdin-pipeable.
3. **Visual rendering of Polish/banner** — terminal-font-coupled.

None of these block Phase 3 from starting, since Phase 3's plans will touch the REPL anyway (custom strategy loader adds `do_custom` to SPHShell), and the WR-01 fix can be folded into that work.

---

_Verified: 2026-05-25T18:04:11Z_
_Verifier: Claude (gsd-verifier)_
