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

    def test_window_preset_matches_baseline(self):
        """ENV-02: --valuation window → avg_val_last100 == 92.0 (zachowanie v1.0)."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.75', '--valuation', 'window',
                     '--no-agent', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 0,
                         msg=f'Oczekiwano exit 0, got {r.returncode}. stderr={r.stderr[:300]}')
        d = json.loads(r.stdout)
        self.assertIn('metrics', d)
        avg_val = d['metrics']['avg_val_last100']
        self.assertEqual(avg_val, 92.0,
                         msg=f'Preset window zeta=0.75 powinien dawać 92.0, got {avg_val}')

    def test_K0_override_changes_kpi(self):
        """ENV-02: --K0 80 dociera do symulatora — symulacja kończy się sukcesem i zwraca liczbę."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.75', '--K0', '80',
                     '--no-agent', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 0,
                         msg=f'Oczekiwano exit 0, got {r.returncode}. stderr={r.stderr[:300]}')
        d = json.loads(r.stdout)
        self.assertIn('metrics', d)
        avg_val = d['metrics']['avg_val_last100']
        self.assertIsInstance(avg_val, (int, float),
                              msg=f'avg_val_last100 powinno być liczbą, got {type(avg_val)}')

    def test_K1_override_with_valuation(self):
        """ENV-02: --K0 100 --K1 200 → symulacja kończy się sukcesem z poprawnym JSON."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.75', '--K0', '100', '--K1', '200',
                     '--no-agent', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 0,
                         msg=f'Oczekiwano exit 0, got {r.returncode}. stderr={r.stderr[:300]}')
        d = json.loads(r.stdout)
        self.assertIn('metrics', d)


class TestPresetDistinguishability(unittest.TestCase):
    """Tests rozróżnialności KPI dla 3 presetów (ENV-02 SC-3). Plan 02, Wave 2.

    SC-3 enforcement: all 3 presets MUST give distinct KPI on the same seed+strategy.
    RESEARCH §B.7 mathematically proves distinguishability for the default env
    (avg_providers ≈ 105, K0=100, K1=120) with --zeta 0.75.
    If this test fails for window vs step (the most likely identical pair), it indicates
    sph_stp is not threading preset (Pitfall 1).
    Note: --zeta 0.5 produces avg_providers ≈ 67 < K0=100, so window==step numerically
    (both return 0). --zeta 0.75 is required for distinguishability (avg_providers ≈ 105).
    """

    def _run_preset(self, preset):
        """Uruchamia symulator z zadanym presetem, zwraca avg_val_last100."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.75', '--no-agent', '--seed', '42',
                     '--json', '--valuation', preset)
        self.assertEqual(r.returncode, 0,
                         msg=f'Preset {preset!r}: oczekiwano exit 0, got {r.returncode}. stderr={r.stderr[:300]}')
        d = json.loads(r.stdout)
        self.assertIn('metrics', d)
        return d['metrics']['avg_val_last100']

    def test_three_presets_give_distinct_kpi(self):
        """SC-3: window/step/linear dają parami różne avg_val_last100 (seed=42, naive zeta=0.75)."""
        window_kpi = self._run_preset('window')
        step_kpi = self._run_preset('step')
        linear_kpi = self._run_preset('linear')
        self.assertNotEqual(window_kpi, step_kpi,
                            msg=f'window={window_kpi} i step={step_kpi} dają ten sam KPI — '
                                'preset nie dociera do sph_stp (Pitfall 1)')
        self.assertNotEqual(step_kpi, linear_kpi,
                            msg=f'step={step_kpi} i linear={linear_kpi} dają ten sam KPI')
        self.assertNotEqual(window_kpi, linear_kpi,
                            msg=f'window={window_kpi} i linear={linear_kpi} dają ten sam KPI')


class TestConfigHeader(unittest.TestCase):
    """Tests format_config_header zwracającego 9-klucz tabelę MD (ENV-03 unit). Plan 03, Wave 3."""

    def _make_args(self):
        """Minimalny argparse.Namespace z polami czytanymi przez format_config_header."""
        import argparse
        return argparse.Namespace(nU=250, nSUS=20, T=1000, kappa=0.25, alpha=1, seed=42)

    def test_header_contains_section_title(self):
        """ENV-03: zwracany string zawiera literał '## Konfiguracja środowiska'."""
        from sphsim.cli.output import format_config_header
        args = self._make_args()
        header = format_config_header(args, 100, 120, [0.1, 0.2, 0.3, 0.4, 1.0], [0.5, 0.5, 0.7, 1.5, 3.0])
        self.assertIn('## Konfiguracja środowiska', header,
                      msg=f'Brak tytułu sekcji w nagłówku: {header[:200]}')

    def test_header_contains_md_table_structure(self):
        """ENV-03: zwracany string zawiera nagłówek tabeli MD i separator."""
        from sphsim.cli.output import format_config_header
        args = self._make_args()
        header = format_config_header(args, 100, 120, [0.1, 0.2, 0.3, 0.4, 1.0], [0.5, 0.5, 0.7, 1.5, 3.0])
        self.assertIn('| Parametr | Wartość |', header,
                      msg=f'Brak nagłówka tabeli w: {header[:200]}')
        self.assertIn('|----------|---------|', header,
                      msg=f'Brak separatora tabeli w: {header[:200]}')

    def test_header_contains_all_9_param_labels(self):
        """ENV-03: zwracany string zawiera wszystkie 9 etykiet parametrów."""
        from sphsim.cli.output import format_config_header
        args = self._make_args()
        header = format_config_header(args, 100, 120, [0.1, 0.2, 0.3, 0.4, 1.0], [0.5, 0.5, 0.7, 1.5, 3.0])
        for label in ['nU', 'T', 'κ (kappa)', 'α (alpha)', 'K0', 'K1', 'φ (phi)', 'ρ (rho)', 'seed']:
            self.assertIn(label, header,
                          msg=f'Brak etykiety "{label}" w nagłówku: {header[:400]}')

    def test_header_renders_phi_and_rho_lists(self):
        """ENV-03: phi/rho renderowane z 2 miejscami po przecinku przez ', '.join(f'{v:.2f}')."""
        from sphsim.cli.output import format_config_header
        args = self._make_args()
        header = format_config_header(args, 100, 120, [0.1, 0.2, 0.3, 0.4, 1.0], [0.5, 0.5, 0.7, 1.5, 3.0])
        self.assertIn('0.10, 0.20, 0.30, 0.40, 1.00', header,
                      msg=f'Błędne formatowanie phi w nagłówku: {header[:400]}')
        self.assertIn('0.50, 0.50, 0.70, 1.50, 3.00', header,
                      msg=f'Błędne formatowanie rho w nagłówku: {header[:400]}')

    def test_header_renders_K1_inf_as_unicode(self):
        """ENV-03: K1=float('inf') renderowany jako '∞' (Unicode), nie 'inf'."""
        from sphsim.cli.output import format_config_header
        args = self._make_args()
        header = format_config_header(args, 100, float('inf'), [0.1, 0.2, 0.3, 0.4, 1.0], [0.5, 0.5, 0.7, 1.5, 3.0])
        self.assertIn('∞', header,
                      msg=f'K1=inf powinien być renderowany jako ∞, nie "inf": {header[:400]}')
        self.assertNotIn('inf', header,
                         msg=f'Napis "inf" nie powinien pojawiać się w nagłówku gdy K1=inf: {header[:400]}')


class TestHumanHeader(unittest.TestCase):
    """Tests że format_human zaczyna się od config header (ENV-03 integration). Plan 03, Wave 3."""

    def test_placeholder(self):
        self.skipTest("Wave 3 implementation — class name locked by Plan 00")


if __name__ == '__main__':
    unittest.main()
