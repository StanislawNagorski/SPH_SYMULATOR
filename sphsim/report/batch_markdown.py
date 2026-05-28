"""Phase 7: Generator raportu MD dla trybu batch (BATCH-03).

Pure function — `render_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list) -> str`.

Sekcje (kolejność load-bearing, testy assertują):
  1. Title — '# Raport batchowy SPH — <strategia> × N seedów (ts)'
  2. Konfiguracja środowiska (REUSE format_config_header z sphsim/cli/output.py)
  3. Strategia i parametry + tryb agenta + liczba seedów
  4. Wyniki per seed — tabela N×6 (seed + 5 KPI)
  5. Agregat statystyczny — tabela 5 KPI × 7 kolumn (KPI / mean / std / min / max / 95% CI / N)
  6. Wykresy — link `![Box-ploty 5 KPI dla N seedów](batch_aggregate.png)`
  7. Werdykt baseline-beating — czy strategia bije baseline `naive --zeta 0.75` (SC#5)

Werdykt korzysta z `BASELINE_PATH` (Phase 6 single source of truth) — ZERO hardcoded
literałów baseline (BLOCKER #1 mitigation). N=1 fallback porównuje mean vs baseline
i emituje DODATKOWY polski disclaimer informujący o braku CI (Warning #7 mitigation).

Polish-language convention zachowana z Phase 6 (PROJECT.md constraint).
"""
import json
from datetime import datetime

from sphsim.cli.output import format_config_header
# Reuse Phase 6 baseline location + KPI rows — single source of truth.
from sphsim.report.markdown import BASELINE_PATH, _KPI_ROWS


def render_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list) -> str:
    """Zwraca pełen raport batchowy MD jako string. Pure function — zero IO.

    Args:
        args:             argparse.Namespace — wymagane pola: nU, nSUS, T, kappa,
                          alpha, K0, phi, rho, seed, strategy, no_agent.
        per_seed_results: list[dict[str, float]] — N dictów z 5 kluczami z KPIS,
                          jeden per seed (output `run_batch`).
        aggregate:        dict[str, AggregateStat] z `aggregate_kpis` (5 KPIs).
        params:           dict parametrów strategii (np. {'zeta': 0.75}).
        K1:               float (może być float('inf')).
        seeds_list:       list[int] — wartości seedów odpowiadające per_seed_results.

    Returns:
        str — pełen raport batchowy MD (≈100..200 linii w zależności od N seedów).
    """
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


def _render_title(args, n_seeds: int) -> str:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f'# Raport batchowy SPH — `{args.strategy}` × {n_seeds} seedów ({ts})'


def _render_strategy_params(args, params, seeds_list) -> str:
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


def _render_per_seed_table(per_seed_results, seeds_list) -> str:
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


def _render_aggregate_table(aggregate) -> str:
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


def _render_boxplot_section() -> str:
    """Static link section — fixed alt-text, N is carried by fig.suptitle (PLOT-04)."""
    return (
        '## Wykresy\n\n'
        '![Box-ploty 5 KPI dla N seedów](batch_aggregate.png)'
    )


def _render_baseline_beating(aggregate) -> str:
    """Werdykt SC#5: czy strategia bije baseline `naive --zeta 0.75`? (avg_val_last100).

    Reads baseline_avg z `BASELINE_PATH` (Phase 6 single source of truth) — ZERO
    hardcoded literałów baseline. Dla N≥2 porównuje CI_lower vs baseline_avg;
    dla N=1 (degenerate — ci_lower is None) fall-backuje do mean vs baseline_avg
    i ZAWSZE dodaje polski disclaimer `*N=1: brak CI, ...*` (Warning #7 mitigation).
    """
    header = "## Werdykt: bije baseline `naive --zeta 0.75`?\n"
    try:
        baseline_raw = json.loads(BASELINE_PATH.read_text(encoding='utf-8'))
        baseline_avg = baseline_raw['metrics']['avg_val_last100']
    except (FileNotFoundError, KeyError, ValueError) as e:
        return header + f"\n*Baseline niedostępny ({type(e).__name__}) — werdykt pominięty.*\n"

    val_stat = aggregate['avg_val_last100']
    if val_stat.ci_lower is not None:
        # N≥2 — CI-based verdict (asymptotic statystyczna inferenecja).
        if val_stat.ci_lower > baseline_avg:
            verdict = f"✓ TAK — CI_lower={val_stat.ci_lower:.2f} > baseline={baseline_avg:.1f}"
        else:
            verdict = f"✗ NIE — CI_lower={val_stat.ci_lower:.2f} ≤ baseline={baseline_avg:.1f}"
        return header + f"\n{verdict}\n"
    else:
        # N=1 — point-estimate fallback + explicit Polish disclaimer (Warning #7).
        if val_stat.mean > baseline_avg:
            verdict = f"✓ TAK — mean={val_stat.mean:.2f} > baseline={baseline_avg:.1f}"
        else:
            verdict = f"✗ NIE — mean={val_stat.mean:.2f} ≤ baseline={baseline_avg:.1f}"
        disclaimer = "*N=1: brak CI, werdykt na podstawie pojedynczego punktu.*"
        return header + f"\n{verdict}\n\n{disclaimer}\n"
