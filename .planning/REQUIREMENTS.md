# Requirements — Milestone v1.1 Agent CLI

**Status:** Active
**Created:** 2026-05-25
**Total:** 25 requirements across 7 categories

---

## v1.1 Requirements

### CLI — interaktywna powłoka i komendy

- [ ] **CLI-01**: Użytkownik może uruchomić tryb interaktywny przez `python sph_sim.py --interactive` (REPL)
- [ ] **CLI-02**: Użytkownik może wpisać `/help` i otrzymać listę wszystkich komend z opisem po polsku
- [ ] **CLI-03**: Użytkownik może wpisać `/exit` lub użyć `Ctrl+D` aby zakończyć sesję
- [ ] **CLI-04**: Wszystkie dotychczasowe inwokacje CLI z v1.0 (np. `--strategy naive --zeta 0.5`) działają bez zmian (backwards compat)

### STRAT — browser i zarządzanie strategiami

- [ ] **STRAT-01**: Użytkownik może wpisać `/strategies` aby zobaczyć listę 5 wbudowanych strategii z krótkim opisem
- [ ] **STRAT-02**: Użytkownik może wpisać `/strategy <nazwa>` aby zobaczyć szczegóły konkretnej strategii (parametry, sygnatura, baseline KPI)
- [ ] **STRAT-03**: Użytkownik może załadować custom strategię z pliku `.py` komendą `/custom <ścieżka>` lub flagą `--custom <ścieżka>`
- [ ] **STRAT-04**: Loader waliduje że plik zawiera funkcję o wymaganej sygnaturze i jasno komunikuje błędy (brak funkcji, zła sygnatura, exception)
- [ ] **STRAT-05**: Projekt zawiera przykładowy szablon `examples/custom_strategy_template.py` z komentarzami po polsku

### AGENT — rational agent veto

- [ ] **AGENT-01**: Strategia jest opakowana w `RationalAgent` który dla każdej rekomendacji COMMIT oblicza `E[zysk_i] = (1-φ_i)·p_i - κ - φ_i·ρ_i`
- [ ] **AGENT-02**: Gdy `E[zysk_i] < 0`, agent override'uje rekomendację na ABSTAIN (weto)
- [ ] **AGENT-03**: Użytkownik może wyłączyć agenta flagą `--no-agent` aby zobaczyć surową strategię (tryb porównawczy)
- [ ] **AGENT-04**: Symulacja śledzi licznik veto'wanych decyzji per faza i zwraca go w wyniku
- [ ] **AGENT-05**: Raport porównawczy (`/compare <strategia>`) uruchamia tę samą strategię raz z agentem i raz bez, pokazuje delta KPI

### ENV — konfigurowalne środowisko

- [ ] **ENV-01**: Użytkownik może override'ować profile `--phi p1,p2,p3,p4,p5` i `--rho r1,r2,r3,r4,r5` z linii poleceń
- [ ] **ENV-02**: Użytkownik może wybrać preset funkcji waluacji `--valuation <window|step|linear>` lub podać `--K0 X --K1 Y`
- [ ] **ENV-03**: Pełna konfiguracja środowiska (nU, T, κ, α, K0, K1, φ, ρ, seed) jest serializowana do nagłówka raportu MD

### BATCH — wiele seedów + agregacja

- [ ] **BATCH-01**: Użytkownik może uruchomić `/batch <strategia> --seeds 10` lub `--seeds 1,2,3,...` aby uruchomić symulację dla wielu seedów
- [ ] **BATCH-02**: Wyniki batcha są agregowane: mean, std, min/max, 95% CI dla każdego KPI
- [ ] **BATCH-03**: Raport MD z trybu batch zawiera tabelę per-seed + sekcję agregatu statystycznego

### REPORT — raport Markdown (zawsze)

- [ ] **REPORT-01**: Każde uruchomienie symulacji generuje plik MD w `./reports/<timestamp>/report.md`
- [ ] **REPORT-02**: Raport zawiera sekcje: konfiguracja środowiska, użyta strategia + parametry, wyniki KPI, rozkład decyzji per faza, porównanie z baseline (`naive --zeta 0.75`)
- [ ] **REPORT-03**: Raport w trybie porównawczym (`/compare` lub `--with-agent` + `--no-agent`) zawiera tabelę delta KPI

### PLOT — wykresy PNG (zawsze)

- [ ] **PLOT-01**: Każde uruchomienie generuje wykres `decision_distribution.png` — słupkowy rozkład COMMIT/ABSTAIN/VETO per faza
- [ ] **PLOT-02**: Każde uruchomienie generuje wykres `kpi_timeseries.png` — `avg_val` i `avg_providers` w funkcji cyklu t (z ostatnimi 100 cyklami zaznaczonymi)
- [ ] **PLOT-03**: Wykresy są linkowane z raportu MD (relatywne ścieżki, `![](decision_distribution.png)`)
- [ ] **PLOT-04**: W trybie batch generowany jest dodatkowy wykres `batch_aggregate.png` z box-plotami KPI

---

## Future Requirements (deferred)

<!-- Considered, valuable, but out of v1.1 scope. -->

- Web UI (Flask/FastAPI) z interaktywnymi wykresami — deferred do v2.0 jeśli okaże się potrzebne
- DSL deklaratywny (YAML/JSON) jako alternatywa dla `.py` loader — deferred, plik `.py` wystarcza dla początkowych użytkowników
- Interaktywny kreator strategii (wizard Q&A) — deferred, można dorzucić w v1.2 po feedbacku
- Persystencja wyników w SQLite/CSV historii — deferred, raporty MD są wystarczające

---

## Out of Scope

<!-- Explicit exclusions with reasoning. -->

- **Web UI**: Odrzucone na rzecz CLI + raport MD — większa uniwersalność dla projektu akademickiego, raport otwiera się wszędzie bez instalacji serwera
- **DSL custom strategies (YAML)**: Odrzucone — plik `.py` daje pełną elastyczność programisty, nie ma potrzeby dodatkowego abstrakcji
- **Wykresy interaktywne (Plotly/Bokeh)**: Odrzucone — PNG z matplotlib jest wystarczające dla raportu MD i nie wymaga JavaScript runtime
- **Zmiana modelu domeny** (ciągłe fazy, inny SPH-STP): Poza scope v1.1 — to byłby v2.0 z osobnym uzasadnieniem teoretycznym
- **i18n interfejsu**: Kod i interfejs zostają w języku polskim (spójność z v1.0 i odbiorcami akademickimi)
- **Deploy/publikacja**: Projekt uruchamiany lokalnie, nie ma deploymentu jako artefaktu

---

## Traceability

<!-- Filled by roadmap — maps REQ-IDs to phases. -->

(Roadmap pending)

---

*Last updated: 2026-05-25 — initial creation*
