# Phase 4: Rational Agent veto layer - Context

**Gathered:** 2026-05-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Wrapper `RationalAgent` opakowujący **każdą** strategię (built-in i custom) i override'ujący rekomendację `COMMIT` → `ABSTAIN` (z osobnym licznikiem `VETO`), gdy oczekiwany zysk netto dla danej iteracji jest ujemny:

```
E[zysk_i] = (1 - φ_i) · p_i  -  κ  -  φ_i · ρ_i
```

gdzie `p_i = (h(dev.phase) / total_h) · expected_P` — **identyczna formuła i ten sam parametr `expected_P`** co w `strategy_incentive` (`sphsim/strategies/incentive.py:6-18`).

Agent jest **domyślnie włączony** dla wszystkich strategii w CLI one-shot i REPL `run`; wyłączany flagą `--no-agent` (CLI) lub poprzez tryb `without-agent` w `compare`. Tryb porównawczy (`--compare-agent` CLI + `compare <nazwa>` REPL) uruchamia tę samą strategię raz z agentem, raz bez, i drukuje delta KPI w jednej tabeli (5 metryk × 3 kolumny `with | without | Δ`). Licznik veto'wanych decyzji jest śledzony per Device (`dev.n_vetoed`) i agregowany do `veto_per_phase: {1: N1, 2: N2, ...}` + `n_vetoed_total` w wyniku symulacji. `format_human` zyskuje nową sekcję "VETO przez RationalAgent — rekomendacje COMMIT odrzucone per faza".

**Scope:**
- Nowy moduł `sphsim/agent/rational.py` z `RationalAgent` klasą i funkcją `wrap_with_agent(strategy_fn, expected_P) -> wrapped_fn` (closure-based pure wrapper, zero zmian w `SPHSimulator`).
- Pole `dev.n_vetoed` w `Device` (paralelnie do `n_commit`/`n_abstain`/`n_delivered`/`n_failed` — `sphsim/core/device.py:17-20`).
- `simulator.run()` agreguje `veto_per_phase` i `n_vetoed_total` analogicznie do `ic_per_phase` (`simulator.py:121-138`); zwraca te pola w wyniku.
- Flagi CLI: `--no-agent` (boolean store_true, poza mutex), `--compare-agent` (boolean store_true, poza mutex). `--expected_P` reuse z `strategy_incentive` (args.py:51) — wspólny worek `--param`/argparse dla strategii i agenta.
- REPL komenda `compare <nazwa> [k=v ...]` (bez slasha per D-17) — symetryczna do `run <nazwa>` z Phase 3 D-41.
- Aktualizacja `scripts/regression_check.py` — dodaje `--no-agent` do każdej z 8 inwokacji baseline_v1 (fixtures pozostają niezmienione).
- Aktualizacja `sphsim/cli/output.py` `format_human` — nowa sekcja "VETO przez RationalAgent" (tabela: Faza | COMMIT zgłoszone | VETO | % zaweto'wanych). JSON: nowe pola `veto_per_phase`, `n_vetoed_total`, opcjonalnie `comparison` (przy `--compare-agent`).
- Modyfikacja `format_human` żeby obsłużyć `comparison` block z `--compare-agent`.

**Out of scope (zostawiamy dla Phase 5-7):**
- Override `--phi`/`--rho`/`--valuation`/`--K0`/`--K1` z linii poleceń (Phase 5 — agent w Phase 4 używa `DEFAULT_PHI`/`DEFAULT_RHO` z `sphsim/config.py`).
- Generator raportu MD (Phase 6 użyje `veto_per_phase` i `n_vetoed` do plot'u `decision_distribution.png` z 3 kategoriami).
- Batch runner (Phase 7 — `compare` w Phase 4 jest jednoseed'owy).
- Persistencja wyników `compare` do plików (jednorazowy stdout, ewentualnie `--json`).
- Zmiana sygnatury `strategy_fn` lub jakichkolwiek pól wymaganych dla custom strategii — Phase 4 NIE łamie Phase 3 kontraktu (D-47).

</domain>

<decisions>
## Implementation Decisions

### Estymator p_i (Area 1)
- **D-53:** **`p_i = (h(dev.phase) / total_h) · expected_P`** — verbatim ta sama formuła co `strategy_incentive` (`incentive.py:12,16`). `total_h = sum(h(j+1) * l_prev[j])` (j ∈ 0..F-2, gdzie `l_prev[j]` to liczba dostawców w fazie j+1 z poprzedniego cyklu). `h(i) = i^alpha` (z `simulator.py:15`). Numeryczna spójność: gdy `strategy = incentive`, agent zwraca identyczną decyzję jak strategia (oba self-veto przy tych samych warunkach) — `dev.n_vetoed` dla incentive będzie 0 w praktyce.
- **D-54:** **Wspólny `--expected_P`** — istniejąca flaga CLI z `strategy_incentive` (args.py:51, default 100.0 = DEFAULT_K0) jest reuse'owana dla agenta. Brak nowej flagi `--agent_P`. W REPL: `run naive expected_P=100 zeta=0.5` — `params` dict zawiera oba (agent czyta `params['expected_P']`, strategy czyta swoje params). Single source of truth — nie ma ryzyka rozbieżności między incentive a agentem.
- **D-55:** **`total_h = 0` → skip veto (allow COMMIT)** — gdy `sum(l_prev) = 0` (pierwszy cykl symulacji, brak historii providerów), agent stosuje fallback `total_h = 1.0` (identycznie do `incentive.py:13-14`) i kontynuuje obliczenia. Konsekwencja: w pierwszym cyklu agent z reguły nie weto'uje (mała `total_h` daje duże `p_i` → `E[zysk] > 0`). To jest zgodne z duchem teorii: bez danych historycznych agent ufa strategii.
- **D-56:** **Brak special case dla `strategy_incentive`** — agent owija wszystkie strategie identycznie. Dla `incentive` wrapper jest no-op'em (oba zwracają to samo COMMIT/ABSTAIN dla każdej rekomendacji bo formuła i `expected_P` są identyczne). `n_vetoed = 0` dla incentive jest poprawnym empirycznym dowodem że strategia jest self-incentive-compatible (`compare incentive` powinien dać delta KPI ≈ 0 — dydaktyczny insight).
- **D-57:** **Guard `phi[idx] >= 1.0` i `idx >= len(phi)` → veto** — verbatim z `incentive.py:9-11`. Agent zwraca `ABSTAIN` (i inkrementuje `n_vetoed`) gdy `dev.phase - 1 >= len(phi)` (faza poza zakresem — uznajemy za awarię konfiguracji) lub `phi[idx] >= 1.0` (faza zawsze fail — `E[zysk] = -κ - ρ_i < 0` matematycznie wymusza veto, guard tylko skraca obliczenia).

### Default mode + compare UX + regression (Area 2)
- **D-58:** **Agent default-on** — `python sph_sim.py --strategy naive --zeta 0.75` (bez `--no-agent`) automatycznie opakowuje strategię w `RationalAgent`. Zgodne z literalnym brzmieniem AGENT-01 (\"**domyślnie** opakowana\"). Wyłączenie: `--no-agent` (CLI flag, store_true, default=False = agent włączony). REPL `run naive zeta=0.75` — agent włączony zawsze; jeśli user chce surową strategię, używa `compare naive` (pokazuje obie wersje). Nie ma `--no-agent` w REPL `run` (deferred do Phase 5 / dyskretne — można dodać jako `run naive --no-agent zeta=0.75` jako Claude's Discretion implementation choice).
- **D-59:** **`scripts/regression_check.py` aktualizowany — fixtures BEZ zmian.** Skrypt regresji dodaje `--no-agent` do każdej z 8 inwokacji baseline_v1 (`naive --zeta 0.5`, `naive --zeta 0.75`, `threshold --max_phase 3`, `phase_prob --probs ...`, `incentive --expected_P 100`, `adaptive --s_target 10` + 2 środowiskowe). Fixtures `tests/fixtures/baseline_v1/*.json` zostają niezmienione (są oracle dla \"v1.0 / Phase 1 surowy simulator\"). Backwards compat CLI-04: `python sph_sim.py --strategy naive --zeta 0.5 --no-agent` daje identyczny output jak v1.0 — agent default-on nie łamie obietnicy, bo `--no-agent` jest udokumentowanym escape hatch'em do trybu v1.0.
- **D-60:** **`--compare-agent` (CLI flag, poza mutex)** — boolean store_true. Działa z `--strategy <name>` i `--custom <path>` (dwa pełne run'y, ten sam seed, ten sam params). Mutex check: `--compare-agent` + `--no-agent` = argparse error (`Cannot use --compare-agent with --no-agent`). `--compare-agent` + `--json` = JSON ma top-level klucz `comparison` (zamiast `metrics`); patrz D-62. `--compare-agent` przy `--interactive` = argparse error (mutex bez `--interactive`).
- **D-61:** **REPL `compare <nazwa> [k=v ...]`** — nowa komenda w `SPHShell` (paralelnie do `run` z Phase 3 D-41). Składnia identyczna jak `run`. Działa dla built-in i custom strategii (custom zarejestrowana przez `custom <path>` wcześniej w sesji). Bez slasha (D-17). `do_help` aktualizowany — dodatkowa linia: `compare <nazwa> [k=v ...]       — Porównaj strategię z i bez RationalAgent (delta KPI).`
- **D-62:** **Format porównania — delta KPI table (5 metryk × 3 kolumny).** Human-readable:
  ```
  ┌────────────────────────────────┬──────────────┬──────────────┬──────────────┐
  │ KPI                            │ with-agent   │ without      │ Δ (with-no)  │
  ├────────────────────────────────┼──────────────┼──────────────┼──────────────┤
  │ avg_val_last100                │       92.00  │       85.30  │       +6.70  │
  │ cum_val_total                  │      9200.0  │      8530.0  │      +670.0  │
  │ avg_net_profit                 │      12.40  │      -3.20   │     +15.60   │
  │ delivery_ratio                 │      88.0%  │       62.5%  │      +25.5%  │
  │ avg_providers_l100             │       45.2  │        38.7  │        +6.5  │
  ├────────────────────────────────┴──────────────┴──────────────┴──────────────┤
  │ Veto'wano: N COMMIT-ów; with-agent bije without-agent: ✓ TAK / ✗ NIE       │
  └─────────────────────────────────────────────────────────────────────────────┘
  ```
  Werdykt na końcu (`✓ TAK` / `✗ NIE`) opiera się na `avg_net_profit` — jeśli `with-agent > without-agent` to ✓. To jest dydaktyczne empiryczne potwierdzenie dla SC #5. JSON: `{"comparison": {"with_agent": {...}, "without_agent": {...}, "delta": {...}, "agent_helps": true|false}}`.

### VETO bookkeeping (Area 3)
- **D-63:** **`dev.n_vetoed` jako 5-te pole licznikowe na Device** — dodane do dataclass `Device` (`sphsim/core/device.py:17-20`) paralelnie do `n_commit`, `n_abstain`, `n_delivered`, `n_failed`. Default 0. Inkrementowane w wrapperze agenta (closure ma dostęp do `dev` przez argument funkcji strategy_fn). Nie inkrementuje się `n_abstain` gdy veto — to **rozróżnione kategorie** (no double-count). Phase 6 plot `decision_distribution.png` rozróżnia 3 grupy: `n_commit` (sukcesy + failures już są w `n_delivered`/`n_failed`), `n_abstain` (strategy zwróciła ABSTAIN), `n_vetoed` (strategy zwróciła COMMIT, agent zaweto'wał).
- **D-64:** **`veto_per_phase` agregacja w `simulator.run()`** — paralelnie do `ic_per_phase` (`simulator.py:121-138`). Po pętli T-cykli, agent agreguje `dev.veto_phase_stats` (nowy dict na Device, schemat `{phase: count}`) do dictu `veto_per_phase = {1: N1, 2: N2, ..., F-1: N_{F-1}}` (tylko fazy z `count > 0` lub wszystkie fazy z zerami — Claude's Discretion: preferuj wszystkie fazy z zerami dla spójności wykresu). `n_vetoed_total = sum(veto_per_phase.values())` jako scalar. Oba pola w returned dict z `simulator.run()`.
- **D-65:** **Po veto Device.status = DOWN, down_left = 1** — identyczna mechanika jak ABSTAIN (`simulator.py:69-72`). Veto = override decyzji do ABSTAIN per AGENT-02; device traci cykl, regeneruje się tak samo. Różnica TYLKO w licznikach (`n_vetoed++` zamiast `n_abstain++`). Implementacyjnie: wrapper zwraca `'ABSTAIN'` do simulator (simulator nie wie o veto), ale BEFORE zwrócenia, wrapper inkrementuje `dev.n_vetoed` i `dev.veto_phase_stats[dev.phase] += 1`. Simulator widzi ABSTAIN i odpowiednio przesuwa stan; potem `n_abstain` jednak NIE inkrementuje — to wymaga lekkiej modyfikacji simulator (patrz Code Context).
- **D-66:** **`format_human` nowa sekcja "VETO przez RationalAgent"** — wstawiona po istniejącej sekcji "ZGODNOŚĆ MOTYWACYJNA (IC)" w `output.py:39-54`. Tylko gdy `n_vetoed_total > 0` (jeśli agent wyłączony lub nigdy nie weto'wał, sekcja pominięta — czysty output dla `--no-agent`). Tabela:
  ```
    VETO przez RationalAgent — rekomendacje COMMIT odrzucone per faza:
    ─────────────────────────────────────────────────────────────
    Faza       COMMIT zgłoszone      VETO     % zaweto'wanych
    ─────────────────────────────────────────────────────────────
       1                     245       12             4.9%
       2                     198       45            22.7%
       ...
    ─────────────────────────────────────────────────────────────
    Łącznie zaweto'wano: 87 COMMIT-ów z 642 zgłoszonych (13.6%).
  ```
  Wartości: `COMMIT zgłoszone = veto_per_phase[ph] + commits[ph]` (z `ic_per_phase`). `% zaweto'wanych = veto / (veto + commits)`. Działa równolegle z istniejącą sekcją IC — obie sekcje pokazują różne aspekty (IC: czy delivered COMMIT-y są zyskowne; VETO: ile COMMIT-ów agent w ogóle nie wpuścił).
- **D-67:** **JSON output schema (backwards compat)** — nowe top-level pola w `format_json` (output.py:5-13): `'veto_per_phase': {1: N, 2: N, ...}`, `'n_vetoed_total': int`, `'agent_enabled': bool`. Istniejące pola (`avg_val_last100`, `cum_val_total`, `avg_net_profit`, `delivery_ratio`, `avg_providers_l100`, `sus_final`, `ic_per_phase`) NIE zmieniają się. Backwards compat: `--no-agent` daje `veto_per_phase: {}`, `n_vetoed_total: 0`, `agent_enabled: false` — JSON ma te pola ale są puste/false, co nie łamie parserów z v1.0 (oni je zignorują, nowe klucze są optional). Decyzja kluczowa dla CLI-04 + Phase 1 regression: `regression_check.py` porównuje JSON exact-match, więc pola muszą się pojawiać CONSISTENTLY (zawsze, nawet gdy puste). Fixtures regenerowane? NIE — pola te są DODAWANE do fixtures jako `"veto_per_phase": {}, "n_vetoed_total": 0, "agent_enabled": false` (jednorazowy patch fixtures + commit; regression check pozostaje bit-exact match). Alternatywa: `regression_check.py` ignoruje 3 nowe klucze (Claude's Discretion na rzecz prostszej implementacji bez regenu fixtures).

### Claude's Discretion
- **Architektura wrappingu** — Pure wrapper closure-based. Nowy moduł `sphsim/agent/__init__.py` + `sphsim/agent/rational.py`. Eksport: `RationalAgent` (klasa) i `wrap_with_agent(strategy_fn: Callable, expected_P: float) -> Callable` (factory). Wrapper jest **closure** (nie klasą) zwracającą funkcję o tej samej sygnaturze co `strategy_fn` — simulator widzi to jako zwykłą strategię, zero zmian w `SPHSimulator.__init__` lub `run()`. Klasa `RationalAgent` przechowuje stan (counter, expected_P) i metoda `__call__` realizuje wrapping (alternatywnie czysta funkcja-closure — Claude wybierze przy implementacji).
- **VETO counter dispatch** — Wrapper inkrementuje `dev.n_vetoed` i `dev.veto_phase_stats[ph]++` PRZED zwróceniem `'ABSTAIN'`. Simulator zobaczy `ABSTAIN` i wykona standardową ścieżkę ABSTAIN (status DOWN, down_left=1). Problem: simulator inkrementuje `dev.n_abstain` na końcu (simulator.py:70) — wrapper musi temu zapobiec. Opcje: (a) wrapper zwraca specjalny string `'VETO'` i simulator dostaje guard `if decision == 'VETO': ... (nie ++n_abstain)`; (b) wrapper modyfikuje `dev.n_abstain -= 1` po fakcie (hack); (c) refactor simulator: usuwa `n_abstain++`, agent/wrapper sam to robi. **Wybór (a)** — najbardziej eksplicytne, simulator dostaje 3-stanowy interface (`COMMIT`/`ABSTAIN`/`VETO`), guard 5 linii w simulator. Zachowanie dla VETO = identyczne jak ABSTAIN (DOWN 1 cykl), tylko inny licznik. To wymaga LEKKIEGO refactoru simulator — udokumentowane w D-65 i Code Context.
- **`--no-agent` w REPL `run`** — Per D-58, deferred do Phase 5 (jako część configurable env override). Phase 4 REPL `run` zawsze używa agenta. Jeśli user chce surową strategię w REPL, używa `compare <name>` (drugi wiersz tabeli pokazuje without-agent). Wystarczające dla SC #1-5.
- **`--compare-agent` interakcja z `--seed`** — Oba run'y używają tego samego `--seed` (default 42). Deterministyczne — z agentem może być inny stan końcowy (mniej COMMIT-ów, mniej downtime, więcej UP), ale to jest pożądane. Decyzja: NIE re-seedować w środku, JEDEN seed na wywołanie. `simulator.run()` jest niezależne między dwoma wywołaniami (`random.seed(seed)` w `__init__` resetuje stan).
- **Lokalizacja sekcji "VETO" w `format_human`** — Po istniejącej sekcji "ZGODNOŚĆ MOTYWACYJNA (IC)" (`output.py:39-54`). To naturalne sąsiedztwo: IC pokazuje per-phase profitability ex-post; VETO pokazuje per-phase agent intervention ex-ante. Razem dają pełen obraz dydaktyczny.
- **`comparison` block w JSON** — Strukturalnie: `{"comparison": {"with_agent": {<full metrics dict>}, "without_agent": {<full metrics dict>}, "delta": {<KPI: with - without>}, "agent_helps": bool}}` na top-level (zastępuje `metrics` w trybie compare). `--json` + `--compare-agent` = wyłącznie `comparison` (nie `metrics`). Konsumenci JSON wykrywają tryb przez obecność klucza `comparison`.
- **Verdict logic dla `agent_helps`** — `agent_helps = (with.avg_net_profit > without.avg_net_profit)`. To dydaktycznie najistotniejsza metryka (SC #5 dokładnie ten KPI cytuje). Można alternatywnie sprawdzać `delivery_ratio` lub `avg_val_last100` — Claude wybierze przy implementacji, ale `avg_net_profit` jest preferred (zysk netto = istota incentive compatibility).
- **Test coverage** — `tests/test_agent.py` (nowy plik) z minimum 8 przypadkami: (1) wrapper nie zmienia ABSTAIN, (2) wrapper nie weto'uje gdy E[zysk] > 0, (3) wrapper weto'uje gdy E[zysk] < 0, (4) `n_vetoed` inkrementuje, `n_abstain` NIE, (5) `total_h = 0` → no veto, (6) `phi[idx] >= 1.0` → veto, (7) `idx >= len(phi)` → veto, (8) `incentive` + wrapper = idempotent. Plus 2 integration testy: (9) `--compare-agent` wytwarza JSON z `comparison` blokiem, (10) `--no-agent` daje `n_vetoed_total = 0`.
- **`STRATEGY_META` dla agenta** — Agent NIE ma `STRATEGY_META` (nie jest strategią). `--expected_P` jest udokumentowane w `args.py` jako parametr strategii `incentive` + opcjonalny parametr dla agenta gdy włączony. Help text aktualizowany: `[incentive|agent] Oczek. płatność (def 100.0)`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specification & State
- `.planning/PROJECT.md` — Constraint "polski w komentarzach, komunikatach CLI" (komunikaty agenta + sekcja "VETO" + tabela compare po polsku); Constraint "Python 3.7+ stdlib only" (zero nowych zależności w Phase 4); Constraint "Backwards compatibility: istniejące CLI invocations z v1.0 muszą działać bez zmian" (D-59 mechanism: `--no-agent` escape hatch); Key Decision "Rational Agent: wrapper veto + tryb porównawczy" (Phase 4 jest implementacją tej decyzji).
- `.planning/REQUIREMENTS.md` §"AGENT" — AGENT-01 (wrapper liczy E[zysk]), AGENT-02 (veto gdy E[zysk] < 0), AGENT-03 (`--no-agent` flag), AGENT-04 (`veto_per_phase` w wyniku), AGENT-05 (`/compare` lub `--compare-agent` delta KPI). **Uwaga:** REQUIREMENTS używa `/compare` — D-17 z Phase 2 zmienia na komendę bez slasha (`compare <nazwa>`); intent zachowany.
- `.planning/ROADMAP.md` §"Phase 4" — 5 Success Criteria. SC #1 (every strategia default-wrapped) — D-58. SC #2 (`--no-agent` CLI + tryb without-agent w `compare`) — D-58/D-60/D-61. SC #3 (`veto_per_phase` w human + JSON) — D-64/D-66/D-67. SC #4 (`/compare` lub `--compare-agent` tabela delta) — D-60/D-61/D-62. SC #5 (`with-agent` ma wyższy `avg_net_profit` w demo scenario, np. `incentive --expected_P 30`) — empiryczny dowód, weryfikowany przez `agent_helps` boolean w JSON.
- `.planning/STATE.md` — milestone v1.1 status. Phase 3 complete, brak blocking concerns dla Phase 4.

### Prior Phase Outputs (już istnieją w repo, niezmienialne tutaj)
- `sphsim/core/simulator.py` (151 linii) — `SPHSimulator.__init__` przyjmuje `strategy_fn` jako argument (`simulator.py:8`); `run()` wywołuje `strategy_fn(dev, l_prev, self.s, self.phi, self.kappa, self.rho, self.h, self.params)` (simulator.py:44-47). Phase 4 LEKKO modyfikuje simulator (D-65, Claude's Discretion (a)): dodaje guard dla 3-stanowego decision = `'VETO'` (zachowanie identyczne jak ABSTAIN ale bez `n_abstain++`); dodaje agregację `veto_per_phase` paralelnie do `ic_per_phase` (`simulator.py:121-138`).
- `sphsim/core/device.py` — `Device` dataclass z 5 polami licznikowymi (`n_commit`, `n_abstain`, `n_delivered`, `n_failed` + 2 koszty `earnings`/`costs`). Phase 4 dodaje **6-te pole licznikowe `n_vetoed: int = 0`** + dict `veto_phase_stats = {}` w `__post_init__` (paralelnie do `phase_stats`).
- `sphsim/strategies/incentive.py` (28 linii) — **GŁÓWNA inspiracja matematyczna**. `strategy_incentive` używa identycznej formuły co `RationalAgent`. `expected_P` parameter (default 100.0 = DEFAULT_K0) reuse'owany w Phase 4. Walidacja guard: `if idx >= len(phi) or phi[idx] >= 1.0: return 'ABSTAIN'` (D-57 verbatim).
- `sphsim/strategies/__init__.py` — `STRATEGIES` mutable dict + `BUILTIN_STRATEGIES` frozenset (Phase 3 D-49). Phase 4 NIE modyfikuje registry — agent nie jest strategią, opakowuje strategie.
- `sphsim/cli/args.py` (65 linii) — Phase 4 dodaje: (1) `--no-agent` (boolean, default False, poza mutex), (2) `--compare-agent` (boolean, default False, poza mutex; mutex argparse-check: nie z `--no-agent`, nie z `--interactive`). Update help text dla `--expected_P` (informuje o reuse przez agenta).
- `sphsim/cli/main.py` (73 linii) — Phase 4 modyfikuje obie branches (built-in i custom) żeby przed budową `SPHSimulator` opakować strategy_fn w `wrap_with_agent(...)` gdy `not args.no_agent`. Nowa funkcja `run_compare(args, strategy_fn, name, params)` dla `--compare-agent` (2x build SPHSimulator, raz z agentem, raz bez, agregacja delta).
- `sphsim/cli/repl.py` (256 linii) — Phase 4 dodaje `do_compare(arg)` (~30 linii, kopiuje wzorzec `do_run` z D-41). Modyfikuje `do_help` (dodaje linię `compare ...`). `do_run` zawsze wrap'uje agentem (D-58).
- `sphsim/cli/output.py` (65 linii) — Phase 4 modyfikuje: (1) `format_human` — nowa sekcja "VETO przez RationalAgent" po sekcji "ZGODNOŚĆ MOTYWACYJNA" (D-66). (2) `format_human` — obsługa `comparison` block (gdy `res['comparison']` istnieje, generuje tabelę 5×3 zamiast standardowego output'u). (3) `format_json` — nowe top-level pola `veto_per_phase`, `n_vetoed_total`, `agent_enabled` (D-67); gdy `comparison` istnieje, zastępuje `metrics` blokiem `comparison`.
- `sphsim/config.py` — `DEFAULT_K0 = 100.0` (=default `expected_P`); `DEFAULT_PHI`, `DEFAULT_RHO`. Phase 4 NIE modyfikuje config.
- `scripts/regression_check.py` — Phase 4 dodaje `--no-agent` do każdej z 8 inwokacji baseline (D-59). **Fixtures `tests/fixtures/baseline_v1/*.json` muszą zostać zaktualizowane jednym patchem dodającym `"veto_per_phase": {}, "n_vetoed_total": 0, "agent_enabled": false` do każdego JSON** (D-67 alternative: regression skip 3 nowe klucze przy compare — Claude's Discretion przy implementacji).
- `tests/test_strategy_meta_consistency.py` — invariant test (Phase 2 D-25). Phase 4 NIE modyfikuje — agent nie ma `STRATEGY_META`.
- `tests/test_loader.py` — testy loadera (Phase 3). Phase 4 NIE modyfikuje — Phase 4 dodaje nowy `tests/test_agent.py` (10 przypadków, Claude's Discretion).

### Phase 1-3 Decision Documents (carry-forward)
- `.planning/phases/01-refactoring-foundation/01-CONTEXT.md` — D-04 (stdlib only), D-13 (plain functions + dicts dla strategii), D-14 (`STRATEGIES` mutable global).
- `.planning/phases/02-interactive-cli-shell/02-CONTEXT.md` — D-17 (komendy bez slasha — `compare`, nie `/compare`), D-22 (prompt `sph>`, bez ANSI), D-24/D-25/D-26 (`STRATEGY_META` schema — Phase 4 nie modyfikuje, agent nie jest strategią).
- `.planning/phases/03-custom-strategy-loader/03-CONTEXT.md` — D-44 (mutex `--interactive | --strategy | --custom` — Phase 4 dodaje flagi POZA mutex), D-46 (`sphsim.custom.<name>` private namespace dla custom strategii — Phase 4 wrap działa identycznie dla custom i built-in), D-47 (sygnatura strategy_fn `(dev, l, s, phi, kappa, rho, h, p)` — wrapper zachowuje tę sygnaturę).

### Stdlib documentation
- `dataclasses` module — https://docs.python.org/3/library/dataclasses.html (dodanie `n_vetoed: int = 0` i modyfikacja `__post_init__` w `Device`).
- `argparse` module — https://docs.python.org/3/library/argparse.html (`action='store_true'`, custom mutex checks dla `--compare-agent` ∧ `--no-agent`).

### v1.0 Reference
- `PROMPT_DLA_AGENTA.txt` — definicja formuły `E[zysk_i] = (1-φ_i)·p_i - κ - φ_i·ρ_i` jest dokładnie ta, którą `RationalAgent` implementuje (sekcja "Reguła decyzyjna racjonalnego agenta" w specyfikacji).

### Codebase Maps
- `.planning/codebase/ARCHITECTURE.md` §"Strategy Function Signature" + §"Simulation Engine Layer" — Phase 4 dodaje **wrapper layer** między Strategy a Simulation Engine. Strategy interface nie zmienia się; wrapper jest closure z tą samą sygnaturą.
- `.planning/codebase/CONVENTIONS.md` §"Function Design" — pure functions dla strategii. `wrap_with_agent` zwraca pure function (closure) — zgodne z konwencją.
- `.planning/codebase/STACK.md` — "Standard Library Only" — Phase 4 nie dodaje zależności. Phase 6 nadal jest first-time matplotlib.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`strategy_incentive` (`sphsim/strategies/incentive.py:6-18`)** — formuła `E[zysk] = (1-φ_i)·p_i - κ - φ_i·ρ_i` już zaimplementowana. Wrapper agent może literally skopiować logikę (sumowanie `total_h`, computowanie `exp_pay`, comparing `net > 0`). Sygnatura wrappera = sygnatura strategy_fn.
- **`expected_P` parameter (`incentive.py:15` + `args.py:51`)** — istniejący float param, default 100.0 (=DEFAULT_K0). Reuse'owany przez agenta (D-54) — wspólne źródło prawdy.
- **`Device` dataclass (`sphsim/core/device.py:9-43`)** — 5 pól licznikowych. Phase 4 dodaje 6-te (`n_vetoed`) + dict `veto_phase_stats` (paralelnie do istniejącego `phase_stats` w `__post_init__:23-24`).
- **`ic_per_phase` aggregation (`simulator.py:113-138`)** — wzór agregacji per-phase ze stats z Device. Phase 4 robi paralelną agregację `veto_per_phase` (paste-and-modify pattern).
- **`SPHSimulator.__init__` (`simulator.py:8`)** — `strategy_fn` przekazywany jako argument. Wrapper jest **closure** o tej samej sygnaturze (`Callable[..., str]`) — simulator pozostaje nieświadomy że dostaje opakowaną strategię.
- **`format_human` (`output.py:16-64`)** — Phase 4 wpina się PO sekcji IC (output.py:54). Tabela VETO ma analogiczny shape (Faza | metryki | werdykt).
- **`format_json` (`output.py:5-13`)** — dodaje nowe top-level klucze (D-67) bez zmiany istniejących. Backwards compat dla v1.0 JSON parsers.
- **`scripts/regression_check.py`** — 8 inwokacji + fixtures. Dodanie `--no-agent` do każdej inwokacji to ~8 linii zmiany w skrypcie (single source of truth dla regression).

### Established Patterns
- **Pure functions + closure pattern (Phase 1 D-13)** — `wrap_with_agent(strategy_fn, expected_P) -> wrapped_fn` zwraca closure, zero state w globalu, łatwo testowalne w izolacji.
- **Strategy registry pattern (Phase 1 D-14)** — Phase 4 NIE modyfikuje `STRATEGIES` dict. Agent owija strategie PO odczycie z registry (w `main.py` lub `repl.py`), zanim trafią do `SPHSimulator`.
- **Polski w komunikatach (PROJECT.md Constraint)** — wszystkie komunikaty UI (nazwa sekcji "VETO przez RationalAgent", header tabeli compare, werdykt `✓ TAK / ✗ NIE`) po polsku. Identyfikatory w kodzie (`RationalAgent`, `wrap_with_agent`, `n_vetoed`, `veto_per_phase`) po angielsku (spójne z Phase 1-3).
- **Stdlib only** — Phase 4 nie dodaje nic. Używamy `dataclasses`, `argparse`, `cmd` (już importowane w `repl.py`).
- **Fail-fast walidacja + argparse mutex** — `--compare-agent` ∧ `--no-agent` → argparse error (verbatim z Phase 2 D-27/D-28 + Phase 3 D-44).
- **Komendy REPL bez slasha (Phase 2 D-17)** — `compare <nazwa>`, NIE `/compare`. Verify script dla Phase 4 (Claude's Discretion) sprawdza formę bez slasha.

### Integration Points

**1. `sphsim/agent/rational.py` (nowy plik) — wrapper factory**
```python
# Pure closure-based wrapper. Zero state w globalu.
def wrap_with_agent(strategy_fn, expected_P):
    """Opakowuje strategy_fn w RationalAgent veto layer.
    
    Wrapper liczy E[zysk] = (1-phi_i)*p_i - kappa - phi_i*rho_i.
    Gdy strategia zwraca COMMIT a E[zysk] < 0, wrapper override'uje
    na 'VETO' (simulator interpretuje VETO jak ABSTAIN ale z osobnym
    licznikiem n_vetoed/veto_phase_stats).
    """
    def wrapped(dev, l, s, phi, kappa, rho, h, p):
        # Strategy decyduje first.
        decision = strategy_fn(dev, l, s, phi, kappa, rho, h, p)
        if decision != 'COMMIT':
            return decision  # ABSTAIN passthrough.
        # Compute E[zysk] (verbatim z incentive.py:9-17).
        idx = dev.phase - 1
        if idx >= len(phi) or phi[idx] >= 1.0:
            dev.n_vetoed += 1
            dev.veto_phase_stats[dev.phase] = dev.veto_phase_stats.get(dev.phase, 0) + 1
            return 'VETO'
        total_h = sum(h(j+1) * (l[j] if j < len(l) else 0) for j in range(len(l)))
        if total_h <= 0:
            total_h = 1.0  # D-55: skip veto (allow COMMIT) gdy brak danych
        exp_pay = (h(dev.phase) / total_h) * expected_P
        net = (1 - phi[idx]) * exp_pay - kappa - phi[idx] * rho[idx]
        if net < 0:
            dev.n_vetoed += 1
            dev.veto_phase_stats[dev.phase] = dev.veto_phase_stats.get(dev.phase, 0) + 1
            return 'VETO'
        return 'COMMIT'
    return wrapped
```

**2. `sphsim/core/simulator.py` modyfikacja — VETO guard + agregacja**
```python
# W run() pętli (po simulator.py:47), zamiast `if decision == 'COMMIT'`:
if decision == 'COMMIT':
    # ... istniejący kod (commit_phase, kappa, rho, ...) — bez zmian
elif decision == 'VETO':
    # Identyczne jak ABSTAIN ale NIE inkrementuje n_abstain (D-65).
    # n_vetoed inkrementowane w wrapperze (przed return).
    dev.status = 'DOWN'
    dev.down_left = 1
else:  # 'ABSTAIN' lub nieznane
    dev.n_abstain += 1
    dev.status = 'DOWN'
    dev.down_left = 1

# Po pętli T-cykli (po simulator.py:138, paralelnie do ic_results agregacji):
veto_per_phase = {}
n_vetoed_total = 0
for dev in self.devices:
    for ph, count in dev.veto_phase_stats.items():
        veto_per_phase[ph] = veto_per_phase.get(ph, 0) + count
        n_vetoed_total += count

# W return dict (simulator.py:140-150), dodaj:
return {
    # ... istniejące pola
    'veto_per_phase':     veto_per_phase,
    'n_vetoed_total':     n_vetoed_total,
}
```

**3. `sphsim/core/device.py` modyfikacja — n_vetoed + veto_phase_stats**
```python
@dataclass
class Device:
    # ... istniejące pola
    n_vetoed: int = 0  # NOWE pole, paralelnie do n_abstain
    
    def __post_init__(self):
        self.phase_stats = {}
        self.veto_phase_stats = {}  # NOWY dict, schema: {phase: count}
```

**4. `sphsim/cli/main.py` modyfikacja — wrap przed build SPHSimulator**
```python
from sphsim.agent.rational import wrap_with_agent

# W obu branches (built-in i custom), po wybraniu strategy_fn:
if not args.no_agent:
    strategy_fn = wrap_with_agent(strategy_fn, args.expected_P)
sim = SPHSimulator(... strategy_fn=strategy_fn ...)

# Compare branch (nowa funkcja):
def run_compare(args, name, raw_strategy_fn, params):
    """Uruchamia 2x: with-agent i without-agent. Returns dict z comparison."""
    common = dict(nU=args.nU, nSUS=args.nSUS, K0=DEFAULT_K0, K1=K1,
                  F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
                  phi=DEFAULT_PHI, rho=DEFAULT_RHO, params=params, seed=args.seed)
    sim_with = SPHSimulator(strategy_fn=wrap_with_agent(raw_strategy_fn, args.expected_P), **common)
    res_with = sim_with.run()
    sim_without = SPHSimulator(strategy_fn=raw_strategy_fn, **common)
    res_without = sim_without.run()
    return {
        'comparison': {
            'with_agent': {k: v for k, v in res_with.items() if k not in ('history', 'devices')},
            'without_agent': {k: v for k, v in res_without.items() if k not in ('history', 'devices')},
            'delta': {kpi: res_with[kpi] - res_without[kpi] for kpi in ['avg_val_last100','cum_val_total','avg_net_profit','delivery_ratio','avg_providers_l100']},
            'agent_helps': res_with['avg_net_profit'] > res_without['avg_net_profit'],
        }
    }
```

**5. `sphsim/cli/repl.py` — do_compare (paralelnie do do_run)**
```python
def do_compare(self, arg):
    """Porównaj strategię z i bez RationalAgent. compare <nazwa> [k=v ...]"""
    tokens = arg.split()
    if not tokens:
        print("Użycie: compare <nazwa> [param=wartość ...].")
        return
    name, *kv_tokens = tokens
    if name not in STRATEGIES:
        print(f"Strategia '{name}' nie istnieje. Dostępne: {', '.join(STRATEGIES.keys())}.")
        return
    # ... budowa params z parse_params_from_meta (jak w do_run)
    # ... 2x SPHSimulator (with + without), agregacja delta, print tabela
```

**6. `sphsim/cli/output.py` — sekcja VETO + comparison renderer**
```python
# W format_human, po sekcji IC (output.py:54), DODAJ:
veto_pp = res.get('veto_per_phase', {})
n_vetoed = res.get('n_vetoed_total', 0)
if n_vetoed > 0:
    lines.append(f"\n  VETO przez RationalAgent — rekomendacje COMMIT odrzucone per faza:")
    lines.append(f"  {sep}")
    lines.append(f"  {'Faza':>6}  {'COMMIT zgłoszone':>18}  {'VETO':>8}  {'% zaweto':>10}")
    lines.append(f"  {sep}")
    ic = res.get('ic_per_phase', {})
    total_committed_phases = 0
    for ph in sorted(set(list(veto_pp.keys()) + list(ic.keys()))):
        commits = ic.get(ph, {}).get('commits', 0)
        vetos = veto_pp.get(ph, 0)
        total = commits + vetos
        pct = (vetos / total * 100) if total > 0 else 0
        lines.append(f"  {ph:>6}  {total:>18}  {vetos:>8}  {pct:>9.1f}%")
        total_committed_phases += total
    lines.append(f"  {sep}")
    pct_total = (n_vetoed / max(total_committed_phases, 1)) * 100
    lines.append(f"  Łącznie zaweto'wano: {n_vetoed} COMMIT-ów z {total_committed_phases} zgłoszonych ({pct_total:.1f}%).")

# Nowa funkcja format_compare(args, comparison_data, K1):
def format_compare(args, comp, K1):
    """Render tabeli 5×3 dla --compare-agent."""
    with_, without_, delta = comp['with_agent'], comp['without_agent'], comp['delta']
    # ... 5 wierszy z formatted floats, werdykt agent_helps
```

**7. `scripts/regression_check.py` modyfikacja — `--no-agent` w każdej inwokacji**
```python
# Każda z 8 inwokacji w INVOCATIONS list (Phase 1 D-08/D-11):
INVOCATIONS = [
    ('naive_zeta05',    ['--strategy', 'naive', '--zeta', '0.5', '--no-agent', '--json']),
    ('naive_zeta075',   ['--strategy', 'naive', '--zeta', '0.75', '--no-agent', '--json']),
    # ... wszystkie 8 z dodatkowym '--no-agent'
]
# Alternatywa (Claude's Discretion przy implementacji): regression skipuje 3 nowe pola
# (veto_per_phase, n_vetoed_total, agent_enabled) przy compare — bez zmian fixtures.
```

**8. Argparse mutex check dla `--compare-agent` ∧ `--no-agent`**
```python
# W args.py, po parse_args() ale przed return:
args = p.parse_args()
if args.compare_agent and args.no_agent:
    p.error("Flagi --compare-agent i --no-agent są wzajemnie wykluczające.")
return args
```

</code_context>

<specifics>
## Specific Ideas

- **Formuła agenta = formuła incentive (D-53/D-54)** — verbatim copy z `incentive.py:9-17`. Single source of truth, zero divergencji numerycznej.
- **`expected_P` wspólne dla incentive i agenta (D-54)** — `--expected_P 100` w CLI / `expected_P=100` w REPL trafia do `params` dict; strategie incentive używają go w swojej logice, agent czyta `params.get('expected_P', DEFAULT_K0)` lub flagę `args.expected_P` bezpośrednio.
- **3-stanowy decision interface w simulator (D-65, Claude's Discretion (a))** — `'COMMIT' | 'ABSTAIN' | 'VETO'`. VETO ma identyczną mechanikę DOWN jak ABSTAIN ale dziedziczy `n_vetoed` zamiast `n_abstain`. Lekkie 5-linijkowe rozszerzenie pętli w `simulator.run()`.
- **Default-on agent (D-58)** — naturalny default zgodny z duchem dydaktycznym v1.1 (\"agent broni KPI\"). Escape hatch `--no-agent` dla regression i porównań.
- **Werdykt `agent_helps` = `with.avg_net_profit > without.avg_net_profit`** — dydaktycznie najsilniejszy sygnał SC #5 (incentive compatibility = positive net profit per device).
- **Demo scenario dla SC #5** — `incentive --expected_P 30 --compare-agent` (low expected_P → incentive strategy zwraca dużo COMMIT'ów które agent veto'uje → with-agent ma mniej failure costs → wyższy avg_net_profit). Phase 4 verify script dostaje ten przypadek jako acceptance test.
- **JSON backwards compat (D-67)** — nowe pola `veto_per_phase`, `n_vetoed_total`, `agent_enabled` DODAWANE do każdego JSON output (nawet `--no-agent`, gdzie są puste). Decyzja KLUCZOWA dla CLI-04: stabilna struktura JSON, parsery z v1.0 ignorują nowe klucze.

</specifics>

<deferred>
## Deferred Ideas

- **Override env params w REPL (`--phi`, `--rho`, `--K0`, `--K1`, `--T`)** — Phase 5. Phase 4 `compare` używa `DEFAULT_*` env params (jak Phase 3 `run`).
- **Plot `decision_distribution.png` z 3 kategoriami (COMMIT/ABSTAIN/VETO)** — Phase 6. Phase 4 dostarcza dane (`veto_per_phase`, `n_vetoed`) — Phase 6 je rysuje.
- **Generator raportu MD z sekcją compare** — Phase 6. Phase 4 dostarcza JSON `comparison` block (D-62 schema) który Phase 6 może bezpośrednio render'ować jako MD tabelę.
- **Batch compare (`--batch --compare-agent --seeds 10`)** — Phase 7. Phase 4 compare jest jednoseed'owy. Phase 7 może wywołać `run_compare()` w pętli i agregować deltę KPI.
- **`--no-agent` w REPL `run`** — Phase 5 (część configurable env). Phase 4 REPL `run` zawsze z agentem; `compare` pokazuje obie wersje.
- **Konfigurowalny estymator `p_i`** — np. `--agent-estimator {static|running_avg|on_the_fly}`. Phase 4 hardcoduje "static" (D-53). Można dodać w późniejszej fazie jeśli badania porównawcze tego wymagają.
- **Visual indicator w REPL że agent jest włączony** — np. prompt `sph[+agent]>` vs `sph>`. Odrzucone — prostota Phase 2 D-22 (prompt `sph>` bez ANSI).
- **`compare <custom_strategy>` z dwoma różnymi path'ami** — Odrzucone. `compare` służy do porównania jednej strategii z/bez agenta, NIE dwóch różnych strategii.
- **`agent_helps` werdykt na wielu KPI (nie tylko `avg_net_profit`)** — Phase 6 może rozszerzyć (np. multi-criterion). Phase 4 wybiera `avg_net_profit` (SC #5 cytuje literally).
- **Confirmation prompt przy `--compare-agent` (długi run, 2x T cykli)** — Odrzucone (friction). User zna swój `--T`.
- **Per-cycle veto log do pliku** — Odrzucone (Phase 4 jest jednorazowy snapshot). Phase 6 dostarcza wykres time-series jeśli potrzeba.
- **Konfiguracja "ścisłości" agenta (np. `--agent-threshold X` zamiast `E[zysk] < 0`)** — Odrzucone. AGENT-02 literally cytuje `E[zysk_i] < 0`, brak parametryzacji.
- **Wrapper jako klasa z `__call__` zamiast czystej closure** — Claude's Discretion przy implementacji. Preferuj closure (prostsze, bezstanowe między wywołaniami w jednym cyklu).

</deferred>

---

*Phase: 4-Rational Agent veto layer*
*Context gathered: 2026-05-27*
