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
