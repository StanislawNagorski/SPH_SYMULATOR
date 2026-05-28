# Formatowanie wyniku symulacji — human-readable + JSON.
# Rozszerzono o sekcję VETO (D-66), format_compare (D-62), format_json extension (D-67).
import json


def format_json(args, res, params, K1):
    out = {
        'strategy': args.strategy,
        'strategy_params': params,
        'env': {'nU': args.nU, 'nSUS': args.nSUS, 'K0': args.K0, 'K1': K1,
                'T': args.T, 'kappa': args.kappa, 'alpha': args.alpha,
                'phi': args.phi, 'rho': args.rho, 'seed': args.seed,
                'valuation': args.valuation},
    }
    if 'comparison' in res:
        # Tryb --compare-agent: zastąp 'metrics' blokiem 'comparison' (D-67).
        # Phase 6: _with_agent_full top-level key musi być pominięty (RESEARCH §N.1).
        out['comparison'] = res['comparison']
    else:
        # Standardowy tryb: dodaj agent_enabled do metrics (D-67 backwards compat).
        # Phase 6: filtr `not k.startswith('_')` strippuje prywatne klucze (np. _with_agent_full)
        # — chroni SC#6 stdout-cleanliness i regression baseline equality.
        out['metrics'] = {
            **{k: v for k, v in res.items()
               if k not in ('history', 'devices') and not k.startswith('_')},
            'agent_enabled': not args.no_agent,
        }
    return json.dumps(out, indent=2)


def format_config_header(args, K0, K1, phi, rho) -> str:
    """Serializuje konfigurację środowiska do tabeli Markdown (ENV-03, SC-4).
    Zwracany string to walidna tabela MD — Phase 6 może go wkleić bezpośrednio do report.md.
    """
    phi_str = ', '.join(f'{v:.2f}' for v in phi)
    rho_str = ', '.join(f'{v:.2f}' for v in rho)
    k1_display = '∞' if K1 == float('inf') else str(K1)
    lines = [
        '## Konfiguracja środowiska',
        '',
        '| Parametr | Wartość |',
        '|----------|---------|',
        f'| nU       | {args.nU} |',
        f'| T        | {args.T} |',
        f'| κ (kappa) | {args.kappa} |',
        f'| α (alpha) | {args.alpha} |',
        f'| K0       | {K0} |',
        f'| K1       | {k1_display} |',
        f'| φ (phi)  | {phi_str} |',
        f'| ρ (rho)  | {rho_str} |',
        f'| seed     | {args.seed} |',
    ]
    return '\n'.join(lines)


def format_compare(args, comp, K1):
    """Render tabeli 5×3 delta KPI dla trybu --compare-agent (D-62).

    Argumenty:
        args: argparse.Namespace z parametrami symulacji.
        comp: dict z kluczami with_agent, without_agent, delta, agent_helps.
        K1: próg waluacji konsumentów.

    Zwraca string z tabelą ASCII 5 KPI × 3 kolumny + werdykt agent_helps.
    """
    with_ = comp['with_agent']
    without_ = comp['without_agent']
    delta = comp['delta']

    kpis = [
        ('avg_val_last100',    '{:>12.2f}'),
        ('cum_val_total',      '{:>12.1f}'),
        ('avg_net_profit',     '{:>12.4f}'),
        ('delivery_ratio',     '{:>12.2%}'),
        ('avg_providers_l100', '{:>12.2f}'),
    ]

    lines = []
    sep62 = '─' * 62
    sep_wide = '─' * 66

    lines.append(f"\n{'='*66}")
    lines.append(f"  PORÓWNANIE STRATEGII z/bez RationalAgent")
    lines.append(f"  Strategia: {args.strategy.upper()} | K1={K1}")
    lines.append(f"{'='*66}")
    lines.append(f"  {'KPI':<24}  {'with-agent':>12}  {'bez agenta':>12}  {'Δ (with-no)':>12}")
    lines.append(f"  {sep_wide}")
    for kpi, fmt in kpis:
        w_val = with_.get(kpi, 0)
        wo_val = without_.get(kpi, 0)
        d_val = delta.get(kpi, 0)
        # Formatowanie wartości
        if kpi == 'delivery_ratio':
            w_str = f"{w_val:>12.2%}"
            wo_str = f"{wo_val:>12.2%}"
            sign = '+' if d_val >= 0 else ''
            d_str = f"{sign}{d_val:.2%}"
            d_str = f"{d_str:>12}"
        else:
            fmt_num = fmt
            w_str = fmt_num.format(w_val)
            wo_str = fmt_num.format(wo_val)
            sign = '+' if d_val >= 0 else ''
            # Użyj podobnego formatu dla delty
            if 'f' in fmt:
                precision = fmt.split('.')[-1].replace('f', '')
                try:
                    prec = int(precision)
                    d_raw = f"{sign}{d_val:.{prec}f}"
                except ValueError:
                    d_raw = f"{sign}{d_val:.2f}"
            else:
                d_raw = f"{sign}{d_val:.2f}"
            d_str = f"{d_raw:>12}"
        lines.append(f"  {kpi:<24}{w_str}{wo_str}{d_str}")
    lines.append(f"  {sep_wide}")
    n_vetoed = with_.get('n_vetoed_total', 0)
    verdict = '✓ TAK' if comp['agent_helps'] else '✗ NIE'
    lines.append(
        f"  Veto'wano: {n_vetoed} COMMIT-ów; with-agent bije without-agent: {verdict}"
    )
    lines.append(f"{'='*66}")
    lines.append("")
    return "\n".join(lines)


def format_human(args, res, K1, verbose):
    # Comparison branch (D-62) — early return dla --compare-agent.
    if 'comparison' in res:
        return format_compare(args, res['comparison'], K1)

    lines = [format_config_header(args, args.K0, K1, args.phi, args.rho), '']
    sep = '─' * 62
    lines.append(f"\n{'='*62}")
    lines.append(f"  SPH SYMULATOR  |  Strategia: {args.strategy.upper()}")
    lines.append(f"  nU={args.nU}, nSUS={args.nSUS}, K1={K1}, T={args.T}, κ={args.kappa}, α={args.alpha}")
    lines.append(f"{'='*62}")
    lines.append(f"\n  METRYKI (asymptota — ostatnie 100 z {args.T} cykli):")
    lines.append(f"  {sep}")
    lines.append(f"  Śr. waluacja Konsumentów (ost.100):   {res['avg_val_last100']:>10.2f}")
    lines.append(f"  Łączna waluacja (wszystkie cykle):    {res['cum_val_total']:>10.1f}")
    lines.append(f"  Śr. zysk netto na urządzenie:         {res['avg_net_profit']:>10.4f}")
    lines.append(f"  Wskaźnik ciągłości dostaw:            {res['delivery_ratio']:>10.2%}")
    lines.append(f"  Śr. liczba dostawców (ost.100):       {res['avg_providers_l100']:>10.2f}")
    lines.append(f"  Zajętość SUS (końcowa):               {res['sus_final']:>10}")
    lines.append(f"  {sep}")

    commit_devs = [d for d in res['devices'] if d.n_commit > 0]
    if commit_devs:
        avg_cp = sum(d.net_profit for d in commit_devs) / len(commit_devs)
        lines.append(f"  Śr. zysk urządzeń wyk. COMMIT:        {avg_cp:>10.4f}")

    # IC per-phase analysis
    ic = res.get('ic_per_phase', {})
    if ic:
        lines.append(f"\n  ZGODNOŚĆ MOTYWACYJNA (IC) — zysk netto per COMMIT w fazie:")
        lines.append(f"  {sep}")
        lines.append(f"  {'Faza':>6}  {'COMMIT':>8}  {'Sukces%':>8}  {'E[przychód]':>12}  {'E[koszt]':>10}  {'E[zysk]':>10}  {'IC?':>5}")
        lines.append(f"  {sep}")
        all_ic = True
        for ph in sorted(ic):
            d = ic[ph]
            ic_mark = '  ✓' if d['ic_satisfied'] else '  ✗'
            if not d['ic_satisfied']:
                all_ic = False
            lines.append(f"  {ph:>6}  {d['commits']:>8}  {d['delivery_rate']:>7.1%}  {d['avg_earning_per_commit']:>12.4f}  {d['avg_cost_per_commit']:>10.4f}  {d['avg_net_per_commit']:>10.4f}  {ic_mark}")
        lines.append(f"  {sep}")
        verdict = "TAK — wszystkie fazy" if all_ic else "NIE — nie wszystkie fazy"
        lines.append(f"  Zgodność motywacyjna: {verdict}")

    # VETO per-phase summary (Phase 4 D-66) — po sekcji IC, przed verbose block.
    veto_pp = res.get('veto_per_phase', {})
    n_vetoed = res.get('n_vetoed_total', 0)
    if n_vetoed > 0:
        lines.append(f"\n  VETO przez RationalAgent — rekomendacje COMMIT odrzucone per faza:")
        lines.append(f"  {sep}")
        lines.append(f"  {'Faza':>6}  {'COMMIT zgłoszone':>18}  {'VETO':>8}  {'% zaweto':>10}")
        lines.append(f"  {sep}")
        ic_ref = res.get('ic_per_phase', {})
        total_committed = 0
        for ph in sorted(set(list(veto_pp.keys()) + list(ic_ref.keys()))):
            commits = ic_ref.get(ph, {}).get('commits', 0)
            vetos = veto_pp.get(ph, 0)
            total = commits + vetos
            pct = (vetos / total * 100) if total > 0 else 0
            lines.append(f"  {ph:>6}  {total:>18}  {vetos:>8}  {pct:>9.1f}%")
            total_committed += total
        lines.append(f"  {sep}")
        pct_total = (n_vetoed / max(total_committed, 1)) * 100
        lines.append(f"  Łącznie zaweto'wano: {n_vetoed} COMMIT-ów z {total_committed} zgłoszonych ({pct_total:.1f}%).")

    if verbose:
        lines.append(f"\n  Próbkowanie waluacji (co 100 cykli):")
        h = res['history']
        for i in range(0, args.T, 100):
            idx = min(i + 99, args.T - 1)
            lines.append(f"    t={i+100:5d}: val={h['val'][idx]:6.1f}  "
                         f"prov={h['providers'][idx]:4d}  SUS={h['sus'][idx]:3d}")
    lines.append("")
    return "\n".join(lines)


def format_batch_summary(args, aggregate, K1) -> str:
    """Phase 7 BATCH-01: krótkie podsumowanie agregatu na stdout (banner + 5 KPI rows + werdykt).

    Werdykt baseline-beating reads BASELINE_PATH (Phase 6 single source of truth)
    — zero hardcoded baseline literals (per RESEARCH §A.1, BLOCKER #1).
    K1 zachowane dla symetrii API; obecnie nieużywane.

    Args:
        args:      argparse.Namespace — wymagane pola: strategy.
        aggregate: dict[str, AggregateStat] z aggregate_kpis (5 kluczy z KPIS).
        K1:        próg waluacji konsumentów (placeholder dla symetrii z format_compare).

    Returns:
        Multi-line string: banner '=== BATCH SUMMARY ===' + 5 KPI rows (mean/std/CI)
        + 'Werdykt' line (baseline-beating verdict driven by BASELINE_PATH).
    """
    # Deferred imports — unika top-level circular (output.py → batch.stats → ... → cli)
    # AND defers BASELINE_PATH filesystem read do call-time (testowalne fallback).
    from sphsim.batch.stats import KPIS
    from sphsim.report.markdown import BASELINE_PATH
    import json
    try:
        baseline_avg = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))["metrics"]["avg_val_last100"]
    except (FileNotFoundError, KeyError, ValueError):
        # Jawny fallback — NIGDY nie substytujemy magic-number'em (BLOCKER #1).
        baseline_avg = None

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

    val_stat = aggregate['avg_val_last100']
    if val_stat.ci_lower is not None and baseline_avg is not None and val_stat.ci_lower > baseline_avg:
        verdict_line = f"✓ BIJE baseline (CI_lower > {baseline_avg:.1f})"
    elif baseline_avg is None:
        verdict_line = "⚠ Werdykt baseline niedostępny (brak fixture)"
    elif val_stat.ci_lower is not None:
        verdict_line = f"✗ NIE bije baseline (CI_lower ≤ {baseline_avg:.1f})"
    elif val_stat.mean > baseline_avg:
        verdict_line = f"✓ TAK (N=1, single-point > {baseline_avg:.1f})"
    else:
        verdict_line = f"✗ NIE (N=1, single-point ≤ {baseline_avg:.1f})"
    lines.append(f"  Werdykt: {verdict_line}")
    return '\n'.join(lines)
