# SPH Mediation Simulator

## What This Is

Symulator strategii mediacji transferu płatnych usług (SPH) — narzędzie badawcze i edukacyjne do projektu z Metod Probabilistycznych Eksploracji (MPE cz. 2, J. Konorski, WETI). Pozwala testować różne reguły decyzyjne COMMIT/ABSTAIN dla floty zawodnych urządzeń autonomicznych w grze ekonomicznej z buforem usług (SUS) i progowymi waluacjami konsumentów. Odbiorcami są studenci i prowadzący zajęcia z teorii gier / systemów wieloagentowych, którzy chcą eksperymentować z własnymi strategiami i porównywać je z baseline'em.

## Core Value

**Uczynić problem mediacji SPH namacalnym i testowalnym** — każdy użytkownik powinien móc napisać własną strategię, uruchomić ją na zdefiniowanym środowisku i otrzymać porównywalny raport KPI względem baseline'u.

## Current Milestone: v1.1 Agent CLI — Interactive Strategy Testbed

**Goal:** Rozszerzyć symulator o interaktywne CLI pozwalające użytkownikom przeglądać, tworzyć i testować własne strategie, z automatycznym raportem MD + wykresami PNG i warstwą "racjonalnego agenta" który weto'uje decyzje o ujemnym oczekiwanym zysku.

**Target features:**
- Interaktywne CLI z komendami `/help`, `/strategies`, `/run`, `/custom`, `/batch`, `/report`
- Browser strategii — opis każdej z 5 wbudowanych strategii + ich baseline KPI
- Custom strategy loader — pliki `.py` z funkcją wg ustalonej sygnatury (importlib)
- Rational Agent wrapper — domyślnie weto'uje COMMIT gdy `E[zysk_i] < 0`
- Tryb porównawczy `with-agent` vs `without-agent` — dowód empiryczny że weto chroni KPI
- Konfigurowalne środowisko: nU/T/κ/α/K1/seed + profile φ/ρ + funkcja waluacji g(u)
- Batch runner — wiele seedów → agregacja statystyczna w raporcie
- Raport MD generowany zawsze (konfiguracja, decyzje, KPI, rozkład, porównanie)
- Wykresy PNG generowane zawsze (matplotlib): rozkład decyzji per faza, KPI w czasie

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Symulator SPH z 5 strategiami (`naive`, `threshold`, `phase_prob`, `incentive`, `adaptive`) — `sph_sim.py` (v1.0)
- ✓ CLI argparse z parametryzacją środowiska (nU, nSUS, K1, T, kappa, alpha, seed) — v1.0
- ✓ Tryby wyjścia: human-readable + JSON (`--json`) — v1.0
- ✓ Reprodukowalność przez `--seed` — v1.0
- ✓ Baseline benchmark: `naive --zeta 0.75` → avg_val=92, avg_profit=+140.76 — v1.0
- ✓ SPH-STP optymalizator transferu bufora — v1.0
- ✓ Model Device z fazami 1..F i cyklem UP/DOWN — v1.0

### Active

<!-- Current scope. Building toward these in v1.1. -->

- [ ] Interaktywne CLI z komendami `/help`, `/strategies`, `/run`
- [ ] Komenda `/custom` ładująca plik `.py` z funkcją strategii
- [ ] Komenda `/batch` uruchamiająca symulację dla wielu seedów z agregacją statystyk
- [ ] Wrapper `RationalAgent` z weto'em ujemnego oczekiwanego zysku
- [ ] Tryb porównawczy `with-agent`/`without-agent` z delta KPI w raporcie
- [ ] Generator raportu MD (konfiguracja + KPI + rozkład decyzji + porównanie)
- [ ] Generator wykresów PNG (matplotlib): rozkład decyzji per faza, KPI w czasie
- [ ] Konfigurowalne profile φ/ρ przez CLI lub plik konfiguracyjny
- [ ] Konfigurowalna funkcja waluacji g(u) — parametry K0/K1 lub preset

### Out of Scope

<!-- Explicit boundaries for v1.1. -->

- Web UI (Flask/FastAPI + przeglądarka) — odrzucone, CLI + raport MD są bardziej uniwersalne dla projektu akademickiego (raport otwiera się wszędzie bez instalacji)
- DSL deklaratywny dla custom strategii (YAML/JSON) — odrzucone, plik `.py` daje pełną elastyczność programisty
- Interaktywny kreator strategii (Q&A builder) — odrzucone na rzecz plików `.py`
- Wykresy interaktywne (Plotly/Bokeh) — PNG z matplotlib wystarczy, mniej zależności
- Zmiana modelu domeny (np. ciągłe fazy, inny SPH-STP) — to byłby nowy milestone v2.0
- Internacjonalizacja interfejsu — kod i interfejs zostają w języku polskim (zgodnie z v1.0)
- Persystencja wyników do bazy danych — raport MD jest jedynym artefaktem
- Web deploy / publikacja — projekt akademicki, uruchamiany lokalnie

## Context

**Domena:** projekt zaliczeniowy z przedmiotu Metody Probabilistyczne Eksploracji (sem. 4, WETI). Symuluje grę ekonomiczną opisaną w pracy J. Konorskiego o mediacji transferu płatnych usług świadczonych przez zawodne urządzenia autonomiczne.

**Pierwsza iteracja (v1.0):** Zbudowano `sph_sim.py` (363 linie, Python stdlib only) z 5 wbudowanymi strategiami i CLI argparse. Wyniki baseline zostały zebrane (`copilot_gsd_results.txt`, `gsd_copilot_resoning.txt`) i opisane w `Raport.pdf`. `naive --zeta 0.75` osiąga avg_val_last100 ≈ 92.

**Drugi cel (v1.1):** Po feedbacku prowadzącego program ma być **testbed'em dla innych użytkowników** — żeby ktoś inny (student, prowadzący, recenzent) mógł zaprojektować własną strategię i sprawdzić jak wypada względem baseline'u. Kluczowy element dydaktyczny: pokazanie że "racjonalny agent" odmawia działania przy ujemnym oczekiwanym zysku — co bezpośrednio odnosi się do warunku motywacyjnej zgodności (incentive compatibility) z teorii mechanizmów.

**Specyfikacja problemu i parametry:** `PROMPT_DLA_AGENTA.txt` (autorytatywne źródło dla modelu, KPI, baseline'u).

**Mapowanie kodu:** `.planning/codebase/` (ARCHITECTURE.md, STRUCTURE.md, STACK.md) — zaktualizowane 2025-01-31.

## Constraints

- **Tech stack**: Python 3.7+ — kontynuacja stacku v1.0; jedyna nowa zależność: `matplotlib` (wymagana, nie opcjonalna)
- **Język**: polski w komentarzach, komunikatach CLI i raporcie — spójność z istniejącym kodem i odbiorcami
- **Reprodukowalność**: każda symulacja musi być reprodukowalna przez `--seed` (zachowanie z v1.0)
- **Backwards compatibility**: istniejące CLI invocations z v1.0 (np. `python sph_sim.py --strategy naive --zeta 0.5`) muszą działać bez zmian
- **Bezpieczeństwo**: `importlib` ładuje pliki `.py` użytkownika — to jest świadome dopuszczenie wykonywania kodu (projekt lokalny, edukacyjny), ale loader powinien jasno komunikować że ładuje arbitralny Python
- **Output**: raport MD + PNG zapisywane w katalogu wyjściowym (domyślnie `./reports/<timestamp>/`); JSON output z v1.0 zachowany dla kompatybilności

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Form factor: CLI + raport MD + PNG (zamiast web UI) | Maksymalna uniwersalność, zero serwera, raport otwiera się wszędzie (GitHub/VSCode/Obsidian), zgodność ze stylem istniejącego skryptu | — Pending (v1.1) |
| Custom strategy: plik `.py` z funkcją (importlib) | Pełna elastyczność programisty, ten sam pattern co istniejące `strategy_*` w `sph_sim.py`, prosta sygnatura | — Pending (v1.1) |
| Rational Agent: wrapper veto + tryb porównawczy (default + flag) | Wymaganie projektowe — demonstrowalny dowód że weto chroni KPI; pokazuje incentive compatibility | — Pending (v1.1) |
| Wizualizacja: zawsze MD + zawsze PNG (matplotlib jako required dep) | User zdecydował "zawsze z plikiem matplotlib" — ujednolica output, brak warunków `--plot` | — Pending (v1.1) |
| Bootstrap v1.0 jako Validated requirements | Symulator istnieje i był testowany — traktujemy `sph_sim.py` jako shipped baseline | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-29 — Phase 8 (Documentation + Interactive Tutorial) complete; milestone v1.1 Agent CLI ready for closeout (all 8 phases shipped, 5 UAT gaps closed via 08-08/09/10).*
