# Phase 3: Custom strategy loader — Pattern Map

**Mapped:** 2026-05-27
**Files analyzed:** 7 (4 new, 3 modified — args.py / main.py / repl.py / __init__.py)
**Analogs found:** 7 / 7 (100% coverage — Phase 1/2 zostawiły bardzo bliskie wzorce)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `sphsim/strategies/loader.py` | service (plugin loader) | request-response (path → tuple) | `sphsim/strategies/__init__.py` + `sphsim/strategies/incentive.py` (meta shape) | partial — no direct analog (NEW capability), composite |
| `examples/custom_strategy_template.py` | template / strategy module | request-response (pure fn) | `sphsim/strategies/threshold.py` (D-51 alias) + `naive.py` | exact (verbatim shape) |
| `tests/test_loader.py` | test | request-response (assertions) | `tests/test_strategy_meta_consistency.py` | exact (stdlib unittest, same bootstrap) |
| `sphsim/strategies/__init__.py` (MOD) | registry | request-response (lookup) | `sphsim/strategies/__init__.py` (self — Phase 1) | exact (insertion site only) |
| `sphsim/cli/args.py` (MOD) | CLI config | argparse parse | `sphsim/cli/args.py` lines 38-42 (existing mutex) | exact |
| `sphsim/cli/main.py` (MOD) | controller | request-response | `sphsim/cli/main.py` lines 10-14 (early branch `args.interactive`) | exact |
| `sphsim/cli/repl.py` (MOD) | REPL controller | event-driven (cmd loop) | `sphsim/cli/repl.py` `do_strategies` / `do_strategy` (Phase 2) | exact |

---

## Pattern Assignments

### `sphsim/strategies/loader.py` (NEW — service, plugin loader)

**Primary analog:** `sphsim/strategies/__init__.py` (registry import + `StrategyFn` type alias) + `sphsim/strategies/incentive.py` (params dict access from `STRATEGY_META`).
**Secondary analog:** `sphsim/cli/args.py` (parsing helper shape — module-level functions, no class).
**Module docstring style:** `sphsim/cli/repl.py` lines 1-14 (multi-line `"""..."""`, polski, wymienia eksportowane symbole i side effects).

**Module docstring pattern** (copy from `repl.py` lines 1-14):
```python
"""Loader custom strategii — ładuje plik .py użytkownika przez importlib (Phase 3).

Eksportuje:
  - load_custom(path) -> (basename, fn, meta)  — pure function (rejestrację robi wywołujący)
  - parse_custom_params(tokens, meta) -> dict  — typed conversion z STRATEGY_META
  - LoaderError                                — exception, polski komunikat w args[0]

Wszystkie komunikaty błędów po polsku (PROJECT.md constraint).
Stdlib only: importlib.util + inspect + os.path + sys (D-46, D-47).
"""
```

**Imports pattern** (composite — copy `repl.py` lines 15-21 style: stdlib first, project after, blank-line separated):
```python
import importlib.util
import inspect
import os
import sys

from sphsim.strategies import BUILTIN_STRATEGIES   # D-49 — sentinel z Phase 1 snapshot
```

**Exception class pattern** (no existing analog — D-48 spec):
```python
class LoaderError(Exception):
    """Błąd ładowania custom strategii — komunikat polski w args[0]."""
    pass
```

**Module-level constant pattern** (copy from `sphsim/strategies/__init__.py` line 11):
```python
# `__init__.py` line 11:
StrategyFn = Callable[..., str]
# Phase 3 loader.py equivalent — tuple stałych przy module top, SCREAMING_SNAKE_CASE per CONVENTIONS.md §Naming:
EXPECTED_PARAMS = ('dev', 'l', 's', 'phi', 'kappa', 'rho', 'h', 'p')
META_REQUIRED_KEYS = ('description', 'params', 'baseline_kpi')
CUSTOM_NAMESPACE_PREFIX = 'sphsim.custom'
```

**Banner pattern** (D-45 — no analog, but follow `print(...)` style z `sphsim/cli/repl.py` line 75 `print(f"  {name:<12}— {description}")`):
```python
# Banner pre-import — stdout (D-45 Claude's Discretion: banner to informacja, nie błąd):
print(f"[OSTRZEŻENIE] Ładuję arbitralny kod Pythona z: {abspath}")
```

**Live importlib import pattern** (copy from `sphsim/cli/repl.py` line 72):
```python
# repl.py line 72 — wzór dla "load module by dotted path" (oprócz: tu używamy spec_from_file_location):
mod = importlib.import_module(f'sphsim.strategies.{name}')
# Phase 3 loader.py — spec_from_file_location wariant (RESEARCH.md Pattern 1):
spec = importlib.util.spec_from_file_location(full_name, abspath)
mod = importlib.util.module_from_spec(spec)
sys.modules[full_name] = mod    # PRZED exec_module (circular import safety, RESEARCH Pitfall #2)
try:
    spec.loader.exec_module(mod)
except Exception as e:
    sys.modules.pop(full_name, None)   # cleanup zombie po failed re-load (Pitfall #2)
    raise LoaderError(f"Błąd podczas importu pliku {abspath}: {type(e).__name__}: {e}")
```

**Error message format** (copy from `sphsim/cli/repl.py` line 90 — inline jednolinijka, polski + lista dostępnych):
```python
# repl.py line 90:
available = ', '.join(STRATEGIES.keys())
print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
# Phase 3 loader.py equivalent — D-48 inline polski:
raise LoaderError(f"Nazwa '{basename}' koliduje z wbudowaną strategią. Zmień nazwę pliku.")
raise LoaderError(f"Nieznany parametr 'foo' dla strategii '{basename}'. Dostępne: {', '.join(declared)}.")
```

**Param tuple unpack pattern** (copy from `sphsim/cli/repl.py` line 102):
```python
# repl.py line 102 — 4-tuple unpack z STRATEGY_META['params']:
for param_name, param_type, default, desc in meta['params']:
    print(f"  {param_name}: {param_type.__name__} = {default!r} — {desc}")
# Phase 3 loader.py — parse_custom_params użycie tego samego unpack'u:
meta_by_name = {pname: (ptype, pdefault) for pname, ptype, pdefault, _ in meta['params']}
```

---

### `examples/custom_strategy_template.py` (NEW — strategy module template)

**Primary analog:** `sphsim/strategies/threshold.py` (D-51 explicit: "alias threshold z innym defaultem").
**Secondary analog:** `sphsim/strategies/naive.py` (verbatim shape — `def strategy_X(...)` + `STRATEGY_META`).

**File header comment pattern** (copy from `sphsim/strategies/threshold.py` lines 1-2 — extend with polski docstring per D-51):
```python
# threshold.py lines 1-2 (existing):
# Strategia threshold: COMMIT tylko jeśli dev.phase <= max_phase.
# Verbatim z sph_sim.py:128–131 (v1.0).
# Phase 3 template — D-51 wymaga POLSKI MULTI-LINE DOCSTRING (edukacyjny):
"""Szablon custom strategii dla SPH Symulatora.

Skopiuj ten plik i zmień nazwę (np. `moja_strategia.py`).
Funkcja MUSI nazywać się `strategy_<nazwa_pliku>` (verbatim wzór built-in).

Sygnatura strategii (verbatim z PROMPT_DLA_AGENTA.txt i Phase 1 D-03):
  dev   — Device(id, phase, status, ...)
  l     — list[int] — liczba dostawców per faza z POPRZEDNIEGO cyklu
  s     — int — bieżąca zajętość bufora SUS
  phi   — list[float] — P(awarii) per faza
  kappa — float — koszt commit
  rho   — list[float] — koszt awarii per faza
  h     — callable(i) — funkcja wagi (i^alpha)
  p     — dict — params z STRATEGY_META + override z --param/k=v

Funkcja zwraca 'COMMIT' lub 'ABSTAIN' (literały, nie enum).
"""
```

**Strategy function body pattern** (copy verbatim from `sphsim/strategies/threshold.py` lines 5-8):
```python
# threshold.py:
def strategy_threshold(dev, l, s, phi, kappa, rho, h, p):
    if dev.status != 'UP':
        return 'ABSTAIN'
    return 'COMMIT' if dev.phase <= int(p.get('max_phase', 3)) else 'ABSTAIN'
# Phase 3 template — basename `custom_strategy_template`, default 4 (D-51):
def strategy_custom_strategy_template(dev, l, s, phi, kappa, rho, h, p):
    # `dev.status` == 'DOWN' znaczy że urządzenie jest w cyklu naprawy — pomijamy.
    if dev.status != 'UP':
        return 'ABSTAIN'
    # `p.get(...)` pobiera param z --param k=v (CLI) lub k=v (REPL custom/run).
    # Default 4 znaczy "COMMIT do fazy 4 włącznie" (faza 5 zawsze pada → ABSTAIN).
    return 'COMMIT' if dev.phase <= int(p.get('max_phase', 4)) else 'ABSTAIN'
```

**STRATEGY_META pattern** (copy verbatim from `sphsim/strategies/threshold.py` lines 11-17, replace name):
```python
# threshold.py lines 11-17:
STRATEGY_META = {
    'description': 'COMMIT tylko dla faz <= max_phase',
    'params': [
        ('max_phase', int, 3, 'Max faza COMMIT'),
    ],
    'baseline_kpi': None,
}
# Phase 3 template — D-51 spec:
STRATEGY_META = {
    'description': 'Szablon — COMMIT dla faz <= max_phase (default 4)',
    'params': [
        ('max_phase', int, 4, 'Maksymalna faza dla COMMIT'),
    ],
    'baseline_kpi': None,
}
```

**Acceptance check** (D-51): `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json` musi dać deterministyczny JSON output.

---

### `tests/test_loader.py` (NEW — test)

**Primary analog:** `tests/test_strategy_meta_consistency.py` (D-25 invariant test z Phase 2).

**Module docstring pattern** (copy from `tests/test_strategy_meta_consistency.py` lines 1-15 — multi-line `"""..."""`, polski, wymienia co testuje):
```python
# test_strategy_meta_consistency.py lines 1-15:
"""
Invariant test (D-25): STRATEGY_META['params'] ↔ argparse add_argument.
...
Test używa wyłącznie stdlib (unittest + importlib + argparse + sys + unittest.mock)
— zero zależności (PROJECT.md constraint stdlib-only utrzymany).
"""
# Phase 3 test_loader.py equivalent:
"""
Unit tests dla sphsim.strategies.loader (Phase 3, D-46 / D-47).

Pokrywa 4 warstwy walidacji loadera + happy path + re-load + collision:
  1. Import errors (SyntaxError, ImportError z user file)
  2. Brak/non-callable strategii
  3. Sygnatura mismatch + escape przez *args
  4. STRATEGY_META schema violations
  5. Happy path: load + return (name, fn, meta)
  6. Re-load: drugie wywołanie — fresh spec, sys.modules replaced (Pitfall #1)
  7. Collision z BUILTIN_STRATEGIES → LoaderError
  8. sys.modules cleanup po failed re-load (Pitfall #2)

Stdlib only: unittest + tempfile + textwrap + os + sys (zgodne z PROJECT.md).
"""
```

**sys.path bootstrap pattern** (copy verbatim from `tests/test_strategy_meta_consistency.py` lines 23-29):
```python
# test_strategy_meta_consistency.py lines 23-29 — copy verbatim:
# Pozwól uruchamiać test bezpośrednio: `python tests/test_loader.py`
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
```

**unittest.TestCase pattern** (copy from `tests/test_strategy_meta_consistency.py` lines 74-83):
```python
# test_strategy_meta_consistency.py lines 74-83:
class TestStrategyMetaConsistency(unittest.TestCase):
    """
    Weryfikuje invariant D-25 dla wszystkich 5 wbudowanych strategii.
    ...
    """
    def test_strategy_meta_matches_argparse(self):
        """STRATEGY_META params per strategia ↔ argparse add_argument (D-25)."""
# Phase 3 test_loader.py — analogiczny class + per-layer test:
class TestLoader(unittest.TestCase):
    """4-warstwowa walidacja loadera + reload + collision (D-46/D-47/D-49)."""

    def setUp(self):
        # tempfile.mkdtemp + helper _write_strategy(path, body) — patrz Claude's Discretion
        ...

    def test_layer1_syntax_error_raises_loader_error(self):
        ...
    def test_layer2_missing_function_raises_loader_error(self):
        ...
    def test_layer3_wrong_signature_raises_loader_error(self):
        ...
    def test_layer3_var_args_escape_accepts(self):  # RESEARCH Pattern 2
        ...
    def test_layer4_missing_meta_key_raises_loader_error(self):
        ...
    def test_happy_path_returns_tuple(self):
        ...
    def test_reload_replaces_sys_modules_entry(self):  # RESEARCH Pitfall #1
        ...
    def test_collision_with_builtin_raises_loader_error(self):  # D-49
        ...
    def test_failed_reload_cleans_up_sys_modules(self):  # RESEARCH Pitfall #2
        ...
```

**Test runner bottom pattern** (copy verbatim from `tests/test_strategy_meta_consistency.py` lines 171-172):
```python
if __name__ == '__main__':
    unittest.main()
```

**Assertion style** (copy from `tests/test_strategy_meta_consistency.py` lines 121-128, 142-149):
```python
# test_strategy_meta_consistency.py lines 121-128 — assertEqual z descriptive msg=:
self.assertEqual(
    len(tup), 4,
    msg=(
        f"{name}: każdy element STRATEGY_META['params'] musi być "
        f"krotką 4-elementową (name, type, default, description), "
        f"otrzymano {tup!r}"
    ),
)
# Phase 3 test_loader.py — assertRaises pattern dla LoaderError:
with self.assertRaises(LoaderError) as ctx:
    load_custom(path_to_broken_strategy)
self.assertIn('Brak funkcji', ctx.exception.args[0],
              msg=f'LoaderError msg should mention "Brak funkcji", got: {ctx.exception.args[0]!r}')
```

---

### `sphsim/strategies/__init__.py` (MODIFY — add BUILTIN_STRATEGIES)

**Analog:** self — Phase 1 D-14 STRATEGIES dict (lines 13-19).

**Existing pattern** (`sphsim/strategies/__init__.py` lines 13-19 — unchanged):
```python
STRATEGIES = {
    'naive': strategy_naive,
    'threshold': strategy_threshold,
    'phase_prob': strategy_phase_prob,
    'incentive': strategy_incentive,
    'adaptive': strategy_adaptive,
}
```

**Insertion site** (immediately after line 19, before EOF):
```python
# D-49 — frozenset snapshot dla collision detection. NIE używamy STRATEGIES.keys()
# bo po runtime'owej rejestracji custom strategii (Phase 3) zawierałby też custom,
# co psułoby collision-check (custom-vs-custom = reload, NIE error).
BUILTIN_STRATEGIES = frozenset(STRATEGIES.keys())
```

**Style note:** stała `SCREAMING_SNAKE_CASE` zgodnie z CONVENTIONS.md §Constants ("Registry dict in SCREAMING_SNAKE_CASE"). Komentarz polski (PROJECT.md constraint).

---

### `sphsim/cli/args.py` (MODIFY — add `--custom` to mutex + `--param` outside mutex)

**Analog:** `sphsim/cli/args.py` lines 38-42 (existing mutex from Phase 2 D-27/D-28).

**Existing mutex pattern** (lines 38-42 — extend):
```python
# args.py lines 38-42 — current Phase 2 state:
mutex = p.add_mutually_exclusive_group(required=True)
mutex.add_argument('--interactive', action='store_true',
                   help='Uruchom tryb interaktywny (REPL)')
mutex.add_argument('--strategy', choices=list(STRATEGIES.keys()),
                   help='Strategia: ' + ', '.join(STRATEGIES.keys()))
```

**Modification** — D-44 (trzeci człon mutex) + D-50 (zmień `choices` na `BUILTIN_STRATEGIES`):
```python
# Phase 3 — after mod:
from sphsim.strategies import STRATEGIES, BUILTIN_STRATEGIES   # MOD line 28 import

mutex = p.add_mutually_exclusive_group(required=True)
mutex.add_argument('--interactive', action='store_true',
                   help='Uruchom tryb interaktywny (REPL)')
mutex.add_argument('--strategy', choices=list(BUILTIN_STRATEGIES),   # D-50 — snapshot, NIE STRATEGIES.keys()
                   help='Strategia: ' + ', '.join(sorted(BUILTIN_STRATEGIES)))
mutex.add_argument('--custom', type=str, default=None,
                   help='Ścieżka do pliku .py z custom strategią')   # D-44 — trzeci człon
```

**`--param` add_argument outside mutex** (D-39, Claude's Discretion `action='append'`):
```python
# Insertion: po line 49 (po `--expected_P`), przed `# Parametry środowiska`:
p.add_argument('--param', action='append', dest='param', default=[],
               help='Param custom strategii w formacie k=v (repeatable; działa tylko z --custom)')
```

**Style match:** linia z `p.add_argument(...)` aligned z istniejącym vertical-alignment style (CONVENTIONS.md §Formatting). Help text polski (PROJECT.md).

---

### `sphsim/cli/main.py` (MODIFY — add `args.custom` early branch)

**Analog:** `sphsim/cli/main.py` lines 11-14 (existing `args.interactive` early branch).

**Existing early-branch pattern** (lines 11-14):
```python
# main.py lines 11-14 — Phase 2 pattern:
if args.interactive:
    from sphsim.cli.repl import run_repl
    run_repl()
    return
```

**Phase 3 second early branch** (insertion site: po linii 14, przed `K1 = ...` linia 15):
```python
# main.py — INSERT po line 14:
if args.custom:
    import sys
    from sphsim.strategies.loader import load_custom, parse_custom_params, LoaderError
    from sphsim.strategies import STRATEGIES
    try:
        name, strategy_fn, meta = load_custom(args.custom)
    except LoaderError as e:
        print(e.args[0], file=sys.stderr)
        sys.exit(1)
    STRATEGIES[name] = strategy_fn   # rejestracja — wywołujący robi (D-46 pure loader)
    try:
        params = parse_custom_params(args.param, meta)
    except LoaderError as e:
        print(e.args[0], file=sys.stderr)
        sys.exit(1)
    K1 = float('inf') if args.K1 < 0 else args.K1
    sim = SPHSimulator(
        nU=args.nU, nSUS=args.nSUS, K0=DEFAULT_K0, K1=K1,
        F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
        phi=DEFAULT_PHI, rho=DEFAULT_RHO,
        strategy_fn=strategy_fn, params=params, seed=args.seed,
    )
    res = sim.run()
    # Output dispatch — copy verbatim z main.py lines 30-33:
    if args.json:
        print(format_json(args, res, params, K1))
    else:
        # args.strategy jest None (mutex), więc format_human musi tolerować —
        # alternatywnie: ustaw args.strategy = name (custom) przed format_human.
        args.strategy = name   # quick fix, sprawia że format_human "Strategia: NAME" działa
        print(format_human(args, res, K1, args.verbose))
    return
```

**Ignore `--param` gdy `--custom` nie ustawiony** (Claude's Discretion — graceful):
```python
# Po `if args.interactive: ... return`, przed `if args.custom: ... return`:
if args.param and not args.custom:
    import sys
    print('Flaga --param ignorowana — działa tylko z --custom.', file=sys.stderr)
```

**Simulator construction pattern** (copy verbatim from `main.py` lines 21-27):
```python
# main.py lines 21-27 — SPHSimulator(...) call shape — exact reuse:
sim = SPHSimulator(
    nU=args.nU, nSUS=args.nSUS, K0=DEFAULT_K0, K1=K1,
    F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
    phi=DEFAULT_PHI, rho=DEFAULT_RHO,
    strategy_fn=STRATEGIES[args.strategy],
    params=params, seed=args.seed,
)
```

---

### `sphsim/cli/repl.py` (MODIFY — add `do_custom` + `do_run`, modify `do_strategies` + `do_help`)

**Analog 1 (do_strategies modification):** `sphsim/cli/repl.py` lines 68-75 (current Phase 2).
**Analog 2 (do_strategy method signature for do_custom/do_run):** `sphsim/cli/repl.py` lines 78-109.
**Analog 3 (error message format):** `sphsim/cli/repl.py` lines 84, 90.

**Existing `do_strategies` pattern** (lines 68-75):
```python
# repl.py lines 68-75 — current Phase 2:
def do_strategies(self, arg):
    """Wyświetl listę wbudowanych strategii."""
    print("Dostępne strategie:")
    for name in STRATEGIES.keys():
        mod = importlib.import_module(f'sphsim.strategies.{name}')
        description = mod.STRATEGY_META['description']
        # Padding nazwy do 12 znaków, separator em-dash z otaczającymi spacjami (D-29).
        print(f"  {name:<12}— {description}")
```

**Phase 3 do_strategies modification** (D-50 — suffix `[custom]` + dispatch namespace):
```python
def do_strategies(self, arg):
    """Wyświetl listę wbudowanych strategii (z suffixem [custom] dla załadowanych runtime)."""
    from sphsim.strategies import BUILTIN_STRATEGIES   # D-49 snapshot
    print("Dostępne strategie:")
    for name in STRATEGIES.keys():
        # Dispatch namespace: built-in vs custom (D-46 — sphsim.custom.X)
        if name in BUILTIN_STRATEGIES:
            mod = importlib.import_module(f'sphsim.strategies.{name}')
            suffix = ''
        else:
            mod = importlib.import_module(f'sphsim.custom.{name}')   # D-46 private namespace
            suffix = ' [custom]'
        description = mod.STRATEGY_META['description']
        print(f"  {name:<12}— {description}{suffix}")
```

**Existing `do_strategy` method signature pattern** (lines 78-109 — copy for do_custom/do_run):
```python
# repl.py line 78-90 — current Phase 2 (error UX pattern):
def do_strategy(self, arg):
    """Wyświetl szczegóły strategii: opis, parametry, baseline KPI."""
    name = arg.strip()
    if name == '':
        # D-32 verbatim
        print("Użycie: strategy <nazwa>. Wpisz 'strategies' żeby zobaczyć listę.")
        return
    if name not in STRATEGIES:
        # D-31 — live list z STRATEGIES.keys()
        available = ', '.join(STRATEGIES.keys())
        print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
        return
    ...
```

**Phase 3 `do_custom` method** (NEW — copy method signature + error pattern from do_strategy):
```python
def do_custom(self, arg):
    """Załaduj custom strategię z pliku .py [k=v dla params]."""
    from sphsim.strategies.loader import load_custom, parse_custom_params, LoaderError
    parts = arg.split()
    if not parts:
        # Echo D-32/D-42 pattern z do_strategy:
        print("Użycie: custom <ścieżka> [param=wartość ...].")
        return
    path, *param_tokens = parts
    # Check reload — read sys.modules przed load_custom (loader sam też patrzy ale komunikat
    # robi wywołujący — D-46 separation).
    basename = os.path.splitext(os.path.basename(path))[0]
    was_loaded = f'sphsim.custom.{basename}' in sys.modules
    try:
        name, fn, meta = load_custom(path)
    except LoaderError as e:
        print(e.args[0])   # D-48 inline polski, do REPL stdout (NIE stderr — UAT widzi w transcript)
        return
    try:
        params = parse_custom_params(param_tokens, meta)
    except LoaderError as e:
        print(e.args[0])
        return
    STRATEGIES[name] = fn   # D-46 — rejestracja w wywołującym
    verb = 'Przeładowano' if was_loaded else 'Załadowano'
    print(f"{verb} custom strategię '{name}'.")
```

**Phase 3 `do_run` method** (NEW — composite: parser z do_strategy + simulator build z main.py):
```python
def do_run(self, arg):
    """Uruchom symulację: run <nazwa> [param=wartość ...]."""
    from sphsim.core.simulator import SPHSimulator
    from sphsim.cli.output import format_human
    from sphsim.config import (DEFAULT_NU, DEFAULT_NSUS, DEFAULT_K0, DEFAULT_K1,
                                DEFAULT_F, DEFAULT_T, DEFAULT_KAPPA, DEFAULT_ALPHA,
                                DEFAULT_PHI, DEFAULT_RHO)
    from sphsim.strategies import BUILTIN_STRATEGIES
    parts = arg.split()
    if not parts:
        # Verbatim z D-42:
        print("Użycie: run <nazwa> [param=wartość ...]. Wpisz 'strategies' żeby zobaczyć dostępne.")
        return
    name, *kv_tokens = parts
    if name not in STRATEGIES:
        # Verbatim z do_strategy line 89-90 pattern:
        available = ', '.join(STRATEGIES.keys())
        print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
        return
    # Params z meta + tokens (delegate do loader.parse_custom_params):
    from sphsim.strategies.loader import parse_custom_params, LoaderError
    if name in BUILTIN_STRATEGIES:
        mod = importlib.import_module(f'sphsim.strategies.{name}')
    else:
        mod = importlib.import_module(f'sphsim.custom.{name}')
    try:
        params = parse_custom_params(kv_tokens, mod.STRATEGY_META)
    except LoaderError as e:
        print(e.args[0]); return
    # Simulator build — env defaults z config.py (Phase 5 doda override):
    sim = SPHSimulator(
        nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, K0=DEFAULT_K0, K1=DEFAULT_K1,
        F=DEFAULT_F, T=DEFAULT_T, kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA,
        phi=DEFAULT_PHI, rho=DEFAULT_RHO,
        strategy_fn=STRATEGIES[name], params=params, seed=42,
    )
    res = sim.run()
    # Format human — fabricate `args`-like ns dla format_human(args, res, K1, verbose):
    import argparse as _ap
    fake_args = _ap.Namespace(strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS,
                              T=DEFAULT_T, kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA)
    print(format_human(fake_args, res, DEFAULT_K1, verbose=False))   # D-41 — bez --json/verbose
```

**Existing `do_help` pattern** (lines 46-52 — extend):
```python
# repl.py lines 46-52 — Phase 2:
def do_help(self, arg):
    """Wyświetl listę dostępnych komend."""
    print("Dostępne komendy:")
    print("  help               — Wyświetl tę listę komend.")
    print("  exit               — Zakończ sesję (alternatywnie Ctrl+D).")
    print("  strategies         — Wyświetl listę wbudowanych strategii.")
    print("  strategy <nazwa>   — Wyświetl szczegóły strategii (parametry, baseline KPI).")
```

**Phase 3 do_help modification** (add 2 lines per Phase 2 D-33 carry-forward + D-50):
```python
def do_help(self, arg):
    """Wyświetl listę dostępnych komend."""
    print("Dostępne komendy:")
    print("  help                            — Wyświetl tę listę komend.")
    print("  exit                            — Zakończ sesję (alternatywnie Ctrl+D).")
    print("  strategies                      — Wyświetl listę dostępnych strategii.")
    print("  strategy <nazwa>                — Szczegóły strategii (parametry, baseline KPI).")
    print("  custom <ścieżka> [k=v ...]      — Załaduj custom strategię z pliku .py.")
    print("  run <nazwa> [k=v ...]           — Uruchom symulację (built-in lub custom).")
```

**Style note:** padding z 19 → 32 znaków bo `custom <ścieżka> [k=v ...]` jest dłuższe — utrzymaj kolumnowy align (CONVENTIONS.md §Formatting "vertical alignment"). Alternatywnie zachowaj 19 i shorten teksty.

---

## Shared Patterns

### Polski w komunikatach + identyfikatory po angielsku
**Source:** PROJECT.md Constraint "polski w komentarzach, komunikatach CLI"; `sphsim/cli/repl.py` line 90 (`f"Strategia '{name}' nie istnieje. Dostępne: {available}."`).
**Apply to:** Wszystkie strings w `loader.py`, `template.py`, `test_loader.py`, error messages w `main.py`/`repl.py` modyfikacjach.
**Pattern:**
```python
# repl.py line 90:
print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
# Identyfikatory po angielsku (LoaderError, load_custom, BUILTIN_STRATEGIES) — spójność z Phase 1/2.
```

### Stdlib-only imports
**Source:** PROJECT.md Constraint "Python 3.7+ stdlib only"; `sphsim/cli/repl.py` lines 15-21 (`atexit`, `cmd`, `importlib`, `os`, `readline`).
**Apply to:** `loader.py` (importlib.util, inspect, os, sys), `test_loader.py` (unittest, tempfile, textwrap, os, sys), `template.py` (zero importów lub `random`).

### Fail-fast walidacja zero side-effects
**Source:** RESEARCH.md Pitfall #2; Phase 1 argparse type check; Phase 2 D-25 invariant test.
**Apply to:** `loader.py.load_custom` — registration `STRATEGIES[name] = fn` robi WYWOŁUJĄCY (D-46), loader returns tuple. `sys.modules.pop` cleanup po failed `exec_module` (Pitfall #2).

### Vertical alignment dla constants + add_argument
**Source:** `sphsim/config.py` lines 4-13; `sphsim/cli/args.py` lines 44-57; CONVENTIONS.md §Formatting.
**Apply to:** Modyfikacje `args.py` (linia `--param`, `--custom`).
**Pattern:**
```python
# config.py lines 4-9 — aligned z extra spaces:
DEFAULT_NU    = 250
DEFAULT_NSUS  = 20
DEFAULT_K0    = 100
# args.py lines 44-49 — kolumnowo wyrównane `type=...`, `default=...`:
p.add_argument('--zeta',       type=float, default=0.5,   help='[naive] Frakcja COMMIT (0..1)')
p.add_argument('--max_phase',  type=int,   default=3,     help='[threshold] Max faza COMMIT')
```

### Module docstring w nowych modułach
**Source:** `sphsim/cli/repl.py` lines 1-14; `tests/test_strategy_meta_consistency.py` lines 1-15.
**Apply to:** `loader.py`, `test_loader.py`, `examples/custom_strategy_template.py`.
**Pattern:** Multi-line `"""..."""`, polski, wymienia (a) cel modułu, (b) eksportowane symbole, (c) stdlib-only confirmation, (d) referencje do decision IDs (D-XX).

### Error message inline jednolinijka (D-48)
**Source:** `sphsim/cli/repl.py` lines 84, 90, 117 (`f"Strategia '{name}' nie istnieje. Dostępne: {available}."`).
**Apply to:** Wszystkie `raise LoaderError(...)` w `loader.py` + `print(...)` w `do_custom`/`do_run`/`main.py custom branch`.
**Pattern:** Jedna linia, polski, czasem z listą dostępnych po dwukropku. Bez multi-line "Sprawdź:" sections (D-48 explicit reject).

### Live importlib import (zamiast cache)
**Source:** `sphsim/cli/repl.py` lines 72, 94 (`importlib.import_module(f'sphsim.strategies.{name}')`).
**Apply to:** Modyfikacja `do_strategies` (D-50) — dodaj dispatch `sphsim.custom.X` dla custom strategii. Modyfikacja `do_run` — analogiczny dispatch dla meta lookup.

---

## No Analog Found

| File / Capability | Reason |
|------|--------|
| `LoaderError(Exception)` class | Phase 1/2 nie mają żadnego custom exception — to pierwszy w repo. Spec D-48: minimal `class LoaderError(Exception): pass`. |
| `spec_from_file_location` + `module_from_spec` | Repo używa tylko `importlib.import_module` (statyczny dotted path). Plugin loader pattern — pierwszy raz. RESEARCH.md Pattern 1 daje verbatim mechanikę. |
| Banner `[OSTRZEŻENIE] Ładuję arbitralny kod...` | Brak istniejących banner-style print'ów w repo. Format z D-45 spec. |
| `parse_custom_params(tokens, meta)` typed conversion | Phase 1/2 robią parsing przez argparse `type=float` na poziomie CLI; runtime conversion z meta to nowa zdolność. Częściowy analog: `strategy_naive` line 9 (`float(p.get('zeta', 0.5))`) — runtime cast z `p` dict — ale to per-strategy, nie centralny parser. |
| `BUILTIN_STRATEGIES = frozenset(...)` | Brak `frozenset` w repo. `frozenset(STRATEGIES.keys())` to standardowy stdlib idiom — RESEARCH.md potwierdza. |
| `sphsim.custom.<basename>` private namespace | Brak istniejących "syntetycznych" namespace'ów. Pattern: zarejestrowanie w `sys.modules` bez prawdziwego parent package'a (RESEARCH.md Pitfall #1 explicit warning że `importlib.reload` tutaj nie zadziała). |

**Planner action:** dla tych 6 capabilities planner musi referować RESEARCH.md sekcje (Pattern 1/2/3 + Common Pitfalls #1/#2/#3) — PATTERNS.md sygnalizuje brak repo analog, RESEARCH ma mechanikę.

---

## Metadata

**Analog search scope:**
- `sphsim/strategies/*.py` (6 plików — `__init__.py` + 5 strategii)
- `sphsim/cli/*.py` (4 pliki — `args.py`, `main.py`, `repl.py`, `output.py`)
- `sphsim/core/simulator.py` (signature reference)
- `sphsim/config.py` (defaults dla `do_run`)
- `tests/test_strategy_meta_consistency.py` (test bootstrap + unittest pattern)

**Files scanned:** 13 Python files (źródło) + 1 test file = 14 total.

**Pattern extraction date:** 2026-05-27.

**Key insight:** Phase 1+2 zostawiły niezwykle spójne wzorce — każdy nowy plik Phase 3 ma exact-match lub close-match analog dla 80%+ jego zawartości. Jedyne NEW patterns (LoaderError, spec_from_file_location, banner) są wyczerpująco udokumentowane w RESEARCH.md z empirycznie zweryfikowanymi przykładami (probe_loader_final.py).
