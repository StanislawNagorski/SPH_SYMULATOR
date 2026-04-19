#!/usr/bin/env python3
"""
=============================================================
  MEDIACJA TRANSFERU PŁATNYCH USŁUG — Symulator Strategii
  Autor: Mikołaj Rutkowski
  Na podstawie: J. Konorski, MPE cz. 2, Katedra Teleinformatyki WETI
=============================================================

UŻYCIE (jedna linia):
  python sph_sim.py --strategy <NAZWA> [parametry_strategii] [parametry_srodowiska]

PRZYKŁADY:
  python sph_sim.py --strategy naive --zeta 0.5
  python sph_sim.py --strategy threshold --max_phase 3
  python sph_sim.py --strategy phase_prob --probs 0.9,0.7,0.5,0.3,0.0
  python sph_sim.py --strategy incentive --expected_P 100
  python sph_sim.py --strategy adaptive --s_target 10
  python sph_sim.py --strategy naive --zeta 0.4 --nU 200 --nSUS 20 --K1 120 --T 1000
  python sph_sim.py --strategy phase_prob --probs 1.0,0.8,0.6,0.2,0.0 --kappa 0.5 --alpha 0 --json

DOSTĘPNE STRATEGIE:
  naive       -- COMMIT dla zeta*100% urządzeń w każdej fazie
  threshold   -- COMMIT tylko dla faz <= max_phase
  phase_prob  -- COMMIT z prawdopodobieństwem per faza (lista probs)
  incentive   -- COMMIT gdy E[zysk_netto] > 0 (zgodna motywacyjnie)
  adaptive    -- COMMIT zależnie od poziomu bufora SUS
"""

import argparse
import json
import random
import math
from dataclasses import dataclass
from typing import List, Tuple, Dict

# ──────────────────────────────────────────────────────────────
# PARAMETRY DOMYŚLNE (z dokumentu)
# ──────────────────────────────────────────────────────────────
DEFAULT_NU    = 250
DEFAULT_NSUS  = 20
DEFAULT_K0    = 100
DEFAULT_K1    = 120
DEFAULT_F     = 5
DEFAULT_T     = 1000
DEFAULT_KAPPA = 0.25
DEFAULT_ALPHA = 1
DEFAULT_PHI   = [0.1, 0.2, 0.3, 0.4, 1.0]
DEFAULT_RHO   = [0.5, 0.5, 0.7, 1.5, 3.0]

# ──────────────────────────────────────────────────────────────
# FUNKCJE MODELU
# ──────────────────────────────────────────────────────────────
def valuation(u, K0, K1):
    if K1 == float('inf'):
        return float(K0) if u >= K0 else 0.0
    return float(K0) if K0 <= u <= K1 else 0.0

def sph_stp(u, s, nSUS, K0, K1):
    """Zwraca (z*, y*) max-izujące P = g(u-x)+x, x=z-y."""
    def P_of_x(x):
        return valuation(u - x, K0, K1) + x

    x_min = -s
    x_max = min(u, nSUS - s)
    if x_min > x_max:
        return 0, 0

    best_x, best_P = x_min, P_of_x(x_min)
    candidates = [x_min, x_max, K0 - u]
    if K1 != float('inf'):
        candidates.append(K1 - u)
    for xc in candidates:
        for x in [int(xc) - 1, int(xc), int(xc) + 1]:
            if x_min <= x <= x_max:
                p = P_of_x(x)
                if p > best_P:
                    best_P, best_x = p, x

    return (best_x, 0) if best_x >= 0 else (0, -best_x)

# ──────────────────────────────────────────────────────────────
# URZĄDZENIE
# ──────────────────────────────────────────────────────────────
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

    def __post_init__(self):
        # Per-phase IC tracking: phase -> {commits, deliveries, failures, earnings, costs}
        self.phase_stats = {}

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

# ──────────────────────────────────────────────────────────────
# STRATEGIE
# ──────────────────────────────────────────────────────────────
def strategy_naive(dev, l, s, phi, kappa, rho, h, p):
    if dev.status != 'UP':
        return 'ABSTAIN'
    return 'COMMIT' if random.random() < float(p.get('zeta', 0.5)) else 'ABSTAIN'

def strategy_threshold(dev, l, s, phi, kappa, rho, h, p):
    if dev.status != 'UP':
        return 'ABSTAIN'
    return 'COMMIT' if dev.phase <= int(p.get('max_phase', 3)) else 'ABSTAIN'

def strategy_phase_prob(dev, l, s, phi, kappa, rho, h, p):
    if dev.status != 'UP':
        return 'ABSTAIN'
    probs = [float(x) for x in str(p.get('probs', '0.9,0.7,0.5,0.3,0.0')).split(',')]
    idx = dev.phase - 1
    prob = probs[idx] if idx < len(probs) else 0.0
    return 'COMMIT' if random.random() < prob else 'ABSTAIN'

def strategy_incentive(dev, l, s, phi, kappa, rho, h, p):
    if dev.status != 'UP':
        return 'ABSTAIN'
    idx = dev.phase - 1
    if idx >= len(phi) or phi[idx] >= 1.0:
        return 'ABSTAIN'
    total_h = sum(h(j + 1) * (l[j] if j < len(l) else 0) for j in range(len(l)))
    if total_h <= 0:
        total_h = 1.0
    exp_P = float(p.get('expected_P', DEFAULT_K0))
    exp_pay = (h(dev.phase) / total_h) * exp_P
    net = (1 - phi[idx]) * exp_pay - kappa - phi[idx] * rho[idx]
    return 'COMMIT' if net > 0 else 'ABSTAIN'

def strategy_adaptive(dev, l, s, phi, kappa, rho, h, p):
    if dev.status != 'UP':
        return 'ABSTAIN'
    idx = dev.phase - 1
    if idx >= len(phi) or phi[idx] >= 1.0:
        return 'ABSTAIN'
    tgt = int(p.get('s_target', 10))
    if s < tgt:
        prob = 0.9
    elif s < tgt * 2:
        prob = 0.5
    else:
        prob = 0.2
    return 'COMMIT' if random.random() < prob else 'ABSTAIN'

STRATEGIES = {
    'naive': strategy_naive,
    'threshold': strategy_threshold,
    'phase_prob': strategy_phase_prob,
    'incentive': strategy_incentive,
    'adaptive': strategy_adaptive,
}

# ──────────────────────────────────────────────────────────────
# SYMULATOR
# ──────────────────────────────────────────────────────────────
class SPHSimulator:
    def __init__(self, nU, nSUS, K0, K1, F, T, kappa, alpha,
                 phi, rho, strategy_fn, params, seed=42):
        self.nU, self.nSUS, self.K0, self.K1 = nU, nSUS, K0, K1
        self.F, self.T, self.kappa, self.alpha = F, T, kappa, alpha
        self.phi, self.rho = phi, rho
        self.strategy_fn, self.params = strategy_fn, params
        random.seed(seed)

        self.h = (lambda i: i ** alpha) if alpha > 0 else (lambda i: 1.0)

        self.devices = []
        for did in range(nU):
            if random.random() < 0.3:
                self.devices.append(Device(id=did, phase=-1, status='DOWN', down_left=1))
            else:
                ph = random.randint(1, F - 1)
                self.devices.append(Device(id=did, phase=ph, status='UP'))

        self.s = nSUS // 2
        self.history = {k: [] for k in ['val', 'cum_val', 'profit', 'delivery', 'sus', 'providers']}

    def run(self):
        l_prev = [0] * (self.F - 1)
        total_val = 0.0
        total_dec = 0
        total_deliv = 0

        for t in range(self.T):
            providers = []
            for dev in self.devices:
                if dev.status == 'DOWN':
                    dev.down_left -= 1
                    if dev.down_left <= 0:
                        dev.status = 'UP'
                        dev.phase = 1
                    continue

                decision = self.strategy_fn(
                    dev, l_prev, self.s,
                    self.phi, self.kappa, self.rho, self.h, self.params
                )

                if decision == 'COMMIT':
                    commit_phase = dev.phase
                    dev.n_commit += 1
                    total_dec += 1
                    dev.costs += self.kappa
                    dev.record_commit(commit_phase, self.kappa)
                    idx = dev.phase - 1
                    fp = self.phi[idx] if idx < len(self.phi) else 1.0
                    if random.random() < fp:
                        repair = self.rho[idx] if idx < len(self.rho) else 0.0
                        dev.costs += repair
                        dev.record_failure(commit_phase, repair)
                        dev.n_failed += 1
                        dev.status = 'DOWN'
                        dev.down_left = 1
                        dev.phase = -1
                    else:
                        providers.append(dev)
                        dev.n_delivered += 1
                        total_deliv += 1
                else:
                    dev.n_abstain += 1
                    dev.status = 'DOWN'
                    dev.down_left = 1

            u = len(providers)
            z, y = sph_stp(u, self.s, self.nSUS, self.K0, self.K1)
            svc_to_cons = u - z + y
            P_total = valuation(svc_to_cons, self.K0, self.K1) + z - y

            l_curr = [0] * (self.F - 1)
            if u > 0:
                for dev in providers:
                    idx = dev.phase - 1
                    if 0 <= idx < self.F - 1:
                        l_curr[idx] += 1
                total_hw = sum(self.h(j + 1) * l_curr[j] for j in range(self.F - 1))
                for dev in providers:
                    idx = dev.phase - 1
                    if total_hw > 0 and 0 <= idx < self.F - 1:
                        pay = (self.h(dev.phase) / total_hw) * P_total
                    else:
                        pay = P_total / u
                    dev.earnings += pay
                    dev.record_delivery(dev.phase, pay)
                    if dev.phase < self.F - 1:
                        dev.phase += 1

            self.s = max(0, self.s + z - y)
            l_prev = l_curr

            val = valuation(svc_to_cons, self.K0, self.K1)
            total_val += val
            avg_profit = sum(d.net_profit for d in self.devices) / self.nU
            deliv_ratio = total_deliv / max(total_dec, 1)

            self.history['val'].append(val)
            self.history['cum_val'].append(total_val)
            self.history['profit'].append(avg_profit)
            self.history['delivery'].append(deliv_ratio)
            self.history['sus'].append(self.s)
            self.history['providers'].append(u)

        last100 = slice(-100, None)

        # Aggregate per-phase IC stats across all devices
        ic_phases = {}
        for dev in self.devices:
            for ph, s in dev.phase_stats.items():
                if ph not in ic_phases:
                    ic_phases[ph] = {'commits': 0, 'deliveries': 0, 'failures': 0, 'earnings': 0.0, 'costs': 0.0}
                for k in ic_phases[ph]:
                    ic_phases[ph][k] += s[k]
        ic_results = {}
        for ph in sorted(ic_phases):
            s = ic_phases[ph]
            if s['commits'] > 0:
                avg_earning = s['earnings'] / s['commits']
                avg_cost = s['costs'] / s['commits']
                avg_net = avg_earning - avg_cost
                delivery_rate = s['deliveries'] / s['commits']
                ic_results[ph] = {
                    'commits': s['commits'],
                    'deliveries': s['deliveries'],
                    'failures': s['failures'],
                    'avg_earning_per_commit': round(avg_earning, 4),
                    'avg_cost_per_commit': round(avg_cost, 4),
                    'avg_net_per_commit': round(avg_net, 4),
                    'delivery_rate': round(delivery_rate, 4),
                    'ic_satisfied': avg_net > 0,
                }

        return {
            'avg_val_last100':    round(sum(self.history['val'][last100]) / 100, 4),
            'cum_val_total':      round(total_val, 2),
            'avg_net_profit':     round(sum(d.net_profit for d in self.devices) / self.nU, 4),
            'delivery_ratio':     round(self.history['delivery'][-1], 4),
            'avg_providers_l100': round(sum(self.history['providers'][last100]) / 100, 2),
            'sus_final':          self.s,
            'ic_per_phase':       ic_results,
            'history':            self.history,
            'devices':            self.devices,
        }

# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(
        description='SPH Symulator — testuj strategię rekomendacji COMMIT/ABSTAIN',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    p.add_argument('--strategy', required=True, choices=list(STRATEGIES.keys()),
                   help='Strategia: ' + ', '.join(STRATEGIES.keys()))
    # Parametry strategii
    p.add_argument('--zeta',       type=float, default=0.5,   help='[naive] Frakcja COMMIT (0..1)')
    p.add_argument('--max_phase',  type=int,   default=3,     help='[threshold] Max faza COMMIT')
    p.add_argument('--probs',      type=str,   default='0.9,0.7,0.5,0.3,0.0',
                   help='[phase_prob] P(COMMIT) per faza, po przecinku')
    p.add_argument('--s_target',   type=int,   default=10,    help='[adaptive] Próg SUS')
    p.add_argument('--expected_P', type=float, default=100.0, help='[incentive] Oczek. płatność')
    # Parametry środowiska
    p.add_argument('--nU',   type=int,   default=DEFAULT_NU,    help=f'Liczba urządzeń (def {DEFAULT_NU})')
    p.add_argument('--nSUS', type=int,   default=DEFAULT_NSUS,  help=f'Pojemność SUS (def {DEFAULT_NSUS})')
    p.add_argument('--K1',   type=float, default=DEFAULT_K1,    help=f'Górna granica waluacji (def {DEFAULT_K1})')
    p.add_argument('--T',    type=int,   default=DEFAULT_T,     help=f'Liczba cykli (def {DEFAULT_T})')
    p.add_argument('--kappa',type=float, default=DEFAULT_KAPPA, help=f'Koszt dostarczenia (def {DEFAULT_KAPPA})')
    p.add_argument('--alpha',type=float, default=DEFAULT_ALPHA, help=f'Wykładnik h(i)=i^alpha (def {DEFAULT_ALPHA})')
    p.add_argument('--seed', type=int,   default=42,            help='Ziarno losowe (def 42)')
    p.add_argument('--json', action='store_true', help='Wynik jako JSON (do parsowania)')
    p.add_argument('--verbose', action='store_true', help='Szczegółowe logi co 100 cykli')
    return p.parse_args()

def main():
    args = parse_args()
    K1 = float('inf') if args.K1 < 0 else args.K1
    params = {
        'zeta': args.zeta, 'max_phase': args.max_phase,
        'probs': args.probs, 's_target': args.s_target,
        'expected_P': args.expected_P,
    }
    sim = SPHSimulator(
        nU=args.nU, nSUS=args.nSUS, K0=DEFAULT_K0, K1=K1,
        F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
        phi=DEFAULT_PHI, rho=DEFAULT_RHO,
        strategy_fn=STRATEGIES[args.strategy],
        params=params, seed=args.seed,
    )
    res = sim.run()

    if args.json:
        out = {
            'strategy': args.strategy,
            'strategy_params': params,
            'env': {'nU': args.nU, 'nSUS': args.nSUS, 'K1': K1,
                    'T': args.T, 'kappa': args.kappa, 'alpha': args.alpha},
            'metrics': {k: v for k, v in res.items() if k not in ('history', 'devices')},
        }
        print(json.dumps(out, indent=2))
    else:
        sep = '─' * 62
        print(f"\n{'='*62}")
        print(f"  SPH SYMULATOR  |  Strategia: {args.strategy.upper()}")
        print(f"  nU={args.nU}, nSUS={args.nSUS}, K1={K1}, T={args.T}, κ={args.kappa}, α={args.alpha}")
        print(f"{'='*62}")
        print(f"\n  METRYKI (asymptota — ostatnie 100 z {args.T} cykli):")
        print(f"  {sep}")
        print(f"  Śr. waluacja Konsumentów (ost.100):   {res['avg_val_last100']:>10.2f}")
        print(f"  Łączna waluacja (wszystkie cykle):    {res['cum_val_total']:>10.1f}")
        print(f"  Śr. zysk netto na urządzenie:         {res['avg_net_profit']:>10.4f}")
        print(f"  Wskaźnik ciągłości dostaw:            {res['delivery_ratio']:>10.2%}")
        print(f"  Śr. liczba dostawców (ost.100):       {res['avg_providers_l100']:>10.2f}")
        print(f"  Zajętość SUS (końcowa):               {res['sus_final']:>10}")
        print(f"  {sep}")

        commit_devs = [d for d in res['devices'] if d.n_commit > 0]
        if commit_devs:
            avg_cp = sum(d.net_profit for d in commit_devs) / len(commit_devs)
            print(f"  Śr. zysk urządzeń wyk. COMMIT:        {avg_cp:>10.4f}")

        # IC per-phase analysis
        ic = res.get('ic_per_phase', {})
        if ic:
            print(f"\n  ZGODNOŚĆ MOTYWACYJNA (IC) — zysk netto per COMMIT w fazie:")
            print(f"  {sep}")
            print(f"  {'Faza':>6}  {'COMMIT':>8}  {'Sukces%':>8}  {'E[przychód]':>12}  {'E[koszt]':>10}  {'E[zysk]':>10}  {'IC?':>5}")
            print(f"  {sep}")
            all_ic = True
            for ph in sorted(ic):
                d = ic[ph]
                ic_mark = '  ✓' if d['ic_satisfied'] else '  ✗'
                if not d['ic_satisfied']:
                    all_ic = False
                print(f"  {ph:>6}  {d['commits']:>8}  {d['delivery_rate']:>7.1%}  {d['avg_earning_per_commit']:>12.4f}  {d['avg_cost_per_commit']:>10.4f}  {d['avg_net_per_commit']:>10.4f}  {ic_mark}")
            print(f"  {sep}")
            verdict = "TAK — wszystkie fazy" if all_ic else "NIE — nie wszystkie fazy"
            print(f"  Zgodność motywacyjna: {verdict}")

        if args.verbose:
            print(f"\n  Próbkowanie waluacji (co 100 cykli):")
            h = res['history']
            for i in range(0, args.T, 100):
                idx = min(i + 99, args.T - 1)
                print(f"    t={i+100:5d}: val={h['val'][idx]:6.1f}  "
                      f"prov={h['providers'][idx]:4d}  SUS={h['sus'][idx]:3d}")
        print()

if __name__ == '__main__':
    main()
