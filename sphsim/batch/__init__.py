"""Phase 7: Batch runner + statystyczna agregacja (BATCH-01..03, PLOT-04)."""
from sphsim.batch.runner import run_batch
from sphsim.batch.stats import aggregate_kpis, AggregateStat, KPIS

__all__ = ['run_batch', 'aggregate_kpis', 'AggregateStat', 'KPIS']
