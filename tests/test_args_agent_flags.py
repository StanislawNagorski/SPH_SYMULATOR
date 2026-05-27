"""
Unit tests dla sphsim/cli/args.py — --no-agent + --compare-agent flags (Phase 4, D-58/D-60/D-54).

Pokrywa:
  1. --no-agent rozpoznana (boolean store_true, default False)
  2. --compare-agent rozpoznana (boolean store_true, default False)
  3. Domyślne wartości (False/False) bez flag
  4. Mutex: --compare-agent + --no-agent → p.error (exit 2) z polskim komunikatem
  5. Mutex: --compare-agent + --interactive → p.error (exit 2)
  6. --help zawiera --no-agent
  7. --help zawiera --compare-agent
  8. --expected_P help text zaktualizowany: '[incentive|agent]'

Stdlib only: unittest + subprocess + sys + os
"""
import os
import sys
import subprocess
import unittest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _run_sph(*args, **kwargs):
    """Uruchamia sph_sim.py z podanymi argumentami. Zwraca CompletedProcess."""
    return subprocess.run(
        [sys.executable, 'sph_sim.py'] + list(args),
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        **kwargs
    )


class TestArgsAgentFlags(unittest.TestCase):
    """Tests dla --no-agent i --compare-agent flag w args.py."""

    def test_no_agent_flag_recognized_exit_zero(self):
        """--no-agent jest rozpoznana przez argparse — exit 0."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--no-agent', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 0,
                         msg=f'--no-agent powinno dać exit 0, ale rc={r.returncode}, stderr={r.stderr[:300]}')

    def test_compare_agent_flag_recognized_exit_zero(self):
        """--compare-agent jest rozpoznana przez argparse — exit 0."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--compare-agent', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 0,
                         msg=f'--compare-agent powinno dać exit 0, ale rc={r.returncode}, stderr={r.stderr[:300]}')

    def test_default_no_agent_is_false(self):
        """Bez flagi --no-agent: args.no_agent == False."""
        from sphsim.cli.args import parse_args
        import argparse
        # Symuluj parse args dla --strategy naive --zeta 0.5
        old_argv = sys.argv
        try:
            sys.argv = ['sph_sim.py', '--strategy', 'naive', '--zeta', '0.5']
            args = parse_args()
            self.assertFalse(args.no_agent,
                             msg=f'args.no_agent powinno być False domyślnie, got {args.no_agent}')
        finally:
            sys.argv = old_argv

    def test_default_compare_agent_is_false(self):
        """Bez flagi --compare-agent: args.compare_agent == False."""
        from sphsim.cli.args import parse_args
        old_argv = sys.argv
        try:
            sys.argv = ['sph_sim.py', '--strategy', 'naive', '--zeta', '0.5']
            args = parse_args()
            self.assertFalse(args.compare_agent,
                             msg=f'args.compare_agent powinno być False domyślnie, got {args.compare_agent}')
        finally:
            sys.argv = old_argv

    def test_mutex_compare_agent_and_no_agent_exit_2(self):
        """--compare-agent + --no-agent → exit 2 z polskim komunikatem 'wykluczające'."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--compare-agent', '--no-agent')
        self.assertNotEqual(r.returncode, 0,
                            msg=f'Mutex --compare-agent + --no-agent powinno fail, got rc={r.returncode}')
        self.assertEqual(r.returncode, 2,
                         msg=f'Argparse error powinien dać rc=2, got rc={r.returncode}')
        combined_out = r.stderr + r.stdout
        self.assertTrue(
            'wykluczające' in combined_out or 'wykluczajace' in combined_out,
            msg=f'Polski komunikat "wykluczające" brakuje w stderr: {combined_out[:400]}'
        )

    def test_mutex_compare_agent_and_interactive_exit_2(self):
        """--compare-agent + --interactive → exit 2 (D-60)."""
        r = _run_sph('--interactive', '--compare-agent')
        self.assertNotEqual(r.returncode, 0,
                            msg=f'Mutex --interactive + --compare-agent powinno fail, got rc={r.returncode}')
        self.assertEqual(r.returncode, 2,
                         msg=f'Argparse error powinien dać rc=2, got rc={r.returncode}')

    def test_help_shows_no_agent(self):
        """--help output zawiera '--no-agent'."""
        r = _run_sph('--help')
        combined = r.stdout + r.stderr
        self.assertIn('--no-agent', combined,
                      msg=f'--no-agent brakuje w --help output')

    def test_help_shows_compare_agent(self):
        """--help output zawiera '--compare-agent'."""
        r = _run_sph('--help')
        combined = r.stdout + r.stderr
        self.assertIn('--compare-agent', combined,
                      msg=f'--compare-agent brakuje w --help output')

    def test_expected_p_help_text_updated(self):
        """--expected_P help text zawiera '[incentive|agent]' (D-54)."""
        r = _run_sph('--help')
        combined = r.stdout + r.stderr
        self.assertIn('[incentive|agent]', combined,
                      msg=f'[incentive|agent] brakuje w help text dla --expected_P: {combined[:600]}')


if __name__ == '__main__':
    unittest.main()
