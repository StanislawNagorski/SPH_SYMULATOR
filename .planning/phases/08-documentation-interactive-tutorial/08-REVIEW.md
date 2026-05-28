---
phase: 08-documentation-interactive-tutorial
reviewed: 2026-05-28T20:30:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - sphsim/cli/args.py
  - sphsim/cli/main.py
  - sphsim/cli/repl.py
  - sphsim/cli/tutorial.py
  - sphsim/report/__init__.py
  - tests/test_tutorial.py
  - tests/test_docs.py
  - scripts/gen_tutorial_assets.sh
  - scripts/verify_phase8.sh
  - docs/PRZEWODNIK.md
findings:
  critical: 1
  warning: 6
  info: 4
  total: 11
status: issues_found
---

# Phase 8: Code Review Report

**Reviewed:** 2026-05-28T20:30:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Phase 8 ships the interactive tutorial (TutorialFlow state machine + REPL precmd/postcmd interception + `--tutorial` CLI flag + Polish user guide + canonical PNG assets + verification script). The contract architecture (D-10 `report_dir_override`, pure tutorial state machine, 5-way mutex) is sound, and the Polish-copy verbatim assertions are well covered by tests.

However, there is **one blocker-tier correctness defect** caused by interaction with `cmd.Cmd`'s default `emptyline()` behavior: every tutorial control verb (`skip`/`back`/`repeat`/`exit`) leaves the dispatcher with `line=''`, which triggers `emptyline()` → `self.onecmd(self.lastcmd)`. The result is that immediately after the user types `exit` in the tutorial, the previous command (commonly `tutorial`) is silently re-executed, restarting the tutorial banner + step 1. Reproduced live below. The existing test suite does not catch this because the affected assertions only check for substring presence ("Tutorial opuszczony", "[krok 2/8"), not absence of the re-displayed banner.

Several warnings also reported around shell-script `rm -rf ./reports/` blast-radius, ambiguous default fallbacks in REPL `wrap_with_agent`, and built-in/custom strategy namespace collision risk.

## Critical Issues

### CR-01: `precmd` returning `''` triggers `cmd.Cmd.emptyline()` which re-runs the last command — tutorial restarts after every control verb

**File:** `sphsim/cli/repl.py:97, 107, 111, 118`
**Issue:** `precmd` returns `''` after handling `skip`/`back`/`repeat`/`exit`. `cmd.Cmd.cmdloop` then calls `self.onecmd('')`. Per CPython's `cmd.py`, `onecmd('')` parses the empty line, hits `if not line: return self.emptyline()`, and `emptyline()` default body is `if self.lastcmd: return self.onecmd(self.lastcmd)`. Because `lastcmd` was set by the previous successful command (typically `tutorial`), the tutorial command is re-dispatched immediately:

```
sph> tutorial             ← lastcmd = 'tutorial'
[banner + krok 1/8 shown]
sph> exit                 ← precmd returns '' (intercept)
        Tutorial opuszczony na kroku 1/8. ...
═══════════════════════════════════════
  INTERAKTYWNY TUTORIAL SPH SYMULATORA v1.1
═══════════════════════════════════════
[krok 1/8 — Baseline]    ← tutorial RESTARTS unintentionally
```

Reproduced verbatim against the current tree with `printf 'tutorial\nexit\nstrategies\nexit\n' | python3 sph_sim.py --interactive`. The banner is printed three times for what the user perceives as a single tutorial session, the "exit" verb does not actually exit, and the `strategies` command silently triggers tutorial step-1 hint logic instead of being a plain REPL invocation.

The same defect fires for `skip` (verify: `printf 'tutorial\nskip\nskip\nexit\nexit\n'` → second skip prints "Tutorial już jest aktywny" because `tutorial` was just re-replayed) and `repeat` (every `repeat` is followed by an unwanted re-banner).

Existing tests do not catch this because they only assert substring presence (e.g. "Tutorial opuszczony" appears at least once, `[krok 2/8` appears at least once, `Do widzenia.` count == 1), never substring absence or banner-count == 1.

**Fix:** Override `emptyline()` on `SPHShell` to no-op (matches REPL UX convention that bare Enter does nothing):

```python
# In SPHShell, anywhere alongside the other do_/precmd/postcmd methods
def emptyline(self):
    """Suppress cmd.Cmd's default 'repeat lastcmd' behavior.

    Required because precmd returns '' to short-circuit tutorial control
    verbs (skip/back/repeat/exit); without this override, those verbs
    silently re-trigger the previous command (commonly `tutorial`),
    restarting the tutorial banner.
    """
    return None
```

Add a regression test that asserts the banner ("INTERAKTYWNY TUTORIAL SPH SYMULATORA") appears **exactly once** for `printf 'tutorial\nexit\nexit\n' | sph_sim.py --interactive`, and that the step-1 description block appears exactly once.

## Warnings

### WR-01: `rm -rf ./reports/` in `verify_phase8.sh` and `gen_tutorial_assets.sh` silently destroys user-local report history

**File:** `scripts/verify_phase8.sh:70, 122, 124, 135, 137, 140, 165`; `scripts/gen_tutorial_assets.sh:31, 46, 65`
**Issue:** Both scripts execute `rm -rf ./reports/` without any guard (no opt-in, no `set -u` clobber check, no preserve-then-restore). A developer with locally interesting reports (e.g. an in-flight experiment) loses them silently by running the phase-exit gate or asset regenerator. `set -euo pipefail` is in effect, so the deletion is non-recoverable.

**Fix:** Either scope deletions to a tutorial-only glob, or use a dedicated tempdir for verification runs:

```bash
# Option A — only delete tutorial dirs we create
rm -rf ./reports/tutorial-* ./reports/batch_* ./reports/[0-9]*-verify

# Option B — run verification in a tempdir
VERIFY_HOME=$(mktemp -d)
trap 'rm -rf "$VERIFY_HOME"' EXIT
cd "$VERIFY_HOME"
# ... copy or symlink project root, run from here ...
```

At minimum, print a warning before deletion: `echo "[INFO] removing ./reports/ — Ctrl+C now if you have unsaved local reports"; sleep 2`.

### WR-02: REPL `wrap_with_agent(..., params.get('expected_P', DEFAULT_K0))` uses K0 threshold as a payment fallback

**File:** `sphsim/cli/repl.py:313, 385, 431, 520`
**Issue:** Four call sites use `params.get('expected_P', DEFAULT_K0)` as the default for `expected_P`. `DEFAULT_K0` is the lower-valuation threshold — it is semantically unrelated to expected payment. The two happen to share value `100.0` in the current `config.py`, so the bug is currently latent, but any future tuning of `DEFAULT_K0` (e.g. lowering to 50) will silently change agent behavior in the REPL.

**Fix:** Import the dedicated default (or hardcode the CLI default that argparse uses):

```python
from sphsim.config import DEFAULT_EXPECTED_P  # add to config if missing
# ...
strategy_fn = wrap_with_agent(STRATEGIES[name], params.get('expected_P', DEFAULT_EXPECTED_P))
```

If `DEFAULT_EXPECTED_P` does not exist, use the argparse-side constant: `params.get('expected_P', 100.0)` — but at minimum stop reusing `DEFAULT_K0` for a meaning it never had.

### WR-03: Built-in vs custom strategy dispatch only consults built-in set, allowing namespace collision when custom shadows a built-in name

**File:** `sphsim/cli/repl.py:195, 223, 301, 373, 499`
**Issue:** Every dispatch block checks `if name in BUILTIN_STRATEGIES` to decide whether to import from `sphsim.strategies.<name>` or `sphsim.custom.<name>`. The `STRATEGIES` registry is a single dict; a custom strategy registered under a built-in's name (e.g. user runs `custom my_naive.py` and the loader names it `naive`) overwrites `STRATEGIES['naive']` but the dispatch still imports `sphsim.strategies.naive` for metadata, returning stale meta/baseline. The actual `strategy_fn` invoked is the custom one (from `STRATEGIES[name]`) but the displayed description, params, and baseline KPI are the built-in's.

**Fix:** Use the actual module of `STRATEGIES[name]` as ground truth, or block name collisions in the loader:

```python
# Option A — derive namespace from registered fn module:
mod = sys.modules[STRATEGIES[name].__module__]
meta = mod.STRATEGY_META

# Option B — at load time in strategies/loader.py:
if name in BUILTIN_STRATEGIES:
    raise LoaderError(f"Custom strategy name '{name}' collides with built-in — wybierz inną nazwę.")
```

### WR-04: `gen_tutorial_assets.sh` uses `head -1` to find newest batch dir; collision-retry suffixes break this

**File:** `scripts/gen_tutorial_assets.sh:48`
**Issue:** `LATEST_B=$(ls -d ./reports/batch_*/ 2>/dev/null | head -1)` picks the FIRST line of `ls`. For batch dir names like `batch_20260528-203000` and `batch_20260528-203000-2` (the `-N` collision suffix from `_resolve_report_dir`-equivalent logic in `write_batch_report:244-246`), `ls` returns them alphabetically — `batch_20260528-203000/` first, `batch_20260528-203000-2/` second. The script picks the older one. Line 35 above correctly uses `tail -1` for the single-run case; the batch line is inconsistent.

Even though the immediately-preceding `rm -rf ./reports/` reduces likelihood of collision-retry suffix to zero in practice, the inconsistency is a footgun if the cleanup is ever removed or fails.

**Fix:** Use `tail -1` symmetrically (and prefer `ls -t -d` for mtime ordering if available):

```bash
LATEST_B=$(ls -d ./reports/batch_*/ 2>/dev/null | tail -1)
```

### WR-05: Step-1 `check_step` matches `naive` anywhere in tokens, not only as the strategy positional

**File:** `sphsim/cli/tutorial.py:261-266`
**Issue:** `len(tokens) >= 2 and tokens[0] == 'run' and 'naive' in tokens` accepts any line where `naive` appears anywhere after `run`. Examples:
- `run threshold naive=true` → would pass step-1 verification if it produced KPI ≥ 80 (it wouldn't here because `naive=true` would fail param parsing earlier, but the principle holds — `run threshold foo=naive` is the safer adversarial case).
- `run threshold max_phase=3` followed somewhere by `naive` as a freeform token cannot occur in practice but the membership check is intent-leaky.

**Fix:** Pin the strategy slot:

```python
return (
    len(tokens) >= 2 and tokens[0] == 'run' and tokens[1] == 'naive'
    and last_sim_result is not None
    and last_sim_result.get('avg_val_last100', 0) >= 80.0
)
```

This is also more consistent with step-3's `tokens[1] in builtin_strategies` pattern.

### WR-06: `report_dir_override=Path('')` (or any falsy-but-not-None Path) silently writes report.md into cwd

**File:** `sphsim/report/__init__.py:132-134, 235-237`
**Issue:** The override branch does `if report_dir_override is not None: report_dir = Path(report_dir_override); report_dir.mkdir(parents=True, exist_ok=True)`. `Path('').mkdir(parents=True, exist_ok=True)` is a no-op (`.` already exists), and subsequent `(report_dir / 'report.md').write_text(...)` writes to `./report.md` — silently polluting cwd. Same for `Path('.')` or any path that already exists as a writable directory the caller did not intend.

This is unlikely to be hit by `repl.py` because `step_report_dir()` always returns a non-empty Path, but the public function contract should be defensive: the wave-1 unit tests verify `report_dir_override=Path('reports/tutorial-test/step-1-baseline')` but never the empty/`.` cases.

**Fix:** Reject obviously-wrong override values at the boundary:

```python
if report_dir_override is not None:
    report_dir = Path(report_dir_override)
    if str(report_dir) in ('', '.'):
        print(f'[OSTRZEŻENIE] report_dir_override pusty/cwd ({report_dir!r}) — raport pominięty.', file=sys.stderr)
        return None
    report_dir.mkdir(parents=True, exist_ok=True)
```

## Info

### IN-01: `getattr(args, 'strategy', None)` is defensive over an attribute that always exists

**File:** `sphsim/cli/args.py:218`
**Issue:** `args.strategy` is always present on the Namespace because argparse creates the attribute with `default=None` when `--strategy` is not given. The `getattr` fallback is dead defensive code and reads as if `strategy` might be absent.

**Fix:** `if args.tutorial and args.strategy:` — equivalent and clearer.

### IN-02: Step-7 hint path in `postcmd` is unreachable because `check_step(7, ...)` returns True for any non-empty line

**File:** `sphsim/cli/repl.py:151`
**Issue:** The condition `if result is not None or ts.step in (2, 4, 7):` enables hint emission for step 7. But step 7's `check_step` returns `bool(line)` (soft-pass), which is True for any non-empty line — and `postcmd` only runs when `line.strip()` is non-empty (line 126). So `passed=True` always for step 7 and the hint branch is dead. Either remove 7 from the tuple, or document the rationale (forward-compat for a future hard-pass step 7).

**Fix:** Drop `7` from the tuple, leaving `ts.step in (2, 4)`. Add comment if intentional.

### IN-03: `_resolve_report_dir` TOCTOU between `.exists()` and `.mkdir(exist_ok=False)`

**File:** `sphsim/report/__init__.py:71-74`
**Issue:** Standard time-of-check/time-of-use race: two processes could see the same `ts` second, both pass `not exists`, one wins `mkdir`, the other raises `FileExistsError` (which propagates and is caught by the OSError branch in `write_report`, returning None silently). Negligible for a single-user CLI but worth documenting or rewriting as EAFP:

```python
while True:
    try:
        candidate.mkdir(parents=True, exist_ok=False)
        return candidate
    except FileExistsError:
        n += 1
        candidate = base / f'{ts}-{n}'
```

### IN-04: Comment in `tests/test_tutorial.py:6-9` claims "pozostałe testy są @unittest.skip" but no `@unittest.skip` exists in the module

**File:** `tests/test_tutorial.py:1-26`
**Issue:** The module docstring is leftover from Wave-0 scaffolding: "Wave 0 scaffolding: pozostałe testy są @unittest.skip z powodem wskazującym na wave i plan". No `@unittest.skip` decorator survives in the final code — all tests are live. The docstring is stale and will confuse future readers.

**Fix:** Tighten the module docstring to describe the Wave-3 reality (e.g. "Live tests for TUT-01..TUT-06 + Plan 08-01/03 unit coverage. No scaffolding remains.").

## Structural Findings (fallow)

No `<structural_findings>` block was provided by the orchestrator for this review — only narrative findings above.

---

_Reviewed: 2026-05-28T20:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
