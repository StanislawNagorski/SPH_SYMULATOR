# Strategia phase_prob: COMMIT z prawdopodobieństwem zależnym od fazy (lista probs).
# Verbatim z sph_sim.py:133–139 (v1.0).
import random


def strategy_phase_prob(dev, l, s, phi, kappa, rho, h, p):
    if dev.status != 'UP':
        return 'ABSTAIN'
    probs = [float(x) for x in str(p.get('probs', '0.9,0.7,0.5,0.3,0.0')).split(',')]
    idx = dev.phase - 1
    prob = probs[idx] if idx < len(probs) else 0.0
    return 'COMMIT' if random.random() < prob else 'ABSTAIN'


STRATEGY_META = {
    'description': 'COMMIT z P(commitów) per faza',
    'params': [
        ('probs', str, '0.9,0.7,0.5,0.3,0.0', 'P(COMMIT) per faza, po przecinku'),
    ],
    'baseline_kpi': None,
}
