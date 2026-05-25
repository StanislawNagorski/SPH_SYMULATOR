---
phase: 02-interactive-cli-shell
reviewed: 2026-05-25T18:30:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - sphsim/cli/args.py
  - sphsim/cli/main.py
  - sphsim/cli/repl.py
  - sphsim/strategies/naive.py
  - sphsim/strategies/threshold.py
  - sphsim/strategies/phase_prob.py
  - sphsim/strategies/incentive.py
  - sphsim/strategies/adaptive.py
  - tests/__init__.py
  - tests/test_strategy_meta_consistency.py
findings:
  critical: 0
  warning: 3
  info: 5
  total: 8
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-05-25T18:30:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found (no Critical; 3 Warning, 5 Info)

## Summary

Phase 2 implementation is correct against the D-15…D-33 contract and the documented spec. All five
strategy modules expose a well-formed `STRATEGY_META`; argparse mutex correctly enforces
`--interactive | --strategy`; `SPHShell` dispatches help/exit/strategies/strategy/EOF/default per
plan; the invariant test (`tests/test_strategy_meta_consistency.py`) passes; the Phase 1
regression suite (`scripts/regression_check.py`) still reports `PASS: 8/8`.

The most important security concern flagged in the review brief — arbitrary module import via
`importlib.import_module(f'sphsim.strategies.{name}')` — is **already mitigated**. `do_strategy()`
guards with `if name not in STRATEGIES:` before importing, so attempts like
`strategy ../../../etc/passwd`, `strategy os`, `strategy __init__`, and embedded semicolons all
return the polite Polish "Strategia '<x>' nie istnieje" message instead of touching `importlib`.
This is exactly the whitelist the brief asked for. No Critical findings.

That said, the implementation has several behavioural sharp edges worth fixing before this code
hits students:

1. `cmd.Cmd`'s default `emptyline()` re-runs the *previous* command when the user just hits
   Enter — surprising UX in this REPL (see WR-01).
2. Two latent forward-compat bugs hit the moment Phase 3 adds a custom strategy: `do_strategies`
   and `do_strategy` will raise `ModuleNotFoundError` / `AttributeError` if a strategy is
   registered in `STRATEGIES` but the module file or `STRATEGY_META` attribute is missing
   (WR-02, WR-03).
3. Several minor robustness / hygiene items (history length unset, dead `default()` defensive
   branch, redundant `noqa` comment) listed as Info.

None of these block the Phase 2 ship; the regression and invariant signals are green.

## Warnings

### WR-01: `emptyline` re-runs previous command — surprising REPL UX

**File:** `sphsim/cli/repl.py:39-117` (no `emptyline` override on `SPHShell`)
**Issue:** `SPHShell` does not override `cmd.Cmd.emptyline()`. The stdlib default *re-executes the
last non-empty command line* when the user presses Enter on an empty prompt. Confirmed by manual
test: after running `strategies`, pressing Enter three times re-prints the 5-row strategies table
three more times. For a study/teaching REPL this is confusing — students will read it as "the
program is repeating itself / hung in a loop", not as a documented behaviour. None of the
specs (`02-CONTEXT.md`, plans, ROADMAP) describes this behaviour; it is an unintended inheritance
from `cmd.Cmd`.
**Fix:** Add a one-line override so blank input is a no-op:
```python
def emptyline(self):
    """Blank line is a no-op (override cmd.Cmd which would re-run last command)."""
    return False
```

### WR-02: `do_strategies` crashes if a registered strategy module is missing or lacks `STRATEGY_META`

**File:** `sphsim/cli/repl.py:68-75`
**Issue:** `do_strategies` does
```python
for name in STRATEGIES.keys():
    mod = importlib.import_module(f'sphsim.strategies.{name}')
    description = mod.STRATEGY_META['description']
```
For the five built-in names this works because Phase 1 already imports the modules eagerly in
`sphsim/strategies/__init__.py`. But the explicit contract in `02-CONTEXT.md` (Integration Points)
is that Phase 3 / custom-loader code injects new keys into `STRATEGIES` at runtime — those
strategies may live as files not under `sphsim.strategies.*` (the loader will use `importlib`
with a file path) and they will not be importable via `sphsim.strategies.<name>`. With current
code, the very next user who types `strategies` after a custom load gets an unhandled
`ModuleNotFoundError` and the REPL crashes out of `cmdloop`.

It is true Phase 3 is out of Phase 2 scope, but the call site is explicitly written assuming
the live `STRATEGIES` registry (D-29 comment in code: "Phase 3 custom strategie naturalnie się
pojawią"). That assumption is incompatible with the import strategy chosen here.
**Fix:** Read `STRATEGY_META` off the function object (or its enclosing module via
`sys.modules`/`inspect.getmodule(fn)`) rather than reconstructing the dotted module path; or
guard with try/except and a fallback row:
```python
for name, fn in STRATEGIES.items():
    mod = sys.modules.get(fn.__module__)
    meta = getattr(mod, 'STRATEGY_META', None)
    description = meta['description'] if meta else '(brak opisu)'
    print(f"  {name:<12}— {description}")
```
This also removes the redundant `importlib` call (modules are already in `sys.modules`).

### WR-03: `do_strategy` has the same forward-compat fragility

**File:** `sphsim/cli/repl.py:93-95`
**Issue:** Same pattern as WR-02:
```python
mod = importlib.import_module(f'sphsim.strategies.{name}')
meta = mod.STRATEGY_META
```
After the whitelist passes (`name in STRATEGIES`), the code assumes both that
`sphsim.strategies.<name>` is importable AND that the module has a `STRATEGY_META` attribute.
For Phase 3 custom strategies loaded from arbitrary paths neither is guaranteed. A user who
registers a strategy that forgot to define `STRATEGY_META` will see an unhandled `AttributeError`
crashing the REPL instead of a polished error.
**Fix:** Resolve via `fn.__module__` / `sys.modules` and use `getattr(mod, 'STRATEGY_META', None)`
with a Polish error message when missing:
```python
fn = STRATEGIES[name]
mod = sys.modules.get(fn.__module__)
meta = getattr(mod, 'STRATEGY_META', None)
if meta is None:
    print(f"Strategia '{name}' nie eksportuje STRATEGY_META — brak metadanych do wyświetlenia.")
    return
```

## Info

### IN-01: `default()` strips already-stripped input (dead defensive code)

**File:** `sphsim/cli/repl.py:112-117`
**Issue:** `cmd.Cmd.parseline()` (called by `onecmd`, which dispatches to `default`) already
strips the trailing newline and leading/trailing whitespace before passing `line` to `default()`.
The branch `text = line.strip() if isinstance(line, str) else str(line)` will essentially never
do anything non-trivial — `line` is always a `str` and already stripped. Confirmed by stdlib
behaviour: `onecmd('foo bar  ')` → `default('foo bar')`. The `isinstance(line, str) else str(line)`
guard guards against a contract violation that the stdlib does not allow.
**Fix:** Either remove the guard:
```python
def default(self, line):
    print(f"Nieznana komenda: '{line}'. Wpisz 'help' żeby zobaczyć dostępne komendy.")
```
or, if defensive intent is desired, document why. As is it reads like a real concern when it
isn't.

### IN-02: `readline` history length is unbounded (`-1`)

**File:** `sphsim/cli/repl.py:140-149` (in `run_repl`)
**Issue:** `readline.get_history_length()` defaults to `-1` (unlimited). Over many sessions
`~/.sphsim_history` will grow without bound. Not a correctness or security bug — typical shells
do similar — but a one-liner here keeps the file polite for users running many sessions:
**Fix:**
```python
readline.set_history_length(1000)
```
Place it once near the top of `run_repl()` before reading the file.

### IN-03: `noqa: F401` for `readline` import works but the rationale is partially incorrect

**File:** `sphsim/cli/repl.py:19`
**Issue:** The comment says `cmd.Cmd uses readline for line-editing on POSIX`. That is true but
`readline` is *also* explicitly used by `run_repl()` (`readline.read_history_file`,
`readline.write_history_file`). The import is therefore not only a side-effect import — it is
used by name. The `# noqa: F401` is therefore unnecessary (F401 would never fire because
`readline.read_history_file` is referenced) and the comment misleads future readers about why
the import exists. Remove the `noqa` and trim the comment.
**Fix:**
```python
import readline  # ~/.sphsim_history + line-editing on POSIX (D-19)
```

### IN-04: `STRATEGY_META['source']` declared in the D-26 contract is silently dropped in the REPL output

**File:** `sphsim/cli/repl.py:107-109`, `sphsim/strategies/naive.py:17-21`
**Issue:** `naive.py` faithfully stores `'source': 'PROJECT.md / v1.0 results'` per D-26, but
`do_strategy` prints only `invocation` and `avg_val_last100`. The `source` field is therefore
data-only with no UX surface. Either is fine, but worth a one-line addition to surface
attribution to students:
**Fix (optional):**
```python
print(f"  {baseline['invocation']} → avg_val_last100 = {baseline['avg_val_last100']}")
if 'source' in baseline:
    print(f"  źródło: {baseline['source']}")
```

### IN-05: Test sets `sys.argv` globally; safe under finally, but worth a `unittest.mock.patch` for consistency

**File:** `tests/test_strategy_meta_consistency.py:55-64`
**Issue:** `_capture_parser` swaps `sys.argv` with a save/restore via `try/finally`. The
construct is correct (no leak on exception) but inconsistent with the surrounding code which
already uses `unittest.mock.patch` for the parser monkey-patch. Using `patch.object(sys, 'argv', ['x', '--strategy', 'naive'])`
inside the same `with` block would centralise the patching idiom and remove the manual save/restore.
This is purely a style consistency note — current code is correct and the test passes.
**Fix (optional):**
```python
with patch.object(argparse.ArgumentParser, 'parse_args', capture), \
     patch.object(sys, 'argv', ['x', '--strategy', 'naive']):
    from sphsim.cli.args import parse_args
    parse_args()
```

---

## Out-of-scope but worth noting

- **`tests/__init__.py` is 0 bytes (empty).** This is the documented intent (package marker for
  unittest discovery — confirmed in `02-04-SUMMARY.md`). Not a finding.
- **Security: arbitrary module import.** The brief flagged
  `importlib.import_module(f'sphsim.strategies.{name}')` as a potential concern. The whitelist
  check `if name not in STRATEGIES` on line 87 of `repl.py` mitigates this completely for Phase 2.
  Attempts with path traversal (`../../../etc/passwd`), reserved module names (`os`, `sys`,
  `__init__`), or embedded shell payloads all hit the whitelist branch and never reach
  `importlib`. Verified manually. No finding.
- **Backwards compat (CLI-04).** `scripts/regression_check.py` reports `PASS: 8/8` after this
  phase. Verified.
- **Polish in user-facing strings.** All REPL outputs, error messages, and intro text comply with
  the PROJECT.md "polski w komunikatach CLI" constraint.

---

_Reviewed: 2026-05-25T18:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
