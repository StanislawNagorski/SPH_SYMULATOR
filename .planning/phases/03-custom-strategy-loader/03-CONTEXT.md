# Phase 3: Custom strategy loader - Context

**Gathered:** 2026-05-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Loader plików `.py` użytkownika przez `importlib`, rejestrujący strategię w istniejącym `STRATEGIES` dict (mutable global z Phase 1, D-14). Wejścia: `--custom <ścieżka>` (CLI one-shot, trzeci człon mutex obok `--interactive | --strategy`) i `custom <ścieżka> [k=v ...]` (REPL, bez slasha per Phase 2 D-17). Loader: ładuje plik → waliduje → drukuje cichy banner bezpieczeństwa → rejestruje w STRATEGIES → custom strategia widoczna w `strategies` (z suffixem `[custom]`) i wybieralna jak built-in. Phase 3 dodaje też komendę REPL `run <nazwa> [k=v]` (odłożona z Phase 2 deferred) — bez tego custom strategia jest "zawieszona" w sesji. Plik `examples/custom_strategy_template.py` z polskimi komentarzami i pełnym kontraktem (SC #3).

**Scope:** loader + walidacja + cichy banner bezpieczeństwa + `--custom` w mutex + `--param k=v` (repeatable) + REPL `custom <ścieżka> [k=v ...]` + REPL `run <nazwa> [k=v ...]` + custom strategia w `strategies` z `[custom]` + template `examples/`.

**Out of scope (zostawiamy dla Phase 4-7):** komenda `compare` (Phase 4 — RationalAgent), override env params z REPL'a (`--phi`, `--rho`, `--valuation` — Phase 5), generator raportu MD (Phase 6), `batch <strategia> --seeds N` (Phase 7), komenda `unload <nazwa>` (YAGNI — reload przez powtórne `custom <ścieżka>` wystarcza), session state object (Phase 5/7 jeśli pojawi się potrzeba), tab autocomplete (cmd.Cmd ma `complete_*` hooks ale nie tutaj), persystencja zarejestrowanych custom strategii między sesjami REPL'a (out — projekt akademiczny).

</domain>

<decisions>
## Implementation Decisions

### Kontrakt pliku custom (Area 1)
- **D-34:** Nazwa strategii = **basename pliku bez `.py`**. `my_strat.py` → klucz `'my_strat'` w STRATEGIES. Loader robi `os.path.splitext(os.path.basename(path))[0]`. Bez konfiguracji w STRATEGY_META, bez nazwy funkcji — jeden source of truth dla user'a (sama nazwa pliku). Konflikt z built-in → error (D-39).
- **D-35:** Funkcja strategii ma nazwę **`strategy_<basename>`** — verbatim ten sam pattern co Phase 1 D-03 (`strategy_naive` w `naive.py`). Loader robi `getattr(mod, f'strategy_{basename}')` i `callable()` check. Spójność: custom plik wygląda bit-by-bit jak built-in z `sphsim/strategies/`. Brak funkcji o tej nazwie → polski błąd z konkretem (patrz D-44).
- **D-36:** **Dowolna ścieżka** — absolutna i relatywna, z `os.path.expanduser` + `os.path.abspath`. Bez whitelist katalogów (`examples/`, cwd) — projekt akademicki lokalny, ograniczenia byłyby sztuczne. Bezpieczeństwo komunikowane przez banner (D-41), nie przez sandbox.
- **D-37:** **Sticky w sesji REPL** — raz załadowana strategia zostaje w STRATEGIES do `exit`. Widoczna w `strategies`, wielokrotnie wybieralna przez `run <nazwa>`. Brak persistencji do plików (`~/.sphsim_custom/` nie istnieje). Po wyjściu z REPL'a — znika. Naturalne dla iteracji edit-run-edit. CLI one-shot: rejestracja → `sim.run()` → koniec procesu (sticky nie ma sensu poza procesem).
- **D-38:** **Reload przez powtórne wywołanie** — `custom my.py` drugi raz w tej samej sesji nadpisuje wcześniejszą rejestrację. Mechanika: jeśli `f'sphsim.custom.{basename}'` (D-46) jest w `sys.modules`, użyj `importlib.reload(mod)`; inaczej `importlib.import_module`. Komunikat: `Przeładowano custom strategię 'my_strat'.` lub `Załadowano custom strategię 'my_strat'.` (pierwszy raz). Custom-custom collision (ten sam basename, różny path) — też reload (drugi nadpisuje pierwszy, basename wygrywa).

### Params runtime + komenda `run` (Area 2)
- **D-39:** **`--param k=v` (CLI, repeatable) + `k=v` w REPL** — jednolity input shape dla obu trybów. CLI: `python sph_sim.py --custom my.py --param zeta=0.7 --param threshold=5`. REPL: `custom my.py zeta=0.7 threshold=5` lub `run my_strat zeta=0.7`. Loader parser: split na pierwszy `=` (wartość może zawierać `=`, np. JSON-like strings), accumuluje w dict.
- **D-40:** **Typy z STRATEGY_META['params']** — single source of truth. Loader patrzy `('zeta', float, 0.5, '...')` i konwertuje `'0.75'` → `float('0.75')`. Wszystkie 5 built-in strategii mają już meta (D-25 z Phase 2). ValueError przy konwersji → `Nie można skonwertować '0.75x' na float dla parametru 'zeta'`. Param niezadeklarowany w meta (np. `--param foo=1` gdy strategia nie ma `foo`) → `Nieznany parametr 'foo' dla strategii 'my_strat'. Dostępne: zeta, threshold.` Param nieprzekazany → default z meta. Komentarz: built-in strategie też przepisuje się na ten flow (one-shot CLI dla built-in: argparse parsuje `--zeta 0.7`, main.py mapuje na `params` dict — nie zmienia się; for `run zeta=0.7` w REPL: nowy parser `k=v` budujesz `params` z meta typów).
- **D-41:** **Komenda `run <nazwa> [k=v ...]`** — nowa metoda `do_run` w `SPHShell` (kontynuacja D-33 z Phase 2: dodaj do istniejącego pliku `sphsim/cli/repl.py`, bez nowego helper modułu). Działa dla built-in (`run naive zeta=0.75`) i custom (`run my_strat threshold=5`) — jednolicie. Env params (nU, T, kappa, alpha, K1, seed) — z `sphsim/config.py` defaults (Phase 5 doda override). Output do REPL'a: `format_human` (krótki, czytelny, jak w one-shot CLI bez `--json`). Brak `--json` w REPL'u (gdy user chce JSON, niech użyje one-shot CLI).
- **D-42:** **`run` bez nazwy** → `Użycie: run <nazwa> [param=wartość ...]. Wpisz 'strategies' żeby zobaczyć dostępne.` (analog D-32 z Phase 2). **`run nieznana`** → `Strategia 'nieznana' nie istnieje. Dostępne: naive, threshold, phase_prob, incentive, adaptive, my_strat.` (live z STRATEGIES, więc custom widoczne).
- **D-43:** **Pozycyjne parsing w REPL** — `do_custom(arg)` i `do_run(arg)` dostają raw string po komendzie. Split: pierwszy token = ścieżka/nazwa (whitespace), reszta = tokens postaci `k=v`. Implementacja: `parts = arg.split()`; `head, rest = parts[0], parts[1:]`; `params = dict(p.split('=', 1) for p in rest if '=' in p)`. Ścieżki ze spacjami **nie są wspierane** (academic projekt, edge case bez wartości). Token bez `=` (np. literówka `zeta 0.7` zamiast `zeta=0.7`) → ostrzeżenie `Pominięto token 'zeta' — oczekiwany format key=value.` (graceful, nie kill całego run'a).

### Mutex CLI + bezpieczeństwo (Area 3)
- **D-44:** **`--custom` jako trzeci człon mutex group** w `sphsim/cli/args.py`. Po refactorze:
  ```python
  mutex = p.add_mutually_exclusive_group(required=True)
  mutex.add_argument('--interactive', action='store_true', ...)
  mutex.add_argument('--strategy', choices=list(STRATEGIES.keys()), ...)
  mutex.add_argument('--custom', type=str, help='Ścieżka do pliku .py z custom strategią')
  ```
  Backwards compat z Phase 1/2 zachowane: `--strategy X` bez `--interactive`/`--custom` nadal valid, regression suite (8 fixtures z `tests/fixtures/baseline_v1/`) musi nadal pass. Nowy CLI invariant: `--custom my.py [--param k=v ...] [env opts] [--seed S] [--json]`. argparse parsuje `--custom` jako string, loader (osobny moduł, D-45) ładuje i waliduje przed `SPHSimulator` build.
- **D-45:** **Cichy jednolinijkowy banner pre-import** — w obu trybach (CLI i REPL). Format: `[OSTRZEŻENIE] Ładuję arbitralny kod Pythona z: <abspath>`. Drukowany do `sys.stdout` **przed** `importlib.import_module` (gdyby plik wybuchł przy imporcie, banner i tak już się pokazał — user wie skąd kod). Bez confirmation prompt `[y/N]` (rejected — friction przy iteracji), bez flagi `--no-warn` (YAGNI — jedna linia output to nie spam). Spójne z PROJECT.md Constraint: "loader powinien jasno komunikować że ładuje arbitralny Python".
- **D-46:** **Loader jako osobny moduł** — `sphsim/strategies/loader.py`. Eksportuje funkcję `load_custom(path: str) -> tuple[str, callable, dict]` zwracającą `(basename, strategy_fn, meta)`. Importuje moduł do private namespace `sphsim.custom.<basename>` (przez `importlib.util.spec_from_file_location` + `module_from_spec` + dodanie do `sys.modules`) — pozwala na reload (D-38) i nie zaśmieca głównego namespace'u (`sphsim.strategies.<name>` zarezerwowane dla built-in). Side effect rejestracji (`STRATEGIES[name] = fn`) robi **wywołujący** (CLI main.py lub REPL `do_custom`), żeby loader był pure — testowalny w izolacji.

### Walidacja + listing + template (Area 4)
- **D-47:** **3-warstwowa walidacja** w `load_custom`:
  1. **Import** — `try: spec = importlib.util.spec_from_file_location(...); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod) except Exception as e: raise LoaderError(f"Błąd podczas importu pliku {path}: {type(e).__name__}: {e}")`. Łapie wszystko (SyntaxError, ImportError, runtime błędy w top-level).
  2. **Funkcja istnieje + callable** — `fn = getattr(mod, fn_name, None); if not callable(fn): raise LoaderError(f"Brak funkcji '{fn_name}' w pliku {path}. Oczekiwana sygnatura: {fn_name}(dev, l, s, phi, kappa, rho, h, p) -> str.")`.
  3. **Sygnatura exact** — `inspect.signature(fn)`; sprawdza dokładnie 8 parametrów pozycyjnych z nazwami `dev, l, s, phi, kappa, rho, h, p` w tej kolejności. Mismatch → `Funkcja '{fn_name}' ma sygnaturę {actual_sig}. Oczekiwana: (dev, l, s, phi, kappa, rho, h, p).` Pozwala na *args/**kwargs (rzadkie ale legit dla wrappers) — wtedy skip strict check.
  4. **STRATEGY_META validation** — `meta = getattr(mod, 'STRATEGY_META', None)`. Walidacja: `isinstance(meta, dict)`, ma klucze `{'description', 'params', 'baseline_kpi'}`, `description: str`, `params: list[tuple-4]` z (str, type, Any, str), `baseline_kpi: dict | None`. Naruszenie → `STRATEGY_META w pliku {path} ma nieprawidłowy format: {konkret}.` Strategia NIE jest rejestrowana przy jakimkolwiek z 4 błędów (fail-fast, zero side effects).
- **D-48:** **`LoaderError` jako custom exception** — `class LoaderError(Exception): pass` w `sphsim/strategies/loader.py`. CLI/REPL łapią ten exception type i drukują `e.args[0]` (polski message). Inne wyjątki (np. permission denied przy odczycie pliku, gdy `os.access` zfailuje) — też owinięte w LoaderError dla spójnego UX. **Inline jednolinijkowe** komunikaty (per D-44 wybrane), bez "Sprawdź:" hint sections (rejected — multi-line trudniej skopiować do issue/grep'a).
- **D-49:** **Konflikt nazw: error** — Loader sprawdza `if basename in BUILTIN_STRATEGIES (snapshot z Phase 1)` ZANIM zarejestruje. Conflict → `LoaderError(f"Nazwa '{basename}' koliduje z wbudowaną strategią. Zmień nazwę pliku.")`. Custom-custom collision (ta sama nazwa, różny path) → reload (D-38) — nie error, basename wygrywa. **`BUILTIN_STRATEGIES`** = stała w `sphsim/strategies/__init__.py` — frozenset 5 oryginalnych nazw, snapshot Phase 1 (`naive`, `threshold`, `phase_prob`, `incentive`, `adaptive`). Live `STRATEGIES.keys()` nie wystarcza (po reload custom zawiera też custom — nie reagowałby na kolizję poprawnie).
- **D-50:** **Listing z suffixem `[custom]`** — `do_strategies` w `SPHShell` (modyfikacja z Phase 2 D-29) iteruje po `STRATEGIES.keys()`. Dla każdej: jeśli `name in BUILTIN_STRATEGIES` → format jak teraz (`  naive       — Opis`); inaczej → `  my_strat    — Opis [custom]`. Padding 12 znaków zachowany. Argparse `--strategy choices` w CLI to **`list(BUILTIN_STRATEGIES)` (snapshot Phase 1)**, NIE `list(STRATEGIES.keys())` — bo argparse w CLI one-shot nie widzi custom strategii (ich rejestracja odbywa się po parsie, gdy CLI parsuje `--custom my.py`, wtedy custom strategia ląduje w `STRATEGIES` dopiero w main.py). Custom strategie uruchamia się przez `--custom <ścieżka>`, NIE przez `--strategy <name>` z CLI. To jest świadome ograniczenie one-shot CLI (REPL jest elastyczny i widzi custom przez `run <nazwa>`).
- **D-51:** **`examples/custom_strategy_template.py`** — minimal + komentarze edukacyjne (~30-50 linii). Zawartość:
  - Header docstring po polsku tłumaczący do czego służy plik
  - Implementacja `strategy_custom_strategy_template` (nazwa = basename pliku) — prosta: COMMIT gdy `dev.phase <= max_phase` (alias `threshold` z innym defaultem), używa `p.get('max_phase', 4)` żeby pokazać dostęp do params
  - Polskie komentarze inline obejmujące: (a) co znaczą argumenty `dev`/`l`/`s`/`phi`/`kappa`/`rho`/`h`/`p`, (b) jak `dev.phase` i `dev.status` decydują o branch'u, (c) wartości zwrotne `'COMMIT'`/`'ABSTAIN'`, (d) kontrakt `STRATEGY_META`
  - Pełen `STRATEGY_META` z `description`, `params: [('max_phase', int, 4, 'Maksymalna faza dla COMMIT')]`, `baseline_kpi: None`
  - Plik **musi się skompilować bez ostrzeżeń** (SC #3), **dawać sensowne wyniki na baseline'owym środowisku** (uruchom `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json` jako acceptance check). Plik **commitowany** (NIE w gitignore) — kanoniczny template. Użytkownik kopiuje gdzie indziej.
- **D-52:** **`examples/` jako katalog projektu** — `examples/custom_strategy_template.py` to JEDYNY plik tworzony tutaj. Brak `examples/__init__.py` (nie pakiet, tylko storage plików). Brak `examples/*.gitignore` (user trzyma swoje strategie poza repo, np. `~/my-strats/`).

### Claude's Discretion
- Dokładny format banner D-45: jednolinijka, ale czy w stderr czy stdout — Claude wybiera (preferuj stdout, spójne z resztą output'u; banner nie jest błędem, jest informacją).
- Mechanizm reload (D-38): `importlib.reload(mod)` vs ponowny `spec_from_file_location` + `module_from_spec` — Claude wybiera. Preferuj reload jeśli moduł już w `sys.modules['sphsim.custom.<basename>']`, inaczej spec_from_file_location (pierwsze ładowanie).
- Czy `do_strategies` w SPHShell zachowuje istniejący wzorzec (Phase 2 importuje moduł żeby pobrać `STRATEGY_META`) czy buduje cache — Claude wybiera. Preferuj live import (custom strategie nie są w `sphsim/strategies/` więc importlib.import_module sięga przez sphsim.custom.X — to musi działać spójnie).
- Czy `do_run` w SPHShell ma `--verbose` echo per cykl — Claude decyduje, preferuj nie (REPL output ma być zwięzły; verbose przez one-shot CLI).
- Test coverage: unit testy loadera (3+ przypadki błędów + happy path) — Claude wybiera czy `tests/test_loader.py` osobno czy rozszerzenie istniejącego `test_strategy_meta_consistency.py`. Preferuj osobny plik (różne odpowiedzialności).
- Czy `--param` w argparse jest `action='append'` (lista, kolejne `--param k=v` rosną) — TAK, Claude implementuje. Default `[]`.
- Format error gdy `--param` jest podany bez `--custom` (built-in nie używa generic param) — Claude wybiera. Preferuj cichy ignore + ostrzeżenie `Flaga --param ignorowana — działa tylko z --custom.` (graceful).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specification & State
- `.planning/PROJECT.md` — Constraint "polski w komentarzach, komunikatach CLI" (banner D-45, error messages D-47/D-48); Constraint "Python 3.7+ stdlib only" (importlib + inspect — stdlib, zero nowych zależności); Key Decision "Custom strategy: plik `.py` przez importlib" (Phase 3 implementacja tej decyzji).
- `.planning/REQUIREMENTS.md` §"STRAT" — STRAT-03 (`--custom <ścieżka>` i `/custom <ścieżka>` ładują przez importlib), STRAT-04 (loader waliduje i komunikuje błędy), STRAT-05 (`examples/custom_strategy_template.py` z polskimi komentarzami). **Uwaga:** REQUIREMENTS używa `/custom` — D-17 z Phase 2 zmienia na komendy bez slasha (`custom <ścieżka>`); intent zachowany.
- `.planning/ROADMAP.md` §"Phase 3" — 5 Success Criteria. SC #1 `--custom` (CLI) i `/custom` (REPL) — REPL bez slasha per D-17. SC #2 błędy z konkretem (nazwa funkcji, oczekiwane argumenty) — implementowane przez D-47/D-48. SC #3 template kompiluje + sensowne wyniki — D-51 acceptance check. SC #4 widoczna w `/strategies` (bez slasha, D-17) jako custom — D-50 suffix `[custom]`. SC #5 jasne ostrzeżenie bezpieczeństwa — D-45 cichy banner pre-import.
- `.planning/STATE.md` — milestone v1.1 status, prior session info; brak blocking concerns dla Phase 3.

### Phase 1 & 2 Outputs (już istnieją w repo, niezmienialne tutaj)
- `sphsim/strategies/__init__.py` — `STRATEGIES = {'naive': ..., 'threshold': ..., 'phase_prob': ..., 'incentive': ..., 'adaptive': ...}` (D-14 Phase 1). Phase 3 doda **runtime** klucze przez `STRATEGIES[basename] = fn`. Phase 3 dodaje też **stałą** `BUILTIN_STRATEGIES = frozenset(STRATEGIES.keys())` jako snapshot przed jakąkolwiek custom rejestracją (D-49).
- `sphsim/strategies/{naive,threshold,phase_prob,incentive,adaptive}.py` — każdy plik ma `strategy_X` + `STRATEGY_META` (Phase 2 D-24/D-25/D-26). **Template `examples/custom_strategy_template.py` MUSI mieć identyczny shape** — to jest live kontrakt dla custom autorów.
- `sphsim/cli/args.py` — mutex group `--interactive | --strategy` (Phase 2 D-27/D-28). Phase 3 dodaje **trzeci człon** `--custom` do mutex (D-44). Phase 3 dodaje też `--param` (action='append', dest='param', default=[]) **POZA** mutex.
- `sphsim/cli/main.py` — `if args.interactive: run_repl(); return` early branch (Phase 2). Phase 3 dodaje **drugą** early branch: `if args.custom: load_and_run_custom(args)` (lub inline w main — Claude decyduje).
- `sphsim/cli/repl.py` — `SPHShell(cmd.Cmd)` z `do_help`, `do_exit`, `do_strategies`, `do_strategy` (Phase 2). Phase 3 dodaje **2 nowe metody w tej samej klasie** (D-33 z Phase 2): `do_custom(arg)` i `do_run(arg)`. Modyfikuje `do_strategies` żeby dodać suffix `[custom]` (D-50). Modyfikuje `do_help` żeby wymienić nowe komendy.
- `sphsim/core/simulator.py` — `SPHSimulator` klasa, `__init__(strategy_fn=..., params=..., ...)` i `run() -> dict` (Phase 1). Phase 3 NIE modyfikuje simulator — tylko buduje go z custom `strategy_fn` (z loadera) zamiast z `STRATEGIES[name]`.
- `sphsim/config.py` — `DEFAULT_NU`, `DEFAULT_NSUS`, `DEFAULT_K0`, `DEFAULT_K1`, `DEFAULT_F`, `DEFAULT_T`, `DEFAULT_KAPPA`, `DEFAULT_ALPHA`, `DEFAULT_PHI`, `DEFAULT_RHO` (Phase 1 D-04). Phase 3 `do_run` w REPL używa tych defaults (env override jest Phase 5).
- `tests/test_strategy_meta_consistency.py` — invariant test D-25 (Phase 2). Phase 3 **NIE modyfikuje** tego testu — STRATEGY_META kontrakt jest taki sam dla custom. Phase 3 może dodać `tests/test_loader.py` (Claude's Discretion).
- `tests/fixtures/baseline_v1/*.json` — 8 regression fixtures (Phase 1). Phase 3 **regression musi nadal pass** — `--custom` to nowa flaga, nie zmienia istniejących inwokacji.

### Stdlib documentation
- `importlib` module — https://docs.python.org/3/library/importlib.html (`import_module`, `util.spec_from_file_location`, `util.module_from_spec`, `reload`).
- `inspect` module — https://docs.python.org/3/library/inspect.html (`signature`, `Parameter`, walidacja sygnatury w D-47).
- `cmd` module — https://docs.python.org/3/library/cmd.html (rozszerzenie SPHShell o `do_custom`, `do_run` per D-33 Phase 2).

### v1.0 Reference
- `PROMPT_DLA_AGENTA.txt` — definicja sygnatury strategii w v1.0 (8 argumentów: `dev, l, s, phi, kappa, rho, h, p`). Walidacja D-47 layer 3 sprawdza dokładnie te nazwy.

### Codebase Maps
- `.planning/codebase/ARCHITECTURE.md` §"Strategy Layer" — strategie = pure functions, signature uniformity, dispatched via STRATEGIES dict. Phase 3 rozszerza ten pattern o runtime registration, nie zmienia kontraktu funkcji.
- `.planning/codebase/CONVENTIONS.md` §"Function Design" — strategy functions return string literals `'COMMIT'`/`'ABSTAIN'`. Template w D-51 musi zachować ten kontrakt.
- `.planning/codebase/STACK.md` — "Standard Library Only" — Phase 3 dodaje `importlib` i `inspect` (oba stdlib), nie łamie constraint'a.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`STRATEGIES` dict (`sphsim/strategies/__init__.py:13-19`)** — mutable global; loader robi `STRATEGIES[basename] = fn` runtime'owo. Live registry — `do_strategies` w REPL'u i `do_strategy <name>` automatycznie widzą custom (Phase 2 D-29 antycypował ten flow).
- **`SPHShell(cmd.Cmd)` (`sphsim/cli/repl.py:39`)** — istniejąca klasa, Phase 3 dodaje 2 nowe `do_*` metody + modyfikuje `do_strategies` (suffix `[custom]`) + `do_help` (wymień nowe komendy). Pattern verbatim z Phase 2.
- **`mutex` group (`sphsim/cli/args.py:38-42`)** — istniejąca mutually exclusive group `required=True` z `--interactive | --strategy`. Phase 3 dodaje trzecią `mutex.add_argument('--custom', type=str)`.
- **`STRATEGY_META` schema z Phase 2** — Phase 3 reuse'uje verbatim ten sam kontrakt (3 klucze: description / params / baseline_kpi). Walidacja D-47 layer 4 sprawdza ten schema. Template D-51 ma identyczny shape.
- **`format_human` (`sphsim/cli/output.py:16`)** — Phase 3 `do_run` w REPL'u używa tej funkcji do drukowania wyniku symulacji (krótki output, czytelny).
- **`SPHSimulator(strategy_fn=..., params=...)` (`sphsim/core/simulator.py`)** — Phase 3 buduje simulator z custom `strategy_fn` (z loadera) i `params` dict (z `--param k=v` parsing). Konstruktor nie wymaga zmian — to interfejs wystarcza.

### Established Patterns
- **Funkcja per plik strategii + registry pattern (Phase 1 D-03/D-14)** — Phase 3 rozszerza: custom plik ma DOKŁADNIE ten sam shape co built-in (`strategy_<basename>` + `STRATEGY_META`). Template D-51 to widzi 1:1.
- **Polski w komentarzach + komunikatach (PROJECT.md Constraint)** — wszystkie error messages loadera (D-47/D-48), banner (D-45), template comments (D-51) po polsku. Identyfikatory w kodzie (LoaderError, load_custom, BUILTIN_STRATEGIES) po angielsku — spójne z Phase 1/2.
- **Stdlib only** — Phase 3 dodaje `importlib`, `importlib.util`, `inspect`, `os.path` — wszystko stdlib. Pierwsza biblioteka zewnętrzna nadal dopiero w Phase 6 (matplotlib).
- **Fail-fast walidacja** — jak w Phase 1 (argparse type check przy parse) i Phase 2 (D-25 invariant test). Phase 3 D-47 ma 4 warstwy walidacji — strategia NIE jest rejestrowana przy żadnym błędzie.
- **Komendy REPL bez slasha (Phase 2 D-17)** — `custom <ścieżka>`, `run <nazwa>` — nie `/custom`, `/run`. UAT i verify_phase3.sh sprawdzają formę bez slasha.

### Integration Points
- **Loader → main.py (`sphsim/cli/main.py:9`)**: po `if args.interactive: run_repl(); return`, dodaj `if args.custom: ...`. Pseudo-kod:
  ```python
  if args.custom:
      from sphsim.strategies.loader import load_custom, LoaderError
      try:
          name, strategy_fn, meta = load_custom(args.custom)
      except LoaderError as e:
          print(e.args[0], file=sys.stderr); sys.exit(1)
      params = parse_custom_params(args.param, meta)  # --param k=v → dict
      sim = SPHSimulator(strategy_fn=strategy_fn, params=params, ...)
      res = sim.run()
      print(format_human(args, res, K1, args.verbose) if not args.json else format_json(args, res, params, K1))
      return
  ```
- **Loader → repl.py do_custom**: 
  ```python
  def do_custom(self, arg):
      path, *param_tokens = arg.split()
      try:
          name, fn, meta = load_custom(path)
      except LoaderError as e:
          print(e.args[0]); return
      params = parse_custom_params_repl(param_tokens, meta)  # k=v → dict
      STRATEGIES[name] = fn
      self._custom_params_cache[name] = params  # for do_run defaults? Claude decides
      print(f"Załadowano custom strategię '{name}'.")
  ```
- **`do_run` w SPHShell**:
  ```python
  def do_run(self, arg):
      tokens = arg.split()
      if not tokens:
          print("Użycie: run <nazwa> [param=wartość ...].")
          return
      name, *kv_tokens = tokens
      if name not in STRATEGIES:
          print(f"Strategia '{name}' nie istnieje. Dostępne: {', '.join(STRATEGIES.keys())}.")
          return
      params = parse_params_from_meta(name, kv_tokens)
      sim = SPHSimulator(strategy_fn=STRATEGIES[name], params=params, ... defaults from config.py)
      res = sim.run()
      print(format_human_short(res))
  ```
- **`do_strategies` modyfikacja**: w Phase 2 iteruje po `STRATEGIES.keys()`, importuje moduł, drukuje description. Phase 3: dla `name not in BUILTIN_STRATEGIES`, importuje z `sphsim.custom.{name}` (private namespace, D-46) i dodaje suffix ` [custom]`. **Krytyczne**: importlib.import_module musi działać dla obu namespace'ów (`sphsim.strategies.<name>` dla built-in, `sphsim.custom.<name>` dla custom).
- **`do_help` modyfikacja**: dodaje 2 linie:
  ```
  custom <ścieżka> [k=v ...]   — Załaduj custom strategię z pliku .py.
  run <nazwa> [k=v ...]        — Uruchom symulację (built-in lub custom).
  ```
- **Regression test musi nadal pass** — Phase 1 `scripts/regression_check.py` uruchamia 8 fixtures z `--strategy X`. Phase 3 dodaje `--custom` do mutex (nie konflikt) i `--param` (poza mutex, nie konflikt z fixtures). Test musi pass jako Phase 3 acceptance criterion.

</code_context>

<specifics>
## Specific Ideas

- **Banner pre-import (D-45) tekst:** `[OSTRZEŻENIE] Ładuję arbitralny kod Pythona z: <abspath>`. Jedna linia, `stdout`, drukowana **przed** `importlib.import_module`/`exec_module`. Polski "Ładuję" w pierwszej osobie (spójne z REPL "Załadowano custom strategię").
- **Template (D-51) ma być uruchamialny od razu:** `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json` musi działać out-of-the-box i dawać deterministyczny output (acceptance check SC #3).
- **`BUILTIN_STRATEGIES` jako frozenset (D-49)** — niemutowalna stała, snapshot Phase 1. Konflikt detection: `if basename in BUILTIN_STRATEGIES: raise LoaderError(...)`. NIE używamy `STRATEGIES.keys()` (po custom load zawiera też custom — kolizja-detection by nie działała).
- **Private namespace `sphsim.custom.<basename>` (D-46)** — custom moduły **nie** ładujemy do `sphsim.strategies.<basename>` (tam są built-in). Pozwala odróżnić namespace w `do_strategies` i `do_strategy <name>` (Phase 2 importuje z `sphsim.strategies.<name>` — Phase 3 dispatch: jeśli `name in BUILTIN_STRATEGIES` → `sphsim.strategies.<name>`, inaczej → `sphsim.custom.<name>`).
- **Sygnatura walidacja (D-47 layer 3):** dokładne nazwy `(dev, l, s, phi, kappa, rho, h, p)`. Pozwalamy na `*args, **kwargs` (rzadkie, dla wrappers). Walidacja: `params = inspect.signature(fn).parameters; expected = ['dev','l','s','phi','kappa','rho','h','p']; if list(params.keys())[:8] != expected and not any(p.kind == VAR_POSITIONAL for p in params.values()): raise`.
- **Komendy bez slasha (D-17 Phase 2 carry-forward)** — `custom`, `run` — UAT testuje formy bez slasha; pomimo że ROADMAP/REQUIREMENTS używają `/custom`, override D-17 stosuje się tutaj też. Phase 3 verify script używa `custom`, `run`.

</specifics>

<deferred>
## Deferred Ideas

- **Komenda `unload <nazwa>`** — odregistracja custom strategii z STRATEGIES bez restartu REPL'a. YAGNI dla Phase 3 (reload przez powtórne `custom <ścieżka>` wystarcza). Można dodać w Phase 4-7 jeśli pojawi się use case.
- **Komenda `compare <strategia>`** — Phase 4 (Rational Agent veto layer). Phase 3 `run` to fundament; Phase 4 doda `compare` jako "uruchom raz z agentem, raz bez, pokaż delta KPI".
- **Override env params w REPL'u (`--phi`, `--rho`, `--valuation`, `--K1`, `--T`)** — Phase 5 (Configurable environment). Phase 3 `run` używa defaults z `sphsim/config.py`.
- **Komenda `batch <strategia> --seeds 10`** — Phase 7.
- **`--no-warn` flag dla banner'a** — odrzucone (D-45, YAGNI). Można dodać jako quick win w późniejszej fazie jeśli ktoś chce stłumić banner przy automated runs.
- **Confirmation prompt `[y/N]` przy load** — odrzucone (D-45, friction przy iteracji). Edukacyjny banner wystarcza.
- **Whitelist katalogów (`examples/`, cwd)** — odrzucone (D-36). Projekt akademicki, sandbox nie potrzebny.
- **Session state object (`SessionContext` z params, env, last_strategy)** — odrzucone dla Phase 3. Każdy `run` self-contained. Phase 5/7 może wprowadzić jeśli persistent env params będą potrzebne.
- **Tab autocomplete dla custom strategii** — `cmd.Cmd` ma `complete_*` hooks ale Phase 3 nie implementuje. Można dodać w Phase 7 jako polish.
- **Format JSON dla `--params`** — odrzucone (D-39, `--param k=v` jest prostsze).
- **Dynamiczne rozszerzanie argparse z STRATEGY_META** — odrzucone (D-39, komplikuje args.py, dwukrotny parse, możliwe kolizje z built-in flagami).
- **Persistencja custom strategii do `~/.sphsim_strategies/`** — odrzucone dla Phase 3. Sticky tylko w sesji REPL'a.
- **Multi-line error messages z "Sprawdź:" hint sections** — odrzucone (D-48, inline jednolinijka łatwiejsza do skopiowania/grepa).
- **Pełne typing/dataclass-owe `StrategyMeta`** — odrzucone (Phase 1 D-13 trzymamy plain functions + plain dicts, type alias `StrategyFn = Callable[..., str]` wystarcza).
- **Rich/colored output banner** — odrzucone (spójność z Phase 2 D-22, format_human bez ANSI).

</deferred>

---

*Phase: 3-Custom strategy loader*
*Context gathered: 2026-05-27*
