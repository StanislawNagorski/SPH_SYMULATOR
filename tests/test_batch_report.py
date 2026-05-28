"""
Unit i integration tests dla Phase 7 — batch markdown + plot (BATCH-03, PLOT-04).

Pokrywa 2 klasy, każda jeden skip-placeholder (RED-W0):
  1. TestBatchReport  — render_batch_report składa:
                        Title + Konfiguracja + Strategia + Per-seed table
                        + Aggregate + Wykresy + Werdykt.
                        Linki ![](batch_aggregate.png).
  2. TestBatchPlots   — plot_batch_aggregate generuje batch_aggregate.png —
                        5 subplotów (1×5), PNG signature, non-zero size,
                        plt.close-in-finally.

Wszystkie GREEN-owane w Wave 3 — Plan 07-04
(sphsim/report/batch_markdown.py + sphsim/report/plots.py::plot_batch_aggregate).

Stdlib only: unittest + subprocess + json + os + sys + tempfile + pathlib.
"""
import json, os, subprocess, sys, unittest
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

PROJECT_ROOT = Path(_PROJECT_ROOT)
MONOLITH = PROJECT_ROOT / 'sph_sim.py'


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


class TestBatchReport(unittest.TestCase):
    """BATCH-03: render_batch_report składa Title + Konfiguracja + Strategia + Per-seed table + Aggregate + Wykresy + Werdykt. Linki ![](batch_aggregate.png)."""

    def test_placeholder(self):
        self.skipTest("Wave 3 — Plan 07-04 — sphsim/report/batch_markdown.py")


class TestBatchPlots(unittest.TestCase):
    """PLOT-04: plot_batch_aggregate generuje batch_aggregate.png — 5 subplotów (1×5), PNG signature, non-zero size, plt.close-in-finally."""

    def test_placeholder(self):
        self.skipTest("Wave 3 — Plan 07-04 — sphsim/report/plots.py::plot_batch_aggregate")


if __name__ == '__main__':
    unittest.main()
