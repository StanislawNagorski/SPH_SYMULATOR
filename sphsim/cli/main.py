# Entry point CLI — parse args, buduje SPHSimulator, run, formatuje wynik.
from sphsim.cli.args import parse_args
from sphsim.cli.output import format_human, format_json
from sphsim.core.simulator import SPHSimulator
from sphsim.strategies import STRATEGIES
from sphsim.config import DEFAULT_K0, DEFAULT_F, DEFAULT_PHI, DEFAULT_RHO


def main():
    args = parse_args()
    if args.interactive:
        from sphsim.cli.repl import run_repl
        run_repl()
        return
    # Graceful warning: --param działa tylko z --custom (D-39 Claude's Discretion).
    # Nie sys.exit — built-in flow leci dalej, zignorowane tokens nie wpływają na argparse.
    if args.param and not args.custom:
        import sys
        print('Flaga --param ignorowana — działa tylko z --custom.', file=sys.stderr)
    # Early branch: custom strategy load + simulate + format (D-44, D-45, D-46).
    if args.custom:
        import sys
        from sphsim.strategies.loader import load_custom, parse_params_from_meta, LoaderError
        # Layer 1: ładowanie + walidacja pliku (banner [OSTRZEŻENIE] na stdout w loaderze).
        try:
            name, strategy_fn, meta = load_custom(args.custom)
        except LoaderError as e:
            print(e.args[0], file=sys.stderr)
            sys.exit(1)
        # Layer 2: parse --param tokens przeciw STRATEGY_META (typed conversion).
        try:
            params = parse_params_from_meta(args.param, meta, name)
        except LoaderError as e:
            print(e.args[0], file=sys.stderr)
            sys.exit(1)
        # Rejestracja w wywołującym (D-46 pure loader). Żyje do końca procesu CLI.
        STRATEGIES[name] = strategy_fn
        # Quick fix: args.strategy = None (mutex), format_human/format_json używają go
        # jako field 'strategy'. Ustawiamy nazwę custom strategii dla spójnego output'u.
        args.strategy = name
        K1 = float('inf') if args.K1 < 0 else args.K1
        sim = SPHSimulator(
            nU=args.nU, nSUS=args.nSUS, K0=DEFAULT_K0, K1=K1,
            F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
            phi=DEFAULT_PHI, rho=DEFAULT_RHO,
            strategy_fn=strategy_fn, params=params, seed=args.seed,
        )
        res = sim.run()
        if args.json:
            print(format_json(args, res, params, K1))
        else:
            print(format_human(args, res, K1, args.verbose))
        return
    K1 = float('inf') if args.K1 < 0 else args.K1
    params = {
        'zeta': args.zeta, 'max_phase': args.max_phase,
        'probs': args.probs, 's_target': args.s_target,
        'expected_P': args.expected_P,
    }
    sim = SPHSimulator(
        nU=args.nU, nSUS=args.nSUS, K0=DEFAULT_K0, K1=K1,
        F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
        phi=DEFAULT_PHI, rho=DEFAULT_RHO,
        strategy_fn=STRATEGIES[args.strategy],
        params=params, seed=args.seed,
    )
    res = sim.run()

    if args.json:
        print(format_json(args, res, params, K1))
    else:
        print(format_human(args, res, K1, args.verbose))
