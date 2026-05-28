# Phase 8: Documentation + Interactive Tutorial — Research

**Researched:** 2026-05-28
**Domain:** cmd.Cmd state machine / Python tutorial UX / Polish markdown documentation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 (form factor):** REPL `tutorial` command inside existing `cmd.Cmd` SPHShell — NOT external paste-back script.
- **D-02 (CLI parity):** `python sph_sim.py --tutorial` enters REPL already in tutorial mode. Mutually exclusive with `--strategy`/`--custom`/`--batch`/`--compare-agent` (extend 4-way mutex to 5-way).
- **D-03 (execution model):** User TYPES each command themselves at `sph>` prompt — tutorial does NOT auto-execute.
- **D-04 (detection):** After user runs command, tutorial verifies by (a) shape-matching command and (b) inspecting simulation result. On success prints `✓ zaliczone — krok N/M`.
- **D-05 (controls):** Tutorial-internal commands: `skip`, `back`, `repeat`, `exit` (no `/` prefix, per Phase 2 D-17).
- **D-06 (no persistence):** Tutorial state in-memory only. Re-entering `tutorial` starts from step 1.
- **D-08 (REPL state persists):** Custom strategy loaded in step 4 remains in `STRATEGIES` for step 5+.
- **D-09 (8 steps target, ≤10 cap):** Golden path: baseline → browse strategies → run strategy → custom load → compare agent → env override → inspect report → batch.
- **D-10 (tutorial reports dir):** `./reports/tutorial-<timestamp>/step-N-<topic>/`. Requires `write_report()` / `write_batch_report()` to accept optional report-dir override (backwards-compat).
- **D-11 (PRZEWODNIK.md structure):** Lead → Quickstart → Walkthrough (7 phases) → Reference → Theory appendix.
- **D-12 (single source for examples):** All command examples verbatim from `07.1-comprehensive-uat/08-UAT.md` and `scripts/verify_phase*.sh`, each annotated `# Z 08-UAT.md test #N`.
- **D-13 (theory depth):** ~1 page summary in PRZEWODNIK.md; deep math stays in `PROMPT_DLA_AGENTA.txt` + `Raport.pdf`.
- **D-14 (canonical artefacts):** `docs/assets/decision_distribution_naive.png`, `docs/assets/kpi_timeseries_naive.png`, `docs/assets/batch_aggregate_naive.png`, all from `--seed 42`.

### Claude's Discretion

- **D-07 (wrong-input handling):** Pick sensible policy. Research recommends: hint on mismatch, allow `skip` after 3 hints, never auto-advance (see §D-07 Recommendation).
- Polish tone: informal but respectful (project leans "Wpisz", not "Proszę wpisać").
- Exact step count: 8 target, 9–10 acceptable, hard cap 10.
- Where `tutorial` appears in `do_help` — alongside other commands.
- Whether to add root `README.md` — optional, not in scope.

### Deferred Ideas (OUT OF SCOPE)

- External paste-back tutorial script.
- Layered tutorial with optional "advanced" branches.
- Cross-session progress persistence.
- Full-sweep `--tutorial-deep`.
- GitHub Pages / external doc hosting.
- Root README.md (planner's discretion).
- i18n / English PRZEWODNIK.md.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| (no new REQ-IDs) | Phase 8 exercises all 7 REQ categories (STRAT, CLI, AGENT, ENV, REPORT, PLOT, BATCH) via tutorial golden path + PRZEWODNIK.md examples | D-09 golden path maps each step to ≥1 REQ category; verified commands from 08-UAT.md all pass |

</phase_requirements>

---

## Summary

Phase 8 delivers two artefacts: `docs/PRZEWODNIK.md` (Polish written guide) and REPL `tutorial` mode + `--tutorial` CLI flag. All required infrastructure exists and is in good shape: `cmd.Cmd`'s `precmd`/`postcmd` hooks cleanly support tutorial state machine without breaking existing commands; `_resolve_report_dir()` already has a `base` parameter but `write_report()` does not yet pass it through (small wiring gap for D-10); `docs/` directory does not yet exist; all three PNG artefacts are byte-deterministic across runs with `--seed 42` (verified by MD5 comparison). The biggest implementation risk is the D-10 report-dir override — the correct approach is adding a `report_dir_override` keyword argument to `write_report()` and `write_batch_report()` that bypasses `_resolve_report_dir()` entirely, not changing `_resolve_report_dir()` itself.

**Primary recommendation:** Implement tutorial as a `TutorialFlow` dataclass held in `self._tutorial_state` on `SPHShell`; intercept tutorial control words (`skip`/`back`/`repeat`) in `precmd()`; inspect step results via a `self._last_sim_result` attribute set at the end of `do_run`, `do_compare`, and `do_batch`; wire `--tutorial` flag as the 5th mutex member + a 4th early branch in `main()`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Tutorial state machine | REPL (SPHShell) | — | Lives inside `cmd.Cmd` cmdloop; all state is in-process |
| Tutorial step verification | REPL postcmd hook | REPL _last_sim_result | postcmd fires after every do_* dispatch; can inspect result |
| Tutorial control interception | REPL precmd hook | — | precmd fires before dispatch; returning '' short-circuits without calling do_* |
| --tutorial CLI flag | CLI args.py / main.py | — | Extends existing 5-way mutex; wires to run_repl(start_in_tutorial=True) |
| Tutorial report directories | report/__init__.py | REPL tutorial_state | write_report needs report_dir_override kwarg; tutorial_state computes path |
| PRZEWODNIK.md | docs/ (new) | — | Static markdown file committed to repo |
| docs/assets/ PNG generation | scripts/generate_tutorial_assets.sh | report/plots.py | Run with --seed 42; byte-deterministic (verified) |
| verify_phase8.sh exit gate | scripts/ | — | Follows check() pattern from verify_phase{3,4,5,6,7}.sh |

---

## Standard Stack

### Core (all stdlib + existing deps — no new packages)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `cmd.Cmd` | stdlib | Tutorial state machine host | Already used; `precmd`/`postcmd`/`cmdqueue` give clean hooks |
| `dataclasses` | stdlib 3.7+ | `TutorialFlow` state object | Typed, no boilerplate |
| `pathlib.Path` | stdlib | Tutorial report dir path construction | Already used throughout |
| `datetime` | stdlib | Tutorial session timestamp (`tutorial-<ts>/`) | Already used in `_timestamp()` |

### No New Dependencies

Phase 8 adds zero new `pip` packages. Existing deps (matplotlib, numpy, scipy) already in `requirements.txt` from Phase 7.

---

## Package Legitimacy Audit

**Not applicable** — Phase 8 installs no new packages.

---

## Architecture Patterns

### System Architecture Diagram

```
User input (TTY or piped stdin)
        │
        ▼
  sph_sim.py --interactive / --tutorial
        │
        ▼
  sphsim/cli/main.py
    early branch: if args.tutorial → run_repl(start_in_tutorial=True)
        │
        ▼
  sphsim/cli/repl.py :: SPHShell.cmdloop()
        │
        ├── precmd(line) ──── if in_tutorial AND line in ('skip','back','repeat')
        │       │                   → handle control, return '' (short-circuit)
        │       │             else
        │       │                   → return line unchanged (normal dispatch)
        │       ▼
        ├── onecmd(line) → do_run / do_compare / do_batch / do_tutorial / …
        │       │           └── sets self._last_sim_result = res
        │       ▼
        └── postcmd(stop, line) ─── if in_tutorial AND line is a "checkable" command
                │                       → self._tutorial_state.check_step(line, self._last_sim_result)
                │                       → if pass: print ✓ + advance step
                │                       → if fail: print hint (D-07)
                ▼
        cmd.Cmd returns stop (False = continue, True = quit)
```

### Recommended Project Structure

```
docs/
├── PRZEWODNIK.md          # Polish user guide (new)
└── assets/
    ├── decision_distribution_naive.png  # from naive --zeta 0.75 --seed 42
    ├── kpi_timeseries_naive.png         # same source
    └── batch_aggregate_naive.png        # from batch naive --seeds 5 (seeds 1..5)

scripts/
└── verify_phase8.sh       # exit gate (new, follows verify_phase7.sh pattern)

sphsim/
└── cli/
    ├── repl.py            # TutorialFlow + do_tutorial + modified do_run/compare/batch
    ├── args.py            # --tutorial as 5th mutex member
    └── main.py            # 4th early branch for --tutorial

sphsim/
└── report/
    └── __init__.py        # write_report + write_batch_report: add report_dir_override kwarg
```

### Pattern 1: Tutorial State Machine in SPHShell

**What:** A `TutorialFlow` dataclass stored as `self._tutorial_state` on `SPHShell` (None when inactive). `precmd` intercepts control words; `postcmd` verifies step completion after real commands.

**When to use:** Any tutorial-internal navigation (`skip`, `back`, `repeat`, `exit`) before the regular dispatch table.

```python
# Source: verified by running cmd.Cmd experiments in this session [VERIFIED: local test]
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

@dataclass
class TutorialFlow:
    step: int = 1                          # current step (1-based)
    total: int = 8                         # configurable; D-09 target
    session_ts: str = field(default_factory=lambda: datetime.now().strftime('%Y%m%d-%H%M%S'))
    hint_count: int = 0                    # hints shown for current step (D-07)
    MAX_HINTS: int = 3                     # after this, suggest `skip`

    @property
    def base_report_dir(self) -> Path:
        """D-10: ./reports/tutorial-<ts>/ — one dir per tutorial session."""
        return Path('reports') / f'tutorial-{self.session_ts}'

    def step_report_dir(self, topic: str) -> Path:
        """D-10: ./reports/tutorial-<ts>/step-N-<topic>/"""
        return self.base_report_dir / f'step-{self.step}-{topic}'
```

**Integration point in `SPHShell.__init__`:**

```python
# Add to SPHShell.__init__ (after super().__init__(...)):
self._tutorial_state: Optional[TutorialFlow] = None
self._last_sim_result: Optional[dict] = None  # set by do_run/do_compare/do_batch
```

### Pattern 2: precmd Intercept for Tutorial Controls

**What:** Override `precmd` to catch `skip`/`back`/`repeat`/`exit` when `self._tutorial_state` is active. Return `''` (empty string) to short-circuit dispatch without calling any `do_*` method.

**Verified:** `precmd` returning `''` causes `cmd.Cmd` to call `emptyline()` (which is already a no-op in `SPHShell` per standard pattern), then `postcmd`. No `do_*` is invoked. [VERIFIED: local test]

```python
# Source: [VERIFIED: local test — precmd returning '' skips dispatch cleanly]
def precmd(self, line):
    """Override: intercept tutorial control words before normal dispatch."""
    if self._tutorial_state is None:
        return line                        # not in tutorial — pass through unchanged

    stripped = line.strip()
    ts = self._tutorial_state

    if stripped == 'skip':
        step = ts.step
        ts.hint_count = 0
        if ts.step < ts.total:
            ts.step += 1
            print(f'⤼ pominięto — krok {step}/{ts.total}')
            self._show_tutorial_step()
        else:
            print(f'⤼ pominięto — krok {step}/{ts.total}. Tutorial zakończony.')
            self._tutorial_state = None
        return ''                          # short-circuit: no do_* call

    elif stripped == 'back':
        if ts.step > 1:
            ts.step -= 1
            ts.hint_count = 0
            print(f'↩ cofnięto do kroku {ts.step}/{ts.total}')
            self._show_tutorial_step()
        else:
            print('Już jesteś na pierwszym kroku.')
        return ''

    elif stripped == 'repeat':
        self._show_tutorial_step()
        return ''

    elif stripped == 'exit':
        print(f'Tutorial opuszczony na kroku {ts.step}/{ts.total}. '
              f'Stan REPL zachowany (załadowane strategie, historia).')
        self._tutorial_state = None
        return ''                          # exit tutorial, NOT the REPL

    return line                            # all other input: normal dispatch
```

**Critical note on `exit` in tutorial vs `exit` in REPL:** The tutorial `exit` (intercepted in `precmd`) drops out of tutorial mode and returns to bare REPL. The REPL `exit` (handled by `do_exit`) ends the session entirely. These are distinct: tutorial `precmd` catches `exit` first when `self._tutorial_state` is active, so tutorial `exit` never reaches `do_exit`. This is the correct behavior per D-05 ("leave tutorial, drop back to bare REPL"). [ASSUMED — the exact sentinel word 'exit' being used for both tutorial-escape and REPL-exit could cause confusion; consider using `quit` for tutorial-exit instead. Flagged for planner to confirm.]

### Pattern 3: postcmd for Step Verification

**What:** Override `postcmd` to check whether the user's last command satisfied the current tutorial step requirement. Fires after every `do_*` dispatch (including when the simulation ran).

```python
# Source: [VERIFIED: local test — postcmd fires after do_run with self._last_sim_result set]
def postcmd(self, stop, line):
    """Override: check tutorial step completion after every command."""
    if self._tutorial_state is None or stop:
        return stop

    ts = self._tutorial_state
    result = self._last_sim_result        # may be None if command didn't produce sim result

    if result is not None and self._check_tutorial_step(ts.step, line.strip(), result):
        step = ts.step
        ts.hint_count = 0
        self._last_sim_result = None      # consume result
        if ts.step < ts.total:
            ts.step += 1
            print(f'\n✓ zaliczone — krok {step}/{ts.total}')
            self._show_tutorial_step()
        else:
            print(f'\n✓ zaliczone — krok {step}/{ts.total}. Tutorial ukończony!')
            self._tutorial_state = None
    elif result is not None:
        # Command ran but didn't satisfy step — show hint (D-07)
        ts.hint_count += 1
        self._last_sim_result = None      # consume so we don't re-trigger
        if ts.hint_count <= ts.MAX_HINTS:
            self._show_step_hint(ts.step)
        else:
            print(f'Wskazówka: Wpisz `skip` żeby przejść dalej.')

    return stop
```

### Pattern 4: Setting _last_sim_result in do_run / do_compare / do_batch

**What:** At the end of a successful simulation in `do_run`, add one line: `self._last_sim_result = res`. Same for `do_compare` (store `res_combined`) and `do_batch` (store `{'aggregate': aggregate, 'per_seed': per_seed_results}`). This is a backwards-compatible addition — existing behavior is unchanged; the new attribute is only consulted by `postcmd` when `self._tutorial_state` is not None.

**Exact insertion points:**

- `do_run` (repl.py line ~219): after `res = sim.run()`, before `fake_args = argparse.Namespace(...)`  
  Add: `self._last_sim_result = res`

- `do_compare` (repl.py line ~295): after `res_combined = {...}` is assembled  
  Add: `self._last_sim_result = res_combined`

- `do_batch` (repl.py line ~399): after `per_seed_results, aggregate = run_batch(...)`  
  Add: `self._last_sim_result = {'aggregate': aggregate, 'per_seed': per_seed_results}`

### Pattern 5: do_tutorial Entry Method

**What:** `do_tutorial(arg)` is the entry point. It initializes `TutorialFlow` on `self._tutorial_state`, prints the opening banner, and shows step 1.

```python
def do_tutorial(self, arg):
    """Uruchom interaktywny tutorial v1.1 (~8 kroków, ≤15 min)."""
    if self._tutorial_state is not None:
        print('Tutorial już jest aktywny. Wpisz `repeat` żeby zobaczyć bieżący krok, '
              '`exit` żeby wyjść.')
        return

    self._tutorial_state = TutorialFlow()
    print(
        '\n'
        '══════════════════════════════════════════════════════════\n'
        '  INTERAKTYWNY TUTORIAL SPH SYMULATORA v1.1\n'
        '  ~8 kroków, ≤15 minut\n'
        '  Sterowanie: skip | back | repeat | exit\n'
        '  `exit` wraca do REPL (stan zachowany), nie kończy sesji.\n'
        '══════════════════════════════════════════════════════════'
    )
    self._show_tutorial_step()
```

### Pattern 6: D-10 Report-Dir Override in write_report

**What:** Add `report_dir_override: Path | None = None` keyword argument to `write_report()` and `write_batch_report()`. When set, bypass `_resolve_report_dir()` entirely and use the provided path directly (with `mkdir(parents=True, exist_ok=True)`). Default remains `None` → existing behavior unchanged.

**Critical finding:** `_resolve_report_dir(base=Path)` already exists and accepts a `base` parameter, but `write_report()` calls `_resolve_report_dir()` without passing `base`. The tutorial does NOT want `_resolve_report_dir`'s inner-timestamp behavior (which would create `reports/tutorial-<ts>/<inner-ts>/` instead of `reports/tutorial-<ts>/step-N-<topic>/`). Use `report_dir_override` to pass the fully-resolved path directly. [VERIFIED: local code inspection]

```python
# In sphsim/report/__init__.py write_report signature change:
def write_report(args, res, params, K1, *, mode='single', report_dir_override=None):
    ...
    try:
        if report_dir_override is not None:
            report_dir = Path(report_dir_override)
            report_dir.mkdir(parents=True, exist_ok=True)
        else:
            try:
                report_dir = _resolve_report_dir()      # unchanged default path
            except OSError as e:
                ...
                return None
```

**Tutorial caller pattern (in `do_run` when tutorial active):**

```python
# In do_run, when self._tutorial_state is not None:
topic_slug = _STEP_TOPICS[self._tutorial_state.step]  # e.g. 'baseline', 'custom', etc.
override = self._tutorial_state.step_report_dir(topic_slug)
report_dir = write_report(fake_args, res, params, DEFAULT_K1, mode='single',
                          report_dir_override=override)
```

### Anti-Patterns to Avoid

- **Modifying `_resolve_report_dir` to accept a "use-as-final" flag:** Over-engineering. Just add `report_dir_override` to the public API.
- **Auto-executing commands in tutorial mode:** Violates D-03. Tutorial only SHOWS the command; user types it.
- **Catching `exit` in `do_exit` to distinguish tutorial-exit vs REPL-exit:** Wrong layer. `precmd` catches `exit` first when `_tutorial_state` is active; `do_exit` never fires for tutorial-exit.
- **Using a separate `cmd.Cmd` subclass for tutorial mode:** Over-engineering. State machine on single `SPHShell` instance is sufficient.
- **Storing tutorial state globally (module-level):** Breaks re-entrability. Store on `self._tutorial_state`.
- **Calling `cmdloop()` recursively for tutorial:** Not needed. Same `cmdloop()`, state machine runs in the same loop.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Non-interactive stdin feeding | Custom subprocess wrapper | `printf "...\n" \| python sph_sim.py --interactive` | cmd.Cmd already reads from stdin when `use_rawinput=False` — verified working |
| PNG byte-determinism checks | Custom hash comparison | Trust: verified identical MD5 for same `--seed 42` across two runs | matplotlib + fixed seed produces identical output |
| Tutorial progress serialization | `~/.sphsim_tutorial_progress` JSON | In-memory `TutorialFlow` dataclass | D-06 explicitly rejects persistence; 15-min flow doesn't need it |
| Polish diff/fuzzy matching for wrong input | Levenshtein distance library | Simple shape-check (see §Shape-Match Strategy) | 8 steps with known expected commands; exact match is sufficient |

---

## Shape-Match Strategy (D-04 Forgiving Verification)

For each step, the `_check_tutorial_step(step_n, line, result)` method must decide if the user's command satisfies the requirement. Strategy: loose shape-match (does line start with the right command word + required positional arg?) + KPI range check from `self._last_sim_result`.

### Worked Example 1: Step 1 — Baseline

**Expected command family:** `run naive` (with or without `zeta=0.75`)  
**Shape check:** `line.startswith('run') and 'naive' in line.split()`  
**Result check:** `result.get('avg_val_last100', 0) >= 80.0` (allow some leeway — seed=42 gives 92.0 for naive default)  
**Source:** UAT test #1: `python3 sph_sim.py --strategy naive --zeta 0.75 --seed 42 --json --no-agent` → `metrics.avg_val_last100 == 92.0` [VERIFIED: 08-UAT.md test #1]

```python
# Step 1 check
if step == 1:
    tokens = line.split()
    return (tokens[0] == 'run' and 'naive' in tokens
            and result.get('avg_val_last100', 0) >= 80.0)
```

### Worked Example 2: Step 4 — Custom Load

**Expected command family:** `custom examples/custom_strategy_template.py`  
**Shape check:** `line.startswith('custom')`  
**Result check:** `bool(set(STRATEGIES.keys()) - BUILTIN_STRATEGIES)` — any non-builtin key in STRATEGIES dict means custom was loaded successfully  
**Source:** UAT test #3: `printf 'custom examples/custom_strategy_template.py\nstrategies\nrun\nexit\n' | python3 sph_sim.py --interactive` [VERIFIED: 08-UAT.md test #3]

```python
# Step 4 check — 'custom' command sets STRATEGIES; check after do_custom fires
# Note: postcmd receives line AFTER do_custom ran; result may be None (custom doesn't set _last_sim_result)
# So detection should be: check STRATEGIES at postcmd time, not via _last_sim_result
if step == 4:
    from sphsim.strategies import STRATEGIES, BUILTIN_STRATEGIES
    return bool(set(STRATEGIES.keys()) - BUILTIN_STRATEGIES)
```

**Important:** Step 4 verification does NOT use `_last_sim_result` (do_custom doesn't produce a simulation result). Instead it inspects `STRATEGIES` directly in `postcmd`. [VERIFIED: local STRATEGIES inspection]

### Worked Example 3: Step 8 — Batch

**Expected command family:** `batch naive --seeds N` (N ≥ 3 acceptable per D-04)  
**Shape check:** `line.startswith('batch') and '--seeds' in line`  
**Result check:** `result.get('aggregate') is not None` — `_last_sim_result` set by `do_batch` includes `{'aggregate': aggregate, ...}`  
**Source:** UAT test #8: `python3 sph_sim.py --strategy naive --zeta 0.75 --batch --seeds 10 --json` [VERIFIED: 08-UAT.md test #8]

```python
# Step 8 check
if step == 8:
    tokens = line.split()
    return (tokens[0] == 'batch' and '--seeds' in line
            and result is not None and 'aggregate' in result)
```

### Step Verification Map (all 8 steps)

| Step | Topic slug | Expected command family | Shape check | Result check |
|------|------------|------------------------|-------------|--------------|
| 1 | `baseline` | `run naive [zeta=0.75]` | `tokens[0]=='run' and 'naive' in tokens` | `avg_val_last100 >= 80.0` |
| 2 | `strategies` | `strategies` then `strategy <name>` | `line=='strategies' or line.startswith('strategy ')` | no sim result; check output printed (hint-only step) |
| 3 | `run-strategy` | `run <any_builtin> [params]` | `tokens[0]=='run' and tokens[1] in BUILTIN_STRATEGIES` | `avg_val_last100 >= 0` (any valid result) |
| 4 | `custom` | `custom examples/custom_strategy_template.py` | `tokens[0]=='custom'` | `bool(set(STRATEGIES.keys()) - BUILTIN_STRATEGIES)` |
| 5 | `compare` | `compare <name> [params]` | `tokens[0]=='compare'` | `'comparison' in result and result['comparison'].get('delta')` |
| 6 | `env` | `run naive --phi … / run naive zeta=0.75 valuation=step` | `tokens[0]=='run'` + any env param present | `avg_val_last100 != 92.0` (changed from default) OR simply any valid run |
| 7 | `report` | (automatic — fired by step 1/3/5 already) | special: instruct user to `run adaptive` and look at reports/ | report_dir exists after previous steps |
| 8 | `batch` | `batch <name> --seeds N` | `tokens[0]=='batch' and '--seeds' in line` | `'aggregate' in result` |

**Note on step 2 and 7:** Step 2 (`strategies`/`strategy`) and step 7 (`report inspection`) are "browse" steps with no simulation result to verify. Recommendation: treat these as display-only steps where ANY input after being shown the task auto-qualifies (or prompt the user to type a specific single command like `strategies` and check `line=='strategies'`). For step 7, the report was already created by an earlier step — just point the user at the path and accept `skip` or any subsequent command.

---

## D-07 Recommendation: Wrong-Input Handling Policy

**Policy:** On command shape mismatch, print a one-line hint pointing back to the exact expected command. After 3 hints for the same step, append a note: "Wpisz `skip` jeśli chcesz pominąć ten krok." Never auto-advance.

**Sample hint text for step 1:**

```
Nie rozpoznano polecenia dla kroku 1. Oczekiwano:
  run naive zeta=0.75
Spróbuj jeszcze raz lub wpisz `skip` żeby pominąć.
```

**Sample hint text after 3 failed attempts:**

```
Wskazówka: Wpisz `skip` żeby przejść do następnego kroku bez weryfikacji.
```

**Rationale:** Matches D-07 spirit ("hint-then-allow-skip, never auto-advance"). Three hints is enough for a 15-min tutorial before it becomes frustrating. [ASSUMED — count of 3 is reasonable but not locked]

---

## Polish Tone Calibration

**Tone target:** Informal but respectful. Use "ty" (implicit), short sentences, direct verbs. Same register as existing REPL output ("Wpisz `help`", "Załadowano custom strategię").

### Sample Tutorial Output Lines

```
[krok 1/8 — Baseline]
══════════════════════════════════════════════════════════
Uruchom symulację baseline dla strategii naive:

  run naive zeta=0.75

To podstawowy punkt odniesienia (KPI = 92) — wszystkie
późniejsze strategie porównujemy do tego wyniku.
══════════════════════════════════════════════════════════
sph>
```

(after user types `run naive zeta=0.75` and sim runs)

```
✓ zaliczone — krok 1/8

[krok 2/8 — Przegląd strategii]
══════════════════════════════════════════════════════════
Wyświetl listę strategii i szczegóły jednej z nich:

  strategies
  strategy incentive

W odpowiedzi zobaczysz opis, parametry i baseline KPI.
══════════════════════════════════════════════════════════
sph>
```

### Sample PRZEWODNIK.md Paragraph (Quickstart section)

```markdown
## Szybki start (60 sekund)

```bash
# Klonuj repo i zainstaluj zależności
git clone <repo-url> && cd ekonometria-2
pip install -r requirements.txt

# Uruchom baseline — oczekiwany wynik: avg_val_last100 = 92.0
python sph_sim.py --strategy naive --zeta 0.75 --seed 42 --no-agent
```

Gotowe. Raport MD i dwa wykresy PNG zostały automatycznie zapisane
w `./reports/<timestamp>/`.
```

---

## --tutorial Flag Wiring Proposal

### args.py Changes (extend 4-way to 5-way mutex)

Current mutex group (line 141 in args.py):
```python
mutex = p.add_mutually_exclusive_group(required=True)
mutex.add_argument('--interactive', ...)
mutex.add_argument('--strategy', ...)
mutex.add_argument('--custom', ...)
```

Phase 7 added `--batch` and `--compare-agent` as post-parse checks (not in mutex group) because of warning #8. `--tutorial` should follow the **same post-parse pattern** to maintain the Polish error message style:

```python
# In args.py, add inside parse_args() after other post-parse checks:
p.add_argument('--tutorial', action='store_true',
               help='Uruchom interaktywny tutorial v1.1 (≤15 min)')
```

Then in the post-parse section:
```python
if args.tutorial and args.interactive:
    p.error("Flagi --tutorial i --interactive są wzajemnie wykluczające.")
if args.tutorial and args.strategy:
    p.error("Flaga --tutorial nie działa z --strategy (użyj trybu tutorial interaktywnie).")
if args.tutorial and args.custom:
    p.error("Flaga --tutorial nie działa z --custom.")
if args.tutorial and args.batch:
    p.error("Flagi --tutorial i --batch są wzajemnie wykluczające.")
if args.tutorial and args.compare_agent:
    p.error("Flagi --tutorial i --compare-agent są wzajemnie wykluczające.")
```

**Alternative (cleaner):** Add `--tutorial` to the existing mutex group directly:
```python
mutex.add_argument('--tutorial', action='store_true',
                   help='Uruchom interaktywny tutorial v1.1 (≤15 min)')
```
This lets argparse handle all conflicts automatically with its default English error. Since Phase 7 already used post-parse pattern to avoid English errors, **use post-parse** for consistency. [ASSUMED — planner should verify which approach matches existing arg error style better]

### main.py Changes (4th early branch)

Current early branches (main.py lines 60-63):
```python
if args.interactive:
    from sphsim.cli.repl import run_repl
    run_repl()
    return
```

Add before the `args.interactive` branch:
```python
if args.tutorial:
    from sphsim.cli.repl import run_repl
    run_repl(start_in_tutorial=True)
    return
```

### run_repl() Signature Change

Current (repl.py line 428):
```python
def run_repl():
```

Changed to:
```python
def run_repl(start_in_tutorial: bool = False):
```

Inside `run_repl()`, after `SPHShell()` is created but before `.cmdloop()`:
```python
shell = SPHShell()
if start_in_tutorial:
    shell.cmdqueue.append('tutorial')  # inject as if user typed it
```

**`cmdqueue` approach:** `cmd.Cmd.__init__` already initializes `self.cmdqueue = []`. Lines in `cmdqueue` are processed BEFORE reading from stdin (see `cmdloop` source: `if self.cmdqueue: line = self.cmdqueue.pop(0)`). This is the idiomatic way to pre-inject commands. [VERIFIED: local cmd.Cmd source inspection]

---

## Non-Interactive Smoke Test Recipe for verify_phase8.sh

The `check()` pattern from `verify_phase7.sh` (lines 43-56) works unchanged. The smoke test for tutorial uses `printf` to pipe all 8 skips + exit:

```bash
# verify_phase8.sh — tutorial smoke test
check "Tutorial: 8 skips + exit completes without crash" \
    "printf 'tutorial\nskip\nskip\nskip\nskip\nskip\nskip\nskip\nskip\nexit\n' | \
     SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | \
     grep -F 'pominięto — krok 8/8' > /dev/null"

check "Tutorial: --tutorial flag enters tutorial mode" \
    "printf 'skip\nskip\nskip\nskip\nskip\nskip\nskip\nskip\nexit\n' | \
     SPHSIM_NO_REPORT=1 $PY sph_sim.py --tutorial 2>&1 | \
     grep -F 'INTERAKTYWNY TUTORIAL' > /dev/null"

check "Tutorial: tutorial command in REPL help" \
    "printf 'help\nexit\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | \
     grep -F 'tutorial' > /dev/null"
```

**How piping works with cmd.Cmd:** When stdin is a pipe (non-TTY), `cmd.Cmd` falls back to `use_rawinput=False` automatically on most platforms, reading from `self.stdin` which is `sys.stdin`. Lines are read via `self.stdin.readline()`. `printf "...\n"` feeds exactly these lines. No special flags needed. [VERIFIED: local subprocess test with `python3 sph_sim.py --interactive`]

**The `SPHSIM_NO_REPORT=1` flag** must be set to prevent tutorial steps from writing reports (which would create `./reports/tutorial-<ts>/` dirs during CI). For steps that REQUIRE a report to be verified (step 7), the smoke test uses `skip` to bypass. Full E2E tutorial test (with actual reports) is done in a separate check with `SPHSIM_NO_REPORT=''`.

---

## PRZEWODNIK.md Outline (locking D-11 into concrete sections)

**File:** `docs/PRZEWODNIK.md`  
**Target length:** ~200–300 lines including code blocks

```markdown
# Przewodnik użytkownika — SPH Symulator Strategii v1.1

> Najszybszy sposób żeby zacząć — uruchom `python sph_sim.py --tutorial`
> i przejdź interaktywnie przez wszystkie zdolności v1.1 (~15 min).

## Szybki start (60 sekund)

[clone → pip install → baseline command → expected output]
[reference to --tutorial for guided experience]

## Interaktywny tutorial

[How to launch, what it covers, controls: skip/back/repeat/exit]
[Screenshot-like ASCII showing step header and sph> prompt]

## Opis funkcjonalności v1.1

### 1. Tryb interaktywny (REPL)

[--interactive / sph> prompt / 8 commands]
[Example from UAT test #2: # Z 08-UAT.md test #2]
\`\`\`bash
printf 'help\nstrategies\nstrategy incentive\nexit\n' | python sph_sim.py --interactive
\`\`\`

### 2. Własna strategia (custom loader)

[--custom / REPL custom / template location]
[Example from UAT test #3: # Z 08-UAT.md test #3]
\`\`\`bash
python sph_sim.py --custom examples/custom_strategy_template.py --json --no-agent
\`\`\`

### 3. Racjonalny agent (veto)

[RationalAgent default-on / --no-agent / compare]
[Example from UAT test #4 and #5: # Z 08-UAT.md test #4 / #5]
\`\`\`bash
python sph_sim.py --strategy naive --zeta 0.95 --seed 42 --compare-agent --json
\`\`\`

### 4. Konfigurowalne środowisko

[--phi / --rho / --valuation / --K0 / validation errors]
[Example from UAT test #6: # Z 08-UAT.md test #6]

### 5. Raport Markdown + wykresy PNG

[Always-on, reports/<ts>/ structure, 3 files]
[Embedded PNG: ![Rozkład decyzji](assets/decision_distribution_naive.png)]
[Sample report.md excerpt as fenced block]
[Example from UAT test #7: # Z 08-UAT.md test #7]

### 6. Batch runner + agregacja

[--batch / --seeds / aggregate stats / 95% CI / baseline verdict]
[Embedded PNG: ![Agregat](assets/batch_aggregate_naive.png)]
[Example from UAT test #8: # Z 08-UAT.md test #8]

### 7. Pełny pipeline (cross-feature)

[One combined example from UAT test #9: # Z 08-UAT.md test #9]

## Referencja

### Flagi CLI (tabela alfabetyczna)

| Flaga | Typ | Domyślnie | Opis |
|-------|-----|-----------|------|
| --alpha | float | 1 | ... |
| --batch | bool | false | ... |
| ... (all flags from args.py) ... |

### Komendy REPL (tabela alfabetyczna)

| Komenda | Składnia | Opis |
|---------|----------|------|
| batch | batch <nazwa> --seeds N|lista [k=v ...] | ... |
| compare | compare <nazwa> [k=v ...] | ... |
| custom | custom <ścieżka> [k=v ...] | ... |
| exit | exit | ... |
| help | help | ... |
| run | run <nazwa> [k=v ...] | ... |
| strategies | strategies | ... |
| strategy | strategy <nazwa> | ... |
| tutorial | tutorial | ... |

### Wbudowane strategie (STRATEGY_META)

| Nazwa | Opis | Kluczowy parametr | Baseline KPI |
|-------|------|-------------------|--------------|
| naive | ... | zeta | 92.0 |
| threshold | ... | max_phase | — |
| phase_prob | ... | probs | — |
| incentive | ... | expected_P | — |
| adaptive | ... | s_target | — |

## Teoria (krótki opis)

[~1 page: SPH model, UP/DOWN fazy 1..5, COMMIT/ABSTAIN/VETO]
[RationalAgent: E[zysk_i] formula, incentive compatibility claim]
[Links: → PROMPT_DLA_AGENTA.txt (pełna teoria), → Raport.pdf (eksperymenty)]
```

---

## docs/assets/ Generation Plan

### Which commands to run

```bash
# 1. decision_distribution_naive.png + kpi_timeseries_naive.png
# (from naive --zeta 0.75 --seed 42)
python sph_sim.py --strategy naive --zeta 0.75 --seed 42 --no-agent
# Copy from reports/<latest>/decision_distribution.png → docs/assets/decision_distribution_naive.png
# Copy from reports/<latest>/kpi_timeseries.png → docs/assets/kpi_timeseries_naive.png

# 2. batch_aggregate_naive.png
# (from batch naive seeds 1..5)
python sph_sim.py --strategy naive --zeta 0.75 --batch --seeds 5 --no-agent
# Copy from reports/batch_<latest>/batch_aggregate.png → docs/assets/batch_aggregate_naive.png
```

### Determinism verification

All three PNGs are **byte-identical across runs** with the same `--seed 42` (verified by MD5 hash comparison in this research session). [VERIFIED: local test — MD5 identical for decision_distribution.png, kpi_timeseries.png, and batch_aggregate.png across two independent runs]

No datetime stamps are embedded in PNG metadata by matplotlib (matplotlib uses Agg backend by default which is pure-software; no system time embedded in pixel data). The `seed` parameter controls all stochastic elements. [VERIFIED: local test]

### Note on matplotlib version drift

D-14 notes "(modulo matplotlib version drift)". If matplotlib upgrades between dev and CI, PNGs MAY differ. The PRZEWODNIK.md note should say:

> *Wykresy wygenerowane matplotlib 3.x z --seed 42. Przy różnych wersjach matplotlib piksele mogą się nieznacznie różnić, wartości KPI są identyczne.*

### Generation script location

Create `scripts/generate_tutorial_assets.sh` (or inline in Wave 0 plan). Should: `rm -rf docs/assets/`, `mkdir -p docs/assets/`, run the two commands above, copy files, verify PNG magic bytes. Sets `SPHSIM_NO_REPORT=''` (clear the env var) to ensure reports are created.

---

## Validation Architecture (Nyquist)

`workflow.nyquist_validation` is not set in `.planning/config.json` → treat as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python `unittest` (stdlib, already in use — phases 1-7) |
| Config file | none (discover via `python -m unittest discover tests`) |
| Quick run | `SPHSIM_NO_REPORT=1 python -m unittest tests.test_tutorial` |
| Full suite | `SPHSIM_NO_REPORT=1 python -m unittest discover tests` |

### Phase 8 Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TUT-01 | `tutorial` REPL command exists and enters tutorial mode | unit | `python -m unittest tests.test_tutorial.TestTutorialEntry` | ❌ Wave 0 |
| TUT-02 | `skip` advances step counter | unit | `python -m unittest tests.test_tutorial.TestTutorialControls` | ❌ Wave 0 |
| TUT-03 | `back` decrements step counter | unit | `python -m unittest tests.test_tutorial.TestTutorialControls` | ❌ Wave 0 |
| TUT-04 | `exit` in tutorial drops to bare REPL (not quit session) | unit | `python -m unittest tests.test_tutorial.TestTutorialExit` | ❌ Wave 0 |
| TUT-05 | `--tutorial` flag wired to run_repl(start_in_tutorial=True) | integration | `python -m unittest tests.test_tutorial.TestTutorialCLI` | ❌ Wave 0 |
| TUT-06 | D-10: reports go to `./reports/tutorial-<ts>/step-N-<topic>/` | integration | `python -m unittest tests.test_tutorial.TestTutorialReports` | ❌ Wave 0 |
| DOC-01 | `docs/PRZEWODNIK.md` exists with required sections | structural | `python -m unittest tests.test_docs.TestPrzewodnik` | ❌ Wave 0 |
| DOC-02 | `docs/assets/*.png` files are present and valid PNG | structural | `python -m unittest tests.test_docs.TestAssets` | ❌ Wave 0 |

### Sampling Rate

- Per task commit: `SPHSIM_NO_REPORT=1 python -m unittest tests.test_tutorial`
- Per wave merge: `SPHSIM_NO_REPORT=1 python -m unittest discover tests`
- Phase gate: `bash scripts/verify_phase8.sh`

### Wave 0 Gaps

- [ ] `tests/test_tutorial.py` — stubs for TUT-01 through TUT-06
- [ ] `tests/test_docs.py` — stubs for DOC-01 and DOC-02
- [ ] `docs/` directory (created in Wave 0 or Wave 1)
- [ ] `docs/assets/` directory

---

## Common Pitfalls

### Pitfall 1: Tutorial `exit` Reaching `do_exit`

**What goes wrong:** If `precmd` doesn't catch `exit` when `_tutorial_state` is active, `do_exit` fires, session ends (returns `True` from `do_exit`), REPL quits entirely — violating D-05 ("leave tutorial, drop back to bare REPL").

**Why it happens:** `cmd.Cmd` dispatches `exit` to `do_exit` unless `precmd` short-circuits with an empty return.

**How to avoid:** `precmd` must check `self._tutorial_state is not None` FIRST, before any dispatch. Return `''` for `exit` when in tutorial mode. [VERIFIED: precmd returning '' prevents do_exit from being called]

**Warning signs:** Test piping `printf "tutorial\nexit\n" | python sph_sim.py --interactive` — if REPL session ends (exit code 0 AND no "Tutorial opuszczony" message AND prompt never returns), `do_exit` fired.

### Pitfall 2: postcmd Fires with line='' After precmd Short-Circuit

**What goes wrong:** When `precmd` returns `''` (e.g., for `skip`), `onecmd('')` calls `emptyline()` (no-op), then `postcmd(False, '')` is called. The `postcmd` must NOT attempt step verification when `line == ''` (empty), or it will try to verify a `skip` action as if it were a simulation result.

**How to avoid:** In `postcmd`, check `if not line.strip(): return stop` at the top before any tutorial logic. [VERIFIED: postcmd fires with '' after precmd short-circuit — confirmed in local test]

### Pitfall 3: _last_sim_result Persists Across Steps

**What goes wrong:** If `do_run` succeeds in step 3 but the user then types something non-simulation-producing in step 4 (like `strategies`), `_last_sim_result` still holds the step-3 result. `postcmd` for step 4 would see the step-3 result and may incorrectly verify step 4.

**How to avoid:** Clear `self._last_sim_result = None` at the start of `do_run`/`do_compare`/`do_batch` (not just at end). Set it only on success path. Consume it in `postcmd` by setting `_last_sim_result = None` after reading. [ASSUMED — double-clear pattern adds safety]

### Pitfall 4: Tutorial Report Dirs Created Without SPHSIM_NO_REPORT Check

**What goes wrong:** During non-interactive smoke tests in `verify_phase8.sh` with `SPHSIM_NO_REPORT=1`, if the `report_dir_override` path bypasses the env var check, reports are created regardless. Verify that D-10 override still respects `SPHSIM_NO_REPORT=1`.

**How to avoid:** In `write_report()`, the env var check is the FIRST thing (line ~99): `if os.environ.get('SPHSIM_NO_REPORT') == '1': return None`. This runs before any `report_dir_override` logic. No change needed — the new `report_dir_override` kwarg should be added AFTER this check. [VERIFIED: write_report opt-out check is line 99, before mkdir]

### Pitfall 5: write_batch_report Uses Hardcoded `Path('reports') / f'batch_{ts}'`

**What goes wrong:** `write_batch_report` does NOT use `_resolve_report_dir` — it has its own hardcoded `Path('reports') / f'batch_{ts}'` pattern (lines 193-199 in `sphsim/report/__init__.py`). To apply D-10 for batch tutorial steps, `write_batch_report` needs its own `report_dir_override` kwarg with the same pattern.

**How to avoid:** Add `report_dir_override=None` to `write_batch_report` signature. When set, skip the `batch_<ts>` mkdir and use `report_dir_override` directly. [VERIFIED: write_batch_report has independent mkdir logic]

### Pitfall 6: cmdqueue Injection Race With Introduction

**What goes wrong:** If `run_repl(start_in_tutorial=True)` injects `'tutorial'` into `cmdqueue`, but the `INTRO` banner (from `SPHShell.intro`) is printed during `cmdloop()` initialization, the user sees the banner THEN the tutorial immediately starts. That's fine. But if the banner contains "Wpisz `tutorial` żeby zacząć tutorial", users may be confused when it auto-starts. 

**How to avoid:** When starting in tutorial mode, suppress or modify the INTRO to mention that tutorial is starting. Or change INTRO to just say "Tryb tutorial — wpisz `skip` żeby pominąć krok." [ASSUMED — exact INTRO modification is Claude's Discretion]

---

## Code Examples

### Verified Pattern: precmd Short-Circuit (from local test)

```python
# Source: [VERIFIED: local cmd.Cmd experiment — precmd('skip') with return '' 
# prevents do_skip (nonexistent) from being called; emptyline() runs instead]
def precmd(self, line):
    if self._tutorial_state is not None:
        if line.strip() in ('skip', 'back', 'repeat'):
            self._handle_tutorial_control(line.strip())
            return ''   # short-circuit: onecmd('') → emptyline() → postcmd(False, '')
    return line         # normal dispatch for all other input
```

### Verified Pattern: cmdqueue Injection

```python
# Source: [VERIFIED: cmd.Cmd.__init__ initializes self.cmdqueue = []; 
# cmdloop pops from cmdqueue before reading stdin]
def run_repl(start_in_tutorial: bool = False):
    shell = SPHShell()
    if start_in_tutorial:
        shell.cmdqueue.append('tutorial')  # processed first, before any stdin read
    shell.cmdloop()
```

### Verified Pattern: _resolve_report_dir Already Supports base= Override

```python
# Source: [VERIFIED: sphsim/report/__init__.py _resolve_report_dir(base=None)]
# base already accepts a Path — but write_report() calls _resolve_report_dir() 
# WITHOUT base. New report_dir_override kwarg bypasses this entirely:
def write_report(args, res, params, K1, *, mode='single', report_dir_override=None):
    if os.environ.get('SPHSIM_NO_REPORT') == '1':
        return None
    try:
        if report_dir_override is not None:
            report_dir = Path(report_dir_override)
            report_dir.mkdir(parents=True, exist_ok=True)
        else:
            try:
                report_dir = _resolve_report_dir()  # unchanged default behavior
            except OSError as e:
                ...
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `--interactive` only (Phase 2) | `--tutorial` as 5th mutex member | Phase 8 | New entry point for guided flow |
| No `docs/` dir | `docs/PRZEWODNIK.md` + `docs/assets/` | Phase 8 | First committed documentation |
| `write_report()` no override | `write_report(..., report_dir_override=None)` | Phase 8 | Tutorial-specific report dirs |
| SPHShell: 8 commands | SPHShell: 9 commands (+ `tutorial`) | Phase 8 | `do_help` update required |
| `run_repl()` no args | `run_repl(start_in_tutorial=False)` | Phase 8 | Supports `--tutorial` CLI flag |

**Deprecated/outdated:**

- None in this phase — Phase 8 adds, does not remove.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Tutorial `exit` (in `precmd`) should reuse the word `exit` to mean "leave tutorial but stay in REPL" — same word as REPL `exit` | Pattern 2 (precmd) | If planner decides `exit` is ambiguous and uses `quit` instead for tutorial-escape, tutorial_control verb table changes |
| A2 | Post-parse approach for `--tutorial` in args.py (not adding to mutex group) is the right pattern, consistent with Phase 7's `--batch` | --tutorial Flag Wiring | If added to mutex group instead, argparse error messages will be English, inconsistent with Polish style |
| A3 | Step count of 8 with the proposed topic slugs: baseline / strategies / run-strategy / custom / compare / env / report / batch | Step Verification Map | If planner splits steps (e.g., separates `strategies` browse from `strategy <name>` into two steps), step count becomes 9 and slugs change |
| A4 | After 3 hints, suggest `skip` (D-07 hint count threshold) | D-07 Recommendation | If threshold should be 2 or unlimited, hint logic changes |
| A5 | `docs/assets/batch_aggregate_naive.png` is generated from `batch naive --seeds 5` (seeds 1..5) for byte-determinism | docs/assets/ Generation Plan | If D-14's "or equivalent" is interpreted differently (e.g., `--seeds 1,7,42,99,128`), the seed list in PRZEWODNIK.md must change |
| A6 | Tutorial step 2 (strategies browse) is a display-only step with no simulation result — verification is pattern-match only | Step Verification Map | If planner requires simulation result for step 2 verification, the check() method must be changed |

---

## Open Questions

1. **Exact `exit` keyword collision (A1 above)**
   - What we know: `precmd` can intercept `exit` before `do_exit` fires; "exit tutorial" behavior is defined (D-05).
   - What's unclear: Whether using `exit` as BOTH "quit REPL" and "quit tutorial" is confusing to users.
   - Recommendation: Keep `exit` for tutorial-escape (matches D-05 literal text). Document clearly in the tutorial opening banner that `exit` leaves the tutorial but NOT the session. If planner disagrees, use `quit` for tutorial-escape.

2. **Step 6 (env override) verification complexity**
   - What we know: ENV step requires user to run with `--phi`, `--rho`, or `--valuation` override. But the REPL `do_run` uses `DEFAULT_*` env params hardcoded (fake_args in do_run doesn't accept env overrides yet — Phase 5 added these for CLI but REPL `do_run` uses DEFAULT_* only).
   - What's unclear: Can the user actually do an env override in REPL `run` command? Checking repl.py line 213-218: `do_run` builds sim with `DEFAULT_PHI`, `DEFAULT_RHO`, hardcoded `K0=DEFAULT_K0`, `valuation='window'`. No env override via REPL `run` k=v args.
   - Recommendation: Change step 6 to demonstrate env override via ONE-SHOT CLI (instruct user to open a new terminal OR reframe step 6 as "try in CLI mode — this is what you'd run: `python sph_sim.py --strategy naive --valuation step`" as an informational step with `skip` expected). Or simplify step 6 to just show the `--phi`/`--rho` syntax without requiring REPL execution. **Planner must decide.**

3. **Tutorial step 7 (report inspection) — show or skip?**
   - What we know: Reports are always created automatically by prior steps. Step 7 can just point the user at the latest report dir and ask them to open it.
   - What's unclear: Is this a "real" step or just a narrative note?
   - Recommendation: Make step 7 a soft step — show the report path, instruct user to `cat reports/<latest>/report.md | head -40`, accept ANY command as "done" (no strict verification). Alternatively, fold this into step 5 (compare) since compare already shows the report banner on stderr.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.x | All | ✓ | 3.x (project-wide assumption) | — |
| matplotlib | PNG generation for docs/assets | ✓ | in requirements.txt | — |
| numpy | batch stats | ✓ | in requirements.txt | — |
| scipy | 95% CI | ✓ | in requirements.txt | — |
| `docs/` directory | PRZEWODNIK.md | ✗ | Does not exist | Create in Wave 0 |
| `docs/assets/` directory | PNG assets | ✗ | Does not exist | Create in Wave 0 |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** `docs/` and `docs/assets/` — created by Phase 8 plan Wave 0.

---

## Security Domain

`security_enforcement` not set in `.planning/config.json` → treat as enabled.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes (tutorial control words) | `line.strip() in ('skip', 'back', 'repeat', 'exit')` exact match — no injection surface |
| V2 Authentication | no | local CLI tool, no auth |
| V3 Session Management | no | in-memory tutorial state, no persistence |
| V4 Access Control | no | single-user local process |
| V6 Cryptography | no | no crypto |

No new attack surface. Tutorial mode accepts existing REPL commands (already validated by respective `do_*` methods) plus 4 control words with exact-match validation. The `report_dir_override` path is constructed programmatically by `TutorialFlow.step_report_dir()` from a trusted timestamp + step number, not from user input — no path traversal risk.

---

## Sources

### Primary (HIGH confidence)

- `sphsim/cli/repl.py` — full read; all method signatures and line numbers verified
- `sphsim/cli/args.py` — full read; mutex pattern + post-parse checks verified
- `sphsim/cli/main.py` — full read; early branch structure verified
- `sphsim/report/__init__.py` — full read; `_resolve_report_dir(base=)` + `write_report` + `write_batch_report` signatures verified
- `sphsim/strategies/__init__.py` — full read; `STRATEGIES`, `BUILTIN_STRATEGIES` registry verified
- Python `cmd.Cmd` stdlib source — read via `inspect.getsource`; `cmdqueue`, `precmd`, `postcmd`, `use_rawinput` behavior verified
- `.planning/phases/08-documentation-interactive-tutorial/08-CONTEXT.md` — all decisions read

### Secondary (MEDIUM confidence)

- `.planning/phases/07.1-comprehensive-uat/08-UAT.md` — 10 E2E tests all verified; commands extracted as D-12 canonical examples
- `scripts/verify_phase7.sh` — check() pattern studied for verify_phase8.sh design
- `examples/custom_strategy_template.py` — read; confirmed Polish comments, STRATEGY_META contract

### Tertiary (LOW confidence)

- Matplotlib version drift caveat for PNG determinism: [ASSUMED based on knowledge of matplotlib's Agg backend — not verified against a future matplotlib upgrade]

---

## Metadata

**Confidence breakdown:**
- cmd.Cmd integration pattern: HIGH — verified by running actual test scripts
- Shape-match strategy: HIGH — derived from actual UAT test #1/3/8 commands
- D-10 report-dir override: HIGH — verified write_report internals, found the gap
- PNG determinism: HIGH — verified by MD5 comparison across two runs
- --tutorial flag wiring: HIGH — verified cmdqueue mechanism in cmd.Cmd source
- PRZEWODNIK.md outline: MEDIUM — structure follows D-11 locked decisions; exact section depth is planning-time decision
- D-07 hint count (3): LOW — reasonable but not validated against user testing

**Research date:** 2026-05-28
**Valid until:** 2026-06-28 (stable stdlib; matplotlib version should be checked if deps update)
