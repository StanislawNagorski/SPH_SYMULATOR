"""
Test stubs dla Phase 8 — Interactive Tutorial (TUT-01..TUT-06).

Wave 0 scaffolding: wszystkie testy są @unittest.skip z powodem wskazującym
na wave i plan, który dostarczy implementację. Stub body to self.fail() aby
usunięcie skip nie dawało fałszywego zielonego.

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
    """TUT-05: flaga --tutorial wchodzi bezpośrednio w tryb tutorial."""

    @unittest.skip("Wave 1 — plan 08-02 adds --tutorial flag; Wave 2 — plan 08-04 wires it")
    def test_tutorial_flag_enters_tutorial_mode(self):
        self.fail("not yet implemented — see skip reason")


class TestTutorialReports(unittest.TestCase):
    """TUT-06: raporty generowane w trybie tutorial trafiają do dedykowanego katalogu."""

    @unittest.skip("Wave 1 — plan 08-01 adds report_dir_override; Wave 2 — plan 08-04 threads it through")
    def test_tutorial_reports_go_to_dedicated_dir(self):
        self.fail("not yet implemented — see skip reason")


if __name__ == '__main__':
    unittest.main()
