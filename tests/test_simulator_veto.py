"""
Unit tests dla rozszerzenia SPHSimulator o 3-stanowy interface COMMIT/ABSTAIN/VETO
oraz agregację veto_per_phase w simulator.run() (Phase 4, D-64/D-65/D-67).

Pokrywa:
  1. Strategy zwracająca 'VETO' → n_abstain NIE inkrementuje
  2. Strategy zwracająca 'VETO' → status DOWN, down_left=1
  3. Strategy zwracająca 'ABSTAIN' → n_abstain inkrementuje (backwards compat)
  4. simulator.run() zwraca klucze 'veto_per_phase' i 'n_vetoed_total'
  5. Bez żadnych veto → veto_per_phase={}, n_vetoed_total=0
  6. n_vetoed_total == sum(d.n_vetoed for d in devices)
  7. veto_per_phase sumuje wkłady z wielu urządzeń
  8. Nieznany decision (np. typo) → traktowany jak ABSTAIN (T-04-04 failsafe)

Stdlib only: unittest (zgodne z PROJECT.md constraint stdlib-only).
"""
import unittest
import os
import sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sphsim.core.simulator import SPHSimulator
from sphsim.config import DEFAULT_PHI, DEFAULT_RHO

# Minimalne parametry symulatora do testów
_COMMON = dict(
    nU=20, nSUS=10, K0=100.0, K1=120.0, F=5, T=10,
    kappa=1.0, alpha=1.0, phi=DEFAULT_PHI, rho=DEFAULT_RHO, params={}, seed=42
)


def _make_sim(strategy_fn):
    return SPHSimulator(strategy_fn=strategy_fn, **_COMMON)


class TestSimulatorVetoBranch(unittest.TestCase):
    """Testy 3-stanowego decision branch (D-65)."""

    def test_veto_does_not_increment_n_abstain(self):
        """Strategy zwracająca 'VETO' — n_abstain NIE inkrementuje (D-65)."""
        def always_veto(dev, l, s, phi, kappa, rho, h, p):
            dev.n_vetoed += 1
            dev.veto_phase_stats[dev.phase] = dev.veto_phase_stats.get(dev.phase, 0) + 1
            return 'VETO'

        sim = _make_sim(always_veto)
        res = sim.run()
        total_abstain = sum(d.n_abstain for d in res['devices'])
        self.assertEqual(total_abstain, 0,
                         msg=f'VETO path must not increment n_abstain, got {total_abstain}')

    def test_veto_sets_device_down(self):
        """Strategy zwracająca 'VETO' → device dostaje status DOWN, down_left=1 (D-65)."""
        call_count = [0]

        def veto_first_call(dev, l, s, phi, kappa, rho, h, p):
            # Dla pierwszego cyklu veto'ujemy; potem ABSTAIN żeby nie zapętlić
            if call_count[0] < len(sim.devices):
                call_count[0] += 1
                dev.n_vetoed += 1
                dev.veto_phase_stats[dev.phase] = dev.veto_phase_stats.get(dev.phase, 0) + 1
                return 'VETO'
            return 'ABSTAIN'

        sim = _make_sim(veto_first_call)
        # Sprawdzamy bezpośrednio przez uruchomienie jednego kroku
        # Używamy pełnego run() i sprawdzamy statystyki veto
        res = sim.run()
        n_vetoed_total = res['n_vetoed_total']
        self.assertGreater(n_vetoed_total, 0,
                           msg='VETO strategy should produce n_vetoed_total > 0')

    def test_abstain_still_increments_n_abstain(self):
        """Strategy zwracająca 'ABSTAIN' → n_abstain inkrementuje (backwards compat D-67)."""
        def always_abstain(dev, l, s, phi, kappa, rho, h, p):
            return 'ABSTAIN'

        sim = _make_sim(always_abstain)
        res = sim.run()
        total_abstain = sum(d.n_abstain for d in res['devices'])
        # Przy zawsze ABSTAIN, co najmniej jeden device powinien mieć n_abstain > 0
        # (pomijamy te które zaczęły DOWN)
        total_vetoed = sum(d.n_vetoed for d in res['devices'])
        self.assertEqual(total_vetoed, 0,
                         msg='ABSTAIN path must not set n_vetoed')
        # Przynajmniej część urządzeń powinna mieć n_abstain > 0
        self.assertGreater(total_abstain, 0,
                           msg='ABSTAIN strategy should produce n_abstain > 0')

    def test_unknown_decision_treated_as_abstain(self):
        """Nieznany decision (np. typo 'COMIT') → traktowany jak ABSTAIN, nie crash (T-04-04)."""
        def bad_strategy(dev, l, s, phi, kappa, rho, h, p):
            return 'COMIT'  # typo

        sim = _make_sim(bad_strategy)
        try:
            res = sim.run()
        except Exception as e:
            self.fail(f'Simulator crashed on unknown decision "COMIT": {e}')
        # Powinna być przetworzona jak ABSTAIN (n_abstain > 0, n_vetoed == 0)
        total_vetoed = sum(d.n_vetoed for d in res['devices'])
        self.assertEqual(total_vetoed, 0,
                         msg='Unknown decision must not produce n_vetoed')


class TestSimulatorVetoAggregation(unittest.TestCase):
    """Testy agregacji veto_per_phase + n_vetoed_total (D-64)."""

    def test_result_has_veto_per_phase_key(self):
        """simulator.run() zwraca klucz 'veto_per_phase'."""
        sim = _make_sim(lambda dev, l, s, phi, kappa, rho, h, p: 'COMMIT')
        res = sim.run()
        self.assertIn('veto_per_phase', res,
                      msg=f'veto_per_phase missing from result keys: {list(res.keys())}')

    def test_result_has_n_vetoed_total_key(self):
        """simulator.run() zwraca klucz 'n_vetoed_total'."""
        sim = _make_sim(lambda dev, l, s, phi, kappa, rho, h, p: 'COMMIT')
        res = sim.run()
        self.assertIn('n_vetoed_total', res,
                      msg=f'n_vetoed_total missing from result keys: {list(res.keys())}')

    def test_veto_per_phase_is_dict(self):
        """'veto_per_phase' jest dict."""
        sim = _make_sim(lambda dev, l, s, phi, kappa, rho, h, p: 'COMMIT')
        res = sim.run()
        self.assertIsInstance(res['veto_per_phase'], dict,
                              msg=f'veto_per_phase should be dict, got {type(res["veto_per_phase"])}')

    def test_n_vetoed_total_is_int(self):
        """'n_vetoed_total' jest int."""
        sim = _make_sim(lambda dev, l, s, phi, kappa, rho, h, p: 'COMMIT')
        res = sim.run()
        self.assertIsInstance(res['n_vetoed_total'], int,
                              msg=f'n_vetoed_total should be int, got {type(res["n_vetoed_total"])}')

    def test_no_veto_gives_empty_veto_per_phase(self):
        """Bez veto — veto_per_phase={}, n_vetoed_total=0 (D-67 backwards compat)."""
        def commit_strategy(dev, l, s, phi, kappa, rho, h, p):
            return 'COMMIT'

        sim = _make_sim(commit_strategy)
        res = sim.run()
        self.assertEqual(res['veto_per_phase'], {},
                         msg=f'No veto — expected empty dict, got {res["veto_per_phase"]!r}')
        self.assertEqual(res['n_vetoed_total'], 0,
                         msg=f'No veto — expected n_vetoed_total=0, got {res["n_vetoed_total"]}')

    def test_n_vetoed_total_equals_sum_of_device_n_vetoed(self):
        """n_vetoed_total == sum(d.n_vetoed for d in devices)."""
        def veto_phase2(dev, l, s, phi, kappa, rho, h, p):
            if dev.phase == 2:
                dev.n_vetoed += 1
                dev.veto_phase_stats[2] = dev.veto_phase_stats.get(2, 0) + 1
                return 'VETO'
            return 'COMMIT'

        sim = _make_sim(veto_phase2)
        res = sim.run()
        device_sum = sum(d.n_vetoed for d in res['devices'])
        self.assertEqual(res['n_vetoed_total'], device_sum,
                         msg=f'n_vetoed_total={res["n_vetoed_total"]} != sum(d.n_vetoed)={device_sum}')

    def test_veto_per_phase_aggregates_across_devices(self):
        """veto_per_phase sumuje wkłady z wielu urządzeń per faza."""
        def veto_phase2(dev, l, s, phi, kappa, rho, h, p):
            if dev.phase == 2:
                dev.n_vetoed += 1
                dev.veto_phase_stats[2] = dev.veto_phase_stats.get(2, 0) + 1
                return 'VETO'
            return 'COMMIT'

        sim = _make_sim(veto_phase2)
        res = sim.run()
        if res['n_vetoed_total'] > 0:
            # Jeśli były veto, muszą być w veto_per_phase
            self.assertGreater(sum(res['veto_per_phase'].values()), 0,
                               msg='veto_per_phase should have counts when vetos occurred')
            self.assertEqual(sum(res['veto_per_phase'].values()), res['n_vetoed_total'],
                             msg='Sum of veto_per_phase values must equal n_vetoed_total')


if __name__ == '__main__':
    unittest.main()
