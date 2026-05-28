# Phase 6: Report + plots generator — Pattern Map

**Mapped:** 2026-05-28
**Files analyzed (new + modified):** 11 (6 new, 5 modified)
**Analogs found:** 10 / 11 (one new dependency surface — matplotlib — has no in-repo analog)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `sphsim/report/__init__.py`            | sub-package entry | file-I/O (side-effect orchestrator) | `sphsim/agent/__init__.py`              | exact (sub-package shape) |
| `sphsim/report/markdown.py`            | formatter / serializer | transform (dict → MD string) | `sphsim/cli/output.py`                  | exact (role + flow) |
| `sphsim/report/plots.py`               | renderer (matplotlib) | file-I/O (PNG side-effect) | (no analog — first matplotlib surface)  | none |
| `sphsim/core/device.py` (MOD)          | model / counter | event-driven counter | existing `veto_phase_stats` (same file)| exact (1:1 mirror) |
| `sphsim/core/simulator.py` (MOD)       | orchestrator / aggregator | aggregation | existing `veto_per_phase` aggregation (same file) | exact (1:1 mirror) |
| `sphsim/cli/main.py` (MOD)             | CLI entry | request-response + side-effect call | existing `sim.run()` → `print(format_*)` sequence | exact (same call site shape) |
| `sphsim/cli/repl.py` (MOD)             | REPL | request-response | `do_run` / `do_compare` (same file) — fake_args audit only | exact |
| `tests/test_report.py`                 | test (multi-class) | unittest | `tests/test_env.py`                     | exact (7-class multi-behavior pattern) |
| `tests/test_simulator_abstain.py`      | test (counter aggregation) | unittest | `tests/test_agent.py`                   | exact (counter+aggregation test set) |
| `scripts/verify_phase6.sh`             | shell exit gate | shell | `scripts/verify_phase5.sh`              | exact (check() framework verbatim) |
| `scripts/regression_check.py` (MOD)    | regression compare | subprocess + diff | `SKIP_KEYS` evolution (same file)       | exact (additive extension) |
| `.gitignore` (MOD)                     | config | static | (no analog — single-line addition)      | trivial |

---

## 1. Sub-package layout pattern

Codebase ma **3 sub-pakiety** do porównania:

| Sub-package | Files | Public surface | Pattern type | Recommendation for `report/` |
|-------------|-------|----------------|--------------|------------------------------|
| `sphsim/agent/` | `__init__.py` (5 linii) + `rational.py` | jedna funkcja `wrap_with_agent` re-exported via `__all__` | **Small focused — 1 public entry, 1 impl module** | **MIRROR THIS** |
| `sphsim/cli/`   | `__init__.py` (1 linia, empty) + `args.py` + `main.py` + `output.py` + `repl.py` | brak re-exportów, importy zawsze fully-qualified | Multi-file but flat | overkill dla 3-modułowego raportu |
| `sphsim/strategies/` | `__init__.py` z `STRATEGIES` dict + 5 strategy files + `loader.py` | runtime-mutowalny rejestr | Registry-based | nie pasuje — raport NIE ma rejestru |

### Decyzja — `sphsim/report/` ma mirrorować `sphsim/agent/`:

Z `sphsim/agent/__init__.py:1-5` skopiuj wzorzec verbatim:
```python
"""Rational agent — wrapper veto-ujący COMMIT przy E[zysk] < 0 (Phase 4, AGENT-01..05)."""
from sphsim.agent.rational import wrap_with_agent

__all__ = ['wrap_with_agent']
```

Phase 6 odpowiednik (`sphsim/report/__init__.py`):
```python
"""Generator raportu MD + wykresów PNG (Phase 6, REPORT-01..03, PLOT-01..03)."""
# Public entry point + private helpers split na 2 moduły (markdown.py, plots.py).
# write_report koordynuje obie strony: mkdir + render MD + savefig PNG.
from sphsim.report.api import write_report   # lub inline w __init__.py — patrz §D.11 RESEARCH

__all__ = ['write_report']
```

**Caveat:** `agent/__init__.py` ma TYLKO re-export (logika w `rational.py`). `report/__init__.py` w RESEARCH §D.11 trzyma logikę `write_report(...)` INLINE w `__init__.py` (zamiast osobnego `api.py`). To akceptowalna wariacja — 3 moduły zamiast 4, prostsze imports. Planner decyduje finalnie po `discuss-phase`.

---

## 2. New-file analog map

### `sphsim/report/__init__.py` → analog `sphsim/agent/__init__.py:1-5`

**What to copy:**
- Docstring style: jedna linijka po polsku, wymienia fazę + ID requirementów (np. "REPORT-01..03, PLOT-01..03")
- Single public function exposure via `__all__`
- Import style: `from sphsim.report.X import Y` (fully-qualified, NIE relative)

**What differs:**
- `write_report` ma **side effects** (mkdir + write files); `wrap_with_agent` jest pure closure
- Body NIE jest pure re-export — Phase 6 `__init__.py` zawiera `write_report` body (RESEARCH §D.11)
- Wymaga `import os` + `import datetime` + `from pathlib import Path` (agent ma tylko `from sphsim.config import DEFAULT_K0`)
- Try/except wrapper wokół całego body — wszystkie wyjątki łapane i logowane na stderr (RESEARCH §D.11 "Raises: Nothing")

### `sphsim/report/markdown.py` → analog `sphsim/cli/output.py:27-49` (`format_config_header`)

**What to copy (literal patterns):**

1. **Function signature + return contract** — z `output.py:27`:
```python
def format_config_header(args, K0, K1, phi, rho) -> str:
    """Serializuje konfigurację środowiska do tabeli Markdown (ENV-03, SC-4).
    Zwracany string to walidna tabela MD — Phase 6 może go wkleić bezpośrednio do report.md.
    """
```
Phase 6 `render_report(args, res, params, K1, mode='single') -> str` ma identyczny shape.

2. **F-string MD table builder** — z `output.py:31-49`:
```python
phi_str = ', '.join(f'{v:.2f}' for v in phi)
rho_str = ', '.join(f'{v:.2f}' for v in rho)
k1_display = '∞' if K1 == float('inf') else str(K1)
lines = [
    '## Konfiguracja środowiska',
    '',
    '| Parametr | Wartość |',
    '|----------|---------|',
    f'| nU       | {args.nU} |',
    ...
]
return '\n'.join(lines)
```
Skopiuj LITERALNIE technikę `lines = [...]; return '\n'.join(lines)` dla każdej sekcji raportu (§C.8 RESEARCH ma 7 sekcji).

3. **`format_compare` ASCII table** — z `output.py:52-120`. Tu Phase 6 NIE kopiuje ASCII (ramki `'='*66`, em-dashy) — **konwertuje na MD** (`| col | col |` + `|-----|-----|`). Logika delta KPI (`output.py:66-72` lista kpis z format specifiers `'{:>12.2f}'`) jest reusable AS-IS dla sekcji 7 raportu — tylko zamień formatter ASCII na MD.

4. **`format_human` IC-per-phase loop** — z `output.py:150-165` (rendering `ic_per_phase` jako tabeli):
```python
for ph in sorted(ic):
    d = ic[ph]
    ic_mark = '  ✓' if d['ic_satisfied'] else '  ✗'
    ...
```
Sekcja 4 raportu (Rozkład decyzji per faza, §C.8) używa identycznej pętli `for ph in sorted(phases)` ale renderuje 4 kolumny MD zamiast 7 kolumn ASCII.

5. **Polish strings + Unicode glyphs** — `'## Konfiguracja środowiska'`, `'∞'`, `'κ (kappa)'`, `'α (alpha)'`, `'φ (phi)'`, `'ρ (rho)'` (`output.py:35-47`). Phase 6 KONTYNUUJE tę konwencję — PROJECT.md constraint "polski w komentarzach, komunikatach CLI i raporcie".

**What differs:**
- `format_config_header` zwraca jedną sekcję MD (≈11 linii). `render_report` zwraca **cały raport** (≈100 linii, 7 sekcji).
- `render_report` reuses `format_config_header` 1:1 jako sekcję 1 (`output.py:27` import → wkleić zwrócony string verbatim do listy `lines`).
- `format_compare` zwraca ASCII (output.py:74-119); Phase 6 sekcja 7 zwraca MD table — nowy renderer.

**Concrete pattern dla `render_report` (composition):**
```python
# sphsim/report/markdown.py
from sphsim.cli.output import format_config_header

def render_report(args, res, params, K1, mode='single') -> str:
    sections = []
    sections.append(f"# Raport symulacji SPH — {args.strategy} ({_timestamp(...)})")
    sections.append("")
    sections.append(format_config_header(args, args.K0, K1, args.phi, args.rho))  # SEKCJA 1 REUSE
    sections.append("")
    sections.append(_render_strategy_section(args, params))                       # SEKCJA 2
    sections.append("")
    sections.append(_render_kpi_table(res))                                       # SEKCJA 3
    sections.append("")
    sections.append(_render_decision_table(res))                                  # SEKCJA 4
    sections.append("")
    sections.append("![Rozkład decyzji](decision_distribution.png)")              # SEKCJA 4 fig
    sections.append("")
    sections.append("![Przebieg KPI](kpi_timeseries.png)")                        # SEKCJA 5
    sections.append("")
    sections.append(_render_baseline_comparison(res))                             # SEKCJA 6
    if mode == 'compare':
        sections.append("")
        sections.append(_render_compare_section(res['comparison']))               # SEKCJA 7
    return '\n'.join(sections)
```

### `sphsim/report/plots.py` → analog (NONE — first matplotlib surface)

Brak istniejącego kodu matplotlib w repo. RESEARCH §B.5 + §B.6 dostarczają kompletny pseudokod — planner przekazuje do executora verbatim. **Patterns to enforce mimo braku analoga:**

- **Top-of-file backend pin** (§B.7 RESEARCH):
  ```python
  import matplotlib
  matplotlib.use('Agg')          # MUST be first matplotlib call
  import matplotlib.pyplot as plt
  ```
- **Polish docstrings + Polish axis labels** — zgodne z resztą kodu (`'Faza urządzenia'`, `'Cykl symulacji'`, RESEARCH §B.5-6)
- **`plt.close(fig)` po każdym savefig** (§B.5 RESEARCH; bez tego memory leak w batch mode — Phase 7 territory)
- **Path-based API**: funkcje przyjmują `path: Path` jako ostatni argument (mirror `sphsim/strategies/loader.py` które używa `Path` w `load_custom`)

### `tests/test_report.py` → analog `tests/test_env.py:1-336`

**What to copy (skeleton):**

1. **Header boilerplate** — `test_env.py:1-19`:
```python
"""
Unit i integration tests dla Phase 6 (Report + plots generator).
Pokrywa REPORT-01..03, PLOT-01..03.
Stdlib only: unittest + subprocess + json + os + sys + tempfile.
"""
import json, os, subprocess, sys, unittest
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

PROJECT_ROOT = Path(_PROJECT_ROOT)
MONOLITH = PROJECT_ROOT / 'sph_sim.py'

def _run_sph(*args, **kwargs):
    return subprocess.run(
        [sys.executable, 'sph_sim.py'] + list(args),
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        **kwargs
    )
```

2. **Multi-class structure** — `test_env.py` ma 7 klas (`TestPhiRhoParsing`, `TestValuationDispatch`, `TestConfigHeader`, etc.). Phase 6 idzie 1:1:
   - `TestReportDirectoryCreation` (REPORT-01)
   - `TestReportMarkdownContent` (REPORT-02 — sekcje 1-6)
   - `TestReportCompareSection` (REPORT-03 — sekcja 7)
   - `TestPlotDecisionDistribution` (PLOT-01)
   - `TestPlotKpiTimeseries` (PLOT-02)
   - `TestPlotsLinkedFromMd` (PLOT-03)
   - `TestSphsimNoReportOptOut` (cross-cutting — env var safety)

3. **`_make_args` helper pattern** — `test_env.py:247-250`:
```python
def _make_args(self):
    import argparse
    return argparse.Namespace(nU=250, nSUS=20, T=1000, kappa=0.25, alpha=1, seed=42)
```
Phase 6 rozszerza o pola wymagane przez `write_report`: `strategy`, `K0`, `K1`, `phi`, `rho`, `valuation`, `no_agent`, `json`, `verbose`. Pełna lista w **§4 fake_args audit** poniżej.

4. **`subprocess.run` per-test exit-code + JSON-parse pattern** — `test_env.py:64-70, 100-106` (powtarza się ≈10× w pliku). Phase 6 używa tego samego shape ale dodaje `env={**os.environ, 'SPHSIM_NO_REPORT': '1'}` żeby NIE śmiecić w `./reports/` podczas testów uruchamiających subprocess (RESEARCH §G.18).

**What differs:**
- Phase 6 testy muszą **monkeypatchować `Path('reports')`** dla testów unit (NIE subprocess) — `unittest.mock.patch` na `sphsim.report.write_report` lub `tempfile.TemporaryDirectory` + `os.chdir`. Brak istniejącego analoga w repo (żaden test w `tests/` nie chdir-uje).
- Pierwszy raz w repo testy generują **binary artifacts** (PNG). Asercja `Path(...).exists() and Path(...).stat().st_size > 0` jest nowa, ale trywialna.

### `tests/test_simulator_abstain.py` → analog `tests/test_agent.py:55-105`

**What to copy:**

1. **Test helper stub strategies** — `test_agent.py:45-52`:
```python
def _stub_abstain(dev, l, s, phi, kappa, rho, h, p):
    return 'ABSTAIN'
def _stub_commit(dev, l, s, phi, kappa, rho, h, p):
    return 'COMMIT'
```
Phase 6 reuse: stub zwracający ABSTAIN dla wybranej fazy → assert `dev.abstain_phase_stats[phase] == N`.

2. **Counter assertion shape** — `test_agent.py:70-73`:
```python
out = w(dev, [10, 10, 10, 10], 10, phi, 1.0, rho, lambda i: i, {})
self.assertEqual(dev.n_vetoed, 0,
                 msg=f"n_vetoed musi pozostać 0 przy ABSTAIN passthrough, got {dev.n_vetoed}")
```
Phase 6 1:1 dla `dev.abstain_phase_stats`:
```python
self.assertEqual(dev.abstain_phase_stats, {3: 1},
                 msg=f"abstain_phase_stats po ABSTAIN faza 3 powinno być {{3: 1}}, got {dev.abstain_phase_stats}")
```

3. **Integration test via subprocess + JSON** — `test_agent.py` ma test 9 i 10 (compare-agent JSON, --no-agent JSON). Phase 6 dodaje test "after sim.run(), `result['abstain_per_phase']` zawiera sumy z `dev.abstain_phase_stats`".

**What differs:**
- Phase 4 testy `test_agent.py` testują **wrapper** (closure). Phase 6 testy testują **simulator aggregation** (orchestrator). Loci diff: instead of `wrap_with_agent(...)(...)` calls, Phase 6 tworzy `SPHSimulator(...).run()` i sprawdza `result['abstain_per_phase']`.

### `scripts/verify_phase6.sh` → analog `scripts/verify_phase5.sh:1-150`

**What to copy verbatim (lines 1-53 — skeleton):**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if command -v python >/dev/null 2>&1; then
    PY=python
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "FATAL: ani 'python' ani 'python3' nie ma w PATH" >&2
    exit 1
fi

trap 'rm -f /tmp/p6_*' EXIT   # ← p5_ → p6_

PASS=0
FAIL=0

check() {
    local desc="$1"
    local cmd="$2"
    if eval "$cmd" > /tmp/p6_check.log 2>&1; then
        echo "[PASS] $desc"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $desc"
        echo "       cmd: $cmd"
        echo "       log:"
        sed 's/^/         /' /tmp/p6_check.log | head -20
        FAIL=$((FAIL + 1))
    fi
}
```

**Section structure to mirror** (verify_phase5.sh:58-129 — 6 numbered sections):

1. `## 1. Regression backwards compat` → identyczna (1 check, ale z `SPHSIM_NO_REPORT=1` w env)
2. `## 2. Full test suite` → dodaj `test_report` i `test_simulator_abstain` checki
3. `## 3-6. SC checks` → Phase 6 SC #1..#5 z ROADMAP
4. (NEW) `## 7. PNG existence checks` — `[ -s ./reports/*/decision_distribution.png ]`
5. (NEW) `## 8. MD smoke parse` — `grep '^## ' ./reports/*/report.md | wc -l == 7`

**Phase 5 → Phase 6 token swaps:**
- `p5_` → `p6_` (trap cleanup namespace)
- `=== Phase 5: ... ===` → `=== Phase 6: Report + plots generator — verification ===`
- `Phase 5 verification: PASS=$PASS / FAIL=$FAIL` → `Phase 6 verification: ...`

**What differs:**
- Phase 6 musi dodać **cleanup `./reports/` before run** żeby PNG existence check był deterministyczny:
  ```bash
  rm -rf ./reports/  # NA POCZĄTKU, przed pierwszym sph_sim.py invocation
  ```
- Phase 6 musi uruchomić `sph_sim.py` **WITHOUT** `SPHSIM_NO_REPORT=1` w SC #1-#5 (żeby raport faktycznie powstał), ale **WITH** `SPHSIM_NO_REPORT=1` w sekcji 1 (regression check — żeby nie zaburzać porównania z fixturami).
- Regression check w Phase 5 nie używał env var override — Phase 6 musi to dodać:
  ```bash
  check "Regression: 8/8 baseline_v1 fixtures (Phase 6 SKIP_KEYS extended)" \
      "SPHSIM_NO_REPORT=1 $PY scripts/regression_check.py"
  ```
  Alternatywa: przekazać przez `regression_check.py`'s `subprocess.run(env=...)` — Phase 6 musi rozszerzyć `run_invocation` w `regression_check.py:101`, żeby przekazać `env={**os.environ, 'SPHSIM_NO_REPORT': '1'}` do subprocess.

---

## 3. Counter aggregation pattern (1:1 mirror Phase 4)

**Source for the pattern: `sphsim/core/device.py:23-26` + `sphsim/agent/rational.py:35-36, 50-51` + `sphsim/core/simulator.py:147-153`.**

### 3a. Device — add `abstain_phase_stats` field

Current `device.py:23-26`:
```python
def __post_init__(self):
    # Per-phase IC tracking: phase -> {commits, deliveries, failures, earnings, costs}
    self.phase_stats = {}
    self.veto_phase_stats = {}  # {phase: count} — Phase 4 D-64
```

Phase 6 mirror (add ONE line):
```python
def __post_init__(self):
    self.phase_stats = {}
    self.veto_phase_stats = {}      # {phase: count} — Phase 4 D-64
    self.abstain_phase_stats = {}   # {phase: count} — Phase 6 PLOT-01 (mirror veto_phase_stats)
```

### 3b. Simulator — increment in ABSTAIN branch

Current `simulator.py:75-78` (ABSTAIN branch):
```python
else:  # 'ABSTAIN' lub nieznany decision — failsafe (T-04-04)
    dev.n_abstain += 1
    dev.status = 'DOWN'
    dev.down_left = 1
```

Phase 6 mirror — dodaj 1 linijkę PO `dev.n_abstain += 1`:
```python
else:  # 'ABSTAIN' lub nieznany decision — failsafe (T-04-04)
    dev.n_abstain += 1
    dev.abstain_phase_stats[dev.phase] = dev.abstain_phase_stats.get(dev.phase, 0) + 1  # Phase 6 PLOT-01
    dev.status = 'DOWN'
    dev.down_left = 1
```

**WAŻNE — semantyka fazy:** Inkrementujemy `dev.phase` PRZED zmianą `dev.status = 'DOWN'` i przed `dev.phase = -1`. W tym momencie `dev.phase` to faza w której DECYZJA padła (1..F-1), NIE `-1`. To jest poprawne — `abstain_phase_stats` mapuje fazę-w-momencie-decyzji do liczby ABSTAIN.

### 3c. Simulator — aggregate to `abstain_per_phase`

Current `simulator.py:147-153` (Phase 4 VETO aggregation):
```python
# Aggregate per-phase VETO stats across all devices (Phase 4 D-64)
veto_per_phase = {}
n_vetoed_total = 0
for dev in self.devices:
    for ph, count in dev.veto_phase_stats.items():
        veto_per_phase[ph] = veto_per_phase.get(ph, 0) + count
        n_vetoed_total += count
```

Phase 6 mirror — wstaw IDENTYCZNY blok poniżej:
```python
# Aggregate per-phase ABSTAIN stats across all devices (Phase 6 PLOT-01)
abstain_per_phase = {}
for dev in self.devices:
    for ph, count in dev.abstain_phase_stats.items():
        abstain_per_phase[ph] = abstain_per_phase.get(ph, 0) + count
```

Brak `n_abstain_total` aggregation — `Device.n_abstain` jest już globalnie liczone w `simulator.py:76` i nie używane w sumie globalnej (różnica w stosunku do veto: `n_vetoed_total` istnieje dla wyświetlania w `format_human`; ABSTAIN total nie jest pokazywane w UI, więc plotter sumuje na żywo).

### 3d. Simulator — return dict extension

Current `simulator.py:155-167` (return dict — 11 kluczy):
```python
return {
    'avg_val_last100':    round(...),
    ...
    'veto_per_phase':     veto_per_phase,
    'n_vetoed_total':     n_vetoed_total,
    'history':            self.history,
    'devices':            self.devices,
}
```

Phase 6 — dodaj 1 klucz (między `veto_per_phase` a `history`):
```python
    'veto_per_phase':      veto_per_phase,
    'n_vetoed_total':      n_vetoed_total,
    'abstain_per_phase':   abstain_per_phase,   # Phase 6 PLOT-01 (mirror veto_per_phase)
    'history':             self.history,
    'devices':             self.devices,
```

**Total deltas for Phase 6 counter aggregation:**
- `device.py`: +1 linia (`__post_init__`)
- `simulator.py`: +1 linia (ABSTAIN branch increment) + 5 linii (aggregation block) + 1 linia (return dict key) = **+7 linii**
- Zero new imports, zero breaking changes — `abstain_per_phase` jest **purely additive** (mirror Phase 4 D-67 precedent).

---

## 4. `fake_args` audit (REPL Pitfall 2 prophylaxis)

RESEARCH §D.11 mówi że `write_report(args, res, params, K1, mode)` potrzebuje pól z `args`:
> `nU, nSUS, T, kappa, alpha, K0, K1, phi, rho, seed, valuation, strategy, no_agent, json`

### REPL `do_run` — `repl.py:220-225`:
```python
fake_args = argparse.Namespace(
    strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
    kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
    phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window',
    seed=42,
)
```

### REPL `do_compare` — `repl.py:288-293`:
```python
fake_args = argparse.Namespace(
    strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
    kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
    phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window',
    seed=42,
)
```

### Coverage audit table:

| Field needed by `write_report` | `do_run` (repl.py:220-225) | `do_compare` (repl.py:288-293) | Status |
|--------------------------------|----------------------------|--------------------------------|--------|
| `strategy`     | ✓ | ✓ | OK |
| `nU`           | ✓ | ✓ | OK |
| `nSUS`         | ✓ | ✓ | OK |
| `T`            | ✓ | ✓ | OK |
| `kappa`        | ✓ | ✓ | OK |
| `alpha`        | ✓ | ✓ | OK |
| `K0`           | ✓ (Phase 5 ENV-03 Pitfall 2 fix) | ✓ | OK |
| `phi`          | ✓ (Phase 5) | ✓ | OK |
| `rho`          | ✓ (Phase 5) | ✓ | OK |
| `seed`         | ✓ (Phase 5) | ✓ | OK |
| `valuation`    | ✓ (Phase 5) | ✓ | OK |
| `no_agent`     | ✓ (always `False` in REPL — T-04-20) | ✓ | OK |
| `verbose`      | ✓ (always `False` in REPL) | ✓ | OK |
| `json`         | ✗ **MISSING** | ✗ **MISSING** | **Phase 6 ADD** |
| `K1`           | n/a — przekazywane jako osobny argument do `write_report(args, res, params, K1)`, NIE z `args.K1` | n/a | OK (consume DEFAULT_K1 directly) |

### Phase 6 fix — extend BOTH `fake_args` blocks:

Po Phase 5 audycie, REPL fake_args jest **prawie kompletny** — brakuje JEDNEGO pola: `json`. To pole jest używane przez `format_json` (jeśli `args.json` istnieje, output to JSON). `write_report` per RESEARCH §D.11 **nie używa `args.json`** w body — ale stylistycznie wszystkie fake_args bloki muszą być spójne z `parse_args` namespace. Dodaj defensywnie:

```python
# repl.py:220-225 + repl.py:288-293 — dodaj `json=False,` na koniec
fake_args = argparse.Namespace(
    strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
    kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
    phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window',
    seed=42, json=False,   # Phase 6: defensive consistency z parse_args namespace
)
```

**Pitfall warning:** Jeśli planner doda flagę CLI `--no-report` (Claude's Discretion option), `fake_args` musi dostać też `no_report=False`. Phase 6 plan musi to wpisać do specyfikacji REPL Pitfall checks w `verify_phase6.sh` (mirror `verify_phase5.sh:131-137` Pitfall 2 gate).

---

## 5. JSON output extension pattern (Phase 4 + Phase 5 precedent)

**Source: `sphsim/cli/output.py:6-24` (`format_json`).**

### Phase 4 evolution (D-67):
Dodano:
- `metrics.agent_enabled` (line 22)
- `metrics.veto_per_phase`, `metrics.n_vetoed_total` (przez `**{k: v for k, v in res.items() if ...}` na line 21 — auto-include)
- `comparison` jako alternatywa zamiast `metrics` (lines 15-17)

### Phase 5 evolution (ENV-03):
Dodano do `env` bloku:
- `K0`, `phi`, `rho`, `seed`, `valuation` (lines 10-13)

### Phase 6 — recommended approach:

`format_json` automatycznie includuje wszystkie klucze z `res` przez `**{k: v for k, v in res.items() if k not in ('history', 'devices')}` (output.py:21). Czyli **`abstain_per_phase` pojawi się w `metrics` AUTOMATYCZNIE** bez żadnej zmiany w `output.py`. Phase 6 nie musi tknąć `format_json`.

### Decyzja dla `report_path` top-level key:

**Rekomendacja:** **NIE dodawać** `report_path` do JSON output. Powody:
1. ZGODNOŚĆ z separacją concerns — JSON to dane symulacji, ścieżka raportu to side-effect metadata.
2. SC#6 ROADMAP literally "JSON output zachowany". Dodanie klucza wymagałoby rozszerzenia `SKIP_KEYS` (kompatybilne z fixtures), ale to dodatkowy noise.
3. Path do raportu jest już printowany na stderr w polish banner ("Raport zapisany do: ...") — ten kanał istnieje.

**Jeśli planner decyduje inaczej** (discuss-phase): dodać klucz `report_path` jako `str(path)` w output.py:13 (w `out` dict, NIE w `env`), i rozszerzyć `SKIP_KEYS` o `'report_path'`. Zero impact na fixtures (additive only).

### Tylko **`abstain_per_phase`** trzeba dodać do `SKIP_KEYS` (patrz §6).

---

## 6. `SKIP_KEYS` evolution pattern

**Source: `scripts/regression_check.py:45-48`.**

```python
SKIP_KEYS = (
    'veto_per_phase', 'n_vetoed_total', 'agent_enabled',  # Phase 4 D-67 Strategia B
    'K0', 'phi', 'rho', 'seed', 'valuation',              # Phase 5 ENV-03 (D-PH5 SKIP-EXT, mirroring D-67)
)
```

### Pattern (3-step additive evolution):
1. Każda nowa faza dodaje WIERSZ z komentarzem `# Phase N <REQ-ID>` na końcu krotki.
2. Klucze ignorowane są w **każdym** dict podczas `deep_diff` (rekurencyjnie — `regression_check.py:67-68`).
3. Fixtures w `tests/fixtures/baseline_v1/` NIGDY nie są regenerowane — backward compat preserved.

### Phase 6 extension:

```python
SKIP_KEYS = (
    'veto_per_phase', 'n_vetoed_total', 'agent_enabled',  # Phase 4 D-67 Strategia B
    'K0', 'phi', 'rho', 'seed', 'valuation',              # Phase 5 ENV-03 (mirroring D-67)
    'abstain_per_phase',                                  # Phase 6 PLOT-01 (mirroring D-67)
    # Jeśli planner doda report_path do JSON output (§5 wyżej decision deferred):
    # 'report_path',                                      # Phase 6 REPORT-01 (mirroring D-67)
)
```

### Subprocess env override (osobna zmiana w tym samym pliku):

Current `regression_check.py:101`:
```python
full_args = [sys.executable, str(MONOLITH), *args, '--no-agent', '--seed', '42', '--json']
try:
    result = subprocess.run(
        full_args,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
```

Phase 6 musi dodać `env={**os.environ, 'SPHSIM_NO_REPORT': '1'}` żeby NIE generować raportów podczas regression check (8 subprocess invocations × 3 pliki = 24 zbędne pliki w `reports/`):

```python
import os  # już jest, ale upewnić się
...
result = subprocess.run(
    full_args,
    cwd=str(PROJECT_ROOT),
    capture_output=True,
    text=True,
    check=True,
    env={**os.environ, 'SPHSIM_NO_REPORT': '1'},   # Phase 6 — opt-out side effects in regression
)
```

To jest **DRUGI** add w `regression_check.py`, oprócz `SKIP_KEYS` extension. Plan Phase 6 musi spec'ować obie zmiany w jednym Plan-aksjonie (atomicity).

---

## 7. Verify-script template — `check()` framework verbatim

**Source: `scripts/verify_phase5.sh:18-53`.**

### Verbatim block to copy (modify only the `p5_` → `p6_` prefix):

```bash
#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  verify_phase6.sh — phase exit gate dla Phase 6 (Report + plots generator)
#  [opis SC #1..#5 + regression + tests]
#  Re-runnable po każdej zmianie w sphsim/ jako pre-flight przed merge'em.
#  Stdlib + POSIX coreutils only — bez nowych zależności (matplotlib wymagane runtime).
#  Exit code: 0 gdy wszystkie checks PASS, 1 gdy jakikolwiek FAIL.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

# Przejdź do project root (skrypt może być wywołany skądkolwiek).
cd "$(dirname "$0")/.."

# Wybierz interpreter Pythona — preferuj python, fallback na python3.
if command -v python >/dev/null 2>&1; then
    PY=python
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "FATAL: ani 'python' ani 'python3' nie ma w PATH" >&2
    exit 1
fi

# Cleanup tmp files + reports/ na exit (trap — nawet przy FAIL).
trap 'rm -f /tmp/p6_*' EXIT

PASS=0
FAIL=0

# Helper: uruchom komendę, drukuj [PASS] albo [FAIL] z hintem + ostatnimi 20 liniami log'u.
check() {
    local desc="$1"
    local cmd="$2"
    if eval "$cmd" > /tmp/p6_check.log 2>&1; then
        echo "[PASS] $desc"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $desc"
        echo "       cmd: $cmd"
        echo "       log:"
        sed 's/^/         /' /tmp/p6_check.log | head -20
        FAIL=$((FAIL + 1))
    fi
}
```

### Modifications vs `verify_phase5.sh`:

| Element | Phase 5 | Phase 6 |
|---------|---------|---------|
| Tmp namespace | `/tmp/p5_*` | `/tmp/p6_*` |
| Banner | `=== Phase 5: Configurable environment — verification ===` | `=== Phase 6: Report + plots generator — verification ===` |
| Summary | `Phase 5 verification: PASS=$PASS / FAIL=$FAIL` | `Phase 6 verification: ...` |
| Final blessing | `✓ Phase 5 ready for /gsd:verify-work` | `✓ Phase 6 ready for /gsd:verify-work` |

### NEW sections to add (no analog in verify_phase5.sh):

```bash
# ── 0. Pre-flight: clean ./reports/ żeby PNG existence check był deterministyczny ──
echo ""
echo "── 0. Pre-flight cleanup ──"
rm -rf ./reports/
echo "      reports/ cleaned"

# ── 7. PNG generation + existence (PLOT-01, PLOT-02) ──
echo ""
echo "── 7. SC #4-5: PNG generation (PLOT-01, PLOT-02) ──"
check "PNG: decision_distribution.png istnieje i ma >0 bajtów" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json > /dev/null && ls ./reports/*/decision_distribution.png | head -1 | xargs -I{} test -s {}"
check "PNG: kpi_timeseries.png istnieje i ma >0 bajtów" \
    "ls ./reports/*/kpi_timeseries.png | head -1 | xargs -I{} test -s {}"

# ── 8. Markdown smoke parse (REPORT-01..03) ──
echo ""
echo "── 8. SC #1-3: Markdown structure ──"
check "MD: report.md istnieje" \
    "ls ./reports/*/report.md | head -1 | xargs -I{} test -s {}"
check "MD: 6+ sekcji H2 ('^## ') w report.md" \
    "ls ./reports/*/report.md | head -1 | xargs grep -c '^## ' | { read n; [ \"\$n\" -ge 6 ] || exit 1; }"
check "MD: ![Rozkład decyzji] linkuje PNG (PLOT-03)" \
    "ls ./reports/*/report.md | head -1 | xargs grep -F '![Rozkład decyzji](decision_distribution.png)' > /dev/null"

# ── 9. Opt-out: SPHSIM_NO_REPORT=1 NIE tworzy plików ──
echo ""
echo "── 9. SC #6: SPHSIM_NO_REPORT=1 opt-out ──"
check "SPHSIM_NO_REPORT=1: NO new reports/ directory created" \
    "rm -rf ./reports && SPHSIM_NO_REPORT=1 $PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json > /dev/null && { [ ! -d ./reports/ ] || [ -z \"\$(ls -A ./reports/)\" ]; }"
```

### Same final summary block (verbatim from verify_phase5.sh:139-149):

```bash
echo ""
echo "════════════════════════════════════════"
echo "  Phase 6 verification: PASS=$PASS / FAIL=$FAIL"
echo "════════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
    echo "✗ Phase 6 NIE jest gotowe — popraw FAIL'e powyżej."
    exit 1
fi
echo "✓ Phase 6 ready for /gsd:verify-work"
exit 0
```

---

## Shared Patterns (cross-cutting)

### Polish-language convention
**Source:** Wszystkie user-facing strings w repo (REPL prompts, error messages, format_human banners, format_config_header). Examples:
- `output.py:35`: `'## Konfiguracja środowiska'`
- `output.py:80`: `'PORÓWNANIE STRATEGII z/bez RationalAgent'`
- `repl.py:115`: `f"Strategia '{name}' nie istnieje. Dostępne: {available}."`
- `args.py:86-114`: wszystkie `help=...` po polsku

**Apply to:** `sphsim/report/markdown.py` (każda sekcja, każdy header, każdy disclaimer) + `sphsim/report/plots.py` (każdy `set_xlabel`, `set_ylabel`, `set_title`, `legend`) + banner po `write_report` ("Raport zapisany do: ...") w `main.py` i `repl.py`.

### Stdlib + matplotlib only — no other new deps
**Source:** PROJECT.md "Python 3.7+; jedyna nowa zależność: matplotlib".
**Apply to:** Phase 6 wszystkie nowe pliki. Nie używać `numpy` w `plots.py` (RESEARCH §B.5 sugeruje `np.arange` — to JEDYNY exception, bo `numpy` jest transitive dep matplotlib).

### Defensive error handling — never crash CLI for side-effect failures
**Source pattern:** `repl.py:312-315` (`_write_history_silent`):
```python
def _write_history_silent():
    try:
        readline.write_history_file(HISTORY_FILE)
    except OSError:
        pass
```
**Apply to:** `write_report` musi łapać `PermissionError`, `OSError` na `mkdir` i `savefig` — log Polish stderr warning, NIE crash. RESEARCH §C.7 spec'uje to: "log Polish warning na stderr ('Nie udało się utworzyć katalogu raportu: <reason>. Raport pominięty.'), kontynuuj symulację normalnie."

### Mirror Phase 4 D-67 (Strategia B): additive-only metrics
**Source pattern:** Phase 4 nigdy nie tknęło `tests/fixtures/baseline_v1/*.json` — wszystkie nowe klucze (`veto_per_phase`, `n_vetoed_total`, `agent_enabled`) zostały dodane do `SKIP_KEYS` i przeszły niezauważone.
**Apply to:** Phase 6 `abstain_per_phase` — SKIP_KEYS extension only, fixtures untouched.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `sphsim/report/plots.py` | renderer (matplotlib) | file-I/O (PNG) | First matplotlib usage in repo. Pseudokod w RESEARCH §B.5-B.9 jest jedynym ground truth. Planner przekazuje verbatim do executora. |
| `tests/test_report.py::TestSphsimNoReportOptOut` | env-var monkeypatch test | unittest | Żaden istniejący test nie testuje env-var opt-out z `os.environ`. Wzór do utworzenia: `unittest.mock.patch.dict(os.environ, {'SPHSIM_NO_REPORT': '1'})`. |
| `.gitignore` 1-line addition (`reports/`) | config | static | Trywialne; brak analogu nie ma znaczenia. |

---

## Metadata

**Analog search scope:**
- `sphsim/agent/` (Phase 4 sub-package — closest sub-package shape match)
- `sphsim/cli/` (formatter + REPL fake_args precedent)
- `sphsim/core/` (counter aggregation pattern source)
- `sphsim/strategies/` (registry pattern — rejected as not applicable)
- `scripts/` (regression_check.py SKIP_KEYS evolution, verify_phase{1,3,4,5}.sh)
- `tests/test_env.py` (Phase 5 — closest test file shape match)
- `tests/test_agent.py` (Phase 4 — closest counter test match)

**Files scanned (read in this session):**
- `sphsim/agent/__init__.py` (5 LoC)
- `sphsim/agent/rational.py` (57 LoC)
- `sphsim/strategies/__init__.py` (27 LoC)
- `sphsim/cli/main.py` (144 LoC)
- `sphsim/cli/repl.py` (335 LoC)
- `sphsim/cli/output.py` (197 LoC)
- `sphsim/core/device.py` (46 LoC)
- `sphsim/core/simulator.py` (168 LoC)
- `tests/test_env.py` (336 LoC)
- `tests/test_agent.py:1-105` (head only — enough for pattern extraction)
- `scripts/regression_check.py` (206 LoC)
- `scripts/generate_baseline.py` (127 LoC)
- `scripts/verify_phase5.sh` (150 LoC)
- `scripts/verify_phase4.sh:1-60` (head only)
- `sphsim/cli/args.py:79-125` (grep'ed only)
- `.gitignore` (12 LoC)
- `.planning/phases/06-report-plots-generator/06-RESEARCH.md:1-500` (excerpted)

**Pattern extraction date:** 2026-05-28
