"""
Unit i integration tests dla Phase 6 — PNG side (PLOT-01, PLOT-02).
Klasy: TestPlots, TestPlotDimensions. Wydzielony z test_report.py żeby Plan 02/03 mogły lądować parallel bez konfliktu mergem.
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


class TestPlots(unittest.TestCase):
    """PLOT-01/PLOT-02: oba PNG istnieją w katalogu raportu, mają >0 bajtów, mają walidny PNG header (b'\\x89PNG\\r\\n\\x1a\\n')."""

    def test_placeholder(self):
        self.skipTest("Wave 2 — Plan 03 — plots.py matplotlib Agg + 2 plot functions + close-figure discipline")


class TestPlotDimensions(unittest.TestCase):
    """PLOT-02 detail: kpi_timeseries.png ma dimensions współmierne do figsize=(10,5) dpi=120 (≥1000×500 px). Pillow opcjonalne — fallback to file size >5 KB jako proxy."""

    def test_placeholder(self):
        self.skipTest("Wave 2 — Plan 03 — PNG dim probe via Pillow or size threshold")


if __name__ == '__main__':
    unittest.main()
