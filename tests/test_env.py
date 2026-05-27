"""
Unit i integration tests dla Phase 5 (Configurable environment).
Pokrywa ENV-01 (--phi/--rho), ENV-02 (--valuation/--K0), ENV-03 (config header).
Stdlib only: unittest + subprocess + json + os + sys.
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

PROJECT_ROOT = Path(_PROJECT_ROOT)
MONOLITH = PROJECT_ROOT / 'sph_sim.py'


def _run_sph(*args, **kwargs):
    """Uruchamia sph_sim.py z podanymi argumentami. Zwraca CompletedProcess."""
    return subprocess.run(
        [sys.executable, 'sph_sim.py'] + list(args),
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        **kwargs
    )


class TestPhiRhoParsing(unittest.TestCase):
    """Tests parsowania --phi i --rho (ENV-01 argparse). Plan 01, Wave 1."""

    def test_placeholder(self):
        self.skipTest("Wave 1 implementation — class name locked by Plan 00")


class TestPhiRhoFlow(unittest.TestCase):
    """Tests przepływu wartości --phi/--rho do SPHSimulator (ENV-01 plumbing). Plan 01, Wave 1."""

    def test_placeholder(self):
        self.skipTest("Wave 1 implementation — class name locked by Plan 00")


class TestValuationDispatch(unittest.TestCase):
    """Tests dispatchu --valuation {window,step,linear} (ENV-02 unit). Plan 02, Wave 2."""

    def test_placeholder(self):
        self.skipTest("Wave 2 implementation — class name locked by Plan 00")


class TestValuationPresets(unittest.TestCase):
    """Tests integracyjne --valuation + --K0/--K1 override (ENV-02 integration). Plan 02, Wave 2."""

    def test_placeholder(self):
        self.skipTest("Wave 2 implementation — class name locked by Plan 00")


class TestPresetDistinguishability(unittest.TestCase):
    """Tests rozróżnialności KPI dla 3 presetów (ENV-02 SC-3). Plan 02, Wave 2."""

    def test_placeholder(self):
        self.skipTest("Wave 2 implementation — class name locked by Plan 00")


class TestConfigHeader(unittest.TestCase):
    """Tests format_config_header zwracającego 9-klucz tabelę MD (ENV-03 unit). Plan 03, Wave 3."""

    def test_placeholder(self):
        self.skipTest("Wave 3 implementation — class name locked by Plan 00")


class TestHumanHeader(unittest.TestCase):
    """Tests że format_human zaczyna się od config header (ENV-03 integration). Plan 03, Wave 3."""

    def test_placeholder(self):
        self.skipTest("Wave 3 implementation — class name locked by Plan 00")


if __name__ == '__main__':
    unittest.main()
