# Device — autonomiczne urządzenie z mutowalnym stanem (fazy 1..F-1).
# Skopiowane VERBATIM z sph_sim.py:84–118 (v1.0). Zachowane wszystkie 10 pól,
# __post_init__ inicjalizujący phase_stats={}, 3 metody record_*,
# property net_profit. Schema słownika phase_stats:
# {commits, deliveries, failures, earnings, costs}.
from dataclasses import dataclass


@dataclass
class Device:
    id: int
    phase: int   # 1..F-1 gdy UP, -1 gdy DOWN
    status: str  # 'UP' | 'DOWN'
    down_left: int = 0
    earnings: float = 0.0
    costs: float = 0.0
    n_commit: int = 0
    n_abstain: int = 0
    n_delivered: int = 0
    n_failed: int = 0
    n_vetoed: int = 0

    def __post_init__(self):
        # Per-phase IC tracking: phase -> {commits, deliveries, failures, earnings, costs}
        self.phase_stats = {}
        self.veto_phase_stats = {}  # {phase: count} — Phase 4 D-64

    def record_commit(self, phase, cost):
        s = self.phase_stats.setdefault(phase, {'commits': 0, 'deliveries': 0, 'failures': 0, 'earnings': 0.0, 'costs': 0.0})
        s['commits'] += 1
        s['costs'] += cost

    def record_delivery(self, phase, payment):
        s = self.phase_stats.setdefault(phase, {'commits': 0, 'deliveries': 0, 'failures': 0, 'earnings': 0.0, 'costs': 0.0})
        s['deliveries'] += 1
        s['earnings'] += payment

    def record_failure(self, phase, repair_cost):
        s = self.phase_stats.setdefault(phase, {'commits': 0, 'deliveries': 0, 'failures': 0, 'earnings': 0.0, 'costs': 0.0})
        s['failures'] += 1
        s['costs'] += repair_cost

    @property
    def net_profit(self):
        return self.earnings - self.costs
