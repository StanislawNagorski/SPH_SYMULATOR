# Strategia naive: COMMIT z prawdopodobieństwem zeta.
# Verbatim z sph_sim.py:123–126 (v1.0).
import random


def strategy_naive(dev, l, s, phi, kappa, rho, h, p):
    if dev.status != 'UP':
        return 'ABSTAIN'
    return 'COMMIT' if random.random() < float(p.get('zeta', 0.5)) else 'ABSTAIN'


STRATEGY_META = {
    'description': 'COMMIT z prawdopodobieństwem zeta',
    'params': [
        ('zeta', float, 0.5, 'Frakcja COMMIT (0..1)'),
    ],
    'baseline_kpi': {
        'invocation': 'naive --zeta 0.75',
        'avg_val_last100': 92.0,
        'source': 'PROJECT.md / v1.0 results',
    },
}
