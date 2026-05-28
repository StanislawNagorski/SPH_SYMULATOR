"""
Unit i integration tests dla Phase 6 — markdown side (REPORT-01..03, PLOT-03, SC#6).
Klasy: TestReportFiles, TestReportSections, TestReportCompareMode, TestPlotLinks, TestJsonStdoutClean.
Stdlib only: unittest + subprocess + json + os + sys + tempfile + shutil + pathlib.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

PROJECT_ROOT = Path(_PROJECT_ROOT)
MONOLITH = PROJECT_ROOT / 'sph_sim.py'
_REPORTS_DIR = PROJECT_ROOT / 'reports'


def _run_sph(*args, **kwargs):
    """Subprocess helper — uruchamia sph_sim.py z cwd=_PROJECT_ROOT (mirror tests/test_env.py)."""
    env = {**os.environ, 'SPHSIM_NO_REPORT': kwargs.pop('SPHSIM_NO_REPORT', '1')}
    return subprocess.run(
        [sys.executable, 'sph_sim.py', *args],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        **kwargs,
    )


def _make_args(**overrides):
    """Builds argparse.Namespace with all fields required by render_report."""
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
    """Builds result dict in sim.run() shape — single-run."""
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
    )
    base.update(overrides)
    return base


def _make_compare_res(**overrides):
    """Builds result dict in run_compare shape — {'comparison': {...}}."""
    with_agent = _make_single_res()
    without_agent = _make_single_res(avg_val_last100=85.3, avg_net_profit=120.0)
    delta = {k: with_agent[k] - without_agent[k]
             for k in ('avg_val_last100', 'cum_val_total', 'avg_net_profit',
                       'delivery_ratio', 'avg_providers_l100')}
    return {
        'comparison': {
            'with_agent': with_agent,
            'without_agent': without_agent,
            'delta': delta,
            'agent_helps': True,
        }
    }


class TestReportFiles(unittest.TestCase):
    """REPORT-01: ./reports/<ts>/ utworzony z 3 plikami; env var SPHSIM_NO_REPORT=1 opt-out; mkdir collision suffiks -N."""

    def setUp(self):
        # Lazy-import — wymusza dyspatch przez sphsim.report jako paczkę.
        from sphsim.report import write_report, _resolve_report_dir, _timestamp
        self.write_report = write_report
        self._resolve = _resolve_report_dir
        self._ts = _timestamp
        # Run wszystkie testy w tempdir żeby nie śmiecić w project root.
        self._orig_cwd = os.getcwd()
        self._tmpdir = tempfile.mkdtemp(prefix='p6_test_files_')
        os.chdir(self._tmpdir)
        # Wyczyść env var override z conftest — chcemy żeby tests faktycznie tworzyły reports/.
        self._orig_no_report = os.environ.pop('SPHSIM_NO_REPORT', None)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmpdir, ignore_errors=True)
        if self._orig_no_report is not None:
            os.environ['SPHSIM_NO_REPORT'] = self._orig_no_report

    def test_report_files_created_in_timestamp_dir(self):
        """SC#1: write_report tworzy ./reports/<ts>/ z 3 plikami (report.md + 2 PNG)."""
        res = _make_single_res()
        # history needed for kpi_timeseries.png
        res['history'] = {
            'val':       [50.0 + i * 0.01 for i in range(1000)],
            'providers': [100 + (i % 30)  for i in range(1000)],
        }
        args = _make_args()
        report_dir = self.write_report(args, res, {'zeta': 0.5}, 120.0, mode='single')
        self.assertIsNotNone(report_dir,
                             msg="write_report zwrócił None — pewnie opt-out env var aktywny")
        self.assertTrue(report_dir.exists(), msg=f"report_dir nie istnieje: {report_dir}")
        self.assertTrue((report_dir / 'report.md').exists(), msg="report.md missing")
        self.assertTrue((report_dir / 'decision_distribution.png').exists(),
                        msg="decision_distribution.png missing")
        self.assertTrue((report_dir / 'kpi_timeseries.png').exists(),
                        msg="kpi_timeseries.png missing")

    def test_sphsim_no_report_env_var_disables_generation(self):
        """SC#6: SPHSIM_NO_REPORT=1 → write_report zwraca None, brak reports/ dir."""
        os.environ['SPHSIM_NO_REPORT'] = '1'
        try:
            report_dir = self.write_report(_make_args(), _make_single_res(),
                                           {}, 120.0, mode='single')
            self.assertIsNone(report_dir,
                              msg="opt-out env var nie powstrzymał write_report")
            reports_path = Path('reports')
            self.assertFalse(
                reports_path.exists() and any(reports_path.iterdir()),
                msg="reports/ powstał mimo opt-out",
            )
        finally:
            del os.environ['SPHSIM_NO_REPORT']

    def test_mkdir_collision_appends_suffix(self):
        """RESEARCH §C.7: collision retry suffiks -N gdy <ts>/ już istnieje."""
        ts = self._ts()
        base = Path('reports')
        base.mkdir(exist_ok=True)
        # Pre-create a directory at the timestamp the next call WILL try.
        collision_dir = base / ts
        collision_dir.mkdir(exist_ok=True)
        # Now _resolve_report_dir powinien dać <ts>-2 (lub większy).
        result = self._resolve(base)
        self.assertNotEqual(result, collision_dir,
                            msg="collision dir powinno być różne od pre-existing")
        self.assertTrue(result.name.startswith(ts),
                        msg=f"new dir powinno mieć prefix '{ts}': {result.name}")
        self.assertTrue(result.exists(), msg=f"resolved dir nie istnieje: {result}")
        # Suffix shape: '<ts>-N' (where N >= 2).
        suffix = result.name[len(ts):]
        self.assertTrue(suffix.startswith('-'),
                        msg=f"suffix nie ma '-N' shape: {result.name!r}")
        self.assertTrue(suffix[1:].isdigit(),
                        msg=f"suffix po '-' nie jest liczbą: {result.name!r}")


class TestReportSections(unittest.TestCase):
    """REPORT-02: report.md zawiera 6 sekcji H2 (Konfiguracja, Strategia, KPI, Rozkład, Wykresy, Baseline) + 5 wierszy KPI + baseline row."""

    def setUp(self):
        from sphsim.report import render_report
        self.render_report = render_report

    def test_render_report_emits_all_six_section_headers(self):
        """SC#2: 6 sekcji w kolejności (single mode)."""
        md = self.render_report(_make_args(), _make_single_res(), {'zeta': 0.75}, 120.0, mode='single')
        expected = [
            '## Konfiguracja środowiska',
            '## Strategia i parametry',
            '## Metryki KPI',
            '## Rozkład decyzji per faza',
            '## Wykresy',
            '## Porównanie z baseline',
        ]
        for header in expected:
            self.assertEqual(md.count(header), 1,
                             msg=f"header '{header}' occurs {md.count(header)}x (expected 1)")
        # Section 7 should NOT appear in single mode.
        self.assertNotIn('## Porównanie z RationalAgent', md,
                         msg="compare section leaked into single mode")

    def test_kpi_table_contains_all_five_named_rows(self):
        """SC#2: 5 KPI rows obowiązkowe z ROADMAP."""
        md = self.render_report(_make_args(), _make_single_res(), {}, 120.0, mode='single')
        for kpi in ('avg_val_last100', 'cum_val_total', 'avg_net_profit',
                    'delivery_ratio', 'avg_providers_l100'):
            self.assertIn(f'| {kpi}', md,
                          msg=f"KPI row '{kpi}' missing from MD output")

    def test_baseline_comparison_row_present_for_default_env(self):
        """SC#2: baseline row z fixture obecny."""
        md = self.render_report(_make_args(), _make_single_res(), {}, 120.0, mode='single')
        self.assertIn('| KPI | Bieżący run | Baseline v1.0 | Δ |', md,
                      msg="baseline table header missing")
        self.assertIn('Baseline z `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json`', md,
                      msg="baseline disclaimer missing")
        # The 5 KPI rows from _KPI_ROWS should each appear in the baseline section.
        # Since baseline section uses the same _KPI_ROWS, presence is verified above by test_kpi_table.

    def test_decision_table_uses_abstain_per_phase_from_plan01(self):
        """REPORT-02 + PLOT-01 input: decision table includes ABSTAIN column populated."""
        res = _make_single_res(abstain_per_phase={1: 12, 2: 8, 3: 5, 4: 2})
        md = self.render_report(_make_args(), res, {}, 120.0, mode='single')
        self.assertIn('| Faza | COMMIT | ABSTAIN | VETO | Suma |', md,
                      msg="decision table header missing")
        # At least one row with the abstain values:
        self.assertRegex(md, r'\| 1\s+\| \d+\s+\| 12\s+\| \d+\s+\| \d+\s+\|',
                         msg="phase 1 row missing or abstain count != 12")

    def test_compare_mode_adds_seventh_section(self):
        """REPORT-03: --compare-agent dodaje sekcję 7 z delta KPI."""
        md = self.render_report(_make_args(compare_agent=True),
                                _make_compare_res(), {}, 120.0, mode='compare')
        self.assertIn('## Porównanie z RationalAgent', md,
                      msg="compare section missing in compare mode")
        self.assertIn('| KPI | with-agent | bez agenta | Δ', md,
                      msg="compare delta table header missing")
        self.assertIn('**Werdykt:**', md,
                      msg="werdykt line missing")


class TestReportCompareMode(unittest.TestCase):
    """REPORT-03: --compare-agent dodaje sekcję 7 z delta KPI (with-agent vs without-agent) + werdykt agent_helps."""

    def setUp(self):
        from sphsim.report import write_report
        self.write_report = write_report
        self._orig_cwd = os.getcwd()
        self._tmpdir = tempfile.mkdtemp(prefix='p6_test_compare_')
        os.chdir(self._tmpdir)
        self._orig_no_report = os.environ.pop('SPHSIM_NO_REPORT', None)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmpdir, ignore_errors=True)
        if self._orig_no_report is not None:
            os.environ['SPHSIM_NO_REPORT'] = self._orig_no_report

    def test_compare_mode_writes_report_with_compare_section(self):
        """REPORT-03 SC#5: compare-mode raport zawiera sekcję 7 + delta table."""
        res_compare = _make_compare_res()
        # Add _with_agent_full key (mirror Plan 04 main.py:run_compare edit) — full res with history.
        full = _make_single_res()
        full['history'] = {
            'val':       [50.0 + i * 0.01 for i in range(1000)],
            'providers': [100 + (i % 30)  for i in range(1000)],
        }
        res_compare['_with_agent_full'] = full

        args = _make_args(compare_agent=True)
        report_dir = self.write_report(args, res_compare, {'zeta': 0.5},
                                       120.0, mode='compare')
        self.assertIsNotNone(report_dir, msg="write_report zwrócił None w compare mode")
        md = (report_dir / 'report.md').read_text(encoding='utf-8')
        self.assertIn('## Porównanie z RationalAgent', md,
                      msg="compare section missing in compare-mode report")
        self.assertIn('with-agent', md, msg="with-agent column header missing")
        self.assertIn('bez agenta', md, msg="bez agenta column header missing")
        self.assertIn('**Werdykt:**', md, msg="werdykt line missing")

    def test_compare_mode_pngs_created_from_with_agent_history(self):
        """REPORT-03 + PLOT-02: PNG-i wygenerowane mimo że comparison block strippuje history."""
        res_compare = _make_compare_res()
        full = _make_single_res()
        full['history'] = {
            'val':       [50.0 + i * 0.01 for i in range(1000)],
            'providers': [100 + (i % 30)  for i in range(1000)],
        }
        res_compare['_with_agent_full'] = full
        args = _make_args(compare_agent=True)
        report_dir = self.write_report(args, res_compare, {}, 120.0, mode='compare')
        self.assertIsNotNone(report_dir)
        self.assertTrue((report_dir / 'decision_distribution.png').exists(),
                        msg="decision_distribution.png missing in compare-mode")
        self.assertTrue((report_dir / 'kpi_timeseries.png').exists(),
                        msg="kpi_timeseries.png missing — _with_agent_full threading broken?")
        # PNG non-zero size — confirms it's not the silent-skip empty file.
        self.assertGreater((report_dir / 'kpi_timeseries.png').stat().st_size, 1000,
                           msg="kpi_timeseries.png pusty — history nie dotarła do plot_kpi_timeseries")


class TestPlotLinks(unittest.TestCase):
    """PLOT-03: report.md zawiera relatywne MD image links ![Rozkład decyzji](decision_distribution.png) + ![Przebieg KPI](kpi_timeseries.png)."""

    def setUp(self):
        from sphsim.report import render_report
        self.render_report = render_report

    def test_decision_distribution_link_present_and_relative(self):
        """PLOT-03: link 1/2 — relatywna ścieżka, GitHub/VSCode/Obsidian-renderable."""
        md = self.render_report(_make_args(), _make_single_res(), {}, 120.0, mode='single')
        link = '![Rozkład decyzji per faza](decision_distribution.png)'
        self.assertIn(link, md, msg=f"link missing: {link}")
        # Anti-regression: no absolute path or http:// prefix leaked.
        self.assertNotIn('](/', md, msg="absolute path leaked in MD image link")
        self.assertNotIn('](http', md, msg="HTTP URL leaked in MD image link")

    def test_kpi_timeseries_link_present_and_relative(self):
        """PLOT-03: link 2/2 — relatywna ścieżka."""
        md = self.render_report(_make_args(), _make_single_res(), {}, 120.0, mode='single')
        link = '![Przebieg KPI w czasie](kpi_timeseries.png)'
        self.assertIn(link, md, msg=f"link missing: {link}")


class TestJsonStdoutClean(unittest.TestCase):
    """SC#6 (kompatybilność v1.0): --json stdout parsuje się jako JSON nawet gdy report banner trafia na stderr — Pitfall 3 mitigation."""

    def tearDown(self):
        # Cleanup any reports/ created by subprocess (cwd=_PROJECT_ROOT — banner goes there).
        if _REPORTS_DIR.exists():
            for child in _REPORTS_DIR.iterdir():
                shutil.rmtree(child, ignore_errors=True)

    def test_json_stdout_is_parseable_json_despite_banner(self):
        """SC#6: subprocess --json + banner → stdout to czysty JSON, banner na stderr."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--no-agent',
                     '--seed', '42', '--json',
                     SPHSIM_NO_REPORT='')  # WŁĄCZ raport, żeby banner też się pojawił
        self.assertEqual(r.returncode, 0,
                         msg=f"sph_sim.py exit={r.returncode} stderr={r.stderr[:300]}")
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError as e:
            self.fail(f"--json stdout NIE jest valid JSON: {e}\n"
                      f"stdout repr: {r.stdout[:300]!r}")
        self.assertIn('strategy', data,
                      msg=f"JSON missing 'strategy' key; got keys: {sorted(data.keys())}")
        # Banner powinien być na STDERR.
        self.assertIn('Raport zapisany do:', r.stderr,
                      msg=f"banner NIE w stderr; stderr: {r.stderr[:300]!r}")

    def test_format_json_strips_with_agent_full_underscore_key(self):
        """format_json filter MUST skip underscore-prefixed top-level keys (Phase 6 SC#6 + RESEARCH §N.1)."""
        from sphsim.cli.output import format_json
        res = {
            'avg_val_last100': 92.0, 'cum_val_total': 92300.0,
            'avg_net_profit': 140.7592, 'delivery_ratio': 0.7931,
            'avg_providers_l100': 105.03, 'sus_final': 1,
            'ic_per_phase': {}, 'veto_per_phase': {}, 'n_vetoed_total': 0,
            'abstain_per_phase': {},
            'history': {}, 'devices': [],
            '_with_agent_full': {'should': 'not appear in JSON'},
        }
        args = _make_args()
        json_str = format_json(args, res, {}, 120.0)
        data = json.loads(json_str)
        # _with_agent_full ląduje wewnątrz 'metrics' — sprawdź tam.
        self.assertIn('metrics', data)
        self.assertNotIn('_with_agent_full', data['metrics'],
                         msg=f"underscore key leaked into JSON metrics: "
                             f"{sorted(data['metrics'].keys())}")
        # Sanity — top-level też nie powinien mieć.
        self.assertNotIn('_with_agent_full', data,
                         msg=f"underscore key leaked top-level: {sorted(data.keys())}")


if __name__ == '__main__':
    unittest.main()
