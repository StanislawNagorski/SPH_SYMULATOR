"""
Unit tests dla Phase 6 data gap fix (PLOT-01 input): abstain_per_phase aggregation.
Mirror Phase 4 D-64 veto_phase_stats pattern. Klasa: TestSimulatorAbstain.
Stdlib only: unittest + subprocess + json + os + sys + tempfile + pathlib.
"""
import json, os, subprocess, sys, unittest
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sphsim.core.simulator import SPHSimulator
from sphsim.config import (
    DEFAULT_NU, DEFAULT_NSUS, DEFAULT_K0, DEFAULT_K1, DEFAULT_F,
    DEFAULT_T, DEFAULT_KAPPA, DEFAULT_ALPHA, DEFAULT_PHI, DEFAULT_RHO,
)

PROJECT_ROOT = Path(_PROJECT_ROOT)
MONOLITH = PROJECT_ROOT / 'sph_sim.py'
_REPORTS_DIR = PROJECT_ROOT / 'reports'


def _run_sph(*args, **kwargs):
    """Subprocess helper — uruchamia sph_sim.py z cwd=_PROJECT_ROOT (mirror tests/test_env.py)."""
    env = {**os.environ, 'SPHSIM_NO_REPORT': kwargs.pop('SPHSIM_NO_REPORT', '1')}
    return subprocess.run(
        [sys.executable, 'sph_sim.py', *args],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        **kwargs,
    )


def _stub_always_abstain(dev, l, s, phi, kappa, rho, h, p):
    """Stub strategy — zawsze zwraca ABSTAIN niezależnie od fazy."""
    return 'ABSTAIN'


def _stub_always_veto(dev, l, s, phi, kappa, rho, h, p):
    """Stub strategy — zawsze zwraca VETO (D-65 disjointness check)."""
    return 'VETO'


class TestSimulatorAbstain(unittest.TestCase):
    """PLOT-01 data gap: Device.abstain_phase_stats per-phase counter + simulator.run() aggregation do result['abstain_per_phase']. Mirror Phase 4 D-64."""

    def _build_sim(self, strategy_fn, T=50, seed=42):
        """Helper — builds SPHSimulator z DEFAULT_* env + given strategy."""
        return SPHSimulator(
            nU=DEFAULT_NU, nSUS=DEFAULT_NSUS,
            K0=DEFAULT_K0, K1=DEFAULT_K1, F=DEFAULT_F,
            T=T, kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA,
            phi=DEFAULT_PHI, rho=DEFAULT_RHO,
            strategy_fn=strategy_fn, params={}, seed=seed,
        )

    def test_abstain_per_phase_key_exists_in_result(self):
        """SC: result dict zawiera klucz 'abstain_per_phase' (REPORT-01 input)."""
        sim = self._build_sim(_stub_always_abstain, T=20)
        res = sim.run()
        self.assertIn('abstain_per_phase', res,
                      msg=f"klucz 'abstain_per_phase' brak w result; klucze={sorted(res.keys())}")
        self.assertIsInstance(res['abstain_per_phase'], dict,
                              msg=f"typ błędny: {type(res['abstain_per_phase'])}")

    def test_abstain_per_phase_aggregates_across_devices(self):
        """SC: po T cyklach ze strategy=ABSTAIN, suma counts ≥ liczba ABSTAIN-events (RESEARCH §F.13)."""
        sim = self._build_sim(_stub_always_abstain, T=20)
        res = sim.run()
        total_abstains_per_phase = sum(res['abstain_per_phase'].values())
        self.assertGreater(total_abstains_per_phase, 0,
                           msg=f"przy stub_always_abstain oczekiwane >0 ABSTAINs per faza, dostałem {res['abstain_per_phase']}")
        # All keys should be valid phase indices (1..F-1 = 1..4 for default F=5)
        for ph in res['abstain_per_phase']:
            self.assertGreaterEqual(ph, 1, msg=f"faza < 1: {ph}")
            self.assertLessEqual(ph, DEFAULT_F - 1,
                                 msg=f"faza > F-1={DEFAULT_F - 1}: {ph}")

    def test_veto_does_not_increment_abstain(self):
        """SC: D-65 disjointness — VETO branch NIE inkrementuje abstain_per_phase."""
        sim = self._build_sim(_stub_always_veto, T=20)
        res = sim.run()
        # NB: VETO from raw strategy (not from wrap_with_agent) is handled by the
        # 'VETO' branch in simulator.py:70-74, which does NOT increment n_abstain
        # nor abstain_phase_stats. abstain_per_phase should be empty.
        self.assertEqual(res['abstain_per_phase'], {},
                         msg=f"VETO inkrementowane jako ABSTAIN — D-65 złamane! abstain_per_phase={res['abstain_per_phase']}")


if __name__ == '__main__':
    unittest.main()
