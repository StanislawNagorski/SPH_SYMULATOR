# Formatowanie wyniku symulacji — human-readable + JSON.
import json


def format_json(args, res, params, K1):
    out = {
        'strategy': args.strategy,
        'strategy_params': params,
        'env': {'nU': args.nU, 'nSUS': args.nSUS, 'K1': K1,
                'T': args.T, 'kappa': args.kappa, 'alpha': args.alpha},
        'metrics': {k: v for k, v in res.items() if k not in ('history', 'devices')},
    }
    return json.dumps(out, indent=2)


def format_human(args, res, K1, verbose):
    lines = []
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

    if verbose:
        lines.append(f"\n  Próbkowanie waluacji (co 100 cykli):")
        h = res['history']
        for i in range(0, args.T, 100):
            idx = min(i + 99, args.T - 1)
            lines.append(f"    t={i+100:5d}: val={h['val'][idx]:6.1f}  "
                         f"prov={h['providers'][idx]:4d}  SUS={h['sus'][idx]:3d}")
    lines.append("")
    return "\n".join(lines)
