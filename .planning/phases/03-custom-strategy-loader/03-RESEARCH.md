# Phase 3: Custom strategy loader — Research

**Researched:** 2026-05-27
**Domain:** dynamiczne ładowanie kodu Pythona przez `importlib` + walidacja sygnatury przez `inspect` + integracja z istniejącym `cmd.Cmd` REPL'em i argparse mutex group
**Confidence:** HIGH (CONTEXT.md zamknął większość decyzji; research empirycznie zweryfikował stdlib mechanikę)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Kontrakt pliku custom (Area 1):**
- **D-34:** Nazwa strategii = **basename pliku bez `.py`** (`my_strat.py` → klucz `'my_strat'`). Loader: `os.path.splitext(os.path.basename(path))[0]`. Konflikt z built-in → error (D-49).
- **D-35:** Funkcja strategii ma nazwę **`strategy_<basename>`** (verbatim wzór z built-in `strategy_naive` w `naive.py`). Loader: `getattr(mod, f'strategy_{basename}')` + `callable()` check.
- **D-36:** **Dowolna ścieżka** — absolutna i relatywna, z `os.path.expanduser` + `os.path.abspath`. Bez whitelist katalogów. Bezpieczeństwo przez banner (D-45), nie przez sandbox.
- **D-37:** **Sticky w sesji REPL** — raz załadowana zostaje do `exit`. Brak persistencji do plików. CLI one-shot: rejestracja → `sim.run()` → koniec procesu.
- **D-38:** **Reload przez powtórne wywołanie** — `custom my.py` drugi raz nadpisuje. Mechanika: jeśli `f'sphsim.custom.{basename}'` w `sys.modules`, użyj re-load; inaczej pierwsze ładowanie. Komunikat: `Przeładowano custom strategię 'my_strat'.` lub `Załadowano custom strategię 'my_strat'.`

**Params runtime + komenda `run` (Area 2):**
- **D-39:** **`--param k=v` (CLI, repeatable) + `k=v` w REPL** — jednolity input shape. CLI: `--param zeta=0.7 --param threshold=5`. REPL: `custom my.py zeta=0.7 threshold=5` lub `run my_strat zeta=0.7`. Split na pierwszy `=` (wartość może zawierać `=`).
- **D-40:** **Typy z STRATEGY_META['params']** — single source of truth. Loader konwertuje `'0.75'` → `float('0.75')`. ValueError → polski błąd. Niezadeklarowany param → `Nieznany parametr 'foo' dla strategii 'my_strat'. Dostępne: zeta, threshold.` Nieprzekazany → default z meta.
- **D-41:** **Komenda `run <nazwa> [k=v ...]`** — nowa `do_run` w `SPHShell`. Działa dla built-in i custom jednolicie. Env params z `sphsim/config.py` defaults. Output: `format_human`. Brak `--json` w REPL.
- **D-42:** **`run` bez nazwy** → `Użycie: run <nazwa> [param=wartość ...]. Wpisz 'strategies' żeby zobaczyć dostępne.` **`run nieznana`** → `Strategia 'nieznana' nie istnieje. Dostępne: naive, threshold, phase_prob, incentive, adaptive, my_strat.`
- **D-43:** **Pozycyjne parsing w REPL** — split, pierwszy token = ścieżka/nazwa, reszta `k=v`. Ścieżki ze spacjami **nie wspierane**. Token bez `=` → ostrzeżenie `Pominięto token 'zeta' — oczekiwany format key=value.`

**Mutex CLI + bezpieczeństwo (Area 3):**
- **D-44:** **`--custom` jako trzeci człon mutex group** w `sphsim/cli/args.py`. Backwards compat: `--strategy X` nadal valid, 8 fixtures z `tests/fixtures/baseline_v1/` musi pass.
- **D-45:** **Cichy jednolinijkowy banner pre-import** w obu trybach. Format: `[OSTRZEŻENIE] Ładuję arbitralny kod Pythona z: <abspath>`. Stdout, **przed** `exec_module`. Bez confirmation prompt, bez `--no-warn`.
- **D-46:** **Loader jako osobny moduł** — `sphsim/strategies/loader.py`. Eksportuje `load_custom(path: str) -> tuple[str, callable, dict]`. Importuje do **private namespace `sphsim.custom.<basename>`** (przez `importlib.util.spec_from_file_location` + `module_from_spec`). Rejestrację robi **wywołujący**.

**Walidacja + listing + template (Area 4):**
- **D-47:** **4-warstwowa walidacja** w `load_custom` (CONTEXT.md miejscami pisze "3-warstwowa" ale wymienia 4 layers): (1) Import (catch SyntaxError/ImportError/runtime), (2) Funkcja istnieje + callable, (3) Sygnatura exact `(dev, l, s, phi, kappa, rho, h, p)` — pozwala *args/**kwargs jako wrapper escape, (4) STRATEGY_META validation (dict z kluczami `description`, `params`, `baseline_kpi`). Strategia NIE jest rejestrowana przy żadnym błędzie (fail-fast, zero side effects).
- **D-48:** **`LoaderError` jako custom exception** w `sphsim/strategies/loader.py`. Inline jednolinijkowe polskie komunikaty.
- **D-49:** **Konflikt nazw: error** — `if basename in BUILTIN_STRATEGIES → LoaderError("Nazwa '...' koliduje z wbudowaną strategią. Zmień nazwę pliku.")`. **`BUILTIN_STRATEGIES = frozenset(STRATEGIES.keys())`** — dodawane w `sphsim/strategies/__init__.py` jako stała (snapshot Phase 1).
- **D-50:** **Listing z suffixem `[custom]`** — `do_strategies` modyfikacja. Argparse `--strategy choices` = `list(BUILTIN_STRATEGIES)` (snapshot). Padding 12 znaków zachowany.
- **D-51:** **`examples/custom_strategy_template.py`** — ~30-50 linii, header docstring polski, `strategy_custom_strategy_template` z `p.get('max_phase', 4)`, pełen `STRATEGY_META`. Acceptance: `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json` musi działać. Plik commitowany.
- **D-52:** **`examples/` jako katalog projektu** — tylko `examples/custom_strategy_template.py`. Brak `__init__.py`, brak `.gitignore`.

### Claude's Discretion

- Format banner D-45: jednolinijka, **stdout** (preferred — banner to informacja, nie błąd).
- Mechanizm reload (D-38): `importlib.reload(mod)` **vs** ponowny `spec_from_file_location` + `module_from_spec`. **Research zalecenie:** **manual re-load** (Option C poniżej, fresh spec + exec) — `importlib.reload()` ma blokujące pitfalls dla dotted namespaces (zob. Common Pitfalls #1).
- `do_strategies` w SPHShell: live import vs cache — **preferuj live import** (custom strategie wymagają dispatchu `sphsim.custom.X`, cache by go komplikował).
- `do_run` `--verbose` per cykl — **nie**. REPL output zwięzły.
- Test coverage: osobny `tests/test_loader.py` (różne odpowiedzialności) — zalecane.
- `--param` w argparse jako `action='append'` — **TAK**, default `[]`.
- Format error gdy `--param` bez `--custom` — **graceful**: `Flaga --param ignorowana — działa tylko z --custom.`

### Deferred Ideas (OUT OF SCOPE)

- Komenda `unload <nazwa>`, `compare <strategia>` (Phase 4), override env params w REPL (Phase 5), `batch` (Phase 7), `--no-warn` flag, confirmation prompt `[y/N]`, whitelist katalogów, session state object, tab autocomplete, JSON format dla `--params`, dynamic argparse z STRATEGY_META, persistencja do `~/.sphsim_strategies/`, multi-line error messages, `StrategyMeta` dataclass, rich/colored output.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STRAT-03 | Użytkownik może załadować custom strategię z pliku `.py` komendą `/custom <ścieżka>` lub flagą `--custom <ścieżka>` | `importlib.util.spec_from_file_location` + `module_from_spec` + `exec_module` workflow (verified empirically); D-44 `--custom` w mutex, D-46 `sphsim/strategies/loader.py`, REPL `custom <ścieżka>` (bez slasha per Phase 2 D-17 override) |
| STRAT-04 | Loader waliduje że plik zawiera funkcję o wymaganej sygnaturze i jasno komunikuje błędy (brak funkcji, zła sygnatura, exception) | 4-warstwowa walidacja D-47 z polskimi komunikatami D-48; `inspect.signature` exact match na 8 nazw `(dev, l, s, phi, kappa, rho, h, p)` z escape dla `*args/**kwargs` (zob. Code Examples) |
| STRAT-05 | Projekt zawiera przykładowy szablon `examples/custom_strategy_template.py` z komentarzami po polsku | D-51 spec: ~30-50 linii, polskie komentarze, full STRATEGY_META, deterministycznie uruchamialny przez `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json` |
</phase_requirements>

## Summary

Phase 3 implementuje czysty plugin-loader pattern oparty na stdlib `importlib.util.spec_from_file_location` + `module_from_spec` + `exec_module` — to standardowy idiom Python 3.4+ dla ładowania `.py` z arbitralnej ścieżki, **już używany** w stdlib (`runpy`) i każdym major plugin systemie (pytest, Flask CLI, Sphinx). CONTEXT.md (D-34..D-52) jest niezwykle kompletny — research **nie redecyduje** żadnej locked decision, tylko surfacuje (a) test taxonomy dla Nyquist VALIDATION.md, (b) dokładną mechanikę stdlib API z empirycznie zweryfikowanymi edge cases, (c) integration-point pseudo-code z numerami linii z istniejącego repo, (d) konkretne acceptance commands dla każdego z 5 ROADMAP SCs.

Krytyczne empiryczne ustalenie z probe'owania (Common Pitfall #1 niżej): **`importlib.reload()` NIE DZIAŁA dla dotted namespace `sphsim.custom.X`** bo parent `sphsim.custom` nie istnieje jako prawdziwy package (no `__path__`, no `find_spec`). Manual re-load przez fresh `spec_from_file_location` + `module_from_spec` + `exec_module` + `sys.modules` replacement jest jedyną poprawną opcją. To zmienia D-38 implementację (CONTEXT.md sugerował obie ścieżki w Claude's Discretion — research rozstrzyga: zawsze manual re-load).

**Primary recommendation:** zaimplementuj `load_custom(path) → (basename, fn, meta)` jako pure function w `sphsim/strategies/loader.py` z 4 warstwami walidacji **w stałej kolejności** (path-resolve → spec/exec → callable check → signature check → meta check). Rejestrację `STRATEGIES[basename] = fn` zostaw wywołującemu (CLI main.py / REPL `do_custom`). Re-load = zawsze fresh spec, nigdy `importlib.reload()`. Test loadera = osobny `tests/test_loader.py` (8+ przypadków: 5 error layers + happy + reload + conflict).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Ładowanie `.py` z arbitralnej ścieżki | Strategy Layer (`sphsim/strategies/loader.py`) | — | Loader jest częścią strategii — paralelnie z `naive.py`, ale meta-rola: rejestracja w `STRATEGIES`. Pure function, testowalna w izolacji. |
| Walidacja sygnatury + meta | Strategy Layer (`loader.py`) | — | Walidacja kontraktu strategii nie jest CLI concern'em; loader trzyma niezmiennik. |
| Banner bezpieczeństwa | Strategy Layer (`loader.py`) | CLI/REPL (re-emisja?) | Banner drukowany **w loaderze**, przed `exec_module` (D-45) — `print(..., file=sys.stdout)`. Wywołujący nie musi go duplikować. |
| Parsowanie `--param k=v` (CLI) | CLI Layer (`sphsim/cli/main.py` helper) | Loader (typy z meta) | CLI parsuje raw `[k=v, ...]` z `args.param`; loader dostarcza typed conversion via meta. |
| Parsowanie `k=v` (REPL) | REPL Layer (`sphsim/cli/repl.py` helper) | Loader (typy z meta) | Symetryczna do CLI mechanika; współdzieli funkcję typu `parse_params_from_meta(tokens, meta)`. |
| Rejestracja w `STRATEGIES[name] = fn` | CLI/REPL Layer (wywołujący) | — | Loader zwraca tuple, **wywołujący** robi side effect. Pozwala na unit-test loadera bez globalnego state'u. |
| Komenda `run <nazwa>` (REPL) | REPL Layer (`do_run` w `SPHShell`) | Simulator | Wywołuje `SPHSimulator` z `params` zbudowanymi z meta + defaults z `sphsim/config.py`. Format output: `format_human` z `output.py`. |
| Listing z `[custom]` suffix | REPL Layer (`do_strategies` modyfikacja) | Strategy Layer (`BUILTIN_STRATEGIES` stała) | `do_strategies` iteruje po `STRATEGIES.keys()`, dispatch namespace: `sphsim.strategies.<name>` jeśli `name in BUILTIN_STRATEGIES` else `sphsim.custom.<name>`. |
| Mutex group `--custom` jako trzeci człon | CLI Layer (`sphsim/cli/args.py`) | — | Argparse mechanika — bez zmian w Simulator/Strategy layer. |

## Standard Stack

### Core (wszystko stdlib — Python 3.7+)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `importlib.util` | stdlib | `spec_from_file_location`, `module_from_spec` — ładowanie `.py` z arbitralnej ścieżki | Standard pattern Python 3.4+; udokumentowany w Python docs jako kanoniczny sposób na "import module from file path". Używany przez pytest, Sphinx, Flask. |
| `importlib` | stdlib | `sys.modules` lookup dla re-load detection | Zerowy overhead, mutowalny dict — natural fit. |
| `inspect` | stdlib | `inspect.signature(fn).parameters` — walidacja sygnatury | Standard reflection API. `Parameter.kind` enum daje POSITIONAL_OR_KEYWORD / VAR_POSITIONAL / VAR_KEYWORD / KEYWORD_ONLY do dokładnego sprawdzenia. |
| `os.path` | stdlib | `expanduser`, `abspath`, `splitext`, `basename`, `exists` | Path normalizacja przed spec_from_file_location. |
| `sys` | stdlib | `sys.modules` dict + `sys.stdout` dla banneru + `sys.exit(1)` przy LoaderError w CLI | — |
| `argparse` | stdlib | `add_argument('--custom', type=str)` w istniejącym mutex; `--param` z `action='append'` | Existing pattern w `sphsim/cli/args.py`. |
| `cmd` | stdlib | `do_custom`, `do_run` jako nowe metody w istniejącej `SPHShell(cmd.Cmd)` | Phase 2 D-33 — kontynuacja. |
| `unittest` | stdlib | Test suite dla loadera (osobny `tests/test_loader.py`) | Phase 2 użył `unittest` w `test_strategy_meta_consistency.py` — spójność. |

### Supporting (już w repo)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `sphsim.strategies.STRATEGIES` | wewn. | Mutable registry — Phase 3 robi `STRATEGIES[basename] = fn` runtime | W wywołującym po `load_custom()` |
| `sphsim.strategies.BUILTIN_STRATEGIES` | **NEW** stała | Snapshot `frozenset(STRATEGIES.keys())` z Phase 1 — D-49 collision detection | W `load_custom()` przed rejestracją; w `do_strategies` dispatch |
| `sphsim.core.simulator.SPHSimulator` | istn. | Budowany z `strategy_fn=fn, params=dict, ...` po loadzie | W CLI main.py branch `if args.custom:` + REPL `do_run` |
| `sphsim.cli.output.format_human` | istn. | Output `do_run` w REPL (krótki, czytelny) | REPL `do_run` |
| `sphsim.config.DEFAULT_*` | istn. | env defaults dla `do_run` (Phase 5 doda override) | REPL `do_run` budujący SPHSimulator |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `importlib.util.spec_from_file_location` | `importlib.import_module` z manipulacją `sys.path` | Brudniejsze — modyfikuje globalny `sys.path`, leaks między testami. **Decision:** zostajemy z `spec_from_file_location` (D-46). |
| `importlib.reload()` dla re-load | Manual re-load via fresh spec | `reload()` nie działa dla `sphsim.custom.X` (zob. Common Pitfall #1). **Decision:** **zawsze manual re-load** — research override Claude's Discretion w D-38. |
| `exec(open(path).read())` | `spec_from_file_location` + `exec_module` | `exec()` nie tworzy module object'u, nie ma `__name__`, brak namespace izolacji, łamie `inspect.getsource`. **Decision:** spec_from_file_location (verified). |
| `runpy.run_path(path)` | spec_from_file_location | `runpy` zwraca dict zamiast module objektu — `getattr(mod, ...)` i `inspect.signature` wymagają module. **Decision:** spec_from_file_location. |
| Cache STRATEGY_META lookups w `do_strategies` | Live `importlib.import_module` per iteration | Phase 2 D-29 już używa live import — spójność, brak invalidation problem. **Decision:** live import (Claude's Discretion z D-50 confirmed). |

**Installation:**

```bash
# Brak — wszystko stdlib (PROJECT.md constraint zachowany).
```

**Version verification:**

```bash
python3 --version
# Confirmed: Python 3.14.3 on dev machine; Project minimum: 3.7+ (PROJECT.md)
# spec_from_file_location: dostępne od 3.4
# inspect.Parameter.VAR_POSITIONAL: dostępne od 3.3
# Wszystko poniżej 3.7 minimum — safe.
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (none — wszystko stdlib) | — | — | — | — | N/A | Approved (no install) |

**Packages removed due to slopcheck [SLOP] verdict:** none — Phase 3 nie dodaje żadnego zewnętrznego pakietu.
**Packages flagged as suspicious [SUS]:** none.

Phase 3 zachowuje PROJECT.md constraint "Python 3.7+ stdlib only" — pierwsza zewnętrzna zależność (`matplotlib`) dopiero w Phase 6.

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────┐         ┌─────────────────────────┐
│  USER (CLI one-shot)    │         │  USER (REPL session)    │
│  python sph_sim.py      │         │  python sph_sim.py      │
│   --custom my.py        │         │   --interactive         │
│   --param zeta=0.7      │         │  > custom my.py zeta=.7 │
│   --seed 42 --json      │         │  > run my_strat         │
└────────┬────────────────┘         └────────┬────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────────────┐         ┌─────────────────────────┐
│  sphsim/cli/args.py     │         │  sphsim/cli/repl.py     │
│  parse_args() z mutex   │         │  SPHShell.do_custom(arg)│
│  {--interactive |       │         │  SPHShell.do_run(arg)   │
│   --strategy | --custom}│         │  Pozycyjny parser k=v   │
│  + --param (append)     │         │                         │
└────────┬────────────────┘         └────────┬────────────────┘
         │                                   │
         │  if args.custom:                  │  do_custom: load + register
         ▼                                   ▼  do_run: dispatch + simulate
         └─────────────┐         ┌───────────┘
                       ▼         ▼
              ┌─────────────────────────────────────┐
              │  sphsim/strategies/loader.py        │
              │  load_custom(path) → (name,fn,meta) │
              │  ┌──────────────────────────────┐   │
              │  │ 1. PATH RESOLVE              │   │
              │  │    expanduser+abspath        │   │
              │  │    exists check              │   │
              │  ├──────────────────────────────┤   │
              │  │ 2. NAME EXTRACT              │   │
              │  │    basename(path)[:-3]       │   │
              │  │    BUILTIN collision → ERR   │   │
              │  ├──────────────────────────────┤   │
              │  │ 3. BANNER (sys.stdout)       │   │
              │  │    [OSTRZEŻENIE] ...         │   │
              │  ├──────────────────────────────┤   │
              │  │ 4. SPEC + EXEC               │   │
              │  │  spec_from_file_location     │   │
              │  │  module_from_spec            │   │
              │  │  sys.modules[name] = mod     │   │
              │  │  spec.loader.exec_module(mod)│◄──┼── LAYER 1: catch all exc
              │  ├──────────────────────────────┤   │
              │  │ 5. fn = getattr(mod, fname)  │◄──┼── LAYER 2: AttributeError / not callable
              │  ├──────────────────────────────┤   │
              │  │ 6. inspect.signature check   │◄──┼── LAYER 3: signature mismatch
              │  ├──────────────────────────────┤   │
              │  │ 7. STRATEGY_META check       │◄──┼── LAYER 4: meta schema
              │  └──────────────────────────────┘   │
              │  RETURN (name, fn, meta)            │
              └────────┬─────────────────┬──────────┘
                       │ LoaderError     │ OK
                       ▼                 ▼
              ┌─────────────────┐  ┌─────────────────────────┐
              │ Polski komunikat│  │ Caller registruje:      │
              │ → stderr (CLI)  │  │   STRATEGIES[name] = fn │
              │ → stdout (REPL) │  │ → SPHSimulator(fn,p,...)│
              │ sys.exit(1) CLI │  │ → sim.run()             │
              └─────────────────┘  │ → format_human / json   │
                                   └─────────────────────────┘
```

Data flow: user input → CLI/REPL parser → loader.py (sequential 4 validation layers, fail-fast) → caller registers + simulates → output.

### Recommended Project Structure (DELTA vs current repo)

```
sphsim/
├── strategies/
│   ├── __init__.py         # +BUILTIN_STRATEGIES = frozenset(STRATEGIES.keys())  ← NEW stała
│   ├── loader.py           # NEW — load_custom() + LoaderError + parse helpers
│   ├── naive.py            # unchanged
│   ├── threshold.py        # unchanged
│   ├── phase_prob.py       # unchanged
│   ├── incentive.py        # unchanged
│   └── adaptive.py         # unchanged
├── cli/
│   ├── args.py             # MODIFY — mutex.add_argument('--custom') + --param append
│   ├── main.py             # MODIFY — second early-branch: if args.custom: ...
│   ├── repl.py             # MODIFY — do_custom, do_run, do_strategies suffix, do_help
│   ├── output.py           # unchanged
│   └── __init__.py         # unchanged
├── core/                   # unchanged (simulator.py, device.py, model.py)
├── config.py               # unchanged
├── __init__.py             # unchanged (lub eksport BUILTIN_STRATEGIES jeśli planner uzna)
└── __main__.py             # unchanged

examples/                   # NEW katalog
└── custom_strategy_template.py   # NEW — D-51 template, polskie komentarze

tests/
├── test_strategy_meta_consistency.py   # unchanged (invariant Phase 2)
└── test_loader.py          # NEW — 8+ przypadków loadera (D-47 layers, reload, conflict, happy path)

scripts/
└── verify_phase3.sh        # NEW — Phase 3 exit gate (paralelnie do verify_phase1.sh)
```

### Pattern 1: spec_from_file_location + module_from_spec + exec_module

**What:** kanoniczny stdlib pattern dla "import module from file path" — Python 3.4+. Tworzy `ModuleSpec`, materializuje `ModuleType` instance, rejestruje w `sys.modules`, wykonuje plik w izolowanym namespace.

**When to use:** **zawsze** dla custom strategy loadingu. Nie używaj `exec()` (brak module obj), nie używaj `runpy.run_path()` (dict zamiast moduł), nie używaj `__import__` z manipulacją `sys.path`.

**Example (verified empirycznie — `/tmp/probe_loader_final.py`):**

```python
# Source: docs.python.org/3/library/importlib.html#importlib.util.spec_from_file_location
import importlib.util
import sys

def _load_module_from_path(full_name: str, path: str):
    spec = importlib.util.spec_from_file_location(full_name, path)
    if spec is None:
        # Może wrócić None dla nie-.py rozszerzeń (np. .txt)
        raise LoaderError(f"Ścieżka {path} nie wygląda na plik Pythona (.py).")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = mod   # MUST register PRZED exec dla circular import safety
    spec.loader.exec_module(mod)    # ← SyntaxError/runtime błędy wybuchają TUTAJ
    return mod
```

### Pattern 2: `inspect.signature` exact-arity-and-names check + escape dla wrappers

**What:** sprawdzanie że funkcja ma dokładnie nazwy `(dev, l, s, phi, kappa, rho, h, p)` w tej kolejności, **ale** pozwala na `*args`/`**kwargs` jako legitymate wrapper escape (rzadkie ale legit — np. decorator).

**Why escape:** użytkownik może mieć `def strategy_my(*args, **kwargs): return inner(*args, **kwargs)` jako thin wrapper.

**Example (verified empirycznie):**

```python
import inspect

EXPECTED = ('dev', 'l', 's', 'phi', 'kappa', 'rho', 'h', 'p')

def _validate_signature(fn, fn_name: str):
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    has_var_pos = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params)
    # Escape: jeśli funkcja używa *args, akceptujemy (wrapper pattern)
    if has_var_pos:
        return
    # Inaczej: pierwsze 8 parametrów musi mieć dokładnie te nazwy
    actual_names = tuple(p.name for p in params[:8])
    if actual_names != EXPECTED:
        raise LoaderError(
            f"Funkcja '{fn_name}' ma sygnaturę {sig}. "
            f"Oczekiwana: ({', '.join(EXPECTED)})."
        )
```

**Empirycznie zweryfikowane przypadki:**
- `def good(dev, l, s, phi, kappa, rho, h, p)` → match ✓
- `def wrong_order(dev, s, l, ...)` → reject (l↔s swap) ✓
- `def too_few(dev, l, s, phi, kappa, rho, h)` → reject (7) ✓
- `def wrap(*args)` → accept (wrapper escape) ✓
- `lambda dev, l, s, phi, kappa, rho, h, p: 'COMMIT'` → match ✓
- `def extra(dev, l, s, phi, kappa, rho, h, p, extra=1)` → match (pierwsze 8 ok) ✓
- `def kwonly(..., *, mode='x')` → match ✓
- Bound method `obj.method(self, dev, l, s, ...)` → match (self stripped przez `inspect.signature` automatycznie) ✓
- `inspect.signature(NotCallable())` → `TypeError` — handle PRZED `inspect.signature` przez `callable()` check.

### Pattern 3: Manual re-load (fresh spec) zamiast `importlib.reload()`

**What:** za drugim `custom my.py` w sesji, zamiast `importlib.reload(sys.modules[name])` (który **NIE DZIAŁA** dla dotted namespace bez prawdziwego parent — zob. Pitfall #1), używamy **świeżej** sekwencji `spec_from_file_location` + `module_from_spec` + `sys.modules[name] = new_mod` + `exec_module(new_mod)`.

**Example (verified — patrz `/tmp/probe_loader_final.py`):**

```python
def load_custom(path: str):
    # ... path resolve, name extract, banner ...
    full_name = f'sphsim.custom.{basename}'
    is_reload = full_name in sys.modules
    spec = importlib.util.spec_from_file_location(full_name, abspath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = mod      # nadpisuje stary jeśli był
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        sys.modules.pop(full_name, None)   # cleanup po failed re-load
        raise LoaderError(f"Błąd podczas importu pliku {abspath}: {type(e).__name__}: {e}")
    # ... walidacja, return ...
    # Wywołujący widzi is_reload przez sygnał "Przeładowano" vs "Załadowano"
```

### Anti-Patterns to Avoid

- **`importlib.reload(sys.modules[name])` dla dotted namespace `sphsim.custom.X`** — wybucha `ImportError: parent 'sphsim.custom' not in sys.modules` (Python 3.14) lub `ModuleNotFoundError: spec not found` jeśli próbujemy zarejestrować syntetyczny parent. Zob. Common Pitfall #1.
- **Brak `sys.modules[full_name] = mod` PRZED `exec_module`** — circular imports w pliku user'a zobaczą `ImportError`. Stdlib docs explicit: register first, exec after.
- **`exec(open(path).read())`** — brak module object'u, `inspect.signature` failuje, brak namespace izolacji, leaks zmienne globalne.
- **Modyfikacja `sys.path` zamiast `spec_from_file_location`** — leaks między uruchomieniami, conflicts z pakietami o tej samej nazwie.
- **`STRATEGIES[name] = fn` w samym loaderze (przed walidacją sukces)** — narusza fail-fast (partial state przy błędzie); D-46 wymaga że side effect rejestracji robi wywołujący.
- **Banner po `exec_module`** — gdyby plik wybuchł przy imporcie, user nie wie skąd kod. Banner MUSI być PRZED `exec_module`.
- **`argparse` `choices=list(STRATEGIES.keys())` dla `--strategy`** — po Phase 3 `STRATEGIES.keys()` ma też custom; argparse parsuje PRZED ładowaniem. **Zmienić na `choices=list(BUILTIN_STRATEGIES)`** (D-50).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ładowanie `.py` z path | `exec(open(path).read())` | `importlib.util.spec_from_file_location` | Brak module obj, brak namespace izolacji, łamie `inspect`. |
| Reload modułu | Custom `del sys.modules[name]; reimport` | Fresh `spec_from_file_location` (Option C powyżej) | Stara mechanika `__pycache__` może zwrócić stale code; fresh spec gwarantuje read-from-disk. |
| Walidacja sygnatury | Custom parsing `fn.__code__.co_varnames` | `inspect.signature(fn).parameters` | `co_varnames` mieszane z local vars, nie tylko parametry. `inspect.signature` to public API. |
| Parsing `--param k=v` | Regex `r'(\w+)=(.+)'` | `tok.split('=', 1)` z guard | `split('=', 1)` natywnie obsługuje `--param json=key=value` (wartości z `=`). Zero zależności. |
| Sprawdzanie czy callable | `hasattr(mod, fn_name) and not None` | `callable(getattr(mod, fn_name, None))` | `callable()` poprawnie odrzuca `None`, atrybuty nie-funkcyjne, bound methods włącznie. |
| Type conversion z meta | `eval(value)` | `type_callable(string_value)` z meta | `eval` to security disaster nawet w educational projekcie. Meta zawiera `float`/`int`/`str` jako sam callable. |

**Key insight:** stdlib `importlib.util` + `inspect` to *kompletny* toolkit dla plugin loaderów — żadne custom code potrzebne. Cały `loader.py` powinien być ≤120 linii (porównawczo: `repl.py` ma 150 linii, `simulator.py` ma 151 linii — spójna skala).

## Common Pitfalls

### Pitfall 1: `importlib.reload()` nie działa dla syntetycznego dotted namespace
**What goes wrong:** drugie wywołanie `custom my.py` → `ImportError: parent 'sphsim.custom' not in sys.modules` lub `ModuleNotFoundError: spec not found for the module 'sphsim.custom.my_strat'`.

**Why it happens:** `importlib.reload()` z source: szuka `__spec__` istniejącego modułu i wymaga że parent `sphsim.custom` ma prawdziwy `find_spec` mechanism (czyli prawdziwy package z `__init__.py` lub namespace package z `__path__`). My **nie tworzymy** prawdziwego `sphsim.custom` packagu — to czysta konwencja nazewnicza dla izolacji.

**Empirycznie zweryfikowane (Python 3.14.3):**

```
ImportError: parent 'sphsim.custom' not in sys.modules
# i nawet po pre-registracji syntetycznego parent:
ModuleNotFoundError: spec not found for the module 'sphsim.custom.my_strat'
```

**How to avoid:** **NIGDY nie używaj `importlib.reload()` w `load_custom`.** Zawsze build fresh `spec_from_file_location`, fresh `module_from_spec`, replace `sys.modules[full_name]`, run `exec_module`. To było empirycznie zweryfikowane jako działające (probe_loader_final.py: `first` → `second` po manual reload).

**Warning signs:** crash na drugim `custom my.py` w tej samej sesji REPL. Test: `tests/test_loader.py::test_reload_picks_up_source_changes`.

### Pitfall 2: `sys.modules` cleanup po failed re-load
**What goes wrong:** load_custom drugi raz; `exec_module` rzuca SyntaxError; `sys.modules['sphsim.custom.my_strat']` zostaje z half-loaded module (lub nawet z fresh empty `ModuleType`). Następne `import sphsim.custom.my_strat` z innego miejsca dostanie corrupted moduł.

**Why it happens:** my zarejestrowaliśmy `sys.modules[full_name] = mod` PRZED `exec_module` (poprawnie — dla circular import safety). Jeśli exec wybuchnie, ten zombie zostaje.

**How to avoid:**

```python
sys.modules[full_name] = mod
try:
    spec.loader.exec_module(mod)
except Exception as e:
    sys.modules.pop(full_name, None)  # cleanup zombie
    raise LoaderError(f"Błąd podczas importu pliku {abspath}: ...")
```

**Warning signs:** strategia widoczna w `STRATEGIES` po failed load (D-47 fail-fast naruszony). Test: `tests/test_loader.py::test_failed_reload_does_not_leave_zombie_in_sys_modules`.

### Pitfall 3: `spec_from_file_location` zwraca `None` dla nie-.py rozszerzeń
**What goes wrong:** user przekazuje `--custom my_strat.txt` (typo); `spec_from_file_location('...', '...txt')` zwraca `None`; następne `module_from_spec(None)` → `AttributeError: 'NoneType' object has no attribute 'loader'`.

**Why it happens:** stdlib filtruje rozszerzenia (heurystycznie). Tylko zarejestrowane source/bytecode/extension suffixes są akceptowane.

**Empirycznie:** verified — `spec_from_file_location('strat', 'strat.txt')` → `None`.

**How to avoid:**

```python
spec = importlib.util.spec_from_file_location(full_name, abspath)
if spec is None or spec.loader is None:
    raise LoaderError(f"Ścieżka {abspath} nie wygląda na plik Pythona (.py).")
```

**Warning signs:** `AttributeError: 'NoneType'`. Test: `tests/test_loader.py::test_rejects_non_py_extension`.

### Pitfall 4: Nieistniejąca ścieżka — `FileNotFoundError` wybucha w `exec_module`, nie w `spec_from_file_location`
**What goes wrong:** user przekazuje `--custom /tmp/nope.py`; `spec_from_file_location` zwraca **valid** `ModuleSpec` (sprawdza tylko że nazwa-rozszerzenia wygląda), `exec_module` wybucha `FileNotFoundError`.

**Empirycznie:**
```
spec on missing path: ModuleSpec(name='nope', loader=<SourceFileLoader>, origin='/tmp/nope.py')
FileNotFoundError at exec_module: [Errno 2] No such file or directory
```

**How to avoid:** dodaj **eksplicytną** `os.path.exists` check PRZED spec_from_file_location dla user-friendly polskiego błędu:

```python
if not os.path.exists(abspath):
    raise LoaderError(f"Plik nie istnieje: {abspath}")
```

Bez tego user dostałby ENG `[Errno 2] No such file or directory` zamiast polskiego "Plik nie istnieje".

**Warning signs:** ENG error message zamiast polskiego. Test: `tests/test_loader.py::test_missing_path`.

### Pitfall 5: `inspect.signature(NotCallable())` rzuca TypeError, nie ValueError
**What goes wrong:** D-47 layer 2 (callable check) musi być PRZED layer 3 (signature check). Jeśli odwrócimy kolejność: `getattr(mod, fn_name)` zwróci np. `int` zamiast funkcji; `inspect.signature(int)` zwróci sygnaturę konstruktora `int`; późniejsza walidacja będzie myląca.

**Empirycznie:** `inspect.signature(NotCallable())` → `TypeError: <obj> is not a callable object`.

**How to avoid:** zachowaj **sekwencję walidacji** w `load_custom`: callable check (D-47 layer 2) MUSI być PRZED signature check (layer 3).

```python
fn = getattr(mod, fn_name, None)
if not callable(fn):
    raise LoaderError(f"Brak funkcji '{fn_name}' w pliku {abspath}. "
                      f"Oczekiwana sygnatura: {fn_name}(dev, l, s, phi, kappa, rho, h, p) -> str.")
# tylko gdy callable wejdziemy w sig check
sig = inspect.signature(fn)
```

**Warning signs:** crash w `inspect.signature` na non-callable. Test: `tests/test_loader.py::test_missing_function`.

### Pitfall 6: Backwards compat — 8 regression fixtures muszą nadal pass
**What goes wrong:** Phase 3 modyfikuje `args.py` (mutex group, --param) i `main.py` (early branch). Jeśli któraś modyfikacja zmieni order of arguments lub default, regression suite (`scripts/regression_check.py`) wybuchnie — Phase 3 acceptance criterion (`--custom` to **nowa** flaga, nie zmienia istniejących).

**Why it happens:** argparse jest wrażliwy na kolejność `add_argument` (wpływa na `--help` output ale nie na parse'owanie). Risk: `--strategy choices=list(STRATEGIES.keys())` zmiana na `choices=list(BUILTIN_STRATEGIES)` — D-50 to **wymaga**, ale `STRATEGIES.keys()` ma na początku Phase 3 te same 5 wartości, więc invariant trzyma.

**How to avoid:** **uruchom `scripts/regression_check.py` po każdej zmianie w `args.py`/`main.py`** (Phase 3 acceptance gate). Verify-phase3.sh musi włączać ten check.

**Warning signs:** "FAIL: X/8 (regresja w: ...)" w regression_check output. Test: `bash scripts/verify_phase3.sh`.

### Pitfall 7: Custom strategy w jednoiterm CLI nie widziany przez argparse `--strategy`
**What goes wrong:** user oczekuje `python sph_sim.py --strategy my_strat` po `--custom my.py`. **Nie zadziała** — argparse parsuje `--strategy` PRZED jakimkolwiek loaderem.

**Why it happens:** CLI one-shot to one-pass — args parsowane na początku `main()`, custom strategie ładowane dopiero w branch'u `if args.custom:`. Po prostu CLI design.

**How to avoid:** custom strategie uruchamia się **wyłącznie** przez `--custom <path>` (CLI) lub przez `run <nazwa>` (REPL — który widzi `STRATEGIES.keys()` runtime). D-50 to dokumentuje ("świadome ograniczenie one-shot CLI"). Nie próbuj robić two-pass argparse — komplikacja > value.

**Warning signs:** user issue: "dlaczego `--strategy my_strat` mówi że nie ma takiej strategii?". Resolution: dokumentacja w `--help` + error message `--strategy: invalid choice: 'my_strat' (choose from 'naive', 'threshold', ...)`. UX OK (argparse natywnie pisze listę choices).

## Runtime State Inventory

> Phase 3 jest częściowo modyfikującą fazą (modyfikacja `args.py`, `main.py`, `repl.py`, `strategies/__init__.py`). Nie jest to rename/refactor/migration — ale dla pewności:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — projekt nie używa baz danych ani persystowanej historii poza `~/.sphsim_history` (readline). Custom strategie są sticky **tylko w sesji** REPL (D-37). | none |
| Live service config | None — projekt nie ma external services (PROJECT.md: lokalny, CLI-only). | none |
| OS-registered state | None — projekt nie używa Task Scheduler, systemd, pm2. | none |
| Secrets/env vars | None — projekt nie używa secrets/env vars (config przez argparse). | none |
| Build artifacts | None — projekt nie ma build step (PROJECT.md: stdlib, `python sph_sim.py` runs directly). Brak `pyproject.toml`, brak `.egg-info`. | none |

**Nothing found in any category — verified by greppowaniu repo:**

```bash
grep -r "pyproject\|setup.py\|setup.cfg\|.egg-info\|systemd\|Task Scheduler" \
    --include="*.py" --include="*.md" .  # → tylko negative-constraint refs w docs (D-07)
```

## Code Examples

### Example 1: `sphsim/strategies/loader.py` skeleton (~100 lines target)

```python
# Source: zweryfikowane przez /tmp/probe_loader_final.py + docs.python.org/3/library/importlib.html
"""Loader plików .py użytkownika — Phase 3 (D-34..D-49).

Pure funkcje + LoaderError. Wywołujący (CLI/REPL) rejestruje w STRATEGIES.
Re-load: zawsze fresh spec (nie używamy importlib.reload — zob. RESEARCH.md Pitfall #1).
"""
import importlib.util
import inspect
import os
import sys


# ── Polski kontrakt sygnatury — verbatim z PROMPT_DLA_AGENTA.txt
EXPECTED_PARAMS = ('dev', 'l', 's', 'phi', 'kappa', 'rho', 'h', 'p')


class LoaderError(Exception):
    """Dowolny problem podczas ładowania custom strategii (D-48).

    Wywołujący wyciąga e.args[0] jako polski one-liner.
    """


def load_custom(path: str):
    """Ładuje, waliduje, zwraca (basename, strategy_fn, meta).

    NIE rejestruje w STRATEGIES — to side effect wywołującego (D-46).
    Drukuje banner przed exec_module (D-45).

    Raises LoaderError z polskim komunikatem przy dowolnym z 4 błędów (D-47).
    """
    # ── 1. PATH RESOLVE (D-36)
    abspath = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(abspath):
        raise LoaderError(f"Plik nie istnieje: {abspath}")

    # ── 2. NAME EXTRACT (D-34) + BUILTIN COLLISION (D-49)
    basename = os.path.splitext(os.path.basename(abspath))[0]
    from sphsim.strategies import BUILTIN_STRATEGIES
    if basename in BUILTIN_STRATEGIES:
        raise LoaderError(
            f"Nazwa '{basename}' koliduje z wbudowaną strategią. Zmień nazwę pliku."
        )

    # ── 3. BANNER (D-45) — stdout, PRZED exec
    print(f"[OSTRZEŻENIE] Ładuję arbitralny kod Pythona z: {abspath}")

    # ── 4. SPEC + EXEC (D-47 layer 1)
    full_name = f'sphsim.custom.{basename}'
    spec = importlib.util.spec_from_file_location(full_name, abspath)
    if spec is None or spec.loader is None:
        raise LoaderError(
            f"Ścieżka {abspath} nie wygląda na plik Pythona (.py)."
        )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = mod        # register PRZED exec (circular import safety)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:               # SyntaxError, ImportError, runtime błędy w top-level
        sys.modules.pop(full_name, None) # cleanup zombie (Pitfall #2)
        raise LoaderError(
            f"Błąd podczas importu pliku {abspath}: {type(e).__name__}: {e}"
        )

    # ── 5. FUNCTION EXISTS + CALLABLE (D-47 layer 2)
    fn_name = f'strategy_{basename}'
    fn = getattr(mod, fn_name, None)
    if not callable(fn):
        raise LoaderError(
            f"Brak funkcji '{fn_name}' w pliku {abspath}. "
            f"Oczekiwana sygnatura: {fn_name}({', '.join(EXPECTED_PARAMS)}) -> str."
        )

    # ── 6. SIGNATURE EXACT (D-47 layer 3) + wrapper escape
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    has_var_pos = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params)
    if not has_var_pos:
        actual_names = tuple(p.name for p in params[:8])
        if actual_names != EXPECTED_PARAMS:
            raise LoaderError(
                f"Funkcja '{fn_name}' ma sygnaturę {sig}. "
                f"Oczekiwana: ({', '.join(EXPECTED_PARAMS)})."
            )

    # ── 7. STRATEGY_META VALIDATE (D-47 layer 4)
    meta = getattr(mod, 'STRATEGY_META', None)
    _validate_meta(meta, abspath)

    return basename, fn, meta


def _validate_meta(meta, abspath):
    """Walidacja STRATEGY_META schema (D-47 layer 4).

    Wymagane klucze: 'description' (str), 'params' (list[tuple-4]), 'baseline_kpi' (dict|None).
    """
    if not isinstance(meta, dict):
        raise LoaderError(
            f"STRATEGY_META w pliku {abspath} musi być dict, otrzymano {type(meta).__name__}."
        )
    for required in ('description', 'params', 'baseline_kpi'):
        if required not in meta:
            raise LoaderError(
                f"STRATEGY_META w pliku {abspath} brakuje klucza '{required}'."
            )
    if not isinstance(meta['description'], str):
        raise LoaderError(
            f"STRATEGY_META['description'] w {abspath} musi być str."
        )
    if not isinstance(meta['params'], list):
        raise LoaderError(
            f"STRATEGY_META['params'] w {abspath} musi być list (krotek 4-elementowych)."
        )
    for i, tup in enumerate(meta['params']):
        if not (isinstance(tup, tuple) and len(tup) == 4):
            raise LoaderError(
                f"STRATEGY_META['params'][{i}] w {abspath} musi być krotką 4-elementową "
                f"(name, type, default, description), otrzymano {tup!r}."
            )
        pname, ptype, _default, pdesc = tup
        if not isinstance(pname, str) or not callable(ptype) or not isinstance(pdesc, str):
            raise LoaderError(
                f"STRATEGY_META['params'][{i}] w {abspath} ma niepoprawne typy elementów."
            )
    if meta['baseline_kpi'] is not None and not isinstance(meta['baseline_kpi'], dict):
        raise LoaderError(
            f"STRATEGY_META['baseline_kpi'] w {abspath} musi być dict lub None."
        )


def parse_params_from_meta(tokens, meta, strategy_name: str):
    """Helper dla CLI + REPL — parsuje [k=v, ...] tokens używając typów z meta.

    Zwraca dict {param_name: typed_value, ...}.
    Niezadeklarowane param → LoaderError z listą dostępnych.
    Nieprzekazany param → default z meta.

    Wspólne dla --param (CLI) i k=v po `custom`/`run` (REPL).
    """
    declared = {name: (ptype, default) for name, ptype, default, _ in meta['params']}
    out = {name: default for name, (_ptype, default) in declared.items()}
    warnings = []
    for tok in tokens:
        if '=' not in tok:
            warnings.append(f"Pominięto token '{tok}' — oczekiwany format key=value.")
            continue
        key, raw_value = tok.split('=', 1)   # split na PIERWSZY = (D-39: wartość może zawierać =)
        if key not in declared:
            available = ', '.join(declared.keys()) if declared else '(brak)'
            raise LoaderError(
                f"Nieznany parametr '{key}' dla strategii '{strategy_name}'. "
                f"Dostępne: {available}."
            )
        ptype, _default = declared[key]
        try:
            out[key] = ptype(raw_value)
        except (ValueError, TypeError) as e:
            raise LoaderError(
                f"Nie można skonwertować '{raw_value}' na {ptype.__name__} "
                f"dla parametru '{key}'."
            )
    for w in warnings:
        print(w)
    return out
```

### Example 2: `sphsim/strategies/__init__.py` DELTA (dodaj `BUILTIN_STRATEGIES`)

```python
# Registry strategii — mutable global; Phase 3 (custom loader) dodaje klucze runtime'owo.
from typing import Callable

from sphsim.strategies.naive import strategy_naive
from sphsim.strategies.threshold import strategy_threshold
from sphsim.strategies.phase_prob import strategy_phase_prob
from sphsim.strategies.incentive import strategy_incentive
from sphsim.strategies.adaptive import strategy_adaptive

StrategyFn = Callable[..., str]

STRATEGIES = {
    'naive': strategy_naive,
    'threshold': strategy_threshold,
    'phase_prob': strategy_phase_prob,
    'incentive': strategy_incentive,
    'adaptive': strategy_adaptive,
}

# Phase 3 D-49: snapshot przed jakąkolwiek custom rejestracją.
# Niemutowalna — collision detection w loaderze + dispatch namespace w do_strategies.
BUILTIN_STRATEGIES = frozenset(STRATEGIES.keys())
```

### Example 3: `sphsim/cli/args.py` DELTA (mutex + --param)

```python
# Modyfikacja istniejącej parse_args() — zmiany na liniach 38-42 + dodanie --param.
mutex = p.add_mutually_exclusive_group(required=True)
mutex.add_argument('--interactive', action='store_true',
                   help='Uruchom tryb interaktywny (REPL)')
mutex.add_argument('--strategy', choices=list(BUILTIN_STRATEGIES),   # D-50: snapshot, NIE STRATEGIES.keys()
                   help='Strategia: ' + ', '.join(BUILTIN_STRATEGIES))
mutex.add_argument('--custom', type=str,
                   help='Ścieżka do pliku .py z custom strategią')   # D-44

# POZA mutex — działa tylko z --custom (Claude's Discretion: graceful ignore z warningiem)
p.add_argument('--param', action='append', default=[], metavar='K=V',
               help='[--custom] Parametr strategii, np. --param zeta=0.7 (repeatable)')
```

I dodać import na górze: `from sphsim.strategies import BUILTIN_STRATEGIES`.

### Example 4: `sphsim/cli/main.py` DELTA (second early branch)

```python
def main():
    args = parse_args()
    if args.interactive:
        from sphsim.cli.repl import run_repl
        run_repl()
        return

    # Phase 3 — D-44 + D-46 + D-47 second early branch.
    if args.custom:
        import sys
        from sphsim.strategies import STRATEGIES
        from sphsim.strategies.loader import load_custom, parse_params_from_meta, LoaderError
        try:
            name, strategy_fn, meta = load_custom(args.custom)
            params = parse_params_from_meta(args.param, meta, name)
        except LoaderError as e:
            print(e.args[0], file=sys.stderr)
            sys.exit(1)
        # Strategia widoczna w STRATEGIES (zostaje na czas procesu — but it's one-shot anyway)
        STRATEGIES[name] = strategy_fn
        K1 = float('inf') if args.K1 < 0 else args.K1
        sim = SPHSimulator(
            nU=args.nU, nSUS=args.nSUS, K0=DEFAULT_K0, K1=K1,
            F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
            phi=DEFAULT_PHI, rho=DEFAULT_RHO,
            strategy_fn=strategy_fn, params=params, seed=args.seed,
        )
        res = sim.run()
        if args.json:
            # format_json potrzebuje args.strategy — ustawiamy custom name dla spójności
            args.strategy = name
            print(format_json(args, res, params, K1))
        else:
            args.strategy = name
            print(format_human(args, res, K1, args.verbose))
        return

    # Existing --strategy path (Phase 1/2) — bez zmian.
    # Graceful warning jeśli --param podany bez --custom:
    if args.param:
        print("Flaga --param ignorowana — działa tylko z --custom.", file=sys.stderr)
    K1 = float('inf') if args.K1 < 0 else args.K1
    params = { ... }   # jak teraz
    # ... reszta jak teraz
```

### Example 5: `sphsim/cli/repl.py` DELTA (do_custom + do_run + do_strategies suffix + do_help)

```python
# DODATKOWE importy:
from sphsim.strategies.loader import load_custom, parse_params_from_meta, LoaderError
from sphsim.strategies import BUILTIN_STRATEGIES
from sphsim.core.simulator import SPHSimulator
from sphsim.cli.output import format_human
from sphsim.config import (DEFAULT_NU, DEFAULT_NSUS, DEFAULT_K0, DEFAULT_K1,
                           DEFAULT_F, DEFAULT_T, DEFAULT_KAPPA, DEFAULT_ALPHA,
                           DEFAULT_PHI, DEFAULT_RHO)
import argparse  # dla namespace-like obj dla format_human


class SPHShell(cmd.Cmd):
    # ... existing intro, prompt, do_exit, do_EOF, default ...

    # ── do_help MODYFIKACJA — dodaj 2 linie (D-50 + D-41)
    def do_help(self, arg):
        """Wyświetl listę dostępnych komend."""
        print("Dostępne komendy:")
        print("  help                       — Wyświetl tę listę komend.")
        print("  exit                       — Zakończ sesję (alternatywnie Ctrl+D).")
        print("  strategies                 — Wyświetl listę wbudowanych i custom strategii.")
        print("  strategy <nazwa>           — Wyświetl szczegóły strategii (parametry, baseline KPI).")
        print("  custom <ścieżka> [k=v ...] — Załaduj custom strategię z pliku .py.")
        print("  run <nazwa> [k=v ...]      — Uruchom symulację (built-in lub custom).")

    # ── do_strategies MODYFIKACJA — dispatch namespace + [custom] suffix (D-50)
    def do_strategies(self, arg):
        """Wyświetl listę wbudowanych i custom strategii."""
        print("Dostępne strategie:")
        for name in STRATEGIES.keys():
            if name in BUILTIN_STRATEGIES:
                mod = importlib.import_module(f'sphsim.strategies.{name}')
                description = mod.STRATEGY_META['description']
                print(f"  {name:<12}— {description}")
            else:
                mod = importlib.import_module(f'sphsim.custom.{name}')
                description = mod.STRATEGY_META['description']
                print(f"  {name:<12}— {description} [custom]")

    # ── do_strategy MODYFIKACJA — dispatch namespace (analog do_strategies)
    def do_strategy(self, arg):
        """Wyświetl szczegóły strategii: opis, parametry, baseline KPI."""
        name = arg.strip()
        if name == '':
            print("Użycie: strategy <nazwa>. Wpisz 'strategies' żeby zobaczyć listę.")
            return
        if name not in STRATEGIES:
            available = ', '.join(STRATEGIES.keys())
            print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
            return
        ns = 'sphsim.strategies' if name in BUILTIN_STRATEGIES else 'sphsim.custom'
        mod = importlib.import_module(f'{ns}.{name}')
        meta = mod.STRATEGY_META
        # ... reszta jak teraz (description, params, baseline KPI)

    # ── do_custom NOWA (D-38 + D-46)
    def do_custom(self, arg):
        """Załaduj custom strategię z pliku .py. Składnia: custom <ścieżka> [k=v ...]"""
        parts = arg.split()
        if not parts:
            print("Użycie: custom <ścieżka> [param=wartość ...].")
            return
        path, *param_tokens = parts
        was_loaded = False
        try:
            full_name = f'sphsim.custom.{os.path.splitext(os.path.basename(os.path.abspath(os.path.expanduser(path))))[0]}'
            was_loaded = full_name in sys.modules
            name, fn, meta = load_custom(path)
            params = parse_params_from_meta(param_tokens, meta, name)
        except LoaderError as e:
            print(e.args[0])
            return
        STRATEGIES[name] = fn
        verb = "Przeładowano" if was_loaded else "Załadowano"
        print(f"{verb} custom strategię '{name}'.")
        if params:
            self._custom_default_params = getattr(self, '_custom_default_params', {})
            self._custom_default_params[name] = params  # opcjonalnie używane przez do_run

    # ── do_run NOWA (D-41 + D-42)
    def do_run(self, arg):
        """Uruchom symulację. Składnia: run <nazwa> [param=wartość ...]"""
        tokens = arg.split()
        if not tokens:
            print("Użycie: run <nazwa> [param=wartość ...]. Wpisz 'strategies' żeby zobaczyć dostępne.")
            return
        name, *kv_tokens = tokens
        if name not in STRATEGIES:
            available = ', '.join(STRATEGIES.keys())
            print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
            return
        # Pobierz meta (dispatch namespace)
        ns = 'sphsim.strategies' if name in BUILTIN_STRATEGIES else 'sphsim.custom'
        mod = importlib.import_module(f'{ns}.{name}')
        meta = mod.STRATEGY_META
        try:
            params = parse_params_from_meta(kv_tokens, meta, name)
        except LoaderError as e:
            print(e.args[0])
            return
        # Buduj SPHSimulator z config defaults (Phase 5 doda override)
        sim = SPHSimulator(
            nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, K0=DEFAULT_K0, K1=DEFAULT_K1,
            F=DEFAULT_F, T=DEFAULT_T, kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA,
            phi=DEFAULT_PHI, rho=DEFAULT_RHO,
            strategy_fn=STRATEGIES[name], params=params, seed=42,
        )
        res = sim.run()
        # format_human oczekuje namespace-like obj z attrs strategy, nU, nSUS, ..., verbose
        fake_args = argparse.Namespace(
            strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, K1=DEFAULT_K1,
            T=DEFAULT_T, kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False,
        )
        print(format_human(fake_args, res, DEFAULT_K1, False))
```

### Example 6: `examples/custom_strategy_template.py` (D-51) — POLSKI template

```python
"""Szablon custom strategii dla SPH Symulatora (Phase 3).

Skopiuj ten plik gdziekolwiek (np. ~/moje-strategie/my_strat.py),
zmodyfikuj funkcję `strategy_<basename>` i uruchom:

    python sph_sim.py --custom <ścieżka_do_pliku>.py --param max_phase=3 --seed 42

Nazwa funkcji MUSI być `strategy_<basename_pliku_bez_py>` —
np. dla `my_strat.py` → `strategy_my_strat`.
"""

# Argumenty funkcji strategii (DOKŁADNIE w tej kolejności):
#   dev    — bieżące urządzenie (obiekt Device z polami: id, phase 1..F-1, status='UP'/'DOWN', ...)
#   l      — lista liczby dostawców per faza w POPRZEDNIM cyklu, długość F-1
#   s      — bieżąca zajętość bufora SUS (int, 0..nSUS)
#   phi    — lista prawdopodobieństw porażki per faza, długość F
#   kappa  — koszt dostarczenia jednej usługi (float)
#   rho    — lista kosztów naprawy per faza, długość F
#   h      — funkcja wagi h(i) = i^alpha (callable, h(int) -> float)
#   p      — słownik parametrów strategii (przekazany przez --param k=v lub `k=v` w REPL)
#
# Wartość zwrotna: literal string 'COMMIT' albo 'ABSTAIN'.

def strategy_custom_strategy_template(dev, l, s, phi, kappa, rho, h, p):
    # Guard: tylko urządzenia UP podejmują decyzję
    if dev.status != 'UP':
        return 'ABSTAIN'

    # Czytamy parametr 'max_phase' — przekazany przez --param max_phase=4 lub default 4
    max_phase = int(p.get('max_phase', 4))

    # Prosta reguła: COMMIT dla wczesnych faz, ABSTAIN dla późnych
    # (alias `threshold` z innym defaultem — pokazuje jak iść własną drogą)
    return 'COMMIT' if dev.phase <= max_phase else 'ABSTAIN'


# Metadane strategii — wymagany kontrakt (D-47 layer 4)
# Klucze: 'description' (str), 'params' (list[tuple-4]), 'baseline_kpi' (dict|None)
STRATEGY_META = {
    'description': 'Szablon: COMMIT dla faz <= max_phase (przykład dydaktyczny)',
    'params': [
        # (nazwa, typ_callable, wartość_domyślna, opis_polski)
        ('max_phase', int, 4, 'Maksymalna faza dla COMMIT'),
    ],
    'baseline_kpi': None,   # opcjonalne — jeśli znasz baseline, podaj dict z 'invocation', 'avg_val_last100'
}
```

**Acceptance:** musi działać out-of-the-box:

```bash
python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json
# Expected: valid JSON output, strategy 'custom_strategy_template' z avg_val_last100 ~ X
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `imp` module (deprecated) | `importlib.util.spec_from_file_location` | Python 3.4 (`imp` deprecated), removed in 3.12 | Tylko `importlib` — `imp` jest poza scope w Python 3.7+. Project minimum 3.7. |
| `__import__()` + sys.path hack | `spec_from_file_location` + `module_from_spec` | Python 3.4 | Czystsze, namespace-isolated, no global state pollution. |
| `inspect.getargspec()` (deprecated) | `inspect.signature()` | Python 3.5 | `signature()` poprawnie obsługuje `*args/**kwargs`, keyword-only, positional-only (PEP 570). |
| `exec(open(path).read())` | `spec.loader.exec_module(mod)` | Python 3.4 | Zapewnia `__name__`, `__file__`, namespace; działa z `inspect`. |

**Deprecated/outdated:**
- `imp` module: usunięte w 3.12 — never use.
- `inspect.getargspec()`: deprecated 3.5+ — use `signature`.
- `imp.find_module/load_module`: → `spec_from_file_location`.

## Validation Architecture

> Phase 3 honoruje `nyquist_validation: true` (default — `.planning/config.json` nie ma explicit `false`). Test framework discovery + sampling rate strategy poniżej.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `unittest` (stdlib) — Python 3.7+ |
| Config file | none — Phase 2 dodał `tests/test_strategy_meta_consistency.py` użyciem `python -m unittest` |
| Quick run command | `python3 -m unittest tests.test_loader -v` (Wave 0 tworzy plik) |
| Full suite command | `python3 -m unittest discover tests -v && python3 scripts/regression_check.py` |
| Phase exit gate | `bash scripts/verify_phase3.sh` (Wave 0 tworzy, paralelnie do `verify_phase1.sh`) |

**Why unittest, not pytest:** stdlib only constraint (PROJECT.md). Phase 2 set precedensa z `unittest` — kontynuujemy.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| STRAT-03 (CLI) | `--custom my.py` ładuje + symuluje + outputuje JSON | integration | `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json \| python3 -c "import json,sys; d=json.load(sys.stdin); assert d['strategy']=='custom_strategy_template'"` | ❌ Wave 0 (smoke script lub w `verify_phase3.sh`) |
| STRAT-03 (REPL) | `custom my.py` w REPL → "Załadowano custom strategię" | integration | `printf 'custom examples/custom_strategy_template.py\nstrategies\nexit\n' \| python sph_sim.py --interactive \| grep -q "custom_strategy_template.*\[custom\]"` | ❌ Wave 0 (w `verify_phase3.sh`) |
| STRAT-03 (REPL run) | `run my_strat` w REPL → symulacja → format_human | integration | `printf 'custom examples/custom_strategy_template.py\nrun custom_strategy_template\nexit\n' \| python sph_sim.py --interactive \| grep -q "SPH SYMULATOR"` | ❌ Wave 0 |
| STRAT-04 (Layer 1: import error) | SyntaxError w pliku → polski LoaderError | unit | `python3 -m unittest tests.test_loader.TestLoader.test_syntax_error_in_user_file -v` | ❌ Wave 0 (`tests/test_loader.py`) |
| STRAT-04 (Layer 2: brak funkcji) | plik bez `strategy_X` → polski LoaderError | unit | `python3 -m unittest tests.test_loader.TestLoader.test_missing_function -v` | ❌ Wave 0 |
| STRAT-04 (Layer 2: non-callable) | `strategy_X = 42` (int) → polski LoaderError | unit | `python3 -m unittest tests.test_loader.TestLoader.test_non_callable_attribute -v` | ❌ Wave 0 |
| STRAT-04 (Layer 3: wrong sig) | sig `(dev, x, y, ...)` → polski LoaderError z konkretną sigem | unit | `python3 -m unittest tests.test_loader.TestLoader.test_wrong_signature -v` | ❌ Wave 0 |
| STRAT-04 (Layer 3: *args escape) | sig `(*args)` → accept (wrapper escape) | unit | `python3 -m unittest tests.test_loader.TestLoader.test_var_positional_accepted -v` | ❌ Wave 0 |
| STRAT-04 (Layer 4: meta missing) | brak `STRATEGY_META` → polski LoaderError | unit | `python3 -m unittest tests.test_loader.TestLoader.test_missing_meta -v` | ❌ Wave 0 |
| STRAT-04 (Layer 4: meta malformed) | `STRATEGY_META = "not dict"` → polski LoaderError | unit | `python3 -m unittest tests.test_loader.TestLoader.test_malformed_meta -v` | ❌ Wave 0 |
| STRAT-04 (Layer 4: missing meta keys) | `STRATEGY_META = {}` (brak `description`) → LoaderError | unit | `python3 -m unittest tests.test_loader.TestLoader.test_meta_missing_keys -v` | ❌ Wave 0 |
| STRAT-04 (D-49: collision) | plik `naive.py` (collision z built-in) → LoaderError | unit | `python3 -m unittest tests.test_loader.TestLoader.test_builtin_name_collision -v` | ❌ Wave 0 |
| STRAT-04 (D-49: not-exists) | `/tmp/nope.py` → "Plik nie istnieje" | unit | `python3 -m unittest tests.test_loader.TestLoader.test_path_not_exists -v` | ❌ Wave 0 |
| STRAT-04 (D-38: reload) | drugie wywołanie `load_custom` na zmodyfikowanym pliku → nowa wersja | unit | `python3 -m unittest tests.test_loader.TestLoader.test_reload_picks_up_changes -v` | ❌ Wave 0 |
| STRAT-04 (fail-fast: no zombie) | failed load nie zostawia śmieci w `sys.modules` | unit | `python3 -m unittest tests.test_loader.TestLoader.test_failed_load_cleans_sys_modules -v` | ❌ Wave 0 |
| STRAT-04 (--param: typed conversion) | `--param max_phase=3` → `int(3)` zgodnie z meta | unit | `python3 -m unittest tests.test_loader.TestLoader.test_param_typed_from_meta -v` | ❌ Wave 0 |
| STRAT-04 (--param: unknown) | `--param foo=1` (nie w meta) → LoaderError | unit | `python3 -m unittest tests.test_loader.TestLoader.test_param_unknown -v` | ❌ Wave 0 |
| STRAT-04 (--param: bad conversion) | `--param zeta=0.75x` → LoaderError | unit | `python3 -m unittest tests.test_loader.TestLoader.test_param_conversion_error -v` | ❌ Wave 0 |
| STRAT-04 (--param: malformed token) | token bez `=` → warning, nie crash | unit | `python3 -m unittest tests.test_loader.TestLoader.test_param_malformed_token_warns -v` | ❌ Wave 0 |
| STRAT-05 (template exists + loads) | `examples/custom_strategy_template.py` istnieje + ładuje się | integration | `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json \| python3 -m json.tool > /dev/null` | ❌ Wave 0 (template Wave 1, test w `verify_phase3.sh`) |
| **Regression** | 8 baseline fixtures nadal pass po zmianach w `args.py`/`main.py` | regression | `python3 scripts/regression_check.py` | ✓ exists |
| **Invariant** | STRATEGY_META ↔ argparse spójność dla built-in (Phase 2) | regression | `python3 -m unittest tests.test_strategy_meta_consistency -v` | ✓ exists |

### Sampling Rate (per Nyquist)

- **Per task commit:** `python3 -m unittest tests.test_loader -v` (~< 5 sec — wszystkie unit testy loadera)
- **Per wave merge:** `python3 -m unittest discover tests -v && python3 scripts/regression_check.py` (~30 sec — pełny suite + 8 regressions)
- **Phase gate (final):** `bash scripts/verify_phase3.sh` — łączy wszystko + 5 ROADMAP SCs + invariant + regression + smoke

### Sample Test File: `tests/test_loader.py` skeleton (Wave 0)

```python
"""Phase 3 D-47 / D-49 — walidacja loadera + fail-fast semantyka.

Każdy test tworzy izolowany .py w tempdir, woła load_custom, asercje
LoaderError z konkretnym polskim message + sprawdza brak side effects.
"""
import os, sys, tempfile, textwrap, unittest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sphsim.strategies.loader import load_custom, parse_params_from_meta, LoaderError
from sphsim.strategies import STRATEGIES, BUILTIN_STRATEGIES


class TestLoader(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._snapshot_strategies = set(STRATEGIES.keys())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        # Cleanup: usuń klucze które tylko ten test dodał
        for k in list(STRATEGIES.keys()):
            if k not in self._snapshot_strategies:
                del STRATEGIES[k]
        # Cleanup sphsim.custom.* z sys.modules
        for k in list(sys.modules.keys()):
            if k.startswith('sphsim.custom.'):
                del sys.modules[k]

    def _write(self, name, content):
        path = os.path.join(self.tmpdir, name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(textwrap.dedent(content))
        return path

    # ─── HAPPY PATH ───
    def test_happy_path_loads_validates_returns(self):
        path = self._write('my_ok.py', '''
            def strategy_my_ok(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'
            STRATEGY_META = {
                'description': 'test',
                'params': [('zeta', float, 0.5, 'p')],
                'baseline_kpi': None,
            }
        ''')
        name, fn, meta = load_custom(path)
        self.assertEqual(name, 'my_ok')
        self.assertTrue(callable(fn))
        self.assertEqual(meta['description'], 'test')

    # ─── LAYER 1: import errors ───
    def test_syntax_error_in_user_file(self):
        path = self._write('bad_syntax.py', 'def broken(:\n')
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        self.assertIn('Błąd podczas importu', cm.exception.args[0])
        self.assertIn('SyntaxError', cm.exception.args[0])

    def test_path_not_exists(self):
        with self.assertRaises(LoaderError) as cm:
            load_custom(os.path.join(self.tmpdir, 'nope.py'))
        self.assertIn('Plik nie istnieje', cm.exception.args[0])

    def test_rejects_non_py_extension(self):
        path = self._write('strat.txt', 'VERSION = 1\n')
        with self.assertRaises(LoaderError):
            load_custom(path)

    # ─── LAYER 2: function presence + callable ───
    def test_missing_function(self):
        path = self._write('no_fn.py', '''
            STRATEGY_META = {'description': 'x', 'params': [], 'baseline_kpi': None}
        ''')
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        self.assertIn("Brak funkcji 'strategy_no_fn'", cm.exception.args[0])
        self.assertIn('dev, l, s, phi, kappa, rho, h, p', cm.exception.args[0])

    def test_non_callable_attribute(self):
        path = self._write('not_callable.py', 'strategy_not_callable = 42\n')
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        self.assertIn("Brak funkcji 'strategy_not_callable'", cm.exception.args[0])

    # ─── LAYER 3: signature ───
    def test_wrong_signature(self):
        path = self._write('wrong_sig.py', '''
            def strategy_wrong_sig(dev, x, y, z):
                return 'COMMIT'
            STRATEGY_META = {'description': 'x', 'params': [], 'baseline_kpi': None}
        ''')
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        self.assertIn("Oczekiwana: (dev, l, s, phi, kappa, rho, h, p)", cm.exception.args[0])

    def test_var_positional_accepted(self):
        path = self._write('var_pos.py', '''
            def strategy_var_pos(*args):
                return 'COMMIT'
            STRATEGY_META = {'description': 'x', 'params': [], 'baseline_kpi': None}
        ''')
        # Powinno przejść — *args to legitymate wrapper escape (D-47 layer 3)
        name, fn, meta = load_custom(path)
        self.assertEqual(name, 'var_pos')

    # ─── LAYER 4: STRATEGY_META ───
    def test_missing_meta(self):
        path = self._write('no_meta.py', '''
            def strategy_no_meta(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'
        ''')
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        self.assertIn('STRATEGY_META', cm.exception.args[0])

    def test_malformed_meta(self):
        path = self._write('bad_meta.py', '''
            def strategy_bad_meta(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'
            STRATEGY_META = "not a dict"
        ''')
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        self.assertIn('musi być dict', cm.exception.args[0])

    def test_meta_missing_keys(self):
        path = self._write('partial_meta.py', '''
            def strategy_partial_meta(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'
            STRATEGY_META = {'description': 'x'}  # brak 'params' i 'baseline_kpi'
        ''')
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        self.assertIn("brakuje klucza", cm.exception.args[0])

    # ─── D-49: built-in collision ───
    def test_builtin_name_collision(self):
        path = self._write('naive.py', '''
            def strategy_naive(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'
            STRATEGY_META = {'description': 'fake', 'params': [], 'baseline_kpi': None}
        ''')
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        self.assertIn("koliduje z wbudowaną", cm.exception.args[0])

    # ─── D-38: reload semantics ───
    def test_reload_picks_up_changes(self):
        import time
        path = self._write('reload_me.py', '''
            def strategy_reload_me(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'
            STRATEGY_META = {'description': 'v1', 'params': [], 'baseline_kpi': None}
        ''')
        _, _, meta1 = load_custom(path)
        self.assertEqual(meta1['description'], 'v1')
        time.sleep(1.1)  # mtime change
        self._write('reload_me.py', '''
            def strategy_reload_me(dev, l, s, phi, kappa, rho, h, p):
                return 'ABSTAIN'
            STRATEGY_META = {'description': 'v2', 'params': [], 'baseline_kpi': None}
        ''')
        _, _, meta2 = load_custom(path)
        self.assertEqual(meta2['description'], 'v2')

    # ─── fail-fast: no zombie ───
    def test_failed_load_cleans_sys_modules(self):
        path = self._write('boom.py', 'raise ZeroDivisionError("init failure")\n')
        full_name = f'sphsim.custom.boom'
        with self.assertRaises(LoaderError):
            load_custom(path)
        self.assertNotIn(full_name, sys.modules)

    # ─── parse_params_from_meta ───
    def test_param_typed_from_meta(self):
        meta = {'params': [('zeta', float, 0.5, 'p'), ('max_phase', int, 3, 'q')],
                'description': 'x', 'baseline_kpi': None}
        out = parse_params_from_meta(['zeta=0.75', 'max_phase=4'], meta, 'fake')
        self.assertEqual(out['zeta'], 0.75)
        self.assertIs(type(out['zeta']), float)
        self.assertEqual(out['max_phase'], 4)
        self.assertIs(type(out['max_phase']), int)

    def test_param_unknown(self):
        meta = {'params': [('zeta', float, 0.5, 'p')], 'description': 'x', 'baseline_kpi': None}
        with self.assertRaises(LoaderError) as cm:
            parse_params_from_meta(['foo=1'], meta, 'fake')
        self.assertIn("Nieznany parametr 'foo'", cm.exception.args[0])
        self.assertIn("Dostępne: zeta", cm.exception.args[0])

    def test_param_conversion_error(self):
        meta = {'params': [('zeta', float, 0.5, 'p')], 'description': 'x', 'baseline_kpi': None}
        with self.assertRaises(LoaderError) as cm:
            parse_params_from_meta(['zeta=0.75x'], meta, 'fake')
        self.assertIn("Nie można skonwertować", cm.exception.args[0])


if __name__ == '__main__':
    unittest.main()
```

### Wave 0 Gaps

- [ ] `tests/test_loader.py` — covers 19 test cases above (loader.py jeszcze nie istnieje — collateral z Wave 1)
- [ ] `examples/custom_strategy_template.py` — wymagany dla SC #3 (Wave 2 jeśli kolejność: loader → template; lub Wave 1 jeśli template + loader równolegle — planner zdecyduje)
- [ ] `scripts/verify_phase3.sh` — phase gate (paralelnie do `verify_phase1.sh`); musi pokrywać 5 ROADMAP SCs + regression + invariant + smoke STRAT-05 acceptance
- [ ] Framework install: **none** (`unittest` w stdlib)

*(Brak gaps dla framework setup — `unittest` używany w Phase 2.)*

## Security Domain

> `security_enforcement` nie jest jawnie ustawione w `.planning/config.json` → traktujemy jako enabled.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | Projekt CLI lokalny, brak auth surface |
| V3 Session Management | no | Brak sesji (REPL = single-user proces) |
| V4 Access Control | no | Brak multi-user/multi-tenancy |
| **V5 Input Validation** | **yes** | **4-warstwowa walidacja w `load_custom` (D-47)** — exact stdlib type/sig/schema check; polskie one-liner errors |
| V6 Cryptography | no | Brak danych do zaszyfrowania |
| V7 Error Handling | partial | `LoaderError` jako custom exception (D-48); polskie messages do user'a, no stack traces leakowane |
| V14 Configuration | partial | Banner pre-import (D-45) świadomie ostrzega o arbitrary code execution — to **konwencja** projektowa, nie pełna sandbox |

### Known Threat Patterns for {Python plugin loader / stdlib importlib}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| **Arbitrary code execution** (load `.py` user'a wykonuje arbitrary Python) | Elevation of Privilege / Information Disclosure | **Świadomie zaakceptowane** (PROJECT.md Constraint: "loader powinien jasno komunikować że ładuje arbitralny Python"). Banner D-45 informuje user'a. Bez sandbox (D-36). Projekt lokalny edukacyjny. |
| **Path traversal** (`..//etc/passwd`) | Information Disclosure | `spec_from_file_location` używa `abspath` — nie traversuje poza FS; user już ma dostęp do swojego FS (i tak by mógł `cat /etc/passwd`). Mitigation: out of scope (lokalny CLI). |
| **Module pollution** (custom `.py` modyfikuje `sys.modules`) | Tampering | **Izolacja namespace `sphsim.custom.*`** (D-46) — collisions z `sphsim.strategies.*` niemożliwe. Custom-custom collision = explicit reload (D-38). |
| **Zombie module po failed exec** | Tampering | `sys.modules.pop(full_name, None)` przy LoaderError (Pitfall #2). Test: `test_failed_load_cleans_sys_modules`. |
| **Built-in shadowing** (custom plik `naive.py` zastępuje built-in) | Tampering | **`BUILTIN_STRATEGIES = frozenset(...)` + collision detection w loaderze** (D-49). Polski error przed exec. |
| **`eval()` w param parsing** | Code Injection | **Nie używamy `eval`** — `type_callable(string_value)` z meta (`float('0.75')`). |
| **Stack trace leak** | Information Disclosure | `LoaderError` → `print(e.args[0])` (one-liner), nie `traceback.print_exc`. CLI: stderr + `sys.exit(1)`; REPL: stdout (no abort). |

**Świadome akceptowane ryzyka:**
- Arbitrary code execution z `.py` user'a — z PROJECT.md Constraint, banner D-45 to mitigation.
- Brak sandbox — projekt akademicki lokalny (D-36).

## Assumptions Log

> Każdy claim oznaczony `[ASSUMED]` poniżej wymaga potwierdzenia (już rozstrzygnięte przez CONTEXT.md albo przez empirical probing). Tabela poniżej wskazuje gdzie wciąż jest niepewność.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `sphsim.custom` namespace (D-46) NIE wymaga tworzenia prawdziwego packagu (no `__init__.py`) | Pattern 1, Pitfall #1 | Jeśli planner spróbuje tworzyć `sphsim/custom/__init__.py` (prawdziwy package) → niepotrzebna komplikacja + zmienia `verify_phase1.sh` line-count check. **Verified empirycznie** w probe — to `[VERIFIED: empirical probe]`, ale spisuję dla widoczności. |
| A2 | Phase 5 (env override) nie wpłynie na shape `do_run` defaults — Phase 3 może hardcodować `DEFAULT_*` jako parametry do `SPHSimulator` | Example 5 (`do_run`) | LOW — Phase 5 rozszerzy, nie zerwie. Tagged ASSUMED bo Phase 5 jeszcze nie wystartował. |
| A3 | `format_human` przyjmuje `argparse.Namespace`-like z atrybutami: `strategy, nU, nSUS, K1, T, kappa, alpha, verbose` — bezpośrednio z `output.py:16` inspect | Example 5 | LOW — sprawdziłem `output.py` ręcznie, accessuje przez `args.strategy.upper()`, `args.nU`, etc. `argparse.Namespace(...)` works. |
| A4 | Test reload (`test_reload_picks_up_changes`) wymaga `time.sleep(1.1)` żeby mtime się zmienił między write'ami w tym samym sekundzie | Sample Test File | LOW — confirmed empirycznie w `/tmp/probe_loader_final.py` (without sleep, drugie load pokazało stale value w jednym z probe runów). |
| A5 | `--param` w argparse jako `action='append'` ma `default=[]` zachowanie konsystentne między Python 3.7 i 3.14 | Example 3 | LOW — `action='append'` z `default=[]` jest stabilne od wieków. |
| A6 | Polski w stderr (CLI) vs stdout (REPL) nie wpływa na grep'owalność testów w `verify_phase3.sh` | Example 4 + Validation | LOW — testy używają `grep` na całym output (stdin+stderr można merge'ować w bash z `2>&1`). |

## Open Questions

1. **Czy `--param` ignorowany bez `--custom` powinien być fatal czy warning?**
   - What we know: Claude's Discretion (CONTEXT.md) sugeruje graceful — warning na stderr.
   - What's unclear: czy w `verify_phase3.sh` testujemy też ten warning? Jeśli tak, zawiera "Flaga --param ignorowana" w stderr.
   - Recommendation: planner — dodaj smoke check w `verify_phase3.sh` że `python sph_sim.py --strategy naive --param zeta=0.7 2>&1 | grep -q "Flaga --param ignorowana"` — niski koszt, łapie regression.

2. **Czy `do_custom` w REPL powinien drukować banner D-45 czy delegować do loadera?**
   - What we know: loader.py drukuje banner do stdout (D-45 + Discretion).
   - What's unclear: czy REPL ma duplikat? **Recommendation:** loader jest single source — `do_custom` po prostu wywołuje `load_custom(path)` i banner się drukuje "za darmo". Nie duplikujemy.

3. **Format komunikatu "Przeładowano" vs "Załadowano" — gdzie sprawdzamy `was_loaded`?**
   - What we know: D-38 wymaga rozróżnienia, ale loader.py jest pure (return tuple). Wywołujący (CLI/REPL) wie state.
   - Recommendation: w `do_custom` sprawdź `full_name in sys.modules` PRZED `load_custom()` (lub po, ale wtedy zawsze będzie True bo load właśnie zarejestrował). **Lepiej:** sprawdź PRZED — patrz Example 5 `do_custom` — `was_loaded = full_name in sys.modules`. CLI one-shot zawsze jest "Załadowano" (proces świeży).

4. **`do_run` w REPL — używamy `seed=42` hardcoded czy z `sphsim/config.py`?**
   - What we know: `sphsim/config.py` nie ma `DEFAULT_SEED` (Phase 1 hardcoded 42 w argparse). Phase 5 może dodać override.
   - Recommendation: hardcode `seed=42` w `do_run` z komentarzem `# Phase 5 doda --seed override w REPL`. **Lub** dodaj `DEFAULT_SEED = 42` do `sphsim/config.py` (Wave 0 task, bardzo mały).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 (`python3`) | wszystko | ✓ | 3.14.3 (project minimum 3.7) | — |
| `importlib.util` (stdlib) | loader | ✓ | stdlib | — |
| `inspect` (stdlib) | loader signature check | ✓ | stdlib | — |
| `unittest` (stdlib) | test suite | ✓ | stdlib | — |
| `cmd` (stdlib) | REPL | ✓ | stdlib (used w Phase 2) | — |
| `readline` (stdlib) | REPL line editing | ✓ | stdlib (POSIX side-effect import) | — |
| `bash` (dla `verify_phase3.sh`) | phase gate | ✓ | macOS default + CI | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

Phase 3 dodaje **zero** zewnętrznych pakietów. PROJECT.md "stdlib only" zachowany.

## Acceptance Verification Commands (5 ROADMAP SCs)

Te komendy powinny iść do `scripts/verify_phase3.sh`. Każda mapuje 1:1 do ROADMAP Phase 3 Success Criterion.

### SC #1 — `--custom` (CLI) i `custom` (REPL) ładują plik `.py` przez `importlib`

```bash
# CLI:
python3 sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['strategy']=='custom_strategy_template', d['strategy']; print('SC#1 CLI OK')"

# REPL (heredoc):
printf 'custom examples/custom_strategy_template.py\nstrategies\nexit\n' \
  | python3 sph_sim.py --interactive 2>&1 \
  | grep -q "Załadowano custom strategię 'custom_strategy_template'" \
  && echo "SC#1 REPL OK"
```

### SC #2 — Polski błąd z konkretem przy każdym z 4 layer'ów

```bash
# Layer 2: brak funkcji
echo "STRATEGY_META = {'description':'x','params':[],'baseline_kpi':None}" > /tmp/no_fn.py
python3 sph_sim.py --custom /tmp/no_fn.py --seed 42 2>&1 \
  | grep -q "Brak funkcji 'strategy_no_fn'" \
  && echo "SC#2 layer2 OK"

# Layer 3: wrong sig
cat > /tmp/wrong_sig.py <<'EOF'
def strategy_wrong_sig(dev, x, y): return 'COMMIT'
STRATEGY_META = {'description':'x','params':[],'baseline_kpi':None}
EOF
python3 sph_sim.py --custom /tmp/wrong_sig.py --seed 42 2>&1 \
  | grep -q "Oczekiwana: (dev, l, s, phi, kappa, rho, h, p)" \
  && echo "SC#2 layer3 OK"

# Layer 1: SyntaxError
echo "def broken(:" > /tmp/syntax.py
python3 sph_sim.py --custom /tmp/syntax.py --seed 42 2>&1 \
  | grep -q "Błąd podczas importu" \
  && echo "SC#2 layer1 OK"

# Layer 4: missing META
cat > /tmp/no_meta.py <<'EOF'
def strategy_no_meta(dev, l, s, phi, kappa, rho, h, p): return 'COMMIT'
EOF
python3 sph_sim.py --custom /tmp/no_meta.py --seed 42 2>&1 \
  | grep -q "STRATEGY_META" \
  && echo "SC#2 layer4 OK"
```

### SC #3 — Template kompiluje + sensowne wyniki

```bash
# Plik istnieje:
test -f examples/custom_strategy_template.py && echo "SC#3 file OK"

# Kompiluje się bez ostrzeżeń:
python3 -W error -c "
import importlib.util, warnings
warnings.simplefilter('error')
spec = importlib.util.spec_from_file_location('t', 'examples/custom_strategy_template.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('SC#3 compile OK')
"

# Polskie komentarze obecne (heurystyka — polskie znaki diakrytyczne):
grep -qP '[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]' examples/custom_strategy_template.py \
  && echo "SC#3 polish comments OK"

# Sensowne wyniki (avg_val_last100 jest finite float):
python3 sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json \
  | python3 -c "
import json,sys,math
d = json.load(sys.stdin)
v = d['metrics']['avg_val_last100']
assert isinstance(v,(int,float)) and math.isfinite(v) and v >= 0, f'avg_val_last100={v}'
print(f'SC#3 result OK (avg_val_last100={v})')
"
```

### SC #4 — Custom strategia widoczna w `strategies` z `[custom]`

```bash
printf 'custom examples/custom_strategy_template.py\nstrategies\nexit\n' \
  | python3 sph_sim.py --interactive 2>&1 \
  | grep -qE 'custom_strategy_template\s+—.*\[custom\]' \
  && echo "SC#4 [custom] suffix OK"

# I że built-in nie ma [custom]:
printf 'strategies\nexit\n' \
  | python3 sph_sim.py --interactive 2>&1 \
  | grep "naive" | grep -v "\[custom\]" \
  && echo "SC#4 builtin clean OK"
```

### SC #5 — Banner bezpieczeństwa

```bash
python3 sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json 2>&1 \
  | grep -qE '^\[OSTRZEŻENIE\] Ładuję arbitralny kod Pythona z: /.*custom_strategy_template\.py$' \
  && echo "SC#5 banner OK"

# I że banner pojawia się PRZED jakimkolwiek innym outputem JSON (heurystyka — pierwsza linia):
python3 sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json 2>&1 \
  | head -1 | grep -q "OSTRZEŻENIE" \
  && echo "SC#5 banner first line OK"
```

### Regression (must still pass — Phase 1 CLI-04 hard requirement)

```bash
python3 scripts/regression_check.py
# Expected: "PASS: 8/8"
```

### Invariant (must still pass — Phase 2 D-25)

```bash
python3 -m unittest tests.test_strategy_meta_consistency -v
# Expected: "OK"
```

## Sources

### Primary (HIGH confidence)

- **Empirical probes (in this session):**
  - `/tmp/probe_loader.py` — confirmed `importlib.reload()` fails dla dotted namespace `sphsim.custom.X` (Pitfall #1)
  - `/tmp/probe_loader2.py` — confirmed even pre-registered synthetic parent rzuca `ModuleNotFoundError: spec not found`
  - `/tmp/probe_loader3.py` — confirmed SyntaxError raises at `exec_module`, `spec_from_file_location` returns `None` dla `.txt`, FileNotFoundError raises at `exec_module` for missing path
  - `/tmp/probe_loader_final.py` — confirmed manual re-load (fresh spec + module_from_spec + sys.modules replace + exec_module) działa for source changes
  - inspect.signature probe — verified 10 edge cases dla D-47 layer 3 (*args escape, lambda, bound methods, positional-only, keyword-only)
- **Python 3 official docs (stdlib):**
  - https://docs.python.org/3/library/importlib.html (importlib.util.spec_from_file_location, module_from_spec, reload semantics)
  - https://docs.python.org/3/library/inspect.html (signature, Parameter.kind)
  - https://docs.python.org/3/library/cmd.html (cmd.Cmd, do_* convention — Phase 2 carry-forward)

### Secondary (MEDIUM confidence)

- WebSearch — Python dynamic loader pattern best practices:
  - https://docs.python.org/3/library/importlib.html
  - https://pytutorial.com/python-importlibutilspec_from_file_location-guide/
  - https://betterstack.com/community/questions/how-to-import-python-module-dynamically/

### Existing repo artifacts (HIGH confidence — verified by Read)

- `sphsim/strategies/__init__.py` — STRATEGIES dict structure
- `sphsim/strategies/{naive,threshold,phase_prob,incentive,adaptive}.py` — STRATEGY_META schema verbatim (all 5 verified)
- `sphsim/cli/args.py` — mutex group existing shape (lines 38-42)
- `sphsim/cli/main.py` — early-branch pattern (line 11)
- `sphsim/cli/repl.py` — SPHShell class shape (line 39), `do_strategies` pattern (line 68-75)
- `sphsim/cli/output.py` — `format_human` signature
- `sphsim/core/simulator.py` — `SPHSimulator(strategy_fn=..., params=...)` interface
- `sphsim/config.py` — `DEFAULT_*` constants
- `tests/test_strategy_meta_consistency.py` — Phase 2 invariant pattern (model for `tests/test_loader.py`)
- `scripts/regression_check.py` — 8 fixtures regression check
- `scripts/verify_phase1.sh` — phase exit gate pattern (model for `verify_phase3.sh`)

### Validated baseline (HIGH confidence)

- Regression test: 8/8 PASS confirmed in this session via `python3 scripts/regression_check.py --verbose`
- Invariant test: PASS confirmed in this session via `python3 -m unittest tests.test_strategy_meta_consistency -v`

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — wszystko stdlib, empirycznie zweryfikowane na Python 3.14.3
- Architecture: **HIGH** — CONTEXT.md D-34..D-52 jest niezwykle precyzyjny, integration points zweryfikowane przez Read na istniejącym repo
- Pitfalls: **HIGH** — 5 z 7 pitfalls empirycznie zweryfikowane probami; 2 (#6, #7) wynikają z CONTEXT.md + istniejącego repo
- Validation Architecture: **HIGH** — 19 unit testów + 6 integration testów + 8 regression + 1 invariant, każdy test mapuje do konkretnego REQ/D
- Acceptance commands: **HIGH** — każda z 5 SC ma deterministyczną grep'owalną komendę

**Research date:** 2026-05-27
**Valid until:** 2026-06-26 (30 dni — stack jest stabilny; jeśli CONTEXT.md się nie zmienia)

---

*Phase: 3-custom-strategy-loader*
*Research completed: 2026-05-27*
