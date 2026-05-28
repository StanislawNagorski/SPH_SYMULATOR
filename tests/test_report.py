"""
Unit i integration tests dla Phase 6 — markdown side (REPORT-01..03, PLOT-03, SC#6).
Klasy: TestReportFiles, TestReportSections, TestReportCompareMode, TestPlotLinks, TestJsonStdoutClean.
Stdlib only: unittest + subprocess + json + os + sys + tempfile + pathlib.
"""
import json, os, subprocess, sys, unittest
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


class TestReportFiles(unittest.TestCase):
    """REPORT-01: ./reports/<ts>/ utworzony z 3 plikami; env var SPHSIM_NO_REPORT=1 opt-out; mkdir collision suffiks -N."""

    def test_placeholder(self):
        self.skipTest("Wave 3 — Plan 04 — REPORT-01 entry-point + mkdir + opt-out wiring")


class TestReportSections(unittest.TestCase):
    """REPORT-02: report.md zawiera 6 sekcji H2 (Konfiguracja, Strategia, KPI, Rozkład, Wykresy, Baseline) + 5 wierszy KPI + baseline row."""

    def test_placeholder(self):
        self.skipTest("Wave 2 — Plan 02 — markdown.py render_report sekcje 1-6")


class TestReportCompareMode(unittest.TestCase):
    """REPORT-03: --compare-agent dodaje sekcję 7 z delta KPI (with-agent vs without-agent) + werdykt agent_helps."""

    def test_placeholder(self):
        self.skipTest("Wave 3 — Plan 04 — compare-mode wiring + render_compare_section")


class TestPlotLinks(unittest.TestCase):
    """PLOT-03: report.md zawiera relatywne MD image links ![Rozkład decyzji](decision_distribution.png) + ![Przebieg KPI](kpi_timeseries.png)."""

    def test_placeholder(self):
        self.skipTest("Wave 2 — Plan 02 — _render_plots_section emits relative MD links")


class TestJsonStdoutClean(unittest.TestCase):
    """SC#6 (kompatybilność v1.0): --json stdout parsuje się jako JSON nawet gdy report banner trafia na stderr — Pitfall 3 mitigation."""

    def test_placeholder(self):
        self.skipTest("Wave 3 — Plan 04 — banner-on-stderr wiring + Plan 05 verify_phase6.sh JSON check")


if __name__ == '__main__':
    unittest.main()
