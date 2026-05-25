# Strategia naive: COMMIT z prawdopodobieństwem zeta.
# Verbatim z sph_sim.py:123–126 (v1.0).
import random


def strategy_naive(dev, l, s, phi, kappa, rho, h, p):
    if dev.status != 'UP':
        return 'ABSTAIN'
    return 'COMMIT' if random.random() < float(p.get('zeta', 0.5)) else 'ABSTAIN'
