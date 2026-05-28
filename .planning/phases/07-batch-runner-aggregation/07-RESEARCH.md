# Phase 7: Batch runner + aggregation — Research

**Researched:** 2026-05-28
**Domain:** Multi-seed orchestration + statistical aggregation + matplotlib boxplots + REPL/CLI command extension
**Confidence:** HIGH (codebase claims VERIFIED by direct file reads + live runtime probes; statistics claims CITED to scipy/numpy docs; one deferred boundary — parallelism — recommended out of scope with reasoning)

---

## Summary

Phase 7 dorzuca **jeden orkiestrator** który N-krotnie woła istniejący single-run pipeline (`SPHSimulator(...).run()`), zbiera 5 KPI per seed, oblicza statystyki agregatu (mean / std / min / max / 95% CI) i produkuje **jeden** raport MD (z tabelą per-seed + tabelą agregatu) plus **jeden nowy PNG** (`batch_aggregate.png` z 5 box-plotami). Cały dodatkowy kod żyje w nowym pakiecie `sphsim/batch/` plus nowy renderer w `sphsim/report/batch_markdown.py` i nowy plot helper w `sphsim/report/plots.py`. Wywołania: nowa flaga `--batch --seeds <N|lista>` w `sphsim/cli/args.py` + nowa komenda `do_batch` w `sphsim/cli/repl.py`.

**95% CI**: rekomendacja **t-Studenta** (`scipy.stats.t.interval`) — `scipy` jest już zainstalowany (1.16.3, VERIFIED), formuła jest podręcznikowa dla małych N (N=10 jest klasycznym małym próbkiem), bootstrap jest niepotrzebnym powiększeniem złożoności bez teoretycznego zysku przy normalnym przybliżeniu KPI z 1000 cykli per seed (CLT applies do większości KPI).

**Parallelism**: **SEQUENTIAL only** w v1. Jeden run kosztuje ~150 ms (VERIFIED `/usr/bin/time` na `naive --zeta 0.75 --seed 42 --T 1000`). Sequential 10 seedów = ~1.5 s — szybciej niż import matplotlib. Multiprocessing wymagałby picklowania `wrap_with_agent(strategy_fn, expected_P)` closure — fragile, nie warte złożoności na N≤100.

**Report extension**: **Wrap, nie podmieniaj** istniejący single-run renderer. Phase 6 `sphsim/report/markdown.py::render_report` jest pure function biorącą jeden `res` dict — Phase 7 dodaje nowy `render_batch_report(args, per_seed_results, aggregate, params, K1)` który **NIE** woła `render_report` per seed (nie chcemy 10 raportów per-seed na jeden batch), tylko składa: (1) header + config + strategy params (reusing `format_config_header`), (2) tabelę per-seed (N wierszy × 6 kolumn), (3) tabelę agregatu (5 wierszy × 5 kolumn), (4) wyniki baseline-beating, (5) link do `batch_aggregate.png`.

**Boxplot**: jedna `matplotlib.pyplot.boxplot(data, labels=...)` figura z 5 boxes side-by-side, dodana do `sphsim/report/plots.py` (już ma backend `Agg`, font Polish fallback, fig.close pattern). Plik wyjściowy obok report.md: `./reports/batch_<ts>/batch_aggregate.png` (relatywny link `![](batch_aggregate.png)`).

**Baseline-beating check**: baseline `avg_val_last100 = 92.0` jest **STATYCZNE** — żyje w `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` (VERIFIED), to ten sam plik, którego używa Phase 6 single-run report (`sphsim/report/markdown.py::BASELINE_PATH`). Phase 7 czyta ten sam plik i porównuje lower bound 95% CI dla `avg_val_last100` z `baseline['metrics']['avg_val_last100']`. **NIE** uruchamiamy 10 dodatkowych baseline-runów — to byłaby duplikacja oracle który jest committed.

**Primary recommendation:** Sześć małych zmian — (1) `sphsim/batch/__init__.py` + `runner.py` + `stats.py` (nowy pakiet — runner, stats, parser seedów), (2) `sphsim/report/batch_markdown.py` + ROZSZERZENIE `sphsim/report/plots.py::plot_batch_aggregate(per_seed_kpis, path)`, (3) `sphsim/cli/args.py` — flaga `--batch` + `--seeds` z custom type converter (parser N|list), (4) `sphsim/cli/main.py` — early branch `args.batch` przed single-run gałęzią, (5) `sphsim/cli/repl.py::do_batch` (analogicznie do `do_compare`), (6) `tests/test_batch.py` (≈15 testów) + `scripts/verify_phase7.sh`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Parser seedów (`N` lub `1,5,42,100`) | CLI args (`sphsim/cli/args.py` — type converter) | — | Walidacja musi rzucić Polski `argparse.ArgumentTypeError` PRZED batch — pattern z `_parse_phi_list` |
| Orkiestracja N×`sim.run()` | Batch (`sphsim/batch/runner.py`) | — | Pure function — przyjmuje args + lista seedów, zwraca `list[dict[kpi -> float]]` |
| Agregacja statystyczna (mean/std/min/max/95% CI) | Batch (`sphsim/batch/stats.py`) | scipy + numpy | scipy.stats.t.interval CITED — VERIFIED instalacja |
| Boxplot 5 KPI | Report (`sphsim/report/plots.py::plot_batch_aggregate`) | — | Reuse istniejącego backend setup (Agg, font fallback, close-in-finally) |
| Render batch MD | Report (`sphsim/report/batch_markdown.py`) | reuse `format_config_header` | NIE reusuj `render_report` — batch ma inną strukturę sekcji |
| Wywołanie write_batch_report z CLI | CLI main (`sphsim/cli/main.py`) | — | Nowy early branch `if args.batch:` — przed `args.compare_agent` i przed single-run |
| Wywołanie z REPL | REPL (`sphsim/cli/repl.py::do_batch`) | — | Symmetric — pattern z `do_compare` |
| Opt-out (test/CI safety) | env-var `SPHSIM_NO_REPORT=1` (już istnieje z Phase 6) | — | Phase 7 dziedziczy — testy NIE śmiecą w `./reports/` |
| Baseline-beating verdict | Batch (`sphsim/batch/runner.py` lub `batch_markdown.py`) | baseline_v1 JSON | Reuse `BASELINE_PATH` z `sphsim/report/markdown.py` (single source of truth) |

---

<user_constraints>
## User Constraints (from CONTEXT.md)

> CONTEXT.md dla Phase 7 NIE ISTNIEJE w momencie tej researcha. Sekcja zostanie uzupełniona przez `discuss-phase` jeśli pojawią się user-locked decisions.
>
> **Wstępne sugestie do discuss-phase (Locked z ROADMAP SC + propozycje researchera):**
>
> - **Locked (z ROADMAP SC #1):** Komenda `/batch <strategia> --seeds 10` (REPL) lub `--batch --seeds 10` (CLI); `--seeds 1,5,42,100` przyjmuje również jawną listę.
> - **Locked (z SC #2):** Tabela per-seed (jeden wiersz na seed: seed + 5 KPI) + sekcja agregatu (mean, std, min, max, 95% CI) dla każdego KPI.
> - **Locked (z SC #3):** Plik `batch_aggregate.png` z box-plotami 5 KPI, linkowany w raporcie.
> - **Locked (z SC #4):** Batch działa z `RationalAgent` (default) i `--no-agent`.
> - **Locked (z SC #5):** Batch report wskazuje czy strategia bije baseline `naive --zeta 0.75` (czy 95% CI dla `avg_val_last100` > 92).
>
> **Do potwierdzenia w discuss-phase (Claude's Discretion):**
>   1. **Output dir naming:** `./reports/batch_<timestamp>/` (jawnie odróżnia od single-run `./reports/<timestamp>/`) vs `./reports/<timestamp>-batch/`. Researcher rekomenduje **`./reports/batch_<timestamp>/`** — prefiks jest discoverable przez `ls reports/batch_*` i nie koliduje z single-run namespace.
>   2. **Seed-list grammar edge cases:** `--seeds 0` — odrzucić (`seed=0` jest valid w numpy ale stylistycznie disrupting) lub akceptować? `--seeds 1,1,2` — deduplikować lub rzucić error? `--seeds 1..10` (range syntax) — wspierać dodatkowo czy nie? Researcher rekomenduje **strict grammar v1**: tylko `N` (positive int → 1..N) lub `int,int,...` (positive ints, dedup z preserved order, rzuca error dla 0/ujemne). Range `1..10` deferred.
>   3. **N=1 edge case:** `--seeds 42` (single seed) — std/CI degenerate. Researcher rekomenduje **graceful display** — w tabeli agregatu pokazać `std = 0.0`, `CI: n/a (N=1)` jako string, zamiast crash; baseline-beating verdict używa tylko mean (nie CI) gdy N=1.
>   4. **`expected_P` w batch z `RationalAgent`:** Każdy run dostaje to samo `expected_P` z args (z `--expected_P` lub default 100). Researcher rekomenduje **tak** — batch porównuje seedy, nie parametry; jeśli user chce eksperymentować z `expected_P`, robi to ZA pomocą kilku batch runów.
>   5. **Boxplot scale:** 5 KPI mają DRASTYCZNIE różne zakresy (`avg_val_last100`≈92, `cum_val_total`≈92000, `delivery_ratio`≈0.79, `avg_providers_l100`≈105, `avg_net_profit`≈141). Side-by-side boxplot z jedną Y-osią będzie nieczytelny. Researcher rekomenduje **5 subplotów (1×5 grid) z indywidualnymi Y-osiami** zamiast pojedynczego boxplotu — każdy KPI dostaje swój panel + label.
>   6. **Bilateralne CI vs jednostronne:** SC #5 mówi "czy 95% CI dla avg_val_last100 jest powyżej 92" — sugeruje **lower bound 95% CI > 92**, czyli klasyczny dwustronny przedział i porównanie lower bounda. Researcher rekomenduje **dwustronny CI** (standard, bardziej zachowawczy) i porównywać `CI_lower > baseline` — to dyskusja dydaktyczna, dwustronny CI jest oczywistym defaultem.
>   7. **Czy batch działa z `--compare-agent`:** Nie pojawia się w SC. Researcher rekomenduje **NIE** w v1 — `--batch` i `--compare-agent` mutex (analogicznie do innych mutex grup); jeśli user chce porównanie, robi dwa batchy (jeden default z agentem, jeden `--no-agent`).
>
> **Deferred do v2:** Parallelism (multiprocessing), persistent batch DB, multi-strategy comparison w jednym batchu, range syntax `1..10`, custom seed generators (np. od hash sekretnej fasoli).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BATCH-01 | Użytkownik może uruchomić `/batch <strategia> --seeds 10` lub `--seeds 1,2,3,...` aby uruchomić symulację dla wielu seedów | §B.3 (seed parser), §C.4 (CLI args wiring), §C.5 (REPL do_batch) |
| BATCH-02 | Wyniki batcha są agregowane: mean, std, min/max, 95% CI dla każdego KPI | §D.6 (stats module), §D.7 (scipy/numpy verified), §D.8 (N=1 edge case) |
| BATCH-03 | Raport MD z trybu batch zawiera tabelę per-seed + sekcję agregatu statystycznego | §E.9 (batch_markdown), §E.10 (table structure), §E.11 (baseline-beating verdict) |
| PLOT-04 | W trybie batch generowany jest dodatkowy wykres `batch_aggregate.png` z box-plotami KPI | §F.12 (plots extension), §F.13 (5-subplot rationale dla różnych skal KPI) |
</phase_requirements>

---

## Section A: Existing State of the Code (codebase reuse map)

### A.1 — Single-run pipeline entry point

[VERIFIED — `sphsim/cli/main.py:124-168` (built-in branch), `:72-122` (custom branch)]

Single-run pipeline ma 6 kroków sekwencyjnych:

```
parse_args()  →  K1 = float('inf') if args.K1 < 0 else args.K1
              →  params = {'zeta': args.zeta, 'max_phase': args.max_phase, ...}
              →  raw_strategy_fn = STRATEGIES[args.strategy]
              →  strategy_fn = wrap_with_agent(raw_strategy_fn, args.expected_P)  if not args.no_agent
              →  sim = SPHSimulator(nU=..., nSUS=..., K0=..., K1=..., F=DEFAULT_F, T=..., kappa=...,
                                    alpha=..., phi=..., rho=..., valuation_preset=...,
                                    strategy_fn=strategy_fn, params=params, seed=args.seed)
              →  res = sim.run()
              →  write_report(args, res, params, K1, mode='single')
```

**Phase 7 nie buduje ekstrahowanej `run_single(args, seed) -> res` funkcji** — to byłby refactor głębszego zasięgu (zmiana entrypointu Phase 6). Zamiast tego, **`sphsim/batch/runner.py::run_batch(args, seeds)` zamyka tę logikę w pętli for-each-seed**, używając tych samych args z mutowanym `args.seed = s`. To czysty pattern adapter — Phase 7 widzi single-run jako black box przyjmujący `args` i emitujący `res`.

**Implication:** `run_batch` musi rekonstruować `params`, `K1`, `raw_strategy_fn`, `strategy_fn` (z opt wrap), `SPHSimulator(...).run()` — całość duplikuje kroki z `main.py`. Czystszy refactor (Claude's Discretion do discuss-phase):

> **Option A (zalecane przez researchera):** Wyciągnąć helper `sphsim/cli/main.py::_run_single(args, K1, params, raw_strategy_fn) -> dict` (pure function, no I/O — bez `write_report` i bez `print`). Single-run main woła `_run_single` + `write_report`; batch woła N× `_run_single` + `write_batch_report`. **Mała refaktoryzacja, izoluje single-run logic od I/O — dobra dla maintenance.**
>
> **Option B:** Duplikacja kodu — `run_batch` ma własną pętlę z SPHSimulator. Szybsze do napisania, ale każda zmiana single-run musi być zsynchronizowana w obu miejscach.

Researcher rekomenduje **Option A** — koszt refactoru jest niski (~20 linii ekstrakcji), zysk wieczny (jedna definicja "run one sim", używana przez batch + single + przyszłe ficzery).

### A.2 — Co już dostarcza `SPHSimulator.run()` per seed

[VERIFIED — `sphsim/core/simulator.py:162-175`]

5 KPI wymaganych dla SC#2 są **dostępne bezpośrednio w returned dict**:

| KPI | Klucz w `res` | Typ | Phase 7 użycie |
|-----|---------------|-----|----------------|
| `avg_val_last100` | `res['avg_val_last100']` | float | Per-seed row + boxplot panel 1 + baseline-beating verdict |
| `cum_val_total` | `res['cum_val_total']` | float | Per-seed row + boxplot panel 2 |
| `avg_net_profit` | `res['avg_net_profit']` | float | Per-seed row + boxplot panel 3 |
| `delivery_ratio` | `res['delivery_ratio']` | float | Per-seed row + boxplot panel 4 |
| `avg_providers_l100` | `res['avg_providers_l100']` | float | Per-seed row + boxplot panel 5 |

**ŻADNE** dodatkowe dane z `res` nie są potrzebne dla batchowego raportu — `history`, `devices`, `ic_per_phase`, `veto_per_phase` są ignorowane (te są per-seed dataloady; batch agreguje tylko 5 skalarnych KPI). To upraszcza pickling/memory — `run_batch` może natychmiast po `sim.run()` wyrzucić wszystko poza 5-elementowym dict per seed.

### A.3 — Determinizm i izolacja per seed

**Każdy `SPHSimulator(seed=S)` woła `random.seed(S)` w `__init__` (verbatim `simulator.py:14`).** To jest **globalna stdlib `random`** — nie per-instance `random.Random(S)`. Implikacje:

- ✅ **Determinizm sekwencyjny:** seed=1 zawsze daje ten sam `res` (regardless of preceding seeds), bo `random.seed(1)` jest unconditionalny reset w `__init__`. [VERIFIED przez Phase 1 regression `8/8 PASS` + ostatni live probe.]
- ✅ **Nie ma "wycieku stanu" między runami w sequential batch** — każdy `SPHSimulator(seed=S)` reseeduje przed pętlą cykli.
- ⚠️ **Strategie używają tej samej globalnej `random.*`:** `naive.py:9`, `adaptive.py:19`, `phase_prob.py:12` wszystkie czytają `random.random()`. Bo seed jest zresetowany w `__init__`, strategy `random.*` calls są deterministyczne dla tego samego seeda — ALE jeśli strategia importuje cokolwiek co woła `random.*` przy `import time`, to **może być przejaw stanu**. [VERIFIED: żaden plik strategii nie woła `random.*` na top-level — tylko wewnątrz funkcji. Safe.]
- ⚠️ **`wrap_with_agent(strategy_fn, expected_P)`** — closure, sama nie wywołuje `random.*` (deterministyczne wyliczenia z `dev`, `l`, `phi`, `kappa`, `rho`, `h`, `p`). [VERIFIED `sphsim/agent/rational.py`.]
- ⚠️ **Jeśli kiedyś strategia użyje `numpy.random.*`**, Phase 7 musi też dodać `np.random.seed(S)` (na razie ZERO strategii to robi — verified `grep -rn "numpy\.random\|np\.random" sphsim/`).

**Konkluzja:** Sequential batch JEST DETERMINISTIC. Te same seedy w tej samej kolejności → bit-identyczne KPI per seed → bit-identyczna agregacja. To jest WAŻNY invariant testowalny (test "same seed list twice → byte-identical numerical results").

### A.4 — REPL command registry (jak wszywać `/batch`)

[VERIFIED — `sphsim/cli/repl.py:55-87` (cmd.Cmd subclass z `do_*` methodami)]

REPL używa **stdlib `cmd.Cmd`** — komendy są zwykłymi metodami `do_<nazwa>(self, arg)`. Dodanie `/batch`:

1. Dodaj metodę `def do_batch(self, arg):` w `SPHShell` — pattern verbatim jak `do_compare` (`repl.py:237-312`).
2. Dodaj jeden wiersz do `do_help` (`repl.py:62-71`) — analogicznie jak `compare`.

**Format komendy w REPL:** `batch <strategia> [--seeds N|list] [param=wartość ...]` — analogicznie do `compare`. Bo REPL używa `arg.split()` na whitespace, parser seedów dostaje token jako string i wywołuje ten sam `_parse_seeds_list` converter co CLI (single source of truth).

**Komendy REPL używają args-like Namespace** (`fake_args` w `do_run`/`do_compare`) — batch musi zbudować identyczny fake_args z DEFAULT_* env params + mutowanym `seed` per pętla, lub przekazać listę seedów jako extra-arg. Researcher rekomenduje: `fake_args` ma jeden default `seed=42` + lista `seeds_to_run` parametr do `run_batch()` (orkiestrator nadpisuje per pętla).

### A.5 — CLI argparse (jak wszywać `--batch --seeds`)

[VERIFIED — `sphsim/cli/args.py:72-125`]

Argparse parser ma już **dwie mutex grupy**:
- **Top-level mutex (required=True):** `--interactive` | `--strategy` | `--custom` (line 78).
- **Post-parse mutex (manual, line 121-124):** `--compare-agent` + `--no-agent` oraz `--compare-agent` + `--interactive`.

Phase 7 dodaje:

| Flaga | Type | Default | Mutex z |
|-------|------|---------|---------|
| `--batch` | `action='store_true'` | False | Nie podaje się explicitly; **post-parse mutex** z `--interactive`, `--compare-agent`, `--custom` (researcher: zostawić `--custom + --batch` na razie obsługiwane — ten przypadek jest sensowny "uruchom custom strategy na 10 seedach") |
| `--seeds` | custom converter `_parse_seeds_list` | None | Wymagane gdy `--batch`, ignorowane bez |

Post-parse logic:
```python
if args.batch and args.compare_agent:
    p.error("Flagi --batch i --compare-agent są wzajemnie wykluczające.")
if args.batch and args.interactive:
    p.error("Flaga --batch nie działa w trybie --interactive (użyj komendy `batch` w REPL).")
if args.batch and args.seeds is None:
    p.error("Flaga --batch wymaga --seeds N lub --seeds lista (np. 1,5,42).")
if args.seeds is not None and not args.batch:
    p.error("Flaga --seeds wymaga --batch.")
```

**Konwerter `_parse_seeds_list`:** Polish errors, pattern verbatim z `_parse_phi_list` (`args.py:32-49`). Szczegóły grammar w §B.3.

### A.6 — Phase 6 report writer — czy daje się reusować?

[VERIFIED — `sphsim/report/__init__.py:79-153` + `sphsim/report/markdown.py:37-65`]

**`write_report(args, res, params, K1, *, mode)`** jest zaprojektowany pod single-run (`mode='single'` lub `'compare'`). Phase 7 NIE PODŁĄCZA się do tego entrypointu — zamiast tego dodaje **nowy entrypoint** `sphsim/report/__init__.py::write_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list) -> Path | None` (symetryczny w API, ale inna sygnatura — bierze listę dictów zamiast pojedynczego).

**Powody NIE-reusowania `write_report`:**

1. `render_report` w `markdown.py:37` produkuje **7-sekcyjny** raport (Title / Konfiguracja / Strategia / KPI / Decyzje / Wykresy / Baseline + opt. Compare) ze SCALARNYM `res` dictem. Batch ma INNY layout — Title / Konfiguracja / Strategia / Per-seed table / Aggregate stats / Boxplot / Baseline-beating verdict.
2. Phase 6 `plot_decision_distribution` i `plot_kpi_timeseries` są dla single run — batch ma inny PNG (`batch_aggregate.png`). Reuse byłby `if mode == 'batch': skip these plots; render different one` — bardziej rozproszony niż czysta separacja.
3. `_render_decision_table` używa `ic_per_phase` / `veto_per_phase` — batch je odrzuca (per-seed scalary tylko).

**Co Phase 7 REUSUJE z Phase 6:**

| Obiekt z Phase 6 | Phase 7 reuse |
|------------------|---------------|
| `format_config_header(args, K0, K1, phi, rho)` z `sphsim/cli/output.py:31` | **TAK** — Sekcja 1 (Konfiguracja środowiska) verbatim |
| `BASELINE_PATH` constant z `sphsim/report/markdown.py:21-25` | **TAK** — single source of truth dla baseline JSON, ten sam plik |
| `_KPI_ROWS` tuple z `sphsim/report/markdown.py:28-34` | **TAK** — porządek 5 KPI + format strings + cel-labels |
| `_timestamp()` helper z `sphsim/report/__init__.py:35` | **TAK** — fs-safe Windows timestamp |
| `_resolve_report_dir(base)` helper z `sphsim/report/__init__.py:40` | **TAK** — generic, działa też dla `./reports/batch_<ts>/` (jedyna zmiana: base path) |
| Matplotlib Agg backend setup + font fallback w `sphsim/report/plots.py:13-19` | **TAK** — moduł już ma; `plot_batch_aggregate` dorzucany do tego pliku dziedziczy setup |
| Exception isolation pattern (`try: ... except: print to stderr; return None`) | **TAK** — `write_batch_report` ma identyczną otoczkę |
| `SPHSIM_NO_REPORT=1` opt-out | **TAK** — Phase 7 dziedziczy bez zmian; testy NIE śmiecą |

**Co Phase 7 DODAJE:**

1. `sphsim/report/batch_markdown.py` — nowy moduł z `render_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list) -> str`. Pure function (Phase 6 pattern).
2. `sphsim/report/plots.py::plot_batch_aggregate(per_seed_kpis, path)` — nowa funkcja w istniejącym pliku.
3. `sphsim/report/__init__.py::write_batch_report` — nowy entry-point obok `write_report`.

---

## Section B: Seed-list parsing (BATCH-01)

### B.3 — Recommended grammar

Custom argparse converter w `sphsim/cli/args.py`:

```python
def _parse_seeds_list(s: str) -> list[int]:
    """Konwertuje '--seeds N' (1..N) lub '--seeds n1,n2,...' (jawna lista) na list[int] (BATCH-01).

    Grammar (strict v1):
        - Pojedynczy dodatni integer N → list(range(1, N+1))   # N seedów: 1, 2, ..., N
        - Przecinkowo-rozdzielona lista dodatnich integerów → dedup + preserve order

    Reject:
        - 0, ujemne integerry → ArgumentTypeError
        - Pusty string → ArgumentTypeError
        - Non-integerry (np. '1.5', 'abc') → ArgumentTypeError
        - Range syntax '1..10' → ArgumentTypeError (deferred do v2)

    Args:
        s: surowy string z CLI / REPL.

    Returns:
        list[int] gwarantowanie niepustą, z elementami > 0, posortowaną w pierwotnym porządku
        wejścia (dla pojedynczego N: rosnąco 1..N).

    Raises:
        argparse.ArgumentTypeError z polskim komunikatem.
    """
    s = s.strip()
    if not s:
        raise argparse.ArgumentTypeError(
            "Pusta wartość --seeds. Podaj N (np. --seeds 10) lub listę (np. --seeds 1,5,42).")
    if ',' in s:
        # lista jawnych seedów
        try:
            raw = [int(x.strip()) for x in s.split(',')]
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Nieprawidłowy format --seeds: '{s}'. Oczekiwano listy integerów (np. 1,5,42).")
        if any(v <= 0 for v in raw):
            raise argparse.ArgumentTypeError(
                f"--seeds: wszystkie wartości muszą być dodatnie (> 0); podano: {raw}.")
        # dedup z preserve order
        seen = set()
        result = []
        for v in raw:
            if v not in seen:
                seen.add(v)
                result.append(v)
        return result
    else:
        # pojedynczy integer N → 1..N
        try:
            n = int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Nieprawidłowy format --seeds: '{s}'. "
                "Oczekiwano N (np. --seeds 10) lub listy (np. --seeds 1,5,42).")
        if n <= 0:
            raise argparse.ArgumentTypeError(
                f"--seeds: N musi być dodatnie (> 0); podano: {n}.")
        return list(range(1, n + 1))
```

**Behavioral table:**

| Input | Result | Reason |
|-------|--------|--------|
| `--seeds 10` | `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]` | Single N → range 1..N |
| `--seeds 1,5,42,100` | `[1, 5, 42, 100]` | Explicit list, dedup, preserve order |
| `--seeds 42` | `[42]` | Single integer = list o jednym elemencie (N=1 edge case, agregat = "n/a" — §D.8) |
| `--seeds 1,1,2,1` | `[1, 2]` | Dedup z preserve first occurrence |
| `--seeds 0` | ArgumentTypeError | Reject — `random.seed(0)` jest valid, ale stylistycznie disrupting; jasny błąd > silent acceptance |
| `--seeds -5` | ArgumentTypeError | Reject — ujemne |
| `--seeds ""` | ArgumentTypeError | Reject — pusty string |
| `--seeds 1,5,abc` | ArgumentTypeError | Reject — `int('abc')` raise ValueError |
| `--seeds 1..10` | ArgumentTypeError | Reject — range syntax NIE wspierany w v1 (deferred) |
| `--seeds 1.5` | ArgumentTypeError | Reject — `int('1.5')` raise ValueError |

Researcher rekomenduje TĘ grammar. Jest **konserwatywna** (rzuca błąd zamiast cichego accept dla 0/duplikatów), **eksplicytna** (nie wprowadza nowej składni `1..10`), i **pomocna w testach** (testowanie wszystkich 10 przypadków → ~10 unit testów `TestSeedsParser`).

---

## Section C: CLI/REPL integration (BATCH-01)

### C.4 — CLI args + main.py wiring

`sphsim/cli/args.py` — dodaj 2 linie do `parse_args()`:
```python
p.add_argument('--batch', action='store_true',
               help='Tryb batch — uruchom strategię N razy na różnych seedach (wymaga --seeds)')
p.add_argument('--seeds', type=_parse_seeds_list, default=None, metavar='N|lista',
               help='Lista seedów: N (1..N) lub jawna (1,5,42). Działa tylko z --batch.')
```

+ 4 linie post-parse mutex checks (zobacz §A.5).

`sphsim/cli/main.py` — dodaj **early branch przed compare-agent branch w obu gałęziach (built-in i custom)**:

```python
# (d') Batch branch — early return, PRZED compare-agent i single-run.
if args.batch:
    from sphsim.batch import run_batch
    from sphsim.report import write_batch_report
    per_seed_results, aggregate = run_batch(args, raw_strategy_fn, params, K1)
    report_dir = write_batch_report(args, per_seed_results, aggregate, params, K1, args.seeds)
    if report_dir:
        print(f'Raport batchowy zapisany do: {report_dir}/report.md', file=sys.stderr)
    # Format na stdout — analogicznie do format_human/format_json, ale dla batchu.
    # Decyzja v1: print one-liner summary na stdout (mean, std, CI dla avg_val_last100 + werdykt baseline-beating).
    # JSON output dla batch — researcher rekomenduje DEFER do v2 (nie ma SC dla --json + --batch).
    print(format_batch_summary(args, aggregate, K1))  # NOWY helper w output.py
    return
```

**Pozycja branchu:** PRZED `compare_agent` check (lines 92-99 i 136-143) — żeby nawet jeśli ktoś poda `--batch --compare-agent` (już blocked w post-parse mutex), batch jest unconditionally pierwszy.

### C.5 — REPL command (`do_batch`)

`sphsim/cli/repl.py` — dodaj `do_batch` po `do_compare` (~80 nowych linii, pattern verbatim z `do_compare`):

```python
# ---- batch <name> --seeds N|list [k=v ...] (BATCH-01) ----
def do_batch(self, arg):
    """Uruchom strategię na wielu seedach: batch <nazwa> --seeds N|lista [param=wartość ...]"""
    tokens = arg.split()
    if not tokens:
        print("Użycie: batch <nazwa> --seeds N|lista [param=wartość ...]. "
              "Np.: batch naive --seeds 10  |  batch naive --seeds 1,5,42 zeta=0.75")
        return

    # Parsing: --seeds wartość, reszta = name + k=v tokeny
    seeds_value = None
    other_tokens = []
    i = 0
    while i < len(tokens):
        if tokens[i] == '--seeds' and i + 1 < len(tokens):
            seeds_value = tokens[i + 1]
            i += 2
        else:
            other_tokens.append(tokens[i])
            i += 1

    if seeds_value is None:
        print("Komenda `batch` wymaga --seeds N lub --seeds lista (np. --seeds 1,5,42).")
        return
    try:
        seeds_list = _parse_seeds_list(seeds_value)  # Reuse converter z args.py (import)
    except argparse.ArgumentTypeError as e:
        print(str(e))
        return
    if not other_tokens:
        print("Komenda `batch` wymaga nazwy strategii. Wpisz 'strategies' żeby zobaczyć dostępne.")
        return
    name, *kv_tokens = other_tokens

    if name not in STRATEGIES:
        available = ', '.join(STRATEGIES.keys())
        print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
        return

    # Dispatch namespace + meta load — pattern z do_compare
    ns = 'sphsim.strategies' if name in BUILTIN_STRATEGIES else 'sphsim.custom'
    mod = importlib.import_module(f'{ns}.{name}')
    meta = mod.STRATEGY_META
    try:
        params = parse_params_from_meta(kv_tokens, meta, name)
    except LoaderError as e:
        print(e.args[0])
        return

    # fake_args dla orkiestratora — seed nadpisywany per loop iteration w run_batch.
    fake_args = argparse.Namespace(
        strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
        kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
        phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window',
        seed=42,  # placeholder — overridden per loop iter w run_batch
        json=False, compare_agent=False, batch=True, seeds=seeds_list,
        expected_P=params.get('expected_P', DEFAULT_K0),
    )

    from sphsim.batch import run_batch
    raw_strategy_fn = STRATEGIES[name]
    per_seed_results, aggregate = run_batch(fake_args, raw_strategy_fn, params, DEFAULT_K1)

    report_dir = write_batch_report(fake_args, per_seed_results, aggregate, params,
                                     DEFAULT_K1, seeds_list)
    if report_dir:
        print(f'Raport batchowy zapisany do: {report_dir}/report.md', file=sys.stderr)
    print(format_batch_summary(fake_args, aggregate, DEFAULT_K1))
```

I jedno dodanie do `do_help`:
```python
print("  batch <nazwa> --seeds N|lista [k=v ...] — Uruchom strategię na wielu seedach (agregat statystyczny).")
```

**REPL fake_args invariants** (Pitfall 2 z Phase 6 — nie powtarzać błędu):
- WSZYSTKIE atrybuty których używa `write_batch_report` / `format_config_header` muszą być na fake_args. Lista (researcher zweryfikował przeciwko Phase 6 markdown.py + Phase 7 batch_markdown.py dryrun): `strategy, nU, nSUS, T, kappa, alpha, verbose, no_agent, phi, rho, K0, valuation, seed, json, compare_agent, batch, seeds, expected_P`.
- Bez `expected_P` test `do_batch naive zeta=0.75` crashuje na wrap_with_agent — to było już złamane w Phase 4, naprawione w Phase 5. Researcher zaznacza — DODAJ `expected_P` do fake_args.

---

## Section D: Statistical aggregation (BATCH-02)

### D.6 — Stats module design

`sphsim/batch/stats.py`:

```python
"""Phase 7: Statystyki agregatu batchowego (BATCH-02).

Public surface:
    - aggregate_kpis(per_seed_kpis: list[dict[str, float]]) -> dict[str, AggregateStat]

AggregateStat to dataclass z polami: mean, std, min, max, ci_lower, ci_upper, n.
Dla N=1: std=0.0, ci_lower=mean, ci_upper=mean (degenerate — markdown renderer
serializuje to jako "n/a" string w tabeli).
Dla N>=2: scipy.stats.t.interval(0.95, df=N-1, loc=mean, scale=sem).
"""
from dataclasses import dataclass
from typing import Optional
import numpy as np
import scipy.stats as st


KPIS = ('avg_val_last100', 'cum_val_total', 'avg_net_profit',
        'delivery_ratio', 'avg_providers_l100')


@dataclass
class AggregateStat:
    mean: float
    std: float           # ddof=1 (sample std)
    min: float
    max: float
    ci_lower: Optional[float]  # None gdy N=1
    ci_upper: Optional[float]  # None gdy N=1
    n: int

    def ci_str(self, fmt='{:.2f}') -> str:
        """Renderuje CI jako string '(lower, upper)' lub 'n/a (N=1)'."""
        if self.ci_lower is None or self.ci_upper is None:
            return f'n/a (N={self.n})'
        return f'({fmt.format(self.ci_lower)}, {fmt.format(self.ci_upper)})'


def aggregate_kpis(per_seed_kpis):
    """Liczy mean/std/min/max/95% CI dla każdego z 5 KPI (BATCH-02).

    Args:
        per_seed_kpis: list[dict] gdzie każdy dict ma 5 kluczy z KPIS i wartości float.

    Returns:
        dict[str, AggregateStat] dla każdego klucza w KPIS.

    Edge cases:
        - N=0: ValueError (orkiestrator powinien filtrować empty input wcześniej).
        - N=1: ci_lower=ci_upper=None, std=0.0; mean=min=max=jedyna wartość.
        - N>=2: scipy.stats.t.interval(0.95, df=N-1, loc=mean, scale=sem).

    Notes:
        std używa ddof=1 (sample std, nie population std) — to standard dla próbki.
        scipy.stats.t.interval CITED: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html
    """
    n = len(per_seed_kpis)
    if n == 0:
        raise ValueError("aggregate_kpis: pusta lista — nic do agregowania.")

    result = {}
    for kpi in KPIS:
        values = np.array([d[kpi] for d in per_seed_kpis], dtype=float)
        mean = float(values.mean())
        # ddof=1: sample std. Dla N=1, np.std(ddof=1) → nan (division by zero).
        # Handluemy jawnie:
        if n == 1:
            std = 0.0
            ci_lower = None
            ci_upper = None
        else:
            std = float(values.std(ddof=1))
            sem = std / np.sqrt(n)
            # scipy.stats.t.interval(confidence, df, loc, scale) zwraca (lower, upper).
            ci_lower_np, ci_upper_np = st.t.interval(0.95, df=n - 1, loc=mean, scale=sem)
            ci_lower = float(ci_lower_np)
            ci_upper = float(ci_upper_np)
        result[kpi] = AggregateStat(
            mean=mean, std=std, min=float(values.min()), max=float(values.max()),
            ci_lower=ci_lower, ci_upper=ci_upper, n=n,
        )
    return result
```

### D.7 — Library choice rationale

**scipy.stats.t.interval VS bootstrap:**

| Aspekt | t-Student (rekomendacja) | Bootstrap |
|--------|--------------------------|-----------|
| Złożoność implementacji | ~3 linie kodu (`scipy.stats.t.interval`) | ~30 linii (resampling + percentile) |
| Założenia | Normalność próbki | Brak — non-parametric |
| Walidność dla N=10 | ✓ Klasyczna konstrukcja dla małych N | ✓ Działa, ale dla N=10 percentile estimates są szumne |
| Dydaktyka | Standard w podręcznikach statystyki — pasuje do projektu akademickiego (Konorski, MPE) | Wymaga dodatkowego wyjaśnienia |
| Verified dependency | `scipy 1.16.3` zainstalowany [VERIFIED] | `scipy` ma `scipy.stats.bootstrap` — TEŻ działa |
| Performance | O(1) — formuła zamknięta | O(B·N) gdzie B≈1000 resamples — 10k operacji ale wciąż <1ms |

Researcher rekomenduje **t-Student** dla v1 — najprostszy, najczytelniejszy w raporcie ("CI 95%: (90.21, 93.78) — przedział oparty o rozkład t-Studenta z df=N-1"), brak hiperparametrów (bootstrap wymaga `n_resamples`, `method='percentile'` vs `'BCa'` etc).

**KPI normality concern**: 5 KPI są agregowane z 1000-cyklowej symulacji per seed. Każdy KPI to faktycznie funkcja sumy lub średniej tysięcy obserwacji — Central Limit Theorem aplikuje, więc rozkład per-seed KPI **JEST** approximately normal dla rozsądnych T. Researcher rekomenduje **t-CI bez dodatkowego testu normalności** w v1 (Shapiro-Wilk byłby overkill dydaktyczny dla N=10).

[CITED: scipy.stats.t.interval docs — https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html — "confidence interval with equal areas around the median"; df = degrees of freedom = N-1; loc = sample mean; scale = sample SEM = std/sqrt(N).]

### D.8 — N=1 edge case handling

[VERIFIED runtime — `np.std([42.0], ddof=1)` zwraca `nan` z `RuntimeWarning: Degrees of freedom <= 0 for slice`.]

Trzeba **jawnie** sprawdzić `n == 1` PRZED wołaniem `values.std(ddof=1)` lub `scipy.stats.t.interval`. Researcher rekomenduje:

- `std = 0.0` (single value — degenerate sample, brak zmienności)
- `ci_lower = ci_upper = None` w `AggregateStat` (markdown serializuje jako `n/a (N=1)`)
- Baseline-beating verdict dla N=1: porównaj tylko mean (czyli pojedynczą wartość) z baseline `avg_val_last100 = 92`; **NIE** używaj CI (bo go nie ma).
- **NIE** crashuj — N=1 jest legalnym wejściem (`--seeds 42`).

Researcher proponuje TEST: `TestStatsN1` weryfikujący że `aggregate_kpis([{'avg_val_last100': 91.5, ...}])` zwraca `AggregateStat(mean=91.5, std=0.0, min=91.5, max=91.5, ci_lower=None, ci_upper=None, n=1)` BEZ exception/warning.

---

## Section E: Batch report markdown (BATCH-03)

### E.9 — `sphsim/report/batch_markdown.py` design

```python
"""Phase 7: Generator raportu MD dla trybu batch (BATCH-03).

Pure function — `render_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list) -> str`.
Sekcje (kolejność load-bearing, testy assertują):

  1. Title — `# Raport batchowy SPH — <strategia> ({ts})`
  2. Konfiguracja środowiska (REUSE format_config_header z output.py)
  3. Strategia i parametry + tryb agenta + liczba seedów
  4. Wyniki per seed — tabela N×6 (seed + 5 KPI)
  5. Agregat statystyczny — tabela 5 KPI × 7 kolumn (KPI / mean / std / min / max / 95% CI / N)
  6. Wykresy — link do batch_aggregate.png
  7. Werdykt baseline-beating — czy lower 95% CI dla avg_val_last100 > 92.0

Polish-language convention zachowana z Phase 6 (PROJECT.md constraint).
"""
import json
from datetime import datetime
from pathlib import Path

from sphsim.cli.output import format_config_header
# Reuse Phase 6 baseline location — single source of truth.
from sphsim.report.markdown import BASELINE_PATH, _KPI_ROWS


def render_batch_report(args, per_seed_results, aggregate, params, K1,
                        seeds_list) -> str:
    sections = [
        _render_title(args, len(seeds_list)),
        format_config_header(args, args.K0, K1, args.phi, args.rho),
        _render_strategy_params(args, params, seeds_list),
        _render_per_seed_table(per_seed_results, seeds_list),
        _render_aggregate_table(aggregate),
        _render_boxplot_section(),
        _render_baseline_beating(aggregate),
    ]
    return '\n\n'.join(sections) + '\n'


def _render_title(args, n_seeds):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f'# Raport batchowy SPH — `{args.strategy}` × {n_seeds} seedów ({ts})'


def _render_strategy_params(args, params, seeds_list):
    lines = [
        '## Strategia i parametry',
        '',
        '| Parametr | Wartość |',
        '|----------|---------|',
        f'| Strategia | `{args.strategy}` |',
    ]
    for k, v in (params or {}).items():
        if v is not None:
            lines.append(f'| {k} | {v} |')
    if getattr(args, 'no_agent', False):
        lines.append('| Tryb agenta | wyłączony (`--no-agent`) |')
    else:
        lines.append('| Tryb agenta | włączony (domyślnie) |')
    lines.append(f'| Liczba seedów (N) | {len(seeds_list)} |')
    lines.append(f'| Lista seedów | {", ".join(str(s) for s in seeds_list)} |')
    return '\n'.join(lines)


def _render_per_seed_table(per_seed_results, seeds_list):
    lines = [
        '## Wyniki per seed',
        '',
        '| Seed | avg_val_last100 | cum_val_total | avg_net_profit | delivery_ratio | avg_providers_l100 |',
        '|------|-----------------|---------------|----------------|----------------|--------------------|',
    ]
    for seed, res in zip(seeds_list, per_seed_results):
        lines.append(
            f'| {seed} '
            f'| {res["avg_val_last100"]:.2f} '
            f'| {res["cum_val_total"]:.1f} '
            f'| {res["avg_net_profit"]:+.4f} '
            f'| {res["delivery_ratio"]:.2%} '
            f'| {res["avg_providers_l100"]:.2f} |'
        )
    return '\n'.join(lines)


def _render_aggregate_table(aggregate):
    lines = [
        '## Agregat statystyczny',
        '',
        '| KPI | mean | std | min | max | 95% CI | N |',
        '|-----|------|-----|-----|-----|--------|---|',
    ]
    for key, fmt, _cel in _KPI_ROWS:
        stat = aggregate[key]
        if key == 'delivery_ratio':
            ci_str = stat.ci_str(fmt='{:.2%}')
            lines.append(
                f'| {key} | {stat.mean:.2%} | {stat.std:.2%} '
                f'| {stat.min:.2%} | {stat.max:.2%} | {ci_str} | {stat.n} |'
            )
        else:
            ci_str = stat.ci_str(fmt=fmt)
            lines.append(
                f'| {key} | {fmt.format(stat.mean)} | {fmt.format(stat.std)} '
                f'| {fmt.format(stat.min)} | {fmt.format(stat.max)} | {ci_str} | {stat.n} |'
            )
    return '\n'.join(lines)


def _render_boxplot_section():
    return ('## Wykresy\n\n'
            '![Box-ploty 5 KPI dla N seedów](batch_aggregate.png)')


def _render_baseline_beating(aggregate):
    """Werdykt SC#5: czy lower 95% CI dla avg_val_last100 > baseline (92.0)?"""
    try:
        baseline_raw = json.loads(BASELINE_PATH.read_text(encoding='utf-8'))
        baseline_val = baseline_raw['metrics']['avg_val_last100']
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        return (
            '## Werdykt: bije baseline?\n\n'
            f'*Baseline niedostępny ({type(e).__name__}) — werdykt pominięty.*'
        )

    stat = aggregate['avg_val_last100']
    lines = [
        '## Werdykt: bije baseline `naive --zeta 0.75`?',
        '',
        f'Baseline: `avg_val_last100 = {baseline_val:.2f}`.',
        '',
    ]

    if stat.ci_lower is None:
        # N=1 — porównaj tylko mean.
        verdict = '✓ TAK' if stat.mean > baseline_val else '✗ NIE'
        lines.append(f'**N=1** — brak CI. Pojedyncza wartość: `{stat.mean:.2f}`. '
                     f'Bije baseline (single-point): {verdict}')
    else:
        verdict = '✓ TAK' if stat.ci_lower > baseline_val else '✗ NIE'
        lines.append(
            f'95% CI dla avg_val_last100: `({stat.ci_lower:.2f}, {stat.ci_upper:.2f})`. '
            f'Lower bound CI **{"> " if stat.ci_lower > baseline_val else "≤ "}** {baseline_val:.2f} → '
            f'bije baseline: **{verdict}**.'
        )
    return '\n'.join(lines)
```

### E.10 — Per-seed table structure

5 KPI × N seedów = `N × 6` (1 kolumna seed + 5 kolumn KPI). Dla N=10 to 10 wierszy — jest manageable w MD. Dla N=100 byłoby przesadnie duże ale researcher rekomenduje **nie ograniczać** w v1 — user który chce N=100 świadomie podejmuje to ryzyko, MD renderery (GitHub/VSCode) radzą sobie z setkami wierszy.

### E.11 — Baseline-beating verdict source

[VERIFIED — `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` zawiera:]
```json
{ "metrics": { "avg_val_last100": 92.0, ... }, ... }
```

Phase 7 czyta **ten sam plik** co Phase 6 (single-run report) — `BASELINE_PATH` z `sphsim/report/markdown.py:21-25` jest importowany. To gwarantuje single source of truth + zero duplicacji.

**Nie regenerujemy baseline na żywo:**
- Koszt: 10 seedów × ~150 ms = ~1.5 s dodatkowo per batch — niewielkie ALE niepotrzebne.
- Komplikacja: jaki seed list użyć dla baseline? Jeśli tylko 1 seed (np. seed=42), nie ma CI; jeśli 10 — duplicate computation.
- Statyczny baseline = oracle. To jest GOOD pattern (Phase 1 Plan 01 — baseline jako committed fixture).

**Warning dla user'a:** Jeśli user override'uje `--phi`, `--rho`, `--K0`, `--valuation`, `--T`, `--nU`, baseline może nie pasować do bieżącej konfiguracji. Researcher rekomenduje DODAĆ disclaimer w sekcji werdyktu (analogicznie do Phase 6 `_render_baseline_comparison`): "*Baseline z domyślnej konfiguracji v1.0. Jeśli używasz override, porównanie jest poglądowe.*"

---

## Section F: Batch boxplot PNG (PLOT-04)

### F.12 — `plot_batch_aggregate` function design

Dodanie do `sphsim/report/plots.py` (NIE nowy plik — reuse setup):

```python
def plot_batch_aggregate(per_seed_kpis, path):
    """PLOT-04: 5 subplotów (1×5 grid) z box-plotami dla każdego z 5 KPI.

    Args:
        per_seed_kpis: list[dict[str, float]] — N dictów z 5 kluczami z KPIS.
        path: pathlib.Path | str — gdzie zapisać PNG.

    Side effects:
        Zapisuje PNG pod `path`. Zamyka figurę w finally (Pitfall 5 — matplotlib leak).

    Notes:
        5 subplotów (NIE jeden grouped boxplot) bo KPI mają drastycznie różne skale
        (avg_val_last100≈92, cum_val_total≈92000, delivery_ratio≈0.79, ...).
        Jedna Y-oś byłaby nieczytelna — albo by przygniotła małe KPI, albo by skompresowała duże.
    """
    if not per_seed_kpis:
        return

    KPI_LABELS = [
        ('avg_val_last100',     'avg_val_last100\n(waluacja, last 100)'),
        ('cum_val_total',       'cum_val_total\n(suma waluacji)'),
        ('avg_net_profit',      'avg_net_profit\n(zysk netto / urządzenie)'),
        ('delivery_ratio',      'delivery_ratio\n(% udanych)'),
        ('avg_providers_l100',  'avg_providers_l100\n(śr. dostawcy, last 100)'),
    ]

    fig, axes = plt.subplots(1, 5, figsize=(15, 4), dpi=120)
    try:
        for ax, (kpi_key, label) in zip(axes, KPI_LABELS):
            values = [d[kpi_key] for d in per_seed_kpis]
            ax.boxplot(values, vert=True, patch_artist=True,
                       boxprops=dict(facecolor='#90CAF9'),
                       medianprops=dict(color='#0D47A1', linewidth=2))
            ax.set_title(label, fontsize=10)
            ax.set_xticks([])
            ax.grid(axis='y', linestyle='--', alpha=0.4)
            # Y-axis percent format dla delivery_ratio
            if kpi_key == 'delivery_ratio':
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
        fig.suptitle(f'Box-ploty 5 KPI (N={len(per_seed_kpis)} seedów)', fontsize=12)
        fig.tight_layout()
        fig.savefig(path)
    finally:
        plt.close(fig)
```

### F.13 — Why 5 subplots, not 1 grouped boxplot

[VERIFIED data ranges z Phase 6 fixture `08-naive-zeta-0.75-baseline.json`:]

| KPI | Typical range | Magnitude |
|-----|---------------|-----------|
| `avg_val_last100` | 50..100 | 10² |
| `cum_val_total` | 50000..100000 | 10⁵ |
| `avg_net_profit` | -10..200 | 10² (z ujemnymi!) |
| `delivery_ratio` | 0..1 (procent) | 10⁰ |
| `avg_providers_l100` | 50..150 | 10² |

Pojedynczy boxplot z jedną Y-osią dla wszystkich 5 dałby kompresję `delivery_ratio` do niewidocznej linii i `cum_val_total` zdominowałoby ekran. Subplots z indywidualnymi Y-osiami są jedynym czytelnym rozwiązaniem.

**Alternatywa (deferred):** Normalize wartości do z-score per KPI i zrobić jeden grouped boxplot z metką "z-score". Researcher rejects — z-score komplikuje interpretację dla użytkownika akademickiego ("co znaczy z-score 1.5 dla cum_val_total?").

### F.14 — File location and link

Output: `./reports/batch_<ts>/batch_aggregate.png` (obok report.md). Link w MD (sekcja 6 raportu): `![Box-ploty 5 KPI dla N seedów](batch_aggregate.png)` — relatywna ścieżka identycznie jak Phase 6 PLOT-03.

---

## Section G: Parallelism — RECOMMENDED DEFERRED (out of scope v1)

### G.15 — Sequential timing measurement

[VERIFIED `/usr/bin/time -p` na `naive --zeta 0.75 --seed 42 --T 1000`:]
```
real 0.15
user 0.14
sys 0.00
```

~150 ms per single run, **including Python startup + sphsim package import time** (~80 ms of that). Actual `SPHSimulator(...).run()` body to ~60-80 ms.

Dla N=10 seedów w jednym Python procesie (jeden import-time + 10 `sim.run()` w pętli) ≈ **80 ms + 10×80 ms = 880 ms ≈ 1 sekunda**.

Dla N=100 seedów: ≈ 80 ms + 100×80 ms = **~8 sekund**. Wciąż akceptowalne dla projektu akademickiego — to mniej niż czas otwarcia raportu w VSCode.

### G.16 — Multiprocessing complications

Gdyby chcieć równoległości:
1. **Pickling strategy_fn:** `wrap_with_agent(strategy_fn, expected_P)` to closure. `multiprocessing.Pool` używa pickle do serializacji argumentów dla worker procesów. Pickling closures w Pythonie wymaga `dill` (third-party dep) lub refaktoryzacji wrap'a z closure → metoda klasy. **Niepotrzebny koszt złożoności dla N≤100.**
2. **Custom strategy import:** Phase 3 loader rejestruje custom strategie w `sys.modules['sphsim.custom.<name>']`. Worker procesy nie odziedziczają tego — trzeba by re-loadować z `args.custom` per worker. Komplikuje seed-list parser i CLI flow.
3. **Determinizm:** `random.seed(N)` jest globalny per process. W worker process'ie reseeding działa tak samo, ALE jeśli kolejność worker'ów nie jest stabilna, raport per-seed table może mieć inną kolejność niż lista seedów. Trzeba by sortować wyniki po seed wracając z pool.

**Researcher rekomenduje:** SEQUENTIAL only w v1. Documentation w `## Out of Scope`. Jeśli kiedyś N > 1000 staje się realnym use case'em, refactor w v2 ma jasny pattern: `concurrent.futures.ProcessPoolExecutor` z `partial(_run_single_with_seed, args)` jako map function.

### G.17 — Sequential implementation skeleton

```python
def run_batch(args, raw_strategy_fn, params, K1):
    """Sekwencyjnie uruchamia symulację dla każdego seeda w args.seeds.

    Returns:
        (per_seed_results, aggregate) gdzie:
            per_seed_results: list[dict[str, float]] — N elementów, każdy z 5 KPI.
            aggregate: dict[str, AggregateStat] — agregat 5 KPI.
    """
    from sphsim.batch.stats import aggregate_kpis, KPIS

    seeds = args.seeds  # już sparsowana lista[int] z _parse_seeds_list
    per_seed_results = []

    # Conditional wrap — analogicznie do main.py:147-148.
    strategy_fn = raw_strategy_fn
    if not args.no_agent:
        from sphsim.agent import wrap_with_agent
        strategy_fn = wrap_with_agent(raw_strategy_fn, args.expected_P)

    for seed in seeds:
        from sphsim.core.simulator import SPHSimulator
        from sphsim.config import DEFAULT_F
        sim = SPHSimulator(
            nU=args.nU, nSUS=args.nSUS, K0=args.K0, K1=K1,
            F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
            phi=args.phi, rho=args.rho, valuation_preset=args.valuation,
            strategy_fn=strategy_fn, params=params, seed=seed,
        )
        res = sim.run()
        # Wycinamy 5 KPI — odrzucamy history/devices/ic_per_phase (NIE potrzebne dla batchu).
        per_seed_results.append({k: res[k] for k in KPIS})

    aggregate = aggregate_kpis(per_seed_results)
    return per_seed_results, aggregate
```

---

## Section H: Common pitfalls

### Pitfall 1: matplotlib state leak between figures (PLOT-04)

**Co idzie nie tak:** Brakujące `plt.close(fig)` po `fig.savefig` powoduje że matplotlib trzyma figury w pamięci. Dla N=10 batch może to nie boleć, ale jeśli user uruchomi 100 batchy w jednym REPL session, pamięć rośnie.

**Dlaczego się zdarza:** Phase 6 zdefuzował dla `plot_decision_distribution` i `plot_kpi_timeseries` (close-in-finally). Phase 7 musi PRZEDŁUŻYĆ ten pattern do `plot_batch_aggregate` — **NIE pomijać**.

**Jak unikać:** `try: ... fig.savefig(path) finally: plt.close(fig)` — wzorzec verbatim z Phase 6 plots.py. Researcher dorzucił do skeletu w §F.12.

**Warning signs:** memory leak warning z pytest `RuntimeWarning: More than 20 figures have been opened`.

### Pitfall 2: REPL state contamination across `/batch` invocations

**Co idzie nie tak:** REPL `cmd.Cmd` instancja żyje przez całą sesję. Jeśli `do_batch` modyfikuje globalny stan (np. `STRATEGIES` dict, sys.modules), kolejne `/batch` mogą widzieć stale state.

**Dlaczego się zdarza:** `do_compare` (Phase 4) i `do_run` (Phase 3) NIE wprowadzają stanu — to były pure dispatchers. Ale Phase 7 `do_batch` ma trochę więcej state (parsing seedów, fake_args). Jeśli `seeds_list` zostaje zapisana w `self.last_batch_seeds` (nie powinna!), to się akumuluje.

**Jak unikać:** `do_batch` MUST być stateless — żadnych instance variables, każdy call rebuilduje fake_args od zera. Researcher zweryfikował szkielet w §C.5 — używa lokalnych zmiennych, nie `self.*`.

**Warning signs:** test `test_repl_two_batches_independent` — uruchom dwa `do_batch` w jednym REPL z różnymi seed listami; second invocation nie może widzieć pierwszego.

### Pitfall 3: Floating-point determinism if numpy version differs

**Co idzie nie tak:** `np.mean`, `np.std`, `scipy.stats.t.interval` używają BLAS/LAPACK internally. Różne wersje numpy mogą dawać minimalnie różne wyniki (~1e-15 precision). Testy które assertują exact equality mogą flake'ować na CI z innym numpy.

**Dlaczego się zdarza:** numpy 2.x BLAS może być inny niż numpy 1.x; macOS Accelerate vs Linux OpenBLAS to różne implementacje.

**Jak unikać:** Testy statystyk MUSZĄ używać `pytest.approx` (lub `unittest.assertAlmostEqual` z `delta=1e-6` / `places=4`). Researcher rekomenduje precision `places=4` — to wystarcza dla rendering raportu (KPI są zaokrąglane do 4 miejsc) i toleruje wszystkie sensowne BLAS variations.

**Warning signs:** CI flakes z `0.7931 != 0.79310000001`.

### Pitfall 4: `--no-agent` baseline semantics for SC #5

**Co idzie nie tak:** SC #5: "Batch report jasno wskazuje czy strategia bije baseline `naive --zeta 0.75`". Baseline jest computed z `--no-agent` (fixture json zawiera "naive --zeta 0.75 --no-agent" w semantyce v1.0 — co Phase 6 explicit oznaczyło w `_render_baseline_comparison` jako "Porównanie z baseline `naive --zeta 0.75 --no-agent`").

**Pytanie:** Czy batch który JEST `--no-agent` porównuje się ze WSZYSTKIM, ale batch który MA agenta — z czym?

**Researcher rekomenduje:** **Porównujemy zawsze z tym samym fixed baseline `naive --zeta 0.75 --no-agent`** (= avg_val_last100 = 92.0). To NIE jest "fair fight" (with-agent batch ma extra capability), ale jest:
- Konsystentne z Phase 6 (single-run report używa tego samego baseline).
- Jasne dydaktycznie — baseline jest stałą referencją, nie jest "negocjowane" per run.
- **Disclaimer** w raporcie: "*Baseline = `naive --zeta 0.75 --no-agent` (v1.0 default). Bieżący batch może używać agenta — różnica w avg_val_last100 może wynikać z lepszej strategii ORAZ z weto'wania.*"

**Warning signs:** Recenzent przedmiotu pyta "czy to fair comparison?" — odpowiedź w disclaimer.

### Pitfall 5: File path collisions if two batches run in same directory

**Co idzie nie tak:** Timestamp `YYYYMMDD-HHMMSS` ma 1-second resolution. Dwa batche w tym samym sekundzie → kolizja `./reports/batch_20260528-114920/` istnieje dwa razy.

**Dlaczego się zdarza:** User uruchamia szybko dwa REPL-owe `/batch` w 1-sec window, lub CI testuje dwa batche w pętli.

**Jak unikać:** Phase 6 `_resolve_report_dir` (`__init__.py:40-60`) **już to obsługuje** — retry z suffixem `-N` (`base/<ts>-2`, `<ts>-3`, ...). Phase 7 ten sam helper, tylko z innym `base=Path('reports') / f'batch_{ts}'`. **Researcher zweryfikował że pattern jest reusable** — w §A.6.

**Warning signs:** `FileExistsError` w teście który tworzy 2 batche w pętli.

### Pitfall 6: scipy/numpy NEW dependency — explicit signal

**Co idzie nie tak:** Phase 1-5 były stdlib only. Phase 6 dodał matplotlib (jako PROJECT.md Key Decision). Phase 7 dodaje **scipy + numpy** — chociaż numpy jest dependency matplotlib (Phase 6 już je sprowadzało), scipy jest **NOWE**.

**Czy jest dostępne?** [VERIFIED — `python3 -c "import scipy; print(scipy.__version__)"` → `1.16.3`. Lokalnie OK.]

**Co planner musi zrobić:**
- DODAĆ `requirements.txt` z `matplotlib`, `numpy`, `scipy` (researcher rekomenduje — Phase 6 to ZOSTAWIŁO na Phase 7 / discuss-phase) — to jest dobra okazja.
- LUB DODAĆ disclaimer w README że "Phase 7 wymaga `pip install scipy`" (mniej preferowane).

**Warning signs:** User na czystym systemie bez scipy uruchamia `--batch` → ImportError przy `from sphsim.batch.stats import aggregate_kpis`. Trzeba dla user-friendliness DODAĆ early-import check (researcher: opcjonalne).

### Pitfall 7: Custom strategy `expected_P` propagation in batch+REPL

**Co idzie nie tak:** REPL `do_batch` builduje `fake_args` z `expected_P=params.get('expected_P', DEFAULT_K0)`. Jeśli user wpisał `batch incentive --seeds 10 expected_P=150`, `params['expected_P']=150` poprzez `parse_params_from_meta`, i fake_args dostaje 150. To dobra ścieżka.

ALE — jeśli user wpisał `batch naive --seeds 10 zeta=0.75` (naive nie ma `expected_P` w meta), `params.get('expected_P', DEFAULT_K0)` zwraca 100. Czy to OK? **TAK** — agent używa default expected_P (zgodnie z Phase 4 D-54).

**Dlaczego to pitfall:** jeśli planner pomyli `expected_P` z `args.expected_P` (top-level CLI flag, default 100.0), dla REPL fake_args musi być świadomy że `expected_P` jest "z params jeśli istnieje, inaczej DEFAULT_K0=100". Phase 4 do_compare miał to samo i było złamane raz (T-04-13 mitigation). Researcher zaznacza by NIE powtarzać.

**Warning signs:** test `TestReplBatchExpectedP` — `batch incentive expected_P=200` produkuje raport z expected_P=200 w tabeli "Strategia i parametry".

---

## Section I: Code Examples (verified from Phase 6 + Phase 4 patterns)

### Pattern 1: Pure-function renderer (reuse Phase 6 markdown.py shape)

```python
# Source: sphsim/report/markdown.py:37-65 (Phase 6 verbatim)
def render_report(args, res, params, K1, *, mode='single') -> str:
    sections = [
        _render_title(args),
        format_config_header(args, args.K0, K1, args.phi, args.rho),
        _render_strategy_params(args, params),
        # ...
    ]
    return '\n\n'.join(sections) + '\n'
```

### Pattern 2: Orchestrator with exception isolation (reuse Phase 6 __init__.py shape)

```python
# Source: sphsim/report/__init__.py:79-153 (Phase 6 verbatim)
def write_report(args, res, params, K1, *, mode='single'):
    if os.environ.get('SPHSIM_NO_REPORT') == '1':
        return None
    try:
        report_dir = _resolve_report_dir()
        # plot 1, plot 2, markdown — each wrapped in try/except
        # ...
        return report_dir
    except Exception as e:
        print(f'[OSTRZEŻENIE] Raport: {e}', file=sys.stderr)
        return None
```

### Pattern 3: scipy 95% CI

```python
# Source: scipy docs — https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html
import scipy.stats as st
import numpy as np

values = np.array([91.5, 92.1, 91.8, ...])  # N samples
n = len(values)
mean = values.mean()
std = values.std(ddof=1)
sem = std / np.sqrt(n)
ci_lower, ci_upper = st.t.interval(0.95, df=n - 1, loc=mean, scale=sem)
```

### Pattern 4: Boxplot subplot grid

```python
# Source: matplotlib pyplot docs — verified Pattern from plot_kpi_timeseries (Phase 6 twin-axis is conceptually similar)
fig, axes = plt.subplots(1, 5, figsize=(15, 4), dpi=120)
try:
    for ax, (label, values) in zip(axes, kpi_data):
        ax.boxplot(values, vert=True, patch_artist=True)
        ax.set_title(label)
    fig.suptitle('Box-ploty 5 KPI')
    fig.tight_layout()
    fig.savefig(path)
finally:
    plt.close(fig)
```

---

## Section J: Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 95% confidence interval | Custom `mean ± 1.96 * std / sqrt(n)` (z-score, zakłada N→∞) | `scipy.stats.t.interval(0.95, df=N-1, loc=mean, scale=sem)` | t-Student jest poprawny dla małych N; 1.96 z-score jest aproksymacją dla N≥30 |
| Sample std | `sum((x - mean)**2)/n` (population std) | `numpy.std(values, ddof=1)` (sample std) | ddof=1 jest poprawne dla próbki; population std under-estymuje wariancję dla małego N |
| Boxplot from scratch | Custom matplotlib bars z manualną quartile calculation | `matplotlib.pyplot.boxplot(values)` | Wbudowany, obsługuje outliers (whiskers + fliers) zgodnie ze standardem |
| Seed list parser | Recursive descent / regex / split-with-conversion | `argparse.ArgumentTypeError` z `int()` cast + jawne walidacje | Pattern z `_parse_phi_list` — istnieje, działa, polski error |
| Mkdir collision retry | os.path.exists loop | Reuse `sphsim/report/__init__.py::_resolve_report_dir` | Phase 6 już to napisał, tested |
| Timestamp formatowanie | strftime ad-hoc | Reuse `_timestamp()` z Phase 6 | Single source of truth, fs-safe na Windows |

**Key insight:** Phase 6 wprowadził kilka helper funkcji (`_resolve_report_dir`, `_timestamp`, `format_config_header`, `BASELINE_PATH`) które są reusowalne dla Phase 7. Researcher zaznacza — IMPORTUJ je, nie kopiuj.

---

## Runtime State Inventory

Phase 7 nie jest rename/refactor/migration. **Sekcja SKIPPED** — greenfield (dodaje nowy pakiet + nowy entrypoint).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | wszystko | ✓ | 3.14.3 | — |
| numpy | sphsim/batch/stats.py | ✓ | 2.3.5 | — |
| scipy | sphsim/batch/stats.py | ✓ | 1.16.3 | — |
| matplotlib | sphsim/report/plots.py (existing + new boxplot) | ✓ | 3.10.7 | — |
| pytest | testy (opt) | NIE sprawdzono | — | `unittest` (stdlib, zgodne z Phases 1-6) |

**Missing dependencies with no fallback:** None — wszystko zainstalowane lokalnie.

**Missing dependencies with fallback:** None — Phase 7 nie wprowadza nowych deps poza tymi które już są (scipy + numpy są instalowane razem z matplotlib via pip).

**Recommended action (Claude's Discretion):** DODAĆ `requirements.txt` w Phase 7 z trzema linijkami (`matplotlib`, `numpy`, `scipy`). Phase 6 zostawiło to "do Phase 7 lub discuss-phase". Researcher: dobry moment.

---

## State of the Art

| Old Approach (v1.0) | Current Approach (v1.1 / Phase 7) | When Changed | Impact |
|---------------------|------------------------------------|--------------|--------|
| Pojedyncze uruchomienie `--seed 42` | Lista seedów `--batch --seeds 10` | Phase 7 | User dostaje rozkład statystyczny zamiast pojedynczego pomiaru |
| Wynik = jeden raport MD | Wynik = jeden raport MD z agregatem statystycznym + box-ploty | Phase 7 | Naukowa robustność — single-seed result jest noise sample, batch redukuje |
| Baseline compare = single value | Baseline compare = lower 95% CI > baseline | Phase 7 | Statystycznie zachowawcze — wymaga istotnej przewagi, nie szumu |
| Stdlib only (Phase 1-5) → +matplotlib (Phase 6) | +scipy +numpy (Phase 7, choć numpy już via matplotlib) | Phase 7 | Pełny "scientific Python" stack |

**Deprecated/outdated:** None. Phase 7 dodaje warstwę; nic nie usuwa.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | scipy 1.16.3 jest "stable enough" — `scipy.stats.t.interval` signature nie zmieni się | §D.6, §D.7 | Niski — `t.interval` API jest w scipy od >10 lat |
| A2 | Per-seed KPI są approximately normalne (CLT dla T=1000) — t-CI jest valid | §D.7 | Niski-średni — dla `delivery_ratio` blisko 0 lub 1 może łamać normalność, ale dla domyślnego env to nie problem |
| A3 | 1 sekunda per N=10 batch jest "fast enough" — nie potrzebujemy parallelism | §G.15 | Niski — projekt akademicki, user pracuje w REPL, 1s jest niewidoczna |
| A4 | Baseline = 92.0 (static fixture) jest "fair reference" dla wszystkich batch trybów | Pitfall 4 | Średni — recenzent może zakwestionować "fairness" — disclaimer mitigates |
| A5 | 5-subplot boxplot jest czytelniejszy niż single grouped boxplot | §F.13 | Niski — alternatywa (z-score normalization) jest gorsza dydaktycznie |
| A6 | Refactor Option A (`_run_single` helper z `main.py`) jest preferowany nad duplikacją | §A.1 Option A vs B | Niski — discuss-phase potwierdzi |
| A7 | Output dir `./reports/batch_<ts>/` (prefix `batch_`) — researcher zaproponował, planner potwierdzi | §A.6, User Constraints | Niski — kosmetyczna decyzja |
| A8 | Seed list grammar v1 odrzuca range syntax `1..10`, deduplikuje, odrzuca 0/ujemne | §B.3 | Niski — można rozszerzyć w v2 bez breaking change |
| A9 | `--batch + --custom` powinno działać (nie mutex) — batch dla custom strategii | §A.5 | Niski — researcher rekomenduje "nie blokować bez powodu" |

**Jeśli ta tabela jest pusta:** nieaktualne — 9 assumed claims listed; planner / discuss-phase potwierdzi po kolei.

---

## Open Questions

1. **Czy `--json` output dla `--batch` jest in-scope?**
   - Co wiemy: SC nie wspomina `--json` dla batchu. Phase 6 SC#6 wymaga że `--json` zachowuje v1.0 compat — to dotyczy single-run.
   - Co niejasne: Czy `--batch --json` powinno wypisać JSON z `{per_seed: [...], aggregate: {...}}`?
   - Rekomendacja: **DEFER** do v2. v1 — `--batch` zawsze human-readable na stdout (one-liner summary) + raport MD. Jeśli user chce JSON, czyta `report.md` lub plany v2.

2. **Czy `requirements.txt` powinien zostać utworzony w Phase 7?**
   - Co wiemy: Phase 6 RESEARCH zostawił tę decyzję — "może być dodany jako opcjonalny artefakt dla CI".
   - Co niejasne: Czy planner Phase 7 dodaje czy zostawia na milestone close?
   - Rekomendacja: **DODAĆ w Phase 7** — to dobry moment, scipy jest "nowe", warto explicite.

3. **Czy batch w trybie `--compare-agent` ma sens?**
   - Co wiemy: SC nic nie mówi. Mutex jest sugerowany przez researchera.
   - Co niejasne: Czy by miało dydaktyczną wartość (batch z agentem vs batch bez agenta, agregaty obu z delta)?
   - Rekomendacja: **DEFER** do v2 — researcher proponuje mutex w v1, user może uruchomić DWA batche.

4. **Czy lista seedów powinna być sortowana w raporcie?**
   - Co wiemy: User wpisuje `--seeds 5,1,42` — researcher rekomenduje preserve order.
   - Co niejasne: Czy "preserve order" jest intuicyjne, czy by sortować rosnąco w tabeli per-seed?
   - Rekomendacja: **Preserve user order** w tabeli per-seed (user wpisał `5,1,42` — widzi wiersze w tej kolejności). Agregat statystyczny jest order-invariant.

---

## Security Domain

Phase 7 nie wprowadza nowych powierzchni ataku. Custom strategy loader (Phase 3) już istnieje i ma swój threat model (`importlib` ładuje arbitralny Python — świadoma decyzja PROJECT.md). Phase 7 reusuje ten loader.

**ASVS:** N/A — projekt akademicki, lokalny, single-user.

`security_enforcement` w `.planning/config.json` NIE jest ustawiony — researcher omija (config nie blokuje, ale też nie wymaga).

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Python `unittest` (stdlib, zgodne z Phases 1-6) |
| Config file | none — `python -m unittest discover tests/` |
| Quick run command | `SPHSIM_NO_REPORT=1 python -m unittest tests/test_batch.py tests/test_batch_stats.py tests/test_batch_report.py -v` |
| Full suite command | `SPHSIM_NO_REPORT=1 python -m unittest discover tests/ -v` |
| Estimated runtime | ~3 s (quick) / ~20 s (full — tests inkluduje 172 z Phase 6 + ~15 nowych Phase 7) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| BATCH-01 | `--seeds 10` parsuje do `[1..10]` | unit | `python -m unittest tests.test_batch.TestSeedsParser.test_single_n` | ❌ Wave 0 |
| BATCH-01 | `--seeds 1,5,42` parsuje do `[1,5,42]` | unit | `python -m unittest tests.test_batch.TestSeedsParser.test_list` | ❌ Wave 0 |
| BATCH-01 | `--seeds 0` rzuca ArgumentTypeError | unit | `python -m unittest tests.test_batch.TestSeedsParser.test_reject_zero` | ❌ Wave 0 |
| BATCH-01 | `--seeds 1,1,2` deduplikuje | unit | `python -m unittest tests.test_batch.TestSeedsParser.test_dedup` | ❌ Wave 0 |
| BATCH-01 | `--batch` bez `--seeds` → argparse error | unit | `python -m unittest tests.test_batch.TestArgsMutex.test_batch_requires_seeds` | ❌ Wave 0 |
| BATCH-01 | `/batch <strategia> --seeds N` w REPL działa end-to-end | integration | `python -m unittest tests.test_batch.TestReplBatch.test_e2e` | ❌ Wave 0 |
| BATCH-01 | `--batch + --compare-agent` rzuca error | unit | `python -m unittest tests.test_batch.TestArgsMutex.test_batch_compare_mutex` | ❌ Wave 0 |
| BATCH-02 | mean/std obliczone correctly (znane warte 5 elementów) | unit | `python -m unittest tests.test_batch_stats.TestAggregate.test_known_values` | ❌ Wave 0 |
| BATCH-02 | 95% CI dla N=10 z znanego mean+std (porównaj ze scipy.stats.t.ppf hand-calculation) | unit | `python -m unittest tests.test_batch_stats.TestAggregate.test_ci_against_manual` | ❌ Wave 0 |
| BATCH-02 | N=1: std=0, CI lower/upper = None | unit | `python -m unittest tests.test_batch_stats.TestAggregate.test_n1_degenerate` | ❌ Wave 0 |
| BATCH-02 | 95% CI synthetic check — generate N=100 normal samples, sprawdź że CI obejmuje true mean | unit | `python -m unittest tests.test_batch_stats.TestAggregate.test_ci_coverage` | ❌ Wave 0 |
| BATCH-03 | Batch report.md ma sekcję "Wyniki per seed" z N wierszami | integration | `python -m unittest tests.test_batch_report.TestBatchReport.test_per_seed_table` | ❌ Wave 0 |
| BATCH-03 | Batch report.md ma sekcję "Agregat statystyczny" z 5 KPI × 7 kolumn | integration | `python -m unittest tests.test_batch_report.TestBatchReport.test_aggregate_table` | ❌ Wave 0 |
| BATCH-03 | Batch report.md ma werdykt "bije baseline" (string match) | integration | `python -m unittest tests.test_batch_report.TestBatchReport.test_baseline_verdict` | ❌ Wave 0 |
| BATCH-03 | Batch report.md zawiera link `![](batch_aggregate.png)` | unit | `python -m unittest tests.test_batch_report.TestBatchReport.test_png_link` | ❌ Wave 0 |
| PLOT-04 | `batch_aggregate.png` istnieje + non-zero size + PNG signature | integration | `python -m unittest tests.test_batch_report.TestBatchPlots.test_png_exists` | ❌ Wave 0 |
| PLOT-04 | Boxplot ma 5 subplot panels | unit | `python -m unittest tests.test_batch_report.TestBatchPlots.test_5_panels` | ❌ Wave 0 |
| BATCH-determinism | Same seed list twice → byte-identical per-seed KPI | integration | `python -m unittest tests.test_batch.TestDeterminism.test_byte_identical` | ❌ Wave 0 |
| BATCH-CLI-REPL | CLI `--batch` i REPL `/batch` produkują identyczne raporty dla tego samego seed list | integration | `python -m unittest tests.test_batch.TestCliReplParity.test_identical_output` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `SPHSIM_NO_REPORT=1 python -m unittest tests/test_batch*.py -v`
- **Per wave merge:** `SPHSIM_NO_REPORT=1 python -m unittest discover tests/ -v && SPHSIM_NO_REPORT=1 python scripts/regression_check.py`
- **Phase gate:** Full suite green + regression PASS=8/8 + `scripts/verify_phase7.sh` PASS≥30 / FAIL=0

### Wave 0 Gaps
- [ ] `tests/test_batch.py` — TestSeedsParser (~7 cases) + TestArgsMutex (~3) + TestReplBatch (~2) + TestDeterminism (~1) + TestCliReplParity (~1)
- [ ] `tests/test_batch_stats.py` — TestAggregate (~5 cases)
- [ ] `tests/test_batch_report.py` — TestBatchReport (~4 cases) + TestBatchPlots (~2 cases)
- [ ] `scripts/verify_phase7.sh` — exit gate (~30+ check() invocations covering 4 SCs + tests + regression + REPL + opt-out — pattern verbatim z `verify_phase6.sh`)
- [ ] Framework install: **none** — `unittest` is stdlib; scipy/numpy/matplotlib już zainstalowane (researcher verified)
- [ ] `requirements.txt` — nowy plik z `matplotlib`, `numpy`, `scipy` (researcher rekomenduje DODAĆ w Phase 7)

---

## Sources

### Primary (HIGH confidence)
- `sphsim/cli/main.py:1-168` — single-run pipeline (4 branches: built-in single, built-in compare, custom single, custom compare)
- `sphsim/cli/args.py:32-125` — argparse, custom type converters pattern (`_parse_phi_list`, `_parse_rho_list`)
- `sphsim/cli/repl.py:55-352` — SPHShell cmd.Cmd subclass; do_run, do_compare, fake_args pattern
- `sphsim/core/simulator.py:1-175` — SPHSimulator constructor + run() returning 5 KPI dict + history + ic_per_phase + veto_per_phase
- `sphsim/report/__init__.py:1-153` — write_report orchestrator, _resolve_report_dir, _timestamp, exception isolation
- `sphsim/report/markdown.py:1-214` — render_report, _KPI_ROWS, BASELINE_PATH, format_config_header reuse, baseline comparison section
- `sphsim/report/plots.py:1-119` — matplotlib Agg backend, font fallback, plot_decision_distribution, plot_kpi_timeseries with close-in-finally pattern
- `sphsim/agent/rational.py:1-56` — wrap_with_agent closure, expected_P propagation
- `sphsim/strategies/__init__.py:1-26` — STRATEGIES dict, BUILTIN_STRATEGIES frozenset (custom strategy discovery)
- `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` — baseline metrics (avg_val_last100=92.0)
- `.planning/phases/06-report-plots-generator/06-RESEARCH.md` — Phase 6 research, reusable patterns (matplotlib pitfalls, opt-out env var, exception isolation)
- `.planning/phases/06-report-plots-generator/06-PHASE-VERIFICATION.md` — Phase 6 verification, 7/7 pitfalls defused, all 6 SCs PASS
- VERIFIED runtime: `python3 -c "import scipy.stats; ..."` → CI tuple (90.21, 93.78) for known mean=92, std=2.5, n=10 — formula works
- VERIFIED runtime: `/usr/bin/time -p python3 sph_sim.py --strategy naive ...` → 0.15s per single run — sequential 10 seeds < 2s

### Secondary (MEDIUM confidence)
- [CITED: scipy.stats.t.interval docs] — https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html — `interval(confidence, df, loc, scale)` signature, returns `(lower, upper)` tuple
- [CITED: numpy.std ddof docs] — `ddof=1` for sample std (Bessel's correction), `ddof=0` (default) for population std
- [CITED: matplotlib.pyplot.boxplot docs] — `boxplot(x, vert=True, patch_artist=False, ...)` returns dict with 'boxes', 'whiskers', 'caps', 'medians', 'fliers'

### Tertiary (LOW confidence)
- None — all claims grounded in either codebase reads, runtime probes, or official docs

---

## Metadata

**Confidence breakdown:**
- Codebase reuse map: HIGH — all 11 source files read directly, key entrypoints + helpers identified verbatim
- Statistical aggregation: HIGH — scipy.stats.t.interval CITED, numpy ddof=1 CITED, N=1 edge case verified by runtime probe
- Architecture patterns: HIGH — Phase 6 patterns (renderer + orchestrator + opt-out + exception isolation) verbatim reuse
- Pitfalls: HIGH — 7 pitfalls grounded in Phase 6 prior experience (which had its own 7 defused pitfalls) + 1 new (Pitfall 6 — scipy as new dependency)
- Seed-list parsing: HIGH — grammar fully specified, all edge cases listed with reject/accept verdict
- Boxplot design: MEDIUM — 5-subplot rationale is researcher's design call (alternative single-boxplot rejected with data range evidence); a real user might prefer the alternative

**Research date:** 2026-05-28
**Valid until:** 2026-06-27 (30 days — Phase 7 deps stable: scipy/numpy/matplotlib API; codebase frozen post-Phase-6)
