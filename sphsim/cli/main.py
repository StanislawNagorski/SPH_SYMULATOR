# Entry point CLI — parse args, buduje SPHSimulator, run, formatuje wynik.
# Phase 4: wrap_with_agent default-on (D-58), --no-agent escape hatch (D-59),
#           --compare-agent tryb porównawczy via run_compare (D-60).
# Phase 6: write_report orchestrator wired przy każdym sim.run()/run_compare();
#          banner na sys.stderr (Pitfall 3 — --json stdout cleanliness).
import sys

from sphsim.cli.args import parse_args
from sphsim.cli.output import format_human, format_json
from sphsim.core.simulator import SPHSimulator
from sphsim.strategies import STRATEGIES
from sphsim.config import DEFAULT_K0, DEFAULT_F, DEFAULT_PHI, DEFAULT_RHO
from sphsim.agent import wrap_with_agent
from sphsim.report import write_report


def run_compare(args, raw_strategy_fn, name, params, K1):
    """Uruchamia 2x: z agentem i bez — zwraca dict z kluczem 'comparison'.

    Argumenty:
        args: argparse.Namespace z parametrami symulacji (nU, nSUS, T, kappa, alpha, seed, expected_P).
        raw_strategy_fn: czysta (niezawinięta) strategia — snapshot sprzed wrap'u (D-60, T-04-13).
        name: nazwa strategii (string) — informacyjnie.
        params: dict parametrów strategii.
        K1: górna granica waluacji konsumentów.

    Zwraca:
        {'comparison': {'with_agent': {...}, 'without_agent': {...}, 'delta': {...}, 'agent_helps': bool}}
    """
    # Phase 5 ENV-02: K0/valuation_preset z args (default DEFAULT_K0/'window' via argparse).
    common = dict(
        nU=args.nU, nSUS=args.nSUS, K0=args.K0, K1=K1,
        F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
        phi=args.phi, rho=args.rho, valuation_preset=args.valuation,
        params=params, seed=args.seed,
    )
    # Uruchomienie z agentem — ten sam seed (Claude's Discretion: deterministyczne porównanie).
    sim_with = SPHSimulator(strategy_fn=wrap_with_agent(raw_strategy_fn, args.expected_P), **common)
    res_with = sim_with.run()
    # Uruchomienie bez agenta — surowa strategia.
    sim_without = SPHSimulator(strategy_fn=raw_strategy_fn, **common)
    res_without = sim_without.run()
    # 5 KPI do delta (D-62).
    KPIS = ['avg_val_last100', 'cum_val_total', 'avg_net_profit', 'delivery_ratio', 'avg_providers_l100']
    return {
        'comparison': {
            'with_agent':    {k: v for k, v in res_with.items() if k not in ('history', 'devices')},
            'without_agent': {k: v for k, v in res_without.items() if k not in ('history', 'devices')},
            'delta':         {k: res_with[k] - res_without[k] for k in KPIS},
            'agent_helps':   res_with['avg_net_profit'] > res_without['avg_net_profit'],
        },
        # Phase 6 PLOT-02: pełny res_with (z history) dla compare-mode PNG; key
        # prefixed underscore → format_json strippuje (RESEARCH §N.1).
        '_with_agent_full': res_with,
    }


def main():
    args = parse_args()
    if args.interactive:
        from sphsim.cli.repl import run_repl
        run_repl()
        return
    # Graceful warning: --param działa tylko z --custom (D-39 Claude's Discretion).
    # Phase 6: `sys` jest top-level import (linia 6) — usuwamy wcześniejsze lokalne
    # `import sys` które shadowowały moduł i powodowały UnboundLocalError w gałęzi
    # built-in single-run (write_report banner używa sys.stderr).
    if args.param and not args.custom:
        print('Flaga --param ignorowana — działa tylko z --custom.', file=sys.stderr)

    # === Early branch: custom strategy ===
    if args.custom:
        from sphsim.strategies.loader import load_custom, parse_params_from_meta, LoaderError
        try:
            name, strategy_fn, meta = load_custom(args.custom)
        except LoaderError as e:
            print(e.args[0], file=sys.stderr)
            sys.exit(1)
        try:
            params = parse_params_from_meta(args.param, meta, name)
        except LoaderError as e:
            print(e.args[0], file=sys.stderr)
            sys.exit(1)
        STRATEGIES[name] = strategy_fn
        args.strategy = name
        K1 = float('inf') if args.K1 < 0 else args.K1

        # (c) snapshot raw strategy BEFORE any wrap — T-04-13 mitigation.
        raw_strategy_fn = strategy_fn

        # (d') Batch branch — early return, PRZED compare-agent i single-run (Phase 7 BATCH-01).
        if args.batch:
            from sphsim.batch import run_batch
            from sphsim.cli.output import format_batch_summary
            per_seed_results, aggregate = run_batch(args, raw_strategy_fn, params, K1)
            # Phase 7 BATCH-03 + PLOT-04: side-effect raport batchowy po sukcesie run_batch.
            from sphsim.report import write_batch_report
            report_dir = write_batch_report(args, per_seed_results, aggregate, params, K1, args.seeds)
            if report_dir:
                print(f'Raport batchowy zapisany do: {report_dir}/report.md', file=sys.stderr)
            print(format_batch_summary(args, aggregate, K1))
            return

        # (d) Compare branch — early return, PRZED conditional wrap (step e).
        if args.compare_agent:
            res = run_compare(args, raw_strategy_fn, name, params, K1)
            # Phase 6 REPORT-03: side-effect raport po sukcesie run_compare.
            report_dir = write_report(args, res, params, K1, mode='compare')
            if report_dir:
                print(f'Raport porównawczy zapisany do: {report_dir}/report.md', file=sys.stderr)
            print(format_json(args, res, params, K1) if args.json else format_human(args, res, K1, args.verbose))
            return

        # (e) Conditional wrap — tylko dla single-run (nie compare).
        if not args.no_agent:
            strategy_fn = wrap_with_agent(strategy_fn, args.expected_P)

        # (f) Build + run + render.
        # Phase 5 ENV-02: K0/valuation_preset z args (default DEFAULT_K0/'window' via argparse).
        sim = SPHSimulator(
            nU=args.nU, nSUS=args.nSUS, K0=args.K0, K1=K1,
            F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
            phi=args.phi, rho=args.rho, valuation_preset=args.valuation,
            strategy_fn=strategy_fn, params=params, seed=args.seed,
        )
        res = sim.run()
        # Phase 6 REPORT-01: side-effect raport po sukcesie sim.run().
        report_dir = write_report(args, res, params, K1, mode='single')
        if report_dir:
            print(f'Raport zapisany do: {report_dir}/report.md', file=sys.stderr)
        if args.json:
            print(format_json(args, res, params, K1))
        else:
            print(format_human(args, res, K1, args.verbose))
        return

    # === Built-in strategy branch ===
    K1 = float('inf') if args.K1 < 0 else args.K1
    params = {
        'zeta': args.zeta, 'max_phase': args.max_phase,
        'probs': args.probs, 's_target': args.s_target,
        'expected_P': args.expected_P,
    }

    # (c) snapshot raw strategy BEFORE any wrap — T-04-13 mitigation.
    raw_strategy_fn = STRATEGIES[args.strategy]

    # (d') Batch branch — early return, PRZED compare-agent i single-run (Phase 7 BATCH-01).
    if args.batch:
        from sphsim.batch import run_batch
        from sphsim.cli.output import format_batch_summary
        per_seed_results, aggregate = run_batch(args, raw_strategy_fn, params, K1)
        # Phase 7 BATCH-03 + PLOT-04: side-effect raport batchowy po sukcesie run_batch.
        from sphsim.report import write_batch_report
        report_dir = write_batch_report(args, per_seed_results, aggregate, params, K1, args.seeds)
        if report_dir:
            print(f'Raport batchowy zapisany do: {report_dir}/report.md', file=sys.stderr)
        print(format_batch_summary(args, aggregate, K1))
        return

    # (d) Compare branch — early return, PRZED conditional wrap (step e).
    if args.compare_agent:
        res = run_compare(args, raw_strategy_fn, args.strategy, params, K1)
        # Phase 6 REPORT-03: side-effect raport porównawczy.
        report_dir = write_report(args, res, params, K1, mode='compare')
        if report_dir:
            print(f'Raport porównawczy zapisany do: {report_dir}/report.md', file=sys.stderr)
        print(format_json(args, res, params, K1) if args.json else format_human(args, res, K1, args.verbose))
        return

    # (e) Conditional wrap — tylko dla single-run.
    strategy_fn = raw_strategy_fn
    if not args.no_agent:
        strategy_fn = wrap_with_agent(strategy_fn, args.expected_P)

    # (f) Build + run + render.
    # Phase 5 ENV-02: K0/valuation_preset z args (default DEFAULT_K0/'window' via argparse).
    sim = SPHSimulator(
        nU=args.nU, nSUS=args.nSUS, K0=args.K0, K1=K1,
        F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
        phi=args.phi, rho=args.rho, valuation_preset=args.valuation,
        strategy_fn=strategy_fn,
        params=params, seed=args.seed,
    )
    res = sim.run()
    # Phase 6 REPORT-01: side-effect raport po sukcesie sim.run().
    report_dir = write_report(args, res, params, K1, mode='single')
    if report_dir:
        print(f'Raport zapisany do: {report_dir}/report.md', file=sys.stderr)

    if args.json:
        print(format_json(args, res, params, K1))
    else:
        print(format_human(args, res, K1, args.verbose))
