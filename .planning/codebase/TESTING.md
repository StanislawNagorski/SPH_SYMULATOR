# Testing Patterns

**Analysis Date:** 2025-01-31

## Current State

**No test files exist in this project.**

The codebase consists of a single simulation script (`sph_sim.py`) with no accompanying test suite, test configuration, or testing infrastructure. This is consistent with the academic context (econometrics course project).

---

## Test Framework

**Runner:** Not configured

**Assertion Library:** Not configured

**Run Commands:**
```bash
# No test commands defined
# Script is run directly:
python sph_sim.py --strategy naive --zeta 0.5
python sph_sim.py --strategy phase_prob --probs 1.0,0.8,0.6,0.2,0.0 --json
```

---

## Testable Units (Recommendations for Adding Tests)

The following functions/classes are the best candidates for unit tests if a test suite is added:

### Pure Functions (Easiest to Test)

**`valuation(u, K0, K1)` in `sph_sim.py` line 53:**
```python
# Examples of verifiable behaviour:
assert valuation(100, 100, 120) == 100.0   # lower bound
assert valuation(120, 100, 120) == 100.0   # upper bound
assert valuation(99, 100, 120)  == 0.0     # below window
assert valuation(121, 100, 120) == 0.0     # above window
assert valuation(100, 100, float('inf')) == 100.0  # inf K1 path
assert valuation(99, 100, float('inf'))   == 0.0
```

**`sph_stp(u, s, nSUS, K0, K1)` in `sph_sim.py` line 58:**
```python
# Returns (z*, y*) tuple — verifiable with known boundary cases
z, y = sph_stp(110, 5, 20, 100, 120)
assert isinstance(z, int) and isinstance(y, int)
assert z >= 0 and y >= 0          # cannot simultaneously withdraw and deposit
```

### Strategy Functions (Require Mocking `random`)

All five strategy functions (`strategy_naive`, `strategy_threshold`, `strategy_phase_prob`, `strategy_incentive`, `strategy_adaptive`) in `sph_sim.py` lines 104–149 share the same signature and return `'COMMIT'` or `'ABSTAIN'`. They are testable by:
- Constructing a `Device` instance directly (dataclass, no constructor logic)
- Patching `random.random()` to return a fixed value

```python
# Example pattern (using unittest.mock):
from unittest.mock import patch
from dataclasses import replace

dev_up = Device(id=0, phase=1, status='UP')
dev_down = Device(id=1, phase=-1, status='DOWN')

# DOWN device must always ABSTAIN
assert strategy_naive(dev_down, [], 5, [], 0.25, [], lambda i: i, {}) == 'ABSTAIN'

# UP device with zeta=1.0 always COMMITs
with patch('random.random', return_value=0.0):
    result = strategy_naive(dev_up, [], 5, [], 0.25, [], lambda i: i, {'zeta': 1.0})
    assert result == 'COMMIT'
```

### `SPHSimulator` Class (Integration-level)

**`sph_sim.py` line 162** — constructor and `.run()` method:
```python
# Deterministic with seed=42; run() output is reproducible
sim = SPHSimulator(
    nU=50, nSUS=10, K0=100, K1=120, F=5, T=100,
    kappa=0.25, alpha=1, phi=[0.1,0.2,0.3,0.4,1.0],
    rho=[0.5,0.5,0.7,1.5,3.0],
    strategy_fn=strategy_naive, params={'zeta': 0.5}, seed=42
)
res = sim.run()
assert 'avg_val_last100' in res
assert 'cum_val_total' in res
assert isinstance(res['history']['val'], list)
assert len(res['history']['val']) == 100
```

---

## Recommended Test Structure (If Tests Are Added)

**Framework:** `pytest` (standard Python, zero config needed)

**File placement:** Co-located or in a `tests/` directory:
```
ekonometria 2/
├── sph_sim.py
└── tests/
    ├── test_valuation.py       # Pure function tests
    ├── test_sph_stp.py         # Pure function tests
    ├── test_strategies.py      # Strategy function tests (mock random)
    └── test_simulator.py       # SPHSimulator integration tests
```

**Install command:**
```bash
pip install pytest
```

**Run command:**
```bash
pytest tests/ -v
```

---

## Mocking

**Framework:** `unittest.mock` (stdlib) or `pytest-mock`

**What to mock:**
- `random.random` — all strategy functions call it; patching enables deterministic decision testing
- `random.randint` — called in `SPHSimulator.__init__` to set initial device phases; patch to control initial state

**What NOT to mock:**
- `valuation()` and `sph_stp()` — these are the functions under test; mock their callers, not them

```python
# Pattern for mocking random in strategy tests:
import random
from unittest.mock import patch

def test_strategy_naive_always_commits():
    dev = Device(id=0, phase=2, status='UP')
    with patch.object(random, 'random', return_value=0.0):  # 0.0 < any zeta > 0
        result = strategy_naive(dev, [], 5, [], 0.25, [], lambda i: i, {'zeta': 0.9})
    assert result == 'COMMIT'

def test_strategy_naive_always_abstains():
    dev = Device(id=0, phase=2, status='UP')
    with patch.object(random, 'random', return_value=1.0):  # 1.0 >= any zeta <= 1.0
        result = strategy_naive(dev, [], 5, [], 0.25, [], lambda i: i, {'zeta': 0.5})
    assert result == 'ABSTAIN'
```

---

## Fixtures and Factories

No fixtures exist. If added, a `Device` factory is the highest-value fixture:

```python
# Suggested pytest fixture pattern:
import pytest
from sph_sim import Device

@pytest.fixture
def up_device():
    return Device(id=0, phase=1, status='UP')

@pytest.fixture
def down_device():
    return Device(id=1, phase=-1, status='DOWN', down_left=1)
```

**Location:** `tests/conftest.py`

---

## Reproducibility via Seed

The simulator uses `random.seed(seed)` at construction time (`sph_sim.py` line 169). The default seed is `42`. This means:
- Any integration test constructing `SPHSimulator` with `seed=42` will produce identical results across runs
- Output metrics can be hardcoded as regression test expectations

---

## Coverage

**Requirements:** None enforced

**View coverage (once pytest is installed):**
```bash
pip install pytest-cov
pytest tests/ --cov=sph_sim --cov-report=term-missing
```

**Key untested areas (current state — entire codebase):**
- `valuation()` — zero tests; pure function, high testability
- `sph_stp()` — zero tests; contains optimization logic, medium complexity
- All five `strategy_*` functions — zero tests
- `SPHSimulator.__init__` and `.run()` — zero tests
- `parse_args()` / `main()` — zero tests; CLI entry points, can be tested via `subprocess` or `argparse` directly

---

## Test Types

**Unit Tests:**
- Scope: individual functions (`valuation`, `sph_stp`, strategy functions)
- Approach: direct call with controlled inputs, assert return values

**Integration Tests:**
- Scope: full `SPHSimulator` run with small `T` (e.g., 100 cycles) and fixed seed
- Approach: assert output dict keys exist and metric values fall within expected ranges

**E2E Tests:**
- Framework: Not configured
- Can be approximated by running `sph_sim.py` as subprocess and parsing `--json` output:
  ```python
  import subprocess, json
  result = subprocess.run(
      ['python', 'sph_sim.py', '--strategy', 'naive', '--zeta', '0.5', '--T', '100', '--json'],
      capture_output=True, text=True
  )
  data = json.loads(result.stdout)
  assert data['metrics']['avg_val_last100'] >= 0
  ```

---

## Common Patterns (To Establish)

**Async Testing:** Not applicable — synchronous simulation only

**Parametric testing with `pytest.mark.parametrize`** is well-suited for strategy comparison:
```python
@pytest.mark.parametrize("strategy,params,min_expected_val", [
    ('naive',      {'zeta': 0.75},                     80.0),
    ('threshold',  {'max_phase': 3},                    15.0),
    ('phase_prob', {'probs': '0.9,0.8,0.7,0.4,0.0'},  70.0),
])
def test_strategy_produces_value(strategy, params, min_expected_val):
    sim = SPHSimulator(..., strategy_fn=STRATEGIES[strategy], params=params, seed=42)
    res = sim.run()
    assert res['avg_val_last100'] >= min_expected_val
```

---

*Testing analysis: 2025-01-31*
