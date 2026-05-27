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

    def test_phi_default_when_flag_absent(self):
        """ENV-01: brak --phi → args.phi == DEFAULT_PHI (lista domyślna)."""
        from sphsim.cli.args import parse_args
        from sphsim.config import DEFAULT_PHI
        old_argv = sys.argv
        try:
            sys.argv = ['sph_sim.py', '--strategy', 'naive', '--zeta', '0.5']
            args = parse_args()
            self.assertEqual(args.phi, DEFAULT_PHI,
                             msg=f'args.phi powinno być DEFAULT_PHI={DEFAULT_PHI}, got {args.phi}')
        finally:
            sys.argv = old_argv

    def test_phi_parses_valid_list(self):
        """ENV-01: --phi 0.05,0.15,0.25,0.35,0.95 → args.phi == [0.05, 0.15, 0.25, 0.35, 0.95]."""
        from sphsim.cli.args import parse_args
        old_argv = sys.argv
        try:
            sys.argv = ['sph_sim.py', '--strategy', 'naive', '--zeta', '0.5',
                        '--phi', '0.05,0.15,0.25,0.35,0.95']
            args = parse_args()
            self.assertEqual(args.phi, [0.05, 0.15, 0.25, 0.35, 0.95],
                             msg=f'args.phi nieprawidłowe: {args.phi}')
        finally:
            sys.argv = old_argv

    def test_phi_wrong_length_exit_2(self):
        """ENV-01: --phi z 3 wartościami → exit 2 z komunikatem 'dokładnie 5'."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5',
                     '--phi', '0.1,0.2,0.3', '--no-agent', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 2,
                         msg=f'Oczekiwano exit 2 dla błędnej długości, got {r.returncode}. stderr={r.stderr[:300]}')
        combined = r.stderr + r.stdout
        self.assertIn('dokładnie 5', combined,
                      msg=f'Brak "dokładnie 5" w komunikacie błędu: {combined[:400]}')

    def test_phi_out_of_range_exit_2(self):
        """ENV-01: --phi z wartością > 1.0 → exit 2 z komunikatem 'poza zakresem'."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5',
                     '--phi', '0.1,0.2,0.3,0.4,1.5', '--no-agent', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 2,
                         msg=f'Oczekiwano exit 2 dla wartości poza zakresem, got {r.returncode}. stderr={r.stderr[:300]}')
        combined = r.stderr + r.stdout
        self.assertIn('poza zakresem', combined,
                      msg=f'Brak "poza zakresem" w komunikacie błędu: {combined[:400]}')

    def test_rho_negative_exit_2(self):
        """ENV-01: --rho z wartością ujemną → exit 2 z komunikatem 'ujemne'."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5',
                     '--rho', '0.5,0.5,0.7,1.5,-3.0', '--no-agent', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 2,
                         msg=f'Oczekiwano exit 2 dla ujemnego rho, got {r.returncode}. stderr={r.stderr[:300]}')
        combined = r.stderr + r.stdout
        self.assertIn('ujemne', combined,
                      msg=f'Brak "ujemne" w komunikacie błędu: {combined[:400]}')


class TestPhiRhoFlow(unittest.TestCase):
    """Tests przepływu wartości --phi/--rho do SPHSimulator (ENV-01 plumbing). Plan 01, Wave 1."""

    def test_phi_reaches_simulator(self):
        """ENV-01: niestandardowe --phi dociera do SPHSimulator — symulacja kończy się sukcesem."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5',
                     '--phi', '0.05,0.15,0.25,0.35,0.95',
                     '--no-agent', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 0,
                         msg=f'Oczekiwano exit 0, got {r.returncode}. stderr={r.stderr[:300]}')
        result = json.loads(r.stdout)
        avg_val = result['metrics']['avg_val_last100']
        self.assertIsInstance(avg_val, (int, float),
                              msg=f'avg_val_last100 powinno być liczbą, got {type(avg_val)}')

    def test_baseline_unchanged_without_phi(self):
        """ENV-01: brak --phi → domyślne wartości → avg_val_last100 == 92.0 (baseline v1.0)."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.75',
                     '--no-agent', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 0,
                         msg=f'Oczekiwano exit 0, got {r.returncode}. stderr={r.stderr[:300]}')
        result = json.loads(r.stdout)
        avg_val = result['metrics']['avg_val_last100']
        self.assertEqual(avg_val, 92.0,
                         msg=f'Baseline avg_val_last100 powinno być 92.0, got {avg_val}')


class TestValuationDispatch(unittest.TestCase):
    """Tests dispatchu --valuation {window,step,linear} (ENV-02 unit). Plan 02, Wave 2."""

    def test_window_default_K0_K1(self):
        """Preset window (domyślny): u=110 w oknie [100,120] → zwraca K0=100.0."""
        from sphsim.core.model import valuation
        self.assertEqual(valuation(110, 100, 120), 100.0)

    def test_window_outside_range(self):
        """Preset window: u<K0 i u>K1 → zwraca 0.0 (poza oknem)."""
        from sphsim.core.model import valuation
        self.assertEqual(valuation(80, 100, 120), 0.0)
        self.assertEqual(valuation(130, 100, 120), 0.0)

    def test_step_above_threshold(self):
        """Preset step: u=130 >= K0=100 → zwraca K0=100.0 (bez kary za nadpodaż)."""
        from sphsim.core.model import valuation
        self.assertEqual(valuation(130, 100, 120, 'step'), 100.0)

    def test_step_below_threshold(self):
        """Preset step: u=80 < K0=100 → zwraca 0.0."""
        from sphsim.core.model import valuation
        self.assertEqual(valuation(80, 100, 120, 'step'), 0.0)

    def test_linear_ramp(self):
        """Preset linear: u=60, K0=100, K1=120 → K0*min(u,K1)/K1 = 100*60/120 = 50.0."""
        from sphsim.core.model import valuation
        self.assertAlmostEqual(valuation(60, 100, 120, 'linear'), 50.0, places=4)

    def test_linear_inf_K1_fallback(self):
        """Preset linear: K1=inf → fallback do step semantics → K0 gdy u>=K0."""
        from sphsim.core.model import valuation
        self.assertEqual(valuation(150, 100, float('inf'), 'linear'), 100.0)

    def test_sph_stp_threads_preset(self):
        """sph_stp musi przekazać preset do P_of_x: wyniki dla step vs window różnią się (Pitfall 1)."""
        from sphsim.core.model import sph_stp, valuation
        r_step = sph_stp(150, 0, 20, 100, 120, 'step')
        r_window = sph_stp(150, 0, 20, 100, 120, 'window')
        # Jeśli (z*,y*) są identyczne, sprawdzamy czy P_of_x(x) różni się dla obu presetów
        z_step, y_step = r_step
        z_window, y_window = r_window
        x_step = z_step - y_step
        x_window = z_window - y_window
        p_step = valuation(150 - x_step, 100, 120, 'step') + x_step
        p_window = valuation(150 - x_window, 100, 120, 'window') + x_window
        # Preset step (brak górnego ograniczenia) musi dać inny wynik P niż window
        self.assertNotEqual(p_step, p_window,
                            msg='Preset step i window dają ten sam P_of_x — preset nie dociera do P_of_x (Pitfall 1)')


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
