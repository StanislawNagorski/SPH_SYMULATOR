"""
Unit i integration tests dla Phase 6 — PNG side (PLOT-01, PLOT-02).
Klasy: TestPlots, TestPlotDimensions. Wydzielony z test_report.py żeby Plan 02/03 mogły lądować parallel bez konfliktu mergem.
Stdlib only: unittest + subprocess + json + os + sys + tempfile + pathlib.
"""
import json, os, subprocess, sys, tempfile, unittest
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


_PNG_MAGIC = b'\x89PNG\r\n\x1a\n'


def _build_fake_decision_data():
    """Mock inputs dla plot_decision_distribution — 4 fazy z różnymi count'ami."""
    return (
        {1: {'commits': 100}, 2: {'commits': 80}, 3: {'commits': 60}, 4: {'commits': 40}},
        {1: 5, 2: 3, 3: 0, 4: 1},      # veto_per_phase
        {1: 12, 2: 8, 3: 5, 4: 2},      # abstain_per_phase
    )


def _build_fake_history(T=1000):
    """Mock history dict z 'val' + 'providers' długości T."""
    return {
        'val':       [50.0 + (i * 0.05 % 50) for i in range(T)],
        'providers': [100 + (i % 30)         for i in range(T)],
    }


class TestPlots(unittest.TestCase):
    """PLOT-01 + PLOT-02: PNG existence + non-zero size + valid PNG signature."""

    def setUp(self):
        from sphsim.report.plots import plot_decision_distribution, plot_kpi_timeseries
        self.plot_decision = plot_decision_distribution
        self.plot_timeseries = plot_kpi_timeseries

    def test_decision_distribution_creates_valid_png(self):
        """PLOT-01: PNG istnieje + > 1 KB + walidny PNG header."""
        ic, veto, abst = _build_fake_decision_data()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'decision_distribution.png'
            self.plot_decision(ic, veto, abst, path)
            self.assertTrue(path.exists(), msg=f"PNG not created at {path}")
            size = path.stat().st_size
            self.assertGreater(size, 1000,
                               msg=f"PNG too small ({size} bytes) — matplotlib likely failed")
            with open(path, 'rb') as f:
                hdr = f.read(8)
            self.assertEqual(hdr, _PNG_MAGIC,
                             msg=f"Bad PNG signature: {hdr!r} (expected {_PNG_MAGIC!r})")

    def test_kpi_timeseries_creates_valid_png(self):
        """PLOT-02: PNG istnieje + > 1 KB + walidny PNG header."""
        history = _build_fake_history(T=1000)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'kpi_timeseries.png'
            self.plot_timeseries(history, 1000, path)
            self.assertTrue(path.exists(), msg=f"PNG not created at {path}")
            self.assertGreater(path.stat().st_size, 1000,
                               msg=f"PNG too small")
            with open(path, 'rb') as f:
                self.assertEqual(f.read(8), _PNG_MAGIC, msg="Bad PNG signature")

    def test_decision_distribution_handles_empty_inputs(self):
        """Robustness: empty dicts → fallback do faz [1,2,3,4], wciąż zapisuje PNG (nie crash)."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'decision_distribution.png'
            self.plot_decision({}, {}, {}, path)   # all empty
            self.assertTrue(path.exists(),
                            msg="empty inputs powinny wciąż dać PNG (defensive fallback faz [1,2,3,4])")
            self.assertGreater(path.stat().st_size, 1000)

    def test_kpi_timeseries_silent_skip_on_empty_history(self):
        """Robustness: brak history / brak kluczy → return cicho, NIE crash (write_report log warning)."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'kpi_timeseries.png'
            self.plot_timeseries({}, 1000, path)  # empty history
            self.assertFalse(path.exists(),
                             msg="empty history powinno dać silent skip — PNG NIE utworzony")
            # And missing 'providers' key:
            self.plot_timeseries({'val': [1, 2, 3]}, 3, path)
            self.assertFalse(path.exists(),
                             msg="brakujący 'providers' powinien dać silent skip")


class TestPlotDimensions(unittest.TestCase):
    """PLOT-02 detail: history T=1000 nie jest truncated — PNG ma rozsądne dimensions."""

    def setUp(self):
        from sphsim.report.plots import plot_kpi_timeseries
        self.plot_timeseries = plot_kpi_timeseries

    def test_kpi_timeseries_size_scales_with_T(self):
        """PNG dla T=1000 powinien mieć więcej bajtów niż dla T=100 (mata danych — większy plik)."""
        with tempfile.TemporaryDirectory() as tmp:
            p_short = Path(tmp) / 'short.png'
            p_long = Path(tmp) / 'long.png'
            self.plot_timeseries(_build_fake_history(T=100), 100, p_short)
            self.plot_timeseries(_build_fake_history(T=1000), 1000, p_long)
            size_short = p_short.stat().st_size
            size_long = p_long.stat().st_size
            # Both should be non-trivial:
            self.assertGreater(size_short, 1000)
            self.assertGreater(size_long, 1000)
            # T=1000 plot should be larger (more line points → more PNG data after compression):
            self.assertGreater(size_long, size_short,
                               msg=f"PNG dla T=1000 ({size_long}B) NIE większy niż dla T=100 ({size_short}B) — "
                                   f"prawdopodobnie truncation lub stała figsize bez data fidelity")

    def test_kpi_timeseries_dimensions_via_pillow_optional(self):
        """Opcjonalny Pillow probe — sprawdza width × height ≥ 1000×500 dla figsize=(10,5) dpi=120."""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow not installed — file-size proxy already covers basic correctness')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'kpi_timeseries.png'
            self.plot_timeseries(_build_fake_history(T=1000), 1000, path)
            with Image.open(path) as img:
                w, h = img.size
            # figsize=(10,5) dpi=120 → minimum 1000×500 (real PNG should be ~1200×600).
            self.assertGreaterEqual(w, 1000,
                                    msg=f"PNG width {w}px < 1000px — figsize/dpi nie zastosowane")
            self.assertGreaterEqual(h, 500,
                                    msg=f"PNG height {h}px < 500px")


if __name__ == '__main__':
    unittest.main()
