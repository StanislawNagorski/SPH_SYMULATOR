# Strategia adaptive: prawdopodobieństwo COMMIT zależne od poziomu bufora SUS.
# Verbatim z sph_sim.py:155–168 (v1.0).
import random


def strategy_adaptive(dev, l, s, phi, kappa, rho, h, p):
    if dev.status != 'UP':
        return 'ABSTAIN'
    idx = dev.phase - 1
    if idx >= len(phi) or phi[idx] >= 1.0:
        return 'ABSTAIN'
    tgt = int(p.get('s_target', 10))
    if s < tgt:
        prob = 0.9
    elif s < tgt * 2:
        prob = 0.5
    else:
        prob = 0.2
    return 'COMMIT' if random.random() < prob else 'ABSTAIN'
