"""Phase 6: Markdown report assembly. Pure functions, zero side effects.

render_report(args, res, params, K1, *, mode) returns a complete MD string
composed from 6 fixed sections + 1 optional compare-mode section. Section 1
(Konfiguracja środowiska) reuses sphsim.cli.output.format_config_header
verbatim — single source of truth for env serialization (ENV-03, D-PH5).

Polish-language convention applies — all section headers, column labels,
and baseline disclaimers in Polish (PROJECT.md constraint).
"""
import json
from datetime import datetime
from pathlib import Path

from sphsim.cli.output import format_config_header

# Path resolution: <repo>/sphsim/report/markdown.py
#   .parent             = <repo>/sphsim/report/
#   .parent.parent      = <repo>/sphsim/
#   .parent.parent.parent = <repo>/
BASELINE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / 'tests' / 'fixtures' / 'baseline_v1'
    / '08-naive-zeta-0.75-baseline.json'
)

# Canonical 5-KPI tuple from ROADMAP SC#2. Order is load-bearing — tests assert on it.
_KPI_ROWS = (
    ('avg_val_last100',     '{:.2f}',     'MAX → 100'),
    ('cum_val_total',       '{:.1f}',     'MAX → 100000'),
    ('avg_net_profit',      '{:+.4f}',    '> 0'),
    ('delivery_ratio',      '{:.2%}',     'wysoki'),
    ('avg_providers_l100',  '{:.2f}',     '≈ 100..120'),
)


def render_report(args, res, params, K1, *, mode='single') -> str:
    """Zwraca pełen raport MD jako string. Pure function — zero side effects.

    Args:
        args:    argparse.Namespace — wymagane pola: nU, nSUS, T, kappa,
                 alpha, K0, phi, rho, seed, strategy, no_agent
                 (compare_agent jest opcjonalne — domyślnie False jeśli
                 atrybut nie istnieje).
        res:     dict z SPHSimulator.run() (single mode) LUB
                 dict z kluczem 'comparison' (compare mode).
        params:  dict parametrów strategii.
        K1:      float (może być float('inf')).
        mode:    'single' | 'compare'.

    Returns:
        str — pełen raport MD (≈100 linii, 4-6 KB).
    """
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


def _render_title(args) -> str:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f'# Raport symulacji SPH — `{args.strategy}` ({ts})'


def _render_strategy_params(args, params) -> str:
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
    # Tryb agenta dispatch — defensive getattr for fake_args missing compare_agent.
    if getattr(args, 'compare_agent', False):
        lines.append('| Tryb agenta | porównawczy (`--compare-agent`) |')
    elif getattr(args, 'no_agent', False):
        lines.append('| Tryb agenta | wyłączony (`--no-agent`) |')
    else:
        lines.append('| Tryb agenta | włączony (domyślnie) |')
    return '\n'.join(lines)


def _extract_metrics_source(res, mode):
    """Zwraca dict z metrykami: w compare bierze with_agent, w single bierze res."""
    if mode == 'compare':
        return res['comparison']['with_agent']
    return res


def _render_kpi_table(res, *, mode='single') -> str:
    src = _extract_metrics_source(res, mode)
    lines = [
        '## Metryki KPI',
        '',
        '| KPI | Wartość | Cel |',
        '|-----|---------|-----|',
    ]
    for key, fmt, cel in _KPI_ROWS:
        val = src.get(key)
        if val is None:
            lines.append(f'| {key} | (brak) | {cel} |')
        else:
            lines.append(f'| {key} | {fmt.format(val)} | {cel} |')
    return '\n'.join(lines)


def _render_decision_table(res, *, mode='single') -> str:
    src = _extract_metrics_source(res, mode)
    ic = src.get('ic_per_phase', {}) or {}
    veto = src.get('veto_per_phase', {}) or {}
    abst = src.get('abstain_per_phase', {}) or {}
    phases = sorted(set(ic.keys()) | set(veto.keys()) | set(abst.keys()))
    lines = [
        '## Rozkład decyzji per faza',
        '',
        '| Faza | COMMIT | ABSTAIN | VETO | Suma |',
        '|------|--------|---------|------|------|',
    ]
    if not phases:
        lines.append('| — | — | — | — | — |')
        lines.append('')
        lines.append('*Brak danych decyzji (run pusty lub strategia inna).*')
        return '\n'.join(lines)
    for p in phases:
        ic_entry = ic.get(p)
        c = ic_entry.get('commits', 0) if isinstance(ic_entry, dict) else 0
        a = abst.get(p, 0)
        v = veto.get(p, 0)
        s = c + a + v
        lines.append(f'| {p}    | {c}    | {a}     | {v}  | {s}  |')
    return '\n'.join(lines)


def _render_plots_section() -> str:
    return (
        '## Wykresy\n\n'
        '![Rozkład decyzji per faza](decision_distribution.png)\n\n'
        '![Przebieg KPI w czasie](kpi_timeseries.png)'
    )


def _render_baseline_comparison(res, *, mode='single') -> str:
    src = _extract_metrics_source(res, mode)
    try:
        baseline_raw = json.loads(BASELINE_PATH.read_text(encoding='utf-8'))
        baseline = baseline_raw['metrics']
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        return (
            '## Porównanie z baseline `naive --zeta 0.75 --no-agent`\n\n'
            f'*Baseline niedostępny ({type(e).__name__}) — sekcja pominięta.*'
        )
    lines = [
        '## Porównanie z baseline `naive --zeta 0.75 --no-agent`',
        '',
        '| KPI | Bieżący run | Baseline v1.0 | Δ |',
        '|-----|-------------|---------------|---|',
    ]
    for key, fmt, _cel in _KPI_ROWS:
        cur = src.get(key)
        base = baseline.get(key)
        if cur is None or base is None:
            lines.append(f'| {key} | (brak) | (brak) | — |')
            continue
        delta = cur - base
        if key == 'delivery_ratio':
            lines.append(f'| {key} | {cur:.2%} | {base:.2%} | {delta:+.2%} |')
        else:
            lines.append(f'| {key} | {fmt.format(cur)} | {fmt.format(base)} | {delta:+.4f} |')
    lines.append('')
    lines.append(
        '*Baseline z `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json`. '
        'Uwaga: jeśli używasz override `--phi`/`--rho`/`--K0`/`--valuation`/`--T`/`--nU`, '
        'środowisko może różnić się od baseline — porównanie jest wtedy poglądowe.*'
    )
    return '\n'.join(lines)


def _render_compare_section(res) -> str:
    comp = res['comparison']
    with_, without_, delta = comp['with_agent'], comp['without_agent'], comp['delta']
    helps = '✓ TAK' if comp.get('agent_helps') else '✗ NIE'
    n_veto = with_.get('n_vetoed_total', 0)
    lines = [
        '## Porównanie z RationalAgent (with-agent vs bez agenta)',
        '',
        '| KPI | with-agent | bez agenta | Δ (with − bez) |',
        '|-----|------------|------------|----------------|',
    ]
    for key, fmt, _cel in _KPI_ROWS:
        w, wo, d = with_.get(key), without_.get(key), delta.get(key)
        if w is None or wo is None or d is None:
            lines.append(f'| {key} | (brak) | (brak) | — |')
            continue
        if key == 'delivery_ratio':
            lines.append(f'| {key} | {w:.2%} | {wo:.2%} | {d:+.2%} |')
        else:
            lines.append(f'| {key} | {fmt.format(w)} | {fmt.format(wo)} | {d:+.4f} |')
    lines.append('')
    lines.append(
        f"**Werdykt:** Agent zaweto'wał {n_veto} COMMIT-ów. "
        f"with-agent bije without-agent: {helps}."
    )
    return '\n'.join(lines)
