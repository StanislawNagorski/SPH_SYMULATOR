---
phase: 3
plan: 03-04
subsystem: custom-strategy-loader
tags: [template, phase-exit-gate, verification, polish-comments, wave-3, final-plan]
requirements:
  fulfilled: [STRAT-05]
dependency_graph:
  requires:
    - "sphsim.strategies.loader (Plan 03-01 — load_custom + parse_params_from_meta + LoaderError)"
    - "sphsim/cli/args.py --custom + --param (Plan 03-02 — D-44/D-39 mutex + repeatable)"
    - "sphsim/cli/main.py args.custom early branch (Plan 03-02 — load+register+simulate+format)"
    - "sphsim/cli/repl.py do_custom + do_run + do_strategies [custom] suffix (Plan 03-03 — D-38/D-41/D-50)"
    - "scripts/regression_check.py (Phase 1 — 8 baseline_v1 fixtures, CLI-04 contract)"
    - "tests/test_loader.py (Plan 03-01 — 21 unit cases)"
    - "tests/test_strategy_meta_consistency.py (Phase 2 — STRATEGY_META ↔ argparse invariant)"
  provides:
    - "examples/custom_strategy_template.py — kanoniczny starter custom strategii (Polish docstring + 8-arg block + STRATEGY_META schema + max_phase param example)"
    - "scripts/verify_phase3.sh — phase exit gate (20 checks across 8 sections, all 5 ROADMAP Phase 3 SCs + regression + invariant + loader tests + mutex enforcement)"
  affects:
    - "Phase 3 acceptance: phase exit gate green — można wejść w /gsd:verify-work"
    - "Phase 4 (RationalAgent veto): czysta baseline do rozszerzenia (template + verify script są stabilne kontrakty)"
    - "Future users: template jest copy-paste'em do iteracji własnych strategii"
tech_stack:
  added: []  # stdlib + POSIX coreutils only — bez nowych zależności
  patterns:
    - "Polish multi-line docstring + 8-argument explanation block + STRATEGY_META schema verbatim z built-in shape (template = live kontrakt)"
    - "Phase exit gate jako bash script z sectional checks + final PASS/FAIL summary (analog scripts/verify_phase1.sh)"
    - "check() helper z eval + log capture + truncated tail printout dla FAIL hints"
    - "`grep > /dev/null` zamiast `grep -q` (unika SIGPIPE upstream'owi pod set -o pipefail)"
    - "`{ cmd || true; } | grep ...` dla komend gdzie loader celowo exit 1 (polski błąd to expected behavior, nie failure)"
    - "Heredoc tmp files /tmp/p3_*.py dla error-path scenarios (bad signature, no function, no STRATEGY_META) — cleanup przez trap EXIT"
key_files:
  created:
    - "examples/custom_strategy_template.py (51 lines — Polish docstring + 8-arg block + strategy_custom_strategy_template + STRATEGY_META)"
    - "scripts/verify_phase3.sh (168 lines, executable — 20 checks across 8 sections)"
  modified: []
decisions:
  - "D-51: template uses max_phase default=4 (alias `threshold` z innym defaultem); strategy_custom_strategy_template returns COMMIT if dev.phase <= max_phase else ABSTAIN, with UP/DOWN guard"
  - "D-52: examples/ is plain directory (NOT a package) — no __init__.py, no .gitignore — single file is canonical template, users copy to ~/my-strats/"
  - "D-45 enforced: banner [OSTRZEŻENIE] appears as stdout line 1 verified by verify_phase3.sh section 4 (head -1 | grep '^\\[OSTRZEŻENIE\\]...')"
  - "Phase exit gate design: 8 sections cover regression + invariant + loader tests + all 5 SCs + mutex (D-44); total 20 checks; exit 0 only when FAIL=0"
  - "SIGPIPE fix (operational): `grep -q` under `set -o pipefail` causes upstream Python SIGPIPE → propagates as exit 120/141; replaced with `grep ... > /dev/null` which reads full stream (no SIGPIPE)"
  - "Failure-tolerant wrapper: `{ cmd 2>&1 || true; } | grep ...` for tests where the loader's exit 1 is the expected behavior — we test the error MESSAGE, not the exit code"
metrics:
  duration: "~6 minutes (sequential executor)"
  tasks: 2/2 complete
  files_created: 2
  files_modified: 0
  total_lines_added: 219  # 51 (template) + 168 (verify_phase3.sh)
  total_checks_in_gate: 20
  completed_date: 2026-05-27
---

# Phase 3 Plan 04: examples/custom_strategy_template.py + scripts/verify_phase3.sh Summary

Delivers the canonical Polish-commented custom strategy template (D-51 / STRAT-05) and the Phase 3 exit gate shell script (verify_phase3.sh) that mechanically validates all 5 ROADMAP Phase 3 Success Criteria plus regression, invariant, loader tests, and mutex enforcement — 20 checks, all green.

## What Was Built

Two artifacts complete the Phase 3 acceptance surface:

1. **`examples/custom_strategy_template.py`** (51 lines) — the canonical starter for any user wanting to write a custom strategy. Polish multi-line header docstring explains purpose, naming rule (D-34/D-35: function = `strategy_<basename>`), example CLI invocation, and the academic-local security note. An inline 8-line argument block enumerates `dev/l/s/phi/kappa/rho/h/p` verbatim from PROMPT_DLA_AGENTA.txt + Phase 1 D-03. The strategy function `strategy_custom_strategy_template(dev, l, s, phi, kappa, rho, h, p)` returns COMMIT for `dev.phase <= max_phase` and ABSTAIN otherwise (default `max_phase=4` — an alias of `threshold` with a different default, per D-51). `STRATEGY_META` carries the description, the `('max_phase', int, 4, 'Maksymalna faza dla COMMIT')` param spec, and `baseline_kpi=None`. The file compiles cleanly under `python -W all -m py_compile`, loads via the Plan 01 loader, runs end-to-end through the Plan 02 CLI (`--custom`) and the Plan 03 REPL (`custom <ścieżka>` + `run custom_strategy_template max_phase=N`), and produces deterministic JSON output for `--seed 42`.

2. **`scripts/verify_phase3.sh`** (168 lines, executable) — bash strict-mode phase exit gate that runs 20 checks across 8 sections:
   - **Section 1** — regression backwards compat (`scripts/regression_check.py` → 8/8)
   - **Section 2** — Phase 2 invariant + Plan 01 loader 21 unit cases + full discover (22 tests)
   - **Section 3 (SC #3)** — template compiles, loads via loader, runs via CLI, produces valid JSON with `strategy=custom_strategy_template`
   - **Section 4 (SC #5)** — banner `[OSTRZEŻENIE]` appears as stdout line 1 before JSON
   - **Section 5 (SC #2)** — 4 layers of Polish error messages with concrete (nonexistent path → `Plik nie istnieje`; bad signature → `Oczekiwana: (dev, l, s, phi, kappa, rho, h, p)`; missing function → `Brak funkcji`; missing STRATEGY_META → `nie eksportuje STRATEGY_META`)
   - **Section 6 (SC #1 + SC #4)** — REPL loads custom, listing shows `[custom]` suffix, `run` works, reload prints `Przeładowano custom strategię`
   - **Section 7 (SC #1)** — CLI determinism (two runs same JSON) + `--param max_phase=` actually changes the output
   - **Section 8 (D-44)** — mutex rejects `--custom + --strategy`, mutex requires at least one of three members

   The script ends with `PASS=20 / FAIL=0` and prints `✓ Phase 3 ready for /gsd:verify-work`. Re-runnable from any cwd (cd to `dirname/$0/..`), cleans `/tmp/p3_*` via `trap ... EXIT`.

## Tasks Completed

| # | Task | Files | Commit | Status |
|---|------|-------|--------|--------|
| 3-04-01 | Create `examples/custom_strategy_template.py` (D-51, STRAT-05) | `examples/custom_strategy_template.py` | `9dc96f0` | done |
| 3-04-02 | Create `scripts/verify_phase3.sh` (phase exit gate, 20 checks) | `scripts/verify_phase3.sh` | `d7a1c10` | done |

## Acceptance Criteria

### Task 3-04-01 (template)

**Source-level:**
- `ls examples/custom_strategy_template.py` → exists ✓
- `ls examples/__init__.py 2>/dev/null; test $? -ne 0` → no __init__.py (D-52) ✓
- `grep -c "def strategy_custom_strategy_template(dev, l, s, phi, kappa, rho, h, p)"` → 1 ✓
- `grep -c "STRATEGY_META = {"` → 1 ✓
- `grep -c "'max_phase', int, 4"` → 1 ✓
- `grep -c "Szablon"` → 2 (≥1) ✓
- English comment pattern grep → 0 ✓

**Compilation:**
- `python -m py_compile examples/custom_strategy_template.py` → exit 0 ✓
- `python -W all -m py_compile examples/custom_strategy_template.py` → exit 0 (no warnings) ✓

**Behavior:**
- Loader unit: `load_custom('examples/custom_strategy_template.py')` returns `('custom_strategy_template', <fn>, {description: 'Szablon: COMMIT dla faz <= max_phase (przykład dydaktyczny)', ...})` ✓
- CLI acceptance (SC #3): `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json` exits 0 with valid JSON containing `strategy=custom_strategy_template` and `metrics.avg_val_last100` ✓
- Banner (SC #5): stdout line 1 is `[OSTRZEŻENIE] Ładuję arbitralny kod Pythona z: /…/examples/custom_strategy_template.py` ✓
- Determinism (SC #3): two runs with `--seed 42` produce byte-identical JSON ✓
- REPL flow (SC #1, #4): `custom examples/... → strategies → run custom_strategy_template max_phase=3 → exit` produces `[custom]` suffix and runs without error ✓
- Param effect: `--param max_phase=2` vs `--param max_phase=4` produces different JSON (KPIs change deterministically) ✓
- Regression `python scripts/regression_check.py` → 8/8 PASS ✓
- Tests `python -m unittest discover tests` → 22/22 OK ✓

### Task 3-04-02 (verify_phase3.sh)

**Source-level:**
- `ls -l scripts/verify_phase3.sh` → -rwxr-xr-x (executable) ✓
- `head -1` → `#!/usr/bin/env bash` ✓
- `grep -c "set -euo pipefail"` → 1 ✓
- `grep -c "regression_check.py"` → 1 ✓
- `grep -c "test_loader"` → 1 ✓
- `grep -c "test_strategy_meta_consistency"` → 1 ✓
- `grep -c "examples/custom_strategy_template.py"` → 12 (≥4) ✓
- `grep -c "\[OSTRZE"` → 4 (≥1) ✓
- `grep -c "\[custom\]"` → 4 (≥1) ✓
- `grep -c "Oczekiwana: (dev, l, s, phi, kappa, rho, h, p)"` → 2 (≥1) ✓
- `grep -c "Plik nie istnieje"` → 2 (≥1) ✓
- `grep -c "Przeładowano custom"` → 2 (≥1) ✓
- `grep -c "diff -q"` → 2 (≥1) ✓

**Behavior:**
- `bash scripts/verify_phase3.sh` → exit 0 ✓
- `[PASS]` count → 20 (target ≥13) ✓
- `[FAIL]` count → 0 ✓
- Tail → `✓ Phase 3 ready for /gsd:verify-work` ✓
- Final cross-check: `regression_check.py && unittest discover tests && bash scripts/verify_phase3.sh` → all exit 0 ✓

## Plan-Level Phase Regression Gates

| Gate | Command | Result |
|------|---------|--------|
| Phase 1 baseline regression (CLI-04) | `python3 scripts/regression_check.py` | PASS: 8/8 |
| Phase 2 invariant | `python3 -m unittest tests.test_strategy_meta_consistency` | Ran 1 test — OK |
| Phase 3 loader unit | `python3 -m unittest tests.test_loader` | Ran 21 tests — OK |
| Full discover | `python3 -m unittest discover tests` | Ran 22 tests in 1.127s — OK |
| Phase 3 exit gate | `bash scripts/verify_phase3.sh` | PASS=20 / FAIL=0, exit 0 |
| Template determinism | two `--seed 42` runs of template | byte-identical JSON |
| Template REPL run | `custom + run + exit` printf into REPL | `Strategia: CUSTOM_STRATEGY_TEMPLATE` block printed |
| Mutex enforcement (D-44) | `--custom foo.py --strategy naive` | argparse rejects with `not allowed with argument` |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Replaced `grep -q` with `grep ... > /dev/null` and wrapped error-path commands in `{ cmd || true; } | grep …` (SIGPIPE / pipefail interaction)**

- **Found during:** Task 3-04-02 first run of `bash scripts/verify_phase3.sh` → 7 of 20 checks failed
- **Issue:** Two interacting bash semantics killed the gate:
  1. `set -o pipefail` propagates the highest non-zero exit code in a pipeline. When the loader's CLI invocation legitimately exits 1 (its job — there's a Polish error message), `python3 sph_sim.py ... | grep -q 'Plik nie istnieje'` returned 1 because of the upstream exit, even though `grep -q` matched. The check then incorrectly recorded `[FAIL]`.
  2. `grep -q` closes stdin as soon as it finds the first match. For long-running upstream processes (like the REPL through `--interactive`), that closure delivers SIGPIPE to the upstream → exit 141 → pipefail propagates → eval reports failure.
- **Fix:** Two surgical changes in `scripts/verify_phase3.sh`:
  - Replaced every `grep -q '...'` with `grep '...' > /dev/null` so grep reads the full stream and never closes stdin early (eliminates SIGPIPE).
  - Wrapped commands that intentionally exit non-zero (the 4 SC #2 layer tests + 2 mutex tests) with `{ cmd 2>&1 || true; } | grep '...' > /dev/null`. The `|| true` neutralises the loader/argparse non-zero exit; the grep is then the sole signal: "was the expected Polish error message printed?". Semantics: we test the error MESSAGE, not the exit code. The 4 LoaderError tests and 2 mutex tests in Section 5 + Section 8 use this pattern.
- **Files modified:** `scripts/verify_phase3.sh` (introduced before commit `d7a1c10` so the committed script is already correct).
- **No retest needed:** Final run after fixes → 20/20 PASS, exit 0. Captured in commit `d7a1c10`.

No other deviations. No Rule 4 architectural decisions. No authentication gates encountered.

## Threat Surface Scan

No new security-relevant surface beyond the plan's `<threat_model>`:

- **T-3-01** (Tampering / Elevation — `exec_module` of user .py) — inherited from Plans 03-01..03-03, ACCEPTED-WITH-WARNING. The template `examples/custom_strategy_template.py` is project-controlled (we commit it), so loading it carries the same banner as any custom — D-45 print fires at line 1 of stdout.
- **T-3-12** (Tampering — verify_phase3.sh writes `/tmp/p3_*` files) — MITIGATED (low): all tmp files use the `p3_` prefix (clearly namespaced); `trap 'rm -f /tmp/p3_*' EXIT` cleans on script exit regardless of PASS/FAIL; no race condition for single-user dev machine; heredoc-generated bad-strategy files are inert (no network, no exec at rest).
- **T-3-13** (Repudiation — `/tmp/p3_template.txt` left behind on abrupt termination) — ACCEPTED: `/tmp` is cleared on reboot on macOS/Linux; debug info for the dev only.
- **T-3-SC** (Dependency confusion / npm/pip install) — N/A: stdlib + POSIX coreutils only. The verify script invokes only `python3`, `bash`, `printf`, `grep`, `cat`, `tail`, `head`, `head -1`, `diff`, `sed`, `rm`, `command`, `chmod` — all in coreutils.

No new threat flags introduced.

## Known Stubs

None. Phase 3 is functionally complete:

- The loader (Plan 01) is pure and tested with 21 unit cases.
- The CLI integration (Plan 02) wires `--custom + --param` through argparse, main.py early branch, and format_human/format_json.
- The REPL integration (Plan 03) adds `do_custom + do_run`, modifies `do_help/do_strategies/do_strategy`, and supports the full edit-run-edit loop.
- The template (Plan 04 / this plan) gives users a copy-paste starter.
- The phase exit gate (Plan 04 / this plan) verifies all 5 ROADMAP Success Criteria mechanically.

The only carried-forward limitation is hardcoded `seed=42` in `SPHShell.do_run` (Plan 03 D-41) — explicit Phase 5 scope to add `--seed` / env override REPL support. That is documented in Plan 03-03's summary, not a stub for Phase 3.

## Issues Encountered

One — the `grep -q` + `set -o pipefail` interaction described under Deviations. Fixed before commit. No other surprises.

## User Setup Required

None. Phase 3 uses only stdlib (`importlib`, `inspect`, `os`, `sys`, `unittest`, `tempfile`, `textwrap`) plus POSIX coreutils for `verify_phase3.sh`. No environment variables, no API keys, no external services. Running `bash scripts/verify_phase3.sh` from any cwd inside the repo is sufficient to assert Phase 3 acceptance.

## Next Phase Readiness

**Phase 3 is complete** — 4/4 plans done (Plan 01 loader + tests, Plan 02 CLI, Plan 03 REPL, Plan 04 template + verify gate). The phase exit gate runs green:

```
$ bash scripts/verify_phase3.sh
...
════════════════════════════════════════
  Phase 3 verification: PASS=20 / FAIL=0
════════════════════════════════════════
✓ Phase 3 ready for /gsd:verify-work
```

All 3 STRAT requirements are fulfilled (STRAT-03 by Plan 02, STRAT-04 by Plan 01, STRAT-05 by this plan). Phase 4 (Rational Agent veto layer) can begin once `/gsd:verify-work` and `/gsd-transition` complete.

## Self-Check: PASSED

Files verified to exist on disk:

- FOUND: `examples/custom_strategy_template.py` (created, 51 lines)
- FOUND: `scripts/verify_phase3.sh` (created, 168 lines, executable -rwxr-xr-x)

Commits verified in `git log --oneline`:

- FOUND: `9dc96f0` (feat(03-04): add examples/custom_strategy_template.py)
- FOUND: `d7a1c10` (feat(03-04): add scripts/verify_phase3.sh)

Behavioral checks (all green at write time):

- `python3 scripts/regression_check.py` → PASS 8/8
- `python3 -m unittest discover tests` → Ran 22 tests, OK
- `bash scripts/verify_phase3.sh` → exit 0, PASS=20 / FAIL=0, "Phase 3 ready" printed

---
*Phase: 03-custom-strategy-loader*
*Completed: 2026-05-27*
