"""
Unit tests dla sphsim.batch.stats (Phase 7, BATCH-02). Pure-unit — no subprocess.

Pokrywa 5 klas, 9 metod (GREEN — Wave 1, Plan 07-01):
  1. TestAggregateKpis      — mean/std/min/max poprawne; std używa ddof=1 (3 testy)
  2. TestCIComputation      — 95% CI zgodne z scipy.stats.t.interval (2 testy)
  3. TestN1Degenerate       — N=1 std=0, ci_lower=None, ci_upper=None (2 testy)
  4. TestEmptyInput         — N=0 rzuca ValueError z polskim komunikatem (1 test)
  5. TestStatsDeterminism   — ten sam input → byte-identical AggregateStat dict (1 test)

Implementuje sphsim/batch/stats.py::aggregate_kpis (Plan 07-01).

Stdlib only: unittest + os + sys + random + warnings (zgodne z PROJECT.md constraint).
"""
import unittest
import os
import sys
import random
import warnings

# Pozwól uruchamiać test bezpośrednio: `python tests/test_batch_stats.py`
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sphsim.batch.stats import aggregate_kpis, AggregateStat, KPIS


# Canonical 10-element próbka (hand-computed values: mean=91.95, sample_std≈0.2953).
# Re-used przez TestAggregateKpis.test_known_values i TestCIComputation.test_ci_against_manual.
_CANONICAL_AVL = [91.5, 92.0, 91.8, 92.3, 91.9, 92.1, 91.7, 92.2, 91.6, 92.4]


def _make_seed_dict(avl: float) -> dict:
    """Helper: buduje pojedynczy dict per-seed z `avl` jako avg_val_last100 i fixed pozostałe 4 KPI."""
    return {
        'avg_val_last100': avl,
        'cum_val_total': 92000.0,
        'avg_net_profit': 140.0,
        'delivery_ratio': 0.79,
        'avg_providers_l100': 105.0,
    }


class TestAggregateKpis(unittest.TestCase):
    """BATCH-02: mean/std/min/max poprawne dla znanych próbek; std używa ddof=1 (sample, nie population)."""

    def test_known_values(self):
        """(1) Dla canonical 10-element sample: mean=91.95, min=91.5, max=92.4, std≈0.302765 (ddof=1)."""
        per_seed = [_make_seed_dict(v) for v in _CANONICAL_AVL]
        result = aggregate_kpis(per_seed)

        self.assertEqual(result['avg_val_last100'].n, 10,
                         msg=f"n musi == 10, got {result['avg_val_last100'].n}")
        self.assertAlmostEqual(result['avg_val_last100'].mean, 91.95, places=4,
                               msg=f"mean: oczekiwane 91.95, got {result['avg_val_last100'].mean}")
        self.assertAlmostEqual(result['avg_val_last100'].min, 91.5, places=4,
                               msg=f"min: oczekiwane 91.5, got {result['avg_val_last100'].min}")
        self.assertAlmostEqual(result['avg_val_last100'].max, 92.4, places=4,
                               msg=f"max: oczekiwane 92.4, got {result['avg_val_last100'].max}")
        # Hand-check: std (ddof=1) dla canonical sample ≈ 0.302765
        # (RESEARCH §D.6 interfaces block — runtime numpy/scipy ground truth).
        # PLAN comment "0.2953" in §interfaces was a hand-arithmetic typo; actual
        # numpy.std(ddof=1) returns 0.302765... — Rule 1 deviation: test asserts truth.
        self.assertAlmostEqual(result['avg_val_last100'].std, 0.302765, places=4,
                               msg=f"std (ddof=1): oczekiwane 0.302765, got {result['avg_val_last100'].std}")

    def test_all_5_kpis_present(self):
        """(2) result.keys() == set(KPIS); len(KPIS) == 5; każdy result[k] to AggregateStat."""
        per_seed = [_make_seed_dict(91.5), _make_seed_dict(92.5)]
        result = aggregate_kpis(per_seed)

        self.assertEqual(set(result.keys()), set(KPIS),
                         msg=f"keys: oczekiwane {set(KPIS)}, got {set(result.keys())}")
        self.assertEqual(len(KPIS), 5,
                         msg=f"len(KPIS) musi == 5, got {len(KPIS)}")
        for k in KPIS:
            self.assertIsInstance(result[k], AggregateStat,
                                  msg=f"result[{k!r}] musi być AggregateStat, got {type(result[k])}")

    def test_std_uses_ddof_1(self):
        """(3) Sample [1,2,3,4,5]: ddof=1 std ≈ 1.5811 (sqrt(2.5)); population std ≈ 1.4142 (sqrt(2.0))."""
        per_seed = [_make_seed_dict(v) for v in [1.0, 2.0, 3.0, 4.0, 5.0]]
        result = aggregate_kpis(per_seed)

        # ddof=1 sample std: sqrt(sum((x-mean)^2) / (n-1)) = sqrt(10/4) = sqrt(2.5) ≈ 1.5811
        self.assertAlmostEqual(result['avg_val_last100'].std, 1.5811, places=3,
                               msg=f"std (ddof=1): oczekiwane 1.5811 (sample, nie 1.4142 population), "
                                   f"got {result['avg_val_last100'].std}")


class TestCIComputation(unittest.TestCase):
    """BATCH-02: 95% CI dla N≥2 zgodne z scipy.stats.t.interval (hand-calc dla N=10); synthetic coverage dla N=100 normals."""

    def test_ci_against_manual(self):
        """(4) Canonical N=10 próbka: ci_lower≈91.733, ci_upper≈92.167 (t_crit df=9 ≈ 2.2622, sem≈0.09574)."""
        per_seed = [_make_seed_dict(v) for v in _CANONICAL_AVL]
        result = aggregate_kpis(per_seed)

        # Hand-calc (runtime ground truth — scipy 1.16, numpy 2.3):
        #   mean = 91.95, sample_std ≈ 0.302765, sem = 0.302765/sqrt(10) ≈ 0.095743
        #   t_critical (df=9, two-sided 95%) ≈ 2.262157
        #   ci_lower ≈ 91.95 - 2.262157*0.095743 ≈ 91.7334
        #   ci_upper ≈ 91.95 + 2.262157*0.095743 ≈ 92.1666
        # Tolerance places=2 (Pitfall 3 — BLAS variance across scipy versions).
        self.assertAlmostEqual(result['avg_val_last100'].ci_lower, 91.733, places=2,
                               msg=f"ci_lower: oczekiwane ≈91.733, got {result['avg_val_last100'].ci_lower}")
        self.assertAlmostEqual(result['avg_val_last100'].ci_upper, 92.167, places=2,
                               msg=f"ci_upper: oczekiwane ≈92.167, got {result['avg_val_last100'].ci_upper}")

    def test_ci_brackets_true_mean_synthetic(self):
        """(5) Single deterministic draw (random.seed(123), N=100, N(92.0, 2.5)): true mean 92.0 leży w 95% CI; mean leży we własnym CI."""
        random.seed(123)
        samples = [random.gauss(92.0, 2.5) for _ in range(100)]
        per_seed = [_make_seed_dict(v) for v in samples]
        result = aggregate_kpis(per_seed)

        stat = result['avg_val_last100']
        # Sanity: oba CI bounds powinny być nie-None dla N=100.
        self.assertIsNotNone(stat.ci_lower, msg="ci_lower musi być float dla N=100")
        self.assertIsNotNone(stat.ci_upper, msg="ci_upper musi być float dla N=100")

        # Single-draw sanity (NIE 95%-coverage-over-many-samples — tylko jeden duży draw):
        # True mean 92.0 powinien leżeć w przedziale ufności dla N=100, mu=92.0, sigma=2.5.
        self.assertLess(stat.ci_lower, 92.0,
                        msg=f"ci_lower musi być < true mean 92.0, got ci_lower={stat.ci_lower}")
        self.assertGreater(stat.ci_upper, 92.0,
                           msg=f"ci_upper musi być > true mean 92.0, got ci_upper={stat.ci_upper}")

        # Mean ZAWSZE leży we własnym CI dla two-sided t-interval (matematyczna definicja).
        self.assertLess(stat.ci_lower, stat.mean,
                        msg=f"ci_lower < mean: {stat.ci_lower} < {stat.mean}")
        self.assertGreater(stat.ci_upper, stat.mean,
                           msg=f"ci_upper > mean: {stat.ci_upper} > {stat.mean}")


class TestN1Degenerate(unittest.TestCase):
    """BATCH-02: N=1 nie crashuje — std=0.0, ci_lower=None, ci_upper=None; mean=min=max=jedyna wartość."""

    def test_n1_no_warning(self):
        """(6) Pod warnings.simplefilter('error') aggregate_kpis dla N=1 NIE rzuca RuntimeWarning (guard PRZED np.std)."""
        with warnings.catch_warnings():
            warnings.simplefilter('error')  # konwertuje wszystkie warningi na exceptions
            # Jeśli guard zawodzi, np.std([42.0], ddof=1) rzuci RuntimeWarning → exception.
            result = aggregate_kpis([{k: 42.0 for k in KPIS}])
            # Sanity guard działa: std jest 0.0 (nie NaN).
            self.assertEqual(result['avg_val_last100'].std, 0.0,
                             msg=f"N=1 std musi być 0.0, got {result['avg_val_last100'].std}")

    def test_n1_field_values(self):
        """(7) Dla N=1 wszystkie 5 KPI: n=1, std=0.0, mean=min=max=42.0, ci_lower=ci_upper=None, ci_str()='n/a (N=1)'."""
        result = aggregate_kpis([{k: 42.0 for k in KPIS}])

        for kpi in KPIS:
            stat = result[kpi]
            self.assertEqual(stat.n, 1, msg=f"{kpi}: n musi == 1, got {stat.n}")
            self.assertEqual(stat.std, 0.0, msg=f"{kpi}: std musi == 0.0, got {stat.std}")
            self.assertEqual(stat.mean, 42.0, msg=f"{kpi}: mean musi == 42.0, got {stat.mean}")
            self.assertEqual(stat.min, 42.0, msg=f"{kpi}: min musi == 42.0, got {stat.min}")
            self.assertEqual(stat.max, 42.0, msg=f"{kpi}: max musi == 42.0, got {stat.max}")
            self.assertIsNone(stat.ci_lower, msg=f"{kpi}: ci_lower musi być None dla N=1, got {stat.ci_lower}")
            self.assertIsNone(stat.ci_upper, msg=f"{kpi}: ci_upper musi być None dla N=1, got {stat.ci_upper}")
            self.assertEqual(stat.ci_str(), 'n/a (N=1)',
                             msg=f"{kpi}: ci_str() musi == 'n/a (N=1)', got {stat.ci_str()!r}")


class TestEmptyInput(unittest.TestCase):
    """BATCH-02: aggregate_kpis([]) rzuca ValueError z polskim komunikatem (orkiestrator filtruje pusty input wcześniej)."""

    def test_n0_raises_value_error(self):
        """(8) aggregate_kpis([]) rzuca ValueError z 'pusta' w komunikacie (Polish — RESEARCH §D.6)."""
        with self.assertRaises(ValueError) as ctx:
            aggregate_kpis([])

        msg = str(ctx.exception)
        self.assertIn('pusta', msg,
                      msg=f"ValueError msg musi zawierać 'pusta', got {msg!r}")


class TestStatsDeterminism(unittest.TestCase):
    """BATCH-02: ten sam input list[dict] → byte-identical dict[AggregateStat] (no random, no global state)."""

    def test_same_input_byte_identical(self):
        """(9) Dwa wywołania aggregate_kpis(per_seed) zwracają equal-by-dataclass AggregateStat dla każdego z 5 KPI."""
        per_seed = [_make_seed_dict(v) for v in _CANONICAL_AVL]

        r1 = aggregate_kpis(per_seed)
        r2 = aggregate_kpis(per_seed)

        for kpi in KPIS:
            self.assertEqual(r1[kpi], r2[kpi],
                             msg=f"{kpi}: r1 != r2 (dataclass equality compares all fields); "
                                 f"r1={r1[kpi]!r} r2={r2[kpi]!r}")


if __name__ == '__main__':
    unittest.main()
