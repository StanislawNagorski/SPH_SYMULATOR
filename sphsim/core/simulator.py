# Symulator — orchestruje T-cyklowy bieg, deleguje decyzje do strategy_fn.
import random
from sphsim.core.device import Device
from sphsim.core.model import valuation, sph_stp

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
                elif decision == 'VETO':
                    # n_vetoed inkrementowane w wrapperze (PRZED return 'VETO').
                    # Tutaj tylko stan: identycznie jak ABSTAIN, ale BEZ n_abstain++ (D-65).
                    dev.status = 'DOWN'
                    dev.down_left = 1
                else:  # 'ABSTAIN' lub nieznany decision — failsafe (T-04-04)
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

        # Aggregate per-phase VETO stats across all devices (Phase 4 D-64)
        veto_per_phase = {}
        n_vetoed_total = 0
        for dev in self.devices:
            for ph, count in dev.veto_phase_stats.items():
                veto_per_phase[ph] = veto_per_phase.get(ph, 0) + count
                n_vetoed_total += count

        return {
            'avg_val_last100':    round(sum(self.history['val'][last100]) / 100, 4),
            'cum_val_total':      round(total_val, 2),
            'avg_net_profit':     round(sum(d.net_profit for d in self.devices) / self.nU, 4),
            'delivery_ratio':     round(self.history['delivery'][-1], 4),
            'avg_providers_l100': round(sum(self.history['providers'][last100]) / 100, 2),
            'sus_final':          self.s,
            'ic_per_phase':       ic_results,
            'veto_per_phase':     veto_per_phase,
            'n_vetoed_total':     n_vetoed_total,
            'history':            self.history,
            'devices':            self.devices,
        }
