# Phase 1: Refactoring foundation - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Rozbicie monolitycznego `sph_sim.py` (433 linie) na pakiet Pythona `sphsim/` z modułami o jednej odpowiedzialności (≤ 150 linii każdy), przy 100% backwards compatibility — wszystkie inwokacje CLI z v1.0 (`python sph_sim.py --strategy <name> [opts]`) zwracają identyczne wyniki numeryczne dla tego samego `--seed`. Faza ustanawia shape pakietu na fazy 2–7 (REPL, custom loader, agent veto, env config, reports, batch), ale dodaje TYLKO to czego potrzebuje refactor monolitu — bez stubów dla przyszłych modułów (YAGNI).

**Scope:** refactor + harness regresji. Out of scope: nowe feature'y, zmiany API CLI, dodatkowe zależności, optymalizacje wydajności.

</domain>

<decisions>
## Implementation Decisions

### Package Layout & Nazewnictwo
- **D-01:** Nazwa pakietu = `sphsim/` (krótka, bez konfliktu z `sph_sim.py` w root). NIE `sph_sim/` — kolidowałoby z istniejącym plikiem o tej samej nazwie.
- **D-02:** Moduły tworzone w Phase 1: `sphsim/core/`, `sphsim/strategies/`, `sphsim/cli/`, plus top-level `sphsim/config.py` (defaults) i `sphsim/__init__.py`. Moduły `agent/`, `report/`, `batch/` dodawane dopiero w fazach 4, 6, 7 — YAGNI, nie tworzymy pustych stubów.
- **D-03:** Każda strategia w osobnym pliku: `sphsim/strategies/naive.py`, `threshold.py`, `phase_prob.py`, `incentive.py`, `adaptive.py`. Każdy ~10–40 linii. STRATEGIES dict w `sphsim/strategies/__init__.py` składany z importów funkcji.
- **D-04:** Wszystkie DEFAULT_* (NU, NSUS, K0, K1, F, T, KAPPA, ALPHA, PHI, RHO) centralizowane w `sphsim/config.py` — Phase 5 (configurable environment) będzie miała jeden punkt nadpisywania.

### Entry-Point Mechanism
- **D-05:** `sph_sim.py` w root = thin shim, tylko CLI dispatch:
  ```python
  from sphsim.cli.main import main
  if __name__ == '__main__':
      main()
  ```
  Bez re-exportów programmatic API, bez kompatybilnościowych aliasów (`from sph_sim import SPHSimulator` w skryptach trzeciego strzelca nie był używany — projekt akademicki single-author).
- **D-06:** Dodatkowo `sphsim/__main__.py` żeby `python -m sphsim ...` też działało (standard Python idiom). Plik to: `from sphsim.cli.main import main; main()`.
- **D-07:** BEZ `pyproject.toml` / `setup.cfg` w Phase 1. Projekt lokalny, nie publikowany. Można dodać w v2.0 jeśli pojawi się use case.

### Backwards-Compat Verification
- **D-08:** Strategia weryfikacji = **snapshot JSON fixtures + skrypt regression** (pure stdlib, bez pytest). Plik `scripts/regression_check.py` uruchamia listę inwokacji, parsuje `--json` output, diff'uje wobec committowanych fixtures w `tests/fixtures/baseline_v1/`. Exit code != 0 przy jakiejkolwiek różnicy. Brak nowych dev dependencies.
- **D-09:** **8 inwokacji** w snapshot suite (z docstringu `sph_sim.py` + baseline):
  1. `python sph_sim.py --strategy naive --zeta 0.5 --seed 42 --json`
  2. `python sph_sim.py --strategy threshold --max_phase 3 --seed 42 --json`
  3. `python sph_sim.py --strategy phase_prob --probs 0.9,0.7,0.5,0.3,0.0 --seed 42 --json`
  4. `python sph_sim.py --strategy incentive --expected_P 100 --seed 42 --json`
  5. `python sph_sim.py --strategy adaptive --s_target 10 --seed 42 --json`
  6. `python sph_sim.py --strategy naive --zeta 0.4 --nU 200 --nSUS 20 --K1 120 --T 1000 --seed 42 --json`
  7. `python sph_sim.py --strategy phase_prob --probs 1.0,0.8,0.6,0.2,0.0 --kappa 0.5 --alpha 0 --seed 42 --json`
  8. `python sph_sim.py --strategy naive --zeta 0.75 --seed 42 --json` (baseline z PROJECT.md: avg_val_last100 ≈ 92)
- **D-10:** Fixtures committowane do `tests/fixtures/baseline_v1/<slug>.json` — autorytatywny baseline, git diff przy każdej zmianie, peer review widzi różnice.
- **D-11:** **PIERWSZY plan/krok Phase 1** = `scripts/generate_baseline.py` uruchamia 8 inwokacji na obecnym monolicie (przed refactorem), zapisuje fixtures, atomic commit "test(01): baseline JSON fixtures from v1.0 monolith". Dopiero w następnych planach zaczynamy faktyczny refactor.

### Module Boundaries
- **D-12:** `sphsim/core/` rozbite na 3 pliki:
  - `core/model.py` — pure functions `valuation(u, K0, K1)`, `sph_stp(u, s, nSUS, K0, K1)`
  - `core/device.py` — `Device` dataclass z polami i `net_profit` property
  - `core/simulator.py` — `SPHSimulator` class (`__init__`, `run`)
- **D-13:** Strategie = plain functions (bez `Protocol` / ABC). Zachowuje sygnaturę v1.0: `def strategy_X(dev, l, s, phi, kappa, rho, h, p) -> str`. Opcjonalny type alias w `sphsim/strategies/__init__.py`: `StrategyFn = Callable[..., str]`. Phase 3 (custom loader) ładuje pliki `.py` z tą samą sygnaturą — żadnego dziedziczenia.
- **D-14:** `sphsim/strategies/__init__.py` zawiera registry:
  ```python
  from sphsim.strategies.naive import strategy_naive
  from sphsim.strategies.threshold import strategy_threshold
  # ...
  STRATEGIES = {
      'naive': strategy_naive,
      'threshold': strategy_threshold,
      # ...
  }
  ```
  Phase 3 doda do tego dict'a runtime'owo przez `STRATEGIES['custom_name'] = loaded_fn`.
- **D-15:** `sphsim/cli/` rozbite na 3 pliki:
  - `cli/args.py` — `parse_args()` + argparse setup
  - `cli/main.py` — orchestration (`parse_args` → build `SPHSimulator` → `run()` → format)
  - `cli/output.py` — `format_human(result)` + `format_json(result)`
  Phase 2 doda `cli/repl.py` obok.
- **D-16:** `sphsim/__init__.py` eksportuje publiczne API:
  ```python
  from sphsim.core.simulator import SPHSimulator
  from sphsim.core.device import Device
  from sphsim.strategies import STRATEGIES
  ```
  Pozwala na `from sphsim import SPHSimulator, STRATEGIES, Device` — przyjazne dla test harness i przyszłych skryptów.

### Claude's Discretion
- Konkretna nazwa pliku defaults (`config.py` vs `defaults.py`) — preferuj `config.py` (bardziej generic, w fazie 5 może rosnąć).
- Format pliku `scripts/regression_check.py` (klasa vs funkcje, kolorowanie diff) — Claude wybiera, byle exit code != 0 przy regresji i czytelny output.
- Nazwy slug'ów dla 8 fixture JSON-ów (`tests/fixtures/baseline_v1/01-naive-zeta-0.5.json` vs `naive_default.json` vs ...) — Claude wybiera spójną konwencję.
- Czy fixture JSON jest pretty-printed (indent=2) czy compact — Claude wybiera; preferuj pretty dla czytelnego git diff.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specification & State
- `PROMPT_DLA_AGENTA.txt` — autorytatywne źródło dla modelu, KPI, baseline'u (parametry NU/NSUS/K0/K1/F/T/κ/α/φ/ρ, definicje KPI, baseline results table)
- `.planning/PROJECT.md` — milestone v1.1 scope, constraints (Python 3.7+, polski w komentarzach, stdlib only w Phase 1), Key Decisions
- `.planning/REQUIREMENTS.md` — REQ CLI-04 (backwards compat) jest jedynym wymaganiem mapowanym do Phase 1
- `.planning/ROADMAP.md` §"Phase 1" — Goal + 4 Success Criteria (numerical regression, ≤150 linii/moduł, sph_sim.py jako entry, JSON identical)
- `.planning/STATE.md` §"Blockers/Concerns" — flaguje Phase 1 jako kluczowy ryzykowny moment (backwards compat, package naming)

### Current Codebase (przed refactorem)
- `sph_sim.py` (433 linie) — pełny monolit do rozbicia. Sekcje wg STRUCTURE.md:
  - lines 39–48: defaults → trafi do `sphsim/config.py`
  - lines 53–79: model functions (`valuation`, `sph_stp`) → `sphsim/core/model.py`
  - lines 84–99: `Device` dataclass → `sphsim/core/device.py`
  - lines 104–157: 5 strategy functions + STRATEGIES dict → `sphsim/strategies/{naive,threshold,phase_prob,incentive,adaptive}.py` + `__init__.py`
  - lines 162–273: `SPHSimulator` class → `sphsim/core/simulator.py`
  - lines 278–303: `parse_args()` → `sphsim/cli/args.py`
  - lines 305–363: `main()` + output formatting → `sphsim/cli/main.py` + `sphsim/cli/output.py`
- `.planning/codebase/STRUCTURE.md` — section map, naming conventions, file locations
- `.planning/codebase/ARCHITECTURE.md` — layer breakdown (Constants/Model/Device/Strategy/Simulator/CLI), data flow, key abstractions

### Verification Reference (po refactorze będą)
- `tests/fixtures/baseline_v1/*.json` — generowane w pierwszym kroku Phase 1, autorytatywny snapshot pre-refactor outputów
- `scripts/regression_check.py` — runner odpalający 8 inwokacji i diff'ujący wobec fixtures

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Cała logika `sph_sim.py`** — refactor mechaniczny, nie przepisywanie. Funkcje, klasy, sygnatury, default'y zostają jeden-do-jednego, zmienia się tylko fizyczne miejsce w plikach.
- **Docstring sph_sim.py (lines 1–27)** — zawiera dokładnie 7 example inwokacji + listę 5 strategii. To źródło dla snapshot suite (D-09).
- **`copilot_gsd_results.txt` + `gsd_copilot_resoning.txt` + `Raport.pdf`** — istnieją w root, zawierają baseline numerical results z v1.0 (avg_val=92 dla `naive --zeta 0.75`). Mogą służyć jako sanity check przy generowaniu fixtures (nie jako źródło prawdy — JSON output jest źródłem).

### Established Patterns
- **Strategy pattern przez registry dict** — `STRATEGIES = {name: fn}` zostaje, tylko fizycznie przeniesione do `strategies/__init__.py`. Phase 3 (custom loader) doda do tego dict'a runtime'owo. NIE zmieniamy na klasy/Protocol.
- **`random.seed(seed)` raz w `SPHSimulator.__init__`** — zapewnia reprodukowalność. Refactor MUSI zachować tę kolejność wywołań `random.*` — jakakolwiek zmiana kolejności (np. inny pattern instancjonowania) może zmienić sekwencję losowań i zepsuć snapshot test. To krytyczny invariant.
- **argparse jako jedyny CLI parser** — Phase 1 nie wprowadza Click/Typer. Po prostu przeniesione 1:1 z `sph_sim.py:278–303` do `sphsim/cli/args.py`.
- **Snake_case w Pythonie + Polish w komentarzach/komunikatach** — zachowane.
- **Python stdlib only** — Phase 1 nie dodaje zależności. `matplotlib` ląduje dopiero w Phase 6.

### Integration Points
- **Punkt wejścia OS**: użytkownik wpisuje `python sph_sim.py [args]` z root. Po refactorze plik `sph_sim.py` ma tylko dispatch — cała logika w pakiecie.
- **Punkt wejścia Pythonowy**: `python -m sphsim [args]` przez `__main__.py`. Drugorzędny path, dla user'ów wolących pakietową konwencję.
- **Punkt wejścia programmatic**: `from sphsim import SPHSimulator, STRATEGIES` — dla test harness, przyszłych skryptów, ewentualnych notebooków.
- **Hook dla Phase 2 (REPL)**: `cli/main.py` musi mieć łatwo wyodrębniony "run simulation" path żeby Phase 2 mógł go wywoływać z REPL command handler bez duplikacji.
- **Hook dla Phase 3 (custom loader)**: `STRATEGIES` dict w `strategies/__init__.py` musi być mutable globalem — custom loader doda klucze runtime'owo.

</code_context>

<specifics>
## Specific Ideas

- **8 inwokacji snapshot suite to konkretna lista z docstringu** (D-09) — nie generujemy własnych, używamy dokładnie tych z `sph_sim.py:11–18` plus baseline `naive --zeta 0.75` z PROJECT.md Key Decisions.
- **"Pierwszy krok Phase 1 = baseline fixtures PRZED refactorem"** (D-11) — krytyczny ordering. Bez tego nie ma punktu odniesienia. Plan 1 musi być właśnie "generate baseline", nie "create package skeleton".
- **`sphsim/` zamiast `sph_sim/`** (D-01) — wybór padł na krótszą nazwę żeby uniknąć kolizji z plikiem `sph_sim.py`. Alternatywa "przenieś sph_sim.py do bin/" została odrzucona — `python sph_sim.py` z root musi działać po refactorze identycznie jak przed (CLI-04 hard requirement).
- **Brak ABC/Protocol dla strategii** (D-13) — funkcje są wystarczające, sygnatura w docstring. Spójne z v1.0 stylem i Phase 3 (custom loader) loading pliku .py z funkcją.

</specifics>

<deferred>
## Deferred Ideas

- **`pyproject.toml` + `pip install -e .`** — deferred do v2.0 jeśli projekt zacznie być dystrybuowany albo używany przez >1 osobę programmatic.
- **`typing.Protocol` dla strategii / type checker integration (mypy)** — deferred. Może być dodane jako odrębne ulepszenie po v1.1, nie zmienia ABI.
- **DeprecationWarning dla starych import paths** — deferred (D-05 zakłada że nikt nie używa programmatic API z monolitu).
- **pytest harness zamiast `scripts/regression_check.py`** — deferred. Jeśli w przyszłości doda się więcej testów (unit testy modeli, property tests strategii), warto zmigrować na pytest. Na Phase 1 wystarczy pure stdlib script.
- **Strategies as classes/composable objects** — deferred bez planu, niezgodne z v1.0 stylem.

</deferred>

---

*Phase: 1-Refactoring foundation*
*Context gathered: 2026-05-25*
