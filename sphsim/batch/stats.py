"""Phase 7: Statystyki agregatu batchowego (BATCH-02).

Public surface: aggregate_kpis, AggregateStat, KPIS.

Pure-function moduł — zero IO, zero global state, zero random. Wejście to
list[dict[str, float]] (jeden dict per seed), wyjście to dict[str, AggregateStat]
(jeden AggregateStat per KPI). Math kernel używa numpy.std(ddof=1) (sample, nie
population) i scipy.stats.t.interval dla 95% CI z df=n-1.

Kolejność KPIS jest load-bearing — musi odpowiadać sphsim/report/markdown.py::_KPI_ROWS
kolumna 0 (avg_val_last100, cum_val_total, avg_net_profit, delivery_ratio,
avg_providers_l100). Plan 07-04 (raport) odczytuje tę kolejność.

Edge cases:
  - N=0 → ValueError z polskim komunikatem ("pusta lista — nic do agregowania")
  - N=1 → std=0.0, ci_lower=None, ci_upper=None (guard PRZED np.std(ddof=1), by uniknąć RuntimeWarning)
  - N≥2, sem>0 → pełne mean/std/min/max + 95% CI via scipy.stats.t.interval
  - N≥2, sem=0 (wszystkie wartości identyczne) → ci_lower=ci_upper=mean (CI degeneruje do punktu;
    zapobiega NaN-flooding z scipy.stats.t.interval(scale=0))
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
import scipy.stats as st


# Canonical 5-KPI tuple. Kolejność MUSI odpowiadać sphsim/report/markdown.py::_KPI_ROWS
# kolumna 0 — Plan 07-04 (raport batch) iteruje po tej tuple by wyrenderować tabelę.
KPIS: tuple[str, ...] = (
    'avg_val_last100',
    'cum_val_total',
    'avg_net_profit',
    'delivery_ratio',
    'avg_providers_l100',
)


@dataclass
class AggregateStat:
    """Statystyka agregatu jednego KPI po wszystkich seedach (BATCH-02).

    Fields:
        mean:     średnia arytmetyczna z N próbek.
        std:      odchylenie standardowe próby (ddof=1). Dla N=1 == 0.0.
        min:      minimum z N próbek.
        max:      maksimum z N próbek.
        ci_lower: dolna granica 95% przedziału ufności (t-Student, df=n-1).
                  None gdy N=1 (przedział nieokreślony dla pojedynczej próbki).
        ci_upper: górna granica 95% CI. None gdy N=1.
        n:        liczba próbek (==len(per_seed_kpis) z aggregate_kpis).
    """
    mean: float
    std: float                  # ddof=1 (sample std)
    min: float
    max: float
    ci_lower: Optional[float]   # None gdy N=1
    ci_upper: Optional[float]   # None gdy N=1
    n: int

    def ci_str(self, fmt: str = '{:.2f}') -> str:
        """Formatuje CI jako string '(lower, upper)' lub 'n/a (N=k)' gdy degenerate.

        Args:
            fmt: format string dla pojedynczej liczby (default '{:.2f}').

        Returns:
            'n/a (N={self.n})' gdy ci_lower lub ci_upper to None (N=1).
            '({fmt.format(lower)}, {fmt.format(upper)})' w przeciwnym przypadku.
        """
        if self.ci_lower is None or self.ci_upper is None:
            return f'n/a (N={self.n})'
        return f'({fmt.format(self.ci_lower)}, {fmt.format(self.ci_upper)})'


def aggregate_kpis(per_seed_kpis: list[dict[str, float]]) -> dict[str, AggregateStat]:
    """Agreguje per-seed KPI w statystyki (mean/std/min/max/95% CI) — BATCH-02.

    Pure function — deterministyczna, no IO, no global state. Wywołana dwukrotnie
    na tym samym wejściu zwraca byte-identical dict[AggregateStat].

    Args:
        per_seed_kpis: lista N dictów, każdy z 5 kluczami z KPIS i wartością float.
                       N≥1. Dla N=0 funkcja rzuca ValueError.

    Returns:
        dict[str, AggregateStat] z dokładnie 5 kluczami (== KPIS); każdy
        AggregateStat zawiera pełną statystykę (mean/std/min/max/ci_*/n).

    Raises:
        ValueError: gdy per_seed_kpis jest pustą listą (polski komunikat).

    Notes:
        - std używa ddof=1 (sample std, nie population).
        - 95% CI computuje scipy.stats.t.interval(0.95, df=n-1, loc=mean, scale=sem),
          gdzie sem = std / sqrt(n).
        - N=1 jest specjalnym przypadkiem (guard PRZED values.std(ddof=1)), by uniknąć
          RuntimeWarning od numpy (np.std([x], ddof=1) → NaN + warning).
    """
    n = len(per_seed_kpis)
    if n == 0:
        raise ValueError("aggregate_kpis: pusta lista — nic do agregowania.")

    result: dict[str, AggregateStat] = {}
    for kpi in KPIS:
        values = np.array([d[kpi] for d in per_seed_kpis], dtype=float)
        mean = float(values.mean())
        if n == 1:
            # Guard: np.std([x], ddof=1) rzuca RuntimeWarning + zwraca NaN.
            # Dla N=1 std nie jest zdefiniowana — wybieramy 0.0 jako sensowny
            # placeholder (RESEARCH §D.8 verified runtime).
            std = 0.0
            ci_lower: Optional[float] = None
            ci_upper: Optional[float] = None
        else:
            std = float(values.std(ddof=1))
            sem = std / np.sqrt(n)
            if sem == 0.0:
                # Zero-variance edge: wszystkie N≥2 wartości identyczne → sem=0.
                # scipy.stats.t.interval(0.95, df, loc, scale=0) zwraca (NaN, NaN).
                # CI degeneruje do punktu (mean, mean) — matematycznie poprawne
                # i nie psuje dataclass equality (NaN != NaN, więc TestStatsDeterminism by failnął).
                ci_lower = mean
                ci_upper = mean
            else:
                ci_lower_np, ci_upper_np = st.t.interval(0.95, df=n - 1, loc=mean, scale=sem)
                ci_lower = float(ci_lower_np)
                ci_upper = float(ci_upper_np)

        result[kpi] = AggregateStat(
            mean=mean,
            std=std,
            min=float(values.min()),
            max=float(values.max()),
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            n=n,
        )

    return result
