# Strategia threshold: COMMIT tylko jeśli dev.phase <= max_phase.
# Verbatim z sph_sim.py:128–131 (v1.0).


def strategy_threshold(dev, l, s, phi, kappa, rho, h, p):
    if dev.status != 'UP':
        return 'ABSTAIN'
    return 'COMMIT' if dev.phase <= int(p.get('max_phase', 3)) else 'ABSTAIN'


STRATEGY_META = {
    'description': 'COMMIT tylko dla faz <= max_phase',
    'params': [
        ('max_phase', int, 3, 'Max faza COMMIT'),
    ],
    'baseline_kpi': None,
}
