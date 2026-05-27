"""
Unit tests dla sphsim.agent.rational (Phase 4, Task 2 TDD, D-53/D-55/D-57/D-63/D-65).

Pokrywa 10 przypadków:
  1.  ABSTAIN passthrough — wrapper nie inkrementuje n_vetoed
  2.  COMMIT + E[zysk] > 0 → wrapper zwraca 'COMMIT', n_vetoed bez zmian
  3.  COMMIT + E[zysk] < 0 → wrapper zwraca 'VETO', n_vetoed += 1, veto_phase_stats inkrementuje
  4.  phi[idx] >= 1.0 → VETO (guard D-57), n_vetoed += 1
  5.  idx >= len(phi) → VETO (guard D-57)
  6.  total_h <= 0 fallback (wszystkie l=0) → brak crashu, zwraca COMMIT lub VETO
  7.  incentive + wrapper = idempotent (D-56): n_vetoed == 0 dla matching expected_P
  8.  sygnatura wrapped: 8 argumentów (dev, l, s, phi, kappa, rho, h, p)
  9.  expected_P=None → fallback DEFAULT_K0
 10.  n_abstain NIE inkrementuje przy VETO (osobny licznik)

Stdlib only: unittest + inspect.
"""

import inspect
import os
import sys
import unittest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sphsim.agent.rational import wrap_with_agent
from sphsim.core.device import Device
from sphsim.config import DEFAULT_K0


def _make_device(phase=1, status='UP'):
    """Helper: tworzy Device z domyślnymi parametrami."""
    return Device(id=0, phase=phase, status=status)


def _stub_abstain(dev, l, s, phi, kappa, rho, h, p):
    return 'ABSTAIN'


def _stub_commit(dev, l, s, phi, kappa, rho, h, p):
    return 'COMMIT'


class TestWrapWithAgentPassthrough(unittest.TestCase):
    """Test 1: ABSTAIN passthrough — wrapper nie weto'uje ani nie liczy E[zysk]."""

    def test_abstain_passthrough_returns_abstain(self):
        """Gdy strategia zwraca ABSTAIN, wrapper musi zwrócić 'ABSTAIN'."""
        w = wrap_with_agent(_stub_abstain, 100.0)
        dev = _make_device(phase=2, status='UP')
        out = w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1, 0.1], 1.0,
                [5, 5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(out, 'ABSTAIN', msg=f"expected ABSTAIN, got {out!r}")

    def test_abstain_passthrough_no_veto_increment(self):
        """Przy ABSTAIN passthrough dev.n_vetoed NIE inkrementuje."""
        w = wrap_with_agent(_stub_abstain, 100.0)
        dev = _make_device(phase=2, status='UP')
        w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1, 0.1], 1.0,
          [5, 5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(
            dev.n_vetoed, 0,
            msg=f"n_vetoed powinno pozostać 0 przy ABSTAIN passthrough, got {dev.n_vetoed}",
        )


class TestWrapWithAgentCommitPositive(unittest.TestCase):
    """Test 2: COMMIT + E[zysk] > 0 → wrapper passthrough COMMIT."""

    def test_positive_net_returns_commit(self):
        """Gdy net > 0, wrapper zwraca 'COMMIT'."""
        w = wrap_with_agent(_stub_commit, 1000.0)  # duże expected_P → net > 0
        dev = _make_device(phase=1, status='UP')
        out = w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1], 1.0,
                [5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(out, 'COMMIT', msg=f"expected COMMIT (high expected_P), got {out!r}")

    def test_positive_net_no_veto_increment(self):
        """Przy net > 0, dev.n_vetoed NIE inkrementuje."""
        w = wrap_with_agent(_stub_commit, 1000.0)
        dev = _make_device(phase=1, status='UP')
        w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1], 1.0,
          [5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(dev.n_vetoed, 0, msg=f"n_vetoed={dev.n_vetoed}, expected 0")


class TestWrapWithAgentCommitNegative(unittest.TestCase):
    """Test 3: COMMIT + E[zysk] < 0 → wrapper zwraca 'VETO', mutuje liczniki."""

    def test_negative_net_returns_veto(self):
        """Gdy net < 0, wrapper zwraca 'VETO'."""
        w = wrap_with_agent(_stub_commit, 0.01)  # mikroskopijne expected_P → net < 0 (kappa=1.0)
        dev = _make_device(phase=1, status='UP')
        out = w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1], 1.0,
                [5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(out, 'VETO', msg=f"expected VETO (tiny expected_P), got {out!r}")

    def test_negative_net_increments_n_vetoed(self):
        """Gdy net < 0, dev.n_vetoed wzrasta o 1."""
        w = wrap_with_agent(_stub_commit, 0.01)
        dev = _make_device(phase=1, status='UP')
        w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1], 1.0,
          [5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(dev.n_vetoed, 1, msg=f"n_vetoed={dev.n_vetoed}, expected 1")

    def test_negative_net_updates_veto_phase_stats(self):
        """Gdy net < 0, dev.veto_phase_stats[dev.phase] wzrasta o 1."""
        w = wrap_with_agent(_stub_commit, 0.01)
        dev = _make_device(phase=1, status='UP')
        w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1], 1.0,
          [5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(
            dev.veto_phase_stats, {1: 1},
            msg=f"veto_phase_stats={dev.veto_phase_stats!r}, expected {{1: 1}}",
        )

    def test_multiple_veto_accumulates(self):
        """Wielokrotne VETO kumuluje n_vetoed i veto_phase_stats."""
        w = wrap_with_agent(_stub_commit, 0.01)
        dev = _make_device(phase=2, status='UP')
        w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1], 1.0,
          [5, 5, 5, 5], lambda i: i, {})
        w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1], 1.0,
          [5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(dev.n_vetoed, 2, msg=f"n_vetoed={dev.n_vetoed}, expected 2")
        self.assertEqual(dev.veto_phase_stats.get(2, 0), 2, msg=f"veto_phase_stats={dev.veto_phase_stats!r}")


class TestWrapWithAgentPhiGuard(unittest.TestCase):
    """Test 4: phi[idx] >= 1.0 → VETO (guard D-57)."""

    def test_phi_one_returns_veto(self):
        """Gdy phi[dev.phase-1] >= 1.0, wrapper zwraca 'VETO' bez obliczania E[zysk]."""
        w = wrap_with_agent(_stub_commit, 0.01)
        dev = _make_device(phase=2, status='UP')
        out = w(dev, [10, 10, 10, 10], 10, [0.1, 1.0, 0.1, 0.1], 1.0,
                [5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(out, 'VETO', msg=f"expected VETO (phi=1.0), got {out!r}")

    def test_phi_one_increments_n_vetoed(self):
        """Gdy phi[idx] >= 1.0, dev.n_vetoed inkrementuje."""
        w = wrap_with_agent(_stub_commit, 0.01)
        dev = _make_device(phase=2, status='UP')
        w(dev, [10, 10, 10, 10], 10, [0.1, 1.0, 0.1, 0.1], 1.0,
          [5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(dev.n_vetoed, 1, msg=f"n_vetoed={dev.n_vetoed}, expected 1")

    def test_phi_above_one_returns_veto(self):
        """Gdy phi[idx] > 1.0, wrapper zwraca 'VETO'."""
        w = wrap_with_agent(_stub_commit, 100.0)
        dev = _make_device(phase=1, status='UP')
        out = w(dev, [10, 10, 10, 10], 10, [1.5, 0.1, 0.1, 0.1], 1.0,
                [5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(out, 'VETO', msg=f"expected VETO (phi=1.5), got {out!r}")


class TestWrapWithAgentIdxGuard(unittest.TestCase):
    """Test 5: idx >= len(phi) → VETO (guard D-57)."""

    def test_phase_beyond_phi_returns_veto(self):
        """Gdy dev.phase - 1 >= len(phi), wrapper zwraca 'VETO'."""
        w = wrap_with_agent(_stub_commit, 0.01)
        dev = _make_device(phase=10, status='UP')  # idx=9, len(phi)=4
        out = w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1], 1.0,
                [5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(out, 'VETO', msg=f"expected VETO (idx out of range), got {out!r}")

    def test_phase_beyond_phi_increments_n_vetoed(self):
        """Gdy idx >= len(phi), dev.n_vetoed inkrementuje."""
        w = wrap_with_agent(_stub_commit, 0.01)
        dev = _make_device(phase=10, status='UP')
        w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1], 1.0,
          [5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(dev.n_vetoed, 1, msg=f"n_vetoed={dev.n_vetoed}, expected 1")


class TestWrapWithAgentTotalHFallback(unittest.TestCase):
    """Test 6: total_h <= 0 fallback (D-55) — brak crashu gdy wszystkie l=0."""

    def test_all_l_zero_no_crash(self):
        """Gdy wszystkie l[j]=0 (total_h=0), wrapper stosuje fallback=1.0 i nie crashuje."""
        w = wrap_with_agent(_stub_commit, 0.01)  # tiny expected_P
        dev = _make_device(phase=1, status='UP')
        try:
            out = w(dev, [0, 0, 0, 0], 0, [0.1, 0.1, 0.1, 0.1], 1.0,
                    [5, 5, 5, 5], lambda i: i, {})
        except ZeroDivisionError:
            self.fail("ZeroDivisionError — brakuje fallback total_h=1.0 (D-55)")
        self.assertIn(
            out, ('COMMIT', 'VETO'),
            msg=f"unexpected return value: {out!r}",
        )

    def test_all_l_zero_big_expected_p_may_commit(self):
        """Gdy total_h=0 fallback=1.0 i duże expected_P, może zwrócić COMMIT (nie jest crash)."""
        w = wrap_with_agent(_stub_commit, 10000.0)  # bardzo duże expected_P
        dev = _make_device(phase=1, status='UP')
        out = w(dev, [0, 0, 0, 0], 0, [0.1, 0.1, 0.1, 0.1], 0.01,
                [0.01, 0.01, 0.01, 0.01], lambda i: i, {})
        # Z tak dużym expected_P i małym kappa/rho, net > 0 → COMMIT
        self.assertEqual(out, 'COMMIT', msg=f"expected COMMIT (high expected_P + fallback), got {out!r}")


class TestWrapWithAgentIdempotency(unittest.TestCase):
    """Test 7: strategy_incentive + wrapper = idempotent (D-56)."""

    def test_incentive_wrapper_idempotent_no_veto(self):
        """Wrapper z strategy_incentive i identycznym expected_P → n_vetoed == 0."""
        from sphsim.strategies.incentive import strategy_incentive
        w = wrap_with_agent(strategy_incentive, 100.0)
        dev = _make_device(phase=1, status='UP')
        out = w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1, 0.1], 1.0,
                [5, 5, 5, 5, 5], lambda i: i, {'expected_P': 100.0})
        self.assertEqual(
            dev.n_vetoed, 0,
            msg=f"incentive+wrapper powinno być idempotent (D-56), got n_vetoed={dev.n_vetoed}",
        )

    def test_incentive_wrapper_abstain_when_net_zero(self):
        """Gdy incentive zwraca ABSTAIN (net<=0), wrapper passthrough → n_vetoed=0."""
        from sphsim.strategies.incentive import strategy_incentive
        # expected_P=0.001 → incentive zwraca ABSTAIN (net<0 → brak COMMIT)
        w = wrap_with_agent(strategy_incentive, 0.001)
        dev = _make_device(phase=1, status='UP')
        out = w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1, 0.1], 100.0,
                [5, 5, 5, 5, 5], lambda i: i, {'expected_P': 0.001})
        # incentive zwróci ABSTAIN (net<0) → wrapper passthrough → ABSTAIN
        self.assertEqual(out, 'ABSTAIN', msg=f"expected ABSTAIN passthrough, got {out!r}")
        self.assertEqual(dev.n_vetoed, 0, msg=f"n_vetoed powinno być 0, got {dev.n_vetoed}")


class TestWrapWithAgentSignature(unittest.TestCase):
    """Test 8: sygnatura wrapped: 8 nazwanych parametrów (kontrakt EXPECTED_PARAMS)."""

    def test_wrapped_has_8_params(self):
        """Closure zwrócone przez wrap_with_agent ma dokładnie 8 parametrów."""
        w = wrap_with_agent(_stub_commit, 100.0)
        sig = inspect.signature(w)
        params = list(sig.parameters.keys())
        self.assertEqual(
            len(params), 8,
            msg=f"wrapped ma {len(params)} param(s), expected 8: {params}",
        )

    def test_wrapped_params_names_match_expected(self):
        """Closure ma sygnaturę (dev, l, s, phi, kappa, rho, h, p) — kontrakt loader.py:31."""
        w = wrap_with_agent(_stub_commit, 100.0)
        sig = inspect.signature(w)
        params = list(sig.parameters.keys())
        expected = ['dev', 'l', 's', 'phi', 'kappa', 'rho', 'h', 'p']
        self.assertEqual(
            params, expected,
            msg=f"sygnatura: {params}, expected: {expected}",
        )


class TestWrapWithAgentDefaultExpectedP(unittest.TestCase):
    """Test 9: expected_P=None → fallback DEFAULT_K0."""

    def test_none_expected_p_uses_default(self):
        """Gdy expected_P=None, wrapper używa DEFAULT_K0 (nie crashuje)."""
        w = wrap_with_agent(_stub_commit, None)
        dev = _make_device(phase=1, status='UP')
        try:
            out = w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1], 1.0,
                    [5, 5, 5, 5], lambda i: i, {})
        except Exception as e:
            self.fail(f"Unexpected exception z expected_P=None: {e}")
        self.assertIn(out, ('COMMIT', 'VETO'), msg=f"unexpected return: {out!r}")

    def test_none_expected_p_same_as_default_k0(self):
        """Wrapper z expected_P=None i expected_P=DEFAULT_K0 dają identyczny wynik."""
        w_none = wrap_with_agent(_stub_commit, None)
        w_default = wrap_with_agent(_stub_commit, DEFAULT_K0)
        dev_none = _make_device(phase=1, status='UP')
        dev_default = _make_device(phase=1, status='UP')
        l = [10, 10, 10, 10]
        phi = [0.1, 0.1, 0.1, 0.1]
        rho = [5, 5, 5, 5]
        out_none = w_none(dev_none, l, 10, phi, 1.0, rho, lambda i: i, {})
        out_default = w_default(dev_default, l, 10, phi, 1.0, rho, lambda i: i, {})
        self.assertEqual(
            out_none, out_default,
            msg=f"expected_P=None daje {out_none!r}, DEFAULT_K0 daje {out_default!r}",
        )


class TestWrapWithAgentNAbstainNotIncremented(unittest.TestCase):
    """Test 10: n_abstain NIE inkrementuje przy VETO (D-65 — osobny licznik)."""

    def test_veto_does_not_increment_n_abstain(self):
        """Przy VETO, dev.n_abstain pozostaje 0 (wrapper tylko mutuje n_vetoed)."""
        w = wrap_with_agent(_stub_commit, 0.01)
        dev = _make_device(phase=1, status='UP')
        out = w(dev, [10, 10, 10, 10], 10, [0.1, 0.1, 0.1, 0.1], 1.0,
                [5, 5, 5, 5], lambda i: i, {})
        self.assertEqual(out, 'VETO', msg=f"expected VETO, got {out!r}")
        self.assertEqual(
            dev.n_abstain, 0,
            msg=f"n_abstain powinno pozostać 0 przy VETO, got {dev.n_abstain}",
        )
        self.assertEqual(
            dev.n_vetoed, 1,
            msg=f"n_vetoed powinno być 1, got {dev.n_vetoed}",
        )


if __name__ == '__main__':
    unittest.main()
