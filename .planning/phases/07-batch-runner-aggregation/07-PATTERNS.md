# Phase 7: Batch runner + aggregation — Pattern Map

**Mapped:** 2026-05-28
**Files analyzed (new + modified):** 12 (8 new, 4 modified)
**Analogs found:** 11 / 12 (one new surface — `sphsim/batch/stats.py` mixes scipy + numpy, has no in-repo statistical-aggregation analog)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `sphsim/batch/__init__.py`             | sub-package entry           | re-export (import → public surface)              | `sphsim/agent/__init__.py`              | exact (sub-package shape) |
| `sphsim/batch/runner.py`               | orchestrator / loop driver  | request-response (N× sim.run aggregate)          | `sphsim/cli/main.py::run_compare` + main.py main-loop | exact (role + flow — N×SPHSimulator like compare's 2×SPHSimulator) |
| `sphsim/batch/stats.py`                | statistical core            | transform (list[dict] → dict[AggregateStat])     | (no analog — first stats surface; closest shape = `sphsim/core/model.py` valuation presets — pure transform) | partial |
| `sphsim/report/batch_markdown.py`      | formatter / serializer      | transform (per_seed + aggregate → MD string)     | `sphsim/report/markdown.py::render_report` | exact (role + flow — same renderer pattern) |
| `sphsim/report/plots.py` (MOD)         | renderer (matplotlib)       | file-I/O (PNG side-effect)                       | `sphsim/report/plots.py::plot_kpi_timeseries` (same file) | exact (1:1 mirror — twin Phase 6 plot fn) |
| `sphsim/report/__init__.py` (MOD)      | sub-package entry / dispatcher | side-effect orchestrator                       | `sphsim/report/__init__.py::write_report` (same file) | exact (1:1 mirror — add write_batch_report twin) |
| `sphsim/cli/args.py` (MOD)             | CLI argparse + type converter | parsing / validation                           | `sphsim/cli/args.py::_parse_phi_list` (same file) | exact (Polish errors, ArgumentTypeError) |
| `sphsim/cli/main.py` (MOD)             | CLI entry / early branch    | request-response                                  | `sphsim/cli/main.py::run_compare` early branch (same file) | exact (compare branch is the template for batch branch) |
| `sphsim/cli/output.py` (MOD)           | formatter (stdout summary)  | transform (aggregate → one-liner string)         | `sphsim/cli/output.py::format_compare` (same file) | exact (same role — render aggregate KPI summary) |
| `sphsim/cli/repl.py` (MOD)             | REPL command                | request-response                                  | `sphsim/cli/repl.py::do_compare` (same file) | exact (1:1 mirror — token parsing + fake_args + side-effect call) |
| `tests/test_batch.py`                  | tests (CLI + REPL + parser) | unittest (subprocess + unit)                     | `tests/test_env.py` + `tests/test_agent.py` | exact (multi-class subprocess test pattern) |
| `tests/test_batch_stats.py`            | tests (statistical core)    | unittest (pure unit, no subprocess)              | `tests/test_agent.py::TestWrapWithAgent` | exact (pure unit, known-values + edge cases) |
| `tests/test_batch_report.py`           | tests (renderer + plot)     | unittest (subprocess + unit)                     | `tests/test_report.py` | exact (Phase 6 test file is direct twin) |
| `scripts/verify_phase7.sh`             | shell exit gate             | shell (≥30 check() invocations)                  | `scripts/verify_phase6.sh` | exact (verbatim framework, swap p6_→p7_) |
| `scripts/regression_check.py` (MOD)    | regression compare          | subprocess + diff                                | `SKIP_KEYS` evolution (same file)        | trivial (likely no change — batch has no new top-level JSON keys) |
| `requirements.txt` (NEW, optional)     | dep manifest                | static                                            | (no analog — new file)                   | none (planner decides if Phase 7 owns it) |

---

## 1. Sub-package layout pattern (`sphsim/batch/`)

Reference: `06-PATTERNS.md §1` already established that `sphsim/report/` mirrored `sphsim/agent/`. Phase 7 follows the **same recipe** — new `sphsim/batch/` sub-package mirrors `sphsim/agent/` (1 public entry, 1 impl module) but adds a second impl module (`stats.py`) because aggregation and orchestration are cleanly separable.

### Verbatim copy from `sphsim/agent/__init__.py:1-5`:

```python
"""Rational agent — wrapper veto-ujący COMMIT przy E[zysk] < 0 (Phase 4, AGENT-01..05)."""
from sphsim.agent.rational import wrap_with_agent

__all__ = ['wrap_with_agent']
```

### Phase 7 equivalent (`sphsim/batch/__init__.py`):

```python
"""Phase 7: Batch runner + statystyczna agregacja (BATCH-01..03, PLOT-04)."""
from sphsim.batch.runner import run_batch
from sphsim.batch.stats import aggregate_kpis, AggregateStat, KPIS

__all__ = ['run_batch', 'aggregate_kpis', 'AggregateStat', 'KPIS']
```

**Key conventions to preserve:**
- One-line docstring naming phase + REQ-IDs (mirror `sphsim/agent/__init__.py:1` and `sphsim/report/__init__.py:1`)
- Fully-qualified imports (NOT relative — `from sphsim.batch.X import Y`, not `from .X import Y`)
- Explicit `__all__` listing public surface — pattern from `sphsim/report/__init__.py:32`

---

## 2. New-file analog map

### 2a. `sphsim/batch/runner.py` → analog `sphsim/cli/main.py::run_compare` (lines 17-55) + main-loop body (lines 124-168)

**What to copy literally:**

1. **Multi-run orchestration shape** — `run_compare` runs 2× `SPHSimulator` with identical `common` dict; `run_batch` runs N× with identical config but rotating `seed`. Verbatim pattern from `main.py:30-36`:

```python
# Phase 4 run_compare common-dict pattern
common = dict(
    nU=args.nU, nSUS=args.nSUS, K0=args.K0, K1=K1,
    F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
    phi=args.phi, rho=args.rho, valuation_preset=args.valuation,
    params=params, seed=args.seed,
)
sim_with = SPHSimulator(strategy_fn=wrap_with_agent(raw_strategy_fn, args.expected_P), **common)
res_with = sim_with.run()
```

Phase 7 batch — single `for seed in args.seeds:` loop, **omit `seed=args.seed` from common dict** and override per iteration:

```python
# sphsim/batch/runner.py — Phase 7 shape
common = dict(
    nU=args.nU, nSUS=args.nSUS, K0=args.K0, K1=K1,
    F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
    phi=args.phi, rho=args.rho, valuation_preset=args.valuation,
    params=params,
    # seed NIE w common — nadpisywane per loop iter.
)
strategy_fn = raw_strategy_fn if args.no_agent else wrap_with_agent(raw_strategy_fn, args.expected_P)
per_seed_results = []
for seed in args.seeds:
    sim = SPHSimulator(strategy_fn=strategy_fn, seed=seed, **common)
    res = sim.run()
    per_seed_results.append({k: res[k] for k in KPIS})  # KPI-only slice
aggregate = aggregate_kpis(per_seed_results)
return per_seed_results, aggregate
```

2. **Conditional `wrap_with_agent` pattern** — verbatim from `main.py:145-148`:

```python
# (e) Conditional wrap — tylko dla single-run.
strategy_fn = raw_strategy_fn
if not args.no_agent:
    strategy_fn = wrap_with_agent(strategy_fn, args.expected_P)
```

Phase 7 wraps ONCE before the loop (closure identical across seeds — RESEARCH §A.3 verified deterministic).

3. **Determinism via `random.seed(S)` in SPHSimulator constructor** — `simulator.py:14` (`random.seed(seed)` in `__init__`) is the contract Phase 7 relies on. NO manual reseeding in runner.py — each `SPHSimulator(seed=S)` call resets stdlib `random` globally. RESEARCH §A.3 confirms safe.

4. **KPI-only result projection** — slice from `res` dict to discard `history`, `devices`, `ic_per_phase`, `veto_per_phase`. Pattern from `main.py::run_compare:47`:

```python
'with_agent': {k: v for k, v in res_with.items() if k not in ('history', 'devices')},
```

Phase 7 narrower — only keep 5 KPIs (`KPIS` tuple from `batch/stats.py`):
```python
per_seed_results.append({k: res[k] for k in KPIS})
```

**What differs:**
- `run_compare` returns single dict with `comparison` block; `run_batch` returns 2-tuple `(per_seed_results, aggregate)`.
- `run_compare` runs exactly 2 sims; `run_batch` runs N (1..100).
- No `_with_agent_full` injection needed (no plot consumes per-seed history).

### 2b. `sphsim/batch/stats.py` → analog (no direct in-repo analog)

**Closest shape:** `sphsim/core/model.py` valuation presets — pure stateless transform functions. But statistical aggregation is greenfield surface.

**Patterns to enforce despite no analog:**

1. **Dataclass for structured return** — pattern from `sphsim/core/device.py:1-26` (`Device` is a dataclass with `__post_init__`). Phase 7 `AggregateStat` is similar:

```python
# sphsim/core/device.py:1-26 — pattern reference
from dataclasses import dataclass
@dataclass
class Device:
    id: int
    phase: int
    status: str
    ...
    def __post_init__(self):
        self.veto_phase_stats = {}
```

Phase 7 mirror:
```python
@dataclass
class AggregateStat:
    mean: float
    std: float
    min: float
    max: float
    ci_lower: Optional[float]   # None for N=1
    ci_upper: Optional[float]
    n: int

    def ci_str(self, fmt='{:.2f}') -> str:
        if self.ci_lower is None or self.ci_upper is None:
            return f'n/a (N={self.n})'
        return f'({fmt.format(self.ci_lower)}, {fmt.format(self.ci_upper)})'
```

2. **Module-level KPI tuple** — pattern verbatim from `sphsim/report/markdown.py:27-34`:

```python
_KPI_ROWS = (
    ('avg_val_last100',     '{:.2f}',     'MAX → 100'),
    ('cum_val_total',       '{:.1f}',     'MAX → 100000'),
    ('avg_net_profit',      '{:+.4f}',    '> 0'),
    ('delivery_ratio',      '{:.2%}',     'wysoki'),
    ('avg_providers_l100',  '{:.2f}',     '≈ 100..120'),
)
```

Phase 7 `KPIS` is a simpler 5-tuple (just the key names — fmt strings stay in `markdown.py`):
```python
KPIS = ('avg_val_last100', 'cum_val_total', 'avg_net_profit',
        'delivery_ratio', 'avg_providers_l100')
```

3. **scipy/numpy formula** — RESEARCH §D.6 gives full skeleton. The `t.interval(0.95, df=n-1, loc=mean, scale=sem)` is canonical [CITED scipy docs]. N=1 edge case requires **explicit guard before `values.std(ddof=1)`** to avoid `RuntimeWarning: Degrees of freedom <= 0`:

```python
if n == 1:
    std = 0.0
    ci_lower = None
    ci_upper = None
else:
    std = float(values.std(ddof=1))
    sem = std / np.sqrt(n)
    ci_lower_np, ci_upper_np = st.t.interval(0.95, df=n - 1, loc=mean, scale=sem)
    ci_lower = float(ci_lower_np)
    ci_upper = float(ci_upper_np)
```

4. **Polish docstrings** — every public symbol gets Polish description (PROJECT.md constraint preserved through Phase 1-6).

### 2c. `sphsim/report/batch_markdown.py` → analog `sphsim/report/markdown.py` (entire file, 215 LoC)

**Verbatim copy of skeleton** from `markdown.py:37-65`:

```python
def render_report(args, res, params, K1, *, mode='single') -> str:
    sections = [
        _render_title(args),
        format_config_header(args, args.K0, K1, args.phi, args.rho),
        _render_strategy_params(args, params),
        _render_kpi_table(res, mode=mode),
        _render_decision_table(res, mode=mode),
        _render_plots_section(),
        _render_baseline_comparison(res, mode=mode),
    ]
    if mode == 'compare':
        sections.append(_render_compare_section(res))
    return '\n\n'.join(sections) + '\n'
```

Phase 7 `render_batch_report` follows IDENTICAL composition pattern but with 7 batch-specific sections (RESEARCH §E.9):

```python
def render_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list) -> str:
    sections = [
        _render_title(args, len(seeds_list)),
        format_config_header(args, args.K0, K1, args.phi, args.rho),  # REUSE Phase 6
        _render_strategy_params(args, params, seeds_list),
        _render_per_seed_table(per_seed_results, seeds_list),
        _render_aggregate_table(aggregate),
        _render_boxplot_section(),
        _render_baseline_beating(aggregate),
    ]
    return '\n\n'.join(sections) + '\n'
```

**REUSE imports (single source of truth):**

```python
from sphsim.cli.output import format_config_header        # Sekcja 1 verbatim
from sphsim.report.markdown import BASELINE_PATH, _KPI_ROWS  # Sekcja 5 + Werdykt
```

`BASELINE_PATH` from `markdown.py:21-25` is **the** baseline location — Phase 7 imports, does not duplicate:
```python
BASELINE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / 'tests' / 'fixtures' / 'baseline_v1'
    / '08-naive-zeta-0.75-baseline.json'
)
```

**MD table builder pattern** — verbatim `lines = [...]; return '\n'.join(lines)` from `markdown.py:73-91` (`_render_strategy_params`). Phase 7 every helper (`_render_per_seed_table`, `_render_aggregate_table`, `_render_baseline_beating`) follows this shape — 4 lines of header + `'|'.join` row construction + `'\n'.join(lines)` return.

**Baseline-beating verdict** — copy try/except pattern from `markdown.py:153-163`:
```python
try:
    baseline_raw = json.loads(BASELINE_PATH.read_text(encoding='utf-8'))
    baseline = baseline_raw['metrics']
except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
    return (
        '## Porównanie z baseline `naive --zeta 0.75 --no-agent`\n\n'
        f'*Baseline niedostępny ({type(e).__name__}) — sekcja pominięta.*'
    )
```

Phase 7 `_render_baseline_beating` follows the same shape — graceful fallback when fixture missing.

**Polish strings + Unicode glyphs** — `## Wyniki per seed`, `## Agregat statystyczny`, `## Werdykt: bije baseline?`, `✓ TAK` / `✗ NIE` — consistent with `markdown.py:189-214` (`_render_compare_section`).

### 2d. `sphsim/report/plots.py` MOD → add `plot_batch_aggregate` (analog: same file, `plot_kpi_timeseries` at lines 75-119)

**Add NEW function in existing file** — Phase 6 setup is reused (Agg backend at line 14, font fallback at line 19). No new imports needed beyond `numpy` (already imported line 16).

**Verbatim pattern from `plots.py:97-119` (`plot_kpi_timeseries`):**

```python
fig, ax1 = plt.subplots(figsize=(10, 5), dpi=120)
try:
    # ... plot calls ...
    ax1.set_xlabel('Cykl symulacji')
    ax1.set_ylabel('avg_val (waluacja Konsumentów)', color=color_val)
    fig.suptitle('Przebieg KPI w czasie symulacji (zaznaczone ostatnie 100 cykli)')
    fig.tight_layout()
    fig.savefig(path)
finally:
    plt.close(fig)
```

Phase 7 `plot_batch_aggregate` (full skeleton in RESEARCH §F.12):

```python
def plot_batch_aggregate(per_seed_kpis, path):
    """PLOT-04: 5 subplotów (1×5 grid) z box-plotami dla każdego z 5 KPI."""
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
            if kpi_key == 'delivery_ratio':
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
        fig.suptitle(f'Box-ploty 5 KPI (N={len(per_seed_kpis)} seedów)', fontsize=12)
        fig.tight_layout()
        fig.savefig(path)
    finally:
        plt.close(fig)
```

**MUST-COPY conventions from Phase 6:**
- `try: ... savefig(path) finally: plt.close(fig)` — Pitfall 5 (matplotlib memory leak in batch mode is even more critical than single-run)
- `if not per_seed_kpis: return` — defensive empty-input guard, mirror `plots.py:89-90`
- Polish axis labels — every `set_xlabel`, `set_ylabel`, `set_title`, `suptitle` in Polish
- Hex colors as string literals (`'#90CAF9'`) — same convention as `plots.py:59-61` (`'#2E7D32'`, `'#757575'`, `'#C62828'`)

### 2e. `sphsim/report/__init__.py` MOD → add `write_batch_report` (analog: same file, `write_report` at lines 79-153)

**Add NEW orchestrator function** mirroring `write_report` 1:1. Key features to copy verbatim:

1. **Opt-out env var check** (lines 99-100):
```python
if os.environ.get('SPHSIM_NO_REPORT') == '1':
    return None
```

2. **Outer try/except for exception isolation** (lines 102-153):
```python
try:
    try:
        report_dir = _resolve_report_dir()  # REUSE — works with custom base path
    except OSError as e:
        print(f'[OSTRZEŻENIE] Nie udało się utworzyć katalogu raportu: {e}. '
              f'Raport pominięty.', file=sys.stderr)
        return None
    # ... plot + markdown writes, each wrapped in try/except ...
    return report_dir
except Exception as e:
    print(f'[OSTRZEŻENIE] Raport: {e}', file=sys.stderr)
    return None
```

3. **`_resolve_report_dir` REUSE with custom base** — function already accepts `base: Path = None` parameter (`__init__.py:40-60`). Phase 7 passes `Path('reports') / f'batch_{_timestamp()}'` shape — but cleaner is to extend `_resolve_report_dir` to accept a stem name OR Phase 7 calls `_resolve_report_dir(base=Path('reports'))` and renames AFTER:

**Recommended (cleaner):** Slightly refactor `_resolve_report_dir(base, *, stem='')` to accept prefix; OR write a new helper `_resolve_batch_report_dir()` that wraps the same logic with `batch_` prefix. RESEARCH §A.6 says: "Phase 6 `_resolve_report_dir` (`__init__.py:40-60`) **already handles** retry with `-N` suffix. Phase 7 same helper, only with `base=Path('reports') / f'batch_{ts}'`."

Pragmatic Phase 7 wire-up:
```python
def write_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list):
    if os.environ.get('SPHSIM_NO_REPORT') == '1':
        return None
    try:
        try:
            ts = _timestamp()
            base = Path('reports') / f'batch_{ts}'
            n = 1
            while base.exists():
                n += 1
                base = Path('reports') / f'batch_{ts}-{n}'
            base.mkdir(parents=True, exist_ok=False)
            report_dir = base
        except OSError as e:
            print(f'[OSTRZEŻENIE] Nie udało się utworzyć katalogu raportu batch: {e}. '
                  f'Raport pominięty.', file=sys.stderr)
            return None

        try:
            plot_batch_aggregate(per_seed_results, report_dir / 'batch_aggregate.png')
        except Exception as e:
            print(f'[OSTRZEŻENIE] Błąd generowania batch_aggregate.png: {e}. '
                  f'Kontynuuję.', file=sys.stderr)

        try:
            md = render_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list)
            (report_dir / 'report.md').write_text(md, encoding='utf-8')
        except Exception as e:
            print(f'[OSTRZEŻENIE] Błąd generowania raportu MD: {e}. '
                  f'Raport niekompletny.', file=sys.stderr)
            return None
        return report_dir
    except Exception as e:
        print(f'[OSTRZEŻENIE] Raport batch: {e}', file=sys.stderr)
        return None
```

4. **`__all__` extension** — add to `report/__init__.py:32`:
```python
__all__ = ['write_report', 'render_report', 'write_batch_report']
```

### 2f. `sphsim/cli/args.py` MOD → `_parse_seeds_list` + `--batch`/`--seeds` flags (analog: same file, `_parse_phi_list` at lines 32-49)

**Verbatim pattern copy from `args.py:32-49`:**

```python
def _parse_phi_list(s: str) -> list:
    """Konwertuje string 'p1,p2,p3,p4,p5' na listę 5 floatów ∈ [0,1] (ENV-01, D-17)."""
    try:
        vals = [float(x.strip()) for x in s.split(',')]
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Nieprawidłowy format --phi: '{s}'. Oczekiwano 5 liczb po przecinku, np. 0.1,0.2,0.3,0.4,1.0"
        )
    if len(vals) != 5:
        raise argparse.ArgumentTypeError(
            f"--phi wymaga dokładnie 5 wartości (podano {len(vals)}): '{s}'"
        )
    for i, v in enumerate(vals):
        if not (0.0 <= v <= 1.0):
            raise argparse.ArgumentTypeError(
                f"--phi[{i+1}]={v} poza zakresem [0, 1]. Wszystkie wartości φ muszą być w [0, 1]."
            )
    return vals
```

**Patterns to copy verbatim into `_parse_seeds_list`:**
- `try: ... except ValueError: raise argparse.ArgumentTypeError(...)` outer guard
- Polish error messages with concrete bad value echo'd back (`'{s}'` in f-string)
- Per-element validation loop with `argparse.ArgumentTypeError` raise
- Strip whitespace in `split(',')` comprehension (`x.strip()`)

Phase 7 full converter at RESEARCH §B.3. The grammar has TWO branches (single `N` → range, comma list → dedup), so the converter is ~30 lines (vs. 17 for `_parse_phi_list`). Behavioral table at RESEARCH §B.3 lists 10 test cases — each becomes a `TestSeedsParser` method.

**Flag wiring** (post `_parse_seeds_list` def, after `--rho` line `args.py:104-106`):

```python
p.add_argument('--batch', action='store_true',
               help='Tryb batch — uruchom strategię N razy na różnych seedach (wymaga --seeds)')
p.add_argument('--seeds', type=_parse_seeds_list, default=None, metavar='N|lista',
               help='Lista seedów: N (1..N) lub jawna (1,5,42). Działa tylko z --batch.')
```

**Post-parse mutex** — mirror `args.py:120-124`:
```python
# Existing:
if args.compare_agent and args.no_agent:
    p.error("Flagi --compare-agent i --no-agent są wzajemnie wykluczające.")
if args.compare_agent and args.interactive:
    p.error("Flaga --compare-agent nie działa w trybie --interactive.")
# Phase 7 additions:
if args.batch and args.compare_agent:
    p.error("Flagi --batch i --compare-agent są wzajemnie wykluczające.")
if args.batch and args.interactive:
    p.error("Flaga --batch nie działa w trybie --interactive (użyj komendy `batch` w REPL).")
if args.batch and args.seeds is None:
    p.error("Flaga --batch wymaga --seeds N lub --seeds lista (np. 1,5,42).")
if args.seeds is not None and not args.batch:
    p.error("Flaga --seeds wymaga --batch.")
```

### 2g. `sphsim/cli/main.py` MOD → early batch branch (analog: same file, `compare_agent` branch at lines 92-99 and 136-143)

**Two insertion points** — one in built-in branch (after `K1` resolution at line 125), one in custom branch (after `K1` resolution at line 86). Both branches need the same `if args.batch:` early-return.

**Verbatim shape from `main.py:136-143` (compare branch):**

```python
# (d) Compare branch — early return, PRZED conditional wrap (step e).
if args.compare_agent:
    res = run_compare(args, raw_strategy_fn, args.strategy, params, K1)
    report_dir = write_report(args, res, params, K1, mode='compare')
    if report_dir:
        print(f'Raport porównawczy zapisany do: {report_dir}/report.md', file=sys.stderr)
    print(format_json(args, res, params, K1) if args.json else format_human(args, res, K1, args.verbose))
    return
```

Phase 7 batch branch (mirror identical structure):

```python
# (d') Batch branch — early return, PRZED compare-agent i single-run (Phase 7 BATCH-01).
if args.batch:
    from sphsim.batch import run_batch
    from sphsim.report import write_batch_report
    per_seed_results, aggregate = run_batch(args, raw_strategy_fn, params, K1)
    report_dir = write_batch_report(args, per_seed_results, aggregate, params, K1, args.seeds)
    if report_dir:
        print(f'Raport batchowy zapisany do: {report_dir}/report.md', file=sys.stderr)
    print(format_batch_summary(args, aggregate, K1))   # NOWY helper w output.py
    return
```

**Positioning constraint** — batch branch goes BEFORE `compare_agent` branch in BOTH paths (built-in + custom). Already enforced by mutex (post-parse error if both flags set), but ordering avoids any ambiguity.

### 2h. `sphsim/cli/output.py` MOD → `format_batch_summary` (analog: same file, `format_compare` at lines 56-end)

`format_compare` (Plan 03, D-62) renders a 5×3 ASCII delta KPI table. Phase 7 `format_batch_summary` is a **shorter** one-liner — mean ± std for each KPI plus baseline verdict — printed to stdout. RESEARCH §C.4 specifies the contract (one-liner summary; full table is in MD).

**Recommended Phase 7 shape (shorter than format_compare):**

```python
def format_batch_summary(args, aggregate, K1) -> str:
    """Phase 7 BATCH-01: krótkie podsumowanie agregatu na stdout (single-line per KPI)."""
    from sphsim.batch.stats import KPIS
    lines = [
        f"=== BATCH SUMMARY — strategia '{args.strategy}' × N={aggregate['avg_val_last100'].n} seedów ===",
    ]
    for kpi in KPIS:
        stat = aggregate[kpi]
        fmt = '{:.2%}' if kpi == 'delivery_ratio' else '{:.2f}'
        if stat.ci_lower is None:
            lines.append(f"  {kpi:<22} mean={fmt.format(stat.mean):>10}  std=n/a (N=1)")
        else:
            ci = f'({fmt.format(stat.ci_lower)}, {fmt.format(stat.ci_upper)})'
            lines.append(
                f"  {kpi:<22} mean={fmt.format(stat.mean):>10}  "
                f"std={fmt.format(stat.std):>10}  95% CI={ci}"
            )
    # Baseline verdict for avg_val_last100
    val_stat = aggregate['avg_val_last100']
    verdict = '?'
    if val_stat.ci_lower is not None and val_stat.ci_lower > 92.0:
        verdict = "✓ BIJE baseline (CI_lower > 92.0)"
    elif val_stat.ci_lower is not None:
        verdict = "✗ NIE bije baseline (CI_lower ≤ 92.0)"
    elif val_stat.mean > 92.0:
        verdict = "✓ TAK (N=1, single-point > 92.0)"
    else:
        verdict = "✗ NIE (N=1, single-point ≤ 92.0)"
    lines.append(f"  Werdykt: {verdict}")
    return '\n'.join(lines)
```

**Patterns copied:**
- Polish strings (`'mean'`, `'std'` are EN but the verdict text and headers are PL)
- Banner-style `=== ... ===` from `output.py:80` (PORÓWNANIE STRATEGII banner)
- `lines = [...]; return '\n'.join(lines)` from `output.py:38-53` (`format_config_header`)
- Per-KPI loop using same `KPIS` tuple as `markdown.py:_KPI_ROWS`

### 2i. `sphsim/cli/repl.py` MOD → `do_batch` (analog: same file, `do_compare` at lines 236-312)

**Phase 7 `do_batch` is a 1:1 mirror of `do_compare` PLUS seed-list parsing.** Verbatim copy of the 5 phases of do_compare:

**Phase 1 — Token parsing + early validation** (`repl.py:237-243`):
```python
def do_compare(self, arg):
    """Porównaj strategię z i bez RationalAgent: compare <nazwa> [param=wartość ...]"""
    tokens = arg.split()
    if not tokens:
        print("Użycie: compare <nazwa> [param=wartość ...]. Wpisz 'strategies' żeby zobaczyć dostępne.")
        return
```

Phase 7 do_batch (RESEARCH §C.5 has full skeleton) — same shape, but token loop separates `--seeds VALUE`:
```python
def do_batch(self, arg):
    """Uruchom strategię na wielu seedach: batch <nazwa> --seeds N|lista [param=wartość ...]"""
    tokens = arg.split()
    if not tokens:
        print("Użycie: batch <nazwa> --seeds N|lista [param=wartość ...]. "
              "Np.: batch naive --seeds 10  |  batch naive --seeds 1,5,42 zeta=0.75")
        return
    # Separate --seeds VALUE from name + k=v tokens
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
        from sphsim.cli.args import _parse_seeds_list
        seeds_list = _parse_seeds_list(seeds_value)  # REUSE — same Polish errors as CLI
    except argparse.ArgumentTypeError as e:
        print(str(e))
        return
    if not other_tokens:
        print("Komenda `batch` wymaga nazwy strategii. Wpisz 'strategies' żeby zobaczyć dostępne.")
        return
    name, *kv_tokens = other_tokens
```

**Phase 2 — Strategy validation + meta load** — verbatim from `repl.py:246-262`:
```python
if name not in STRATEGIES:
    available = ', '.join(STRATEGIES.keys())
    print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
    return
ns = 'sphsim.strategies' if name in BUILTIN_STRATEGIES else 'sphsim.custom'
mod = importlib.import_module(f'{ns}.{name}')
meta = mod.STRATEGY_META
try:
    params = parse_params_from_meta(kv_tokens, meta, name)
except LoaderError as e:
    print(e.args[0])
    return
```

**Phase 3 — `fake_args` construction** — verbatim shape from `repl.py:302-307`:
```python
# Phase 6 fake_args (compare):
fake_args = argparse.Namespace(
    strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
    kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
    phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window',
    seed=42, json=False, compare_agent=True,
)
```

Phase 7 fake_args MUST add `batch`, `seeds`, `expected_P`, and Phase 7 specific fields. **Full fake_args audit at §4 below.**

**Phase 4 — Run + render** — mirror `repl.py:308-312`:
```python
from sphsim.batch import run_batch
from sphsim.report import write_batch_report
raw_strategy_fn = STRATEGIES[name]
per_seed_results, aggregate = run_batch(fake_args, raw_strategy_fn, params, DEFAULT_K1)
report_dir = write_batch_report(fake_args, per_seed_results, aggregate, params,
                                 DEFAULT_K1, seeds_list)
if report_dir:
    print(f'Raport batchowy zapisany do: {report_dir}/report.md', file=sys.stderr)
print(format_batch_summary(fake_args, aggregate, DEFAULT_K1))
```

**Phase 5 — `do_help` extension** — add 1 line at `repl.py:62-71`:
```python
print("  batch <nazwa> --seeds N|lista [k=v ...] — Uruchom strategię na wielu seedach (agregat statystyczny).")
```

### 2j. `tests/test_batch_stats.py` → analog `tests/test_agent.py:55-105` (`TestWrapWithAgent` class)

**Pure-unit pattern, no subprocess.** Phase 4 `test_agent.py` opens with stubs + Device fixtures + asserts. Phase 7 stats tests open with hand-crafted KPI dicts + asserts on `AggregateStat` fields.

**Verbatim header pattern from `test_agent.py:1-37`:**

```python
"""Unit i integration tests dla sphsim.batch.stats (Phase 7, BATCH-02)."""
import unittest
import os, sys
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sphsim.batch.stats import aggregate_kpis, AggregateStat, KPIS
```

**Per-test assertion pattern from `test_agent.py:107-113`** (Phase 4 used self.assertAlmostEqual for floating-point):
```python
self.assertEqual(dev.veto_phase_stats, {1: 1},
                 msg=f"veto_phase_stats == {{1: 1}}, got {dev.veto_phase_stats!r}")
```

Phase 7 stats — MUST use `assertAlmostEqual(places=4)` for float comparisons (Pitfall 3 — BLAS variance):
```python
self.assertAlmostEqual(stat.mean, 92.0, places=4,
                       msg=f"mean expected 92.0, got {stat.mean}")
self.assertAlmostEqual(stat.ci_lower, 90.21, places=2,
                       msg=f"CI lower expected ~90.21, got {stat.ci_lower}")
```

**Test classes** (4-5 classes, ~12-15 tests total — per RESEARCH "Wave 0 Gaps"):
- `TestAggregateKpis` — known-value mean/std (3 tests)
- `TestCIComputation` — synthetic Gaussian samples, CI coverage (2 tests)
- `TestN1Degenerate` — single-seed graceful (2 tests)
- `TestEmptyInput` — N=0 raises ValueError (1 test)
- `TestDeterminism` — same input → byte-identical output (1 test)

### 2k. `tests/test_batch.py` → analog `tests/test_env.py:1-336` (multi-class subprocess pattern)

**Verbatim header from `test_env.py:1-30`:**

```python
"""
Unit i integration tests dla Phase 7 (Batch runner + aggregation).
Pokrywa BATCH-01 (--seeds parser + CLI/REPL wire), BATCH-02 (aggregation), PLOT-04 (boxplot).
Stdlib only: unittest + subprocess + json + os + sys.
"""
import json, os, subprocess, sys, unittest
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

PROJECT_ROOT = Path(_PROJECT_ROOT)

def _run_sph(*args, **kwargs):
    env = {**os.environ, 'SPHSIM_NO_REPORT': '1'}  # opt-out per Phase 6 pattern
    return subprocess.run(
        [sys.executable, 'sph_sim.py'] + list(args),
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        **kwargs,
    )
```

**Test classes** (RESEARCH "Wave 0 Gaps"):
- `TestSeedsParser` — direct `_parse_seeds_list` unit (~7 tests)
- `TestArgsMutex` — subprocess argparse error code 2 + Polish error message match (~3 tests)
- `TestReplBatch` — printf `batch naive --seeds 5\nexit\n` | sph_sim.py --interactive (~2 tests)
- `TestDeterminism` — same seeds twice → byte-identical (~1 test)
- `TestCliReplParity` — CLI `--batch --seeds 3` vs REPL `batch naive --seeds 3` (~1 test)

**Argparse error pattern from `test_env.py:62-70`** (exit code 2 + Polish message match):
```python
def test_phi_wrong_length_exit_2(self):
    r = _run_sph('--strategy', 'naive', '--zeta', '0.5',
                 '--phi', '0.1,0.2,0.3', '--no-agent', '--seed', '42', '--json')
    self.assertEqual(r.returncode, 2,
                     msg=f'Oczekiwano exit 2 dla błędnej długości, got {r.returncode}. stderr={r.stderr[:300]}')
    combined = r.stderr + r.stdout
    self.assertIn('dokładnie 5', combined,
                  msg=f'Brak "dokładnie 5" w komunikacie błędu: {combined[:400]}')
```

Phase 7 mirror for `--seeds 0`:
```python
def test_seeds_zero_exit_2(self):
    r = _run_sph('--strategy', 'naive', '--zeta', '0.5',
                 '--batch', '--seeds', '0', '--no-agent', '--seed', '42', '--json')
    self.assertEqual(r.returncode, 2,
                     msg=f'Oczekiwano exit 2 dla --seeds 0, got {r.returncode}. stderr={r.stderr[:300]}')
    combined = r.stderr + r.stdout
    self.assertIn('dodatnie', combined,
                  msg=f'Brak "dodatnie" w komunikacie błędu: {combined[:400]}')
```

### 2l. `tests/test_batch_report.py` → analog `tests/test_report.py` (entire file)

**Verbatim header from `test_report.py:1-78`:**

```python
"""Unit i integration tests dla Phase 7 — batch markdown + plot (BATCH-03, PLOT-04)."""
import argparse, json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
```

**`_make_args` helper pattern from `test_report.py:31-42`:**

```python
def _make_args(**overrides):
    """Builds argparse.Namespace with all fields required by render_batch_report."""
    base = dict(
        nU=250, nSUS=20, T=1000, kappa=0.25, alpha=1,
        K0=100.0, K1=120.0,
        phi=[0.1, 0.2, 0.3, 0.4, 1.0],
        rho=[0.5, 0.5, 0.7, 1.5, 3.0],
        seed=42, strategy='naive', no_agent=False, compare_agent=False,
        valuation='window',
        batch=True, seeds=[1, 2, 3], expected_P=100.0,
        json=False, verbose=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)
```

**`_make_single_res` mirror — `_make_per_seed_results`**:
```python
def _make_per_seed_results(n=3):
    """Builds list of N per-seed KPI dicts (mirror sim.run() output filtered to 5 KPIs)."""
    return [
        {'avg_val_last100': 92.0 + i*0.5, 'cum_val_total': 92300.0 + i*100,
         'avg_net_profit': 140.0 + i*0.5, 'delivery_ratio': 0.79 + i*0.01,
         'avg_providers_l100': 105.0 + i*0.1}
        for i in range(n)
    ]
```

**Tempdir + chdir pattern from `test_report.py:89-100`** (REUSE for batch report tests — same pattern, batch_<ts>/ same logic):
```python
def setUp(self):
    self._orig_cwd = os.getcwd()
    self._tmpdir = tempfile.mkdtemp(prefix='p7_test_batch_')
    os.chdir(self._tmpdir)
    self._orig_no_report = os.environ.pop('SPHSIM_NO_REPORT', None)

def tearDown(self):
    os.chdir(self._orig_cwd)
    shutil.rmtree(self._tmpdir, ignore_errors=True)
    if self._orig_no_report is not None:
        os.environ['SPHSIM_NO_REPORT'] = self._orig_no_report
```

### 2m. `scripts/verify_phase7.sh` → analog `scripts/verify_phase6.sh` (212 LoC, **39 check() invocations**)

**Verbatim copy of header (lines 1-57)** — only swap `p6_` → `p7_` and "Phase 6" → "Phase 7":

```bash
#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  verify_phase7.sh — phase exit gate dla Phase 7 (batch runner + aggregation)
#  [Plan 07-XX — Wave N skeleton (Plan 07-YY owns SC check() bodies)]
#
#  Phase 7 covers BATCH-01..03 + PLOT-04 (multi-seed orchestrator + scipy CI + boxplot).
#  Phase 7 exit gate runs all SC checks below; partial pass blocks merge.
#
#  Phase 7 Success Criteria:
#    SC #1: /batch <strategia> --seeds 10 i --batch --seeds 1,5,42,100 oba działają
#    SC #2: Raport MD ma tabelę per-seed (N wierszy × 6 kolumn) + agregat (5 KPI × 7 kolumn z CI)
#    SC #3: batch_aggregate.png istnieje, non-zero, PNG signature, linked w raporcie
#    SC #4: Batch działa z RationalAgent (default) i --no-agent
#    SC #5: Werdykt baseline-beating w raporcie (lower 95% CI > 92.0 dla avg_val_last100)
#
#  Re-runnable po każdej zmianie w sphsim/ jako pre-flight przed merge'em.
#  Stdlib + POSIX coreutils only — runtime deps: scipy + numpy + matplotlib (Phase 7).
#
#  Exit code: 0 gdy wszystkie checks PASS, 1 gdy jakikolwiek FAIL.
# ─────────────────────────────────────────────────────────────────────
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

trap 'rm -f /tmp/p7_*' EXIT

PASS=0
FAIL=0

check() {
    local desc="$1"
    local cmd="$2"
    if eval "$cmd" > /tmp/p7_check.log 2>&1; then
        echo "[PASS] $desc"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $desc"
        echo "       cmd: $cmd"
        echo "       log:"
        sed 's/^/         /' /tmp/p7_check.log | head -20
        FAIL=$((FAIL + 1))
    fi
}
```

**Section structure from `verify_phase6.sh`** — Phase 7 mirrors verbatim (10 sections, **≥30 check() invocations**, targeting ~35-40 like Phase 6's 39):

| Section | Phase 6 (verbatim shape) | Phase 7 equivalent |
|---------|--------------------------|--------------------|
| 0. Pre-flight cleanup | `rm -rf ./reports/` | `rm -rf ./reports/` (same) |
| 1. Regression backwards compat | `regression_check.py` PASS=8/8 | unchanged (if no SKIP_KEYS change) OR add abstain_per_phase already in Phase 6 list |
| 2. Full test suite | `unittest discover tests` + per-file checks | add `test_batch`, `test_batch_stats`, `test_batch_report` checks |
| 2a. Pre-flight artifact bundle | run `sph_sim.py --strategy naive ...` to produce reports/<ts>/ | run `sph_sim.py --batch --seeds 5 ...` to produce reports/batch_<ts>/ |
| 3. SC #1 — file presence | 3 files in reports/<ts>/ | 2 files in reports/batch_<ts>/ (report.md + batch_aggregate.png) |
| 4. SC #2 — MD sections | 6 H2 sections + 5 KPI rows | 6 H2 sections + N per-seed rows + 5 aggregate rows |
| 5. SC #3 — PNG validation | PNG signature + size | PNG signature + size for batch_aggregate.png |
| 6. SC #4 — MD image links | `![Rozkład...](decision_distribution.png)` | `![Box-ploty 5 KPI...](batch_aggregate.png)` |
| 7. SC #5 — compare delta table | `## Porównanie z RationalAgent` section | `## Werdykt: bije baseline` section + `--no-agent` parallel run |
| 8. SC #6 — JSON stdout cleanliness | `--json` pure JSON | (skip — RESEARCH §"Open Questions" defers `--json + --batch`) |
| 9. REPL Pitfall checks | `printf 'run naive ...\nexit\n' | --interactive` | `printf 'batch naive --seeds 5\nexit\n' | --interactive` |
| 10. Opt-out | `SPHSIM_NO_REPORT=1 ... && [ ! -d reports ]` | same with `--batch` |

**Phase 6 check count breakdown (from `grep -c '^check '`):** **39 check() invocations**. Phase 7 must hit **≥30** (RESEARCH spec); targeting ~35-40 to match Phase 6's coverage.

**Token swaps to apply globally** (sed-friendly):
- `p6_` → `p7_`
- `Phase 6` → `Phase 7`
- `Plan 06-` → `Plan 07-`
- `Report + plots generator` → `Batch runner + aggregation`
- `REPORT-01..03 + PLOT-01..03` → `BATCH-01..03 + PLOT-04`
- `decision_distribution.png` → `batch_aggregate.png` (where applicable)
- `reports/<ts>/` → `reports/batch_<ts>/`

**NEW SC-specific checks (Phase 7-only — no Phase 6 analog):**

```bash
# SC #1: seed-list grammar
check "SC #1 (seeds N): --seeds 5 expands to [1,2,3,4,5]" \
    "$PY -c \"from sphsim.cli.args import _parse_seeds_list; assert _parse_seeds_list('5') == [1,2,3,4,5]\""
check "SC #1 (seeds list): --seeds 1,5,42 parses to [1,5,42]" \
    "$PY -c \"from sphsim.cli.args import _parse_seeds_list; assert _parse_seeds_list('1,5,42') == [1,5,42]\""
check "SC #1 (seeds reject 0): --seeds 0 raises ArgumentTypeError" \
    "$PY -c \"from sphsim.cli.args import _parse_seeds_list; import argparse
try: _parse_seeds_list('0'); raise SystemExit(1)
except argparse.ArgumentTypeError: pass\""

# SC #2: per-seed table N rows
check "SC #2 (per-seed table): N rows in MD per-seed table for --seeds 5" \
    "test -n \"\$LATEST_B\" && [ \"\$(grep -cE '^\\| [0-9]+ ' \"\${LATEST_B}report.md\")\" -ge 5 ]"
check "SC #2 (aggregate table): 5 KPI rows in agregat statystyczny" \
    "test -n \"\$LATEST_B\" && [ \"\$(grep -cE '^\\| (avg_val_last100|cum_val_total|avg_net_profit|delivery_ratio|avg_providers_l100)' \"\${LATEST_B}report.md\")\" -ge 5 ]"

# SC #3: batch_aggregate.png
check "SC #3 (PLOT-04): batch_aggregate.png ma PNG signature" \
    "test -n \"\$LATEST_B\" && $PY -c \"import sys; data=open('\${LATEST_B}batch_aggregate.png','rb').read(8); sys.exit(0 if data == b'\\x89PNG\\r\\n\\x1a\\n' else 1)\""
check "SC #3 (PLOT-04 size): batch_aggregate.png > 10 KB (5 subplots × matplotlib render)" \
    "test -n \"\$LATEST_B\" && [ \"\$(wc -c < \"\${LATEST_B}batch_aggregate.png\" | tr -d ' ')\" -ge 10000 ]"
check "SC #3 (PLOT-03-mirror): MD link ![Box-ploty 5 KPI...](batch_aggregate.png) obecny" \
    "test -n \"\$LATEST_B\" && grep -F '](batch_aggregate.png)' \"\${LATEST_B}report.md\" > /dev/null"

# SC #4: --no-agent batch parallel
check "SC #4 (--no-agent batch): batch produces report.md + PNG dla --no-agent też" \
    "rm -rf ./reports/; SPHSIM_NO_REPORT='' $PY sph_sim.py --strategy naive --zeta 0.5 --batch --seeds 3 --no-agent --seed 42 > /tmp/p7_noagent.log 2>&1 && ls -d ./reports/batch_*/ | head -1 | xargs -I{} test -s {}report.md"

# SC #5: baseline-beating verdict
check "SC #5 (werdykt): '## Werdykt: bije baseline' obecny w raporcie" \
    "test -n \"\$LATEST_B\" && grep -F '## Werdykt: bije baseline' \"\${LATEST_B}report.md\" > /dev/null"
check "SC #5 (verdict line): linia '**bije baseline:**' obecna" \
    "test -n \"\$LATEST_B\" && grep -E '\\*\\*(TAK|NIE|✓|✗)' \"\${LATEST_B}report.md\" > /dev/null"

# CLI/REPL parity
check "REPL Pitfall: 'batch naive --seeds 3' w REPL nie crashe + tworzy raport" \
    "rm -rf ./reports/; printf 'batch naive --seeds 3\\nexit\\n' | SPHSIM_NO_REPORT='' $PY sph_sim.py --interactive 2>&1 | grep -F 'Raport batchowy zapisany do:' > /dev/null"
check "REPL Pitfall: 'batch naive --seeds 0' w REPL nie crashe, polski error" \
    "printf 'batch naive --seeds 0\\nexit\\n' | $PY sph_sim.py --interactive 2>&1 | grep -F 'dodatnie' > /dev/null"

# Mutex
check "Mutex: --batch --compare-agent → exit 2 + Polish error" \
    "rm -rf ./reports/; $PY sph_sim.py --strategy naive --zeta 0.5 --batch --seeds 3 --compare-agent --seed 42 2>&1; [ \$? -eq 2 ]"
check "Mutex: --batch bez --seeds → exit 2 + Polish error" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --batch --seed 42 2>&1; [ \$? -eq 2 ]"
check "Mutex: --seeds bez --batch → exit 2 + Polish error" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --seeds 5 --seed 42 2>&1; [ \$? -eq 2 ]"
```

**Final summary block — verbatim from `verify_phase6.sh:202-211`:**

```bash
echo ""
echo "════════════════════════════════════════"
echo "  Phase 7 verification: PASS=$PASS / FAIL=$FAIL"
echo "════════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
    echo "✗ Phase 7 NIE jest gotowe — popraw FAIL'e powyżej."
    exit 1
fi
echo "✓ Phase 7 ready for /gsd:verify-work"
exit 0
```

---

## 3. Multi-run orchestration pattern (1:1 mirror Phase 4 `run_compare`)

`run_compare` in `sphsim/cli/main.py:17-55` runs 2× SPHSimulator with shared `common` dict. Phase 7 `run_batch` runs N× — same shape, different cardinality.

### 3a. Common dict construction (verbatim from `main.py:30-36`)

```python
common = dict(
    nU=args.nU, nSUS=args.nSUS, K0=args.K0, K1=K1,
    F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
    phi=args.phi, rho=args.rho, valuation_preset=args.valuation,
    params=params, seed=args.seed,  # ← Phase 4 includes seed here
)
```

Phase 7 difference — **exclude `seed` from common** (overridden per loop):
```python
common = dict(
    nU=args.nU, nSUS=args.nSUS, K0=args.K0, K1=K1,
    F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
    phi=args.phi, rho=args.rho, valuation_preset=args.valuation,
    params=params,
)
# seed NIE w common — przekazujemy per iteration
```

### 3b. Loop body (mirrors `main.py:37-42` 2-line pattern, N-times)

```python
# Phase 4 — 2× call pattern
sim_with = SPHSimulator(strategy_fn=wrap_with_agent(raw_strategy_fn, args.expected_P), **common)
res_with = sim_with.run()
sim_without = SPHSimulator(strategy_fn=raw_strategy_fn, **common)
res_without = sim_without.run()
```

Phase 7 loop:
```python
strategy_fn = raw_strategy_fn if args.no_agent else wrap_with_agent(raw_strategy_fn, args.expected_P)
per_seed_results = []
for seed in args.seeds:
    sim = SPHSimulator(strategy_fn=strategy_fn, seed=seed, **common)
    res = sim.run()
    per_seed_results.append({k: res[k] for k in KPIS})
```

### 3c. Determinism contract (RESEARCH §A.3 verified)

**`SPHSimulator.__init__` line 14:** `random.seed(seed)`. This is unconditional — every constructor resets stdlib `random`. Phase 7 invariant:

> Same `args.seeds = [1, 2, 3]` twice → byte-identical `per_seed_results` list.

This is testable (RESEARCH §"Validation Architecture" cites `TestDeterminism.test_byte_identical`). **No additional reseeding required** — re-seeding inside loop is unnecessary because `SPHSimulator.__init__(seed=S)` does it.

---

## 4. `fake_args` audit for REPL `do_batch` (Pitfall 2 prophylaxis)

Phase 6's PATTERNS.md §4 established the convention: every `fake_args` block must contain ALL fields used by downstream consumers (`render_report`, `format_config_header`, `write_report`). Phase 7 extends with batch-specific fields.

### Fields needed by Phase 7 consumers:

| Field | Source consumer | Phase 6 fake_args has it? | Phase 7 add? |
|-------|------------------|---------------------------|--------------|
| `strategy` | `format_config_header`, `_render_title`, `format_batch_summary` | ✓ | reuse |
| `nU` | `format_config_header`, `SPHSimulator(**common)` | ✓ | reuse |
| `nSUS` | `SPHSimulator` | ✓ | reuse |
| `T` | `format_config_header`, `SPHSimulator` | ✓ | reuse |
| `kappa` | `format_config_header`, `SPHSimulator` | ✓ | reuse |
| `alpha` | `format_config_header`, `SPHSimulator` | ✓ | reuse |
| `K0` | `format_config_header`, `SPHSimulator` | ✓ | reuse |
| `phi` | `format_config_header`, `SPHSimulator` | ✓ | reuse |
| `rho` | `format_config_header`, `SPHSimulator` | ✓ | reuse |
| `seed` | `format_config_header` (placeholder), `SPHSimulator` (overridden) | ✓ | reuse (placeholder 42, batch overrides per loop) |
| `valuation` | `format_config_header`, `SPHSimulator` | ✓ | reuse |
| `no_agent` | `run_batch` (agent wrap decision), `_render_strategy_params` | ✓ (always False in REPL) | reuse |
| `compare_agent` | `_render_strategy_params` defensive getattr | ✓ (always False) | reuse — set False (mutex w/ batch) |
| `verbose` | `format_human` (not used by batch path, but defensive) | ✓ | reuse |
| `json` | `format_json` (not used by batch path, but defensive) | ✓ | reuse |
| `batch` | (defensive consistency — not consumed by batch_markdown, but markdown sees `args.batch`) | ✗ | **Phase 7 ADD** = `True` |
| `seeds` | `_render_strategy_params` (lists N seedów) | ✗ | **Phase 7 ADD** = `seeds_list` |
| `expected_P` | `wrap_with_agent(strategy_fn, args.expected_P)` in `run_batch` | ✗ | **Phase 7 ADD** = `params.get('expected_P', DEFAULT_K0)` |

### Phase 7 `do_batch` fake_args (extending Phase 6 compare's fake_args verbatim):

```python
fake_args = argparse.Namespace(
    strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
    kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
    phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window',
    seed=42, json=False, compare_agent=False,
    # Phase 7 additions:
    batch=True,
    seeds=seeds_list,
    expected_P=params.get('expected_P', DEFAULT_K0),
)
```

**Critical Phase 7 Pitfall** (RESEARCH §H Pitfall 7): `expected_P` MUST come from `params.get('expected_P', DEFAULT_K0)`, NOT a hardcoded `100.0`. This is the same fix that Phase 4 `do_compare` got — and Phase 7 must NOT regress.

**Verification check for `verify_phase7.sh`:**
```bash
check "REPL Pitfall 7: 'batch incentive --seeds 3 expected_P=200' propagates expected_P" \
    "rm -rf ./reports/; printf 'batch incentive --seeds 3 expected_P=200\\nexit\\n' | SPHSIM_NO_REPORT='' $PY sph_sim.py --interactive 2>&1 > /dev/null; ls -d ./reports/batch_*/ | head -1 | xargs -I{} grep -F 'expected_P | 200' {}report.md"
```

---

## 5. JSON output extension pattern

### Phase 4 + Phase 5 + Phase 6 precedent:

Phase 4 added `agent_enabled` + `veto_per_phase` + `n_vetoed_total`. Phase 5 added `K0`, `phi`, `rho`, `seed`, `valuation` to env block. Phase 6 added `abstain_per_phase` to metrics. All via auto-include from `**{k: v for k, v in res.items() if k not in ('history', 'devices') and not k.startswith('_')}` (`output.py:23-25`).

### Phase 7 — RESEARCH "Open Questions" #1: DEFER `--json + --batch`

RESEARCH explicitly recommends DEFERRING JSON for batch output:
> "v1 — `--batch` zawsze human-readable na stdout (one-liner summary) + raport MD. Jeśli user chce JSON, czyta `report.md` lub plany v2."

**Consequence:** `format_json` is **NOT touched** by Phase 7. `format_batch_summary` writes human-readable text to stdout. No `SKIP_KEYS` extension needed.

If discuss-phase OVERRIDES this recommendation:
- Add `format_batch_json(args, aggregate, per_seed_results, K1)` returning `json.dumps({'batch': {'aggregate': {...}, 'per_seed': [...]}})`.
- Extend `SKIP_KEYS` with `'batch_aggregate'` / similar if any batch key leaks into single-run JSON path.

---

## 6. `SKIP_KEYS` evolution pattern (likely NO change in Phase 7)

`scripts/regression_check.py:51-55` currently:
```python
SKIP_KEYS = (
    'veto_per_phase', 'n_vetoed_total', 'agent_enabled',  # Phase 4 D-67 Strategia B
    'K0', 'phi', 'rho', 'seed', 'valuation',              # Phase 5 ENV-03
    'abstain_per_phase',                                  # Phase 6 PLOT-01
)
```

**Phase 7 analysis:** `--batch` is a new mode that doesn't run during regression check (regression runs single-run JSON only, per `regression_check.py:108`: `full_args = [sys.executable, str(MONOLITH), *args, '--no-agent', '--seed', '42', '--json']` — no `--batch`). Batch keys never appear in regression JSON.

**Conclusion:** **No SKIP_KEYS change required.** Phase 7 stays additive at the `sphsim/batch/` package level; regression is untouched.

If planner decides to add a `report_path_batch` top-level key to JSON output (not recommended — see §5), THEN extend:
```python
SKIP_KEYS = (
    ...,
    # Phase 7 BATCH (only if JSON output adopts):
    # 'batch_aggregate', 'batch_per_seed',
)
```

---

## 7. Shared Patterns (cross-cutting)

### Polish-language convention (MANDATORY for all new files)
**Source:** Every user-facing string in repo. Examples:
- `output.py:39-51`: `'## Konfiguracja środowiska'`, `'κ (kappa)'`, `'α (alpha)'`
- `args.py:37-48`: every `argparse.ArgumentTypeError` message
- `repl.py:115`: `f"Strategia '{name}' nie istnieje. Dostępne: {available}."`
- `markdown.py:182-185`: baseline disclaimer

**Apply to Phase 7 ALL new files:** Polish docstrings, Polish argparse help, Polish error messages, Polish markdown section headers, Polish matplotlib axis labels, Polish stdout banners.

### Sub-package layout (`__init__.py` re-export idiom)
**Source pattern:** `sphsim/agent/__init__.py:1-5` (5 lines: docstring + import + `__all__`).
**Apply to:** `sphsim/batch/__init__.py` (mirror exactly).

### Defensive error handling — never crash CLI for side-effect failures
**Source pattern:** `sphsim/report/__init__.py:79-153` (write_report's nested try/except).
**Apply to:** `sphsim/report/__init__.py::write_batch_report` — same outer try + inner per-resource try (mkdir, plot, MD render).

### Reuse existing helpers — DO NOT duplicate
**Source pattern:** `sphsim/report/markdown.py:15` (`from sphsim.cli.output import format_config_header`).
**Apply to:** `sphsim/report/batch_markdown.py` MUST import (NOT re-implement):
- `format_config_header` from `sphsim.cli.output`
- `BASELINE_PATH`, `_KPI_ROWS` from `sphsim.report.markdown`
- `_resolve_report_dir`, `_timestamp` from `sphsim.report` (or extend if needed for batch base)
- `_parse_seeds_list` from `sphsim.cli.args` (for REPL `do_batch`)

### Mirror Phase 4 D-67 (Strategia B): additive-only metrics
**Source pattern:** Phase 4 / 5 / 6 never touched `tests/fixtures/baseline_v1/*.json`. All new keys added to `SKIP_KEYS` and propagated invisibly.
**Apply to Phase 7:** No fixture changes. If JSON for batch is deferred (recommended), no SKIP_KEYS change. Fixtures remain frozen.

### matplotlib state hygiene (Pitfall 5)
**Source pattern:** `sphsim/report/plots.py:72` and `:118` — `try: ... savefig(path) finally: plt.close(fig)`.
**Apply to:** `plot_batch_aggregate` MUST use the same `try/finally` even though figure is dynamic-size (1×5 subplots). Without `plt.close`, batch in REPL session leaks 5 figures per `/batch` invocation.

### Deterministic random per `random.seed(S)` in SPHSimulator constructor
**Source pattern:** `sphsim/core/simulator.py:14` — `random.seed(seed)` unconditional in `__init__`.
**Apply to:** Phase 7 `run_batch` loop relies on this contract. No manual `random.seed` calls in runner.py.

### `argparse.ArgumentTypeError` with Polish messages (custom type converters)
**Source pattern:** `sphsim/cli/args.py:32-49` (`_parse_phi_list`) — try/except wrapping `int()`/`float()`, raise `argparse.ArgumentTypeError` with Polish message echo'ing bad input.
**Apply to:** `_parse_seeds_list` — same shape, two grammar branches (single N, comma list). 10 reject cases per behavioral table.

### Floating-point test assertions (Pitfall 3)
**Source pattern:** Phase 4 / Phase 5 tests use `assertEqual` for ints, `assertAlmostEqual(places=4)` for floats.
**Apply to:** `tests/test_batch_stats.py` — every float assertion MUST use `assertAlmostEqual(places=4)` to tolerate BLAS variations across numpy versions.

---

## 8. No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `sphsim/batch/stats.py` | statistical core | transform (list[dict] → dict[AggregateStat]) | First scipy/numpy aggregation surface in repo. Phase 6 introduced numpy (via matplotlib), but pure-stats helpers are new. RESEARCH §D.6 provides full skeleton — planner passes verbatim to executor. |
| `requirements.txt` (NEW) | dep manifest | static | No existing manifest in repo. Phase 6 left this for Phase 7. RESEARCH §"Environment Availability" recommends adding `matplotlib`, `numpy`, `scipy`. Decision deferred to discuss-phase. |
| `tests/test_batch_stats.py::TestCIComputation::test_ci_against_manual` | unit test (manual scipy comparison) | unittest | First test that manually computes CI to compare against scipy. Pattern: `scipy.stats.t.ppf(0.975, df=n-1)` → expected lower/upper bounds. No prior analog. |

---

## 9. Phase 7 file count summary

**New files (8):**
1. `sphsim/batch/__init__.py`
2. `sphsim/batch/runner.py`
3. `sphsim/batch/stats.py`
4. `sphsim/report/batch_markdown.py`
5. `tests/test_batch.py`
6. `tests/test_batch_stats.py`
7. `tests/test_batch_report.py`
8. `scripts/verify_phase7.sh`

**Optional new files (1):** `requirements.txt` (Claude's Discretion).

**Modified files (4):**
1. `sphsim/report/plots.py` — add `plot_batch_aggregate`
2. `sphsim/report/__init__.py` — add `write_batch_report` + extend `__all__`
3. `sphsim/cli/args.py` — add `_parse_seeds_list` + `--batch`/`--seeds` flags + post-parse mutex
4. `sphsim/cli/main.py` — add 2× `if args.batch:` early branches (built-in + custom)
5. `sphsim/cli/output.py` — add `format_batch_summary`
6. `sphsim/cli/repl.py` — add `do_batch` + extend `do_help`

**Total deltas estimate (RESEARCH §"Summary"):** ~800 LoC new, ~100 LoC modified.

---

## Metadata

**Analog search scope:**
- `sphsim/agent/` (sub-package shape — already established mirror in Phase 6)
- `sphsim/cli/` (run_compare, fake_args, _parse_phi_list, do_compare — all 4 are direct templates)
- `sphsim/core/` (SPHSimulator constructor + `random.seed` determinism contract)
- `sphsim/report/` (Phase 6 — write_report + render_report + plot_kpi_timeseries — all reused or mirrored)
- `scripts/` (verify_phase6.sh framework verbatim — 39 check() invocations as reference)
- `tests/test_env.py` (multi-class subprocess test pattern for Phase 5)
- `tests/test_agent.py` (pure-unit test pattern for Phase 4)
- `tests/test_report.py` (Phase 6 — direct template for Phase 7 report tests)

**Files scanned (read in this session):**
- `sphsim/cli/main.py` (168 LoC — full file)
- `sphsim/cli/args.py` (126 LoC — full file)
- `sphsim/cli/output.py:1-60` (format_json, format_config_header head)
- `sphsim/cli/repl.py:200-360` (do_run, do_compare, default, run_repl)
- `sphsim/core/simulator.py:1-50` (constructor + random.seed contract)
- `sphsim/agent/rational.py` (57 LoC — full file)
- `sphsim/agent/__init__.py` (5 LoC — full file)
- `sphsim/report/__init__.py` (153 LoC — full file)
- `sphsim/report/markdown.py` (214 LoC — full file)
- `sphsim/report/plots.py` (119 LoC — full file)
- `sphsim/config.py` (14 LoC — full file)
- `tests/test_env.py:1-120` (header + TestPhiRhoParsing class)
- `tests/test_agent.py:1-110` (header + TestWrapWithAgent class start)
- `tests/test_report.py:1-100` (header + _make_args helper + class start)
- `scripts/regression_check.py:40-100` (SKIP_KEYS + deep_diff + run_invocation)
- `scripts/verify_phase6.sh` (212 LoC — full file, 39 check() invocations counted)
- `.planning/phases/07-batch-runner-aggregation/07-RESEARCH.md` (Sections A-J + Pitfalls + Sources)
- `.planning/phases/06-report-plots-generator/06-PATTERNS.md` (757 LoC — full file, reference structure)
- `.planning/REQUIREMENTS.md` (137 LoC — BATCH-01..03, PLOT-04)
- `.planning/ROADMAP.md` (235 LoC — Phase 7 section SCs)

**Pattern extraction date:** 2026-05-28
**Verify_phase6.sh check count (reference target for Phase 7):** 39 check() invocations
