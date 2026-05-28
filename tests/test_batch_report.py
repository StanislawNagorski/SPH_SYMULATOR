"""
Unit i integration tests dla Phase 7 — batch markdown + plot (BATCH-03, PLOT-04).

Pokrywa 2 klasy:
  1. TestBatchReport  — render_batch_report składa:
                        Title + Konfiguracja + Strategia + Per-seed table
                        + Aggregate + Wykresy + Werdykt.
                        Linki ![](batch_aggregate.png).
                        5 metod (per VALIDATION.md), w tym test_baseline_verdict_n1
                        (Warning #7 mitigation — N=1 disclaimer path).
  2. TestBatchPlots   — plot_batch_aggregate generuje batch_aggregate.png —
                        5 subplotów (1×5), PNG signature, non-zero size,
                        plt.close-in-finally. test_5_panels mockuje plt.subplots
                        i assertuje (nrows, ncols) == (1, 5) — Warning #6
                        mitigation (NOT a PNG-width-byte proxy).

Wszystkie GREEN-owane w Wave 3 — Plan 07-04
(sphsim/report/batch_markdown.py + sphsim/report/plots.py::plot_batch_aggregate).

Stdlib only: unittest + subprocess + json + os + sys + tempfile + shutil + pathlib + argparse.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

PROJECT_ROOT = Path(_PROJECT_ROOT)
MONOLITH = PROJECT_ROOT / 'sph_sim.py'

# Phase 7 batch-report imports — defer-tested at runtime via testSuite execution.
from sphsim.batch.stats import aggregate_kpis
from sphsim.report.batch_markdown import render_batch_report
from sphsim.report.plots import plot_batch_aggregate
from sphsim.report import write_batch_report


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
    """Builds argparse.Namespace with all fields required by render_batch_report."""
    base = dict(
        nU=250, nSUS=20, T=1000, kappa=0.25, alpha=1,
        K0=100.0, K1=120.0,
        phi=[0.1, 0.2, 0.3, 0.4, 1.0],
        rho=[0.5, 0.5, 0.7, 1.5, 3.0],
        seed=42, strategy='naive', no_agent=False, compare_agent=False,
        valuation='window',
        batch=True, seeds=[1, 2, 3], expected_P=100.0,
        json=False, verbose=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def _make_per_seed_results(n=3):
    """N dictów z 5 kluczami KPIS — deterministyczny generator dla testów.

    Wartości avg_val_last100 zaczynają się od 92.0 i rosną o 0.5 per seed —
    dla N≥3 mean(avg_val_last100) ≥ 92.5 > 92.0 (baseline) → ✓ TAK verdict.
    Aby przetestować ✗ NIE, użyj _make_per_seed_results_low().
    """
    return [
        {'avg_val_last100': 92.0 + i*0.5, 'cum_val_total': 92300.0 + i*100,
         'avg_net_profit': 140.0 + i*0.5, 'delivery_ratio': 0.79 + i*0.01,
         'avg_providers_l100': 105.0 + i*0.1}
        for i in range(n)
    ]


def _make_per_seed_results_high(n=3):
    """N dictów z avg_val_last100 ≫ 92.0 — guaranteed ✓ TAK verdict (CI_lower > 92.0)."""
    return [
        {'avg_val_last100': 95.0 + i*0.1, 'cum_val_total': 95000.0 + i*100,
         'avg_net_profit': 150.0 + i*0.5, 'delivery_ratio': 0.85 + i*0.01,
         'avg_providers_l100': 110.0 + i*0.1}
        for i in range(n)
    ]


def _make_per_seed_results_low(n=3):
    """N dictów z avg_val_last100 ≪ 92.0 — guaranteed ✗ NIE verdict (mean ≤ 92.0)."""
    return [
        {'avg_val_last100': 50.0 + i*0.1, 'cum_val_total': 50000.0 + i*100,
         'avg_net_profit': 80.0 + i*0.5, 'delivery_ratio': 0.60 + i*0.01,
         'avg_providers_l100': 75.0 + i*0.1}
        for i in range(n)
    ]


class TestBatchReport(unittest.TestCase):
    """BATCH-03: render_batch_report składa Title + Konfiguracja + Strategia + Per-seed table + Aggregate + Wykresy + Werdykt. Linki ![](batch_aggregate.png)."""

    def setUp(self):
        # Tempdir + SPHSIM_NO_REPORT pop pattern (PATTERNS §2l) — harmless for pure renders,
        # consistency z TestBatchPlots.
        self._orig_cwd = os.getcwd()
        self._tmpdir = tempfile.mkdtemp(prefix='p7_test_batch_report_')
        os.chdir(self._tmpdir)
        self._orig_no_report = os.environ.pop('SPHSIM_NO_REPORT', None)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmpdir, ignore_errors=True)
        if self._orig_no_report is not None:
            os.environ['SPHSIM_NO_REPORT'] = self._orig_no_report

    def test_per_seed_table(self):
        """Section 'Wyniki per seed' present z N+2 rowsami (header + sep + N data rows)."""
        seeds = [1, 2, 3, 4, 5]
        per_seed = _make_per_seed_results(5)
        agg = aggregate_kpis(per_seed)
        args = _make_args(seeds=seeds)
        md = render_batch_report(args, per_seed, agg, {'zeta': 0.75}, 120.0, seeds)

        self.assertIn('## Wyniki per seed', md, "section header missing")
        self.assertIn('| Seed | avg_val_last100', md, "table header missing")
        # Each seed row present — assert via row prefix `| <seed> ` (space-padded).
        for s in seeds:
            self.assertIn(f'| {s} | ', md,
                          msg=f"seed {s} row missing from per-seed table")

    def test_aggregate_table(self):
        """Section 'Agregat statystyczny' present z 5 KPI rowsami."""
        per_seed = _make_per_seed_results(3)
        agg = aggregate_kpis(per_seed)
        md = render_batch_report(_make_args(), per_seed, agg, {'zeta': 0.75}, 120.0, [1, 2, 3])

        self.assertIn('## Agregat statystyczny', md, "section header missing")
        self.assertIn('| KPI | mean | std | min | max | 95% CI | N |', md,
                      "aggregate table header missing")
        # All 5 KPIS must appear as row prefixes.
        for kpi in ('avg_val_last100', 'cum_val_total', 'avg_net_profit',
                    'delivery_ratio', 'avg_providers_l100'):
            self.assertIn(f'| {kpi} |', md,
                          msg=f"KPI '{kpi}' row missing from aggregate table")

    def test_baseline_verdict(self):
        """N≥2 verdict path: ✓ TAK when CI_lower > baseline_avg; ✗ NIE otherwise."""
        # High case — values clustered around 95.0 (baseline = 92.0) → CI_lower > 92.0.
        per_seed_high = _make_per_seed_results_high(5)
        agg_high = aggregate_kpis(per_seed_high)
        md_high = render_batch_report(_make_args(), per_seed_high, agg_high,
                                      {'zeta': 0.75}, 120.0, [1, 2, 3, 4, 5])
        self.assertIn('## Werdykt: bije baseline', md_high, "verdict section missing (high case)")
        self.assertIn('✓', md_high, "expected ✓ glyph in high-value verdict")
        self.assertIn('TAK', md_high, "expected 'TAK' in high-value verdict")

        # Low case — values around 50.0 → CI_lower ≪ 92.0 → ✗ NIE.
        per_seed_low = _make_per_seed_results_low(5)
        agg_low = aggregate_kpis(per_seed_low)
        md_low = render_batch_report(_make_args(), per_seed_low, agg_low,
                                     {'zeta': 0.75}, 120.0, [1, 2, 3, 4, 5])
        self.assertIn('## Werdykt: bije baseline', md_low, "verdict section missing (low case)")
        self.assertIn('✗', md_low, "expected ✗ glyph in low-value verdict")
        self.assertIn('NIE', md_low, "expected 'NIE' in low-value verdict")

    def test_baseline_verdict_n1(self):
        """Warning #7 mitigation: N=1 falls back to mean comparison + emits Polish disclaimer.

        Stresses the degenerate-aggregate path where AggregateStat.ci_lower is None.
        Asserts BOTH the verdict glyph (✓/✗) AND the literal disclaimer substring.
        """
        per_seed = _make_per_seed_results(1)  # N=1 → ci_lower=ci_upper=None
        agg = aggregate_kpis(per_seed)
        # Sanity: AggregateStat for N=1 must have ci_lower=None (preconditions for this path).
        self.assertIsNone(agg['avg_val_last100'].ci_lower,
                          msg="N=1 sanity: avg_val_last100.ci_lower should be None")

        md = render_batch_report(_make_args(seeds=[1]), per_seed, agg,
                                 {'zeta': 0.75}, 120.0, [1])

        # Verdict section header still present.
        self.assertIn('## Werdykt: bije baseline', md,
                      "verdict section header missing in N=1 path")
        # Verdict line must contain ✓ TAK or ✗ NIE (point-estimate comparison).
        self.assertTrue('✓ TAK' in md or '✗ NIE' in md,
                        msg="N=1 verdict missing both ✓ TAK and ✗ NIE glyph-words")
        # Warning #7 — explicit disclaimer literal.
        self.assertIn('N=1: brak CI, werdykt na podstawie pojedynczego punktu', md,
                      msg="Warning #7: N=1 Polish disclaimer literal missing")

    def test_png_link(self):
        """Section 'Wykresy' links batch_aggregate.png via fixed alt-text + relative path."""
        per_seed = _make_per_seed_results(3)
        agg = aggregate_kpis(per_seed)
        md = render_batch_report(_make_args(), per_seed, agg,
                                 {'zeta': 0.75}, 120.0, [1, 2, 3])

        self.assertIn('![Box-ploty 5 KPI dla N seedów](batch_aggregate.png)', md,
                      "expected PNG link with fixed alt-text + relative path")


class TestBatchPlots(unittest.TestCase):
    """PLOT-04: plot_batch_aggregate generuje batch_aggregate.png — 5 subplotów (1×5), PNG signature, non-zero size, plt.close-in-finally."""

    def setUp(self):
        self._orig_cwd = os.getcwd()
        self._tmpdir = tempfile.mkdtemp(prefix='p7_test_batch_plots_')
        os.chdir(self._tmpdir)
        self._orig_no_report = os.environ.pop('SPHSIM_NO_REPORT', None)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmpdir, ignore_errors=True)
        if self._orig_no_report is not None:
            os.environ['SPHSIM_NO_REPORT'] = self._orig_no_report

    def test_png_exists(self):
        """plot_batch_aggregate writes a valid PNG (signature + ≥10KB size)."""
        per_seed = _make_per_seed_results(5)
        path = Path(self._tmpdir) / 'test.png'
        plot_batch_aggregate(per_seed, path)

        self.assertTrue(path.exists(), f"PNG file not created: {path}")
        data = path.read_bytes()
        self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n',
                         msg="PNG signature mismatch (first 8 bytes)")
        self.assertGreater(len(data), 10000,
                           msg=f"PNG too small ({len(data)} bytes); expected ≥10KB")

    def test_5_panels(self):
        """Warning #6 mitigation: assert plt.subplots called with (nrows=1, ncols=5).

        Uses unittest.mock.patch on the namespace where plt.subplots is LOOKED UP
        ('sphsim.report.plots.plt.subplots') — NOT where it's defined. wraps=...
        keeps the real function running so the figure is actually created and the
        PNG is written. Accepts both positional (1, 5, ...) and kwarg
        (nrows=1, ncols=5, ...) calling conventions.
        """
        per_seed = _make_per_seed_results(5)
        path = Path(self._tmpdir) / 'out.png'

        import matplotlib.pyplot as real_plt
        with patch('sphsim.report.plots.plt.subplots',
                   wraps=real_plt.subplots) as mock_subplots:
            plot_batch_aggregate(per_seed, path)
            mock_subplots.assert_called_once()
            call_args, call_kwargs = mock_subplots.call_args
            # Robust to positional vs kwarg calling convention.
            nrows = call_args[0] if len(call_args) > 0 else call_kwargs.get('nrows', 1)
            ncols = call_args[1] if len(call_args) > 1 else call_kwargs.get('ncols', 1)
            self.assertEqual(
                (nrows, ncols), (1, 5),
                msg=(f'expected (1, 5) subplot grid (Warning #6 contract); '
                     f'got ({nrows}, {ncols}); args={call_args}, kwargs={call_kwargs}'),
            )


if __name__ == '__main__':
    unittest.main()
