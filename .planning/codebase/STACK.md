# Technology Stack

**Analysis Date:** 2025-01-31

## Languages

**Primary:**
- Python 3 — entire simulation script (`sph_sim.py`, 363 lines)

**Secondary:**
- None

## Runtime

**Environment:**
- CPython 3 (shebang: `#!/usr/bin/env python3`)
- No virtual environment or `.python-version` file detected

**Package Manager:**
- None — project uses only Python standard library
- No `requirements.txt`, `pyproject.toml`, `setup.py`, or `Pipfile` present
- No lockfile (not applicable)

## Frameworks

**Core:**
- None — pure Python script, no external framework

**Testing:**
- Not applicable — no test framework configured, no test files present

**Build/Dev:**
- None — single-file script executed directly via `python sph_sim.py`

## Key Dependencies

**Standard Library Only (no pip installs required):**
- `argparse` — CLI argument parsing for all strategy and environment parameters
- `json` — structured JSON output mode (`--json` flag)
- `random` — stochastic simulation, seeded via `--seed` (default 42)
- `math` — imported but not directly called in visible logic
- `dataclasses` (`@dataclass`) — `Device` model definition (`sph_sim.py` line 84)
- `typing` (`List`, `Tuple`, `Dict`) — type hints throughout

## Configuration

**Environment:**
- No environment variables used
- No `.env` file present
- All configuration passed exclusively via CLI arguments at runtime

**Key CLI Parameters (runtime config):**
- `--strategy` (required): `naive` | `threshold` | `phase_prob` | `incentive` | `adaptive`
- `--nU` (default 250): number of simulated devices
- `--nSUS` (default 20): SUS buffer capacity
- `--K1` (default 120): upper valuation threshold
- `--T` (default 1000): number of simulation cycles
- `--kappa` (default 0.25): delivery cost
- `--alpha` (default 1): exponent for payment weighting function h(i) = i^α
- `--seed` (default 42): random seed for reproducibility
- `--json`: output results as JSON (machine-parseable)
- `--verbose`: print per-100-cycle sampling log

**Build:**
- No build step — script runs directly:
  ```bash
  python sph_sim.py --strategy naive --zeta 0.5
  ```

## Platform Requirements

**Development:**
- Python 3.7+ (uses `@dataclass` and f-strings)
- No OS-specific dependencies
- No network access required

**Production:**
- Standalone script — no deployment infrastructure
- Output: human-readable table (default) or JSON (with `--json` flag)
- Designed to be invoked by an AI agent selecting optimal strategy parameters

---

*Stack analysis: 2025-01-31*
