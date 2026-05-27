# Phase 3: Custom strategy loader - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-27
**Phase:** 03-custom-strategy-loader
**Areas discussed:** Kontrakt pliku custom, Params runtime + komenda run, Mutex CLI + ostrzeżenie bezpieczeństwa, Walidacja + listing + template

---

## Area 1: Kontrakt pliku custom

### Q1.1 — Skąd loader bierze nazwę custom strategii?

| Option | Description | Selected |
|--------|-------------|----------|
| Basename pliku | `my_strat.py` → `my_strat`. Najprostsze, zero ceremonii. Konflikt z built-in → error. | ✓ |
| STRATEGY_META['name'] | Decoupling pliku od nazwy strategii. | |
| Nazwa funkcji (strategy_X → X) | Spójne z built-in pattern, ale wymaga prefixu w nazwie funkcji. | |
| Ty decydujesz | Claude wybiera — preferuje basename + opcjonalny override przez meta. | |

**User's choice:** Basename pliku
**Notes:** Single source of truth — sama nazwa pliku determinuje nazwę strategii. Captured as D-34.

### Q1.2 — Jak loader znajduje funkcję strategii?

| Option | Description | Selected |
|--------|-------------|----------|
| Prefix `strategy_<basename>` | Verbatim ten sam pattern co built-in (D-03/D-14 Phase 1). | ✓ |
| Fixed name `strategy` | Krótsze, ale łamie spójność z built-in. | |
| Referencja w meta: STRATEGY_META['fn'] | Najbardziej elastyczne, ale boilerplate. | |

**User's choice:** Prefix `strategy_<basename>`
**Notes:** Custom plik bit-by-bit identyczny z built-in (`naive.py` ma `strategy_naive`, custom `my.py` ma `strategy_my`). Captured as D-35.

### Q1.3 — Czy `--custom <ścieżka>` ogranicza lokalizację?

| Option | Description | Selected |
|--------|-------------|----------|
| Dowolna ścieżka | Absolutna i relatywna, expanduser + abspath. Banner ostrzega. | ✓ |
| Tylko examples/ albo cwd | Whitelist katalogów. Sztuczne dla academic. | |
| Ty decydujesz | Claude wybiera. | |

**User's choice:** Dowolna ścieżka
**Notes:** Projekt akademicki, lokalny — sandbox by był sztucznym ograniczeniem. Captured as D-36.

### Q1.4 — Persistencja w REPL'u?

| Option | Description | Selected |
|--------|-------------|----------|
| Sticky do końca sesji | Załadowana zostaje w STRATEGIES do `exit`. Phase 4 `compare` skorzysta. | ✓ |
| Sticky + komenda `unload` | YAGNI dla Phase 3. | |
| Reload za każdym razem | Importlib.reload przy każdym `custom <ścieżka>`. | |

**User's choice:** Sticky do końca sesji
**Notes:** Naturalny model — raz załadowane, wielokrotnie wybieralne. Reload uzyskany przez powtórne `custom my.py`. Captured as D-37/D-38.

---

## Area 2: Params runtime + komenda `run`

### Q2.1 — Jak użytkownik przekazuje params do custom strategii?

| Option | Description | Selected |
|--------|-------------|----------|
| Generyczne `--param k=v` | CLI: `--param zeta=0.7` (repeatable). REPL: `custom my.py zeta=0.7`. | ✓ |
| Dynamiczne argparse z meta | Loader pre-skanuje, dodaje flagi runtime. Najergonomiczniejsze ale komplikuje args.py. | |
| JSON `--params '{...}'` | Zwarte ale brzydkie w shell'u. | |
| Tylko defaults z meta | Brak runtime override. Niepraktyczne. | |

**User's choice:** Generyczne `--param k=v`
**Notes:** Prosta implementacja, jednolity input shape dla CLI i REPL. Captured as D-39.

### Q2.2 — Skąd typy do konwersji `k=v`?

| Option | Description | Selected |
|--------|-------------|----------|
| STRATEGY_META['params'] | Pojedyncze źródło prawdy. ValueError → polski błąd. | ✓ |
| Auto-detect | Bez walidacji że parametr istnieje. | |
| Wszystko string | Strategia sama konwertuje. Przesuwa odpowiedzialność. | |

**User's choice:** STRATEGY_META['params']
**Notes:** Param niezadeklarowany w meta → polski error z dostępnymi paramami. Captured as D-40.

### Q2.3 — Sygnatura komendy `custom` w REPL'u?

| Option | Description | Selected |
|--------|-------------|----------|
| `custom <ścieżka> [k=v ...]` | Whitespace split, jednolite z CLI. Edge case: ścieżki ze spacjami nie wspierane. | ✓ |
| Tylko ładowanie, params osobno | Wymaga session state. | |
| JSON-like w REPL | Brzydkie. | |

**User's choice:** `custom <ścieżka> [k=v ...]`
**Notes:** Captured as D-43.

### Q2.4 — Czy Phase 3 dodaje komendę `run` w REPL'u?

| Option | Description | Selected |
|--------|-------------|----------|
| Dodaj `run` w Phase 3 | Bez tego loaded custom strategia jest "zawieszona". Phase 2 odkładała tutaj. | ✓ |
| Tylko CLI one-shot | REPL ładuje ale nie uruchamia. UX rozczarowuje. | |
| Odkładamy `run` na Phase 4 | Razem z `compare`. | |

**User's choice:** Dodaj `run` w Phase 3
**Notes:** Phase 2 CONTEXT explicitly deferred `run` to Phase 3 — to NIE scope creep, to clarification odłożonej decyzji. Captured as D-41.

### Q2.5 — Sygnatura `run`?

| Option | Description | Selected |
|--------|-------------|----------|
| `run <nazwa> [k=v ...]` | Działa dla built-in i custom, jednolicie. Env params z config.py. | ✓ |
| `run` bez argumentów | Wymaga session state. Złożone. | |
| `run <nazwa>` + osobne `set` | Pełen sub-shell. Phase 5/7. | |

**User's choice:** `run <nazwa> [k=v ...]`
**Notes:** Output = `format_human` (krótki), brak `--json` w REPL'u. Captured as D-41/D-42.

---

## Area 3: Mutex CLI + ostrzeżenie bezpieczeństwa

### Q3.1 — Jak `--custom` wpisuje się w mutex?

| Option | Description | Selected |
|--------|-------------|----------|
| Trzeci człon mutex | `mutex.add_argument('--custom', ...)`. Czyste 3 tryby. | ✓ |
| Pod-flaga `--strategy` | `--strategy custom --custom-file my.py`. Mniej eleganckie. | |
| Loader+strategy combo | `--custom my.py --strategy my`. Redundancja. | |

**User's choice:** Trzeci człon mutex
**Notes:** Mutex `--interactive | --strategy | --custom`, required=True. Backwards compat zachowane. Captured as D-44.

### Q3.2 — Prominence ostrzeżenia bezpieczeństwa?

| Option | Description | Selected |
|--------|-------------|----------|
| Cichy banner pre-import | Jedna linia przed importem, CLI i REPL identycznie. Zero friction. | ✓ |
| Interaktywne `[y/N]` (REPL) | Bezpieczniej dla nowych userów, ale friction przy iteracji. | |
| Cichy banner + `--no-warn` | YAGNI. | |

**User's choice:** Cichy banner pre-import
**Notes:** Spójne z PROJECT.md "loader powinien jasno komunikować". Captured as D-45.

### Q3.3 — Treść banner'a?

| Option | Description | Selected |
|--------|-------------|----------|
| Jednolinijka `[OSTRZEŻENIE] Ładuję arbitralny kod...` | Zwięzłe, jedna linia output. | ✓ |
| Box-drawing 3 linie | Bardziej widoczne ale rozwleka output. | |
| Multi-line z kontekstem | Edukacyjne ale patronizing. | |

**User's choice:** Jednolinijka
**Notes:** Dokładny tekst: `[OSTRZEŻENIE] Ładuję arbitralny kod Pythona z: <abspath>`. Captured as D-45.

---

## Area 4: Walidacja + listing + template

### Q4.1 — Głębokość walidacji?

| Option | Description | Selected |
|--------|-------------|----------|
| 3-warstwowa: import / fn / sig + meta | (1) try/except import, (2) callable check, (3) inspect.signature, (4) STRATEGY_META validation. Fail-fast. | ✓ |
| Tylko callable + arity 8 | Bez sprawdzania nazw param. Błędy późno. | |
| Best-effort, no strict signature | Pozwala duck-typing ale fail-late w simulator loop. | |

**User's choice:** 3-warstwowa
**Notes:** Captured as D-47 (4 layers actually: import, callable, signature, meta). `LoaderError` jako custom exception (D-48).

### Q4.2 — Konflikt nazw z built-in?

| Option | Description | Selected |
|--------|-------------|----------|
| Error — każ zmienić nazwę | Built-in to source of truth, nie shadow'uj. | ✓ |
| Auto-prefix `_custom` | Magia, user nie wie skąd nowa nazwa. | |
| Override built-in | Niebezpieczne dla baseline'ów. | |
| Custom-custom collision | Też reload (basename wygrywa). | |

**User's choice:** Error — każ zmienić nazwę
**Notes:** `BUILTIN_STRATEGIES = frozenset(...)` jako snapshot Phase 1, niemutowalny. Custom-custom collision: reload (D-38). Captured as D-49.

### Q4.3 — Semantyka powtórnego `custom my.py`?

| Option | Description | Selected |
|--------|-------------|----------|
| Reload — nadpisuje | importlib.reload, naturalne dla iteracji edit-save. | ✓ |
| Error przy drugim | Wymaga `unload`. YAGNI. | |

**User's choice:** Reload — nadpisuje
**Notes:** Komunikat: `Przeładowano custom strategię 'X'.` vs `Załadowano custom strategię 'X'.` (pierwszy raz). Captured as D-38.

### Q4.4 — Listing custom strategii?

| Option | Description | Selected |
|--------|-------------|----------|
| Suffix `[custom]` | `  my_strat   — Opis [custom]`. Nazwa lewa, znacznik w opisie. | ✓ |
| Prefix `[custom]` | Łamie aligned padding. | |
| Osobna sekcja | Gadatliwe dla małej listy. | |

**User's choice:** Suffix `[custom]`
**Notes:** Argparse `--strategy choices` używa `list(BUILTIN_STRATEGIES)` (snapshot), bo CLI parse jest przed rejestracją custom. Custom uruchamiany przez `--custom <ścieżka>`. Captured as D-50.

### Q4.5 — Template `examples/custom_strategy_template.py`?

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal + komentarze edukacyjne | ~30-50 linii, prosta strategia (threshold-like), pełne STRATEGY_META. | ✓ |
| Tutorial z 3 wariantami | Dłuższy, gorszy do skopiowania-i-modyfikacji. | |
| Minimal bez komentarzy | Wymaga zewnętrznej dokumentacji. | |

**User's choice:** Minimal + komentarze edukacyjne
**Notes:** Acceptance check: `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json` musi działać out-of-the-box (SC #3). Captured as D-51/D-52.

### Q4.6 — Format błędów loadera?

| Option | Description | Selected |
|--------|-------------|----------|
| Inline jednolinijka per błąd | `Błąd: Brak funkcji 'strategy_X' w /path. Oczekiwana sygnatura: ...` | ✓ |
| Multi-line z hint'ami | "Sprawdź:" lista. Bardziej pomocne ale więcej utrzymania. | |

**User's choice:** Inline jednolinijka
**Notes:** Łatwiej skopiować do issue/grep'a. `LoaderError(message)` raise → caller drukuje `e.args[0]`. Captured as D-48.

---

## Claude's Discretion

Areas where user deferred to Claude:

- Stdout vs stderr dla banner'a (D-45) — Claude preferuje stdout, banner to info, nie błąd
- Mechanika reload (D-38) — `importlib.reload` vs spec_from_file_location (Claude wybiera per sytuacja)
- Czy `do_strategies` cache'uje meta czy live import (D-50) — Claude preferuje live (custom z `sphsim.custom.<name>` namespace)
- Czy `do_run` ma `--verbose` (D-41) — Claude preferuje nie (REPL ma być zwięzły)
- Coverage testów loadera — Claude wybiera czy `tests/test_loader.py` osobno
- `--param` jako `action='append'` z default `[]` — TAK, Claude implementuje
- Format error gdy `--param` bez `--custom` — graceful warning + ignore (Claude wybiera)

## Deferred Ideas

- Komenda `unload <nazwa>` — YAGNI, reload przez powtórne `custom` wystarcza
- Komenda `compare <strategia>` — Phase 4 (Rational Agent)
- Override env params w REPL'u — Phase 5
- Komenda `batch` — Phase 7
- `--no-warn` flag — odrzucone (YAGNI, jedna linia banner'a)
- Confirmation `[y/N]` — odrzucone (friction)
- Whitelist katalogów — odrzucone (academic projekt)
- Session state object — odrzucone (każdy `run` self-contained w Phase 3)
- Tab autocomplete — Phase 7 polish
- JSON `--params` — odrzucone
- Dynamiczne rozszerzanie argparse z meta — odrzucone
- Persistencja custom do `~/.sphsim_strategies/` — odrzucone
- Multi-line error messages — odrzucone
- Rich/colored output — spójność z Phase 2 D-22
