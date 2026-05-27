# RationalAgent — wrapper veto-ujący COMMIT przy E[zysk] < 0.
# Formuła i parametr expected_P identyczne z sphsim/strategies/incentive.py (D-53/D-54).
# Decyzja VETO: net = (1-phi_i)*p_i - kappa - phi_i*rho_i < 0 (AGENT-02).
# Guards: phi[idx]>=1.0 lub idx>=len(phi) → VETO (D-57); total_h<=0 → fallback 1.0 (D-55).
from sphsim.config import DEFAULT_K0


def wrap_with_agent(strategy_fn, expected_P=None):
    """Opakowuje strategy_fn w RationalAgent veto layer.

    Wrapper liczy E[zysk] = (1-phi_i)*p_i - kappa - phi_i*rho_i (verbatim z incentive.py:6-18).
    Gdy strategia zwraca COMMIT a E[zysk] < 0, wrapper override'uje na 'VETO'
    (simulator interpretuje VETO jak ABSTAIN ale z osobnym licznikiem n_vetoed).
    Passthrough: ABSTAIN i każda inna wartość poza COMMIT nie jest przeliczana (D-56).

    Args:
        strategy_fn: callable z 8-arg sygnaturą (dev, l, s, phi, kappa, rho, h, p).
        expected_P:  oczekiwana płatność (float); gdy None, używa DEFAULT_K0=100.

    Returns:
        Closure 'wrapped' z tą samą 8-arg sygnaturą co strategy_fn (kontrakt EXPECTED_PARAMS).
    """
    if expected_P is None:
        expected_P = DEFAULT_K0

    def wrapped(dev, l, s, phi, kappa, rho, h, p):
        # Strategia decyduje first.
        decision = strategy_fn(dev, l, s, phi, kappa, rho, h, p)
        if decision != 'COMMIT':
            return decision  # ABSTAIN passthrough — NIE liczy E[zysk] (D-56 idempotency).

        # Guard D-57: faza poza zakresem phi lub phi=1.0 → deterministyczne VETO.
        idx = dev.phase - 1
        if idx >= len(phi) or phi[idx] >= 1.0:
            dev.n_vetoed += 1
            dev.veto_phase_stats[dev.phase] = dev.veto_phase_stats.get(dev.phase, 0) + 1
            return 'VETO'

        # Compute total_h (verbatim z incentive.py:12-14); D-55 fallback.
        total_h = sum(h(j + 1) * (l[j] if j < len(l) else 0) for j in range(len(l)))
        if total_h <= 0:
            total_h = 1.0  # D-55: brak danych historycznych → allow COMMIT

        # Compute E[zysk] (verbatim z incentive.py:16-17, D-53).
        exp_pay = (h(dev.phase) / total_h) * expected_P
        net = (1 - phi[idx]) * exp_pay - kappa - phi[idx] * rho[idx]

        # AGENT-02: override COMMIT → VETO gdy net < 0 (literalnie "< 0", nie "<= 0").
        if net < 0:
            dev.n_vetoed += 1
            dev.veto_phase_stats[dev.phase] = dev.veto_phase_stats.get(dev.phase, 0) + 1
            return 'VETO'

        return 'COMMIT'

    return wrapped
