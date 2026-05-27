# Funkcje modelu — pure (bez side effects, bez random.*).
# Skopiowane VERBATIM z sph_sim.py:53–79 (v1.0). Zachowane sygnatury, ciała,
# kolejność candidates list w sph_stp (tie-breaking w `if p > best_P`).
from typing import Tuple


def valuation(u, K0, K1, preset='window'):
    """Funkcja waluacji Konsumentów g(u; K0, K1, preset). preset: 'window' (def, v1.0) | 'step' | 'linear'."""
    if preset == 'step':
        return float(K0) if u >= K0 else 0.0
    if preset == 'linear':
        if K1 == float('inf') or K1 <= 0:
            return float(K0) if u >= K0 else 0.0
        return float(K0) * min(float(u), float(K1)) / float(K1)
    # domyślnie: window (v1.0 compatible)
    if K1 == float('inf'):
        return float(K0) if u >= K0 else 0.0
    return float(K0) if K0 <= u <= K1 else 0.0


def sph_stp(u, s, nSUS, K0, K1, preset='window'):
    """Zwraca (z*, y*) max-izujące P = g(u-x)+x, x=z-y. Przekazuje preset do wewnętrznej P_of_x."""
    def P_of_x(x):
        return valuation(u - x, K0, K1, preset) + x

    x_min = -s
    x_max = min(u, nSUS - s)
    if x_min > x_max:
        return 0, 0

    best_x, best_P = x_min, P_of_x(x_min)
    candidates = [x_min, x_max, K0 - u]
    if K1 != float('inf'):
        candidates.append(K1 - u)
    for xc in candidates:
        for x in [int(xc) - 1, int(xc), int(xc) + 1]:
            if x_min <= x <= x_max:
                p = P_of_x(x)
                if p > best_P:
                    best_P, best_x = p, x

    return (best_x, 0) if best_x >= 0 else (0, -best_x)
