# Phase 2: Interactive CLI shell - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 02-interactive-cli-shell
**Areas discussed:** REPL library, Strategy metadata + baseline KPI, REPL UX details, REPL entry + future hooks

---

## REPL library

| Option | Description | Selected |
|--------|-------------|----------|
| stdlib `cmd.Cmd` | Klasa z `do_*` metodami. Zero nowych zależności, spójne z stdlib-only constraint. Brak Ctrl+R search out-of-the-box ale działa autocomplete podstawowy. | ✓ |
| goły `input()` loop | `while True: line = input('sph> ')` + ręczny dispatch. Pełna kontrola, brak historii. | |
| `prompt_toolkit` | Nowa zależność (łamie stdlib-only). Historia persistent, fuzzy autocomplete, syntax highlighting. Over-engineering dla 4 komend. | |

**User's choice:** stdlib `cmd.Cmd`
**Notes:** Spójność z constraint "Python stdlib only" z PROJECT.md (D-18).

---

## Slash prefix dla komend

| Option | Description | Selected |
|--------|-------------|----------|
| Override `parseline()` | Akceptuje `/help` i `help`. Najmniejsza ingerencja. | |
| Strict `/` only | Tylko `/help` valid. Zgodne 1:1 z literą ROADMAP. | |
| Tolerant aliases | `/help` i `help` równoważne explicit. | |
| **Free-text:** komendy bez prefiksu | "nie potrzebujemy komend z '/' to było jedynie propozycja. komendy mogą być bezpośrednio jak łatwiej" | ✓ |

**User's choice:** Komendy bez slasha (`help`, `exit`, `strategies`, `strategy naive`) — natywny `cmd.Cmd` style.
**Notes:** Świadome odstępstwo od dosłownego tekstu ROADMAP Success Criteria. Intent (browser strategii) zachowany. UAT i `verify_phase2.sh` muszą testować formę bez slasha (D-17).

---

## Welcome intro

| Option | Description | Selected |
|--------|-------------|----------|
| 1-liner banner | Krótki ASCII tag (`=`*62 + 2 linie). | |
| Minimalist | Goły jednolinier bez ramki. | |
| Full akademic header | Z brand'em z args.py docstring (autor, KT WETI, MPE cz. 2). | ✓ |

**User's choice:** Full akademic header z autorami "Stanisław Nagórski, Mikołaj Rutkowski".
**Notes:** Doprecyzowanie: istniejący docstring w `sphsim/cli/args.py` ma tylko "Autor: Mikołaj Rutkowski" — Phase 2 wyrówna do "Autorzy: Stanisław Nagórski, Mikołaj Rutkowski" w obu miejscach (REPL intro + args.py docstring) — D-23.

---

## Strategy metadata source

| Option | Description | Selected |
|--------|-------------|----------|
| `STRATEGY_META` dict per plik | Lokalność = opis koło kodu. Phase 3 custom loader używa tego samego kontraktu. | ✓ |
| Docstring + introspection | `inspect.getdoc()` + `inspect.signature()`. Mniej boilerplate ale brak structured params. Fragile. | |
| Central registry | `STRATEGY_INFO` obok `STRATEGIES`. Łamałoby Phase 3 — custom loader musiałby mutować dwa dicty. | |
| Sidecar YAML | Łamie stdlib-only. | |

**User's choice:** `STRATEGY_META` dict per plik (D-24).
**Notes:** Kontrakt: `description: str`, `params: list[tuple]`, `baseline_kpi: dict | None` (D-25, D-26).

---

## Baseline KPI source

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcode w `STRATEGY_META` | Wartość jako konstanta. Zero I/O, zero FileNotFoundError. Refresh = git commit. Tylko `naive` ma baseline. | ✓ |
| Wczytaj z fixtures | REPL czyta `tests/fixtures/baseline_v1/*.json` przy starcie. Coupling do nazw plików. | |
| Re-run sim w tle | `strategy naive` faktycznie uruchamia symulację. 300ms+ per komenda — zła UX. | |

**User's choice:** Hardcode w `STRATEGY_META`. Tylko `naive` ma baseline (avg_val_last100=92.0 z PROJECT.md). Pozostałe strategie: `baseline_kpi: None` (D-26).

---

## Tabela `strategies` — format

| Option | Description | Selected |
|--------|-------------|----------|
| Plain aligned text | F-string z paddingiem + em-dash. Zero unicode. Spójne z output.py. | ✓ |
| Unicode box table | `┌ ─ ┬ ┐ ...` ramka. Bardziej formalny look. | |
| ASCII pipe table | Markdown-style `|name|desc|`. | |

**User's choice:** Plain aligned text (D-29).

---

## Historia komend i Ctrl+C/Ctrl+D

| Option | Description | Selected |
|--------|-------------|----------|
| `readline` + `~/.sphsim_history` | Persistent między sesjami. Strzałki + Ctrl+R działają. Ctrl+C anuluje linię, Ctrl+D = exit. | ✓ |
| Session-only history | Tylko bieżąca sesja, nic na dysk. Ctrl+C = exit (KeyboardInterrupt nie łapany). | |
| Brak historii | `use_rawinput = False`. Czyste `input()` bez Tab-complete. Regres UX. | |

**User's choice:** `readline` + `~/.sphsim_history` (D-19, D-20).

---

## Nieznana komenda

| Option | Description | Selected |
|--------|-------------|----------|
| Polish error + sugestia | `Nieznana komenda: 'X'. Wpisz 'help' żeby zobaczyć dostępne komendy.` | ✓ |
| Default `cmd.Cmd` (English) | `*** Unknown syntax: X` — inkonsystencja językowa. | |
| Polish + did-you-mean | `difflib.get_close_matches`. Dla 4 komend over-kill. | |

**User's choice:** Polish error + sugestia (D-30).

---

## Nieistniejąca strategia w `strategy <nazwa>`

| Option | Description | Selected |
|--------|-------------|----------|
| Polish error + lista | `Strategia 'X' nie istnieje. Dostępne: naive, threshold, ...` | ✓ |
| Polish + did-you-mean | Tylko sugestia bez listy. | |
| Pusta lista + komunikat | Mniej informacyjnie. | |

**User's choice:** Polish error + lista wzięta z `STRATEGIES.keys()` (D-31).

---

## CLI integration — `--interactive` flag

| Option | Description | Selected |
|--------|-------------|----------|
| Strict: exclusive z `--strategy` | argparse error gdy oba. Czyste rozdzielenie trybów one-shot vs REPL. | ✓ |
| Tolerant: REPL ignoruje pozostałe flagi | `--interactive --strategy naive` startuje REPL i ignoruje strategię. Ukrywa błędy. | |
| REPL session defaults | `--interactive --seed 7` zachowuje jako default dla przyszłych komend `run`. Wymaga `Session` shape. | |

**User's choice:** Strict (D-27, D-28). Mutually exclusive group w argparse, `--strategy` lub `--interactive` wymagane.

---

## Future hooks (Phase 3-7 readiness)

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal (YAGNI) | Tylko `SPHShell` z 4 metodami w `cli/repl.py`. Phase 3 dodaje `do_custom` przez naturalny grow. | ✓ |
| Session object + helpers | `cli/session.py` + `cli/strategy_browser.py` już teraz. Pre-emptive scaffolding. Łamałoby D-02 z Phase 1. | |
| Bez klasy, goła funkcja | Przeczyłoby wyborowi cmd.Cmd. | |

**User's choice:** Minimal/YAGNI (D-33).
**Notes:** Użytkownik pierwotnie napisał "nie rozumiem tego pytania i konsekwencji". Po wyjaśnieniu (Opcja A = dopisać `do_custom` do istniejącej klasy w Phase 3; Opcja B = tworzyć pliki session.py/strategy_browser.py których Phase 2 nie używa) wybrał A — spójne z D-02 z Phase 1 ("nie tworzymy pustych stubów dla przyszłych modułów").

---

## Claude's Discretion

- Dokładny mechanizm `do_EOF` (musi zwracać `True` + opcjonalnie `print('\n')` przed pożegnaniem).
- Kolejność wyświetlania pól w `strategy <name>` (preferuj `description` na górze, baseline na dole).
- Format `params` w outpucie `strategy <name>` — sugerowane `  zeta: float = 0.5 — Frakcja COMMIT (0..1)`.
- Czy `do_EOF` drukuje pożegnanie identyczne jak `do_exit` — tak, jedno źródło prawdy.
- Format i lokalizacja smoke testu D-25 (`STRATEGY_META` ↔ argparse consistency) — preferuj `tests/test_strategy_meta_consistency.py`.

## Deferred Ideas

- Komenda `run` w REPL'u — uruchamianie symulacji (Phase 3-4 zone).
- Komenda `custom <ścieżka>` — Phase 3 (Custom strategy loader).
- Komenda `compare <strategia>` — Phase 4 (Rational Agent veto layer).
- Override środowiska z REPL'a (`set phi ...`) — Phase 5.
- Komenda `batch <strategia> --seeds N` — Phase 7.
- Tab autocomplete dla nazw strategii (`complete_strategy` hook) — quick win na później.
- Persystencja konfiguracji REPL'a (`~/.sphsim_rc`) — brak uzasadnienia w projekcie akademickim.
- i18n REPL UX — explicit odrzucone w PROJECT.md.
- Fuzzy matching literówek (`difflib.get_close_matches`) — odrzucone w D-30, dla 4 komend over-kill.
- Centralna tabela `STRATEGY_INFO` w `strategies/__init__.py` — odrzucone (łamałoby Phase 3).
- Sidecar YAML/JSON dla metadanych — odrzucone (łamałoby stdlib-only).
- Rich/colored output (ANSI codes) — odrzucone w D-22.
