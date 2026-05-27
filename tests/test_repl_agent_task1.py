"""
TDD RED tests dla Phase 4 Plan 05 Task 1:
  - do_run wrap z wrap_with_agent (D-58)
  - do_help z linią 'compare <nazwa>' (D-61)
  - fake_args.no_agent=False (defensive compatibility z format_json)
  - Module docstring: '7 komend' (docstring bump)

Stdlib only: unittest + subprocess + sys + os.
"""
import os
import subprocess
import sys
import unittest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class TestReplTask1Source(unittest.TestCase):
    """Weryfikacja kodu źródłowego repl.py po Task 1."""

    def _read_repl(self):
        path = os.path.join(_PROJECT_ROOT, 'sphsim', 'cli', 'repl.py')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_import_wrap_with_agent(self):
        """repl.py importuje wrap_with_agent z sphsim.agent."""
        src = self._read_repl()
        self.assertIn(
            'from sphsim.agent import wrap_with_agent',
            src,
            msg='brak importu wrap_with_agent w repl.py',
        )

    def test_do_run_wraps_strategy(self):
        """do_run używa wrap_with_agent(STRATEGIES[name], ...) przed SPHSimulator."""
        src = self._read_repl()
        self.assertIn(
            'wrap_with_agent(STRATEGIES[name]',
            src,
            msg='do_run nie opakowuje strategii w wrap_with_agent',
        )

    def test_do_help_has_compare_line(self):
        """do_help zawiera linię z 'compare <nazwa>'."""
        src = self._read_repl()
        self.assertIn(
            'compare <nazwa>',
            src,
            msg="do_help nie zawiera opisu 'compare <nazwa>'",
        )

    def test_fake_args_has_no_agent(self):
        """fake_args w do_run ma atrybut no_agent=False (defensive compatibility)."""
        src = self._read_repl()
        self.assertIn(
            'no_agent=False',
            src,
            msg="fake_args w do_run nie ma no_agent=False",
        )

    def test_docstring_says_7_komend(self):
        """Module docstring mówi '7 komend' (nie 6)."""
        src = self._read_repl()
        self.assertTrue(
            '7 komend' in src or '7 commands' in src,
            msg="Module docstring nie zawiera '7 komend'",
        )


class TestReplTask1Behavior(unittest.TestCase):
    """Testy behawioralne REPL po Task 1 (subprocess)."""

    _python = sys.executable
    _cwd = _PROJECT_ROOT

    def _run_repl(self, commands, timeout=60):
        """Uruchamia REPL z podanymi komendami i zwraca stdout."""
        result = subprocess.run(
            [self._python, 'sph_sim.py', '--interactive'],
            input=commands,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=self._cwd,
        )
        return result

    def test_help_shows_compare(self):
        """help pokazuje komendę 'compare'."""
        r = self._run_repl('help\nexit\n')
        self.assertIn(
            'compare',
            r.stdout.lower(),
            msg=f"'compare' nie pojawia się w do_help output: {r.stdout[:800]}",
        )

    def test_run_with_agent_no_crash(self):
        """do_run z wrap_with_agent nie crashuje (REPL run naive z agentem)."""
        r = self._run_repl('run naive zeta=0.5\nexit\n', timeout=90)
        self.assertEqual(
            r.returncode, 0,
            msg=f"REPL crashed rc={r.returncode}, stderr={r.stderr[:400]}",
        )
        self.assertTrue(
            'NAIVE' in r.stdout or 'Strategia: NAIVE' in r.stdout or 'METRYKI' in r.stdout,
            msg=f"Brak outputu NAIVE w REPL run: {r.stdout[-1500:]}",
        )


if __name__ == '__main__':
    unittest.main()
