"""
Unit i integration tests dla Phase 6 — markdown side (REPORT-01..03, PLOT-03, SC#6).
Klasy: TestReportFiles, TestReportSections, TestReportCompareMode, TestPlotLinks, TestJsonStdoutClean.
Stdlib only: unittest + subprocess + json + os + sys + tempfile + pathlib.
"""
import argparse, json, os, subprocess, sys, unittest
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

    def test_placeholder(self):
        self.skipTest("Wave 3 — Plan 04 — REPORT-01 entry-point + mkdir + opt-out wiring")


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

    def test_placeholder(self):
        self.skipTest("Wave 3 — Plan 04 — compare-mode wiring + render_compare_section")


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

    def test_placeholder(self):
        self.skipTest("Wave 3 — Plan 04 — banner-on-stderr wiring + Plan 05 verify_phase6.sh JSON check")


if __name__ == '__main__':
    unittest.main()
