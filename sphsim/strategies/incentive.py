# Strategia incentive: COMMIT gdy E[zysk_netto] > 0 (zgodna motywacyjnie).
# Verbatim z sph_sim.py:141–153 (v1.0); DEFAULT_K0 ładowane z sphsim.config (D-04, D-13).
from sphsim.config import DEFAULT_K0


def strategy_incentive(dev, l, s, phi, kappa, rho, h, p):
    if dev.status != 'UP':
        return 'ABSTAIN'
    idx = dev.phase - 1
    if idx >= len(phi) or phi[idx] >= 1.0:
        return 'ABSTAIN'
    total_h = sum(h(j + 1) * (l[j] if j < len(l) else 0) for j in range(len(l)))
    if total_h <= 0:
        total_h = 1.0
    exp_P = float(p.get('expected_P', DEFAULT_K0))
    exp_pay = (h(dev.phase) / total_h) * exp_P
    net = (1 - phi[idx]) * exp_pay - kappa - phi[idx] * rho[idx]
    return 'COMMIT' if net > 0 else 'ABSTAIN'


STRATEGY_META = {
    'description': 'COMMIT gdy E[zysk_netto] > 0',
    'params': [
        ('expected_P', float, 100.0, 'Oczek. płatność'),
    ],
    'baseline_kpi': None,
}
