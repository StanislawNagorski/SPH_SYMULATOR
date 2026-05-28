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
                            + D-10 unit tests dla report_dir_override (plan 08-01).

Stdlib only: unittest + subprocess + os + sys + tempfile + shutil + argparse + pathlib.
"""
import argparse
import inspect
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _make_args(**overrides):
    """Builds argparse.Namespace with all fields required by write_report / render_report.

    Mirrors tests/test_report.py::_make_args — keep the two in sync for test stability.
    """
    base = dict(
        nU=250, nSUS=20, T=1000, kappa=0.25, alpha=1,
        K0=100.0, K1=120.0,
        phi=[0.1, 0.2, 0.3, 0.4, 1.0],
        rho=[0.5, 0.5, 0.7, 1.5, 3.0],
        seed=42, strategy='naive', no_agent=True, compare_agent=False,
        valuation='window',
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def _make_single_res(**overrides):
    """Builds result dict in sim.run() shape — single-run (mirror tests/test_report.py)."""
    base = dict(
        avg_val_last100=92.0,
        cum_val_total=92300.0,
        avg_net_profit=140.7592,
        delivery_ratio=0.7931,
        avg_providers_l100=105.03,
        sus_final=1,
        ic_per_phase={1: {'commits': 100}, 2: {'commits': 80}, 3: {'commits': 60}, 4: {'commits': 40}},
        veto_per_phase={1: 5, 2: 3},
        n_vetoed_total=8,
        abstain_per_phase={1: 12, 2: 8, 3: 5, 4: 2},
        history={
            'val':       [50.0 + i * 0.01 for i in range(1000)],
            'providers': [100 + (i % 30) for i in range(1000)],
        },
    )
    base.update(overrides)
    return base


def _make_per_seed_results(n=3):
    """N dictów z 5 kluczami KPIS — deterministyczny generator dla testów batch (mirror test_batch_report)."""
    return [
        {'avg_val_last100': 92.0 + i*0.5, 'cum_val_total': 92300.0 + i*100,
         'avg_net_profit': 140.0 + i*0.5, 'delivery_ratio': 0.79 + i*0.01,
         'avg_providers_l100': 105.0 + i*0.1}
        for i in range(n)
    ]


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
    """TUT-06: raporty generowane w trybie tutorial trafiają do dedykowanego katalogu.

    Plan 08-01 (D-10) provides the `report_dir_override` kwarg on `write_report` and
    `write_batch_report`. The subprocess end-to-end test (`test_tutorial_reports_go_to_dedicated_dir`)
    stays skipped — plan 08-04 wires TutorialFlow.step_report_dir through `do_run`.
    The new unit tests below verify the override kwarg contract directly via function call.
    """

    def setUp(self):
        # Tempdir + SPHSIM_NO_REPORT pop pattern (mirror tests/test_report.py::TestReportFiles).
        self._orig_cwd = os.getcwd()
        self._tmpdir = tempfile.mkdtemp(prefix='p8_test_tutorial_reports_')
        os.chdir(self._tmpdir)
        self._orig_no_report = os.environ.pop('SPHSIM_NO_REPORT', None)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmpdir, ignore_errors=True)
        if self._orig_no_report is not None:
            os.environ['SPHSIM_NO_REPORT'] = self._orig_no_report

    @unittest.skip("Wave 2 — plan 08-04 wires _tutorial_state into do_run")
    def test_tutorial_reports_go_to_dedicated_dir(self):
        self.fail("not yet implemented — see skip reason")

    # ── D-10 unit tests (plan 08-01) ───────────────────────────────────────

    def test_report_dir_override_creates_path_and_writes_files(self):
        """D-10 + Pattern 6: write_report(..., report_dir_override=Path('reports/tutorial-X/step-1-baseline'))
        returns that path and writes report.md + 2 PNGs there, bypassing ./reports/<ts>/.
        """
        from sphsim.report import write_report
        override = Path('reports/tutorial-test/step-1-baseline')
        result = write_report(_make_args(), _make_single_res(), {'zeta': 0.5},
                              120.0, mode='single', report_dir_override=override)
        self.assertIsNotNone(result,
                             msg="write_report zwrócił None — czy SPHSIM_NO_REPORT przeciekł?")
        self.assertEqual(result, override,
                         msg=f"write_report nie zwrócił override path: {result} != {override}")
        self.assertTrue(override.exists(), msg=f"override dir nie istnieje: {override}")
        self.assertTrue((override / 'report.md').exists(),
                        msg="report.md missing in override dir")
        self.assertTrue((override / 'decision_distribution.png').exists(),
                        msg="decision_distribution.png missing in override dir")
        self.assertTrue((override / 'kpi_timeseries.png').exists(),
                        msg="kpi_timeseries.png missing in override dir")
        # Anti-regression: no ./reports/<ts>/ created (default branch NOT taken).
        reports_root = Path('reports')
        sibling_dirs = [p for p in reports_root.iterdir()
                        if p.is_dir() and p.name != 'tutorial-test']
        self.assertEqual(sibling_dirs, [],
                         msg=f"default ./reports/<ts>/ branch leaked: {sibling_dirs}")

    def test_report_dir_override_keyword_only(self):
        """report_dir_override MUST be keyword-only — positional call → TypeError."""
        from sphsim.report import write_report
        sig = inspect.signature(write_report)
        self.assertIn('report_dir_override', sig.parameters,
                      msg="write_report signature missing report_dir_override kwarg")
        self.assertEqual(sig.parameters['report_dir_override'].kind,
                         inspect.Parameter.KEYWORD_ONLY,
                         msg="report_dir_override is not keyword-only")
        self.assertIsNone(sig.parameters['report_dir_override'].default,
                          msg="report_dir_override default is not None")

    def test_report_dir_override_default_none_unchanged_behavior(self):
        """D-10 backwards-compat: report_dir_override=None (default) falls back to ./reports/<ts>/."""
        from sphsim.report import write_report
        result = write_report(_make_args(), _make_single_res(), {'zeta': 0.5},
                              120.0, mode='single')  # no override kwarg
        self.assertIsNotNone(result, msg="write_report zwrócił None w default branch")
        # Default path must be under ./reports/<ts>/ — NOT under tutorial-*.
        result_str = str(result)
        self.assertTrue(result_str.startswith('reports/') or 'reports' in result.parts,
                        msg=f"default branch nie zapisał do reports/: {result}")
        self.assertNotIn('tutorial', result_str,
                         msg=f"default branch leaked override-style path: {result}")

    def test_sphsim_no_report_wins_over_override(self):
        """Pitfall 4: SPHSIM_NO_REPORT=1 must fire BEFORE report_dir_override logic."""
        from sphsim.report import write_report
        os.environ['SPHSIM_NO_REPORT'] = '1'
        try:
            override = Path('tmp_should_not_exist/step-X')
            result = write_report(_make_args(), _make_single_res(), {'zeta': 0.5},
                                  120.0, mode='single', report_dir_override=override)
            self.assertIsNone(result,
                              msg="env-var opt-out NIE wygrał nad override")
            self.assertFalse(override.exists(),
                             msg=f"override path utworzony mimo opt-out: {override}")
        finally:
            del os.environ['SPHSIM_NO_REPORT']

    # ── D-10 write_batch_report unit tests (plan 08-01, Task 2) ────────────

    def test_batch_report_dir_override_creates_path_and_writes_files(self):
        """D-10 + Pattern 6: write_batch_report(..., report_dir_override=Path('reports/tutorial-X/step-8-batch'))
        returns that path and writes report.md + batch_aggregate.png there, bypassing ./reports/batch_<ts>/.
        """
        from sphsim.report import write_batch_report
        from sphsim.batch.stats import aggregate_kpis

        per_seed = _make_per_seed_results(3)
        aggregate = aggregate_kpis(per_seed)
        seeds = [1, 2, 3]
        args = _make_args(batch=True, seeds=seeds, expected_P=100.0,
                          json=False, verbose=False)
        override = Path('reports/tutorial-test/step-8-batch')

        result = write_batch_report(args, per_seed, aggregate, {'zeta': 0.75},
                                    120.0, seeds, report_dir_override=override)
        self.assertIsNotNone(result,
                             msg="write_batch_report zwrócił None — env-var leak?")
        self.assertEqual(result, override,
                         msg=f"write_batch_report nie zwrócił override path: {result} != {override}")
        self.assertTrue(override.exists(), msg=f"override dir nie istnieje: {override}")
        self.assertTrue((override / 'report.md').exists(),
                        msg="report.md missing in batch override dir")
        self.assertTrue((override / 'batch_aggregate.png').exists(),
                        msg="batch_aggregate.png missing in batch override dir")
        # Anti-regression: no ./reports/batch_<ts>/ created.
        reports_root = Path('reports')
        sibling_dirs = [p for p in reports_root.iterdir()
                        if p.is_dir() and p.name.startswith('batch_')]
        self.assertEqual(sibling_dirs, [],
                         msg=f"default ./reports/batch_<ts>/ branch leaked: {sibling_dirs}")

    def test_batch_report_dir_override_keyword_only(self):
        """report_dir_override on write_batch_report MUST be keyword-only with None default."""
        from sphsim.report import write_batch_report
        sig = inspect.signature(write_batch_report)
        self.assertIn('report_dir_override', sig.parameters,
                      msg="write_batch_report signature missing report_dir_override kwarg")
        self.assertEqual(sig.parameters['report_dir_override'].kind,
                         inspect.Parameter.KEYWORD_ONLY,
                         msg="report_dir_override is not keyword-only on write_batch_report")
        self.assertIsNone(sig.parameters['report_dir_override'].default,
                          msg="report_dir_override default is not None on write_batch_report")

    def test_batch_sphsim_no_report_wins_over_override(self):
        """Pitfall 4 (batch): SPHSIM_NO_REPORT=1 must fire BEFORE report_dir_override logic."""
        from sphsim.report import write_batch_report
        from sphsim.batch.stats import aggregate_kpis
        per_seed = _make_per_seed_results(3)
        aggregate = aggregate_kpis(per_seed)
        os.environ['SPHSIM_NO_REPORT'] = '1'
        try:
            override = Path('tmp_batch_should_not_exist/step-X')
            result = write_batch_report(_make_args(), per_seed, aggregate,
                                        {'zeta': 0.5}, 120.0, [1, 2, 3],
                                        report_dir_override=override)
            self.assertIsNone(result,
                              msg="env-var opt-out NIE wygrał nad batch override")
            self.assertFalse(override.exists(),
                             msg=f"batch override path utworzony mimo opt-out: {override}")
        finally:
            del os.environ['SPHSIM_NO_REPORT']


if __name__ == '__main__':
    unittest.main()
