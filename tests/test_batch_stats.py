"""
Unit tests dla sphsim.batch.stats (Phase 7, BATCH-02). Pure-unit — no subprocess.

Pokrywa 5 klas, każda jeden skip-placeholder (RED-W0):
  1. TestAggregateKpis      — mean/std/min/max poprawne; std używa ddof=1
  2. TestCIComputation      — 95% CI zgodne z scipy.stats.t.interval
  3. TestN1Degenerate       — N=1 std=0, ci_lower=None, ci_upper=None
  4. TestEmptyInput         — N=0 rzuca ValueError z polskim komunikatem
  5. TestStatsDeterminism   — ten sam input → byte-identical AggregateStat dict

Wszystkie GREEN-owane w Wave 1 — Plan 07-01 (sphsim/batch/stats.py::aggregate_kpis).

Stdlib only: unittest + os + sys (zgodne z PROJECT.md constraint).
"""
import unittest
import os, sys

# Pozwól uruchamiać test bezpośrednio: `python tests/test_batch_stats.py`
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class TestAggregateKpis(unittest.TestCase):
    """BATCH-02: mean/std/min/max poprawne dla znanych próbek; std używa ddof=1 (sample, nie population)."""

    def test_placeholder(self):
        self.skipTest("Wave 1 — Plan 07-01 — sphsim/batch/stats.py::aggregate_kpis")


class TestCIComputation(unittest.TestCase):
    """BATCH-02: 95% CI dla N≥2 zgodne z scipy.stats.t.interval (hand-calc dla N=10); synthetic coverage dla N=100 normals."""

    def test_placeholder(self):
        self.skipTest("Wave 1 — Plan 07-01 — scipy.stats.t.interval w aggregate_kpis")


class TestN1Degenerate(unittest.TestCase):
    """BATCH-02: N=1 nie crashuje — std=0.0, ci_lower=None, ci_upper=None; mean=min=max=jedyna wartość."""

    def test_placeholder(self):
        self.skipTest("Wave 1 — Plan 07-01 — N=1 guard PRZED values.std(ddof=1)")


class TestEmptyInput(unittest.TestCase):
    """BATCH-02: aggregate_kpis([]) rzuca ValueError z polskim komunikatem (orkiestrator filtruje pusty input wcześniej)."""

    def test_placeholder(self):
        self.skipTest("Wave 1 — Plan 07-01 — ValueError dla empty input")


class TestStatsDeterminism(unittest.TestCase):
    """BATCH-02: ten sam input list[dict] → byte-identical dict[AggregateStat] (no random, no global state)."""

    def test_placeholder(self):
        self.skipTest("Wave 1 — Plan 07-01 — pure-function aggregate_kpis")


if __name__ == '__main__':
    unittest.main()
