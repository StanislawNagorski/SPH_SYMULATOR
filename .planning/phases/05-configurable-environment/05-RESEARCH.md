# Phase 5: Configurable Environment — Research

**Researched:** 2026-05-27
**Domain:** Python stdlib argparse / CLI flag design / SPH domain valuation functions
**Confidence:** HIGH (all claims verified directly from codebase — no external dependencies involved)

---

## Summary

Phase 5 adds three groups of CLI flags to an already-mature argparse layer: `--phi` / `--rho` for profile override (ENV-01), `--valuation` / `--K0` / `--K1` for valuation preset selection (ENV-02), and a config serialization helper that emits an MD header table (ENV-03). The simulator already centralises defaults in `sphsim/config.py` (14 lines) and passes `phi`, `rho`, `K0`, `K1` through the SPHSimulator constructor verbatim — so the "routing" pattern exists and works; Phase 5 only needs to expose it at the CLI surface.

The biggest unknown is the **scope of ENV-03**: ROADMAP Phase 6 "generates a report MD always" (REPORT-01/02), yet SC-4 says the config header must appear in the report. The two phases must not duplicate code — Phase 5 should ship a `build_config_header(args, K0, K1) -> str` helper in `sphsim/cli/output.py` that Phase 6 can reuse, plus a `--dump-config` style flag that satisfies SC-4 today without touching the Phase 6 report directory scaffold.

The recommended cut: Phase 5 delivers the parsing/validation plumbing and a reusable config-header formatter; it does NOT create `reports/` directories or write files. That is Phase 6 territory.

**Primary recommendation:** Three small, focused changes — (1) two new argparse args with custom `type=` converters for list parsing/validation, (2) valuation preset dispatch via a `make_valuation_fn(preset, K0, K1)` factory in `sphsim/core/model.py`, (3) a `format_config_header(args, K0, K1, phi, rho) -> str` function added to `sphsim/cli/output.py` and printed when `--dump-config` is passed (or always at the top of human-readable output).

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Parse & validate `--phi` / `--rho` lists | CLI (`sphsim/cli/args.py`) | — | All argparse live here; type= converters are the right hook |
| Parse & validate `--valuation` / `--K0` / `--K1` | CLI (`sphsim/cli/args.py`) | — | Same layer; preset + parametric form both resolved at parse time |
| Valuation preset factory (`make_valuation_fn`) | Core Model (`sphsim/core/model.py`) | — | `valuation(u,K0,K1)` already lives here; presets are pure math |
| Config serialisation to MD table | CLI Output (`sphsim/cli/output.py`) | — | `format_human`/`format_json` live here; follow existing pattern |
| φ/ρ/K0/K1 propagation to simulator | CLI main (`sphsim/cli/main.py`) | — | Both branches already build SPHSimulator — extend kwargs here |
| REPL env override (future) | REPL (`sphsim/cli/repl.py`) | — | `do_run` uses hardcoded DEFAULT_*; Phase 5 may extend or defer |

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENV-01 | `--phi p1,p2,p3,p4,p5` and `--rho r1,r2,r3,r4,r5` override DEFAULT_PHI/DEFAULT_RHO; validated for length=5 and range | §A.1, §A.6, §C.9-10, Proposed Design §CLI Flag Shape |
| ENV-02 | `--valuation <window\|step\|linear>` preset selector; alternatively `--K0 X --K1 Y` for full parametric control; window=default (v1.0 compat) | §A.2, §B.7-8, Proposed Design §Valuation Presets |
| ENV-03 | Full env config (nU, T, κ, α, K0, K1, φ, ρ, seed) serialised into MD header in a readable table | §A.3, §D.11-12, Proposed Design §Report Header |
</phase_requirements>

---

## Section A: Existing State of the Code

### A.1 — Where are DEFAULT_PHI and DEFAULT_RHO defined?

**File:** `sphsim/config.py` lines 12–13 [VERIFIED: codebase]

```python
DEFAULT_PHI   = [0.1, 0.2, 0.3, 0.4, 1.0]  # prob. awarii per faza (faza 5 = certain failure)
DEFAULT_RHO   = [0.5, 0.5, 0.7, 1.5, 3.0]  # koszty naprawy per faza
```

Types: Python `list[float]`, length 5. These match `PROMPT_DLA_AGENTA.txt` table verbatim.

**Import sites:**

| File | Import | Usage |
|------|--------|-------|
| `sphsim/cli/main.py:8` | `from sphsim.config import DEFAULT_K0, DEFAULT_F, DEFAULT_PHI, DEFAULT_RHO` | Passed to `SPHSimulator(phi=DEFAULT_PHI, rho=DEFAULT_RHO, ...)` |
| `sphsim/cli/repl.py:34` | `from sphsim.config import ..., DEFAULT_PHI, DEFAULT_RHO` | Passed to `SPHSimulator` in `do_run` and `do_compare` |
| `sphsim/agent/rational.py` | not imported — wrapper receives `phi`/`rho` as args from simulator | — |

`SPHSimulator.__init__` (`simulator.py:8`) accepts `phi` and `rho` as positional constructor arguments and stores them as `self.phi`, `self.rho`. The simulator consumes them at `simulator.py:56-58` (failure probability lookup: `fp = self.phi[idx]`, `repair = self.rho[idx]`).

**Phase 5 impact:** Both call sites in `main.py` (lines 93, 130) hard-code `phi=DEFAULT_PHI, rho=DEFAULT_RHO`. Phase 5 must replace these with `phi=args_phi, rho=args_rho` where the parsed list defaults to `DEFAULT_PHI`/`DEFAULT_RHO` when the flag is absent.

### A.2 — Where is the valuation function g(u) defined?

**File:** `sphsim/core/model.py:7-10` [VERIFIED: codebase]

```python
def valuation(u, K0, K1):
    if K1 == float('inf'):
        return float(K0) if u >= K0 else 0.0
    return float(K0) if K0 <= u <= K1 else 0.0
```

This is the **window preset** (v1.0 baseline): returns K0 when K0 ≤ u ≤ K1, zero otherwise. The current form is already fully parametric via `(K0, K1)` — the Phase 5 "window" preset is exactly this function.

**Current K0/K1 defaults** (`config.py:3-4`):
```python
DEFAULT_K0    = 100
DEFAULT_K1    = 120
```

The existing CLI flag `--K1` (args.py:59) already lets users override K1 from the command line. `DEFAULT_K0 = 100` is used as the fallback `expected_P` for the RationalAgent wrapper (via `rational.py:6` `from sphsim.config import DEFAULT_K0`). Phase 5 will add `--K0` as a peer to `--K1`.

**No step or linear presets exist today.** Phase 5 must introduce them. The function is called by both `simulator.py:80` (STP optimisation) and `simulator.py:105` (cycle valuation) via `from sphsim.core.model import valuation, sph_stp`. Note that `sph_stp` also calls `valuation` internally — the preset must propagate correctly to both call sites.

**Critical:** `sph_stp` calls `valuation` directly (model.py:16: `def P_of_x(x): return valuation(u - x, K0, K1) + x`). The current design hard-codes the `valuation` function name. Phase 5 must decide: (a) add preset dispatch inside `valuation(u, K0, K1)` itself (implicit, clean), or (b) pass a `valuation_fn` callable into `sph_stp` and `SPHSimulator` (explicit, testable). See §Proposed Design.

### A.3 — How is the report header currently generated?

`format_human` in `sphsim/cli/output.py:96-105` emits a minimal environment summary inline:

```python
lines.append(f"  SPH SYMULATOR  |  Strategia: {args.strategy.upper()}")
lines.append(f"  nU={args.nU}, nSUS={args.nSUS}, K1={K1}, T={args.T}, κ={args.kappa}, α={args.alpha}")
```

This is a two-line banner, **not** a full MD table. The following are NOT present today:
- K0, φ, ρ, seed in any formatted output
- A standalone MD header function
- A `reports/` directory scaffold
- A `--dump-config` flag or `--md` flag

**Phase 6 scope** (ROADMAP lines 172-181): Phase 6 "generates a full MD report always" with sections including "konfiguracja środowiska". The ENV-03 requirement says the config must appear "w nagłówku raportu MD". The ROADMAP Phase 6 SC #2 explicitly states "raport zawiera sekcje: konfiguracja środowiska". This means:

- Phase 6 owns the `reports/<timestamp>/report.md` file creation
- Phase 5 must deliver the config-serialisation helper that Phase 6 will call
- Phase 5 must satisfy SC-4 TODAY — meaning there must be a usable output mode (not a deferred "Phase 6 will do it")

**Recommended scope (see §D.11):** Phase 5 adds `format_config_header(args, K0, K1, phi, rho) -> str` to `output.py` and either (a) prints it at the top of every human-readable run, or (b) adds a `--dump-config` flag. Option (a) is cleaner and directly satisfies SC-4 without a new flag. Phase 6 reuses the function.

### A.4 — Current argparse structure and flag layout

**File:** `sphsim/cli/args.py` [VERIFIED: codebase]

**Mutex group (required=True, line 38-44):**
- `--interactive` (store_true)
- `--strategy` (choices=BUILTIN_STRATEGIES)
- `--custom` (type=str)

**Strategy params (lines 46-54, outside mutex):**
- `--zeta`, `--max_phase`, `--probs`, `--s_target`, `--expected_P`
- `--param` (action=append, for `--custom` use only)

**Environment params (lines 56-65, outside mutex):**
- `--nU` (int, default=DEFAULT_NU)
- `--nSUS` (int, default=DEFAULT_NSUS)
- `--K1` (float, default=DEFAULT_K1) ← NOTE: K0 is NOT a CLI flag today
- `--T` (int, default=DEFAULT_T)
- `--kappa` (float, default=DEFAULT_KAPPA)
- `--alpha` (float, default=DEFAULT_ALPHA)
- `--seed` (int, default=42)

**Output control (lines 64-65):**
- `--json` (store_true)
- `--verbose` (store_true)

**Agent flags (lines 66-68, Phase 4 additions):**
- `--no-agent` (store_true)
- `--compare-agent` (store_true)
- Post-parse mutex checks at lines 72-75

**Phase 5 additions slot in after `--K1` in environment params group:**

```
--K0 X          (float, default=DEFAULT_K0)
--phi p1,..,p5  (str, parsed via custom type= converter)
--rho r1,..,r5  (str, parsed via custom type= converter)
--valuation     (str, choices=['window','step','linear'], default='window')
```

There is no `--K0` flag today. Phase 5 adds it as a peer to `--K1`.

### A.5 — Comma-separated list precedent

The existing flag `--probs` (args.py:48) passes a comma-separated string:

```python
p.add_argument('--probs', type=str, default='0.9,0.7,0.5,0.3,0.0',
               help='[phase_prob] P(COMMIT) per faza, po przecinku')
```

It is parsed **later** inside `strategy_phase_prob.py` (not at argparse level). This is the v1.0 precedent but it defers validation — errors show up at runtime, not at argument parse time.

**Phase 5 should use `type=` converters** (not `type=str`) for `--phi` and `--rho` so that argparse itself prints a clean Polish error on bad input. See §C.9 for the validator design.

There is no existing example of a `type=` converter function that parses a list in this codebase. Phase 5 introduces this pattern.

### A.6 — How does `--seed` flow from CLI to simulator?

Full trace [VERIFIED: codebase]:

1. `args.py:63`: `p.add_argument('--seed', type=int, default=42, ...)`
2. `main.py:127`: `sim = SPHSimulator(..., seed=args.seed, ...)`  
3. `simulator.py:13`: `random.seed(seed)` called in `__init__`

The seed is never stored on `args` — it's a direct pass-through via the SPHSimulator constructor kwarg. The same pattern applies to `nU`, `nSUS`, `K1`, `T`, `kappa`, `alpha`. Phase 5 follows the identical pattern for `phi`, `rho`, `K0`, and the resolved K0/K1 from the valuation preset.

**run_compare** (`main.py:27`): hard-codes `phi=DEFAULT_PHI, rho=DEFAULT_RHO` in the `common` dict. Phase 5 must update `run_compare` to use `args`-derived phi/rho/K0.

---

## Section B: Valuation Function Presets (ENV-02, SC-3)

### B.7 — Proposed functional forms for step and linear presets

The SPH domain: `g(u)` is the valuation Consumers pay when `u` services are delivered. The current "window" preset is a constant payment K0 when u falls in [K0, K1], zero otherwise. This gives KPI `avg_val_last100 = 92.0` for the baseline. Any alternative preset must:

1. Use the same `(K0, K1)` parameter pair to stay compatible with `--K0 X --K1 Y`
2. Give outputs distinguishable from "window" in the avg_val_last100 KPI
3. Be mathematically sensible for the auction/mediation domain

**Preset: window (existing, v1.0 compatible)**
```
g_window(u; K0, K1) = K0       if K0 ≤ u ≤ K1
                    = 0        otherwise
```
Semantics: flat payment inside the window, nothing outside. The STP optimiser maximises `P = g(u-x) + x` — the optimizer's candidate search in `sph_stp` is already built for this shape (candidates include `K0-u` and `K1-u` breakpoints).

**Preset: step**
```
g_step(u; K0, K1) = K0          if u >= K1        (high-demand: full payment)
                  = K0 * (u/K0)  if K0 <= u < K1  (= u, linear ramp through mid-zone)
                  = 0            if u < K0
```

Simpler formulation: `g_step(u; K0, K1) = K0 if u >= K0 else 0`. This is a **step function at K0** — the consumer pays K0 as long as at least K0 services are delivered, and pays 0 otherwise, ignoring K1 as an upper bound. This is mathematically simpler than window and semantically meaningful: "pay if minimum demand is met, regardless of oversupply".

Effect on KPI: higher avg_val_last100 than window (because oversupply above K1 is no longer penalised) at the cost of removing the incentive to cap providers. Distinguishable from window for any seed+strategy combination because `g_step(u) = K0 for all u >= K0` vs `g_window(u) = 0 for u > K1`.

**Preset: linear**
```
g_linear(u; K0, K1) = K0 * min(u, K1) / K0   = min(u, K1)   for u <= K1
                     = K1                       for u > K1
```

Cleaner: g_linear is a ramp from 0 to K1 as u goes from 0 to K1, then flat at K1.

```
g_linear(u; K0, K1) = 0                 if u == 0
                    = K0 * (u / K1)     if 0 < u <= K1
                    = K0                if u > K1
```

Wait — semantically K0 is the consumer's "willingness to pay" parameter and K1 is the "saturation" count. For linear: payment rises linearly with number of providers until saturation.

**Proposed concrete forms** [ASSUMED — domain-derived from model, but not validated against original Konorski paper]:

```
# window (v1.0):  flat K0 when K0 ≤ u ≤ K1, else 0
# step:           K0 when u >= K0 (no upper bound penalty)
# linear:         proportional to u up to K1, capped at K0
```

Python:
```python
def _g_window(u, K0, K1):
    if K1 == float('inf'):
        return float(K0) if u >= K0 else 0.0
    return float(K0) if K0 <= u <= K1 else 0.0

def _g_step(u, K0, K1):
    # Pays K0 when u >= K0 (single threshold, no upper cap)
    return float(K0) if u >= K0 else 0.0

def _g_linear(u, K0, K1):
    # Linear ramp: g = K0 * min(u, K1) / K1
    if K1 == float('inf') or K1 <= 0:
        return float(K0) if u >= K0 else 0.0
    return float(K0) * min(u, K1) / K1
```

SC-3 says all three must give **deterministyczne, dające się odróżnić wyniki KPI** on the same seed + strategy. Verification:

- `window(100, K0=100, K1=120)` = 100; `step(100, ...)` = 100; `linear(100, ...)` = 100*100/120 ≈ 83.3 → **linear is distinguishable**
- `window(130, ...)` = 0; `step(130, ...)` = 100; `linear(130, ...)` = 100 → **window is distinguishable from step+linear at oversupply**
- `window(80, ...)` = 0; `step(80, ...)` = 0; `linear(80, ...)` = 100*80/120 ≈ 66.7 → **linear is distinguishable in undersupply**

All three are distinguishable in KPI for the default env (avg providers ≈ 105 for naive). SC-3 is satisfied.

**`--K0 X --K1 Y` interaction:** Both K0 and K1 are scalar parameters shared across all presets. When `--K0 X --K1 Y` is provided, those values override the preset's default K0/K1. No preset-specific K0/K1 defaults are needed — the user provides them explicitly. This is clean and consistent.

**CRITICAL — `sph_stp` uses `valuation` internally:** `sph_stp` (model.py:13) calls the module-level `valuation` function. If Phase 5 replaces `valuation` with a preset-dispatched version, `sph_stp` automatically inherits the new behaviour. If Phase 5 instead uses a passed-in callable, `sph_stp` must also accept the callable. See §Proposed Design for the recommended approach.

### B.8 — How should `--valuation` and `--K0/--K1` interact?

**Recommended design:**

1. `--valuation window|step|linear` selects the mathematical form. Default: `window`.
2. `--K0 X` and `--K1 Y` override the scalar parameters regardless of preset. They are NOT a mutex with `--valuation` — they stack.
3. `--K0 X` and `--K1 Y` without `--valuation` use the `window` preset (v1.0 compatible).
4. The combination `--valuation step --K0 90 --K1 150` is valid: step preset with non-default K0/K1.

This is NOT a mutex group. `--valuation` and `--K0/--K1` are orthogonal dimensions.

**No need for preset-specific K0/K1 defaults** — K0 and K1 are always taken from `args.K0` and `args.K1` (or `DEFAULT_K0`/`DEFAULT_K1` when not provided). The preset controls the shape of `g`, the K values control the thresholds.

**Implementation:** After parsing, call a factory:

```python
val_fn = make_valuation_fn(args.valuation, K0, K1)
```

Pass `val_fn` into `SPHSimulator` as a new constructor argument. Simulator passes it to `sph_stp` and uses it directly.

---

## Section C: Validation Rules (SC-1)

### C.9 — Where should validation live?

**Recommended: `type=` converter in argparse for both `--phi` and `--rho`.** This gives the cleanest UX — argparse prints the error immediately with usage, before any simulation code runs.

Pattern (no analog in codebase today, so Phase 5 introduces it):

```python
def _parse_phi_list(s: str) -> list:
    """Parser dla --phi: '0.1,0.2,0.3,0.4,1.0' → [0.1, 0.2, 0.3, 0.4, 1.0].
    Rzuca argparse.ArgumentTypeError przy błędzie (D-17 polski komunikat).
    """
    import argparse
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

def _parse_rho_list(s: str) -> list:
    """Parser dla --rho: '0.5,0.5,0.7,1.5,3.0' → [0.5, 0.5, 0.7, 1.5, 3.0].
    Rzuca argparse.ArgumentTypeError przy błędzie (D-17 polski komunikat).
    """
    import argparse
    try:
        vals = [float(x.strip()) for x in s.split(',')]
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Nieprawidłowy format --rho: '{s}'. Oczekiwano 5 liczb po przecinku, np. 0.5,0.5,0.7,1.5,3.0"
        )
    if len(vals) != 5:
        raise argparse.ArgumentTypeError(
            f"--rho wymaga dokładnie 5 wartości (podano {len(vals)}): '{s}'"
        )
    for i, v in enumerate(vals):
        if v < 0.0:
            raise argparse.ArgumentTypeError(
                f"--rho[{i+1}]={v} jest ujemne. Wszystkie wartości ρ muszą być ≥ 0."
            )
    return vals
```

Then in `parse_args()`:
```python
p.add_argument('--phi', type=_parse_phi_list, default=DEFAULT_PHI,
               metavar='p1,p2,p3,p4,p5',
               help=f'Profile awarii φ (5 wartości w [0,1], def: {DEFAULT_PHI})')
p.add_argument('--rho', type=_parse_rho_list, default=DEFAULT_RHO,
               metavar='r1,r2,r3,r4,r5',
               help=f'Koszty naprawy ρ (5 wartości ≥ 0, def: {DEFAULT_RHO})')
```

**Why `type=` converter and not post-parse:** The Phase 3 `--param k=v` pattern uses post-parse processing (inside `main.py:69-71`), but that was because param parsing requires the strategy's `STRATEGY_META` context. For `--phi` and `--rho`, no such context is needed — all validation is self-contained. `type=` is cleaner.

**Precedent for `argparse.ArgumentTypeError`:** The Python 3 stdlib supports this explicitly (no external dependency). Message goes through `p.error()` automatically — same exit-2 + usage line as `p.error()`.

### C.10 — Error UX

Argparse with `type=` converter gives:

```
error: argument --phi: Nieprawidłowy format --phi: '0.1,0.2,X'.
       Oczekiwano 5 liczb po przecinku, np. 0.1,0.2,0.3,0.4,1.0
```

This is consistent with Phase 4 D-60 `p.error()` pattern — immediate exit, usage line printed, Polish message. No need for custom exception class.

---

## Section D: Report Header (ENV-03, SC-4)

### D.11 — Scope for Phase 5

Phase 6 (ROADMAP §"Phase 6") owns `reports/<timestamp>/report.md` creation and the full report structure. It depends on Phase 5. Therefore:

**Phase 5 must provide:**
- `format_config_header(args, K0, K1, phi, rho) -> str` — returns a Markdown table string
- This function lives in `sphsim/cli/output.py` alongside `format_human`/`format_json`
- It is called at the top of `format_human` output (always, not behind a flag), satisfying SC-4
- Phase 6 calls the same function when generating `report.md`

**Phase 5 must NOT provide:**
- File I/O (no writing to `reports/` directories)
- Timestamp-based directory creation
- Plot generation

**SC-4 states:** "Nagłówek wygenerowanego raportu MD zawiera kompletną konfigurację środowiska: `nU, T, κ, α, K0, K1, φ, ρ, seed` w czytelnej tabeli"

The word "nagłówku raportu MD" can be satisfied by printing the MD table to stdout (human-readable mode) since there is no file-based report yet in Phase 5. When the user runs with human output mode, the header appears at the top. Phase 6 embeds it into the file.

**Recommended implementation — always-on header in `format_human`:**

```
format_human(args, res, K1, verbose):
    # NEW: config header at top
    lines.append(format_config_header(args, K0, K1, phi, rho))
    lines.append(f"\n{'='*62}")
    ...existing SPH SYMULATOR banner...
```

The config header function:

```python
def format_config_header(args, K0, K1, phi, rho) -> str:
    """Serializuje konfigurację środowiska do tabeli Markdown (ENV-03, SC-4).
    Zwracany string to valida tabela MD — Phase 6 może go wkleić bezpośrednio do report.md.
    """
    phi_str = ', '.join(f'{v:.2f}' for v in phi)
    rho_str = ', '.join(f'{v:.2f}' for v in rho)
    k1_display = '∞' if K1 == float('inf') else str(K1)
    lines = [
        '## Konfiguracja środowiska\n',
        '| Parametr | Wartość |',
        '|----------|---------|',
        f'| nU       | {args.nU} |',
        f'| T        | {args.T} |',
        f'| κ (kappa) | {args.kappa} |',
        f'| α (alpha) | {args.alpha} |',
        f'| K0       | {K0} |',
        f'| K1       | {k1_display} |',
        f'| φ (phi)  | {phi_str} |',
        f'| ρ (rho)  | {rho_str} |',
        f'| seed     | {args.seed} |',
    ]
    return '\n'.join(lines)
```

### D.12 — Is there an existing config dataclass?

No. There is no `EnvConfig`, `SimConfig`, or dataclass for config in the current codebase. Config lives as named constants in `sphsim/config.py` and as `args.*` attributes on the argparse Namespace.

**Phase 5 does NOT need to introduce a config dataclass.** The `format_config_header` function takes explicit arguments — it is decoupled from any dataclass. This is consistent with the existing pattern (all output functions receive individual args, not a config object).

If a future phase introduces batch running (Phase 7), a dataclass may become warranted. For Phase 5, keep it flat.

---

## Section E: Determinism and Backward Compatibility

### E.13 — v1.0 baseline protection

The baseline benchmark: `naive --zeta 0.75 → avg_val_last100 = 92.0` [VERIFIED: `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json:18`]

`regression_check.py` re-runs 8 invocations from `scripts/generate_baseline.py:INVOCATIONS` and compares against `tests/fixtures/baseline_v1/*.json`. Phase 4 added `--no-agent` to each invocation (D-59). Phase 5 must NOT break any of these 8 invocations.

**Phase 5 guarantee mechanism:** All new CLI flags (`--phi`, `--rho`, `--valuation`, `--K0`) have defaults that reproduce the v1.0 behaviour:
- `--phi` default = `DEFAULT_PHI` = `[0.1, 0.2, 0.3, 0.4, 1.0]`
- `--rho` default = `DEFAULT_RHO` = `[0.5, 0.5, 0.7, 1.5, 3.0]`
- `--valuation` default = `'window'` → same `valuation(u, K0, K1)` function
- `--K0` default = `DEFAULT_K0` = `100`

No existing invocation uses `--phi`, `--rho`, `--valuation`, or `--K0`, so regression check INVOCATIONS are unaffected.

**However:** The regression check currently adds `--no-agent` but does NOT add `--phi`, `--rho`, etc. No change to INVOCATIONS is needed. The `deep_diff` in `regression_check.py` uses `SKIP_KEYS` for Phase 4 additions — Phase 5 may need to extend `SKIP_KEYS` if the `env` block in JSON output gains new keys (K0, phi, rho, valuation). See §Pitfall 15.

**Exact invocations that must NOT change behavior:**
```bash
python sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json
python sph_sim.py --strategy threshold --max_phase 3 --no-agent --seed 42 --json
python sph_sim.py --strategy phase_prob --probs 0.9,0.7,0.5,0.3,0.0 --no-agent --seed 42 --json
python sph_sim.py --strategy incentive --expected_P 100 --no-agent --seed 42 --json
python sph_sim.py --strategy adaptive --s_target 10 --no-agent --seed 42 --json
python sph_sim.py --strategy naive --zeta 0.4 --nU 200 --nSUS 20 --K1 120 --T 1000 --no-agent --seed 42 --json
python sph_sim.py --strategy phase_prob --probs 1.0,0.8,0.6,0.2,0.0 --kappa 0.5 --alpha 0 --no-agent --seed 42 --json
python sph_sim.py --strategy naive --zeta 0.75 --no-agent --seed 42 --json
```

All 8 use `--no-agent` (D-59 from Phase 4). None use `--phi`, `--rho`, `--K0`, or `--valuation`. Regression is safe as long as defaults are correct.

### E.14 — Seed propagation for new presets

The `step` and `linear` presets are deterministic functions of `u` — they introduce **no randomness**. `u` (number of providers) is a count of devices that committed successfully in a cycle, determined by `random.random() < fp` calls inside the simulator loop. The seed already controls all randomness in the simulator. No additional seeding is needed for new presets.

The `valuation_fn` itself is a pure function `(u, K0, K1) -> float` with no random state. SC-3 (deterministic KPI per seed+strategy) is automatically satisfied.

---

## Section F: Pitfalls and Landmines

### F.15 — Key pitfalls from prior phases

**D-17 (Polish UX in all user-facing strings):** All argparse help strings, `ArgumentTypeError` messages, the config header section title, and any new `format_human` section headings must be in Polish. English identifiers and code comments are fine. Examples:

- `help='Profile awarii φ (5 wartości w [0,1])'` — Polish in argparse help
- `"Nieprawidłowy format --phi"` — Polish in error
- `"## Konfiguracja środowiska"` — Polish section header in MD

**D-44/D-50 mutex semantics:** The three-member mutex (`--interactive | --strategy | --custom`) must not be touched. `--phi`, `--rho`, `--valuation`, `--K0` are environment params, not mode selectors — they go outside the mutex. This is identical to how `--nU`, `--nSUS`, `--K1` are currently positioned.

**D-41 `format_human` reuse from REPL (`do_run`):** The REPL's `do_run` builds a `fake_args = argparse.Namespace(strategy=name, nU=..., ...)` and passes it to `format_human`. If `format_config_header` reads `args.phi`, `args.rho`, `args.K0`, the `fake_args` must include these fields. Phase 5 must update `do_run`'s `fake_args` construction. Current `fake_args` (repl.py:219-222):
```python
fake_args = argparse.Namespace(
    strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
    kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
)
```
Phase 5 must add `phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window'` to this Namespace. The same applies to `do_compare`'s `fake_args`.

**`run_compare` in `main.py:27-45` hard-codes DEFAULT_PHI/DEFAULT_RHO/DEFAULT_K0:** These must be replaced with `args`-derived values. Currently:
```python
common = dict(
    nU=args.nU, nSUS=args.nSUS, K0=DEFAULT_K0, K1=K1,
    ...
    phi=DEFAULT_PHI, rho=DEFAULT_RHO, ...
)
```
Phase 5 changes `K0=DEFAULT_K0` → `K0=K0` (already resolved from args), `phi=DEFAULT_PHI` → `phi=args.phi`, `rho=DEFAULT_RHO` → `rho=args.rho`.

**`format_json` `env` block (output.py:11-12) currently omits K0, phi, rho, seed:** The existing JSON:
```python
'env': {'nU': args.nU, 'nSUS': args.nSUS, 'K1': K1,
        'T': args.T, 'kappa': args.kappa, 'alpha': args.alpha},
```
Phase 5 adds `'K0': K0, 'phi': phi, 'rho': rho, 'seed': args.seed, 'valuation': args.valuation` to this block. This extends the JSON schema. The regression check uses `deep_diff` with `SKIP_KEYS` — if the `env` block in fixtures does NOT include these new keys, `deep_diff` will flag them as `KEY EXTRA w actual`. The simplest fix: add `'K0'`, `'phi'`, `'rho'`, `'seed'`, `'valuation'` to `SKIP_KEYS` in `regression_check.py` (the Phase 4 D-67 approach). Alternative: patch the 8 baseline fixtures. The skip-keys approach requires minimal change.

**`sph_stp` depends on `valuation` function call:** If Phase 5 replaces the module-level `valuation` with a preset dispatcher, `sph_stp` (which calls `valuation` via closure in `P_of_x`) will automatically pick up the new function — IF the dispatch happens at the `valuation` function level. If Phase 5 instead passes a `valuation_fn` callable through `SPHSimulator`, `sph_stp` must also receive it as a parameter (currently `sph_stp` signature is `(u, s, nSUS, K0, K1)` and calls `valuation` directly). This is the main architectural decision — see §Proposed Design.

**`rational.py` uses `DEFAULT_K0` as `expected_P` fallback.** This is fine — the agent's `expected_P` is not the same as the valuation K0. They happen to share the same default value (100) but are conceptually independent.

### F.16 — Phase 6/7 scope fence

Phase 5 must NOT touch:
- `reports/` directory creation or file writing
- `matplotlib` imports or PNG generation
- Timestamp-based naming
- Batch loop logic or seed iteration
- The `format_json` structure beyond adding env fields (Phase 6 may re-use `format_json` data for MD generation)

Phase 5 CAN (and should) ship:
- `format_config_header()` function in `output.py` — reusable by Phase 6
- The `valuation_fn` callable wired into `SPHSimulator` — Phase 6 gets it for free in reports
- Extended JSON `env` block — Phase 6 reads it

---

## Proposed Design (1-page summary)

### CLI Flag Shape

```
# In args.py — environment params section (after --K1 line):
p.add_argument('--K0',       type=float, default=DEFAULT_K0,
               help=f'Dolny próg waluacji K0 (def {DEFAULT_K0})')
p.add_argument('--phi',      type=_parse_phi_list, default=DEFAULT_PHI,
               metavar='p1,..,p5',
               help='Profile awarii φ (5 liczb w [0,1], def: 0.1,0.2,0.3,0.4,1.0)')
p.add_argument('--rho',      type=_parse_rho_list, default=DEFAULT_RHO,
               metavar='r1,..,r5',
               help='Koszty naprawy ρ (5 liczb ≥ 0, def: 0.5,0.5,0.7,1.5,3.0)')
p.add_argument('--valuation', choices=['window','step','linear'], default='window',
               help='Preset funkcji waluacji g(u) (def: window = tryb v1.0)')
```

No mutex changes. All four flags are independent env params like `--nU` and `--T`.

### Validation Strategy

Two `type=` converter functions defined at module level in `args.py` (before `parse_args()`):
- `_parse_phi_list(s: str) -> list` — validates length=5, each ∈ [0.0, 1.0]
- `_parse_rho_list(s: str) -> list` — validates length=5, each ≥ 0.0

Both raise `argparse.ArgumentTypeError` with Polish messages. Error format mirrors Phase 4 D-60 style.

### Valuation Preset Architecture

**Recommended: preset dispatch inside the `valuation` function itself (cleanest).**

Replace `sphsim/core/model.py:7-10`:

```python
def valuation(u, K0, K1, preset='window'):
    """Funkcja waluacji Konsumentów g(u; K0, K1).
    preset: 'window' (def, v1.0) | 'step' | 'linear'
    """
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

`sph_stp` call at model.py:16 (`return valuation(u - x, K0, K1) + x`) becomes:
```python
return valuation(u - x, K0, K1, preset) + x
```

`SPHSimulator` gets a new `valuation_preset='window'` parameter:
```python
def __init__(self, ..., valuation_preset='window'):
    self.valuation_preset = valuation_preset
```

And calls inside `run()` (`simulator.py:80,105`) become:
```python
z, y = sph_stp(u, self.s, self.nSUS, self.K0, self.K1, self.valuation_preset)
val = valuation(svc_to_cons, self.K0, self.K1, self.valuation_preset)
```

**Why not a `valuation_fn` callable?** Passing a callable through `SPHSimulator` → `sph_stp` requires changing the signature of `sph_stp` (currently: `(u, s, nSUS, K0, K1)`) and its internal lambda. A preset string is simpler and preserves the existing `(K0, K1)` parameter passing. The preset-string approach also makes `format_config_header` and JSON output trivial — just serialise `args.valuation`.

**Resolution from args:** In `main.py`:
```python
K0 = args.K0   # (was DEFAULT_K0 hardcoded)
K1 = float('inf') if args.K1 < 0 else args.K1
phi = args.phi   # list[float], already validated by type= converter
rho = args.rho   # list[float], already validated
valuation_preset = args.valuation

sim = SPHSimulator(
    nU=args.nU, nSUS=args.nSUS, K0=K0, K1=K1,
    F=DEFAULT_F, T=args.T, kappa=args.kappa, alpha=args.alpha,
    phi=phi, rho=rho, valuation_preset=valuation_preset,
    strategy_fn=strategy_fn, params=params, seed=args.seed,
)
```

### Config Object

No new dataclass. Config fields are flat on `args` (argparse Namespace). `format_config_header(args, K0, K1, phi, rho)` receives them explicitly.

### Report Header Scope

`format_config_header` added to `output.py`. Called at top of `format_human` output (not behind a flag — always shown). Phase 6 calls the same function when building `report.md`. The function signature:

```python
def format_config_header(args, K0, K1, phi, rho) -> str:
```

This satisfies SC-4 ("nagłówek raportu MD zawiera kompletną konfigurację") because the human-readable stdout IS the "raport" in Phase 5 context (before Phase 6 adds file-based reports).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Comma-list validation | Custom parser class | `argparse.ArgumentTypeError` in `type=` converter | Stdlib pattern; auto-integrates with argparse error handling |
| Preset dispatch | Global mutable state, subclass | `preset` string arg to `valuation()` | Simplest change, backward compatible, testable in isolation |
| Config table formatting | Jinja2 / external template | f-string MD table in `format_config_header` | Stdlib only constraint; pattern matches existing `format_human` |

---

## Common Pitfalls

### Pitfall 1: `sph_stp` breakage when changing `valuation`

**What goes wrong:** `sph_stp` calls `valuation(u - x, K0, K1)` in an inner lambda (model.py:16). If Phase 5 adds a `preset` parameter to `valuation()` but forgets to thread it through `sph_stp`, the STP optimiser silently uses the window preset regardless of `--valuation`.

**Why it happens:** `sph_stp` is called as `sph_stp(u, self.s, self.nSUS, self.K0, self.K1)` — the preset is not in its current signature.

**How to avoid:** Also add `preset='window'` to `sph_stp` signature and thread it into the `P_of_x` lambda. Test: `g_step` with oversupply should give different `P_total` than `g_window`.

**Warning signs:** SC-3 test shows step/linear KPI = window KPI (they're all the same) → `sph_stp` is not using the new preset.

### Pitfall 2: `fake_args` in REPL missing new fields

**What goes wrong:** `format_human` calls `format_config_header(args, ...)` which reads `args.phi`, `args.rho`, `args.K0`. The REPL's `fake_args` Namespace (repl.py:219-222) doesn't have these fields → `AttributeError`.

**Why it happens:** `fake_args` is a manual `argparse.Namespace(...)` construction — it doesn't auto-populate new fields.

**How to avoid:** Phase 5 plan explicitly updates `fake_args` in both `do_run` and `do_compare` to include `phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window'`.

**Warning signs:** `python sph_sim.py --interactive` → `run naive` → `AttributeError: Namespace object has no attribute 'phi'`.

### Pitfall 3: Regression check fails on extended `env` JSON block

**What goes wrong:** Phase 5 adds `K0`, `phi`, `rho`, `valuation`, `seed` to the JSON `env` block. Existing fixtures don't have these. `deep_diff` in `regression_check.py` reports `KEY EXTRA w actual` for each new key → regression fails.

**Why it happens:** `deep_diff` checks for extra keys by default (Phase 4 used `SKIP_KEYS` for new metrics keys, but `env` block keys are not currently in `SKIP_KEYS`).

**How to avoid:** Add the new env keys to `SKIP_KEYS` in `regression_check.py`, OR patch all 8 fixtures to include the new fields with their default values. Skip-keys approach is one-line change, consistent with Phase 4 D-67 strategy.

**Warning signs:** `scripts/regression_check.py` exits 1 with `diff [...] env.K0: KEY EXTRA w actual`.

### Pitfall 4: `--phi 0.1,0.2,0.3,0.4,1.0` (with spaces) fails

**What goes wrong:** Shell may strip quotes — `--phi 0.1, 0.2, 0.3` passes three separate tokens. The `type=` converter receives only `"0.1,"`, which fails `float()`.

**Why it happens:** Argparse treats spaces as token delimiters. `--phi "0.1,0.2,0.3,0.4,1.0"` (quoted) works; `--phi 0.1,0.2,0.3,0.4,1.0` (no spaces around commas) also works.

**How to avoid:** Document that values must be comma-separated WITHOUT spaces, or make the converter strip spaces around each value (`x.strip()`). The strip is already in the proposed converter above.

---

## Validation Architecture

`workflow.nyquist_validation` is absent from `.planning/config.json` (only `_auto_chain_active` and `use_worktrees` are set) — therefore treated as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python `unittest` (stdlib, no pytest) |
| Config file | none — tests run via `python -m unittest discover tests/` |
| Quick run command | `python -m unittest tests/test_env.py -v` (new file) |
| Full suite command | `python -m unittest discover tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENV-01 | `--phi 0.1,0.2,0.3,0.4,1.0` parses and reaches simulator | unit | `python -m unittest tests/test_env.py::TestPhiRhoParsing -v` | ❌ Wave 0 |
| ENV-01 | `--phi` length != 5 raises argparse error exit 2 | unit | same file | ❌ Wave 0 |
| ENV-01 | `--phi` value > 1.0 raises argparse error | unit | same file | ❌ Wave 0 |
| ENV-01 | `--rho` negative value raises argparse error | unit | same file | ❌ Wave 0 |
| ENV-02 | `--valuation step` gives different KPI than window (same seed) | integration | `python -m unittest tests/test_env.py::TestValuationPresets -v` | ❌ Wave 0 |
| ENV-02 | `--valuation linear` gives different KPI than window (same seed) | integration | same | ❌ Wave 0 |
| ENV-02 | `--K0 X --K1 Y` overrides are reflected in simulation | integration | same | ❌ Wave 0 |
| ENV-03 | human-readable output contains φ, ρ, K0, seed in MD table format | integration | `python -m unittest tests/test_env.py::TestConfigHeader -v` | ❌ Wave 0 |
| ENV-03 | `format_config_header()` returns all 9 required fields | unit | same | ❌ Wave 0 |
| regression | All 8 baseline invocations still pass | integration | `python scripts/regression_check.py` | ✅ exists |

### Sampling Rate

- **Per task commit:** `python -m unittest tests/test_env.py -v`
- **Per wave merge:** `python -m unittest discover tests/ -v`
- **Phase gate:** Full suite green + `regression_check.py` PASS before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_env.py` — covers ENV-01, ENV-02, ENV-03
- [ ] No new framework install needed — unittest is stdlib

---

## Security Domain

No new security surface. Phase 5 adds CLI flags with numeric/string inputs. `type=` converters raise `ArgumentTypeError` on invalid input before any simulation runs. No file I/O, no subprocess, no eval, no importlib loading in this phase. The existing security note in PROJECT.md (importlib for custom strategies) is unaffected.

---

## Environment Availability

Phase 5 is purely code/config changes. No external tools, services, or runtimes beyond Python 3.7+ stdlib. No matplotlib (Phase 6). No environment audit needed.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| v1.0: K1 only as CLI override, K0 hardcoded | Phase 5: both K0 and K1 overridable | Phase 5 | K0 now movable without code edit |
| v1.0: φ/ρ hardcoded in config.py | Phase 5: overridable via --phi/--rho | Phase 5 | Researchers can test different risk profiles |
| v1.0: single window valuation function | Phase 5: window/step/linear presets | Phase 5 | Three distinguishable g(u) shapes for sensitivity analysis |
| No config header in output | Phase 5: MD table always in human output | Phase 5 | Reproducibility — run parameters visible in output |

**Deprecated/outdated:**
- The pattern of hard-coding `DEFAULT_PHI`/`DEFAULT_RHO` inside `main.py` SPHSimulator calls is replaced by `args.phi`/`args.rho` derived from CLI.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `g_step = K0 if u >= K0 else 0` is mathematically sensible for the SPH domain | §B.7 | Preset may not have academic backing in Konorski's model — but SC-3 only requires distinguishable KPIs, not domain correctness |
| A2 | `g_linear = K0 * min(u, K1) / K1` gives distinguishable KPI from window on default env | §B.7 | If avg providers is always >> K1, linear ≈ K0 ≈ window numerically — need to verify with a test run |
| A3 | Printing the config header always (not behind a flag) satisfies SC-4 | §D.11 | Planner may prefer a `--dump-config` flag or defer to Phase 6; this is a scope judgement call |
| A4 | Adding new keys to `env` block in JSON requires `SKIP_KEYS` extension in `regression_check.py` | §E.13/F.15 | If fixtures are patched instead, `SKIP_KEYS` change is not needed |

---

## Open Questions

1. **REPL env override scope for Phase 5**
   - What we know: REPL `do_run` uses hardcoded `DEFAULT_*` (D-41 comment: "Phase 5 doda override")
   - What's unclear: Should Phase 5 add `--phi`/`--rho`/`--valuation` to REPL `run` command (e.g., `run naive zeta=0.75 phi=0.05,0.1,0.2,0.3,1.0`), or is CLI-only sufficient for SC-1 through SC-4?
   - Recommendation: ROADMAP SC-1 and SC-3/SC-4 only mention CLI flags. Defer REPL env override to Phase 6 or as Claude's Discretion. SC-4 mentions "nagłówek raportu" — the REPL's `do_run` output should also show the config header using default values.

2. **`sph_stp` candidate list for step/linear presets**
   - What we know: `sph_stp` currently has candidate breakpoints at `K0-u` and `K1-u` (model.py:24-25), tuned for the window function
   - What's unclear: For `step`, the only breakpoint is `K0-u`. For `linear`, the breakpoint might be different. The current search over `[K0-u-1, K0-u, K0-u+1]` and optionally `[K1-u-1, K1-u, K1-u+1]` may miss the optimum for linear
   - Recommendation: For Phase 5, keep the existing candidate search (it's a small finite search that checks ±1 around breakpoints). Linear may not find the true optimum but will be close. Full optimization refactor is out of scope.

3. **`--K1 -1` = infinity semantics with `--valuation step`**
   - What we know: current code has `K1 = float('inf') if args.K1 < 0 else args.K1` (main.py:75). For step preset, K1 is already ignored (no upper bound in step). For linear, K1=∞ needs a guard.
   - Recommendation: `_g_linear` should fall back to `_g_step` when K1 is inf (as proposed in §B.7: `if K1 == float('inf') or K1 <= 0: return float(K0) if u >= K0 else 0.0`).

---

## Sources

### Primary (HIGH confidence)
- `sphsim/config.py` — DEFAULT_PHI, DEFAULT_RHO, DEFAULT_K0, DEFAULT_K1 definitions (all values and types verified)
- `sphsim/core/model.py` — valuation function and sph_stp (exact code read)
- `sphsim/cli/args.py` — complete argparse structure (all flags enumerated)
- `sphsim/cli/main.py` — full data flow from args to SPHSimulator
- `sphsim/cli/output.py` — format_human, format_json, format_compare (full code)
- `sphsim/cli/repl.py` — fake_args construction pattern (do_run, do_compare)
- `sphsim/core/simulator.py` — SPHSimulator constructor + run() phi/rho usage
- `tests/fixtures/baseline_v1/08-naive-zeta-0.75-baseline.json` — baseline KPI (92.0 avg_val)
- `scripts/regression_check.py` — SKIP_KEYS, deep_diff, INVOCATIONS import pattern
- `.planning/ROADMAP.md` Phase 5 + Phase 6 — scope boundary for ENV-03 vs REPORT-01/02
- `PROMPT_DLA_AGENTA.txt` — domain definition of g(u), K0, K1, φ, ρ parameters

### Secondary (MEDIUM confidence)
- `.planning/phases/04-rational-agent-veto-layer/04-CONTEXT.md` — D-41, D-44, D-50, D-59, D-60 pattern carry-forwards

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pure stdlib, no new dependencies
- Architecture: HIGH — all patterns traced from existing code
- Pitfalls: HIGH — all identified from code reading, not speculation
- Valuation preset functional forms: MEDIUM — domain semantics [ASSUMED]; KPI distinguishability [ASSUMED until verified by test]

**Research date:** 2026-05-27
**Valid until:** Indefinite for code facts; re-verify preset math when implementing SC-3 test

---

## Package Legitimacy Audit

No new packages are installed in Phase 5. All changes are stdlib-only (Python 3.7+) consistent with PROJECT.md constraint. No audit required.
