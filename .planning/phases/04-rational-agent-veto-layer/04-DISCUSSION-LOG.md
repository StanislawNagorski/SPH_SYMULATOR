# Phase 4: Rational Agent veto layer - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-27
**Phase:** 4-Rational Agent veto layer
**Areas discussed:** Estymator p_i, Default + compare UX + regression, VETO bookkeeping

---

## Area Selection

User wybrał: "nie chcem omawiac wybierz te ktore bys mi rekomendowal" → Claude wybrał 3 obszary z najsilniejszą rekomendacją (P0/P1 priority), odkładając architekturę wrappingu jako Claude's Discretion.

| Option | Description | Selected |
|--------|-------------|----------|
| Estymator p_i | Jak agent oblicza p_i (P0 — bez tego formuła nie istnieje) | ✓ |
| VETO jako kategoria | 3-cia decyzja vs side-counter (P1 — Phase 6 plot dependency) | ✓ |
| Default + compare UX + regression | Default-on, --no-agent, --compare-agent, regression fixtures (P0 — backwards compat) | ✓ |
| Architektura wrappingu | Pure wrapper vs simulator-integrated (P2 — Claude wybiera w D-65) | (Claude's Discretion) |

---

## Estymator p_i

### Q1: Jak agent oblicza p_i?

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse `expected_P` | `p_i = (h(dev.phase) / total_h) * expected_P` — identycznie jak `strategy_incentive` (incentive.py:12,16). Numeryczna spójność. | ✓ |
| Running average z historii | Adaptacyjne, ale cold start problem dla pierwszych N cykli | |
| On-the-fly z l_prev + SPH-STP | Czysta teoria, ale hard-coded zależność od modelu | |

**User's choice:** Reuse `expected_P` (Rec)
**Notes:** Decyzja zapewnia że `strategy_incentive` + wrapper są idempotentne (oba self-veto przy tych samych warunkach).

### Q2: `expected_P` source w CLI/REPL?

| Option | Description | Selected |
|--------|-------------|----------|
| Wspólny `--expected_P` | Reuse istniejącej flagi z incentive (args.py:51, default 100.0) dla wszystkich strategii | ✓ |
| Osobna flaga `--agent_P` | Jawna separacja, ale ryzyko rozbieżności między incentive a agentem | |
| Hardcoded = DEFAULT_K0 | Zero boilerplate, ale niereguowalne | |

**User's choice:** Wspólny `--expected_P` (Rec)
**Notes:** Single source of truth między incentive strategy i agent.

### Q3: `total_h = 0` edge case?

| Option | Description | Selected |
|--------|-------------|----------|
| Skip veto (allow COMMIT) | Verbatim z incentive.py:13-14 (`total_h = 1.0` fallback). Agent ufa strategii bez danych. | ✓ |
| Veto wszystko (zachowawczo) | Anti-pattern — system nigdy nie odpali (chain reaction) | |
| Fallback p_i = K0 / nU | Ad hoc, brak teoretycznego uzasadnienia | |

**User's choice:** Skip veto (Rec)
**Notes:** Spójność z `strategy_incentive` fallback.

### Q4: Wrap `strategy_incentive` (która sama veto'uje)?

| Option | Description | Selected |
|--------|-------------|----------|
| Nic specjalnego | Wrapper zawsze owija. Dla incentive wrapper jest no-op (oba zgadzają się). `n_vetoed = 0` w praktyce. | ✓ |
| Skip wrap dla incentive | Special case, łamie AGENT-01 obietnicę | |
| Warning + skip | Spam komunikatami przy iteracji | |

**User's choice:** Nic specjalnego (Rec)
**Notes:** Wrap'owanie incentive jest dydaktyczne — `compare incentive` pokazuje że strategia jest self-incentive-compatible (Δ ≈ 0).

### Q5: `phi[idx]` guard?

| Option | Description | Selected |
|--------|-------------|----------|
| Idx z guardą | Verbatim z incentive.py:9-11 (`if idx >= len(phi) or phi[idx] >= 1.0: veto`) | ✓ |
| Idx tylko, bez phi=1 guard | Mniej guardów, math sam się broni (E[zysk] < 0 przy phi=1) | |

**User's choice:** Idx z guardą (Rec)
**Notes:** Pełna spójność z `strategy_incentive`.

---

## Default mode + compare UX + regression

### Q1: Agent default-on?

| Option | Description | Selected |
|--------|-------------|----------|
| TAK, default-on | Zgodne z AGENT-01 wording. `--no-agent` jako escape hatch dla regression. | ✓ |
| Default-off, opt-in | `--with-agent` flag — łamie AGENT-01 | |
| Default-on REPL, off CLI | Niespójność trybów | |

**User's choice:** TAK, default-on (Rec)
**Notes:** Naturalny default dla dydaktycznej wartości v1.1.

### Q2: Backwards compat z regression fixtures?

| Option | Description | Selected |
|--------|-------------|----------|
| Update regression_check.py | Dodaje `--no-agent` do 8 inwokacji. Fixtures bez zmian. | ✓ |
| Re-generate fixtures with agent | Tracimy oracle v1.0 — łamie CLI-04 | |
| Dual fixtures (v1 + v2) | 2x utrzymania, overhead | |

**User's choice:** Update regression_check.py (Rec)
**Notes:** Fixtures zostają oracle dla "v1.0 / Phase 1 surowy simulator".

### Q3: Compare interface? (Claude wybrał — user pominął dyskusję)

| Option | Description | Selected |
|--------|-------------|----------|
| `--compare-agent` (CLI) + `compare <nazwa>` (REPL) | Symetryczne do `--strategy`/`run <name>` z Phase 2/3 | ✓ |
| Tylko CLI flag | REPL command odłożony do Phase 5 | |
| Tylko REPL command | Brak CLI mode dla compare (sztuczne ograniczenie) | |

**Claude's choice:** Oba (Rec) — D-60 + D-61

### Q4: Format porównania? (Claude wybrał)

| Option | Description | Selected |
|--------|-------------|----------|
| Delta KPI table (5×3) | with-agent \| without-agent \| Δ kolumny + verdict `agent_helps` | ✓ |
| Dwa pełne raporty side-by-side | Trudne do skanowania, dużo redundantnych danych | |

**Claude's choice:** Delta KPI table (Rec) — D-62

---

## VETO bookkeeping

### Q1: VETO jako Device counter? (Claude wybrał)

| Option | Description | Selected |
|--------|-------------|----------|
| 3-cia kategoria na Device | `dev.n_vetoed` jako 5-te pole licznikowe. Phase 6 plot wymaga 3 kategorii. | ✓ |
| Tylko side-channel w wrapperze | Nie ma per-device śladu, ale prostszy refactor Device | |

**Claude's choice:** 3-cia kategoria na Device (Rec) — D-63

### Q2: Output schema? (Claude wybrał)

| Option | Description | Selected |
|--------|-------------|----------|
| `veto_per_phase` dict + `n_vetoed_total` scalar | Mirror istniejącego `ic_per_phase` shape (simulator.py:121-138) | ✓ |
| Inline w `ic_per_phase` dict (nowy klucz `vetos`) | Łamie semantykę IC (IC = delivered profitability, VETO = ex-ante) | |

**Claude's choice:** Osobny `veto_per_phase` (Rec) — D-64

### Q3: Po veto Device.status? (Claude wybrał)

| Option | Description | Selected |
|--------|-------------|----------|
| DOWN + down_left=1 (jak ABSTAIN) | Identyczna mechanika — veto = override do ABSTAIN per AGENT-02 | ✓ |
| UP + skip cycle | Niezgodne z mechaniką sym (ABSTAIN → DOWN to invariant z v1.0) | |

**Claude's choice:** DOWN + down_left=1 (Rec) — D-65

### Q4: format_human output? (Claude wybrał)

| Option | Description | Selected |
|--------|-------------|----------|
| Nowa sekcja "VETO przez RationalAgent" po sekcji IC | Symetryczna do istniejącej IC tabeli (faza, count, %) | ✓ |
| Inline z IC table (dodanie kolumny VETO do IC tabeli) | Łamie semantykę IC, nadmiernie szeroka tabela | |
| Tylko w JSON, nie w human | Słabsza dydaktyka — user musi parsować JSON żeby zobaczyć | |

**Claude's choice:** Nowa sekcja po IC (Rec) — D-66

---

## Claude's Discretion

Pełna lista w CONTEXT.md `<decisions>` §"Claude's Discretion". Najważniejsze:

- **Architektura wrappingu** — Pure closure-based wrapper w nowym module `sphsim/agent/rational.py`. Funkcja `wrap_with_agent(strategy_fn, expected_P)` zwraca closure o sygnaturze `(dev, l, s, phi, kappa, rho, h, p) -> str` (3-stanowo: `'COMMIT'|'ABSTAIN'|'VETO'`).
- **3-stanowy decision interface w simulator** — Simulator dostaje guard `elif decision == 'VETO':` po istniejącym `if decision == 'COMMIT':`. VETO ma identyczną mechanikę DOWN jak ABSTAIN, różnica TYLKO w liczniku.
- **`--no-agent` w REPL `run`** — Phase 4 NIE dodaje. REPL `run` zawsze z agentem. Surowa strategia widoczna przez `compare <name>` (drugi wiersz tabeli). Deferred do Phase 5 jako część configurable env override.
- **JSON regression fix** — Albo patch fixtures (dodaje 3 nowe klucze `{}, 0, false` do każdego JSON), albo regression skipuje 3 nowe klucze przy compare. Decyzja przy implementacji.
- **Werdykt `agent_helps`** — `with.avg_net_profit > without.avg_net_profit` (SC #5 explicit).

## Deferred Ideas

Pełna lista w CONTEXT.md `<deferred>`. Top items:

- Override env params w REPL (`--phi`, `--rho`) → Phase 5
- Plot `decision_distribution.png` z 3 kategoriami → Phase 6
- Generator raportu MD z sekcją compare → Phase 6
- Batch compare (`--batch --compare-agent --seeds 10`) → Phase 7
- `--no-agent` w REPL `run` → Phase 5
- Konfigurowalny estymator p_i (static/running_avg/on_the_fly) → przyszłe milestone'y
- Per-cycle veto log do pliku → out of scope (jednorazowy snapshot)
