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
                            + D-10 unit tests dla report_dir_override (plan 08-01).

Plus TestTutorialFlow — Plan 08-03 (Wave 1): pure state machine
(TutorialFlow + STEP_TOPICS + STEP_TASKS + check_step) w sphsim/cli/tutorial.py.

Stdlib only: unittest + subprocess + os + sys + tempfile + shutil + argparse + pathlib + re.
"""
import argparse
import inspect
import os
import re
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


def _run_repl_interactive(commands, timeout=120, no_report='1'):
    """Subprocess helper — uruchamia REPL z podanymi komendami via stdin.

    Mirror tests/test_repl_agent_task1.py::TestReplTask1Behavior._run_repl. Used by
    Wave 2 / Plan 08-04 tutorial behavior tests (TUT-01..TUT-04).
    """
    env = {**os.environ, 'SPHSIM_NO_REPORT': no_report}
    return subprocess.run(
        [sys.executable, 'sph_sim.py', '--interactive'],
        input=commands,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=_PROJECT_ROOT,
        env=env,
    )


def _run_repl_tutorial_flag(commands, timeout=120, no_report='1'):
    """Subprocess helper — runs `python sph_sim.py --tutorial` with stdin commands."""
    env = {**os.environ, 'SPHSIM_NO_REPORT': no_report}
    return subprocess.run(
        [sys.executable, 'sph_sim.py', '--tutorial'],
        input=commands,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=_PROJECT_ROOT,
        env=env,
    )


class TestTutorialEntry(unittest.TestCase):
    """TUT-01: komenda do_tutorial dostępna w REPL — Wave 2 / Plan 08-04 wiring.

    Combines source-grep tests (cheap structural verification of SPHShell additions)
    with subprocess behavior tests (end-to-end TUT-01 — banner + step 1 display +
    do_help line). All Polish copy strings asserted VERBATIM per the action block of
    08-04-PLAN.md.
    """

    def _read_repl(self):
        path = os.path.join(_PROJECT_ROOT, 'sphsim', 'cli', 'repl.py')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_do_tutorial_present_in_repl(self):
        """TUT-01 source: SPHShell has do_tutorial + precmd + postcmd."""
        src = self._read_repl()
        self.assertIn('def do_tutorial', src,
                      msg='SPHShell brakuje def do_tutorial')
        self.assertIn('def precmd', src,
                      msg='SPHShell brakuje def precmd')
        self.assertIn('def postcmd', src,
                      msg='SPHShell brakuje def postcmd')

    def test_tutorial_banner_and_step1_shown(self):
        """TUT-01 behavior: `tutorial` w REPL → banner + krok 1/8 + Tutorial opuszczony po exit."""
        r = _run_repl_interactive('tutorial\nexit\nexit\n')
        self.assertEqual(r.returncode, 0,
                         msg=f'REPL crashed rc={r.returncode}, stderr={r.stderr[:600]}')
        self.assertIn('INTERAKTYWNY TUTORIAL', r.stdout,
                      msg=f'banner brakuje w stdout: {r.stdout[:800]}')
        self.assertIn('[krok 1/8', r.stdout,
                      msg=f'step 1 display brakuje w stdout: {r.stdout[:800]}')
        self.assertIn('Tutorial opuszczony', r.stdout,
                      msg=f'exit msg brakuje w stdout: {r.stdout[:800]}')

    def test_help_includes_tutorial_line(self):
        """do_help wyświetla wiersz dla `tutorial` (discoverability)."""
        r = _run_repl_interactive('help\nexit\n')
        self.assertIn('tutorial', r.stdout,
                      msg=f'do_help nie wymienia tutorial: {r.stdout[:800]}')


class TestTutorialControls(unittest.TestCase):
    """TUT-02 + TUT-03: nawigacja skip/back/repeat w trybie tutorial."""

    def test_skip_advances_counter(self):
        """TUT-02: skip advances step counter (1 → 2 displayed)."""
        r = _run_repl_interactive('tutorial\nskip\nexit\nexit\n')
        self.assertEqual(r.returncode, 0,
                         msg=f'REPL crashed rc={r.returncode}, stderr={r.stderr[:600]}')
        self.assertIn('pominięto — krok 1/8', r.stdout,
                      msg=f'pominięto komunikat brakuje: {r.stdout[:1500]}')
        self.assertIn('[krok 2/8', r.stdout,
                      msg=f'krok 2/8 nie pokazany po skip: {r.stdout[:1500]}')

    def test_back_decrements_counter(self):
        """TUT-03: back z kroku 2 wraca do kroku 1 (decrement)."""
        r = _run_repl_interactive('tutorial\nskip\nback\nexit\nexit\n')
        self.assertEqual(r.returncode, 0,
                         msg=f'REPL crashed rc={r.returncode}, stderr={r.stderr[:600]}')
        self.assertIn('cofnięto do kroku 1/8', r.stdout,
                      msg=f'back nie cofnął do kroku 1: {r.stdout[:1500]}')

    def test_back_at_step_one_boundary(self):
        """TUT-03 boundary: back na step 1 → polski komunikat 'Już jesteś na pierwszym kroku.'"""
        r = _run_repl_interactive('tutorial\nback\nexit\nexit\n')
        self.assertEqual(r.returncode, 0,
                         msg=f'REPL crashed rc={r.returncode}, stderr={r.stderr[:600]}')
        self.assertIn('Już jesteś na pierwszym kroku.', r.stdout,
                      msg=f'back boundary msg brakuje: {r.stdout[:1500]}')


class TestTutorialExit(unittest.TestCase):
    """TUT-04: 'exit' w trybie tutorial wraca do REPL, nie kończy procesu (Pitfall 1)."""

    def test_exit_in_tutorial_does_not_quit_repl(self):
        """TUT-04: tutorial exit → REPL żyje dalej; strategies still works; final exit fires do_exit."""
        r = _run_repl_interactive('tutorial\nexit\nstrategies\nexit\n')
        self.assertEqual(r.returncode, 0,
                         msg=f'REPL crashed rc={r.returncode}, stderr={r.stderr[:600]}')
        self.assertIn('Tutorial opuszczony', r.stdout,
                      msg=f'tutorial exit msg brakuje: {r.stdout[:1500]}')
        # Strategies command must have produced output AFTER tutorial exit (REPL still alive).
        self.assertIn('Dostępne strategie', r.stdout,
                      msg=f'strategies command nie zadziałał po tutorial exit: {r.stdout[:1500]}')
        # Final exit triggers do_exit farewell ONCE.
        self.assertIn('Do widzenia.', r.stdout,
                      msg=f'do_exit farewell brakuje na końcu: {r.stdout[:1500]}')

    def test_pitfall_1_tutorial_exit_does_not_trigger_do_exit(self):
        """Pitfall 1: tutorial 'exit' nie powinno triggerować do_exit (Do widzenia.) — tylko drugi exit."""
        r = _run_repl_interactive('tutorial\nexit\nstrategies\nexit\n')
        # `Do widzenia.` should appear EXACTLY once — only from the FINAL exit (after `strategies`).
        count = r.stdout.count('Do widzenia.')
        self.assertEqual(count, 1,
                         msg=f"`Do widzenia.` count should be 1, got {count}. stdout={r.stdout[:2000]}")


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

    def test_tutorial_flag_enters_tutorial_mode(self):
        """TUT-05 end-to-end: `python sph_sim.py --tutorial` → banner + krok 1/8 auto-shown."""
        r = _run_repl_tutorial_flag('exit\nexit\n')
        self.assertEqual(r.returncode, 0,
                         msg=f'--tutorial crashed rc={r.returncode}, stderr={r.stderr[:600]}')
        self.assertIn('INTERAKTYWNY TUTORIAL', r.stdout,
                      msg=f'banner brakuje pod --tutorial: {r.stdout[:1500]}')
        self.assertIn('[krok 1/8', r.stdout,
                      msg=f'krok 1/8 nie pokazany pod --tutorial: {r.stdout[:1500]}')


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

    def test_tutorial_reports_go_to_dedicated_dir(self):
        """TUT-06 end-to-end: `tutorial` → `run naive zeta=0.75` → report w `./reports/tutorial-<ts>/step-1-baseline/`."""
        r = subprocess.run(
            [sys.executable, os.path.join(_PROJECT_ROOT, 'sph_sim.py'), '--interactive'],
            input='tutorial\nrun naive zeta=0.75\nexit\nexit\n',
            capture_output=True,
            text=True,
            timeout=180,
            cwd=self._tmpdir,
            env={**os.environ, 'SPHSIM_NO_REPORT': ''},
        )
        self.assertEqual(r.returncode, 0,
                         msg=f'REPL crashed rc={r.returncode}, stderr={r.stderr[:600]}')
        # ./reports/tutorial-<ts>/step-1-baseline/ exists with required artifacts.
        tutorial_dirs = list(Path(self._tmpdir, 'reports').glob('tutorial-*'))
        self.assertEqual(len(tutorial_dirs), 1,
                         msg=f'expected exactly 1 tutorial-* dir, got: {tutorial_dirs}')
        step1_dir = tutorial_dirs[0] / 'step-1-baseline'
        self.assertTrue(step1_dir.exists(),
                        msg=f'step-1-baseline missing under {tutorial_dirs[0]}')
        self.assertTrue((step1_dir / 'report.md').exists(),
                        msg='report.md missing in tutorial step-1-baseline')
        self.assertTrue((step1_dir / 'decision_distribution.png').exists(),
                        msg='decision_distribution.png missing in tutorial step-1-baseline')
        self.assertTrue((step1_dir / 'kpi_timeseries.png').exists(),
                        msg='kpi_timeseries.png missing in tutorial step-1-baseline')

    def test_non_tutorial_report_unchanged(self):
        """TUT-06 backwards-compat: `run naive` outside tutorial → `./reports/<ts>/` (no tutorial- prefix)."""
        r = subprocess.run(
            [sys.executable, os.path.join(_PROJECT_ROOT, 'sph_sim.py'), '--interactive'],
            input='run naive zeta=0.75\nexit\n',
            capture_output=True,
            text=True,
            timeout=180,
            cwd=self._tmpdir,
            env={**os.environ, 'SPHSIM_NO_REPORT': ''},
        )
        self.assertEqual(r.returncode, 0,
                         msg=f'REPL crashed rc={r.returncode}, stderr={r.stderr[:600]}')
        # ./reports/<ts>/ exists; NO tutorial-* dir created.
        tutorial_dirs = list(Path(self._tmpdir, 'reports').glob('tutorial-*'))
        self.assertEqual(tutorial_dirs, [],
                         msg=f'tutorial-* dir leaked in non-tutorial run: {tutorial_dirs}')
        all_dirs = [p for p in Path(self._tmpdir, 'reports').iterdir() if p.is_dir()]
        self.assertEqual(len(all_dirs), 1,
                         msg=f'expected exactly 1 ./reports/<ts>/ dir, got: {all_dirs}')
        ts_dir = all_dirs[0]
        # Name should be a timestamp (YYYYMMDD-HHMMSS), not tutorial- prefix.
        self.assertRegex(ts_dir.name, r'^\d{8}-\d{6}(-\d+)?$',
                         msg=f'non-tutorial dir name should be timestamp: {ts_dir.name}')

    def test_tutorial_step_verification_advances(self):
        """TUT-06 + Task 2 GREEN: successful step 1 verification fires `✓ zaliczone — krok 1/8` and auto-advances to step 2."""
        r = subprocess.run(
            [sys.executable, os.path.join(_PROJECT_ROOT, 'sph_sim.py'), '--interactive'],
            input='tutorial\nrun naive zeta=0.75\nexit\nexit\n',
            capture_output=True,
            text=True,
            timeout=180,
            cwd=self._tmpdir,
            env={**os.environ, 'SPHSIM_NO_REPORT': ''},
        )
        self.assertEqual(r.returncode, 0,
                         msg=f'REPL crashed rc={r.returncode}, stderr={r.stderr[:600]}')
        self.assertIn('✓ zaliczone — krok 1/8', r.stdout,
                      msg=f'step 1 verification not fired: {r.stdout[-2000:]}')
        self.assertIn('[krok 2/8', r.stdout,
                      msg=f'auto-advance to step 2 not visible: {r.stdout[-2000:]}')

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
