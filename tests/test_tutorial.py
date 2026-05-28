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

Plus TestTutorialFlow — Plan 08-03 (Wave 1): pure state machine
(TutorialFlow + STEP_TOPICS + STEP_TASKS + check_step) w sphsim/cli/tutorial.py.

Stdlib only: unittest + subprocess + os + sys + re.
"""
import os
import re
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

    @unittest.skip("Wave 1 — plan 08-01 adds report_dir_override; Wave 2 — plan 08-04 wires it through")
    def test_tutorial_reports_go_to_dedicated_dir(self):
        self.fail("not yet implemented — see skip reason")


class TestTutorialFlow(unittest.TestCase):
    """Plan 08-03: pure state machine (TutorialFlow + STEP_TOPICS + STEP_TASKS + check_step).

    Tests run in isolation — no repl.py / sphsim.* dependency at module level
    other than the just-built sphsim.cli.tutorial module. All imports inside
    test methods to keep module-level free of side effects.
    """

    # === Task 1 tests: dataclasses + module-level constants ===

    def test_tutorialflow_defaults(self):
        """Test 1: TutorialFlow() defaults — step=1, total=8, hint_count=0, MAX_HINTS=3, session_ts matches r'\\d{8}-\\d{6}'."""
        from sphsim.cli.tutorial import TutorialFlow
        tf = TutorialFlow()
        self.assertEqual(tf.step, 1)
        self.assertEqual(tf.total, 8)
        self.assertEqual(tf.hint_count, 0)
        self.assertEqual(tf.MAX_HINTS, 3)
        self.assertRegex(tf.session_ts, r'^\d{8}-\d{6}$')

    def test_base_report_dir_shape(self):
        """Test 2: base_report_dir returns Path('reports') / f'tutorial-{session_ts}'."""
        from pathlib import Path
        from sphsim.cli.tutorial import TutorialFlow
        tf = TutorialFlow()
        self.assertEqual(tf.base_report_dir, Path('reports') / f'tutorial-{tf.session_ts}')

    def test_step_report_dir_shape(self):
        """Test 3: step_report_dir('baseline') returns base / step-1-baseline at default step=1."""
        from pathlib import Path
        from sphsim.cli.tutorial import TutorialFlow
        tf = TutorialFlow()
        self.assertEqual(
            tf.step_report_dir('baseline'),
            Path('reports') / f'tutorial-{tf.session_ts}' / 'step-1-baseline',
        )

    def test_step_topics_keys_and_slugs(self):
        """Test 4: STEP_TOPICS dict with int keys 1..8 mapping to ordered slugs."""
        from sphsim.cli.tutorial import STEP_TOPICS
        expected = {
            1: 'baseline',
            2: 'strategies',
            3: 'run-strategy',
            4: 'custom',
            5: 'compare',
            6: 'env',
            7: 'report',
            8: 'batch',
        }
        self.assertEqual(STEP_TOPICS, expected)

    def test_step_tasks_have_tutorialstep_instances(self):
        """Test 5: STEP_TASKS dict[int]->TutorialStep with .description, .expected_command_hint, .topic matching STEP_TOPICS."""
        from sphsim.cli.tutorial import STEP_TASKS, STEP_TOPICS, TutorialStep
        self.assertEqual(set(STEP_TASKS.keys()), set(range(1, 9)))
        for step_n in range(1, 9):
            ts = STEP_TASKS[step_n]
            self.assertIsInstance(ts, TutorialStep)
            self.assertIsInstance(ts.description, str)
            self.assertIsInstance(ts.expected_command_hint, str)
            self.assertEqual(ts.topic, STEP_TOPICS[step_n])

    def test_step1_polish_copy_contains_run_naive_and_kpi(self):
        """Test 6: STEP_TASKS[1].description contains 'run naive' and 'KPI' (RESEARCH §Polish Tone Calibration verbatim)."""
        from sphsim.cli.tutorial import STEP_TASKS
        desc = STEP_TASKS[1].description
        self.assertIn('run naive', desc)
        self.assertIn('KPI', desc)

    def test_step6_open_question_2_resolution(self):
        """Test 7: STEP_TASKS[6].description contains '--phi' and 'informacyjny' (Open Question #2 — soft-pass informational step)."""
        from sphsim.cli.tutorial import STEP_TASKS
        desc = STEP_TASKS[6].description
        self.assertIn('--phi', desc)
        self.assertIn('informacyjny', desc)

    # === Task 2 tests: check_step per RESEARCH §Step Verification Map ===

    def test_check_step1_baseline_pass_and_fail(self):
        """Test 1 (step 1 baseline): run naive + KPI>=80 passes; non-naive run fails."""
        from sphsim.cli.tutorial import check_step
        self.assertTrue(check_step(
            1, 'run naive zeta=0.75',
            {'avg_val_last100': 92.0},
            {'naive': lambda: None}, frozenset({'naive'}),
        ))
        self.assertFalse(check_step(
            1, 'run incentive',
            {'avg_val_last100': 50.0},
            {'naive': lambda: None, 'incentive': lambda: None},
            frozenset({'naive', 'incentive'}),
        ))

    def test_check_step1_low_kpi_fails(self):
        """Test 2 (step 1 low KPI): run naive but avg_val_last100 < 80 fails."""
        from sphsim.cli.tutorial import check_step
        self.assertFalse(check_step(
            1, 'run naive',
            {'avg_val_last100': 50.0},
            {'naive': lambda: None}, frozenset({'naive'}),
        ))

    def test_check_step2_strategies(self):
        """Test 3 (step 2 strategies): line=='strategies' or startswith('strategy ') passes; else fails."""
        from sphsim.cli.tutorial import check_step
        self.assertTrue(check_step(2, 'strategies', None, set(), frozenset()))
        self.assertTrue(check_step(2, 'strategy incentive', None, set(), frozenset()))
        self.assertFalse(check_step(2, 'run naive', None, set(), frozenset()))

    def test_check_step3_any_builtin(self):
        """Test 4 (step 3 any builtin): run <builtin> passes; run <non-builtin> fails."""
        from sphsim.cli.tutorial import check_step
        builtins = frozenset({'naive', 'incentive', 'adaptive'})
        self.assertTrue(check_step(
            3, 'run incentive',
            {'avg_val_last100': 50.0},
            set(builtins), builtins,
        ))
        self.assertFalse(check_step(
            3, 'run xyz',
            {'avg_val_last100': 50.0},
            set(builtins), builtins,
        ))

    def test_check_step4_custom(self):
        """Test 5 (step 4 custom): new key in strategies_keys but not in builtins → True; no new key → False."""
        from sphsim.cli.tutorial import check_step
        # custom loaded → diff non-empty
        self.assertTrue(check_step(
            4, 'custom examples/custom_strategy_template.py',
            None,
            {'naive', 'my_custom'}, frozenset({'naive'}),
        ))
        # no custom loaded → diff empty
        self.assertFalse(check_step(
            4, 'custom path.py',
            None,
            {'naive'}, frozenset({'naive'}),
        ))

    def test_check_step5_compare(self):
        """Test 6 (step 5 compare): compare cmd + comparison.delta truthy → True; empty delta → False."""
        from sphsim.cli.tutorial import check_step
        self.assertTrue(check_step(
            5, 'compare incentive',
            {'comparison': {'delta': {'avg_val': 5.0}}},
            set(), frozenset(),
        ))
        self.assertFalse(check_step(
            5, 'compare',
            {'comparison': {}},
            set(), frozenset(),
        ))

    def test_check_step6_soft_pass(self):
        """Test 7 (step 6 soft-pass): any non-empty line → True; empty → False (Open Question #2 resolution)."""
        from sphsim.cli.tutorial import check_step
        self.assertTrue(check_step(6, 'anything', None, set(), frozenset()))
        self.assertTrue(check_step(6, 'skip', None, set(), frozenset()))
        self.assertFalse(check_step(6, '', None, set(), frozenset()))

    def test_check_step7_soft_pass(self):
        """Test 8 (step 7 soft-pass): any non-empty line → True (Open Question #3 resolution)."""
        from sphsim.cli.tutorial import check_step
        self.assertTrue(check_step(7, 'anything', None, set(), frozenset()))
        self.assertTrue(check_step(7, 'skip', None, set(), frozenset()))
        self.assertFalse(check_step(7, '', None, set(), frozenset()))

    def test_check_step8_batch(self):
        """Test 9 (step 8 batch): batch + --seeds + aggregate in result → True; missing --seeds → False; no result → False."""
        from sphsim.cli.tutorial import check_step
        self.assertTrue(check_step(
            8, 'batch naive --seeds 5',
            {'aggregate': {'avg_val_last100': {'mean': 92.0}}, 'per_seed': []},
            set(), frozenset(),
        ))
        self.assertFalse(check_step(
            8, 'batch naive',
            {'aggregate': {'avg_val_last100': {'mean': 92.0}}},
            set(), frozenset(),
        ))
        self.assertFalse(check_step(
            8, 'batch naive --seeds 5',
            None,
            set(), frozenset(),
        ))


if __name__ == '__main__':
    unittest.main()
