# Registry strategii — mutable global; Phase 3 (custom loader) dodaje klucze runtime'owo.
# Kolejność kluczy zachowana verbatim z sph_sim.py:170–176 (widoczna w argparse --help choices).
from typing import Callable

from sphsim.strategies.naive import strategy_naive
from sphsim.strategies.threshold import strategy_threshold
from sphsim.strategies.phase_prob import strategy_phase_prob
from sphsim.strategies.incentive import strategy_incentive
from sphsim.strategies.adaptive import strategy_adaptive

StrategyFn = Callable[..., str]

STRATEGIES = {
    'naive': strategy_naive,
    'threshold': strategy_threshold,
    'phase_prob': strategy_phase_prob,
    'incentive': strategy_incentive,
    'adaptive': strategy_adaptive,
}

# D-49 — frozenset snapshot 5 wbudowanych strategii Phase 1. Używana do detekcji
# kolizji w loaderze custom strategii (Phase 3) ZANIM dojdzie do runtime'owej
# rejestracji oraz do dispatch namespace w `do_strategies`/`do_strategy` (D-50).
# NIE używamy `STRATEGIES.keys()` bo po custom load zawierałby też custom,
# co psułoby collision-check (custom-vs-custom = reload per D-38, NIE error).
BUILTIN_STRATEGIES = frozenset(STRATEGIES.keys())
