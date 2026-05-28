"""
Test stubs dla Phase 8 — Interactive Tutorial (TUT-01..TUT-06).

Wave 0 scaffolding: pozostałe testy są @unittest.skip z powodem wskazującym
na wave i plan, który dostarczy implementację. Stub body to self.fail() aby
usunięcie skip nie dawało fałszywego zielonego.

Wave 1 — Plan 08-02: TestTutorialCLI flipped — 8 real tests for the
argparse-layer behavior (--tutorial flag parses, 5 mutex combinations
produce Polish errors, required-mode Polish error replaces argparse English
fallback, existing CLI baseline still works). End-to-end "tutorial banner
prints" test stays @unittest.skip — Plan 08-04 wires it via run_repl.

Pokrywa 5 klas:
  1. TestTutorialEntry    — TUT-01: do_tutorial dostępne w REPL
  2. TestTutorialControls — TUT-02 + TUT-03: skip/back nawigacja
  3. TestTutorialExit     — TUT-04: exit w trybie tutorial nie zamyka REPL
  4. TestTutorialCLI      — TUT-05: --tutorial flag wejście do trybu tutorial
  5. TestTutorialReports  — TUT-06: raporty tutorial do dedykowanego katalogu

Stdlib only: unittest + subprocess + os + sys.
"""
import os
import subprocess
import sys
import unittest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _run_sph(*args, **kwargs):
    """Subprocess helper — uruchamia sph_sim.py z cwd=_PROJECT_ROOT (mirror tests/test_batch.py)."""
    env = {**os.environ, 'SPHSIM_NO_REPORT': kwargs.pop('SPHSIM_NO_REPORT', '1')}
    return subprocess.run(
        [sys.executable, 'sph_sim.py', *args],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        **kwargs,
    )


class TestTutorialEntry(unittest.TestCase):
    """TUT-01: komenda do_tutorial dostępna w REPL ('tutorial' wpisane w REPL wchodzi w tryb tutorial)."""

    @unittest.skip("Wave 2 — plan 08-04 wires do_tutorial in repl.py")
    def test_do_tutorial_present_in_repl(self):
        self.fail("not yet implemented — see skip reason")


class TestTutorialControls(unittest.TestCase):
    """TUT-02 + TUT-03: nawigacja skip/back w trybie tutorial."""

    @unittest.skip("Wave 2 — plan 08-04")
    def test_skip_advances_counter(self):
        self.fail("not yet implemented — see skip reason")

    @unittest.skip("Wave 2 — plan 08-04")
    def test_back_decrements_counter(self):
        self.fail("not yet implemented — see skip reason")


class TestTutorialExit(unittest.TestCase):
    """TUT-04: 'exit' w trybie tutorial wraca do REPL, nie kończy procesu."""

    @unittest.skip("Wave 2 — plan 08-04")
    def test_exit_in_tutorial_does_not_quit_repl(self):
        self.fail("not yet implemented — see skip reason")


class TestTutorialCLI(unittest.TestCase):
    """TUT-05: flaga --tutorial — argparse layer (Wave 1, Plan 08-02).

    8 real tests cover:
      - --tutorial parseable (--help short-circuits before mutex)
      - 5 conflict combinations produce Polish errors verbatim per PATTERNS.md
      - Existing CLI baseline unchanged (regression-light)
      - Required-mode Polish error replaces argparse English fallback
    The end-to-end "tutorial banner prints" subprocess test stays @unittest.skip
    until Plan 08-04 lands run_repl(start_in_tutorial=True).
    """

    def test_tutorial_flag_parses_without_error(self):
        """--tutorial --help → exit 0 (--help short-circuits inside argparse before mutex)."""
        r = _run_sph('--tutorial', '--help')
        self.assertEqual(
            r.returncode, 0,
            msg=f'--tutorial --help powinno dać exit 0, ale rc={r.returncode}, stderr={r.stderr[:400]}'
        )
        self.assertIn(
            '--tutorial', r.stdout,
            msg=f'--tutorial brakuje w --help output: {r.stdout[:400]}'
        )

    def test_tutorial_plus_interactive_errors_polish(self):
        """--tutorial + --interactive → exit 2 z polskim komunikatem."""
        r = _run_sph('--tutorial', '--interactive')
        self.assertNotEqual(r.returncode, 0,
                            msg=f'Mutex --tutorial + --interactive powinno fail, rc={r.returncode}')
        combined = r.stderr + r.stdout
        self.assertIn(
            'Flagi --tutorial i --interactive są wzajemnie wykluczające.', combined,
            msg=f'Polski komunikat brakuje w stderr: {combined[:600]}'
        )

    def test_tutorial_plus_strategy_errors_polish(self):
        """--tutorial + --strategy naive → exit 2 z polskim komunikatem."""
        r = _run_sph('--tutorial', '--strategy', 'naive')
        self.assertNotEqual(r.returncode, 0,
                            msg=f'Mutex --tutorial + --strategy powinno fail, rc={r.returncode}')
        combined = r.stderr + r.stdout
        self.assertIn(
            'Flaga --tutorial nie działa z --strategy', combined,
            msg=f'Polski komunikat brakuje w stderr: {combined[:600]}'
        )

    def test_tutorial_plus_custom_errors_polish(self):
        """--tutorial + --custom <path> → exit 2 z polskim komunikatem."""
        r = _run_sph('--tutorial', '--custom', 'examples/custom_strategy_template.py')
        self.assertNotEqual(r.returncode, 0,
                            msg=f'Mutex --tutorial + --custom powinno fail, rc={r.returncode}')
        combined = r.stderr + r.stdout
        self.assertIn(
            'Flaga --tutorial nie działa z --custom.', combined,
            msg=f'Polski komunikat brakuje w stderr: {combined[:600]}'
        )

    def test_tutorial_plus_batch_errors_polish(self):
        """--tutorial + --batch --seeds 5 → exit 2 z polskim komunikatem."""
        r = _run_sph('--tutorial', '--batch', '--seeds', '5')
        self.assertNotEqual(r.returncode, 0,
                            msg=f'Mutex --tutorial + --batch powinno fail, rc={r.returncode}')
        combined = r.stderr + r.stdout
        self.assertIn(
            'Flagi --tutorial i --batch są wzajemnie wykluczające.', combined,
            msg=f'Polski komunikat brakuje w stderr: {combined[:600]}'
        )

    def test_tutorial_plus_compare_agent_errors_polish(self):
        """--tutorial + --compare-agent → exit 2 z polskim komunikatem."""
        r = _run_sph('--tutorial', '--compare-agent')
        self.assertNotEqual(r.returncode, 0,
                            msg=f'Mutex --tutorial + --compare-agent powinno fail, rc={r.returncode}')
        combined = r.stderr + r.stdout
        self.assertIn(
            'Flagi --tutorial i --compare-agent są wzajemnie wykluczające.', combined,
            msg=f'Polski komunikat brakuje w stderr: {combined[:600]}'
        )

    def test_existing_cli_unchanged_baseline_works(self):
        """--strategy naive --seed 42 --json --no-agent → still prints avg_val_last100 (baseline)."""
        r = _run_sph('--strategy', 'naive', '--seed', '42', '--json', '--no-agent')
        self.assertEqual(
            r.returncode, 0,
            msg=f'Baseline strategy invocation powinno dać exit 0, rc={r.returncode}, stderr={r.stderr[:400]}'
        )
        self.assertIn(
            'avg_val_last100', r.stdout,
            msg=f'avg_val_last100 brakuje w JSON output: {r.stdout[:600]}'
        )

    def test_no_mode_errors_polish(self):
        """python sph_sim.py (no mode flag) → exit 2 z polskim komunikatem 'Musisz podać jeden z trybów:'."""
        r = _run_sph()
        self.assertNotEqual(r.returncode, 0,
                            msg=f'Brak trybu powinno fail, rc={r.returncode}')
        combined = r.stderr + r.stdout
        self.assertIn(
            'Musisz podać jeden z trybów:', combined,
            msg=f'Polski required-mode komunikat brakuje w stderr: {combined[:600]}'
        )

    @unittest.skip("Wave 2 — plan 08-04 wires run_repl(start_in_tutorial=True)")
    def test_tutorial_flag_enters_tutorial_mode(self):
        self.fail("not yet implemented — see skip reason")


class TestTutorialReports(unittest.TestCase):
    """TUT-06: raporty generowane w trybie tutorial trafiają do dedykowanego katalogu."""

    @unittest.skip("Wave 1 — plan 08-01 adds report_dir_override; Wave 2 — plan 08-04 wires it")
    def test_tutorial_reports_go_to_dedicated_dir(self):
        self.fail("not yet implemented — see skip reason")


if __name__ == '__main__':
    unittest.main()
