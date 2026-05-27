"""
TDD RED tests dla Phase 4 Plan 05 Task 2:
  - do_compare istnieje jako metoda SPHShell (D-61)
  - do_compare uruchamia 2x SPHSimulator (sim_with + sim_without)
  - do_compare buduje comparison dict z 'comparison' kluczem
  - do_compare oblicza agent_helps na podstawie avg_net_profit
  - do_compare wraps raw strategy w wrap_with_agent (D-58)
  - Behavior: brak argumentu → "Użycie: compare <nazwa>"
  - Behavior: nieznana strategia → "nie istnieje. Dostępne:"
  - Behavior: incentive expected_P=30 → delta table + werdykt ✓ / ✗
  - Behavior: custom strategy compare działa (D-50)

Stdlib only: unittest + subprocess + sys + os.
"""
import os
import subprocess
import sys
import unittest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class TestReplTask2Source(unittest.TestCase):
    """Weryfikacja kodu źródłowego repl.py po Task 2."""

    def _read_repl(self):
        path = os.path.join(_PROJECT_ROOT, 'sphsim', 'cli', 'repl.py')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_do_compare_method_exists(self):
        """repl.py ma metodę do_compare."""
        src = self._read_repl()
        self.assertIn(
            'def do_compare',
            src,
            msg='brak metody do_compare w repl.py',
        )

    def test_sim_with_exists(self):
        """do_compare buduje sim_with = SPHSimulator z agentem."""
        src = self._read_repl()
        self.assertIn(
            'sim_with = SPHSimulator',
            src,
            msg="brak 'sim_with = SPHSimulator' w repl.py",
        )

    def test_sim_without_exists(self):
        """do_compare buduje sim_without = SPHSimulator bez agenta."""
        src = self._read_repl()
        self.assertIn(
            'sim_without = SPHSimulator',
            src,
            msg="brak 'sim_without = SPHSimulator' w repl.py",
        )

    def test_comparison_key_built(self):
        """do_compare buduje dict z kluczem 'comparison'."""
        src = self._read_repl()
        self.assertIn(
            "'comparison'",
            src,
            msg="brak klucza 'comparison' w repl.py",
        )

    def test_agent_helps_calculated(self):
        """do_compare oblicza agent_helps."""
        src = self._read_repl()
        self.assertIn(
            'agent_helps',
            src,
            msg="brak 'agent_helps' w repl.py",
        )

    def test_wrap_agent_in_do_compare(self):
        """do_compare używa wrap_with_agent(raw_strategy_fn ...) dla sim_with."""
        src = self._read_repl()
        self.assertIn(
            'wrap_with_agent(raw_strategy_fn',
            src,
            msg="brak 'wrap_with_agent(raw_strategy_fn' w repl.py",
        )

    def test_usage_message_exists(self):
        """do_compare ma komunikat 'Użycie: compare'."""
        src = self._read_repl()
        self.assertIn(
            'Użycie: compare',
            src,
            msg="brak komunikatu 'Użycie: compare' w repl.py",
        )


class TestReplTask2Behavior(unittest.TestCase):
    """Testy behawioralne do_compare (subprocess)."""

    _python = sys.executable
    _cwd = _PROJECT_ROOT

    def _run_repl(self, commands, timeout=150):
        """Uruchamia REPL z podanymi komendami i zwraca subprocess.CompletedProcess."""
        result = subprocess.run(
            [self._python, 'sph_sim.py', '--interactive'],
            input=commands,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=self._cwd,
        )
        return result

    def test_compare_no_args_shows_usage(self):
        """compare bez argumentów wyświetla 'Użycie: compare'."""
        r = self._run_repl('compare\nexit\n', timeout=30)
        self.assertTrue(
            'Użycie: compare' in r.stdout or 'Uzycie: compare' in r.stdout,
            msg=f"Brak komunikatu Użycie: compare: {r.stdout[:500]}",
        )

    def test_compare_unknown_strategy_error(self):
        """compare nieistniejąca strategia → 'nie istnieje'."""
        r = self._run_repl('compare absolutely_not_real_strategy_name\nexit\n', timeout=30)
        self.assertIn(
            'nie istnieje',
            r.stdout,
            msg=f"Brak komunikatu 'nie istnieje': {r.stdout[:500]}",
        )

    def test_compare_incentive_produces_delta_table(self):
        """compare incentive expected_P=30 → delta table z metrykami i werdyktem."""
        r = self._run_repl('compare incentive expected_P=30\nexit\n', timeout=150)
        self.assertEqual(
            r.returncode, 0,
            msg=f"REPL crashed rc={r.returncode}, stderr={r.stderr[:400]}",
        )
        out = r.stdout
        self.assertTrue(
            'avg_net_profit' in out or 'net_profit' in out.lower(),
            msg=f"Brak wiersza avg_net_profit w tabeli compare: {out[-2000:]}",
        )
        self.assertTrue(
            '✓' in out or '✗' in out or 'TAK' in out or 'NIE' in out,
            msg=f"Brak werdyktu TAK/NIE w tabeli compare: {out[-2000:]}",
        )

    def test_compare_custom_strategy(self):
        """compare custom_strategy_template po custom load działa (D-50)."""
        commands = 'custom examples/custom_strategy_template.py\ncompare custom_strategy_template\nexit\n'
        r = self._run_repl(commands, timeout=150)
        self.assertEqual(
            r.returncode, 0,
            msg=f"REPL crashed rc={r.returncode}, stderr={r.stderr[:400]}",
        )
        out = r.stdout
        self.assertTrue(
            'avg_net_profit' in out or 'agent_helps' in out or '✓' in out or '✗' in out,
            msg=f"compare custom_strategy_template nie zwróciło tabeli: {out[-2000:]}",
        )


if __name__ == '__main__':
    unittest.main()
