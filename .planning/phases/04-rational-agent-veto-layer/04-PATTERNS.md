# Phase 4: Rational Agent veto layer — Pattern Map

**Mapped:** 2026-05-27
**Files analyzed:** 11 (3 NEW + 7 MODIFIED + 1 fixtures patch)
**Analogs found:** 11 / 11 (all match — codebase is mature after Phases 1–3)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `sphsim/agent/__init__.py` (NEW) | package-init | namespace export | `sphsim/strategies/__init__.py` | role-match (registry vs. factory export) |
| `sphsim/agent/rational.py` (NEW) | strategy-wrapper (closure factory) | request-response (per-cycle decision) | `sphsim/strategies/incentive.py` | exact (verbatim formula) |
| `tests/test_agent.py` (NEW) | unit test | request-response | `tests/test_loader.py` | exact (unittest + stdlib + per-test setUp/tearDown) |
| `sphsim/core/device.py` (MOD) | model (dataclass) | mutable state | itself + `phase_stats` precedent | exact (parallel counter field) |
| `sphsim/core/simulator.py` (MOD) | core orchestrator | event-driven loop | itself (`ABSTAIN` branch + `ic_per_phase` aggregation) | exact (paste-and-modify) |
| `sphsim/cli/args.py` (MOD) | CLI argparse | request-response | itself (`--interactive` boolean + `--custom` mutex) | exact (boolean flag + manual mutex check pattern) |
| `sphsim/cli/output.py` (MOD) | CLI formatter | transform | itself (`ic_per_phase` section, `format_json`) | exact (paste-and-modify) |
| `sphsim/cli/main.py` (MOD) | CLI entry-point | request-response | itself (built-in + custom branches) | exact (insert wrap call) |
| `sphsim/cli/repl.py` (MOD) | REPL command (cmd.Cmd) | request-response | itself (`do_run` from Phase 3 D-41) | exact (paste-and-modify into `do_compare`) |
| `scripts/regression_check.py` (MOD via `generate_baseline.py`) | regression script | batch | itself (`INVOCATIONS` list) | exact (add flag to each tuple) |
| `tests/fixtures/baseline_v1/*.json` (PATCH) | test fixtures | data | itself | exact (single sed-style patch or alt: regression skip 3 new keys) |

---

## Pattern Assignments

### 1. `sphsim/agent/rational.py` (NEW — strategy-wrapper, closure factory)

**Primary analog:** `/Users/stanislawnagorski/Documents/STUDIA/sem4/ekonometria 2/sphsim/strategies/incentive.py` (entire 28-line file is the math source-of-truth)

**Verbatim formula to copy (`incentive.py:6-18`):**

```python
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
```

**Strategy signature contract** (`sphsim/strategies/loader.py:31`):

```python
EXPECTED_PARAMS = ('dev', 'l', 's', 'phi', 'kappa', 'rho', 'h', 'p')
```

The wrapped closure MUST keep this exact 8-arg signature — Phase 3 D-47 layer 3 enforces it for custom strategies, and the loader test (`test_loader.py:163-187`) treats it as the only escape hatch (`*args`). Wrapper that mutates the contract breaks `tests/test_strategy_meta_consistency.py` invariant (`test_strategy_meta_consistency.py:84-168`).

**Module docstring style** (`incentive.py:1-2`) — first-line single-sentence comment in Polish, optional reference to v1.0 source. Apply to `rational.py:1-…`:

```python
# RationalAgent — wrapper veto-ujący COMMIT przy E[zysk] < 0.
# Formuła i parametr expected_P identyczne z sphsim/strategies/incentive.py (D-53/D-54).
```

**Import style** (`incentive.py:3`):

```python
from sphsim.config import DEFAULT_K0
```

Use the same import for fallback when `expected_P` is not provided (mirror `incentive.py:15`).

**Decision return values** — Phase 4 D-65 (Claude's Discretion (a)) extends to a 3-state enum-by-string: `'COMMIT' | 'ABSTAIN' | 'VETO'`. Wrapper returns `'VETO'` (not `'ABSTAIN'`) so that simulator can dispatch without double-counting (`n_abstain` vs `n_vetoed`).

**Reference closure skeleton** (from CONTEXT.md `<code_context>` §1, already vetted against `incentive.py` math):

```python
def wrap_with_agent(strategy_fn, expected_P):
    def wrapped(dev, l, s, phi, kappa, rho, h, p):
        decision = strategy_fn(dev, l, s, phi, kappa, rho, h, p)
        if decision != 'COMMIT':
            return decision
        idx = dev.phase - 1
        if idx >= len(phi) or phi[idx] >= 1.0:
            dev.n_vetoed += 1
            dev.veto_phase_stats[dev.phase] = dev.veto_phase_stats.get(dev.phase, 0) + 1
            return 'VETO'
        total_h = sum(h(j + 1) * (l[j] if j < len(l) else 0) for j in range(len(l)))
        if total_h <= 0:
            total_h = 1.0
        exp_pay = (h(dev.phase) / total_h) * expected_P
        net = (1 - phi[idx]) * exp_pay - kappa - phi[idx] * rho[idx]
        if net < 0:
            dev.n_vetoed += 1
            dev.veto_phase_stats[dev.phase] = dev.veto_phase_stats.get(dev.phase, 0) + 1
            return 'VETO'
        return 'COMMIT'
    return wrapped
```

Note divergence from `incentive.py`: agent threshold is `net < 0` (AGENT-02 literal); `strategy_incentive` uses `net > 0` (commit when positive). For `incentive` strategy + agent, the boundary `net == 0` yields ABSTAIN from strategy (no commit) → agent passthrough → no veto. Numerically idempotent for incentive (D-56).

---

### 2. `sphsim/agent/__init__.py` (NEW — package init)

**Primary analog:** `/Users/stanislawnagorski/Documents/STUDIA/sem4/ekonometria 2/sphsim/strategies/__init__.py` (27 lines) for the export-aggregation pattern. For minimal init (no registry), also `sphsim/__init__.py:1-6`.

**Pattern (`sphsim/__init__.py:1-6`):**

```python
"""SPH Mediation Simulator — pakiet refactoringu monolitu sph_sim.py v1.0."""
from sphsim.core.simulator import SPHSimulator
from sphsim.core.device import Device
from sphsim.strategies import STRATEGIES

__all__ = ['SPHSimulator', 'Device', 'STRATEGIES']
```

**Apply to `sphsim/agent/__init__.py`:**

```python
"""Rational agent — wrapper veto-ujący COMMIT przy E[zysk] < 0 (Phase 4, AGENT-01..05)."""
from sphsim.agent.rational import wrap_with_agent, RationalAgent

__all__ = ['wrap_with_agent', 'RationalAgent']
```

If `RationalAgent` is implemented as a pure-function module (no class — per Deferred note "Wrapper jako klasa…Claude's Discretion"), then export only `wrap_with_agent`.

---

### 3. `sphsim/core/device.py` (MOD — add `n_vetoed` + `veto_phase_stats`)

**Primary analog:** `device.py` itself — the existing 5 counters (`n_commit`, `n_abstain`, `n_delivered`, `n_failed` plus `earnings`/`costs`) and the `__post_init__` dict precedent.

**Existing counter pattern** (`device.py:17-20`):

```python
    n_commit: int = 0
    n_abstain: int = 0
    n_delivered: int = 0
    n_failed: int = 0
```

Insert `n_vetoed: int = 0` directly after `n_failed` (line 20) — match alphabetical-of-frequency grouping (the 4 existing counters are ordered by lifecycle: commit → abstain → delivered → failed; `n_vetoed` belongs between `n_abstain` and `n_delivered` logically, but per CONTEXT.md `<code_context>` §3 the documented insert point is **after `n_failed`** to avoid changing the existing argument order in any `Device(...)` positional construction. Verify no positional `Device(...)` calls exist before deciding — quick `grep` shows only kwargs at `simulator.py:20,23` so insert position is irrelevant in practice).

**Existing `__post_init__` pattern** (`device.py:22-24`):

```python
    def __post_init__(self):
        # Per-phase IC tracking: phase -> {commits, deliveries, failures, earnings, costs}
        self.phase_stats = {}
```

Mirror with one extra line:

```python
    def __post_init__(self):
        self.phase_stats = {}
        self.veto_phase_stats = {}  # {phase: count} — Phase 4 D-64
```

**Why dict-in-`__post_init__` not a dataclass field:** dataclass mutable defaults are forbidden (`field(default_factory=dict)` works but the existing code uses the simpler `__post_init__` pattern — keep consistency).

---

### 4. `sphsim/core/simulator.py` (MOD — VETO guard + `veto_per_phase` aggregation)

**Primary analog:** `simulator.py` itself — the ABSTAIN branch (`simulator.py:69-72`) and the `ic_per_phase` aggregation (`simulator.py:113-138`) are paste-and-modify templates.

**ABSTAIN branch to mirror** (`simulator.py:69-72`):

```python
                else:
                    dev.n_abstain += 1
                    dev.status = 'DOWN'
                    dev.down_left = 1
```

**Modification per D-65 (3-state interface):**

```python
                elif decision == 'VETO':
                    # n_vetoed inkrementowane w wrapperze (PRZED return 'VETO').
                    # Tutaj tylko stan: identycznie jak ABSTAIN, ale BEZ n_abstain++.
                    dev.status = 'DOWN'
                    dev.down_left = 1
                else:  # 'ABSTAIN' lub nieznany decision
                    dev.n_abstain += 1
                    dev.status = 'DOWN'
                    dev.down_left = 1
```

Note: the outer `if decision == 'COMMIT':` block at `simulator.py:49-68` stays untouched. The change is 2 lines (turn the `else:` into `elif decision == 'VETO': … else:`).

**`ic_per_phase` aggregation template to copy** (`simulator.py:113-138`):

```python
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
                ...
                ic_results[ph] = { ... }
```

**Parallel aggregation to insert** (after line 138, before the `return` at line 140):

```python
        # Aggregate per-phase VETO stats across all devices (Phase 4 D-64)
        veto_per_phase = {}
        n_vetoed_total = 0
        for dev in self.devices:
            for ph, count in dev.veto_phase_stats.items():
                veto_per_phase[ph] = veto_per_phase.get(ph, 0) + count
                n_vetoed_total += count
```

**Return dict pattern to extend** (`simulator.py:140-150`):

```python
        return {
            'avg_val_last100':    round(...),
            'cum_val_total':      round(...),
            'avg_net_profit':     round(...),
            'delivery_ratio':     round(...),
            'avg_providers_l100': round(...),
            'sus_final':          self.s,
            'ic_per_phase':       ic_results,
            'history':            self.history,
            'devices':            self.devices,
        }
```

Add two lines (before `'history':` to keep history/devices last per current convention):

```python
            'veto_per_phase':     veto_per_phase,
            'n_vetoed_total':     n_vetoed_total,
```

---

### 5. `sphsim/cli/args.py` (MOD — `--no-agent`, `--compare-agent` + mutex check)

**Primary analog:** `args.py` itself.

**Existing boolean-flag pattern (`args.py:63-64`):**

```python
    p.add_argument('--json', action='store_true', help='Wynik jako JSON (do parsowania)')
    p.add_argument('--verbose', action='store_true', help='Szczegółowe logi co 100 cykli')
```

**Insert two parallel flags (outside mutex):**

```python
    p.add_argument('--no-agent', action='store_true',
                   help='Wyłącz RationalAgent (surowa strategia, bez veto)')
    p.add_argument('--compare-agent', action='store_true',
                   help='Uruchom 2x: z agentem i bez — tabela delta KPI')
```

**Mutex check pattern** — `args.py` currently has only the argparse-builtin mutex group (`args.py:38-44`). Phase 4 adds custom post-parse checks. Pattern from the broader codebase: `sphsim/cli/main.py:17-19` shows the precedent (post-parse soft validation, single `print(..., file=sys.stderr)`):

```python
    if args.param and not args.custom:
        import sys
        print('Flaga --param ignorowana — działa tylko z --custom.', file=sys.stderr)
```

For Phase 4 the check is HARD (argparse `p.error()` exits 2 with usage line). Insert before `return p.parse_args()` — but `p.error()` needs `p` in scope, so refactor: capture parser, parse, validate, return:

```python
    args = p.parse_args()
    if args.compare_agent and args.no_agent:
        p.error("Flagi --compare-agent i --no-agent są wzajemnie wykluczające.")
    if args.compare_agent and args.interactive:
        p.error("Flaga --compare-agent nie działa w trybie --interactive.")
    return args
```

**Polish-language error pattern** (consistent with existing repl `print(...)` messages and loader `LoaderError` args). Match style of `repl.py:106` (`print("Użycie: …")`) and `loader.py:127` (`raise LoaderError(f"Plik nie istnieje: {abspath}")`).

**`--expected_P` help-text update** (`args.py:51`) — current:

```python
    p.add_argument('--expected_P', type=float, default=100.0, help='[incentive] Oczek. płatność')
```

Update to (D-54, D-67 docs):

```python
    p.add_argument('--expected_P', type=float, default=100.0,
                   help='[incentive|agent] Oczek. płatność (def 100.0)')
```

---

### 6. `sphsim/cli/output.py` (MOD — VETO section + `format_compare` + JSON extension)

**Primary analog:** `output.py` itself — the IC section (`output.py:38-54`) is the structural template for the new VETO section.

**IC section to mirror** (`output.py:38-54`):

```python
    # IC per-phase analysis
    ic = res.get('ic_per_phase', {})
    if ic:
        lines.append(f"\n  ZGODNOŚĆ MOTYWACYJNA (IC) — zysk netto per COMMIT w fazie:")
        lines.append(f"  {sep}")
        lines.append(f"  {'Faza':>6}  {'COMMIT':>8}  {'Sukces%':>8}  {'E[przychód]':>12}  {'E[koszt]':>10}  {'E[zysk]':>10}  {'IC?':>5}")
        lines.append(f"  {sep}")
        all_ic = True
        for ph in sorted(ic):
            d = ic[ph]
            ic_mark = '  ✓' if d['ic_satisfied'] else '  ✗'
            if not d['ic_satisfied']:
                all_ic = False
            lines.append(f"  {ph:>6}  {d['commits']:>8}  ...")
        lines.append(f"  {sep}")
        verdict = "TAK — wszystkie fazy" if all_ic else "NIE — nie wszystkie fazy"
        lines.append(f"  Zgodność motywacyjna: {verdict}")
```

**Apply same structure for VETO section (insert AFTER line 54, BEFORE `if verbose:` at line 56):**

```python
    # VETO per-phase summary (Phase 4 D-66)
    veto_pp = res.get('veto_per_phase', {})
    n_vetoed = res.get('n_vetoed_total', 0)
    if n_vetoed > 0:
        lines.append(f"\n  VETO przez RationalAgent — rekomendacje COMMIT odrzucone per faza:")
        lines.append(f"  {sep}")
        lines.append(f"  {'Faza':>6}  {'COMMIT zgłoszone':>18}  {'VETO':>8}  {'% zaweto':>10}")
        lines.append(f"  {sep}")
        ic = res.get('ic_per_phase', {})
        total_committed = 0
        for ph in sorted(set(list(veto_pp.keys()) + list(ic.keys()))):
            commits = ic.get(ph, {}).get('commits', 0)
            vetos = veto_pp.get(ph, 0)
            total = commits + vetos
            pct = (vetos / total * 100) if total > 0 else 0
            lines.append(f"  {ph:>6}  {total:>18}  {vetos:>8}  {pct:>9.1f}%")
            total_committed += total
        lines.append(f"  {sep}")
        pct_total = (n_vetoed / max(total_committed, 1)) * 100
        lines.append(f"  Łącznie zaweto'wano: {n_vetoed} COMMIT-ów z {total_committed} zgłoszonych ({pct_total:.1f}%).")
```

**`format_json` extension pattern** (`output.py:5-13`):

```python
def format_json(args, res, params, K1):
    out = {
        'strategy': args.strategy,
        'strategy_params': params,
        'env': {'nU': args.nU, 'nSUS': args.nSUS, 'K1': K1,
                'T': args.T, 'kappa': args.kappa, 'alpha': args.alpha},
        'metrics': {k: v for k, v in res.items() if k not in ('history', 'devices')},
    }
    return json.dumps(out, indent=2)
```

The `metrics` dict already does `{k:v for … if k not in ('history','devices')}` — Phase 4's added `veto_per_phase`/`n_vetoed_total` will appear automatically (they're in `res` from `simulator.run()`). Add only the `agent_enabled` field explicitly (D-67) since it's not in `res`:

```python
        'metrics': {**{k: v for k, v in res.items() if k not in ('history', 'devices')},
                    'agent_enabled': not args.no_agent},
```

**Compare-block JSON pattern** — when `args.compare_agent` is True, replace `metrics` with `comparison`. Pattern (paralleled by CONTEXT §`<code_context>` and Claude's Discretion):

```python
    if 'comparison' in res:  # signal: --compare-agent path
        out['comparison'] = res['comparison']
    else:
        out['metrics'] = { ... as before ... }
```

**`format_compare` (new function for human-readable delta table)** — no perfect analog; closest is `format_human` IC section (output.py:38-54) for tabular structure. Table from CONTEXT.md D-62 ascii is the spec; key bits:

```python
def format_compare(args, comp, K1):
    with_, without_, delta = comp['with_agent'], comp['without_agent'], comp['delta']
    kpis = [
        ('avg_val_last100', '{:>10.2f}'),
        ('cum_val_total', '{:>10.1f}'),
        ('avg_net_profit', '{:>10.4f}'),
        ('delivery_ratio', '{:>10.2%}'),
        ('avg_providers_l100', '{:>10.2f}'),
    ]
    # ... build 5-row × 3-column table ...
    verdict = '✓ TAK' if comp['agent_helps'] else '✗ NIE'
    # ...
```

Polish UI labels, identical to existing `format_human` Polish header style (`output.py:20-30`).

---

### 7. `sphsim/cli/main.py` (MOD — wrap `strategy_fn` + `run_compare` branch)

**Primary analog:** `main.py` itself — both branches (built-in `args.strategy` and custom `args.custom`) have a `SPHSimulator(...)` build call that needs the wrap.

**Built-in branch pattern (`main.py:60-66`):**

```python
    sim = SPHSimulator(
        nU=args.nU, nSUS=args.nSUS, K0=DEFAULT_K0, K1=K1,
        F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
        phi=DEFAULT_PHI, rho=DEFAULT_RHO,
        strategy_fn=STRATEGIES[args.strategy],
        params=params, seed=args.seed,
    )
```

**Insert immediately before** (built-in branch):

```python
    strategy_fn = STRATEGIES[args.strategy]
    if not args.no_agent:
        from sphsim.agent import wrap_with_agent
        strategy_fn = wrap_with_agent(strategy_fn, args.expected_P)
    sim = SPHSimulator(
        ...
        strategy_fn=strategy_fn,
        ...
    )
```

**Custom branch (`main.py:42-47`)** — same pattern, after the `strategy_fn` returned by `load_custom(...)`:

```python
    if not args.no_agent:
        from sphsim.agent import wrap_with_agent
        strategy_fn = wrap_with_agent(strategy_fn, args.expected_P)
    sim = SPHSimulator(... strategy_fn=strategy_fn, ...)
```

**`run_compare` function** — new top-level helper. No direct analog (Phase 4 is first compare mode). Sketch from CONTEXT.md `<code_context>` §4:

```python
def run_compare(args, raw_strategy_fn, name, params, K1):
    common = dict(nU=args.nU, nSUS=args.nSUS, K0=DEFAULT_K0, K1=K1,
                  F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
                  phi=DEFAULT_PHI, rho=DEFAULT_RHO, params=params, seed=args.seed)
    from sphsim.agent import wrap_with_agent
    sim_with = SPHSimulator(strategy_fn=wrap_with_agent(raw_strategy_fn, args.expected_P), **common)
    res_with = sim_with.run()
    sim_without = SPHSimulator(strategy_fn=raw_strategy_fn, **common)
    res_without = sim_without.run()
    KPIS = ['avg_val_last100','cum_val_total','avg_net_profit','delivery_ratio','avg_providers_l100']
    return {
        'with_agent': {k: v for k, v in res_with.items() if k not in ('history','devices')},
        'without_agent': {k: v for k, v in res_without.items() if k not in ('history','devices')},
        'delta': {k: res_with[k] - res_without[k] for k in KPIS},
        'agent_helps': res_with['avg_net_profit'] > res_without['avg_net_profit'],
    }
```

Wire into `main()` as a third branch (between custom and built-in) when `args.compare_agent` is set, OR as a post-build short-circuit in both branches. CONTEXT.md prefers a dedicated function called from both branches.

---

### 8. `sphsim/cli/repl.py` (MOD — `do_compare` + `do_help` update)

**Primary analog:** `repl.py` itself — `do_run` (`repl.py:172-215`) is the exact paste-and-modify template for `do_compare`.

**`do_run` template (`repl.py:172-215`) — copy verbatim, modify simulator-build block:**

```python
    def do_run(self, arg):
        """Uruchom symulację: run <nazwa> [param=wartość ...]"""
        tokens = arg.split()
        if not tokens:
            print("Użycie: run <nazwa> [param=wartość ...]. Wpisz 'strategies' żeby zobaczyć dostępne.")
            return
        name, *kv_tokens = tokens

        if name not in STRATEGIES:
            available = ', '.join(STRATEGIES.keys())
            print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
            return

        ns = 'sphsim.strategies' if name in BUILTIN_STRATEGIES else 'sphsim.custom'
        mod = importlib.import_module(f'{ns}.{name}')
        meta = mod.STRATEGY_META

        try:
            params = parse_params_from_meta(kv_tokens, meta, name)
        except LoaderError as e:
            print(e.args[0])
            return

        sim = SPHSimulator(
            nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, K0=DEFAULT_K0, K1=DEFAULT_K1, F=DEFAULT_F,
            T=DEFAULT_T, kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA,
            phi=DEFAULT_PHI, rho=DEFAULT_RHO,
            strategy_fn=STRATEGIES[name], params=params, seed=42,
        )
        res = sim.run()

        fake_args = argparse.Namespace(
            strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
            kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False,
        )
        print(format_human(fake_args, res, DEFAULT_K1, False))
```

**Two modifications for `do_compare`:**

1. **Inside `do_run` itself** — per D-58, `do_run` wraps `STRATEGIES[name]` in `wrap_with_agent(...)` by default. Use `params.get('expected_P', DEFAULT_K0)` (since REPL has no `args.expected_P` flag; D-54 says agent reads from `params` dict in REPL context).

2. **New `do_compare`** — runs simulator twice (with + without wrap) and prints delta table.

**`do_help` update (`repl.py:58-66`):**

```python
    def do_help(self, arg):
        """Wyświetl listę dostępnych komend."""
        print("Dostępne komendy:")
        print("  help                            — Wyświetl tę listę komend.")
        print("  exit                            — Zakończ sesję (alternatywnie Ctrl+D).")
        print("  strategies                      — Wyświetl listę wbudowanych i custom strategii.")
        print("  strategy <nazwa>                — Wyświetl szczegóły strategii (parametry, baseline KPI).")
        print("  custom <ścieżka> [k=v ...]      — Załaduj custom strategię z pliku .py.")
        print("  run <nazwa> [k=v ...]           — Uruchom symulację (built-in lub custom).")
```

Add one row (after `run`):

```python
        print("  compare <nazwa> [k=v ...]       — Porównaj strategię z i bez RationalAgent (delta KPI).")
```

**Module docstring update (`repl.py:1-16`)** — bump "6 komend" → "7 komend" in line 3 and add `compare` to the bulleted list. Mirror the Phase 3 update style (lines 4-10).

**Class docstring update (`repl.py:52`)** — bump "4 komendy" string (currently outdated to begin with — code already has 6 commands; Phase 4 may want to fix to 7 in passing).

---

### 9. `tests/test_agent.py` (NEW — 10 unit tests)

**Primary analog:** `/Users/stanislawnagorski/Documents/STUDIA/sem4/ekonometria 2/tests/test_loader.py` (396 lines, 19 tests) — Phase 3 test style; stdlib-only, `unittest.TestCase`, per-test `setUp`/`tearDown` for isolation.

**Module docstring pattern (`test_loader.py:1-22`):**

```python
"""
Unit tests dla sphsim.strategies.loader (Phase 3, D-46 / D-47 / D-49).
...
Stdlib only: unittest + tempfile + textwrap + os + sys + time + shutil
+ io + contextlib (zgodne z PROJECT.md constraint stdlib-only).
"""
```

**Apply to `test_agent.py`:**

```python
"""
Unit tests dla sphsim.agent.rational (Phase 4, D-53/D-55/D-57/D-63/D-65).

Pokrywa 10 przypadków:
  1. wrapper passthrough dla ABSTAIN
  2. brak veto gdy E[zysk] > 0
  3. veto gdy E[zysk] < 0
  4. n_vetoed inkrementuje, n_abstain NIE
  5. total_h == 0 → no veto (D-55 fallback total_h=1.0)
  6. phi[idx] >= 1.0 → veto (D-57 guard)
  7. idx >= len(phi) → veto (D-57 guard)
  8. incentive + wrapper = idempotent (D-56)
  9. --compare-agent JSON ma blok 'comparison' (integration)
 10. --no-agent → n_vetoed_total = 0 (integration)

Stdlib only: unittest + subprocess + json + os + sys + tempfile.
"""
```

**sys.path bootstrap pattern (`test_loader.py:33-36`):**

```python
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
```

**`setUp`/`tearDown` isolation pattern (`test_loader.py:51-69`)** — Phase 4 agent tests have less state to clean (no sys.modules pollution), but the snapshot+restore idiom applies if any test registers a custom strategy via `STRATEGIES`.

**Test method naming + assertion message pattern (`test_loader.py:93-102`):**

```python
def test_happy_path_loads_validates_returns(self):
    """load_custom dla validnego pliku zwraca (basename, callable, dict z description)."""
    path = self._write_valid('happy')
    name, fn, meta = load_custom(path)
    self.assertEqual(name, 'happy', msg=f'basename should be "happy", got {name!r}')
```

Each `assertEqual`/`assertIn` carries a verbose `msg=` with current value — copy this discipline.

**Integration test pattern (subprocess for CLI tests)** — `test_loader.py` does not subprocess; use `subprocess.run([sys.executable, 'sph_sim.py', ...], ...)` modeled after `scripts/regression_check.py:79-99`:

```python
def run_invocation(args):
    full_args = [sys.executable, str(MONOLITH), *args, '--seed', '42', '--json']
    result = subprocess.run(full_args, cwd=str(PROJECT_ROOT),
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout), None
```

**Test fixture builder for synthetic Device** — no analog in `test_loader.py`. Quick helper:

```python
def _make_device(phase=1, status='UP', n_commit=0, n_abstain=0, n_vetoed=0):
    dev = Device(id=0, phase=phase, status=status)
    dev.n_commit = n_commit
    dev.n_abstain = n_abstain
    dev.n_vetoed = n_vetoed
    return dev
```

**Stub strategy_fn pattern** — use closures `lambda dev, l, s, phi, kappa, rho, h, p: 'COMMIT'` (or `'ABSTAIN'`) for testing wrapper in isolation.

**`if __name__ == '__main__': unittest.main()` pattern (`test_loader.py:394-395`)** — match exactly.

---

### 10. `scripts/regression_check.py` (MOD via `scripts/generate_baseline.py`)

**Primary analog:** `scripts/generate_baseline.py:32-51` (the canonical `INVOCATIONS` list — DRY-imported by `regression_check.py:33`).

**Existing `INVOCATIONS` pattern (`generate_baseline.py:32-51`):**

```python
INVOCATIONS = [
    ('01-naive-zeta-0.5',
     ['--strategy', 'naive', '--zeta', '0.5']),
    ('02-threshold-max-phase-3',
     ['--strategy', 'threshold', '--max_phase', '3']),
    ...
    ('08-naive-zeta-0.75-baseline',
     ['--strategy', 'naive', '--zeta', '0.75']),
]
```

**Phase 4 modification — add `'--no-agent'` to each of 8 tuples (D-59):**

```python
INVOCATIONS = [
    ('01-naive-zeta-0.5',
     ['--strategy', 'naive', '--zeta', '0.5', '--no-agent']),
    ('02-threshold-max-phase-3',
     ['--strategy', 'threshold', '--max_phase', '3', '--no-agent']),
    ('03-phase-prob-default',
     ['--strategy', 'phase_prob', '--probs', '0.9,0.7,0.5,0.3,0.0', '--no-agent']),
    ('04-incentive-expected-P-100',
     ['--strategy', 'incentive', '--expected_P', '100', '--no-agent']),
    ('05-adaptive-s-target-10',
     ['--strategy', 'adaptive', '--s_target', '10', '--no-agent']),
    ('06-naive-zeta-0.4-custom-env',
     ['--strategy', 'naive', '--zeta', '0.4',
      '--nU', '200', '--nSUS', '20', '--K1', '120', '--T', '1000', '--no-agent']),
    ('07-phase-prob-custom-kappa-alpha',
     ['--strategy', 'phase_prob', '--probs', '1.0,0.8,0.6,0.2,0.0',
      '--kappa', '0.5', '--alpha', '0', '--no-agent']),
    ('08-naive-zeta-0.75-baseline',
     ['--strategy', 'naive', '--zeta', '0.75', '--no-agent']),
]
```

**`COMMANDS_HUMAN` list (`generate_baseline.py:54-63`)** must be updated in lockstep (8 strings get `--no-agent` appended before `--seed 42 --json`).

**`regression_check.py` requires NO changes** — it imports `INVOCATIONS` and `COMMANDS_HUMAN` from `generate_baseline.py` (line 33: `from generate_baseline import INVOCATIONS, ...`). Single source of truth.

---

### 11. `tests/fixtures/baseline_v1/*.json` (PATCH or alt: skip-keys)

**Primary analog:** `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` (and 7 siblings).

**Existing fixture shape (`08-naive-zeta-0.75-baseline.json`):**

```json
{
  "env": { ... },
  "metrics": {
    "avg_net_profit": 140.7592,
    "avg_providers_l100": 105.03,
    "avg_val_last100": 92.0,
    "cum_val_total": 92300.0,
    "delivery_ratio": 0.7931,
    "ic_per_phase": { ... },
    "sus_final": 1
  },
  "strategy": "naive",
  "strategy_params": { ... }
}
```

**D-67 Option A (patch fixtures, one-time)** — add 3 keys to `metrics` block in all 8 files:

```json
  "metrics": {
    ...existing keys...,
    "veto_per_phase": {},
    "n_vetoed_total": 0,
    "agent_enabled": false
  }
```

Use `sort_keys=True` in re-write to preserve git-diff determinism (matches `generate_baseline.py:108` style).

**D-67 Option B (skip 3 keys in regression compare — Claude's Discretion)** — modify `deep_diff` in `regression_check.py:36-76` to drop `veto_per_phase`, `n_vetoed_total`, `agent_enabled` from comparison. CONTEXT.md notes both options; planner picks one.

---

## Shared Patterns

### Polish UI strings, English identifiers

**Source:** `PROJECT.md` constraint + `repl.py:38-48` (Polish intro), `loader.py:127` (Polish errors), `output.py:23-30` (Polish METRYKI labels).

**Apply to all Phase 4 user-facing strings:**

- Section header: `"VETO przez RationalAgent — rekomendacje COMMIT odrzucone per faza:"`
- Compare verdict: `"✓ TAK"` / `"✗ NIE"`
- argparse errors: `"Flagi --compare-agent i --no-agent są wzajemnie wykluczające."`
- Help text: `"[incentive|agent] Oczek. płatność (def 100.0)"`
- REPL help: `"compare <nazwa> [k=v ...]       — Porównaj strategię z i bez RationalAgent (delta KPI)."`

Identifiers (function names, parameter names, dict keys) remain English: `wrap_with_agent`, `RationalAgent`, `n_vetoed`, `veto_per_phase`, `agent_enabled`, `comparison`, `agent_helps`, `with_agent`, `without_agent`, `delta`.

### Stdlib-only constraint

**Source:** `PROJECT.md` Constraint "Python 3.7+ stdlib only" + `loader.py:21` (explicit reaffirmation in module docstring).

**Apply to:** Every new file. Already-imported modules to leverage:
- `dataclasses` (Device) — `device.py:6`
- `argparse` — `args.py:27`, `repl.py:17`
- `cmd` — `repl.py:19`
- `importlib` — `repl.py:20`, `loader.py:23`
- `json`, `subprocess`, `unittest`, `tempfile`, `os`, `sys` — already used in tests/scripts

No new dependencies. Matplotlib is deferred to Phase 6.

### Closure-based pure-function strategy contract

**Source:** Phase 1 D-13 (referenced in `loader.py:9-15`, `CONVENTIONS.md` §"Function Design").

**Apply to:** `wrap_with_agent` — returns a function with identical 8-arg signature; no module-level state; simulator sees it as just another strategy. Aligns with `EXPECTED_PARAMS` invariant from `loader.py:31`.

### `STRATEGIES` registry untouched

**Source:** Phase 3 D-49 `BUILTIN_STRATEGIES = frozenset(STRATEGIES.keys())` (`sphsim/strategies/__init__.py:26`).

**Apply to:** Phase 4 does NOT add `'rational_agent'` to `STRATEGIES`. Agent wraps strategies at the CLI layer (after read from registry, before simulator build). Documented in CONTEXT.md `<canonical_refs>` line 116.

### Fail-fast argparse mutex with Polish errors

**Source:** Phase 3 D-44 mutex pattern (`args.py:38-44`) + soft-validate idiom (`main.py:17-19`).

**Apply to:** New `--compare-agent` ∧ `--no-agent` mutex (D-60) AND `--compare-agent` ∧ `--interactive` mutex. Use `p.error("Polish message.")` for hard errors (exits 2 with usage line).

### Polish module docstring with v1.0 / decision references

**Source:** `incentive.py:1-2`, `device.py:1-5`, `simulator.py:1`, `loader.py:1-22`.

**Apply to:** `sphsim/agent/rational.py` opening 1–5 lines should reference the formula source (`incentive.py:6-18`) and the relevant Phase 4 decisions (`D-53/D-54/D-65`).

### Deterministic random seed

**Source:** `simulator.py:13` (`random.seed(seed)` in `__init__`).

**Apply to:** `run_compare` runs `SPHSimulator(...)` twice in succession; each `__init__` reseeds (D-Claude's-Discretion: same seed for both, deterministic comparison). No external reseeding needed — pattern is already correct in CONTEXT.md `<code_context>` §4.

---

## No Analog Found

Every Phase 4 file has a strong analog in the existing codebase. The closest-to-novel construct is `run_compare` / `format_compare` (no precedent for dual-simulator comparison output), but the structural parts (loop + delta dict + tabular print) all derive from existing fragments (`simulator.run`, `format_human` IC section, JSON serialization).

---

## Metadata

**Analog search scope:**
- `/Users/stanislawnagorski/Documents/STUDIA/sem4/ekonometria 2/sphsim/` (12 files)
- `/Users/stanislawnagorski/Documents/STUDIA/sem4/ekonometria 2/tests/` (2 test files + fixtures dir)
- `/Users/stanislawnagorski/Documents/STUDIA/sem4/ekonometria 2/scripts/` (2 Python scripts + verify shell)

**Files read (full):**
1. `sphsim/strategies/incentive.py` (28 lines) — formula source-of-truth
2. `sphsim/strategies/__init__.py` (27 lines) — registry + BUILTIN_STRATEGIES frozenset
3. `sphsim/strategies/loader.py` (245 lines) — EXPECTED_PARAMS contract + LoaderError pattern
4. `sphsim/core/device.py` (44 lines) — dataclass counter pattern + `__post_init__`
5. `sphsim/core/simulator.py` (151 lines) — ABSTAIN branch + ic_per_phase aggregation
6. `sphsim/cli/args.py` (66 lines) — argparse mutex + boolean flag pattern
7. `sphsim/cli/main.py` (73 lines) — built-in/custom dual branch + SPHSimulator build
8. `sphsim/cli/output.py` (65 lines) — IC section template + format_json
9. `sphsim/cli/repl.py` (256 lines) — do_run template for do_compare + do_help
10. `sphsim/config.py` (14 lines) — DEFAULT_K0 = 100 (=`expected_P` default)
11. `sphsim/__init__.py` (7 lines) — public API export style
12. `scripts/regression_check.py` (187 lines) — DRY import of INVOCATIONS
13. `scripts/generate_baseline.py` (127 lines) — canonical INVOCATIONS list
14. `tests/test_loader.py` (396 lines) — test style template for test_agent.py
15. `tests/test_strategy_meta_consistency.py` (173 lines) — invariant test (verify not broken)
16. `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` (68 lines) — fixture shape

**Pattern extraction date:** 2026-05-27
