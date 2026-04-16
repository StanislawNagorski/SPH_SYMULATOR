# Codebase Structure

**Analysis Date:** 2025-01-31

## Directory Layout

```
ekonometria 2/              # Project root (git repo)
├── sph_sim.py              # Entire simulation codebase — single Python file
├── PROMPT_DLA_AGENTA.txt   # AI agent task specification / problem description
└── .planning/              # GSD planning artefacts (generated)
    └── codebase/           # Codebase analysis documents
        ├── ARCHITECTURE.md
        └── STRUCTURE.md
```

## Directory Purposes

**Root `/`:**
- Purpose: Entire project lives here — no subdirectories for source code
- Contains: One Python script, one text specification, planning docs
- Key files: `sph_sim.py`, `PROMPT_DLA_AGENTA.txt`

**`.planning/codebase/`:**
- Purpose: GSD codebase map documents consumed by planning and execution agents
- Contains: ARCHITECTURE.md, STRUCTURE.md (and potentially STACK.md, CONVENTIONS.md, etc.)
- Generated: Yes (by GSD map-codebase command)
- Committed: Yes (part of project repo)

## Key File Locations

**Entry Points:**
- `sph_sim.py:361` — `if __name__ == '__main__': main()` — CLI entry point
- `sph_sim.py:305` — `def main()` — top-level orchestration
- `sph_sim.py:278` — `def parse_args()` — argument parsing

**Configuration / Constants:**
- `sph_sim.py:39–48` — All default simulation parameters (`DEFAULT_*` constants)

**Core Model:**
- `sph_sim.py:53–79` — `valuation()` and `sph_stp()` — mathematical model functions
- `sph_sim.py:84–99` — `Device` dataclass — agent state
- `sph_sim.py:162–273` — `SPHSimulator` class — simulation engine

**Strategies:**
- `sph_sim.py:104–157` — All 5 strategy functions + `STRATEGIES` registry dict

**Output / Reporting:**
- `sph_sim.py:322–359` — JSON and human-readable formatted output in `main()`

**Specification:**
- `PROMPT_DLA_AGENTA.txt` — Full problem description: system model, parameters table, KPI definitions, baseline results, strategy descriptions, and expected AI response format

## Naming Conventions

**Files:**
- Snake_case with descriptive prefix: `sph_sim.py` (SPH = Service Provision Helper; sim = simulator)
- Uppercase for documentation: `PROMPT_DLA_AGENTA.txt`

**Functions:**
- Snake_case: `strategy_naive`, `parse_args`, `sph_stp`, `valuation`
- Strategy functions prefixed with `strategy_`: `strategy_naive`, `strategy_threshold`, `strategy_phase_prob`, `strategy_incentive`, `strategy_adaptive`

**Variables:**
- Short mathematical names matching academic paper notation: `nU`, `nSUS`, `K0`, `K1`, `F`, `T`, `kappa`, `alpha`, `phi`, `rho`
- Single-letter Greek letter names: `s` (SUS occupancy), `u` (providers count), `z`, `y` (buffer transfers), `l` (provider counts per phase vector)
- Constants prefixed with `DEFAULT_`: `DEFAULT_NU`, `DEFAULT_KAPPA`, etc.

**Classes:**
- PascalCase: `SPHSimulator`, `Device`

**Dataclass Fields:**
- Snake_case: `down_left`, `n_commit`, `n_abstain`, `n_delivered`, `n_failed`, `net_profit`

**Strategy Registry:**
- `STRATEGIES` — uppercase dict mapping string name → function reference

## Where to Add New Code

**New Strategy:**
- Add function at `sph_sim.py` after line 149 (after `strategy_adaptive`), following the signature:
  ```python
  def strategy_myname(dev, l, s, phi, kappa, rho, h, p):
      if dev.status != 'UP':
          return 'ABSTAIN'
      # ... decision logic ...
      return 'COMMIT' or 'ABSTAIN'
  ```
- Register in `STRATEGIES` dict at `sph_sim.py:151–157`: `'myname': strategy_myname`
- Add CLI argument in `parse_args()` at `sph_sim.py:278–303` if new parameters needed

**New Metric:**
- Add to `self.history` dict initialization in `SPHSimulator.__init__` (`sph_sim.py:182`)
- Append value inside `SPHSimulator.run()` loop (`sph_sim.py:256–261`)
- Include in returned dict at `sph_sim.py:264–273`
- Add display line in `main()` output block (`sph_sim.py:337–345`)

**New Environment Parameter:**
- Add `DEFAULT_PARAM` constant at `sph_sim.py:39–48`
- Add `--param` argparse argument at `sph_sim.py:278–303`
- Pass to `SPHSimulator.__init__` and store as `self.param`
- Use in `SPHSimulator.run()` as needed

**Utilities / Helpers:**
- No separate utils directory; add helper functions directly in `sph_sim.py` near the relevant section (model functions: lines 53–79, or before the class)

## Special Files

**`PROMPT_DLA_AGENTA.txt`:**
- Purpose: Specification document for AI agents — describes the optimization problem, all model parameters, KPI targets, baseline benchmark results, and required output format
- Generated: No — authored by project creator
- Committed: Yes
- Contains baseline results table for strategy comparison (naive/phase_prob/incentive/threshold)

**`sph_sim.py` Section Map (by line):**
- Lines 1–27: Module docstring with usage examples
- Lines 29–35: Imports
- Lines 39–48: Default constants
- Lines 53–79: Model functions
- Lines 84–99: Device dataclass
- Lines 104–157: Strategy functions + STRATEGIES dict
- Lines 162–273: SPHSimulator class
- Lines 278–303: parse_args()
- Lines 305–363: main() + `__main__` guard

---

*Structure analysis: 2025-01-31*
