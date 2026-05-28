# Roadmap: SPH Mediation Simulator — Milestone v1.1 Agent CLI

## Overview

Milestone v1.1 rozszerza istniejący `sph_sim.py` (v1.0, 363 linii, single-file) o interaktywne CLI, custom strategy loader, warstwę "racjonalnego agenta" (weto ujemnego oczekiwanego zysku), konfigurowalne środowisko, raporty MD + wykresy PNG (zawsze) oraz batch runner z agregacją statystyczną. Punktem startowym jest refactoring monolitycznego pliku w pakiet z modułami (przy zachowaniu wstecznej kompatybilności CLI z v1.0), następnie warstwami dokładamy interaktywność, custom strategie, agenta racjonalnego, konfigurowalne środowisko, generator raportu/wykresów i finalnie batch runner. Każda faza dostarcza jedną spójną, weryfikowalną zdolność użytkową dla studenta/prowadzącego eksperymentującego z własnymi strategiami.

## Milestones

- 🚧 **v1.1 Agent CLI** — Phases 1-8 (Phases 1-7 complete; Phase 8 planned, awaiting execution)

Note: v1.0 nie był śledzony w GSD — istnieje jako "Validated" w PROJECT.md (baseline `naive --zeta 0.75` → avg_val=92).

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Refactoring foundation** - Split `sph_sim.py` into package (`strategies/`, `agent/`, `report/`, `cli/`) preserving v1.0 CLI behavior (completed 2026-05-25)
- [x] **Phase 2: Interactive CLI shell** - REPL z `/help`, `/exit`, `/strategies`, `/strategy <nazwa>` (completed 2026-05-25)
- [x] **Phase 3: Custom strategy loader** - `importlib`-based loader plików `.py` + walidacja + szablon przykładowy (completed 2026-05-27)
- [x] **Phase 4: Rational Agent veto layer** - Wrapper weto'ujący COMMIT przy `E[zysk] < 0` + tryb porównawczy (completed 2026-05-27)
- [x] **Phase 5: Configurable environment** - Override `φ/ρ`, presety waluacji, serializacja konfiguracji do raportu (completed 2026-05-27)
- [x] **Phase 6: Report + plots generator** - Raport MD + 2 wykresy PNG (matplotlib) generowane zawsze (completed 2026-05-28)
- [x] **Phase 7: Batch runner + aggregation** - Wiele seedów, agregacja statystyczna, box-ploty (completed 2026-05-28)
- [ ] **Phase 8: Documentation + Interactive Tutorial** - Polski przewodnik użytkownika (`docs/PRZEWODNIK.md`) + REPL `tutorial` mode (`--tutorial` flag) prowadzący krok-po-kroku przez v1.1

## Phase Details

### Phase 1: Refactoring foundation

**Goal**: Monolityczny `sph_sim.py` jest rozbity na pakiet modułów (z czytelnym podziałem odpowiedzialności), a wszystkie dotychczasowe inwokacje CLI z v1.0 nadal działają bez zmian
**Depends on**: Nothing (first phase)
**Requirements**: CLI-04
**Success Criteria** (what must be TRUE):

  1. Wszystkie 5 baseline'owych inwokacji z docstringu v1.0 (np. `python sph_sim.py --strategy naive --zeta 0.5`, `--strategy phase_prob --probs ...`) zwracają identyczne wyniki numeryczne dla `--seed 42` jak przed refactorem
  2. Kod jest podzielony na moduły (sugerowane: `sph_sim/strategies/`, `sph_sim/core/`, `sph_sim/cli/`) — każdy moduł ma jedną odpowiedzialność, żaden nie przekracza ~150 linii
  3. Plik `sph_sim.py` w katalogu głównym pozostaje uruchamialny jako entry point (`python sph_sim.py ...`)
  4. Output `--json` zawiera dokładnie te same klucze i wartości co w v1.0 dla baseline benchmarku `naive --zeta 0.75`

**Plans**: 5 plans
Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Generate baseline JSON fixtures from v1.0 monolith + regression_check.py harness (PRE-refactor; D-11 ordering)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Package skeleton (sphsim/, sphsim/core/) + sphsim/config.py + sphsim/core/model.py + sphsim/core/device.py

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — Extract 5 strategies into per-file modules + STRATEGIES registry (sphsim/strategies/)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 01-04-PLAN.md — Extract SPHSimulator + cli/ layer; cutover sph_sim.py to thin shim; finalize sphsim/__init__.py public API

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 01-05-PLAN.md — verify_phase1.sh phase exit gate (4 ROADMAP Success Criteria + D-06 + D-07 + D-16)

### Phase 2: Interactive CLI shell

**Goal**: Użytkownik może uruchomić tryb interaktywny i wewnątrz REPL'a przeglądać dostępne strategie z ich opisami, parametrami i baseline KPI
**Depends on**: Phase 1
**Requirements**: CLI-01, CLI-02, CLI-03, STRAT-01, STRAT-02
**Success Criteria** (what must be TRUE):

  1. Komenda `python sph_sim.py --interactive` uruchamia REPL z polskim promptem i wita użytkownika instrukcją wpisania `help` (D-17 override: komendy bez prefiksu `/`)
  2. W REPL'u `help` wyświetla listę wszystkich dostępnych komend (`help`, `exit`, `strategies`, `strategy <nazwa>`) z krótkim opisem po polsku (D-17 override)
  3. `strategies` wyświetla tabelę 5 wbudowanych strategii (nazwa + jednolinijkowy opis) (D-17 override)
  4. `strategy naive` (i analogicznie dla 4 pozostałych) wyświetla pełen opis: parametry, sygnatura, baseline KPI (np. `naive --zeta 0.75 → avg_val_last100 = 92.0`) (D-17 override)
  5. `exit` lub `Ctrl+D` kończy sesję z czystym komunikatem pożegnalnym (D-17 override + D-20)

**Plans**: 4 plans
Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Add STRATEGY_META to all 5 strategy files (D-24/D-25/D-26)
- [x] 02-02-PLAN.md — Add --interactive in mutex group + docstring fix in sphsim/cli/args.py (D-23/D-27/D-28)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-03-PLAN.md — Implement SPHShell REPL (sphsim/cli/repl.py) + wire --interactive in sphsim/cli/main.py (D-17..D-22, D-29..D-33)
- [x] 02-04-PLAN.md — STRATEGY_META ↔ argparse invariant test (tests/test_strategy_meta_consistency.py per D-25 Claude's Discretion)

### Phase 3: Custom strategy loader

**Goal**: Użytkownik może napisać własną strategię w pliku `.py`, załadować ją do symulatora i uruchomić jak każdą wbudowaną
**Depends on**: Phase 2
**Requirements**: STRAT-03, STRAT-04, STRAT-05
**Success Criteria** (what must be TRUE):

  1. Komenda `--custom <ścieżka>` (CLI) oraz `/custom <ścieżka>` (REPL) ładują plik `.py` przez `importlib` i rejestrują strategię z nazwą wziętą z pliku
  2. Loader sprawdza obecność funkcji o wymaganej sygnaturze i przy każdym błędzie (brak funkcji, zła sygnatura, exception przy imporcie) wyświetla czytelny polski komunikat z konkretem (nazwa brakującej funkcji, oczekiwane argumenty)
  3. Plik `examples/custom_strategy_template.py` istnieje, zawiera komentarze po polsku, kompiluje się bez ostrzeżeń, ładuje się przez loader i daje sensowne wyniki na baseline'owym środowisku
  4. Załadowana custom strategia jest widoczna w `/strategies` jako dodatkowy wiersz oznaczony jako "custom"
  5. Loader przy ładowaniu jasno komunikuje że wykonuje arbitralny Python z pliku użytkownika (świadome ostrzeżenie bezpieczeństwa)

**Plans**: 4 plans
Plans:
**Wave 1**

- [x] 03-01-PLAN.md — Loader module (load_custom + parse_params_from_meta + LoaderError) + BUILTIN_STRATEGIES + tests/test_loader.py (19+ cases covering D-47 4 layers + D-49 collision + D-38 reload)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02-PLAN.md — CLI integration: --custom in mutex + --param append + main.py args.custom early branch (D-44, D-46, D-50)
- [x] 03-03-PLAN.md — REPL integration: SPHShell do_custom + do_run + do_strategies [custom] suffix + do_strategy dispatch + do_help 6 komend (D-41, D-42, D-50)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 03-04-PLAN.md — examples/custom_strategy_template.py (D-51 STRAT-05) + scripts/verify_phase3.sh phase exit gate (5 ROADMAP SCs + regression + invariant)

### Phase 4: Rational Agent veto layer

**Goal**: Wrapper `RationalAgent` weto'uje rekomendacje COMMIT o ujemnym oczekiwanym zysku — dydaktycznie dowodząc warunek motywacyjnej zgodności (incentive compatibility)
**Depends on**: Phase 3
**Requirements**: AGENT-01, AGENT-02, AGENT-03, AGENT-04, AGENT-05
**Success Criteria** (what must be TRUE):

  1. Każda strategia (wbudowana i custom) jest domyślnie opakowana w `RationalAgent`, który dla każdej rekomendacji COMMIT oblicza `E[zysk_i] = (1-φ_i)·p_i - κ - φ_i·ρ_i` i przy `E[zysk_i] < 0` override'uje na ABSTAIN
  2. Flaga `--no-agent` (CLI) oraz tryb bez agenta w `/compare` wyłącza wrapper i pokazuje surową strategię
  3. Wynik symulacji zawiera licznik veto'wanych decyzji per faza (`veto_per_phase: {1: N1, 2: N2, ...}`) widoczny w outputcie human-readable i JSON
  4. Komenda `/compare <strategia>` lub `--compare-agent` uruchamia tę samą strategię raz z `RationalAgent` i raz bez, a w raporcie pojawia się tabela delta KPI (`avg_val`, `avg_profit`, `delivery_ratio`) między obiema wersjami
  5. Dla scenariusza demonstracyjnego (np. `incentive --expected_P 30` gdzie strategia rekomenduje COMMIT przy ujemnym zysku) `with-agent` ma wyższy `avg_net_profit` niż `without-agent` — empiryczny dowód że weto chroni KPI

**Plans**: 7 plans
Plans:
**Wave 1**

- [x] 04-01-PLAN.md — Device n_vetoed/veto_phase_stats + simulator 3-state interface + veto_per_phase aggregation
- [x] 04-02-PLAN.md — sphsim/agent/ package (rational.py wrap_with_agent closure factory, D-53 formula)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-03-PLAN.md — output.py: VETO section in format_human + format_compare delta table + format_json extensions (agent_enabled, comparison)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04-04-PLAN.md — CLI: args.py (--no-agent + --compare-agent + mutex) + main.py wrap + run_compare
- [x] 04-05-PLAN.md — REPL: do_compare command + do_run wrap (agent default-on) + do_help update

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 04-06-PLAN.md — tests/test_agent.py (10+ cases, TDD) + scripts/generate_baseline.py --no-agent (D-59) + regression PASS=8/8

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 04-07-PLAN.md — scripts/verify_phase4.sh phase exit gate (5 ROADMAP SC + regression + tests + invariants + SC#5 empirical)

### Phase 5: Configurable environment

**Goal**: Użytkownik może override'ować profile `φ/ρ` z linii poleceń, wybrać preset funkcji waluacji oraz zobaczyć pełną konfigurację w nagłówku raportu
**Depends on**: Phase 4
**Requirements**: ENV-01, ENV-02, ENV-03
**Success Criteria** (what must be TRUE):

  1. Flagi `--phi p1,p2,p3,p4,p5` i `--rho r1,r2,r3,r4,r5` przyjmują listy 5 liczb i nadpisują `DEFAULT_PHI`/`DEFAULT_RHO`; symulator waliduje długość i zakres ([0,1] dla φ, ≥0 dla ρ)
  2. Flaga `--valuation <window|step|linear>` wybiera preset funkcji waluacji `g(u)`; alternatywnie `--K0 X --K1 Y` daje pełną kontrolę parametryczną (window jest domyślem zgodnym z v1.0)
  3. Wszystkie 3 presety waluacji dają deterministyczne, dające się odróżnić wyniki KPI na tym samym seedzie + strategii
  4. Nagłówek wygenerowanego raportu MD zawiera kompletną konfigurację środowiska: `nU, T, κ, α, K0, K1, φ, ρ, seed` w czytelnej tabeli

**Plans**: 5 plans
Plans:
**Wave 0** *(scaffolding)*

- [x] 05-00-PLAN.md — tests/test_env.py 7-class stub + scripts/verify_phase5.sh skeleton (locks taxonomy for Waves 1-4)

**Wave 1** *(blocked on Wave 0 completion)*

- [x] 05-01-PLAN.md — ENV-01: --phi/--rho argparse type= converters (Polish errors) + main.py threading + TestPhiRhoParsing/Flow

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 05-02-PLAN.md — ENV-02: --K0/--valuation flags + valuation/sph_stp preset dispatch + simulator threading + TestValuationDispatch/Presets/Distinguishability (SC-3)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 05-03-PLAN.md — ENV-03: format_config_header() MD table + format_human prepend + JSON env block extension + REPL fake_args fix (Pitfall 2) + TestConfigHeader/HumanHeader

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 05-04-PLAN.md — regression_check.py SKIP_KEYS extension + scripts/verify_phase5.sh phase exit gate (4 ROADMAP SCs + regression + tests + REPL Pitfall 2)

### Phase 6: Report + plots generator

**Goal**: Każde uruchomienie symulacji (single-run) automatycznie produkuje raport MD z linkowanymi wykresami PNG — bez żadnych flag, zawsze
**Depends on**: Phase 5
**Requirements**: REPORT-01, REPORT-02, REPORT-03, PLOT-01, PLOT-02, PLOT-03
**Success Criteria** (what must be TRUE):

  1. Każde uruchomienie symulacji tworzy katalog `./reports/<timestamp>/` z plikami `report.md`, `decision_distribution.png`, `kpi_timeseries.png`
  2. `report.md` zawiera sekcje: konfiguracja środowiska, użyta strategia + parametry, tabelę KPI (`avg_val_last100`, `cum_val_total`, `avg_net_profit`, `delivery_ratio`, `avg_providers_l100`), rozkład decyzji per faza, porównanie z baseline `naive --zeta 0.75`
  3. `decision_distribution.png` to wykres słupkowy COMMIT/ABSTAIN/VETO per faza (1-5); `kpi_timeseries.png` to wykres `avg_val` i `avg_providers` w funkcji cyklu z zaznaczonym oknem ostatnich 100 cykli
  4. Oba wykresy są linkowane z `report.md` jako relatywne ścieżki (`![Rozkład](decision_distribution.png)`) i wyświetlają się poprawnie w GitHub/VSCode/Obsidian
  5. W trybie `--compare-agent` raport dodatkowo zawiera tabelę delta KPI (with-agent vs without-agent)
  6. Stary `--json` output nadal działa (kompatybilność z v1.0); raport MD nie jest zamiennikiem tylko dodatkiem

**Plans**: six plans (06-00 through 06-05, complete 2026-05-28)
**UI hint**: yes

### Phase 7: Batch runner + aggregation

**Goal**: Użytkownik może uruchomić tę samą strategię dla wielu seedów i otrzymać raport z agregacją statystyczną (mean/std/CI) oraz box-plotami KPI
**Depends on**: Phase 6
**Requirements**: BATCH-01, BATCH-02, BATCH-03, PLOT-04
**Success Criteria** (what must be TRUE):

  1. Komenda `/batch <strategia> --seeds 10` (REPL) lub `--batch --seeds 10` (CLI) uruchamia strategię na 10 kolejnych seedach (1..10); `--seeds 1,5,42,100` przyjmuje również jawną listę
  2. Raport MD w trybie batch zawiera tabelę per-seed (jeden wiersz na seed: seed + 5 KPI) oraz sekcję agregatu statystycznego (mean, std, min, max, 95% CI) dla każdego KPI
  3. Plik `batch_aggregate.png` z box-plotami 5 KPI jest generowany i linkowany w raporcie
  4. Batch działa z `RationalAgent` (default) i `--no-agent` (dla porównań statystycznych)
  5. Batch report jasno wskazuje czy strategia bije baseline `naive --zeta 0.75` (czy 95% CI dla `avg_val_last100` jest powyżej 92)

**Plans**: 7 plans
Plans:
**Wave 0** *(scaffolding)*

- [x] 07-00-PLAN.md — Wave 0 scaffolding: test stubs (test_batch + test_batch_stats + test_batch_report) + requirements.txt (matplotlib/numpy/scipy)

**Wave 1** *(blocked on Wave 0 completion)*

- [x] 07-01-PLAN.md — BATCH-02: sphsim/batch/stats.py (aggregate_kpis + AggregateStat + KPIS) + TestAggregateKpis/TestCIComputation/TestN1Degenerate/TestEmptyInput/TestStatsDeterminism (9 tests green)
- [x] 07-02-PLAN.md — BATCH-01 CLI: sphsim/cli/args.py _parse_seeds_list (MAX_SEEDS=1000 cap) + --batch/--seeds flags + 4-way post-parse mutex + TestSeedsParser/TestArgsMutex (11 tests green)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 07-03-PLAN.md — BATCH-01 orchestrator: sphsim/batch/runner.py (N×SPHSimulator loop) + sphsim/cli/main.py 2× early branches + sphsim/cli/output.py::format_batch_summary + TestDeterminism (2 tests green)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 07-04-PLAN.md — BATCH-03 + PLOT-04: sphsim/report/batch_markdown.py + sphsim/report/plots.py::plot_batch_aggregate + sphsim/report/__init__.py::write_batch_report + main.py wiring + TestBatchReport/TestBatchPlots (6 tests green)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 07-05-PLAN.md — BATCH-01 REPL: sphsim/cli/repl.py SPHShell.do_batch + do_help update + CLI/REPL parity + TestReplBatch/TestCliReplParity (3 tests green)

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 07-06-PLAN.md — verify_phase7.sh phase exit gate (5 ROADMAP SCs + 4 REQ-IDs + regression PASS=8/8 + REPL Pitfalls + opt-out — ≥30 check() invocations) + STATE/ROADMAP closeout

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Refactoring foundation | 5/5 | Complete   | 2026-05-25 |
| 2. Interactive CLI shell | 4/4 | Complete   | 2026-05-25 |
| 3. Custom strategy loader | 4/4 | Complete   | 2026-05-27 |
| 4. Rational Agent veto layer | 7/7 | Complete   | 2026-05-27 |
| 5. Configurable environment | 5/5 | Complete   | 2026-05-27 |
| 6. Report + plots generator | 6/6 | Complete   | 2026-05-28 |
| 7. Batch runner + aggregation | 7/7 | Complete   | 2026-05-28 |
| 8. Documentation + Interactive Tutorial | 4/8 | In Progress|  |

### Phase 8: Documentation + Interactive Tutorial

**Goal:** Nowy użytkownik (student/prowadzący) bez znajomości projektu potrafi w ≤15 minut: (1) przeczytać polski przewodnik `docs/PRZEWODNIK.md` z opisem wszystkich CLI/REPL commands i flag, (2) uruchomić w REPL tryb `tutorial` (lub `python sph_sim.py --tutorial`) i przejść krok-po-kroku przez wszystkie zdolności v1.1 (strategies → custom → agent → env → report → batch) z opcją `skip` per krok, inspirowany scenariuszami z `scripts/uat_*.sh` / `verify_phase*.sh`
**Requirements**: TUT-01, TUT-02, TUT-03, TUT-04, TUT-05, TUT-06, DOC-01, DOC-02, EX-01, GATE-01 (validation-level IDs from 08-VALIDATION.md — Phase 8 adds no new REQUIREMENTS.md REQ-IDs; exercises all 7 prior REQ categories via tutorial golden path + PRZEWODNIK examples)
**Depends on:** Phase 7
**Plans:** 4/8 plans executed

Plans:
**Wave 0** *(scaffolding)*

- [x] 08-00-PLAN.md — Test scaffolding: tests/test_tutorial.py (5 classes, TUT-01..TUT-06) + tests/test_docs.py (3 classes, DOC-01/DOC-02/EX-01) + docs/.gitkeep + docs/assets/.gitkeep + scripts/verify_phase8.sh skeleton

**Wave 1** *(blocked on Wave 0 completion — three parallel plans, no file overlap)*

- [x] 08-01-PLAN.md — sphsim/report/__init__.py: D-10 report_dir_override kwarg on write_report + write_batch_report (backwards-compat default None)
- [x] 08-02-PLAN.md — sphsim/cli/args.py: --tutorial 5-way mutex extension + Polish post-parse errors + Plan 8-02 also wires the 4th early branch in sphsim/cli/main.py
- [x] 08-03-PLAN.md — sphsim/cli/tutorial.py (NEW): TutorialFlow + TutorialStep @dataclasses + STEP_TOPICS + STEP_TASKS + check_step (pure state machine, no I/O, no sphsim imports)

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 08-04-PLAN.md — sphsim/cli/repl.py: __init__ + precmd + postcmd + do_tutorial + _show_tutorial_step/_show_step_hint + do_help tutorial line + run_repl(start_in_tutorial=True) + do_run/do_compare/do_batch _last_sim_result + report_dir_override threading (D-08, D-10, D-05, Pitfalls 1/2/3 from RESEARCH)

**Wave 3** *(blocked on Wave 2 completion — two parallel plans, no file overlap)*

- [ ] 08-05-PLAN.md — scripts/gen_tutorial_assets.sh (NEW) + docs/assets/decision_distribution_naive.png + kpi_timeseries_naive.png + batch_aggregate_naive.png (deterministic --seed 42 per D-14)
- [ ] 08-06-PLAN.md — docs/PRZEWODNIK.md (NEW): Polish user guide, D-11 structure (Lead → Quickstart → Walkthrough → Reference → Theory), D-12 verbatim examples annotated `# Z 08-UAT.md test #N`, D-14 PNG embeds + matplotlib drift note

**Wave 4** *(blocked on Wave 3 completion — final BLOCKING gate)*

- [ ] 08-07-PLAN.md — scripts/verify_phase8.sh: 33 check() invocations across 7 categories (PRZEWODNIK sections, PNG magic, --tutorial mutex, REPL controls, TUT-06 dirs, source assertions, regression + tests) + 1 BLOCKING checkpoint requiring user confirmation that ≤15-min onboarding goal is achievable
