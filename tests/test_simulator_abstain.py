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


class TestSimulatorAbstain(unittest.TestCase):
    """PLOT-01 data gap: Device.abstain_phase_stats per-phase counter + simulator.run() aggregation do result['abstain_per_phase']. Mirror Phase 4 D-64."""

    def test_placeholder(self):
        self.skipTest("Wave 1 — Plan 01 — device.py + simulator.py inkrementacja + agregacja")


if __name__ == '__main__':
    unittest.main()
