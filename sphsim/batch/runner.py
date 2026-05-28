"""Phase 7: Sequential batch orchestrator (BATCH-01).

Pure function — żadnego IO. Wywołuje N× SPHSimulator(seed=S).run() + aggregate_kpis.
Determinizm via SPHSimulator.__init__ unconditional reseed (simulator.py:14)
— NIE reseed'ujemy manualnie w loopie (double-seeding == idempotent ale myli).
"""
from sphsim.core.simulator import SPHSimulator
from sphsim.config import DEFAULT_F
from sphsim.batch.stats import aggregate_kpis, KPIS
from sphsim.agent import wrap_with_agent


def run_batch(args, raw_strategy_fn, params, K1):
    """Sekwencyjnie uruchamia symulację dla każdego seeda w args.seeds (BATCH-01).

    Adapter między Plan 07-01 (aggregate_kpis) a CLI surface. Owns ZERO matematyki
    (deleguje do aggregate_kpis) i ZERO IO (caller zapisuje stdout/raport). Slice
    do KPIS-only dict — history/devices/ic_per_phase/veto_per_phase/abstain_per_phase
    NIE są propagowane (memory savings + simpler downstream consumers Plan 07-04).

    Args:
        args:             argparse.Namespace — wymagane pola: seeds (list[int]),
                          nU, nSUS, K0, T, kappa, alpha, phi, rho, valuation,
                          strategy, no_agent, expected_P.
        raw_strategy_fn:  Czysta (niezawinięta) strategia — snapshot sprzed
                          wrap_with_agent (T-04-13 mitigation, analogicznie do main.py).
        params:           dict parametrów strategii (np. {'zeta': 0.75}).
        K1:               Górna granica waluacji konsumentów (float).

    Returns:
        Tuple (per_seed_results, aggregate):
          - per_seed_results: list[dict[str, float]] o długości len(args.seeds);
            każdy dict zawiera DOKŁADNIE 5 kluczy z KPIS (slice — bez history/devices).
          - aggregate: dict[str, AggregateStat] z 5 kluczami z KPIS
            (mean/std/min/max/95% CI z df=n-1).

    Notes:
        - Determinizm: SPHSimulator.__init__ reseed'uje PRNG bezwarunkowo
          (simulator.py:14). NIE reseed'ujemy ręcznie w loop iter — dwukrotne
          wywołanie run_batch z identycznym args.seeds → byte-identical per_seed_results.
        - Agent wrap: tylko gdy args.no_agent is False (mirror main.py:147-148).
          wrap_with_agent przyjmuje expected_P jako drugi argument.
        - Per-iter mutacja: seed jest jedynym parametrem zmieniającym się między
          iteracjami → wykluczamy go z `common` i przekazujemy per-call.
    """
    common = dict(
        nU=args.nU, nSUS=args.nSUS, K0=args.K0, K1=K1,
        F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
        phi=args.phi, rho=args.rho, valuation_preset=args.valuation,
        params=params,
        # seed NIE w common — varia per-iter; przekazywany jako keyword argument w pętli.
    )

    # Conditional wrap — tylko gdy args.no_agent is False (mirror main.py:147-148).
    strategy_fn = raw_strategy_fn
    if not args.no_agent:
        strategy_fn = wrap_with_agent(raw_strategy_fn, args.expected_P)

    per_seed_results = []
    for seed in args.seeds:
        sim = SPHSimulator(strategy_fn=strategy_fn, seed=seed, **common)
        res = sim.run()
        # KPI slice: tylko 5 kanonicznych KPIS-ów (KPIS tuple z stats.py).
        # history/devices/ic_per_phase/veto_per_phase/abstain_per_phase NIE są propagowane
        # — Plan 07-04 (raport batch) potrzebuje wyłącznie KPI-ów do agregacji.
        per_seed_results.append({k: res[k] for k in KPIS})

    aggregate = aggregate_kpis(per_seed_results)
    return per_seed_results, aggregate
