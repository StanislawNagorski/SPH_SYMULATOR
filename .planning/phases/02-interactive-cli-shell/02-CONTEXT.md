# Phase 2: Interactive CLI shell - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Dodanie trybu interaktywnego (REPL) jako drugiego entry-pointu obok istniejącego one-shot CLI z v1.0. Nowy plik `sphsim/cli/repl.py` (D-15 z Phase 1) z klasą `SPHShell(cmd.Cmd)` udostępniającą 4 komendy: `help`, `exit`, `strategies`, `strategy <nazwa>`. Komenda `strategy <nazwa>` pokazuje opis, listę parametrów (nazwa, typ, default, opis po polsku) i — dla strategii z baseline'em — KPI `naive --zeta 0.75 → avg_val_last100 = 92.0`. Phase 2 wprowadza też wymagany przez to kontrakt metadanych: każdy plik `sphsim/strategies/<name>.py` eksportuje `STRATEGY_META` obok funkcji.

**Scope:** REPL z 4 komendami (browser strategii, bez `run`) + `STRATEGY_META` dla 5 wbudowanych strategii. Z minimalnym CLI hookiem (`--interactive` strict mutually exclusive z `--strategy`).

**Out of scope (zostawiamy dla Phase 3-7):** komenda `run` z REPL'a, `custom <ścieżka>` (Phase 3), `compare` (Phase 4), override `--phi`/`--rho`/`--valuation` z REPL'a (Phase 5), `batch` (Phase 7), Session/state object między komendami, autocomplete dla nazw strategii (Tab w cmd.Cmd działa automatycznie przez readline, ale custom completers nie wprowadzamy).

</domain>

<decisions>
## Implementation Decisions

### Komendy bez slasha (odstępstwo od dosłownego tekstu ROADMAP)
- **D-17:** Komendy są BEZ prefiksu `/` — `help`, `exit`, `strategies`, `strategy naive`. Świadome odstępstwo od tekstu ROADMAP Success Criteria (które używały `/help` itp.). Użytkownik zatwierdził: "komendy mogą być bezpośrednio jak łatwiej". Powód: natywny `cmd.Cmd` używa komend bez prefiksu, override `parseline()` byłby workaroundem dla niczego. UAT i verify_phase2.sh muszą sprawdzać `help` (nie `/help`).

### REPL technology
- **D-18:** `sphsim/cli/repl.py` używa `cmd.Cmd` ze stdlib (zero nowych zależności, spójne z Phase 1 stdlib-only constraint). Klasa `SPHShell(cmd.Cmd)` z metodami `do_help`, `do_exit`, `do_strategies`, `do_strategy`. Pattern verbatim z dokumentacji `cmd` modułu.
- **D-19:** `readline` importowany dla historii. Plik `~/.sphsim_history` (path: `os.path.expanduser('~/.sphsim_history')`). Read at startup, write at clean exit. `FileNotFoundError` przy pierwszym uruchomieniu = silent skip (nie błąd). `cmd.Cmd` integruje się z `readline` automatycznie na POSIX — strzałki góra/dół + Ctrl+R działają out-of-the-box.
- **D-20:** Ctrl+C w REPL = anuluj bieżącą linię (cmd.Cmd default — KeyboardInterrupt w `cmdloop` jest łapany przez cmd). Ctrl+D = clean exit (cmd.Cmd dispatch EOF → `do_EOF`, który musi zwracać `True` żeby zatrzymać loop). `exit` komenda również zwraca `True`. Pożegnanie: `Do widzenia.`

### Welcome intro (Full akademic header)
- **D-21:** Intro wyświetlane przy starcie REPL'a (przed pierwszym promptem):
  ```
  ==============================================================
    MEDIACJA TRANSFERU PŁATNYCH USŁUG — Symulator Strategii
    v1.1 (tryb interaktywny)
    Autorzy: Stanisław Nagórski, Mikołaj Rutkowski
    Na podstawie: J. Konorski, MPE cz. 2, KT WETI
  ==============================================================
    Wpisz `help` żeby zobaczyć dostępne komendy.
    Wpisz `exit` lub Ctrl+D żeby zakończyć.
  ==============================================================
  ```
- **D-22:** Prompt = `sph> ` (krótko, jednoznacznie). Bez ANSI colors (spójność z `format_human` z `output.py` które koloru nie używa).
- **D-23 (housekeeping):** Docstring w `sphsim/cli/args.py` ma obecnie tylko "Autor: Mikołaj Rutkowski". Phase 2 wyrównuje to do "Autorzy: Stanisław Nagórski, Mikołaj Rutkowski" (jedna linia w istniejącym pliku) żeby brand był spójny między REPL intro a `--help`. To jest jedyny dotyk istniejącego kodu Phase 1 (poza dodaniem `--interactive` w `parse_args`).

### Strategy metadata location
- **D-24:** Każdy plik `sphsim/strategies/<name>.py` eksportuje obok funkcji słownik `STRATEGY_META` o poniższym kontrakcie. Lokalność (metadata koło kodu) = sam plik strategii jest samowystarczalny i Phase 3 (custom strategy loader) używa tego samego kontraktu — custom strategie też eksportują `STRATEGY_META`.
  ```python
  STRATEGY_META = {
      'description': str,                # jedno-zdaniowy opis po polsku
      'params': list[tuple],             # [(name, type, default, opis), ...]
      'baseline_kpi': dict | None,       # opcjonalny — patrz D-25
  }
  ```
- **D-25:** `params` jako lista krotek 4-elementowych `(name: str, type: type, default: Any, description: str)`. `type` jako rzeczywista klasa Pythona (`float`, `int`, `str`) — pozwala formatować w `do_strategy` jako `zeta: float = 0.5 — Frakcja COMMIT (0..1)` bez konwersji string-do-typu. Wartości `name`/`default` muszą być identyczne z argumentami w argparse w `sphsim/cli/args.py` — to jest INVARIANT (Phase 2 dodaje smoke test który to weryfikuje, patrz `<code_context>` Integration Points).
- **D-26:** `baseline_kpi` jest opcjonalny. Tylko `naive` ma baseline z PROJECT.md/v1.0:
  ```python
  'baseline_kpi': {
      'invocation': 'naive --zeta 0.75',
      'avg_val_last100': 92.0,
      'source': 'PROJECT.md / v1.0 results',
  }
  ```
  Pozostałe 4 strategie (`threshold`, `phase_prob`, `incentive`, `adaptive`) mają `baseline_kpi: None`. Komenda `strategy <name>` przy `None` po prostu pomija sekcję baseline. NIE wczytujemy z `tests/fixtures/baseline_v1/*.json` — hardcode jest świadomy (zero I/O przy starcie REPL, zero ryzyka FileNotFoundError, refresh wartości = git commit metadanych).

### CLI integration (--interactive flag)
- **D-27:** `--interactive` jest mutually exclusive z `--strategy` w argparse (przez `add_mutually_exclusive_group(required=True)`). Wymusza to dwa wyraźne tryby: one-shot CLI (`--strategy X ...`) ALBO REPL (`--interactive`), bez mieszania. Próba `python sph_sim.py --interactive --strategy naive` daje argparse error w polskim stylu (mechanizm argparse domyślny, treść angielska — akceptowalne dla błędu argparse).
- **D-28:** Dotychczasowy walidator `--strategy` jako `required=True` musi zostać przeniesiony do mutually exclusive group jako "wymagane jest --interactive ALBO --strategy". Po refactorze: bez żadnego z dwóch flag = `error: jeden z argumentów --interactive --strategy jest wymagany`. To jest jedyna zmiana w `sphsim/cli/args.py` poza dodaniem samego `--interactive` (działa boolean store_true). **Backwards compat (CLI-04 z Phase 1):** wszystkie 8 fixtures z `tests/fixtures/baseline_v1/` używa `--strategy X` — bez `--interactive`. `scripts/regression_check.py` musi nadal przechodzić = mutex nie łamie tego (`--strategy X` bez `--interactive` jest valid).

### REPL UX details (table format + error messages)
- **D-29:** Tabela `strategies` = plain aligned text z paddingiem (12 znaków na nazwę, em-dash separator). Zero unicode box-drawing, zero zależności. Treść:
  ```
  Dostępne strategie:
    naive       — COMMIT z prawdopodobieństwem zeta
    threshold   — COMMIT tylko dla faz <= max_phase
    phase_prob  — COMMIT z P(commitów) per faza
    incentive   — COMMIT gdy E[zysk_netto] > 0
    adaptive    — COMMIT zależnie od poziomu bufora SUS
  ```
  Opis każdej strategii pochodzi z `STRATEGY_META['description']` (single source of truth). Phase 3 (custom loader) dodaje custom strategie do tej samej tabeli z prefiksem/sufiksem `[custom]`.
- **D-30:** Nieznana komenda (override `default()` w `SPHShell`):
  ```
  sph> srategies
  Nieznana komenda: 'srategies'. Wpisz 'help' żeby zobaczyć dostępne komendy.
  ```
  Bez fuzzy matching (Levenshtein/difflib). Dla 4 komend nie ma sensu.
- **D-31:** Nieistniejąca strategia w `strategy <nazwa>`:
  ```
  sph> strategy random
  Strategia 'random' nie istnieje. Dostępne: naive, threshold, phase_prob, incentive, adaptive.
  ```
  Lista wzięta z `STRATEGIES.keys()` (live, więc Phase 3 custom loader naturalnie pokaże dodane strategie).
- **D-32:** `strategy` bez argumentu (sam `strategy`) = `Użycie: strategy <nazwa>. Wpisz 'strategies' żeby zobaczyć listę.` Krótkie, kierujące do następnego kroku.

### Future hooks (minimal/YAGNI)
- **D-33:** Phase 2 NIE tworzy `sphsim/cli/session.py`, `strategy_browser.py`, ani innych pre-emptive helper modules. Tylko `sphsim/cli/repl.py` z klasą `SPHShell`. Konsekwencja: gdy Phase 3 doda `do_custom`, naturalna lokalizacja to "dodaj metodę do `SPHShell` w tym samym pliku" lub (jeśli plik urośnie) refactor na ten moment. Spójne z D-02 z Phase 1 ("nie tworzymy pustych stubów dla przyszłych modułów — YAGNI").

### Claude's Discretion
- Dokładny mechanizm `do_EOF` (musi zwracać `True` + opcjonalnie wydrukować `\n` przed pożegnaniem) — Claude wybiera.
- Kolejność wyświetlania pól w `strategy <name>` (description → params → baseline_kpi czy inaczej) — Claude wybiera; preferuj `description` na górze, baseline na dole.
- Format `params` w outpucie `strategy <name>` — Claude wybiera, byle czytelne (sugerowane: `  zeta: float = 0.5 — Frakcja COMMIT (0..1)`).
- Czy `do_EOF` drukuje pożegnanie identyczne jak `do_exit` — tak (jedno źródło prawdy).
- Smoke test weryfikujący invariant D-25 (`STRATEGY_META['params']` ↔ argparse) — Claude wybiera czy jako `tests/test_strategy_meta_consistency.py` czy jako asercja przy starcie REPL'a. Preferuj test (offline weryfikacja, nie spowalnia REPL).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specification & State
- `.planning/PROJECT.md` — Constraint "polski w komentarzach, komunikatach CLI" (musi dotyczyć REPL UX); Constraint "Python 3.7+ stdlib only" (uzasadnia wybór `cmd.Cmd` + `readline` w D-18/D-19); baseline `naive --zeta 0.75 → avg_val=92` (D-26).
- `.planning/REQUIREMENTS.md` §"CLI" — CLI-01 (`--interactive` REPL), CLI-02 (`/help` lista komend), CLI-03 (`/exit` lub `Ctrl+D`); §"STRAT" — STRAT-01 (`/strategies`), STRAT-02 (`/strategy <nazwa>` z params + baseline KPI). **Uwaga:** dokument używa nazw `/help`, `/strategies` itp. — D-17 zmienia na komendy bez prefiksu, intent zachowany.
- `.planning/ROADMAP.md` §"Phase 2" — 5 Success Criteria. **Uwaga:** SC mówią `/help`, `/strategies`, `/strategy naive`, `/exit` — D-17 zmienia na komendy bez slasha, UAT i `verify_phase2.sh` testują formę bez slasha.

### Phase 1 Output (już istnieje w repo, niezmienialne tutaj)
- `sphsim/strategies/__init__.py` — `STRATEGIES = {'naive': ..., 'threshold': ..., 'phase_prob': ..., 'incentive': ..., 'adaptive': ...}` (mutable global, D-14 z Phase 1). REPL czyta tę listę live (NIE robi własnej kopii).
- `sphsim/strategies/{naive,threshold,phase_prob,incentive,adaptive}.py` — każdy plik dostanie nową stałą `STRATEGY_META` (5 plików edytowanych w Phase 2). Funkcje strategii NIE są zmieniane.
- `sphsim/cli/args.py` — dodanie `--interactive` (boolean store_true) + przeniesienie `--strategy` z `required=True` do `add_mutually_exclusive_group(required=True)` z `--interactive` (D-27/D-28). Drobny update: "Autor: Mikołaj Rutkowski" → "Autorzy: Stanisław Nagórski, Mikołaj Rutkowski" (D-23).
- `sphsim/cli/main.py` — dodanie wczesnej gałęzi: `if args.interactive: from sphsim.cli.repl import run_repl; run_repl(); return`. Reszta funkcji `main()` (one-shot path) nietknięta.
- `tests/fixtures/baseline_v1/*.json` — 8 fixtures z Phase 1, nieedytowane w Phase 2. `scripts/regression_check.py` musi nadal pass = Phase 2 weryfikuje to jako acceptance criterion.

### v1.0 Reference (dla baseline KPI)
- `PROMPT_DLA_AGENTA.txt` — definicje KPI (`avg_val_last100`, etc.), baseline `naive --zeta 0.75 → avg_val=92`. Wartość trafia do `STRATEGY_META['baseline_kpi']` w `sphsim/strategies/naive.py`.

### Codebase Maps
- `.planning/codebase/STRUCTURE.md` — section map (przed refactorem, ale opisy strategii i ich docstringi pochodzą z `sph_sim.py:104–157` — referencja semantyczna).
- `.planning/codebase/ARCHITECTURE.md` — Strategy layer breakdown (każda strategia = pure function, sygnatura `(dev, l, s, phi, kappa, rho, h, p) -> 'COMMIT'|'ABSTAIN'`).
- `.planning/codebase/STACK.md` — potwierdzenie "stdlib only" — uzasadnia `cmd.Cmd` + `readline` (zero nowych zależności).

### Stdlib documentation (downstream agent może odwołać się do oficjalnej dokumentacji)
- `cmd` module — https://docs.python.org/3/library/cmd.html (klasa `Cmd`, `cmdloop`, `do_*`, `default`, `precmd`, `postcmd`, `prompt`, `intro`, `do_EOF` convention)
- `readline` module — https://docs.python.org/3/library/readline.html (`read_history_file`, `write_history_file`, integration with `input()`)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`STRATEGIES` dict (`sphsim/strategies/__init__.py:13-19`)** — live mutable registry; REPL iteruje po `STRATEGIES.keys()` i `STRATEGIES[name]`. Komenda `strategies` używa go bez kopiowania (Phase 3 custom loader doda klucze runtime'owo i automatycznie pokażą się w REPL).
- **`format_human()` (`sphsim/cli/output.py:16`)** — wzorzec wizualny banner'ów (`'='*62`, `'─'*62`) i wcięć — D-21 intro używa tej samej szerokości i stylu.
- **`argparse` setup (`sphsim/cli/args.py:32-57`)** — istniejący kontrakt typed args dla każdej strategii (`--zeta float`, `--max_phase int`, `--probs str`, `--s_target int`, `--expected_P float`). To jest źródło prawdy dla `STRATEGY_META['params']` (D-25 invariant).

### Established Patterns
- **Funkcja per plik strategii + registry pattern (D-03/D-14 z Phase 1)** — Phase 2 rozszerza ten sam pattern dodając `STRATEGY_META` jako drugi top-level export obok `strategy_*` funkcji. Plik strategii pozostaje samowystarczalny.
- **Polski w komentarzach i komunikatach** — wszystkie błędy REPL'a, intro, opisy w `STRATEGY_META['description']` po polsku. Identyfikatory w kodzie (function names, dict keys) po angielsku — spójne z istniejącym stylem (`STRATEGIES`, `STRATEGY_META`, `do_strategies`).
- **Stdlib only (Constraint z PROJECT.md)** — `cmd.Cmd` + `readline` + `os.path.expanduser` to wszystko ze stdlib. Phase 2 NIE dodaje `pyproject.toml`/`requirements.txt`. Pierwsza biblioteka zewnętrzna pojawia się dopiero w Phase 6 (matplotlib).

### Integration Points
- **Wejście CLI (`sphsim/cli/main.py:9`)**: nowa wczesna gałąź `if args.interactive: run_repl(); return` przed istniejącym kodem one-shot. `args` z argparse ma teraz pole `interactive` (boolean).
- **Wejście REPL (`sphsim/cli/repl.py:run_repl()`)**: funkcja top-level tworząca `SPHShell()` i wywołująca `.cmdloop()`. To jest jedyny publiczny export pliku — `from sphsim.cli.repl import run_repl`.
- **Czytanie metadanych strategii**: `do_strategy` w `SPHShell` robi `from sphsim.strategies import STRATEGIES` + dla każdej strategii dynamicznie importuje moduł żeby dostać `STRATEGY_META`. Pattern: `import importlib; mod = importlib.import_module(f'sphsim.strategies.{name}'); meta = mod.STRATEGY_META`. **Phase 3 hook:** custom loader już teraz musi wstrzykiwać funkcję `strategy_X` do `STRATEGIES` + atrybut `STRATEGY_META` do modułu — kontrakt jednoznaczny.
- **Invariant test (D-25)**: `tests/test_strategy_meta_consistency.py` (lub równoważne) importuje argparse z `sphsim/cli/args.py` i `STRATEGY_META` dla każdej z 5 strategii. Sprawdza że każdy param zadeklarowany w `STRATEGY_META['params']` ma odpowiadające `add_argument` z tą samą nazwą, typem i defaultem. Failure = explicit błąd "STRATEGY_META rozjazd: naive zeta default w argparse=0.5, w STRATEGY_META=0.6". To jest minimalna nowa warstwa testowa Phase 2 (cmd-level testy REPL'a są opcjonalne — patrz Claude's Discretion D-33).
- **Phase 1 regression suite musi nadal pass**: `scripts/regression_check.py` odpala 8 inwokacji wszystkie z `--strategy X`. Po dodaniu mutex group `--strategy X` bez `--interactive` jest valid (D-28) — regression nie powinna się złamać. Jest to acceptance criterion Phase 2.

</code_context>

<specifics>
## Specific Ideas

- **Welcome intro tekst (D-21)** — dokładny tekst po polsku, autorzy explicit: Stanisław Nagórski + Mikołaj Rutkowski. Spójność z `sphsim/cli/args.py` docstring (który po D-23 też wymienia oboje).
- **Baseline KPI tylko dla `naive`** (D-26) — pozostałe 4 strategie mają `baseline_kpi: None`. NIE wymyślamy syntetycznych baseline'ów dla `threshold`/`phase_prob`/`incentive`/`adaptive`. Phase 2 nie generuje nowych benchmarków.
- **`avg_val_last100: 92.0` z PROJECT.md** (D-26) — wartość kanoniczna, zapisana jako liczba float (nie string `"~92"`). Source field = `'PROJECT.md / v1.0 results'`.
- **Komendy bez slasha (D-17)** — explicit override decyzji wynikającej z dosłownego tekstu ROADMAP. `verify_phase2.sh` i UAT testują `help`, `strategies`, `strategy naive`, `exit` (nie `/help`, `/strategies`, etc.).
- **`STRATEGY_META['params']` to lista krotek 4-elementowych** (D-25), nie dict — kolejność wyświetlania w `strategy <name>` jest deterministyczna i mirroring kolejności w argparse `add_argument` calls.

</specifics>

<deferred>
## Deferred Ideas

- **Komenda `run` w REPL'u** — uruchamianie symulacji z REPL'a. Najnaturalniejsze miejsce dla Phase 3 lub samodzielnej decyzji w późniejszym discuss-phase (ROADMAP nie ma tego explicit w Phase 2-7, ale Phase 4 `compare` zakłada że strategia jest uruchamialna).
- **Komenda `custom <ścieżka>` w REPL'u** — Phase 3 (Custom strategy loader) — to jest jego scope.
- **Komenda `compare <strategia>`** — Phase 4 (Rational Agent veto layer) — tam ląduje delta KPI.
- **Override środowiska z REPL'a** (`set phi 0.1,0.2,...`) — Phase 5 (Configurable environment).
- **Komenda `batch <strategia> --seeds 10`** — Phase 7.
- **Tab autocomplete dla nazw strategii** — `cmd.Cmd` ma `complete_strategy` hook, ale Phase 2 nie implementuje. Można dodać jako quick win w późniejszej fazie jeśli pojawi się potrzeba.
- **Persystencja konfiguracji REPL'a** — `~/.sphsim_rc` z preferencjami (prompt, kolory itp.) — nie ma uzasadnienia teraz, projekt akademiczny.
- **Internationalization REPL UX** — odrzucone w PROJECT.md ("Out of Scope: Internacjonalizacja interfejsu — kod i interfejs zostają w języku polskim").
- **Fuzzy matching dla literówek** (`difflib.get_close_matches`) — odrzucone w D-30, dla 4 komend nie ma sensu. Jeśli liczba komend urośnie w Phase 3+ powyżej 8-10, warto rozważyć.
- **Centralna tabela `STRATEGY_INFO`** w `strategies/__init__.py` — odrzucone w Area 2 dyskusji (łamałoby Phase 3 custom loader).
- **Sidecar YAML/JSON dla metadanych** — odrzucone w Area 2 (łamałoby stdlib-only).
- **Rich/colored output (ANSI codes, `rich` library)** — odrzucone w D-22, spójność z istniejącym `format_human` które koloru nie używa.

</deferred>

---

*Phase: 2-Interactive CLI shell*
*Context gathered: 2026-05-25*
