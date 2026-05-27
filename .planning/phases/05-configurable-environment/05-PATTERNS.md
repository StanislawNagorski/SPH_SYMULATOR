# Phase 5: Configurable Environment — Pattern Map

**Mapped:** 2026-05-27
**Files analyzed:** 8 new/modified files
**Analogs found:** 8 / 8 (all have at least role-match analogs; no file is net-new without precedent)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `sphsim/cli/args.py` | CLI parsing | request-response | `sphsim/cli/args.py` (self — extend) | exact |
| `sphsim/core/model.py` | pure math / preset dispatch | transform | `sphsim/core/model.py` (self — extend) | exact |
| `sphsim/core/simulator.py` | simulation orchestrator | CRUD | `sphsim/core/simulator.py` (self — extend constructor) | exact |
| `sphsim/cli/main.py` | CLI entry point / data flow | request-response | `sphsim/cli/main.py` (self — extend) | exact |
| `sphsim/cli/output.py` | output formatting | transform | `sphsim/cli/output.py` (self — add function) | exact |
| `sphsim/cli/repl.py` | interactive REPL | event-driven | `sphsim/cli/repl.py` (self — extend fake_args) | exact |
| `tests/test_env.py` | test — unit + integration | request-response | `tests/test_args_agent_flags.py` + `tests/test_agent.py` | role-match |
| `scripts/verify_phase5.sh` | exit-gate shell script | batch | `scripts/verify_phase4.sh` | exact |
| `scripts/regression_check.py` | regression harness | batch | `scripts/regression_check.py` (self — extend SKIP_KEYS) | exact |

---

## Pattern Assignments

### `sphsim/cli/args.py` (CLI parsing, request-response)

**Role in Phase 5:** Add `--K0`, `--phi`, `--rho`, `--valuation` flags to the environment params block. Introduce two `type=` converter functions (`_parse_phi_list`, `_parse_rho_list`) at module level before `parse_args()`.

**Analog:** `sphsim/cli/args.py` itself — extend in-place.

**Imports pattern** (`args.py` lines 27–30):
```python
import argparse
from sphsim.strategies import STRATEGIES, BUILTIN_STRATEGIES
from sphsim.config import DEFAULT_NU, DEFAULT_NSUS, DEFAULT_K1, DEFAULT_T, DEFAULT_KAPPA, DEFAULT_ALPHA
```

**Deviation:** Phase 5 must add `DEFAULT_K0, DEFAULT_PHI, DEFAULT_RHO` to the import from `sphsim.config` (line 29).

**Existing env-param flag pattern** (`args.py` lines 57–63 — the block Phase 5 extends after):
```python
p.add_argument('--nU',   type=int,   default=DEFAULT_NU,    help=f'Liczba urządzeń (def {DEFAULT_NU})')
p.add_argument('--nSUS', type=int,   default=DEFAULT_NSUS,  help=f'Pojemność SUS (def {DEFAULT_NSUS})')
p.add_argument('--K1',   type=float, default=DEFAULT_K1,    help=f'Górna granica waluacji (def {DEFAULT_K1})')
p.add_argument('--T',    type=int,   default=DEFAULT_T,     help=f'Liczba cykli (def {DEFAULT_T})')
p.add_argument('--kappa',type=float, default=DEFAULT_KAPPA, help=f'Koszt dostarczenia (def {DEFAULT_KAPPA})')
p.add_argument('--alpha',type=float, default=DEFAULT_ALPHA, help=f'Wykładnik h(i)=i^alpha (def {DEFAULT_ALPHA})')
p.add_argument('--seed', type=int,   default=42,            help='Ziarno losowe (def 42)')
```

**`choices=` flag analog** (`args.py` line 41 — pattern for `--valuation` choices):
```python
mutex.add_argument('--strategy', choices=list(BUILTIN_STRATEGIES),
                   help='Strategia: ' + ', '.join(sorted(BUILTIN_STRATEGIES)))
```

**Post-parse error pattern** (`args.py` lines 71–75 — D-60 style for any post-parse checks):
```python
if args.compare_agent and args.no_agent:
    p.error("Flagi --compare-agent i --no-agent są wzajemnie wykluczające.")
if args.compare_agent and args.interactive:
    p.error("Flaga --compare-agent nie działa w trybie --interactive.")
```

**Comma-separated string precedent** (`args.py` line 48 — existing pattern but WITHOUT `type=` converter, which Phase 5 improves upon):
```python
p.add_argument('--probs', type=str, default='0.9,0.7,0.5,0.3,0.0',
               help='[phase_prob] P(COMMIT) per faza, po przecinku')
```

**Deviation for Phase 5:** `--phi` and `--rho` use `type=_parse_phi_list` / `type=_parse_rho_list` instead of `type=str`. This moves validation into argparse (raises `argparse.ArgumentTypeError` immediately with Polish message) rather than deferring to runtime. The converter functions are defined at module level above `parse_args()` — there is NO existing `type=` converter function in this codebase; Phase 5 introduces this pattern for the first time.

**New flags to add** (insert after `--K1` line, before `--T`):
```python
p.add_argument('--K0',       type=float, default=DEFAULT_K0,
               help=f'Dolny próg waluacji K0 (def {DEFAULT_K0})')
p.add_argument('--phi',      type=_parse_phi_list, default=DEFAULT_PHI,
               metavar='p1,..,p5',
               help='Profile awarii φ (5 liczb w [0,1], def: 0.1,0.2,0.3,0.4,1.0)')
p.add_argument('--rho',      type=_parse_rho_list, default=DEFAULT_RHO,
               metavar='r1,..,r5',
               help='Koszty naprawy ρ (5 liczb ≥ 0, def: 0.5,0.5,0.7,1.5,3.0)')
p.add_argument('--valuation', choices=['window', 'step', 'linear'], default='window',
               help='Preset funkcji waluacji g(u) (def: window = tryb v1.0)')
```

**`type=` converter pattern — NO analog exists; Phase 5 introduces it:**
```python
def _parse_phi_list(s: str) -> list:
    try:
        vals = [float(x.strip()) for x in s.split(',')]
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Nieprawidłowy format --phi: '{s}'. Oczekiwano 5 liczb po przecinku, np. 0.1,0.2,0.3,0.4,1.0"
        )
    if len(vals) != 5:
        raise argparse.ArgumentTypeError(
            f"--phi wymaga dokładnie 5 wartości (podano {len(vals)}): '{s}'"
        )
    for i, v in enumerate(vals):
        if not (0.0 <= v <= 1.0):
            raise argparse.ArgumentTypeError(
                f"--phi[{i+1}]={v} poza zakresem [0, 1]. Wszystkie wartości φ muszą być w [0, 1]."
            )
    return vals
```

(`_parse_rho_list` is identical in shape; range check is `v < 0.0` with message "Wszystkie wartości ρ muszą być ≥ 0".)

---

### `sphsim/core/model.py` (pure math / preset dispatch, transform)

**Role in Phase 5:** Extend `valuation()` to accept a `preset='window'` parameter and dispatch to three functional forms. Extend `sph_stp()` to accept and thread the same `preset` parameter.

**Analog:** `sphsim/core/model.py` itself — extend in-place.

**Current full file** (lines 1–34):
```python
# Funkcje modelu — pure (bez side effects, bez random.*).
from typing import Tuple

def valuation(u, K0, K1):
    if K1 == float('inf'):
        return float(K0) if u >= K0 else 0.0
    return float(K0) if K0 <= u <= K1 else 0.0

def sph_stp(u, s, nSUS, K0, K1):
    """Zwraca (z*, y*) max-izujące P = g(u-x)+x, x=z-y."""
    def P_of_x(x):
        return valuation(u - x, K0, K1) + x
    ...
    candidates = [x_min, x_max, K0 - u]
    if K1 != float('inf'):
        candidates.append(K1 - u)
    ...
```

**Deviation for Phase 5:** Replace `valuation(u, K0, K1)` with `valuation(u, K0, K1, preset='window')` — add `preset` parameter with default `'window'` to maintain full backward compatibility. The window branch is the existing body verbatim. Add `step` and `linear` branches above it. Update `sph_stp` signature to `sph_stp(u, s, nSUS, K0, K1, preset='window')` and pass `preset` into the `P_of_x` closure call. The candidate search list (`K0 - u`, `K1 - u` breakpoints) is unchanged for Phase 5.

**New `valuation` body:**
```python
def valuation(u, K0, K1, preset='window'):
    if preset == 'step':
        return float(K0) if u >= K0 else 0.0
    if preset == 'linear':
        if K1 == float('inf') or K1 <= 0:
            return float(K0) if u >= K0 else 0.0
        return float(K0) * min(float(u), float(K1)) / float(K1)
    # default: window (v1.0 compatible)
    if K1 == float('inf'):
        return float(K0) if u >= K0 else 0.0
    return float(K0) if K0 <= u <= K1 else 0.0
```

**`sph_stp` inner lambda update** (line 16 in current file → becomes):
```python
def P_of_x(x):
    return valuation(u - x, K0, K1, preset) + x
```

**Critical:** `sph_stp` is called at `simulator.py:~line 80` as `sph_stp(u, self.s, self.nSUS, self.K0, self.K1)`. After this change, calls become `sph_stp(u, self.s, self.nSUS, self.K0, self.K1, self.valuation_preset)`. The simulator must also be updated (see below).

---

### `sphsim/core/simulator.py` (orchestrator, CRUD)

**Role in Phase 5:** Add `valuation_preset='window'` to the `__init__` constructor. Store as `self.valuation_preset`. Thread it into the two call sites of `sph_stp` and `valuation` inside `run()`.

**Analog:** `sphsim/core/simulator.py` itself — extend in-place.

**Current constructor signature** (`simulator.py` lines 7–8):
```python
def __init__(self, nU, nSUS, K0, K1, F, T, kappa, alpha,
             phi, rho, strategy_fn, params, seed=42):
```

**Deviation for Phase 5:** Add `valuation_preset='window'` as last keyword argument (before `seed`):
```python
def __init__(self, nU, nSUS, K0, K1, F, T, kappa, alpha,
             phi, rho, strategy_fn, params, valuation_preset='window', seed=42):
    ...
    self.valuation_preset = valuation_preset
```

The two call sites inside `run()` that invoke `sph_stp` and `valuation` directly must pass `self.valuation_preset`. The existing pattern from `simulator.py` line 4:
```python
from sphsim.core.model import valuation, sph_stp
```
remains unchanged.

---

### `sphsim/cli/main.py` (CLI entry point, request-response)

**Role in Phase 5:** (a) Replace three `DEFAULT_K0 / DEFAULT_PHI / DEFAULT_RHO` hard-codes with `args`-derived values. (b) Thread `valuation_preset` into both `SPHSimulator` instantiations and into `run_compare`.

**Analog:** `sphsim/cli/main.py` itself — extend in-place.

**Current hard-coded DEFAULT_* pattern** (`main.py` lines 25–29 — `run_compare` common dict):
```python
common = dict(
    nU=args.nU, nSUS=args.nSUS, K0=DEFAULT_K0, K1=K1,
    F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
    phi=DEFAULT_PHI, rho=DEFAULT_RHO, params=params, seed=args.seed,
)
```

**Deviation:** Replace with:
```python
K0 = args.K0
phi = args.phi
rho = args.rho
valuation_preset = args.valuation

common = dict(
    nU=args.nU, nSUS=args.nSUS, K0=K0, K1=K1,
    F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
    phi=phi, rho=rho, valuation_preset=valuation_preset,
    params=params, seed=args.seed,
)
```

**Current SPHSimulator instantiation pattern** (`main.py` lines 91–96 and lines 127–133 — both branches use same shape):
```python
sim = SPHSimulator(
    nU=args.nU, nSUS=args.nSUS, K0=DEFAULT_K0, K1=K1,
    F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
    phi=DEFAULT_PHI, rho=DEFAULT_RHO,
    strategy_fn=strategy_fn, params=params, seed=args.seed,
)
```

**Deviation:** Both instantiations replace `K0=DEFAULT_K0`, `phi=DEFAULT_PHI`, `rho=DEFAULT_RHO` with `K0=K0`, `phi=phi`, `rho=rho` (resolved above), and add `valuation_preset=valuation_preset`.

**`--seed` flow precedent** (`args.py:63`, `main.py:127`): `args.seed` → `seed=args.seed` in SPHSimulator constructor — exact same pass-through pattern applies for `args.K0`, `args.phi`, `args.rho`, `args.valuation`.

**Import line to update** (`main.py` line 8):
```python
from sphsim.config import DEFAULT_K0, DEFAULT_F, DEFAULT_PHI, DEFAULT_RHO
```
After Phase 5, `DEFAULT_K0`, `DEFAULT_PHI`, `DEFAULT_RHO` are no longer needed as direct pass-throughs in `main.py` (they come from `args.*`). `DEFAULT_F` still required. Remove the unused three from the import, or retain them for the `run_compare` fallback if REPL is not updated.

---

### `sphsim/cli/output.py` (output formatting, transform)

**Role in Phase 5:** Add `format_config_header(args, K0, K1, phi, rho) -> str` function. Call it at the top of `format_human` (always-on, not behind a flag). Extend the `env` block in `format_json` with new fields.

**Analog:** `sphsim/cli/output.py` — `format_human` (lines 96–169) and `format_json` (lines 6–22).

**`format_human` banner pattern** (lines 101–106 — the two-line header Phase 5 extends before):
```python
lines = []
sep = '─' * 62
lines.append(f"\n{'='*62}")
lines.append(f"  SPH SYMULATOR  |  Strategia: {args.strategy.upper()}")
lines.append(f"  nU={args.nU}, nSUS={args.nSUS}, K1={K1}, T={args.T}, κ={args.kappa}, α={args.alpha}")
lines.append(f"{'='*62}")
```

**Deviation:** `format_config_header(args, K0, K1, phi, rho)` is inserted before `lines.append(f"\n{'='*62}")`. It returns a standalone Markdown table string. `format_human` calls it and appends its result at the very top of `lines`. The function signature:
```python
def format_config_header(args, K0, K1, phi, rho) -> str:
    """Serializuje konfigurację środowiska do tabeli Markdown (ENV-03, SC-4)."""
```

**f-string MD table pattern** — existing `format_compare` (lines 55–56) shows the established per-line f-string style:
```python
lines.append(f"  {'KPI':<24}  {'with-agent':>12}  {'bez agenta':>12}  {'Δ (with-no)':>12}")
lines.append(f"  {sep_wide}")
```

**`format_json` env block to extend** (`output.py` lines 10–11):
```python
'env': {'nU': args.nU, 'nSUS': args.nSUS, 'K1': K1,
        'T': args.T, 'kappa': args.kappa, 'alpha': args.alpha},
```

**Deviation:** Add `'K0': K0, 'phi': phi, 'rho': rho, 'seed': args.seed, 'valuation': args.valuation` to the env dict. These new keys must be added to `SKIP_KEYS` in `regression_check.py` (see below) to preserve backward compat.

**REPL constraint:** `format_human` now calls `format_config_header(args, K0, K1, phi, rho)` — the `args` Namespace must have `.phi`, `.rho`, `.K0`, `.valuation`. The REPL `fake_args` must be updated (see `repl.py` section).

---

### `sphsim/cli/repl.py` (REPL, event-driven)

**Role in Phase 5:** Add `phi`, `rho`, `K0`, `valuation` to `fake_args` in both `do_run` (lines 219–222) and `do_compare` (lines 284–287).

**Analog:** `sphsim/cli/repl.py` itself — `fake_args` construction in `do_run` and `do_compare`.

**Current `do_run` fake_args** (`repl.py` lines 219–222):
```python
fake_args = argparse.Namespace(
    strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
    kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
)
```

**Current `do_compare` fake_args** (`repl.py` lines 284–287):
```python
fake_args = argparse.Namespace(
    strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
    kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
)
```

**Deviation:** Both `fake_args` constructions must add four fields so that `format_config_header` can read them without `AttributeError`:
```python
fake_args = argparse.Namespace(
    strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
    kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
    phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window',
)
```

`DEFAULT_K0` is already imported at `repl.py` line 33. `DEFAULT_PHI` and `DEFAULT_RHO` are already imported at `repl.py` line 34. No new imports needed.

The SPHSimulator calls inside `do_run` (lines 209–214) and `do_compare` `common` dict (lines 258–262) hard-code `DEFAULT_*` — these are REPL-specific defaults and are acceptable to leave as-is for Phase 5 (the REPL does not expose `--phi`/`--rho`/`--valuation` CLI flags). The REPL env override via `run naive phi=0.1,...` is deferred (per RESEARCH.md Open Question 1).

---

### `tests/test_env.py` (test — unit + integration, request-response)

**Role in Phase 5:** New file covering ENV-01 (phi/rho parsing + validation), ENV-02 (valuation presets KPI distinguishability), ENV-03 (config header format and content).

**Analog:** `tests/test_args_agent_flags.py` (argparse flag tests) + `tests/test_agent.py` (integration via subprocess).

**File header pattern** (`test_agent.py` lines 1–36):
```python
"""
Unit i integration tests dla ... (Phase N, D-XX/D-YY).
Pokrywa N przypadków:
  1. ...
Stdlib only: unittest + subprocess + json + os + sys
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

PROJECT_ROOT = Path(_PROJECT_ROOT)
MONOLITH = PROJECT_ROOT / 'sph_sim.py'
```

**Unit test class pattern** (`test_args_agent_flags.py` lines 37–65 — argparse unit tests via `sys.argv` manipulation):
```python
class TestArgsAgentFlags(unittest.TestCase):
    def test_default_no_agent_is_false(self):
        from sphsim.cli.args import parse_args
        old_argv = sys.argv
        try:
            sys.argv = ['sph_sim.py', '--strategy', 'naive', '--zeta', '0.5']
            args = parse_args()
            self.assertFalse(args.no_agent, msg=f'..., got {args.no_agent}')
        finally:
            sys.argv = old_argv
```

**Integration test via subprocess pattern** (`test_agent.py` lines 210–238):
```python
def test_compare_agent_json_has_comparison_block(self):
    full_args = [
        sys.executable, str(MONOLITH),
        '--strategy', 'incentive', '--expected_P', '30', '--compare-agent',
        '--seed', '42', '--json',
    ]
    proc = subprocess.run(
        full_args,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    self.assertEqual(proc.returncode, 0, msg=f"exit code {proc.returncode}, stderr: {proc.stderr[:300]}")
    result = json.loads(proc.stdout)
    self.assertIn('comparison', result, msg=f"JSON klucze: {list(result.keys())}")
```

**Validation error (exit 2) test pattern** (`test_args_agent_flags.py` lines 78–88):
```python
def test_mutex_compare_agent_and_no_agent_exit_2(self):
    r = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--compare-agent', '--no-agent')
    self.assertNotEqual(r.returncode, 0, msg=f'..., got rc={r.returncode}')
    self.assertEqual(r.returncode, 2, msg=f'Argparse error powinien dać rc=2, got rc={r.returncode}')
    combined_out = r.stderr + r.stdout
    self.assertTrue('wykluczające' in combined_out, msg=f'...: {combined_out[:400]}')
```

**Deviation for `test_env.py`:** Three test classes:
1. `TestPhiRhoParsing` — unit: `sys.argv` manipulation to test `parse_args()` directly (length=5, range [0,1] for phi, ≥0 for rho, exit-2 errors with Polish messages). Pattern from `test_args_agent_flags.py`.
2. `TestValuationPresets` — integration: subprocess with `--valuation step` / `--valuation linear` / `--valuation window` on same seed+strategy, assert KPI values differ. Pattern from `test_agent.py` subprocess block.
3. `TestConfigHeader` — integration: subprocess human-readable output piped / unit: import `format_config_header` directly and assert all 9 required field names appear in the returned string.

---

### `scripts/verify_phase5.sh` (exit-gate shell script, batch)

**Role in Phase 5:** Verify all 4 Phase 5 ROADMAP Success Criteria + regression + full test suite.

**Analog:** `scripts/verify_phase4.sh` (lines 1–192) — exact structural copy with Phase 5 content.

**Script skeleton pattern** (`verify_phase4.sh` lines 1–64):
```bash
#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  verify_phase4.sh — phase exit gate dla Phase 4 ...
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

cd "$(dirname "$0")/.."

if command -v python >/dev/null 2>&1; then
    PY=python
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "FATAL: ani 'python' ani 'python3' nie ma w PATH" >&2
    exit 1
fi

trap 'rm -f /tmp/p4_*' EXIT   # Phase 5: change prefix to /tmp/p5_*

PASS=0
FAIL=0

check() {
    local desc="$1"
    local cmd="$2"
    if eval "$cmd" > /tmp/p4_check.log 2>&1; then
        echo "[PASS] $desc"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $desc"
        echo "       cmd: $cmd"
        echo "       log:"
        sed 's/^/         /' /tmp/p4_check.log | head -20
        FAIL=$((FAIL + 1))
    fi
}
```

**JSON-pipe check pattern** (`verify_phase4.sh` lines 93–98):
```bash
check "SC #1 (naive): agent_enabled==true w domyślnym uruchomieniu" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --seed 42 --json 2>/dev/null | \
     $PY -c \"import json,sys; d=json.load(sys.stdin); assert d['metrics']['agent_enabled'] is True, ...\""
```

**Human-readable grep pattern** (`verify_phase4.sh` lines 122–124):
```bash
check "SC #3 (human): sekcja 'VETO przez RationalAgent' widoczna" \
    "$PY sph_sim.py --strategy phase_prob --probs 1.0,1.0,1.0,1.0,0.0 --seed 42 2>/dev/null | \
     grep 'VETO przez RationalAgent' > /dev/null"
```

**Exit code pattern** (`verify_phase4.sh` lines 183–192):
```bash
echo ""
echo "════════════════════════════════════════"
echo "  Phase 4 verification: PASS=$PASS / FAIL=$FAIL"
echo "════════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
    echo "✗ Phase 4 NIE jest gotowe — popraw FAIL'e powyżej."
    exit 1
fi
echo "✓ Phase 4 ready for /gsd:verify-work"
exit 0
```

**Deviation for Phase 5:** Change all `p4_` prefixes to `p5_`. Write checks for:
- SC #1: `--phi 0.1,0.2,0.3,0.4,1.0` accepted (exit 0); `--phi` with length != 5 exits 2; phi value > 1.0 exits 2; rho negative exits 2
- SC #2: `--valuation window|step|linear` accepted (exit 0); `--K0 90 --K1 150` accepted (exit 0)
- SC #3: `--valuation step` KPI != `--valuation window` KPI (same seed) — via JSON comparison in a small inline Python `-c` script
- SC #4: human-readable output contains "Konfiguracja środowiska" and all 9 parameter names
- Regression: `$PY scripts/regression_check.py` (should pass after SKIP_KEYS extended)
- Full test suite: `$PY -m unittest discover tests`
- `test_env.py` specifically: `$PY -m unittest tests.test_env`

---

### `scripts/regression_check.py` (regression harness, batch)

**Role in Phase 5:** Extend `SKIP_KEYS` to include the 5 new JSON env fields added by Phase 5.

**Analog:** `scripts/regression_check.py` itself — extend in-place.

**Current SKIP_KEYS** (`regression_check.py` line 41):
```python
SKIP_KEYS = ('veto_per_phase', 'n_vetoed_total', 'agent_enabled')
```

**Deviation:** Add the 5 new env-level keys that Phase 5 injects into the `env` block of JSON output:
```python
SKIP_KEYS = (
    'veto_per_phase', 'n_vetoed_total', 'agent_enabled',  # Phase 4
    'K0', 'phi', 'rho', 'seed', 'valuation',              # Phase 5
)
```

**D-67 rationale comment** (`regression_check.py` lines 36–41 — copy the established comment style):
```python
# Phase 5 D-XX (Strategia B): nowe klucze w env bloku (K0, phi, rho, seed, valuation)
# ignorowane przy compare z baseline_v1 fixtures — fixtures nie zawierają tych pól.
```

No other change to `regression_check.py`. The `deep_diff` function already handles extra keys in nested dicts via `SKIP_KEYS` filtering at line 60–61:
```python
ek = set(expected.keys()) - set(SKIP_KEYS)
ak = set(actual.keys()) - set(SKIP_KEYS)
```

---

## Shared Patterns

### Polish UX in all user-facing strings (D-17)
**Source:** `sphsim/cli/args.py` lines 46–69 (all help strings), `sphsim/cli/output.py` lines 104–159 (all section headings)
**Apply to:** All new argparse `help=` strings, all `ArgumentTypeError` messages, all new `format_config_header` section labels
**Pattern:** English identifiers and code comments are fine. Everything a user reads (argparse help, error messages, output section headers, REPL messages) is in Polish.

### `argparse.Namespace` + f-string formatting
**Source:** `sphsim/cli/output.py` lines 96–169
**Apply to:** `format_config_header` — reads `args.*` attributes, formats with f-strings per line, `'\n'.join(lines)` pattern

### `type=` default value in argparse — list default
**Source:** `sphsim/cli/args.py` line 48 (`--probs`, `type=str`)
**Deviation:** `--phi`/`--rho` use `type=_parse_phi_list` with `default=DEFAULT_PHI` (a list). When the flag is absent, argparse returns the default directly without calling the converter. This is correct stdlib argparse behaviour — no special handling needed.

### subprocess integration test pattern
**Source:** `tests/test_agent.py` lines 207–238, `tests/test_args_agent_flags.py` lines 26–34
**Apply to:** `TestValuationPresets` and `TestConfigHeader` integration tests in `test_env.py`
```python
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PROJECT_ROOT = Path(_PROJECT_ROOT)
MONOLITH = PROJECT_ROOT / 'sph_sim.py'

proc = subprocess.run(
    [sys.executable, str(MONOLITH), ...flags...],
    cwd=str(PROJECT_ROOT), capture_output=True, text=True,
)
self.assertEqual(proc.returncode, 0, msg=f"exit code {proc.returncode}, stderr: {proc.stderr[:300]}")
```

### Exit-gate shell script structure
**Source:** `scripts/verify_phase4.sh` lines 29–64 (`set -euo pipefail`, `cd`, Python detection, `trap`, `check()` function, PASS/FAIL counters)
**Apply to:** `scripts/verify_phase5.sh` — copy this skeleton verbatim, only change prefix `p4_` → `p5_` and add Phase 5-specific check bodies

---

## No Analog Found

All 8 files have analogs. The one genuinely novel pattern is:

| Pattern | Reason |
|---------|--------|
| `type=` converter function (`_parse_phi_list`, `_parse_rho_list`) in `args.py` | No existing `type=` converter in the codebase — `--probs` uses `type=str` and defers parsing. Phase 5 introduces the argparse `ArgumentTypeError` pattern for the first time. |

The absence of a codebase analog for `type=` converters is documented in RESEARCH.md §A.5 and §C.9. The Python stdlib pattern is well-defined and requires no external reference.

---

## Metadata

**Analog search scope:** `sphsim/cli/`, `sphsim/core/`, `tests/`, `scripts/`
**Files read:** 10 source files (args.py, main.py, repl.py, output.py, model.py, simulator.py, config.py, test_agent.py, test_args_agent_flags.py, regression_check.py, verify_phase4.sh)
**Pattern extraction date:** 2026-05-27
