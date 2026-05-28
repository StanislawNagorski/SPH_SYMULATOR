# Phase 6: Report + plots generator — Research

**Researched:** 2026-05-28
**Domain:** Python matplotlib (Agg backend) + Markdown report assembly + filesystem side-effect contract
**Confidence:** HIGH (all claims verified directly from codebase + live runtime probes; one decision point — `--no-report` opt-out — flagged as Claude's Discretion for the discuss step)

---

## Summary

Phase 6 dorzuca **dwie side effects** do każdego pojedynczego (single-run) uruchomienia symulatora:
(1) zapis pliku `report.md` do `./reports/<timestamp>/` z 7 sekcjami w polskim Markdownie i (2) zapis dwóch PNG-ów (`decision_distribution.png` + `kpi_timeseries.png`) wygenerowanych przez `matplotlib` z backendem `Agg`. Cały dodatkowy kod żyje w nowym pakiecie `sphsim/report/` (nie istnieje) i jest wywoływany jednorazowo po `sim.run()` z trzech entrypointów: `sphsim/cli/main.py` (built-in i custom branch, w tym compare), `sphsim/cli/repl.py::do_run`, `sphsim/cli/repl.py::do_compare`.

Większość danych do raportu **już istnieje** w returned dict z `SPHSimulator.run()` — `history` ma 1000 wpisów `val[]`/`providers[]` (PLOT-02 gotowe), `ic_per_phase` zawiera per-phase `commits` i `failures` (połowa danych do PLOT-01), `veto_per_phase` z Phase 4 zawiera VETO counts. **Brakuje jednego elementu:** per-phase ABSTAIN counter. Phase 4 dodało `dev.n_abstain` ale tylko globalnie — nie ma `abstain_phase_stats`. Phase 6 musi to dodać do `Device` + agregację w `simulator.run()`, **analogicznie do `veto_phase_stats` z Phase 4** (zero ryzyka regresu, pattern istniejący 1:1).

Najważniejszy decyzja architektoniczna: **report jest stricte side-effect**, JSON output do stdout pozostaje semantycznie nienaruszony (SC#6). Nowy klucz `report_path` może być dodany do JSON jako opcjonalna ścieżka — kontrolowane przez rozszerzenie `SKIP_KEYS` w `regression_check.py` (precedent z Phase 4 D-67 i Phase 5). Testy muszą się uruchamiać bez śmiecenia w `./reports/` — strategia: **opt-out env var `SPHSIM_NO_REPORT=1`** (NIE flagą CLI, żeby SC#1 literalnie "bez flag" zostało nieskazitelne) + dodatkowo `--no-report` flaga jako Claude's Discretion safety net (planner decyduje po `discuss-phase`).

**Primary recommendation:** Sześć małych zmian — (1) `sphsim/report/__init__.py` + `markdown.py` + `plots.py` (nowy pakiet), (2) `Device.abstain_phase_stats` + `simulator.run()` agregacja `abstain_per_phase`, (3) wywołanie `write_report(...)` jednorazowe po `sim.run()` w `main.py` (single-run + compare) + `repl.py::do_run/do_compare`, (4) banner Polish-language "Raport zapisany do ..." na stderr, (5) `regression_check.py` SKIP_KEYS extension dla `report_path` + `abstain_per_phase`, (6) `tests/test_report.py` (≈12 testów) + `scripts/verify_phase6.sh` exit gate.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Generowanie `report.md` (assembly sekcji + serializacja) | Report (`sphsim/report/markdown.py`) | — | Nowy pakiet; izoluje matplotlib od reszty CLI; reuse `format_config_header` |
| Generowanie 2× PNG (matplotlib Agg) | Report (`sphsim/report/plots.py`) | — | Top-of-file `matplotlib.use('Agg')` — headless backend |
| Tworzenie katalogu `./reports/<ts>/` + ścieżki | Report (`sphsim/report/__init__.py::write_report`) | — | Pojedynczy entry-point, atomowa odpowiedzialność |
| Wywołanie write_report z CLI single-run | CLI main (`sphsim/cli/main.py`) | — | Po `sim.run()`, przed `print(format_human/format_json)` |
| Wywołanie write_report z CLI compare | CLI main (`sphsim/cli/main.py::run_compare`) | — | Po obu `sim.run()`, przed `print(format_compare)` |
| Wywołanie write_report z REPL | REPL (`sphsim/cli/repl.py::do_run`, `do_compare`) | — | Symmetric — tryb interaktywny też produkuje raporty |
| Per-phase ABSTAIN aggregation (PLOT-01 input) | Core simulator (`sphsim/core/device.py` + `simulator.py`) | — | Pattern 1:1 z Phase 4 `veto_phase_stats` (D-64) |
| Opt-out (test / CI safety) | Env-var `SPHSIM_NO_REPORT=1` | optional CLI `--no-report` flag | SC#1 literally "bez flag" — env var jest bezpieczny escape hatch |
| Banner "Raport zapisany do ..." | CLI output / stderr | — | Polski, na stderr (żeby `--json` stdout pozostał czysto JSON-em) |

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REPORT-01 | Każde uruchomienie symulacji generuje plik MD w `./reports/<timestamp>/report.md` | §B.4, §C.7, §D.10 (write_report contract), §G.18 (opt-out) |
| REPORT-02 | Raport zawiera sekcje: konfiguracja środowiska, strategia + parametry, KPI table, rozkład decyzji per faza, porównanie z baseline | §C.8 (sekcje 1-7), §C.9 (baseline source) |
| REPORT-03 | Raport w trybie compare (`--compare-agent`) zawiera tabelę delta KPI | §C.8 sekcja 7, §E.12 (reuse format_compare data) |
| PLOT-01 | `decision_distribution.png` — słupkowy COMMIT/ABSTAIN/VETO per faza | §B.5, §F.13 (brakuje abstain_per_phase — dodać), §H.20 |
| PLOT-02 | `kpi_timeseries.png` — `avg_val` i `avg_providers` per cykl z zaznaczonym last-100 oknem | §B.6, §F.14 (history już istnieje), §H.21 |
| PLOT-03 | Wykresy linkowane z raportu MD przez relatywne ścieżki | §C.8 sekcja 6, §I.23 |
</phase_requirements>

---

## User Constraints (from CONTEXT.md)

> CONTEXT.md dla Phase 6 NIE ISTNIEJE w momencie tej researcha. Sekcja zostanie uzupełniona przez `discuss-phase` lub planner, jeśli pojawią się user-locked decisions. **Wstępne sugestie do discuss-phase:**
>
> - **Locked (z ROADMAP SC):** Output dir = `./reports/<timestamp>/`; ZAWSZE 3 pliki (report.md + 2 PNG); matplotlib jako required dep (PROJECT.md Key Decision); JSON output zachowany (SC#6).
> - **Do potwierdzenia w discuss-phase:**
>   1. Format timestamp: `YYYYMMDD-HHMMSS` (fs-safe na Windows) vs ISO `2026-05-28T06:52:29` (czytelniejszy, ale `:` blokowany na Windows)
>   2. Opt-out mechanism: env var `SPHSIM_NO_REPORT=1` (literalnie "bez flag" — SC#1 czysty) vs flaga `--no-report` (eksplicytna, łatwiejsza do dokumentacji)
>   3. Baseline comparison row (REPORT-02 SC#2): czy ładować z `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` (oracle istniejący, kuratorski) czy regenerować na żywo (kosztowne)
>   4. `report_path` w JSON output: dodać czy ukryć (wpływa na `SKIP_KEYS` w `regression_check.py`)
> - **Deferred do Phase 7:** `batch_aggregate.png` (PLOT-04 jest BATCH territory, NIE Phase 6); persystencja historii; ROADMAP cleanup `./reports/` (rotation policy)

---

## Section A: Existing State of the Code

### A.1 — Czy `sphsim/report/` istnieje?

**NIE.** [VERIFIED: `ls sphsim/` confirmed — package directories są: `agent/`, `cli/`, `core/`, `strategies/` + 2 plików top-level. Brak `report/`.]

ROADMAP Phase 1 wspomniało o module `report/` jako "target" refactoringu, ale w trakcie Phase 1 NIE został utworzony — Phase 1 Plan 02 stworzył tylko `core/`. Phase 6 ma więc czystą tablicę.

**Implication:** Phase 6 wprowadza nowy package `sphsim/report/` z 3 modułami:
- `sphsim/report/__init__.py` — eksport `write_report(...)` (single public entry point)
- `sphsim/report/markdown.py` — assembly funkcje (`render_report`, prywatne `_render_kpi_table`, `_render_decision_table`, etc.)
- `sphsim/report/plots.py` — top-of-file `matplotlib.use('Agg')`, dwie funkcje (`plot_decision_distribution`, `plot_kpi_timeseries`)

### A.2 — Co jest dostępne w returned dict z `sim.run()`?

[VERIFIED — live runtime probe na seed=42, naive zeta=0.75, T=1000:]

```python
result_keys = ['avg_val_last100', 'cum_val_total', 'avg_net_profit',
               'delivery_ratio', 'avg_providers_l100', 'sus_final',
               'ic_per_phase', 'veto_per_phase', 'n_vetoed_total',
               'history', 'devices']
```

**Detalicznie:**

| Klucz | Typ | Kształt / przykład | Phase 6 użycie |
|------|-----|---------------------|----------------|
| `avg_val_last100` | float | `92.0` | Tabela KPI (sekcja 3) |
| `cum_val_total` | float | `92300.0` | Tabela KPI (sekcja 3) |
| `avg_net_profit` | float | `140.7592` | Tabela KPI (sekcja 3) |
| `delivery_ratio` | float | `0.7931` | Tabela KPI (sekcja 3) |
| `avg_providers_l100` | float | `105.03` | Tabela KPI (sekcja 3) |
| `sus_final` | int | `1` | Opcjonalnie w sekcji 3 |
| `ic_per_phase` | dict[int, dict] | klucze 1..4 (NIE 5 — phi[5]=1.0 nigdy COMMIT) | PLOT-01 input dla COMMIT counts (klucz `commits`); tabela rozkładu (sekcja 4) |
| `veto_per_phase` | dict[int, int] | `{}` gdy `--no-agent`; `{1: 12, 2: 45, ...}` gdy agent | PLOT-01 VETO bars; tabela rozkładu (sekcja 4) |
| `n_vetoed_total` | int | `0` lub `>0` | Disclaimer w raporcie ("agent zaweto'wał N COMMIT-ów") |
| `history` | dict[str, list] | każda lista długości T=1000 | PLOT-02 input — `val[]` i `providers[]` (cykl t na X-osi) |
| `devices` | list[Device] | nU=250 obiektów | Nie używane bezpośrednio w Phase 6 (już zagregowane) |

`history` keys (VERIFIED): `['val', 'cum_val', 'profit', 'delivery', 'sus', 'providers']` — wszystkie listy o długości T=1000. PLOT-02 używa `val` + `providers`.

**WAŻNE — luka danych dla PLOT-01:** `ic_per_phase[ph]['commits']` to surowy COMMIT count PRZED veto. `veto_per_phase[ph]` to liczba zaweto'wanych. **`abstain_per_phase` NIE ISTNIEJE.** Phase 4 D-63 dodało `dev.n_abstain` (global counter) ale NIE per-phase. To trzeba dodać. Szczegóły w §F.13.

### A.3 — Aktualne format_human / format_json / format_compare — co już wiemy

[VERIFIED: `sphsim/cli/output.py`]

| Funkcja | Lokalizacja | Phase 6 reuse |
|---------|-------------|---------------|
| `format_config_header(args, K0, K1, phi, rho)` | `output.py:27` | **Reuse 1:1** w sekcji 1 raportu MD (już zwraca walidny MD!) |
| `format_human(args, res, K1, verbose)` | `output.py:123` | NIE używane w raporcie MD (raport ma własną logikę) |
| `format_json(args, res, params, K1)` | `output.py:6` | Może dostać nowy klucz `report_path` (decyzja w discuss) |
| `format_compare(args, comp, K1)` | `output.py:52` | Generuje ASCII tabelę — NIE bezpośrednio MD. Phase 6 ma własny `_render_compare_md_table` |

`format_config_header` (output.py:27-49) zwraca string MD z `## Konfiguracja środowiska` jako H2 i tabelę 9 wierszy (`nU`, `T`, `κ`, `α`, `K0`, `K1`, `φ`, `ρ`, `seed`). Phase 6 wkleja ten string verbatim jako sekcję 1 raportu MD.

### A.4 — Aktualny `format_compare` daje wszystko czego potrzebuje SC#5?

Tak. Phase 4 D-62 zaprojektował dict `comparison` z polami:
```python
{
    'with_agent':    {...full metrics dict bez history/devices...},
    'without_agent': {...},
    'delta':         {kpi: with - without for 5 KPIs},
    'agent_helps':   bool,
}
```

Phase 6 dla compare-mode raportu:
- Sekcja 7 "Porównanie z RationalAgent (compare-agent)" — tabela MD 5 KPI × 3 kolumny (with / without / Δ)
- Werdykt `agent_helps` jako jednolinijkowy disclaimer
- Można też wykorzystać DODATKOWE plotting: PLOT-01 dla `with_agent` (z VETO bars) — to pokazuje rozkład W TRYBIE Z AGENTEM (`without_agent` ma VETO=0 dla wszystkich)

**Decyzja architektoniczna:** Compare mode generuje **JEDEN** raport (`./reports/<ts>/report.md`) zawierający dane z obu run-ów. PNG-i są generowane z `with_agent` results (bo to one mają pełen VETO rozkład). To upraszcza filesystem layout — 3 pliki w katalogu zawsze, niezależnie od trybu.

### A.5 — Baseline comparison row (REPORT-02 SC#2)

**Fixtures istnieją:** [VERIFIED: `ls tests/fixtures/baseline_v1/`]
```
01-naive-zeta-0.5.json
02-threshold-max-phase-3.json
03-phase-prob-default.json
04-incentive-expected-P-100.json
05-adaptive-s-target-10.json
06-naive-zeta-0.4-custom-env.json
07-phase-prob-custom-kappa-alpha.json
08-naive-zeta-0.75-baseline.json   ← KANONICZNY BASELINE
MANIFEST.txt
```

[VERIFIED: `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json`]
```json
{
  "env": {"K1": 120, "T": 1000, "alpha": 1, "kappa": 0.25, "nSUS": 20, "nU": 250},
  "metrics": {
    "avg_val_last100": 92.0,
    "cum_val_total": 92300.0,
    "avg_net_profit": 140.7592,
    "delivery_ratio": 0.7931,
    "avg_providers_l100": 105.03,
    ...
  },
  "strategy": "naive",
  "strategy_params": {"zeta": 0.75, ...}
}
```

**Rekomendacja:** Załaduj baseline staticznie z tego pliku (Path constant). Nie regeneruj — to zwiększyłoby czas każdego report-a 2×. Plik istnieje, jest committed, jest oracle z Phase 1. Disclaimer: jeśli user nadpisał `--phi`/`--rho`/`--K0`/`--valuation` (Phase 5), env nie pasuje do baseline — sekcja powinna dodać komunikat "*Uwaga: baseline obliczony dla domyślnego środowiska v1.0; bieżąca konfiguracja może się różnić.*"

---

## Section B: Matplotlib Integration (PLOT-01, PLOT-02, PLOT-03)

### B.4 — Czy matplotlib jest dostępne?

[VERIFIED runtime check:]
- `matplotlib 3.10.7` zainstalowany w `/opt/homebrew/lib/python3.14/site-packages/matplotlib/`
- Python 3.14.3 (deweloperska maszyna)
- `slopcheck install matplotlib` → `[OK]` na PyPI (zaufany pakiet, miliony pobrań, długa historia)
- PROJECT.md Key Decision: "Wizualizacja: `matplotlib` jako required dep, PNG zawsze (bez flagi `--plot`)" — Phase 6 to operacjonalizuje

**Brak `pyproject.toml` ani `requirements.txt`** w repo. PROJECT.md mówi "Python 3.7+ — kontynuacja stacku v1.0; jedyna nowa zależność: `matplotlib` (wymagana, nie opcjonalna)". To znaczy, że Phase 6 jest pierwszą fazą która FAKTYCZNIE wymaga matplotlib — wcześniejsze fazy żyły w stdlib only.

**Decyzja:** Phase 6 NIE wprowadza `requirements.txt` ani `pyproject.toml` (out of scope — istniejący tryb to "kontynuacja stacku" without packaging files). Plan może DODAĆ `requirements.txt` z jedną linią `matplotlib>=3.5` jako opcjonalny artefakt dla użytkowników CI. Decyzja do discuss-phase.

### B.5 — Plot 1: `decision_distribution.png` — design

**Data:** dla każdej fazy `1..4` (faza 5 nigdy nie COMMIT, więc pomijamy lub dodajemy z 0):

```
COMMIT_p  = ic_per_phase[p]['commits']            # commits = strategy zwróciła COMMIT (PRZED veto)
                                                   # ALE: jeśli strategy COMMIT → veto, NIE inkrementuje commits
                                                   # więc commits = COMMITs które przeszły do simulator
VETO_p    = veto_per_phase.get(p, 0)              # COMMIT-y odrzucone przez agenta
ABSTAIN_p = abstain_per_phase.get(p, 0)           # NOWE — Phase 6 musi dodać (§F.13)
```

**WAŻNE — semantyka `ic_per_phase['commits']`:** [VERIFIED: `simulator.py:53` `dev.n_commit += 1` w branch `if decision == 'COMMIT'`]. Czyli `commits` to liczba COMMIT-ów które rzeczywiście dotarły do simulatora i zostały wykonane (sukces lub fail). To **NIE są** rekomendacje strategii — to są wykonane COMMITs. To korzystna semantyka — `ic_per_phase['commits']` to "successful pass-through" wartość.

Trzy stosy słupkowe — grouped bar chart (3 grupy: COMMIT/ABSTAIN/VETO) × 4-5 faz na osi X.

**Pseudocode:**
```python
import matplotlib
matplotlib.use('Agg')  # headless backend — MUST be before pyplot import
import matplotlib.pyplot as plt
import numpy as np

def plot_decision_distribution(ic_per_phase, veto_per_phase, abstain_per_phase, path):
    """Generuje wykres słupkowy COMMIT/ABSTAIN/VETO per faza 1..F-1.

    Args:
        ic_per_phase: dict[int, dict] — z sim.run()['ic_per_phase']; klucz 'commits'.
        veto_per_phase: dict[int, int] — z sim.run()['veto_per_phase'].
        abstain_per_phase: dict[int, int] — NOWE z Phase 6.
        path: Path do PNG.
    """
    phases = sorted(set(list(ic_per_phase.keys()) + list(veto_per_phase.keys()) + list(abstain_per_phase.keys())))
    commits  = [ic_per_phase.get(p, {}).get('commits', 0) for p in phases]
    abstains = [abstain_per_phase.get(p, 0) for p in phases]
    vetos    = [veto_per_phase.get(p, 0) for p in phases]

    x = np.arange(len(phases))
    w = 0.27
    fig, ax = plt.subplots(figsize=(8, 5), dpi=120)
    ax.bar(x - w, commits,  w, label='COMMIT',  color='#2E7D32')   # zielony
    ax.bar(x,     abstains, w, label='ABSTAIN', color='#757575')   # szary
    ax.bar(x + w, vetos,    w, label='VETO',    color='#C62828')   # czerwony
    ax.set_xlabel('Faza urządzenia')
    ax.set_ylabel('Liczba decyzji (T={} cykli)'.format(...))
    ax.set_title('Rozkład decyzji per faza')
    ax.set_xticks(x)
    ax.set_xticklabels([f'Faza {p}' for p in phases])
    ax.legend(loc='upper right')
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)  # MUST — bez tego matplotlib trzyma figures w pamięci
```

### B.6 — Plot 2: `kpi_timeseries.png` — design

**Data:** `history['val']` i `history['providers']` (oba długości T=1000). [VERIFIED: live probe pokazał `len(history['val']) == 1000`, sample wartości `[100.0, 100.0, 100.0, 0.0, 100.0]`.]

Dwa wykresy linowe na jednej figurze, dwie osie Y (twin axes — lewa dla `val`, prawa dla `providers`). Pionowa linia/shaded region zaznaczający ostatnie 100 cykli (`T-100` do `T-1`).

**Pseudocode:**
```python
def plot_kpi_timeseries(history, T, path):
    """Wykres avg_val i avg_providers per cykl z zaznaczonym oknem last-100.

    Args:
        history: dict z sim.run()['history']; wymaga kluczy 'val', 'providers'.
        T: liczba cykli (z args.T).
        path: Path do PNG.
    """
    cycles = list(range(1, T + 1))
    val = history['val']
    providers = history['providers']

    fig, ax1 = plt.subplots(figsize=(10, 5), dpi=120)
    color_val = '#1565C0'   # niebieski
    ax1.set_xlabel('Cykl symulacji')
    ax1.set_ylabel('avg_val (waluacja Konsumentów)', color=color_val)
    ax1.plot(cycles, val, color=color_val, linewidth=0.8, alpha=0.85, label='avg_val')
    ax1.tick_params(axis='y', labelcolor=color_val)

    ax2 = ax1.twinx()
    color_prov = '#EF6C00'  # pomarańczowy
    ax2.set_ylabel('avg_providers (liczba dostawców)', color=color_prov)
    ax2.plot(cycles, providers, color=color_prov, linewidth=0.8, alpha=0.85, label='avg_providers')
    ax2.tick_params(axis='y', labelcolor=color_prov)

    # Last-100 window — shaded grey
    last100_start = max(1, T - 99)
    ax1.axvspan(last100_start, T, alpha=0.15, color='grey', label='Ostatnie 100 cykli')

    fig.suptitle('Przebieg KPI w czasie symulacji')
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
```

### B.7 — Backend Agg (headless safety)

[VERIFIED: `matplotlib.use('Agg')` zmienia backend na `Agg` (raster only, no GUI). Test passed: PNG 4224 bajtów wygenerowany OK.]

**Krytyczne:** `matplotlib.use('Agg')` MUSI być wywołane **PRZED** `import matplotlib.pyplot`. To ogranicza wybór architektury:

```python
# sphsim/report/plots.py — top of file:
import matplotlib
matplotlib.use('Agg')          # MUST be first matplotlib call
import matplotlib.pyplot as plt
```

Powód: bez `Agg`, na macOS matplotlib defaultuje do `MacOSX` backend, który próbuje otworzyć GUI okno — niedopuszczalne w CI/SSH/Linux headless. `Agg` nigdy nie wywołuje X11/Cocoa.

### B.8 — Polish glyphs w matplotlib

[VERIFIED: live test — `ax.set_title('Rozkład decyzji ąęłńóśźż')` + savefig OK, brak FontWarning.]

Default sans-serif font matplotlib: `DejaVu Sans` — pełna obsługa polskich znaków. Brak konieczności konfiguracji `font.family` ani manualnego ładowania TTF.

**Caveat:** Inne maszyny (Linux minimal) mogą mieć inny default. Jako safety, dodać explicit `plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'sans-serif']` — graceful fallback.

### B.9 — Styling defaults

Rekomendacje:
- `figsize=(8, 5)` dla decision_distribution, `(10, 5)` dla timeseries
- `dpi=120` — retina-friendly bez balansowania na 300 DPI (zbyt duże pliki)
- Color palette explicitly w hex (`#2E7D32`, `#757575`, `#C62828`, `#1565C0`, `#EF6C00`) — deterministyczna semantyka (zielony=akcja, szary=neutralność, czerwony=odrzucenie), reproducible cross-platform
- `linewidth=0.8` dla timeseries — 1000 punktów na X-osi, cieńsza linia czytelniejsza
- `alpha=0.85` na liniach — soft, profesjonalna estetyka
- `grid(linestyle='--', alpha=0.4)` na osi Y — pomaga porównać wartości

---

## Section C: Markdown Report Layout (REPORT-01/02/03)

### C.7 — Output directory contract

**SC#1 wymaga:** `./reports/<timestamp>/` z 3 plikami.

**Timestamp format — rekomendacja:** `%Y%m%d-%H%M%S` (np. `20260528-065229`). [VERIFIED runtime: `datetime.now().strftime('%Y%m%d-%H%M%S')` daje `20260528-065229`.]

Powody:
- Filesystem-safe na Windows, Linux, macOS (brak `:` znaku — ISO 8601 zawiera `:` i się wywala na NTFS)
- Sortowalny leksykograficznie = sortowalny chronologicznie
- Krótki (15 znaków) — łatwy do copy-paste
- Brak ambiguity ze strefą czasową (zawsze lokalna)

**Path resolution:** `./reports/<ts>/` względem `cwd` w momencie uruchomienia. `cwd` = project root w 99% przypadków (user uruchamia `python sph_sim.py ...`), ale dla bezpieczeństwa rozwiązać przez `Path('reports') / ts` (relatywna do CWD, NIE do `__file__` lokalizacji).

**`.gitignore` impact:** [VERIFIED: `.gitignore` zawiera `__pycache__/, *.pyc, *.pyo, *.pyd, .DS_Store, Thumbs.db, *.swp, *.swo`. **NIE** zawiera `reports/`.] Phase 6 plan MUSI dodać linijkę `reports/` do `.gitignore` — inaczej każdy report wskoczy do `git status` i będzie wycieczał historię.

**Edge cases:**
- Concurrent runs (2× `python sph_sim.py` w tej samej sekundzie) → kolizja katalogów. Rozwiązanie: jeśli `reports/<ts>/` już istnieje, dodaj suffiks `-N` (`20260528-065229-2`). Zero ryzyka data loss.
- Read-only filesystem (rare) → `mkdir` rzuca `PermissionError`. Plan: catch, log Polish warning na stderr ("Nie udało się utworzyć katalogu raportu: <reason>. Raport pominięty."), kontynuuj symulację normalnie (NIE crash).

### C.8 — Sekcje raportu (REPORT-02 SC#2)

Plan 7 sekcji w `report.md`:

```markdown
# Raport symulacji SPH — <strategia> (<timestamp>)

## 1. Konfiguracja środowiska
<format_config_header verbatim — 9 wierszy MD table>

## 2. Strategia i parametry
| Parametr | Wartość |
|----------|---------|
| Strategia | <args.strategy> |
| <param1>  | <value1> |
| ...       | ...     |
**Tryb agenta:** <Włączony / Wyłączony (--no-agent) / Tryb porównawczy (--compare-agent)>

## 3. Metryki KPI

| KPI | Wartość | Cel |
|-----|---------|-----|
| avg_val_last100      | 92.00     | MAX → 100   |
| cum_val_total        | 92300.0   | MAX → 100000 |
| avg_net_profit       | +140.7592 | > 0 |
| delivery_ratio       | 79.31%    | wysoki |
| avg_providers_l100   | 105.03    | ≈ 100..120 |

## 4. Rozkład decyzji per faza

| Faza | COMMIT | ABSTAIN | VETO | Suma |
|------|--------|---------|------|------|
| 1    | 53968  | 12000   | 12   | ...  |
| 2    | 36514  | ...     | ...  | ...  |
| ...  | ...    | ...     | ...  | ...  |

![Rozkład decyzji](decision_distribution.png)

## 5. Przebieg KPI w czasie

![Przebieg KPI](kpi_timeseries.png)

## 6. Porównanie z baseline (`naive --zeta 0.75 --no-agent`)

| KPI | Bieżący run | Baseline v1.0 | Δ |
|-----|-------------|---------------|---|
| avg_val_last100 | 92.00 | 92.00 | +0.00 |
| ...             | ...   | ...   | ... |

*Baseline z `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json`. Uwaga: jeśli używasz override `--phi`/`--rho`/`--K0`/`--valuation`/`--T`/`--nU`, środowisko może się różnić od baseline.*

## 7. (Conditional, tylko `--compare-agent`) Porównanie z/bez RationalAgent

| KPI | with-agent | bez agenta | Δ (with - bez) |
|-----|------------|------------|----------------|
| avg_val_last100  | 92.00  | 85.30 | +6.70   |
| ...              | ...    | ...   | ...     |

**Werdykt:** Agent zaweto'wał N COMMIT-ów. with-agent bije without-agent: ✓ TAK / ✗ NIE.
```

Wszystkie nagłówki sekcji w polskim — spójne z PROJECT.md "polski w komentarzach, komunikatach CLI i raporcie".

### C.9 — Baseline source — load static fixture

```python
# sphsim/report/markdown.py
from pathlib import Path
import json

BASELINE_PATH = Path(__file__).resolve().parent.parent.parent / 'tests' / 'fixtures' / 'baseline_v1' / '08-naive-zeta-0.75-baseline.json'

def load_baseline():
    """Zwraca dict z baseline metrics dla naive --zeta 0.75. Może rzucić FileNotFoundError."""
    return json.loads(BASELINE_PATH.read_text(encoding='utf-8'))
```

Plan: jeśli `BASELINE_PATH` nie istnieje (rare — fixtures są committed), sekcja 6 jest pominięta z disclaimerem "Baseline niedostępny — pominięto sekcję porównania." Nie blokuje wygenerowania raportu.

### C.10 — `report.md` size estimate

7 sekcji × ~10 linii + 2 obrazki referencji + 2 long tables (≈30 lines) → łącznie ≈100 linii MD ≈ 4-6 KB. Trywialne dla disk I/O i git. PNG-i (2 × ~50 KB at dpi=120) → łącznie ~100 KB per uruchomienie. Pojedynczy run zajmie ≈ 110 KB.

---

## Section D: write_report API

### D.11 — Single public entry point

```python
# sphsim/report/__init__.py
from pathlib import Path
from datetime import datetime
import os

from sphsim.report.markdown import render_report
from sphsim.report.plots import plot_decision_distribution, plot_kpi_timeseries


def write_report(args, res, params, K1, *, mode='single') -> Path | None:
    """Zapisuje pełen raport (MD + 2 PNG) do ./reports/<timestamp>/.

    Args:
        args:    argparse.Namespace (potrzebne pola: nU, nSUS, T, kappa, alpha,
                 K0, K1, phi, rho, seed, valuation, strategy, no_agent, json).
        res:     dict z SPHSimulator.run() (single mode) lub dict z
                 'comparison' kluczem (compare mode).
        params:  dict parametrów strategii.
        K1:      resolved K1 (może być float('inf')).
        mode:    'single' | 'compare' — wpływa na obecność sekcji 7
                 + źródło danych dla PNG (compare uses with_agent metrics).

    Returns:
        Path do utworzonego katalogu raportu, lub None gdy raport pominięty
        (env SPHSIM_NO_REPORT=1 lub mkdir fail).

    Side effects:
        - Tworzy katalog ./reports/<timestamp>/ (mkdir parents=True)
        - Zapisuje 3 pliki: report.md, decision_distribution.png, kpi_timeseries.png

    Raises:
        Nothing — wszystkie wyjątki łapane i logowane na stderr.
    """
    if os.environ.get('SPHSIM_NO_REPORT'):
        return None
    # ... reszta logiki ...
```

Zwracany `Path` jest używany przez caller do:
- Wypisania banner "Raport zapisany do: <path>/report.md" na stderr (po polsku)
- Opcjonalnego dodania klucza `report_path` do JSON output (decyzja w discuss-phase)

### D.12 — Wywołanie z `main.py` i `repl.py`

**Single-run w `main.py` (built-in branch + custom branch):**
```python
# Po sim.run() (main.py:101 i analog w custom branch:101):
sim = SPHSimulator(...)
res = sim.run()

# NOWE — Phase 6:
from sphsim.report import write_report
report_dir = write_report(args, res, params, K1, mode='single')
if report_dir:
    print(f"Raport zapisany do: {report_dir}/report.md", file=sys.stderr)

# Istniejące — output bez zmian:
if args.json:
    print(format_json(args, res, params, K1))
else:
    print(format_human(args, res, K1, args.verbose))
```

**Compare w `main.py::run_compare`:**
```python
# Po obu sim.run():
res = run_compare(args, raw_strategy_fn, name, params, K1)

# NOWE — Phase 6:
report_dir = write_report(args, res, params, K1, mode='compare')
if report_dir:
    print(f"Raport zapisany do: {report_dir}/report.md", file=sys.stderr)

print(format_json(args, res, params, K1) if args.json else format_human(args, res, K1, args.verbose))
```

**REPL `do_run` (`repl.py:215`):** Po `res = sim.run()`, identyczna logika jak w main. `fake_args` MUSI zostać rozszerzone o nowe pola jeśli write_report ich potrzebuje. (Phase 5 już dodała `phi`, `rho`, `K0`, `valuation` do `fake_args` — wystarczające).

**REPL `do_compare` (`repl.py:282`):** Po obu `sim.run()`, identyczna logika. `res_combined = {'comparison': ...}` przekazane do `write_report(mode='compare')`.

### D.13 — Stderr banner — polski

Banner po polsku, na stderr, NIE na stdout (żeby `--json` stdout pozostał czysty):
```
Raport zapisany do: reports/20260528-065229/report.md
```

Dla compare mode:
```
Raport porównawczy (with/without agent) zapisany do: reports/20260528-065229/report.md
```

Brak ANSI colors (spójne z Phase 2 D-22 — prompt bez ANSI).

---

## Section E: REPL Integration

### E.14 — Czy `do_run` REPL używa tej samej code path co CLI?

[VERIFIED: `sphsim/cli/repl.py:209-226`] — REPL `do_run` buduje SPHSimulator BEZPOŚREDNIO (nie przez `sphsim/cli/main.py::main`). Ma własny `fake_args` Namespace. Phase 5 Pitfall 2 (D-23 fix) pokazał, że `fake_args` musi mieć wszystkie pola których oczekuje `format_human` / `format_config_header`.

**Implication dla Phase 6:** `write_report(args, ...)` czyta wiele atrybutów z `args`. Trzeba potwierdzić że `fake_args` REPL-a (zarówno w `do_run` jak i `do_compare`) ma wszystkie pola. Lista pól wymaganych przez `write_report`:
- `strategy` (już jest)
- `nU, nSUS, T, kappa, alpha, K0, phi, rho, seed, valuation` (już jest po Phase 5)
- `no_agent, json` (już jest — w Phase 4 dodane)

`fake_args` w Phase 5 D-23 fix (`repl.py:219-225`) ma wszystkie potrzebne pola. **Brak nowych zmian w `fake_args` na Phase 6.**

### E.15 — Czy `do_compare` używa tej samej code path?

[VERIFIED: `sphsim/cli/repl.py:282-294`] — `do_compare` REPL też buduje SPHSimulator BEZPOŚREDNIO (dwa razy, raz z agentem, raz bez), nie przez `run_compare` z main.py. Buduje własny `comparison_block` dict i `res_combined = {'comparison': comparison_block}`. Format wynikowy jest IDENTYCZNY ze strukturą z main.py `run_compare`.

**Implication dla Phase 6:** `write_report(args, res_combined, params, K1, mode='compare')` zadziała tak samo dobrze z REPL `do_compare` jak z CLI `run_compare`. Pojedynczy contract.

### E.16 — Wbudowanie wywołania write_report

```python
# repl.py do_run, po res = sim.run():
from sphsim.report import write_report
import sys
report_dir = write_report(fake_args, res, params, DEFAULT_K1, mode='single')
if report_dir:
    print(f"Raport zapisany do: {report_dir}/report.md", file=sys.stderr)
print(format_human(fake_args, res, DEFAULT_K1, False))

# repl.py do_compare, po res_combined budowy:
report_dir = write_report(fake_args, res_combined, params, DEFAULT_K1, mode='compare')
if report_dir:
    print(f"Raport zapisany do: {report_dir}/report.md", file=sys.stderr)
print(format_human(fake_args, res_combined, DEFAULT_K1, False))
```

3 nowe linie na entry-point × 4 entrypoints (main built-in, main custom, main compare, repl do_run, repl do_compare) = ~15 nowych linii kodu we wszystkich entrypointach. Trywialne.

---

## Section F: Data Gaps — co trzeba dodać

### F.13 — `abstain_per_phase` — NOWY counter (PLOT-01 input)

**Problem:** PLOT-01 wymaga COMMIT/ABSTAIN/VETO per faza. Mamy:
- COMMIT per faza: `ic_per_phase[ph]['commits']` ✓
- VETO per faza: `veto_per_phase[ph]` ✓ (Phase 4 D-64)
- **ABSTAIN per faza: BRAK.** `dev.n_abstain` jest globalny, NIE per-phase.

**Rozwiązanie — pattern 1:1 z Phase 4 D-64:**

1. `sphsim/core/device.py` — dodać `abstain_phase_stats = {}` w `__post_init__` (paralelnie do `veto_phase_stats`):

```python
def __post_init__(self):
    self.phase_stats = {}
    self.veto_phase_stats = {}     # Phase 4 D-64
    self.abstain_phase_stats = {}  # Phase 6 PLOT-01
```

2. `sphsim/core/simulator.py` — inkrementacja w branch ABSTAIN (`simulator.py:75-78`):

```python
else:  # 'ABSTAIN' lub nieznany decision — failsafe (T-04-04)
    dev.n_abstain += 1
    dev.abstain_phase_stats[dev.phase] = dev.abstain_phase_stats.get(dev.phase, 0) + 1
    dev.status = 'DOWN'
    dev.down_left = 1
```

3. `sphsim/core/simulator.py` — agregacja w `run()` (po veto_per_phase agregacji, linia ~155):

```python
abstain_per_phase = {}
for dev in self.devices:
    for ph, count in dev.abstain_phase_stats.items():
        abstain_per_phase[ph] = abstain_per_phase.get(ph, 0) + count
```

4. Returned dict — dodać `'abstain_per_phase': abstain_per_phase`.

**Pattern paralelizmu Phase 4:** Klucz `abstain_per_phase` powinien być DODANY do `SKIP_KEYS` w `regression_check.py` (paralelnie do Phase 4 D-67 i Phase 5 D-PH5).

**Pitfall:** ABSTAIN counter NIE inkrementuje się przy VETO (`simulator.py:70-74` ma separate branch `elif decision == 'VETO'`). To poprawne (D-65). Jeśli zmiana w simulatorze coś popsuje, regression check złapie (8 fixtures).

### F.14 — `history` dimensions — VERIFIED

[VERIFIED live probe:]
- `len(history['val']) == 1000` (T=1000 default)
- `len(history['providers']) == 1000`
- Każda lista ma długość `T` (zmienia się gdy user podaje `--T`)

PLOT-02 dostaje gotowe dane. Zero nowych zmian w simulatorze dla timeseries.

### F.15 — Wszystko inne jest gotowe

`ic_per_phase`, `veto_per_phase`, `n_vetoed_total`, KPI metrics, `comparison.delta`, `comparison.agent_helps` — wszystko z Phases 1-5.

---

## Section G: Compatibility / Regression / Test Pollution

### G.16 — JSON output po Phase 6 (SC#6)

**Aktualne wyjście** (Phase 5):
```json
{
  "strategy": "naive",
  "strategy_params": {...},
  "env": {"nU": 250, ..., "valuation": "window"},
  "metrics": {"avg_val_last100": 92.0, ..., "agent_enabled": true}
}
```

**Phase 6 może dodać:**
- `"abstain_per_phase": {1: N, 2: N, ...}` do `metrics` (consequence of F.13)
- Opcjonalnie: `"report_path": "reports/20260528-065229"` na top-level (claude's discretion)

**Decyzja:** `abstain_per_phase` MUSI być w JSON (data gap fill). `report_path` — opcjonalnie. Discuss decyduje.

### G.17 — `regression_check.py` SKIP_KEYS extension

[VERIFIED: `scripts/regression_check.py:45-48`]
```python
SKIP_KEYS = (
    'veto_per_phase', 'n_vetoed_total', 'agent_enabled',  # Phase 4 D-67
    'K0', 'phi', 'rho', 'seed', 'valuation',              # Phase 5 D-PH5
)
```

Phase 6 dodaje:
```python
SKIP_KEYS = (
    'veto_per_phase', 'n_vetoed_total', 'agent_enabled',  # Phase 4 D-67
    'K0', 'phi', 'rho', 'seed', 'valuation',              # Phase 5 D-PH5
    'abstain_per_phase', 'report_path',                   # Phase 6 D-PH6
)
```

**Side note:** Phase 6 NIE potrzebuje touch'ować INVOCATIONS (8 baseline runs) ani fixtures. Pattern 1:1 z Phase 4 i 5.

### G.18 — Test pollution + opt-out mechanism

**Problem:** Testy uruchamiają `sph_sim.py` 100+ razy podczas test discover (test_loader, test_agent, test_env, ...). Każde uruchomienie zapisze 3 pliki do `./reports/<ts>/`. Po 100 testach mamy 100 katalogów × 3 pliki = 300 plików w `reports/`. To zaśmieca filesystem, spowalnia I/O (mkdir + 3 writes), psuje `git status`.

**Rozwiązanie 1 — Env var (PREFEROWANE):**
```python
# sphsim/report/__init__.py
def write_report(args, res, params, K1, *, mode='single'):
    if os.environ.get('SPHSIM_NO_REPORT'):
        return None
    ...
```

W testach:
```python
# tests/conftest.py (nowy) lub w każdym test file:
os.environ['SPHSIM_NO_REPORT'] = '1'
```

I w `scripts/regression_check.py`:
```python
def run_invocation(args):
    env = {**os.environ, 'SPHSIM_NO_REPORT': '1'}
    full_args = [sys.executable, str(MONOLITH), *args, '--no-agent', '--seed', '42', '--json']
    result = subprocess.run(full_args, env=env, ...)
```

**Plus dla testów które chcą RZECZYWIŚCIE testować raport** (np. `tests/test_report.py`): używać `tmp_path` (built-in pytest/unittest fixture) i monkeypatching `Path.cwd()`. Phase 6 plan musi to zaadresować.

**Rozwiązanie 2 — Flaga `--no-report` (BACKUP):**
Dodać `p.add_argument('--no-report', action='store_true')`. Discuss-phase decyduje czy też dodać do CLI, czy zostawić tylko env-var.

**Argument za env-var only:** SC#1 literalnie "bez żadnych flag, zawsze" — flaga CLI mogłaby zostać zinterpretowana jako naruszenie SC#1. Env var jest "out-of-band" — nie pojawia się w `--help`, użytkownicy nie widzą, ale CI i testy go używają.

### G.19 — Regression check + report side effects

`regression_check.py` używa `subprocess.run(...)` z `env={**os.environ, 'SPHSIM_NO_REPORT': '1'}`. Cała procedura regression nie tworzy żadnych raportów → fixtures `tests/fixtures/baseline_v1/*.json` pozostają oracle dla TYLKO JSON output. Backwards compat zachowany.

---

## Section H: Validation Architecture

> `workflow.nyquist_validation` jest absent z `.planning/config.json` — treated as **enabled**.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python `unittest` (stdlib, zgodnie z Phases 1-5) |
| Config file | brak — testy odpalane przez `python -m unittest discover tests/` |
| Quick run command | `python -m unittest tests/test_report.py -v` (nowy plik) |
| Full suite command | `python -m unittest discover tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REPORT-01 | Pojedyncze uruchomienie tworzy `./reports/<ts>/report.md` + 2 PNG | integration | `python -m unittest tests.test_report.TestReportFiles -v` | ❌ Wave 0 |
| REPORT-01 | env var `SPHSIM_NO_REPORT=1` powstrzymuje generowanie | unit | same | ❌ Wave 0 |
| REPORT-01 | mkdir collision dodaje suffiks `-N` | unit | same | ❌ Wave 0 |
| REPORT-02 | `report.md` zawiera 6 nagłówków sekcji (Konfiguracja środowiska, Strategia, Metryki KPI, Rozkład decyzji, Przebieg KPI, Porównanie z baseline) | integration | `python -m unittest tests.test_report.TestReportSections -v` | ❌ Wave 0 |
| REPORT-02 | Tabela KPI zawiera 5 nazwanych wierszy | unit | same | ❌ Wave 0 |
| REPORT-02 | Baseline comparison row jest obecny dla domyślnego env | integration | same | ❌ Wave 0 |
| REPORT-03 | Compare mode (`--compare-agent`) dodaje sekcję 7 z delta KPI | integration | `python -m unittest tests.test_report.TestReportCompareMode -v` | ❌ Wave 0 |
| PLOT-01 | `decision_distribution.png` istnieje + non-zero size | integration | `python -m unittest tests.test_report.TestPlots -v` | ❌ Wave 0 |
| PLOT-01 | abstain_per_phase aggregation correct (12-phase scenario) | unit | `python -m unittest tests.test_simulator_abstain -v` | ❌ Wave 0 |
| PLOT-02 | `kpi_timeseries.png` istnieje + non-zero size | integration | same | ❌ Wave 0 |
| PLOT-02 | history T=1000 nie jest truncated w PNG | unit | same (smoke check via Pillow PNG dimensions) | ❌ Wave 0 |
| PLOT-03 | `report.md` zawiera relatywne MD image links: `![...](decision_distribution.png)` | unit | `python -m unittest tests.test_report.TestPlotLinks -v` | ❌ Wave 0 |
| regression | All 8 baseline invocations still PASS (SKIP_KEYS extended for abstain_per_phase, report_path) | integration | `SPHSIM_NO_REPORT=1 python scripts/regression_check.py` | ✅ exists (extend) |
| SC#6 | `--json` output stdout nadal parsuje się jako JSON (no banner contamination) | unit | `python -c "import json,subprocess; r=subprocess.run([sys.executable,'sph_sim.py','--strategy','naive','--zeta','0.5','--no-agent','--seed','42','--json'],env={**os.environ,'SPHSIM_NO_REPORT':'1'},capture_output=True,text=True); json.loads(r.stdout)"` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m unittest tests/test_report.py tests/test_simulator_abstain.py -v` (≈3 s)
- **Per wave merge:** `python -m unittest discover tests/ -v` + `SPHSIM_NO_REPORT=1 python scripts/regression_check.py`
- **Phase gate:** Full suite green + regression PASS=8/8 + `scripts/verify_phase6.sh` PASS≥20 / FAIL=0 przed `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_report.py` — covers REPORT-01, REPORT-02, REPORT-03, PLOT-01, PLOT-02, PLOT-03 (≈12 cases)
- [ ] `tests/test_simulator_abstain.py` — covers `abstain_per_phase` aggregation (F.13 data gap fix; ≈3 cases)
- [ ] `tests/conftest.py` — `os.environ['SPHSIM_NO_REPORT'] = '1'` jako session-scoped fixture (lub equivalent unittest setUp)
- [ ] Framework install: brak — unittest jest stdlib; matplotlib już zainstalowany lokalnie. CI: `pip install matplotlib` MOŻE być wymagany — discuss-phase decyduje.

---

## Section I: Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Markdown table formatting | Jinja2 template engine, MarkdownIt | f-string MD tables w `render_report` | Stdlib only constraint; pattern matches `format_config_header` z Phase 5 |
| PNG generation | PIL/Pillow direct drawing | `matplotlib` (already required dep per PROJECT.md) | matplotlib zaprojektowany do tego; PROJECT.md decision już zapadła |
| Timestamp formatting | `time.time()` + manual conversion | `datetime.now().strftime('%Y%m%d-%H%M%S')` | Stdlib, ergonomiczne, cross-platform |
| Directory creation z collision handling | Mutex/lock plików | `Path.mkdir(parents=True, exist_ok=False)` + simple `-N` suffiks retry loop | Stdlib, simple, deterministic |
| MD-to-image link generation | `markdownify` lub HTML render then convert | Pojedynczy f-string `![alt](filename.png)` | Płaska struktura katalogu — link relatywny zawsze działa |
| Baseline data loading | Re-run simulation | Static JSON fixture (`tests/fixtures/baseline_v1/08-...json`) | Phase 1 D-08/D-11 contract — fixtures są oracle |
| Compare-mode delta table | Re-render `format_compare` ASCII | Dedicated `_render_compare_md_table` w `markdown.py` | ASCII tabela z `format_compare` nie jest poprawnym MD — trzeba osobnego renderera |

**Key insight:** matplotlib jest jedyną nową zależnością. Wszystkie inne potrzeby pokrywa stdlib + już istniejące fixtures + już istniejące funkcje (`format_config_header`).

---

## Section J: Common Pitfalls

### Pitfall 1: Matplotlib GUI backend na macOS / SSH

**Co idzie nie tak:** Bez `matplotlib.use('Agg')` przed `import pyplot`, na macOS matplotlib defaultuje do `MacOSX` backend i próbuje otworzyć GUI okno. W headless / SSH / CI → crash z `RuntimeError: Cannot connect to display`.

**Dlaczego się dzieje:** `matplotlib.use()` musi być wywołane PRZED `import matplotlib.pyplot`. Jeśli inny moduł zaimportował pyplot wcześniej (np. test infrastructure), `use('Agg')` nie ma efektu.

**Jak uniknąć:** W `sphsim/report/plots.py` na pierwszej linii:
```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
```
Zero `pyplot` imports gdziekolwiek wcześniej w codebase. Verified `grep -rn "matplotlib\|pyplot" sphsim/ tests/` zwrócił 0 wyników — czysta tablica.

**Warning signs:** CI failure z stacktrace `tkinter.TclError` lub `RuntimeError: cannot use display`. Test lokalny działa, CI nie.

### Pitfall 2: PNG file open in browser/viewer locks file on Windows

**Co idzie nie tak:** Użytkownik otwiera `reports/<ts>/decision_distribution.png` w Windows Photo Viewer. Re-run symulacji próbuje nadpisać. `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process.`

**Dlaczego się dzieje:** Windows trzyma file lock dopóki viewer trzyma file open.

**Jak uniknąć:** Każdy run dostaje **nowy katalog** `<ts>/`. Phase 6 NIE nadpisuje istniejących plików. Plus collision handler dodaje `-N` suffiks gdy `<ts>/` już istnieje. Zero ryzyka PermissionError.

**Warning signs:** N/A — by design unikamy.

### Pitfall 3: `--json` stdout corrupted by report banner

**Co idzie nie tak:** Jeśli "Raport zapisany do: ..." print pójdzie na stdout, `--json` mode wyrzuca: `Raport zapisany do: ...\n{"strategy": "naive", ...}`. Caller parsuje `json.loads(stdout)` → JSONDecodeError.

**Dlaczego się dzieje:** `print(...)` defaultuje do stdout. JSON output mode oczekuje że stdout to TYLKO valid JSON.

**Jak uniknąć:** `print(banner, file=sys.stderr)` — banner zawsze na stderr, niezależnie od `--json`. Tylko `format_json(...)` idzie na stdout.

**Warning signs:** `regression_check.py` exit 2 z "stdout nie jest JSON: Expecting value: line 1 column 1". Test SC#6 verify (jeśli istnieje) catch'uje.

### Pitfall 4: Test pollution — 100 katalogów `reports/` zaśmieca CI

**Co idzie nie tak:** Każdy test który uruchamia `sph_sim.py` jako subprocess tworzy nowy `reports/<ts>/`. Po `python -m unittest discover tests/` mamy 100+ katalogów. Slow I/O, brudny `git status`, zatłoczony filesystem.

**Dlaczego się dzieje:** `write_report` jest zawsze włączone (SC#1).

**Jak uniknąć:** Env var `SPHSIM_NO_REPORT=1`:
- `tests/conftest.py` ustawia `os.environ['SPHSIM_NO_REPORT'] = '1'` w session setUp
- `regression_check.py::run_invocation` przekazuje `env={**os.environ, 'SPHSIM_NO_REPORT': '1'}` do `subprocess.run`
- Test który TESTUJE samego `write_report` (tests/test_report.py) używa `tmp_path` (pytest) lub `tempfile.TemporaryDirectory()` (unittest) i monkeypatch'uje `Path('reports')` → `tmp_dir / 'reports'`

**Warning signs:** Po `python -m unittest discover tests/` widać `git status` z 100+ nowych katalogów.

### Pitfall 5: matplotlib memory leak — figures nie closed

**Co idzie nie tak:** `plt.subplots()` tworzy figure, `fig.savefig(...)` zapisuje, ale jeśli `plt.close(fig)` NIE jest wywołany, matplotlib trzyma figure w globalnym registry. Po 1000 testach: out-of-memory.

**Dlaczego się dzieje:** matplotlib ma globalny "current figure" registry. `plt.subplots()` rejestruje figure. Bez close, ref-count nigdy nie spada.

**Jak uniknąć:** **ZAWSZE** `plt.close(fig)` na końcu każdej plot funkcji. `try/finally` jeśli chcemy być extra-safe:
```python
fig, ax = plt.subplots(...)
try:
    ax.bar(...)
    fig.savefig(path)
finally:
    plt.close(fig)
```

**Warning signs:** Test suite uruchamia się szybko, ale po 100+ runs widać `UserWarning: More than 20 figures have been opened.`

### Pitfall 6: REPL `fake_args` brakuje pól dla `write_report`

**Co idzie nie tak:** `write_report(args, ...)` czyta np. `args.K0` lub `args.valuation`. REPL `fake_args = argparse.Namespace(...)` zbudowany ręcznie z hardcoded fields. Jeśli plan nie sprawdzi że Phase 5 fake_args ma wszystkie wymagane pola → `AttributeError`.

**Dlaczego się dzieje:** REPL Pattern 1:1 z Phase 5 Pitfall 2 (D-23) — `fake_args` jest manualną Namespace, NIE auto-populated.

**Jak uniknąć:** [VERIFIED Phase 5: `repl.py:220-225` i `repl.py:289-293`] — Phase 5 already added `phi`, `rho`, `K0`, `valuation` do `fake_args`. **Wymagane pola dla Phase 6 to subset Phase 5.** No new fake_args changes needed. **Test go potwierdzi:** `tests/test_report.py::test_repl_run_produces_report` — odpala `printf 'run naive zeta=0.5\nexit\n' | python sph_sim.py --interactive` i sprawdza że `./reports/<ts>/` powstał.

**Warning signs:** REPL `run` crashe z `AttributeError: Namespace object has no attribute 'X'`.

### Pitfall 7: Polish characters w ścieżce filesystem (defensive)

**Co idzie nie tak:** Project path zawiera polskie znaki: `/Users/.../STUDIA/sem4/ekonometria 2/` — spacja, brak polskich znaków. **Ale** jeśli user uruchamia z katalogu z polskimi znakami (`/projekty/badania-łańcuchów/`), Path operations powinny działać — Python 3 string są Unicode by default.

**Jak uniknąć:** Używać `pathlib.Path` zamiast string concatenation. Path obsługuje Unicode natywnie na wszystkich platformach.

**Warning signs:** `FileNotFoundError` z dziwnymi bytes w komunikacie. Edge case, low risk.

---

## Section K: Runtime State Inventory

> Phase 6 NIE jest rename/refactor/migration. **Sekcja wymagana?** Częściowo — Phase 6 dodaje SIDE EFFECT (`reports/` katalog). Inwentaryzacja runtime state dla SAFETY:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `./reports/<timestamp>/` NOWY katalog tworzony na każde uruchomienie. Brak prior data. | Nowe — Phase 6 jest pierwszym side-effect-on-fs producerem. |
| Live service config | Brak. Symulator nie ma external services. | None — verified by grep -r "http\|database\|redis" sphsim/ → 0 wyników. |
| OS-registered state | Brak. Brak Task Scheduler, launchd, systemd. | None — czysto lokalny CLI. |
| Secrets/env vars | NOWE env var `SPHSIM_NO_REPORT`. Czytane tylko w `sphsim/report/__init__.py::write_report`. Brak zapisywania. | Dokumentować w README / `--help` epilog (przyszłe Phase 7+). |
| Build artifacts | Brak — projekt nie ma build step (pure Python). `__pycache__/` już gitignore-d. | None — verified. |

**Nothing found in category:** N/A — Phase 6 NIE jest migracją.

---

## Section L: Code Examples

### `sphsim/report/__init__.py` (skeleton)

```python
"""Phase 6: Report + plots generator.

Single public entry point: write_report(args, res, params, K1, mode='single' | 'compare').

Side effects (każde uruchomienie symulacji):
- Tworzy ./reports/<timestamp>/ katalog.
- Zapisuje report.md (assembly w markdown.py).
- Zapisuje decision_distribution.png i kpi_timeseries.png (plotting w plots.py).

Opt-out: env var SPHSIM_NO_REPORT=1 (CI, testy, regression check).
"""
import os
import sys
from pathlib import Path
from datetime import datetime

from sphsim.report.markdown import render_report
from sphsim.report.plots import plot_decision_distribution, plot_kpi_timeseries


def _timestamp() -> str:
    """ISO-like, fs-safe na Windows: %Y%m%d-%H%M%S."""
    return datetime.now().strftime('%Y%m%d-%H%M%S')


def _resolve_report_dir() -> Path:
    """Tworzy ./reports/<ts>/ — z collision retry suffiks -N."""
    base = Path('reports')
    ts = _timestamp()
    candidate = base / ts
    n = 1
    while candidate.exists():
        n += 1
        candidate = base / f'{ts}-{n}'
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


def write_report(args, res, params, K1, *, mode='single'):
    """Zapisuje raport MD + 2 PNG do ./reports/<timestamp>/.

    Returns Path do katalogu raportu, lub None gdy pominięty / fail.
    Nigdy nie rzuca wyjątku — failure logowane na stderr.
    """
    if os.environ.get('SPHSIM_NO_REPORT'):
        return None
    try:
        report_dir = _resolve_report_dir()
    except OSError as e:
        print(f'Nie udało się utworzyć katalogu raportu: {e}. Raport pominięty.', file=sys.stderr)
        return None

    # Rozpakuj dane dla compare mode — PNG-i z with_agent metrics.
    if mode == 'compare':
        plot_res = res['comparison']['with_agent']
        # 'history' i 'devices' są stripped z comparison block — fallback:
        # write_report dla compare musi otrzymać dodatkowo full history (Phase 6 design choice).
        # Patrz §M.24 (Open Questions).
    else:
        plot_res = res

    try:
        plot_decision_distribution(
            plot_res.get('ic_per_phase', {}),
            plot_res.get('veto_per_phase', {}),
            plot_res.get('abstain_per_phase', {}),
            report_dir / 'decision_distribution.png',
        )
        plot_kpi_timeseries(
            plot_res.get('history', {}),
            args.T,
            report_dir / 'kpi_timeseries.png',
        )
    except Exception as e:
        print(f'Błąd generowania wykresów: {e}. Kontynuuję bez PNG.', file=sys.stderr)

    md = render_report(args, res, params, K1, mode=mode)
    (report_dir / 'report.md').write_text(md, encoding='utf-8')
    return report_dir
```

### `sphsim/report/plots.py` (skeleton — initial 2 funkcje)

```python
"""Phase 6: Matplotlib plot generation. Backend='Agg' — headless safe."""
import matplotlib
matplotlib.use('Agg')         # MUST be before pyplot import — D-PH6
import matplotlib.pyplot as plt

# Defensive font fallback (Pitfall 7 mitigation):
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'sans-serif']


def plot_decision_distribution(ic_per_phase, veto_per_phase, abstain_per_phase, path):
    """PLOT-01: słupkowy COMMIT/ABSTAIN/VETO per faza 1..F-1."""
    phases = sorted(set(list(ic_per_phase.keys()) +
                        list(veto_per_phase.keys()) +
                        list(abstain_per_phase.keys())))
    if not phases:
        phases = [1, 2, 3, 4]  # safety dla pustych runs

    commits  = [ic_per_phase.get(p, {}).get('commits', 0) for p in phases]
    abstains = [abstain_per_phase.get(p, 0) for p in phases]
    vetos    = [veto_per_phase.get(p, 0) for p in phases]

    import numpy as np
    x = np.arange(len(phases))
    w = 0.27

    fig, ax = plt.subplots(figsize=(8, 5), dpi=120)
    try:
        ax.bar(x - w, commits,  w, label='COMMIT',  color='#2E7D32')
        ax.bar(x,     abstains, w, label='ABSTAIN', color='#757575')
        ax.bar(x + w, vetos,    w, label='VETO',    color='#C62828')
        ax.set_xlabel('Faza urządzenia')
        ax.set_ylabel('Liczba decyzji')
        ax.set_title('Rozkład decyzji per faza')
        ax.set_xticks(x)
        ax.set_xticklabels([f'Faza {p}' for p in phases])
        ax.legend(loc='upper right')
        ax.grid(axis='y', linestyle='--', alpha=0.4)
        fig.tight_layout()
        fig.savefig(path)
    finally:
        plt.close(fig)


def plot_kpi_timeseries(history, T, path):
    """PLOT-02: avg_val i avg_providers per cykl, ostatnie 100 cykli zaznaczone."""
    if not history or 'val' not in history or 'providers' not in history:
        return  # nothing to plot — silent skip

    val = history['val']
    providers = history['providers']
    if not val or not providers:
        return

    cycles = list(range(1, len(val) + 1))
    fig, ax1 = plt.subplots(figsize=(10, 5), dpi=120)
    try:
        color_val = '#1565C0'
        ax1.set_xlabel('Cykl symulacji')
        ax1.set_ylabel('avg_val (waluacja)', color=color_val)
        ax1.plot(cycles, val, color=color_val, linewidth=0.8, alpha=0.85, label='avg_val')
        ax1.tick_params(axis='y', labelcolor=color_val)

        ax2 = ax1.twinx()
        color_prov = '#EF6C00'
        ax2.set_ylabel('avg_providers (liczba dostawców)', color=color_prov)
        ax2.plot(cycles, providers, color=color_prov, linewidth=0.8, alpha=0.85, label='avg_providers')
        ax2.tick_params(axis='y', labelcolor=color_prov)

        last100_start = max(1, T - 99)
        ax1.axvspan(last100_start, T, alpha=0.15, color='grey')

        fig.suptitle('Przebieg KPI w czasie symulacji (z zaznaczonymi ostatnimi 100 cyklami)')
        fig.tight_layout()
        fig.savefig(path)
    finally:
        plt.close(fig)
```

### `sphsim/report/markdown.py` (skeleton — assembly)

```python
"""Phase 6: Markdown report assembly. Pure functions, zero side effects.
Returned string jest zapisywany przez write_report. Tester może
asercjować na zwracanym stringu bez touch'owania filesystem.
"""
import json
from pathlib import Path

from sphsim.cli.output import format_config_header

BASELINE_PATH = (Path(__file__).resolve().parent.parent.parent /
                 'tests' / 'fixtures' / 'baseline_v1' /
                 '08-naive-zeta-0.75-baseline.json')


def render_report(args, res, params, K1, *, mode='single') -> str:
    """Assembluje pełen string MD z 6-7 sekcji."""
    parts = []
    parts.append(_header(args))
    parts.append(format_config_header(args, args.K0, K1, args.phi, args.rho))
    parts.append(_render_strategy_params(args, params))
    parts.append(_render_kpi_table(res, mode=mode))
    parts.append(_render_decision_table(res, mode=mode))
    parts.append(_render_plots_section())
    parts.append(_render_baseline_comparison(args, res, mode=mode))
    if mode == 'compare':
        parts.append(_render_compare_section(res))
    return '\n\n'.join(parts) + '\n'


def _header(args) -> str:
    from datetime import datetime
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f'# Raport symulacji SPH — `{args.strategy}` ({ts})'


def _render_kpi_table(res, *, mode='single') -> str:
    """Tabela 5 KPI z named rows (SC#2)."""
    src = res['comparison']['with_agent'] if mode == 'compare' else res
    lines = [
        '## Metryki KPI',
        '',
        '| KPI | Wartość | Cel |',
        '|-----|---------|-----|',
        f'| avg_val_last100      | {src["avg_val_last100"]:.2f}   | MAX → 100   |',
        f'| cum_val_total        | {src["cum_val_total"]:.1f}     | MAX → 100000 |',
        f'| avg_net_profit       | {src["avg_net_profit"]:+.4f}   | > 0          |',
        f'| delivery_ratio       | {src["delivery_ratio"]:.2%}    | wysoki       |',
        f'| avg_providers_l100   | {src["avg_providers_l100"]:.2f}| ≈ 100..120   |',
    ]
    return '\n'.join(lines)


def _render_decision_table(res, *, mode='single') -> str:
    """Tabela rozkładu decyzji per faza (SC#3 — dane do PLOT-01)."""
    src = res['comparison']['with_agent'] if mode == 'compare' else res
    ic   = src.get('ic_per_phase', {})
    veto = src.get('veto_per_phase', {})
    abst = src.get('abstain_per_phase', {})
    phases = sorted(set(list(ic.keys()) + list(veto.keys()) + list(abst.keys())))

    lines = ['## Rozkład decyzji per faza', '',
             '| Faza | COMMIT | ABSTAIN | VETO | Suma |',
             '|------|--------|---------|------|------|']
    for p in phases:
        c = ic.get(p, {}).get('commits', 0)
        a = abst.get(p, 0)
        v = veto.get(p, 0)
        s = c + a + v
        lines.append(f'| {p}    | {c}    | {a}     | {v}  | {s}  |')
    return '\n'.join(lines)


def _render_plots_section() -> str:
    return ('## Wykresy\n\n'
            '![Rozkład decyzji per faza](decision_distribution.png)\n\n'
            '![Przebieg KPI w czasie](kpi_timeseries.png)')


def _render_baseline_comparison(args, res, *, mode='single') -> str:
    src = res['comparison']['with_agent'] if mode == 'compare' else res
    try:
        baseline_raw = json.loads(BASELINE_PATH.read_text(encoding='utf-8'))
        b = baseline_raw['metrics']
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return ('## Porównanie z baseline\n\n'
                '*Baseline niedostępny — sekcja pominięta.*')
    KPIS = [('avg_val_last100', '{:.2f}'), ('cum_val_total', '{:.1f}'),
            ('avg_net_profit', '{:+.4f}'), ('delivery_ratio', '{:.2%}'),
            ('avg_providers_l100', '{:.2f}')]
    lines = ['## Porównanie z baseline `naive --zeta 0.75 --no-agent`', '',
             '| KPI | Bieżący run | Baseline v1.0 | Δ |',
             '|-----|-------------|---------------|---|']
    for kpi, fmt in KPIS:
        cur = src[kpi]
        base = b[kpi]
        delta = cur - base
        if kpi == 'delivery_ratio':
            lines.append(f'| {kpi} | {cur:.2%} | {base:.2%} | {delta:+.2%} |')
        else:
            lines.append(f'| {kpi} | {fmt.format(cur)} | {fmt.format(base)} | {delta:+.4f} |')
    lines.append('')
    lines.append('*Baseline z `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json`.* '
                 '*Uwaga: jeśli używasz override `--phi/--rho/--K0/--valuation/--T/--nU`, '
                 'środowisko może różnić się od baseline.*')
    return '\n'.join(lines)


def _render_compare_section(res) -> str:
    comp = res['comparison']
    with_, without_, delta = comp['with_agent'], comp['without_agent'], comp['delta']
    helps = '✓ TAK' if comp['agent_helps'] else '✗ NIE'
    lines = ['## Porównanie z RationalAgent (with-agent vs bez agenta)', '',
             '| KPI | with-agent | bez agenta | Δ (with - bez) |',
             '|-----|------------|------------|----------------|']
    KPIS = [('avg_val_last100', '{:.2f}'), ('cum_val_total', '{:.1f}'),
            ('avg_net_profit', '{:+.4f}'), ('delivery_ratio', '{:.2%}'),
            ('avg_providers_l100', '{:.2f}')]
    for kpi, fmt in KPIS:
        w, wo, d = with_[kpi], without_[kpi], delta[kpi]
        if kpi == 'delivery_ratio':
            lines.append(f'| {kpi} | {w:.2%} | {wo:.2%} | {d:+.2%} |')
        else:
            lines.append(f'| {kpi} | {fmt.format(w)} | {fmt.format(wo)} | {d:+.4f} |')
    lines.append('')
    lines.append(f'**Werdykt:** Agent zaweto\'wał {with_.get("n_vetoed_total", 0)} COMMIT-ów. '
                 f'with-agent bije without-agent: {helps}.')
    return '\n'.join(lines)


def _render_strategy_params(args, params) -> str:
    lines = ['## Strategia i parametry', '',
             '| Parametr | Wartość |',
             '|----------|---------|',
             f'| Strategia | {args.strategy} |']
    for k, v in params.items():
        if v is not None:
            lines.append(f'| {k} | {v} |')
    if args.compare_agent:
        lines.append('| Tryb agenta | porównawczy (`--compare-agent`) |')
    elif args.no_agent:
        lines.append('| Tryb agenta | wyłączony (`--no-agent`) |')
    else:
        lines.append('| Tryb agenta | włączony (default) |')
    return '\n'.join(lines)
```

---

## Section M: Wave Proposal

### Wave 0 — Scaffolding (locks taxonomy)

- **06-00-PLAN:** `tests/test_report.py` skeleton (12 stub testów, all marked `unittest.skip("Wave N")`); `tests/test_simulator_abstain.py` skeleton (3 stubs); `scripts/verify_phase6.sh` skeleton (banner + check() helper + summary, FAIL=0 placeholder); `.gitignore` add `reports/`.

### Wave 1 — Data gap fix (blocks Waves 2+)

- **06-01-PLAN:** `sphsim/core/device.py` add `abstain_phase_stats` + `sphsim/core/simulator.py` add inkrementacja w ABSTAIN branch + agregacja `abstain_per_phase`. `tests/test_simulator_abstain.py` 3 testy (correct aggregation, VETO doesn't increment abstain, zero-fill phases).
- Regression must PASS (SKIP_KEYS not yet extended — will fail if `abstain_per_phase` leaks into env block; verify it lands in `metrics` and SKIP_KEYS catches it).

### Wave 2 — Report package (parallel-eligible)

Plans 02 and 03 **CAN execute in parallel** (different files, no shared deps).

- **06-02-PLAN:** `sphsim/report/__init__.py` + `sphsim/report/markdown.py` — write_report orchestrator + 7 sekcji MD assembly + baseline loader. Tests: TestReportSections, TestReportSidedEffects (env var), TestReportCompareMode. Uses Wave 1's `abstain_per_phase` (already merged).
- **06-03-PLAN:** `sphsim/report/plots.py` — `matplotlib.use('Agg')` + 2 plot funkcje + close-figure discipline. Tests: TestPlots (PNG files exist + non-zero + via Pillow check dimensions). Uses Wave 1's `abstain_per_phase` (already merged).

### Wave 3 — Integration (blocked on Wave 2)

- **06-04-PLAN:** Wire `write_report(...)` w `sphsim/cli/main.py` (single + custom + compare branch), `sphsim/cli/repl.py::do_run` i `do_compare`. Banner na stderr w polskim. Tests: TestEntrypoints (4 entrypoints × generuje raport correctly). `regression_check.py::run_invocation` przekazuje `SPHSIM_NO_REPORT=1` env.

### Wave 4 — Final gate (blocked on Wave 3)

- **06-05-PLAN:** `regression_check.py` SKIP_KEYS extension (`abstain_per_phase`, opcjonalnie `report_path`). Full `scripts/verify_phase6.sh` (≈20 checks: REPORT-01/02/03 × pliki istnieją + sekcje obecne + PLOT-01/02/03 + SC#5 compare mode + SC#6 JSON regression + env var opt-out works). Mark phase complete.

**Parallelism:** Wave 2 plans 02 i 03 mogą być equipped jednocześnie przez Claude'a (Plan 02 dotyka tylko markdown.py + tests, Plan 03 tylko plots.py + tests). Wave 1 jest blocking (data gap). Waves 3 i 4 są sekwencyjne (integration → gate).

---

## Section N: Open Questions

1. **Compare mode + history dla PNG-ów**
   - **Co wiadomo:** `run_compare` (main.py:42-44) strippuje `history` i `devices` z `with_agent` / `without_agent` dict. Comparison block w JSON nie zawiera history.
   - **Co niejasne:** Jak PLOT-02 (kpi_timeseries) dostanie history dla compare mode? Opcja (a): NIE stripować history przed write_report; (b): write_report dla compare mode bierze raw `res_with`/`res_without` od `run_compare`, nie tylko `comparison` block.
   - **Rekomendacja:** Modyfikuj `run_compare` żeby zwracał dict `{'comparison': {...}, '_with_agent_full': res_with}` (z private prefix). `write_report(mode='compare')` używa `res['_with_agent_full']['history']` dla PNG-ów. JSON output strippuje pola z `_` prefix przed serializacją. Plan-discuss decyduje.

2. **`--no-report` flaga CLI vs tylko env var**
   - **Co wiadomo:** SC#1 mówi "bez żadnych flag, zawsze". Env var `SPHSIM_NO_REPORT=1` jest "out-of-band" — nie pojawia się w `--help`, więc literalnie satisfies SC#1.
   - **Co niejasne:** Czy dodać też `--no-report` flagę dla user discoverability (np. dev chce sprawdzić CLI bez report-pollution)?
   - **Rekomendacja:** Domyślnie tylko env var (czysty SC#1). Jeśli user feedback wymaga flagi, dodać w Phase 7+ jako convenience.

3. **`requirements.txt` / `pyproject.toml`**
   - **Co wiadomo:** PROJECT.md mówi "Python 3.7+ + matplotlib". Brak `requirements.txt`. Lokalnie matplotlib 3.10.7 jest zainstalowany.
   - **Co niejasne:** CI / inni użytkownicy nie mają instrukcji jak zainstalować matplotlib. Czy Phase 6 wprowadza `requirements.txt`?
   - **Rekomendacja:** Dodać `requirements.txt` z `matplotlib>=3.5` jako single line — minimal overhead, ułatwia adoption. Decision do discuss-phase.

4. **PNG dimensions check via Pillow (test only)**
   - **Co wiadomo:** PLOT-01/02 tests muszą weryfikować PNG content NIE TYLKO existence (PNG z `fig.savefig` z błędnym title nadal istnieje + jest non-zero).
   - **Co niejasne:** Czy używać Pillow (`from PIL import Image`) do smoke testu dimensions, czy testować TYLKO file existence + non-zero size?
   - **Rekomendacja:** File existence + `os.path.getsize() > 1000` jako proxy for "valid PNG generated". Pillow jest opcjonalne. Pełen pixel-diff out-of-scope.

5. **Timestamp z timezone vs naive**
   - **Co wiadomo:** `datetime.now()` zwraca naive datetime (lokalna strefa, bez tzinfo).
   - **Co niejasne:** Czy raport powinien zawierać tz info (np. dla użytkowników z innej strefy)?
   - **Rekomendacja:** Naive timestamp w fs path (`20260528-065229` — krótki, sortowalny). Wewnątrz raportu nagłówek może mieć `datetime.now().astimezone().isoformat()` (z tz suffix). Decision do discuss-phase, low priority.

---

## Section O: Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.7+ | All sphsim/ code | ✓ | 3.14.3 (lokalnie) | — |
| matplotlib | `sphsim/report/plots.py` | ✓ | 3.10.7 (lokalnie) | — (PROJECT.md required dep) |
| PIL/Pillow | Tests (opcjonalnie — dla PNG dimensions check) | TBD | TBD | os.path.getsize >0 as proxy |
| `pip` | Install matplotlib na CI | ✓ assumed | — | — |
| `tests/fixtures/baseline_v1/` (committed) | `_render_baseline_comparison` | ✓ | — | Sekcja 6 z disclaimer "baseline niedostępny" |

**Missing dependencies with no fallback:** brak — matplotlib już zainstalowany lokalnie, baseline fixtures są committed.

**Missing dependencies with fallback:** PIL/Pillow — fallback do file size check.

---

## Section P: Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| matplotlib | PyPI | 22 lat (od 2003) | 30M+/tydzień | https://github.com/matplotlib/matplotlib | [OK] (verified via `slopcheck install matplotlib`) | Approved — already PROJECT.md required dep |
| numpy | PyPI (transitive, matplotlib dep) | 19 lat (od 2006) | 100M+/tydzień | https://github.com/numpy/numpy | implicit OK via matplotlib | Approved (transitive) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

[VERIFIED: `slopcheck install matplotlib` returned `[OK]` — confirmed legit on PyPI. matplotlib jest core scientific Python package, miliony użytkowników, długa historia maintainership (NumFOCUS sponsored project).]

---

## Section Q: Security Domain

> `security_enforcement` jest absent z `.planning/config.json` — treated as **enabled** per defaults.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — projekt akademicki, lokalny CLI |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes (minimal) | argparse + `type=` converters już z Phase 5; Phase 6 nie wprowadza nowych user-input vectors |
| V6 Cryptography | no | — |
| V12 File and Resources | **yes** | Filesystem writes: `mkdir`, `write_text`, `savefig`. Path resolution via `pathlib.Path`; brak shell injection wektora. PII: brak — symulacja deterministyczna. |
| V14 Configuration | yes (minimal) | Env var `SPHSIM_NO_REPORT` — single boolean, no parsing risk. |

### Known Threat Patterns for {Python CLI + matplotlib}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal (custom `--report-dir` flag — NIE wprowadzane w Phase 6) | Tampering | N/A — Phase 6 hardcoduje `./reports/`. Brak user-controlled path. |
| Filesystem exhaustion (1000+ runs × 100 KB = 100 MB) | DoS | Documented w README — user musi rotować `./reports/`. Out-of-scope dla Phase 6 cleanup. |
| Matplotlib font enumeration leak (PII font discovery from PNG metadata) | Info Disclosure | Default matplotlib metadata zawiera `matplotlib version` w PNG EXIF — niska wrażliwość. Brak akcji. |
| ReDoS w polskich regex (nieobecne — brak regex w Phase 6) | DoS | N/A |
| Symlink attack na `./reports/` (user pre-tworzy symlink do system file) | Tampering | Pathlib `mkdir(exist_ok=False)` zwraca FileExistsError — collision handler dodaje `-N` suffiks. Risk: low — local educational tool. |

**Phase 6 security stance:** minimal new surface (file writes only, no user-controlled paths, no eval, no subprocess). Threat model unchanged from Phase 5.

---

## Section R: State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| v1.0: tylko `--json` stdout + human-readable banner | Phase 6: każde uruchomienie produkuje persistent MD raport + 2 PNG | Phase 6 | Reproducibility + shareability: dydaktyczne wyniki idą do MD który student może dołączyć do sprawozdania |
| Phase 1-5: brak side effects na FS poza `tests/fixtures/` | Phase 6: side effect `./reports/<ts>/` | Phase 6 | Pierwsza faza która FAKTYCZNIE używa filesystem dla outputu. Wymaga `.gitignore` update i `SPHSIM_NO_REPORT` opt-out. |
| Phase 4: `dev.n_abstain` global counter | Phase 6: + `abstain_phase_stats` dict per Device (pattern 1:1 z `veto_phase_stats`) | Phase 6 | Symetria z VETO bookkeeping; PLOT-01 dostaje pełne dane |

**Deprecated/outdated:**
- Brak — Phase 6 jest czysto additive. Backwards compat: pełna.

---

## Section S: Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | DejaVu Sans default matplotlib font wspiera wszystkie polskie znaki na wszystkich platformach | §B.8 | Low — verified lokalnie; defensive font.sans-serif fallback dodany |
| A2 | matplotlib `Agg` backend działa identycznie na macOS / Linux / Windows | §B.7 | Low — Agg jest pure-Python raster renderer, cross-platform |
| A3 | `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` pozostanie committed i niezmieniony | §C.9, §A.5 | Medium — gdy ktoś przegeneruje fixtures w przyszłej fazie, baseline KPI w raporcie może się zmienić |
| A4 | `SPHSIM_NO_REPORT` env var jako opt-out satisfies SC#1 "bez żadnych flag" | §G.18, §N.2 | Medium — semantic interpretation; discuss-phase confirm |
| A5 | Timestamp `%Y%m%d-%H%M%S` jest fs-safe na Windows | §C.7 | Low — verified `:` jest blokowany, `-` jest OK |
| A6 | Compare mode z PNG-ami pokazuje `with_agent` history (NOT `without_agent`) | §A.4, §N.1 | Medium — Claude's Discretion; discuss-phase confirm |
| A7 | `report_path` w JSON output nie łamie żadnego parsera v1.0 | §G.16 | Low — JSON parsers tolerują extra top-level keys; SKIP_KEYS extension safeguard |
| A8 | matplotlib zostanie wymagany na CI bez `requirements.txt` (dev install lub explicit `pip install matplotlib` na CI yaml) | §B.4, §N.3 | Medium — CI failure if no matplotlib; discuss-phase confirm |

**ANY claim tagged [ASSUMED]:** all 8 above. Verified-vs-assumed split: A1, A2, A5, A7 są verified empirically lub by docs. A3, A4, A6, A8 są discretionary decisions czekające na discuss-phase confirm.

---

## Section T: Sources

### Primary (HIGH confidence — code reading + live runtime probes)
- `sphsim/core/simulator.py` — `run()` returned dict structure, history shape, ic/veto aggregation patterns
- `sphsim/core/device.py` — Device dataclass + phase_stats / veto_phase_stats precedent
- `sphsim/cli/main.py` — single-run + custom + compare branches, integration points dla write_report
- `sphsim/cli/repl.py` — do_run + do_compare fake_args structure (Phase 5 D-23 already covers Phase 6 needs)
- `sphsim/cli/output.py` — `format_config_header` reuse (verbatim w Section 1 raportu MD), `format_compare` jako wzór compare data structure
- `sphsim/agent/rational.py` — closure-based wrapper pattern (no new insight, ale potwierdza VETO bookkeeping flow)
- `scripts/regression_check.py` — SKIP_KEYS pattern dla Phase 6 extension
- `scripts/generate_baseline.py` — INVOCATIONS list + fixture paths
- `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` — kanoniczny baseline, dosłowny content
- `.planning/ROADMAP.md` Phase 6 — 6 Success Criteria
- `.planning/REQUIREMENTS.md` — REPORT-01/02/03 + PLOT-01/02/03 verbatim
- `.planning/PROJECT.md` — Key Decision "matplotlib required dep, PNG zawsze"; Constraints "polski w raporcie", "backwards compat"
- `.planning/phases/05-configurable-environment/05-RESEARCH.md` — Phase 5 precedent dla format_config_header + SKIP_KEYS extension pattern (D-PH5)
- `.planning/phases/04-rational-agent-veto-layer/04-CONTEXT.md` — Phase 4 veto_phase_stats / abstain_phase_stats parallelism inspiration
- `PROMPT_DLA_AGENTA.txt` — KPI semantics + baseline numbers (avg_val=92, avg_profit=140.76)
- Live runtime probes (Python 3.14.3 z matplotlib 3.10.7):
  - `history` keys = `['val', 'cum_val', 'profit', 'delivery', 'sus', 'providers']`, length = T (1000)
  - result dict keys = 11 fields, `n_vetoed_total=0` dla `--no-agent`
  - `ic_per_phase` keys = `[1, 2, 3, 4]` (NOT 5)
  - matplotlib Agg backend works headless, Polish chars render OK in DejaVu Sans

### Secondary (MEDIUM confidence)
- `.planning/codebase/STACK.md` — "Standard Library Only" constraint już naruszony przez Phase 6 (matplotlib) — to zaplanowana decyzja
- `scripts/verify_phase5.sh` — wzór `check()` helper + `set -euo pipefail` + cleanup trap dla Phase 6 verify script

### Tertiary (LOW confidence)
- None — Phase 6 jest dobrze pokryta przez direct code reading + live verification

---

## Metadata

**Confidence breakdown:**
- Standard stack (matplotlib): HIGH — required dep, installed, verified
- Architecture (3-modułowy report package): HIGH — wzorzec analogiczny do `sphsim/agent/` (Phase 4)
- Pitfalls (matplotlib + test pollution + JSON compat): HIGH — wszystkie 7 pitfalls identyfikowanych z code reading lub live probes, nie z spekulacji
- Data gap (abstain_per_phase): HIGH — direct verification by `grep n_abstain` + simulator.run() probe
- Compare-mode history threading (Open Q1): MEDIUM — Claude's Discretion punkt, discuss-phase confirm potrzebny
- Timestamp / env-var opt-out (Open Q2): MEDIUM — UX decision, discuss-phase confirm potrzebny

**Research date:** 2026-05-28
**Valid until:** Indefinite for code facts; re-verify if Phase 7 changes simulator.run() returned dict shape, lub gdy matplotlib API zmieni się (next major release unlikely to break basic API)
