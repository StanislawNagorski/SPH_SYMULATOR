# Coding Conventions

**Analysis Date:** 2025-01-31

## Language & Context

**Primary language:** Python 3 (shebang `#!/usr/bin/env python3`)
**Domain language:** Polish — all user-facing strings, comments, variable labels, and docstrings are in Polish.
**Academic context:** Econometrics/game-theory simulation; clarity and mathematical fidelity take priority over enterprise patterns.

---

## Naming Patterns

**Files:**
- `snake_case` for Python files: `sph_sim.py`
- Single-file script pattern; no package/module hierarchy

**Constants:**
- `SCREAMING_SNAKE_CASE` with `DEFAULT_` prefix for all module-level defaults:
  ```python
  DEFAULT_NU    = 250
  DEFAULT_NSUS  = 20
  DEFAULT_K0    = 100
  DEFAULT_K1    = 120
  DEFAULT_KAPPA = 0.25
  DEFAULT_PHI   = [0.1, 0.2, 0.3, 0.4, 1.0]
  ```
- Registry dict in `SCREAMING_SNAKE_CASE`: `STRATEGIES = { 'naive': strategy_naive, ... }`

**Functions:**
- `snake_case`: `valuation()`, `sph_stp()`, `parse_args()`, `main()`
- Strategy functions prefixed with `strategy_`: `strategy_naive`, `strategy_threshold`, `strategy_phase_prob`, `strategy_incentive`, `strategy_adaptive`

**Classes:**
- `PascalCase`: `Device`, `SPHSimulator`

**Instance variables:**
- Short `snake_case`, often mirroring mathematical symbols from the model:
  ```python
  self.nU, self.nSUS, self.K0, self.K1
  self.phi, self.rho, self.kappa, self.alpha
  self.strategy_fn, self.params
  ```
- Loop-local variables use short, math-aligned names: `u`, `z`, `y`, `l_prev`, `l_curr`, `idx`, `fp`, `pay`

**CLI arguments:**
- `--snake_case` flags matching parameter names from the academic model: `--max_phase`, `--s_target`, `--expected_P`, `--nU`, `--nSUS`

---

## Code Style

**Formatting:**
- No formatter config detected (no `.prettierrc`, `pyproject.toml`, or `.flake8` present)
- Vertical alignment of related assignments using extra spaces:
  ```python
  DEFAULT_NU    = 250
  DEFAULT_NSUS  = 20
  DEFAULT_K0    = 100
  ```
- Inline assignments on single lines for compact dataclass-like init:
  ```python
  self.nU, self.nSUS, self.K0, self.K1 = nU, nSUS, K0, K1
  self.F, self.T, self.kappa, self.alpha = F, T, kappa, alpha
  ```

**Linting:**
- No linting configuration detected; standard PEP 8 is the implied guide

**Line length:**
- Kept reasonably short; long print statements broken with implicit continuation

**Section separators:**
- Unicode box-drawing lines used to delimit logical sections in source:
  ```python
  # ──────────────────────────────────────────────────────────────
  # PARAMETRY DOMYŚLNE (z dokumentu)
  # ──────────────────────────────────────────────────────────────
  ```
- Section headers in Polish, ALL CAPS

---

## Import Organization

**Order (as observed in `sph_sim.py`):**
1. Standard library — stdlib only, no third-party dependencies:
   ```python
   import argparse
   import json
   import random
   import math
   from dataclasses import dataclass
   from typing import List, Tuple, Dict
   ```

**Path aliases:** None — single flat file, no relative imports

---

## Module / File Design

**Single-file script pattern:**
- Entire simulation lives in `sph_sim.py`
- Protected entry point at the bottom:
  ```python
  if __name__ == '__main__':
      main()
  ```

**Exports:** None — script, not a library; no `__all__`

**Barrel files:** Not applicable

---

## Type Annotations

**Usage:** Partial — `typing` is imported (`List`, `Tuple`, `Dict`) but annotations are applied only on the `Device` dataclass fields, not on free functions or `SPHSimulator` methods:
```python
@dataclass
class Device:
    id: int
    phase: int
    status: str
    down_left: int = 0
    earnings: float = 0.0
```
Free functions like `valuation()`, `sph_stp()`, and all `strategy_*` functions have no signatures annotated.

---

## Docstrings & Comments

**Module-level docstring:**
- Full multi-line docstring at top of file acting as user manual (Polish), covering usage, examples, and strategy descriptions
- Wrapped in triple-quoted `"""..."""`

**Function docstrings:**
- Sparse — only `sph_stp()` has a one-line docstring; other functions are undocumented:
  ```python
  def sph_stp(u, s, nSUS, K0, K1):
      """Zwraca (z*, y*) max-izujące P = g(u-x)+x, x=z-y."""
  ```

**Inline comments:**
- Polish-language inline comments explain mathematical intent, not mechanics:
  ```python
  # Parametry strategii
  # Parametry środowiska
  ```

**`@property` usage:**
- Used on `Device` for derived computation:
  ```python
  @property
  def net_profit(self):
      return self.earnings - self.costs
  ```

---

## Error Handling

**Strategy:** Minimal — academic script, no exception handling blocks observed.

**Patterns:**
- Guard clauses at top of strategy functions:
  ```python
  if dev.status != 'UP':
      return 'ABSTAIN'
  if idx >= len(phi) or phi[idx] >= 1.0:
      return 'ABSTAIN'
  ```
- Defensive division guard using `max(…, 1)`:
  ```python
  deliv_ratio = total_deliv / max(total_dec, 1)
  ```
- Infinity handling via explicit check:
  ```python
  K1 = float('inf') if args.K1 < 0 else args.K1
  if K1 == float('inf'):
      return float(K0) if u >= K0 else 0.0
  ```
- No `try/except` blocks anywhere in the codebase.

---

## Logging

**Framework:** None — `print()` only.

**Patterns:**
- Default output: formatted human-readable table with Unicode box-drawing characters, Polish labels
- JSON output mode enabled by `--json` flag: prints `json.dumps(out, indent=2)` to stdout
- Verbose mode enabled by `--verbose` flag: prints sampled history every 100 cycles
- No log levels, no file logging

---

## CLI Interface

**Framework:** `argparse` (`parse_args()` in `sph_sim.py`)

**Pattern:**
- All simulation parameters exposed as CLI flags with defaults matching the academic model
- `--strategy` is the only required argument
- `--json` and `--verbose` are boolean switches for output format
- Strategy-specific params are always parsed even when the selected strategy ignores them

---

## Function Design

**Size:** Functions are short; strategy functions are 5–10 lines each. `SPHSimulator.run()` is the longest block (~80 lines) as it contains the main simulation loop.

**Parameters:** Strategy functions share a uniform signature to enable dict-based dispatch:
```python
def strategy_*(dev, l, s, phi, kappa, rho, h, p) -> str:
    ...
```

**Return values:**
- Strategy functions return string literals `'COMMIT'` or `'ABSTAIN'` (not enums)
- `SPHSimulator.run()` returns a plain `dict` of metrics plus raw `history` and `devices` lists

---

## Data Structures

**`@dataclass`** for `Device` — mutable, all fields default to 0/0.0 where appropriate.
**Plain `dict`** for simulation results and strategy params — no typed result objects.
**Plain `list`** for time-series history: `self.history = {k: [] for k in [...]}`.
**Lambda** for the weighting function `h`:
```python
self.h = (lambda i: i ** alpha) if alpha > 0 else (lambda i: 1.0)
```

---

*Convention analysis: 2025-01-31*
