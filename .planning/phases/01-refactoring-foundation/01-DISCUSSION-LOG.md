# Phase 1: Refactoring foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 1-Refactoring foundation
**Areas discussed:** Package layout & nazewnictwo, Entry-point mechanism, Backwards-compat verification, Module boundaries

---

## Package layout & nazewnictwo

### Q1: Nazwa pakietu vs konflikt z sph_sim.py

| Option | Description | Selected |
|--------|-------------|----------|
| `sphsim/` (bez podkreślnika) | Pakiet sphsim/, root sph_sim.py jako thin shim. Brak konfliktu, czysta separacja. | ✓ |
| `sph_sim/` + przeniesienie do bin/ | Zachowuje pełną nazwę ale wymaga ruszania pliku root — ryzyko zepsucia `python sph_sim.py`. | |
| `sph/` (krótka nazwa) | Najczystsza ale traci kontekst "simulator". | |

**User's choice:** `sphsim/`
**Notes:** Recommended option — naming conflict resolved najmniej inwazyjnie. `sph_sim.py` w root przetrwa jako shim.

### Q2: Które moduły TERAZ vs odkładamy

| Option | Description | Selected |
|--------|-------------|----------|
| Tylko Phase 1 needs (core/strategies/cli) | YAGNI, 3 moduły. Agent/report/batch dodawane w odpowiednich fazach. | ✓ |
| Wszystkie 6 od razu (puste stuby) | Locks shape pakietu ale martwe pliki. | |
| Minimum (tylko core/cli, strategies płasko) | Phase 3 i tak będzie musiał rozbić strategies. | |

**User's choice:** Tylko Phase 1 needs
**Notes:** YAGNI wygrywa. Każda faza buduje swoje moduły.

### Q3: strategies/ podpakiet — jeden plik czy osobne?

| Option | Description | Selected |
|--------|-------------|----------|
| Jeden plik strategies/builtin.py + registry.py | Prosta struktura, analog v1.0. | |
| Osobny plik per strategia (5 plików) | Pełna izolacja, każda strategia testowalna niezależnie. | ✓ |
| Jeden płaski strategies.py | Niezgodne z roadmap. | |

**User's choice:** Osobny plik per strategia
**Notes:** Użytkownik wybrał izolację mimo niewielkiego rozmiaru każdego pliku. Daje czystą bazę dla Phase 3 (custom loader) gdzie strategie też są pojedynczymi plikami.

### Q4: Gdzie DEFAULT_* constants

| Option | Description | Selected |
|--------|-------------|----------|
| Osobny sphsim/config.py | Jeden punkt zmiany dla Phase 5 (configurable env). | ✓ |
| W core/model.py razem z math | "Wszystko domenowe w jednym miejscu". | |
| W cli/args.py jako argparse defaults | Nie da się importować spoza CLI. | |

**User's choice:** `sphsim/config.py`
**Notes:** Phase 5 będzie nadpisywać defaults z CLI — osobny plik daje jasny punkt zmian.

---

## Entry-point mechanism

### Q1: Co robi shim sph_sim.py w root

| Option | Description | Selected |
|--------|-------------|----------|
| Tylko CLI dispatch | Minimal: `from sphsim.cli.main import main; main()`. | ✓ |
| Dispatch + re-export API | Zachowuje wsteczną kompatybilność dla `from sph_sim import SPHSimulator`. | |
| Re-export + DeprecationWarning | Migracja-friendly ale over-engineered dla single-author project. | |

**User's choice:** Tylko CLI dispatch
**Notes:** Single-author project akademicki — nikt nie importuje monolitu programmatic, więc nie potrzebujemy re-exportów.

### Q2: python -m sphsim też?

| Option | Description | Selected |
|--------|-------------|----------|
| Tak — dodaj sphsim/__main__.py | Standard Python idiom, zero kosztu. | ✓ |
| Nie — tylko python sph_sim.py | Strict v1.0 invocation only. | |

**User's choice:** Tak, __main__.py
**Notes:** Dodatkowa ścieżka uruchamiania bez kosztu utrzymania.

### Q3: pyproject.toml w Phase 1?

| Option | Description | Selected |
|--------|-------------|----------|
| Nie, bez packaging metadata | Projekt lokalny, nie publikowany. | ✓ |
| Tak, minimalny pyproject.toml | `pip install -e .` dla dev. | |

**User's choice:** Nie
**Notes:** Deferred do v2.0 jeśli pojawi się distribution use case.

---

## Backwards-compat verification

### Q1: Strategia weryfikacji

| Option | Description | Selected |
|--------|-------------|----------|
| Snapshot JSON fixtures + skrypt regression | Pure stdlib, prosty assert, exit code != 0. | ✓ |
| Pytest harness z parametrize + fixtures | Idiomatic, lepsze CI ale dodaje pytest. | |
| Manualny checklist + git diff | Brak automatyzacji. | |
| Property test (Hypothesis) | Tylko strukturalne, nie numeryczne — niewystarczające dla CLI-04. | |

**User's choice:** Snapshot JSON fixtures + skrypt regression
**Notes:** Zero new dev dependencies. Stdlib script wystarczy.

### Q2: Które inwokacje w snapshot suite

| Option | Description | Selected |
|--------|-------------|----------|
| Wszystkie 7 z docstringu + 1 baseline (8 total) | Pełne pokrycie kombinacji z v1.0 + baseline z PROJECT.md. | ✓ |
| Minimum: 5 strategii z defaults | Pokrywa większość ale nie env overrides. | |
| Tylko baseline naive --zeta 0.75 | Za wąsko. | |

**User's choice:** Wszystkie 7 z docstringu + 1 baseline
**Notes:** 8 fixtures, lista konkretnie wymieniona w CONTEXT.md D-09.

### Q3: Fixtures committowane?

| Option | Description | Selected |
|--------|-------------|----------|
| Tak, autorytatywny baseline w repo | Git diff przy każdej zmianie, peer review widoczne. | ✓ |
| Nie, generowane przez setup script lokalnie | Brak ground truth w repo. | |

**User's choice:** Tak commit
**Notes:** ~5 KB/plik × 8 = ~40 KB, minimalne obciążenie repo.

### Q4: Kiedy generujemy baseline

| Option | Description | Selected |
|--------|-------------|----------|
| Pierwszy krok Phase 1: skrypt + commit z monolitu | Atomic commit "przed-refactor" jako ground truth. | ✓ |
| Manualnie przed plan-phase | Wymaga akcji poza GSD workflow. | |
| Generuj ad-hoc w każdym tests run | Brak ground truth, baseline się "przesuwa". | |

**User's choice:** Pierwszy krok Phase 1
**Notes:** Critical ordering — plan 1 fazy 1 to MUSI być generate-baseline, nie refactor. Inaczej nie ma odniesienia.

---

## Module boundaries

### Q1: Jak rozbijamy core/

| Option | Description | Selected |
|--------|-------------|----------|
| core/model.py + device.py + simulator.py | 3 pliki, pełna separacja. | ✓ |
| core/model.py (math+Device) + simulator.py | 2 pliki, miesza math z dataclass. | |
| Jeden core/sim.py | >150 linii, narusza roadmap criterion 2. | |

**User's choice:** 3 pliki (model + device + simulator)
**Notes:** Każdy plik ~40–150 linii, czyste single-responsibility.

### Q2: STRATEGIES dict gdzie

| Option | Description | Selected |
|--------|-------------|----------|
| strategies/__init__.py eksportuje STRATEGIES | Importuje funkcje, składa dict. | ✓ |
| Osobny strategies/registry.py | Dwa miejsca, jasna intencja ale extra plik. | |

**User's choice:** strategies/__init__.py
**Notes:** Mniej plików, importuje 5 funkcji ze swoich modułów.

### Q3: cli/ split

| Option | Description | Selected |
|--------|-------------|----------|
| cli/args.py + main.py + output.py | 3 pliki, miejsce na Phase 2 repl.py. | ✓ |
| cli/main.py + output.py | 2 pliki, ale main.py spuchnie w Phase 2. | |
| Jeden cli/__init__.py | Mało miejsca na rozszerzenia. | |

**User's choice:** 3 pliki (args + main + output)
**Notes:** Phase 2 doda cli/repl.py obok bez reorganizacji.

### Q4: Strategy type — Protocol/ABC czy funkcje

| Option | Description | Selected |
|--------|-------------|----------|
| Luźne funkcje z docstring sygnatury | Spójne z v1.0, prosty refactor, Phase 3 friendly. | ✓ |
| typing.Protocol StrategyProtocol | mypy-friendly ale brak typecheckera w projekcie. | |
| Abstract base class StrategyBase | Wymaga dziedziczenia, ciężkie dla Phase 3. | |

**User's choice:** Plain functions
**Notes:** Opcjonalny type alias `StrategyFn = Callable[..., str]` w `strategies/__init__.py`.

### Q5: sphsim/__init__.py — re-exports?

| Option | Description | Selected |
|--------|-------------|----------|
| Tak: SPHSimulator + STRATEGIES + Device | Programmatic-friendly dla test harness, notebooków. | ✓ |
| Pusty __init__.py | User musi używać pełnych ścieżek. | |

**User's choice:** Tak, re-export
**Notes:** Krótka lista publicznego API.

---

## Claude's Discretion

- Konkretna nazwa pliku defaults (`config.py` vs `defaults.py`) — Claude wybrał `config.py`.
- Format `scripts/regression_check.py` (klasa vs funkcje, kolorowanie diff) — Claude wybiera w plan-phase, byle exit code != 0 przy regresji.
- Naming convention dla 8 fixture JSON-ów (`tests/fixtures/baseline_v1/<slug>.json`) — Claude wybierze spójną konwencję w plan-phase.
- Pretty-print vs compact JSON w fixtures — Claude preferuje pretty (indent=2) dla czytelnego git diff.

## Deferred Ideas

- `pyproject.toml` + `pip install -e .` — v2.0 jeśli distribution use case.
- `typing.Protocol` dla strategii / mypy integration — może być dodane jako odrębne ulepszenie po v1.1.
- `DeprecationWarning` dla starych import paths — pominięte (single-author project).
- pytest harness zamiast `scripts/regression_check.py` — deferred do momentu gdy będzie więcej testów.
- Strategies as classes/composable objects — pominięte, niezgodne z v1.0.
