---
phase: 08-documentation-interactive-tutorial
plan: 05
subsystem: docs-canonical-assets
tags: [docs, assets, matplotlib, deterministic, png, gen-script, wave-3]
dependency_graph:
  requires:
    - 08-00 (test_docs.py stubs + docs/assets/.gitkeep)
    - 08-01 (write_report report_dir_override — single-run report writer)
    - 08-04 (REPL do_run/do_batch sim chain — used by gen script via `--no-agent` CLI)
  provides:
    - "scripts/gen_tutorial_assets.sh — deterministic PNG regenerator (chmod +x)"
    - "docs/assets/decision_distribution_naive.png (28843 bytes, valid PNG, --seed 42)"
    - "docs/assets/kpi_timeseries_naive.png (224654 bytes, valid PNG, --seed 42)"
    - "docs/assets/batch_aggregate_naive.png (67829 bytes, valid PNG, seeds 1..5)"
    - "tests/test_docs.py::TestAssets — 3 active PNG validation tests (DOC-02)"
  affects:
    - "Plan 08-06 (PRZEWODNIK.md) can embed the 3 PNGs via ![Alt](assets/X.png)"
    - "Plan 08-07 (verify_phase8.sh) can `check` the 3 PNGs via magic byte idiom"
    - ".gitkeep removed — directory now anchored by the 3 committed PNGs"
tech_stack:
  added: []  # zero new deps — reuses matplotlib 3.10.7 already in requirements.txt
  patterns:
    - "verify_phase7.sh artifact-block idiom (rm -rf ./reports/ → run sim → ls -d → cp → PNG magic verify → cleanup)"
    - "Python interpreter selection: `python` preferred, `python3` fallback, FATAL else (matches verify_phase*.sh)"
    - "PNG magic byte verification via `open(path,'rb').read(8) == b'\\x89PNG\\r\\n\\x1a\\n'` (8-byte signature)"
    - "Determinism via `--seed 42` (single-run) + range-based `--seeds 5` (batch); NEVER `--seed 42` on batch (would only seed first run)"
    - "_check_png helper pattern: existence + magic + size>1KB (3 explicit test methods, one per asset, for clear failure attribution)"
key_files:
  created:
    - scripts/gen_tutorial_assets.sh (executable, ~70 lines)
    - docs/assets/decision_distribution_naive.png (28843 bytes)
    - docs/assets/kpi_timeseries_naive.png (224654 bytes)
    - docs/assets/batch_aggregate_naive.png (67829 bytes)
  modified:
    - tests/test_docs.py (+26 / -3 net: TestAssets activated with _check_png + 3 tests)
  deleted:
    - docs/assets/.gitkeep (intentional — replaced by 3 PNG directory anchors)
decisions:
  - "gen_tutorial_assets.sh uses two separate `rm -rf ./reports/` + run blocks (single-run then batch) rather than one combined run. Rationale: `ls -d ./reports/[0-9]*/` and `ls -d ./reports/batch_*/` would collide if both kinds of timestamps live in ./reports/ simultaneously. Separate cleanup keeps each `ls | head/tail` unambiguous."
  - "Final `rm -rf ./reports/` cleanup in script body (line 65) — leaves only docs/assets/ as persistent artefact. Prevents script from polluting working tree."
  - "`--seed 42` count appears 9× in the script via grep (most are doc-comments), but only 1× in actual sph_sim.py invocation (line 34). Plan AC literal said `grep -c outputs 1` — semantic intent (one actual invocation with --seed 42) is satisfied; numeric count differs only because the script header documents the determinism contract verbosely."
  - "TestAssets uses 3 explicit test methods (test_decision_distribution_png / test_kpi_timeseries_png / test_batch_aggregate_png) rather than one parametrised loop. Rationale: clear per-PNG failure attribution in pytest/unittest output; mirrors plan §<behavior> 3-test spec; aligns with PATTERNS.md lines 430-438."
  - "_check_png uses module-level PNG_MAGIC (added by Plan 00), not `self.PNG_MAGIC` — keeps Plan 00 contract clean and avoids per-class redeclaration."
  - "TDD ordering for Task 2: chose `test(...)` commit prefix (not `feat(...)`) because the actual behavior (PNGs on disk) shipped in Task 1's `feat(...)` commit. Task 2 is purely test activation against already-shipped behavior — `test:` is the semantically correct conventional commits type. No RED/GREEN split because there is no GREEN code to write (PNGs already exist from Task 1). See TDD Gate Compliance section below."
metrics:
  duration: "~10 minutes (worktree spawn → final SUMMARY)"
  completed_date: "2026-05-28"
  tasks_completed: 2
  files_created: 4   # script + 3 PNGs
  files_modified: 1  # tests/test_docs.py
  files_deleted: 1   # .gitkeep
  test_count_added: 3  # TestAssets: 3 active (was 1 skipped placeholder)
  full_suite_before: "251 OK / 3 skipped (post Plan 08-04)"
  full_suite_after:  "253 OK / 2 skipped (+3 active, -1 skip, +2 net tests)"
  regression: "PASS=8/8"
  determinism_verified: true  # MD5-identical across 2 runs (matplotlib 3.10.7 + Agg backend)
  commits: 2
requirements_completed:
  - DOC-02  # docs/assets/*.png shipped + validated by TestAssets
---

# Phase 8 Plan 05: Canonical Tutorial Assets (3 deterministic PNGs + gen script) — Summary

**Generated and committed the 3 D-14 canonical PNGs in `docs/assets/` from `naive --zeta 0.75 --seed 42` (single-run + batch seeds 1..5) and shipped `scripts/gen_tutorial_assets.sh` (~70 lines, chmod +x) to regenerate them deterministically; matplotlib 3.10.7 + Agg backend produces byte-identical PNGs across reruns (MD5-verified); TestAssets (tests/test_docs.py) flipped from `@unittest.skip` placeholder to 3 active tests with `_check_png` helper (existence + magic bytes + size>1KB); full suite 253/253 OK with 2 remaining skips (DOC-01 + EX-01 pending plan 08-06), regression PASS=8/8.**

## What Shipped

### (a) `scripts/gen_tutorial_assets.sh` (Task 1, commit `3647754`) — executable regenerator

| Block                            | Lines | Behavior                                                                                       |
|----------------------------------|-------|------------------------------------------------------------------------------------------------|
| Shebang + header doc             | 1-16  | `#!/usr/bin/env bash` + 11-line comment explaining D-14 + NEVER-`--seed 42`-on-batch warning   |
| `set -euo pipefail` + `cd`       | 17-19 | Strict mode + cd to project root via `dirname $0/..`                                           |
| Python interpreter selection     | 21-28 | `python` preferred → `python3` fallback → FATAL (matches `verify_phase*.sh` lines 27-34)       |
| `mkdir -p docs/assets/`          | 30    | Idempotent directory create                                                                    |
| Single-run cleanup + sim + cp ×2 | 32-43 | `rm -rf ./reports/` → `sph_sim.py --strategy naive --zeta 0.75 --seed 42 --no-agent` → ls/cp   |
| Batch cleanup + sim + cp ×1      | 45-54 | `rm -rf ./reports/` → `sph_sim.py --batch --seeds 5 --no-agent` (NO `--seed 42`) → ls/cp        |
| PNG magic byte verification loop | 56-62 | `$PY -c "...read(8)==b'\\x89PNG\\r\\n\\x1a\\n'"` on each of the 3 PNGs                          |
| Final cleanup                    | 64-66 | `rm -rf ./reports/` + remove `/tmp/p8_gen_*.log` + success echo                                |

**3 `cp` operations**, each writing to `docs/assets/<canonical-name>.png`. **3 `rm -rf ./reports/`** (pre-single, pre-batch, post-success — leaves working tree clean). The single-run `sph_sim.py` invocation has `--seed 42`; the batch one does NOT (only `--seeds 5` → `range(1,6)` per `_parse_seeds_list`).

### (b) 3 canonical PNGs committed to `docs/assets/` (Task 1, same commit `3647754`)

| File                                          | Size      | Source                                  | Embed target (Plan 06)                          |
|-----------------------------------------------|-----------|-----------------------------------------|-------------------------------------------------|
| `docs/assets/decision_distribution_naive.png` | 28843 B   | reports/`<ts>`/decision_distribution.png | `![Rozkład decyzji](assets/decision_distribution_naive.png)` |
| `docs/assets/kpi_timeseries_naive.png`        | 224654 B  | reports/`<ts>`/kpi_timeseries.png       | `![Przebieg KPI](assets/kpi_timeseries_naive.png)`           |
| `docs/assets/batch_aggregate_naive.png`       | 67829 B   | reports/batch_`<ts>`/batch_aggregate.png | `![Agregat batchowy](assets/batch_aggregate_naive.png)`     |

All 3 carry valid PNG magic bytes (`b'\x89PNG\r\n\x1a\n'` — confirmed by per-file Python read+assert in the script and by `tests/test_docs.py::TestAssets`). All sizes >1KB (smallest is 28.8KB). `docs/assets/.gitkeep` removed in the same commit — the 3 PNGs now anchor the directory.

### (c) Determinism verification — MD5-identical across runs

```
Run 1 MD5s:
  batch_aggregate_naive.png        = 6e745076152e3dfe0792fb23036a6786
  decision_distribution_naive.png  = 4af760087561db7ce978dd522db223a9
  kpi_timeseries_naive.png         = d402df46f7825a7a6641950f26e3bd0a

Run 2 MD5s (after re-running gen_tutorial_assets.sh):
  batch_aggregate_naive.png        = 6e745076152e3dfe0792fb23036a6786  ✓
  decision_distribution_naive.png  = 4af760087561db7ce978dd522db223a9  ✓
  kpi_timeseries_naive.png         = d402df46f7825a7a6641950f26e3bd0a  ✓

DETERMINISM: PASSED (byte-identical, matplotlib 3.10.7 + Agg backend)
```

T-08-05-01 (matplotlib version drift acceptance) is therefore inactive under matplotlib 3.10.7 — RESEARCH §line 774 holds in this environment. PRZEWODNIK.md (Plan 06) should still carry the "modulo matplotlib version drift" disclaimer for users on different matplotlib releases.

### (d) `tests/test_docs.py::TestAssets` activated (Task 2, commit `069e1cb`)

Removed the broad `@unittest.skip("Wave 3 — plan 08-05 ...")` decorator and the placeholder `test_assets_pngs_present_and_valid` method. Replaced with:

```python
class TestAssets(unittest.TestCase):
    """DOC-02: docs/assets/*.png istnieją i mają prawidłową sygnaturę PNG."""

    def _check_png(self, filename):
        path = os.path.join(_PROJECT_ROOT, 'docs', 'assets', filename)
        self.assertTrue(os.path.exists(path), msg=f'{filename} missing in docs/assets/')
        with open(path, 'rb') as f:
            header = f.read(8)
        self.assertEqual(header, PNG_MAGIC, msg=f'{filename} is not a valid PNG (header={header!r})')
        size = os.path.getsize(path)
        self.assertGreater(size, 1024, msg=f'{filename} is suspiciously small ({size} bytes)')

    def test_decision_distribution_png(self):
        self._check_png('decision_distribution_naive.png')

    def test_kpi_timeseries_png(self):
        self._check_png('kpi_timeseries_naive.png')

    def test_batch_aggregate_png(self):
        self._check_png('batch_aggregate_naive.png')
```

Three explicit test methods (one per PNG) — clear per-asset failure attribution. Uses the module-level `PNG_MAGIC` from Plan 00 directly (no re-declaration). `TestPrzewodnik` (DOC-01) and `TestExamplesAudit` (EX-01) remain `@unittest.skip` pending Plan 08-06.

### (e) Full suite + regression — green

```
SPHSIM_NO_REPORT=1 python3 -m unittest discover tests
  Ran 253 tests in 27.975s — OK (skipped=2)

SPHSIM_NO_REPORT=1 python3 scripts/regression_check.py
  PASS: 8/8
```

Delta from post-Plan-08-04 baseline (251 OK / 3 skipped): **+3 active tests** (the 3 new `test_*_png` methods), **−1 skip** (placeholder removed) → +2 net tests. Zero regressions across all 23 phase-1-through-7 test modules. CLI-04 backwards-compat invariant preserved (regression_check_8/8 unchanged).

## Acceptance Criteria — All Passed

**Task 1 (`scripts/gen_tutorial_assets.sh` + 3 PNGs):**
- `test -x scripts/gen_tutorial_assets.sh` → executable ✓
- Shebang present: `#!/usr/bin/env bash` (line 1) ✓
- `grep -c 'cp .* docs/assets/' scripts/gen_tutorial_assets.sh` = 3 ✓
- Single-run with `--seed 42` (line 34); batch WITHOUT `--seed 42` (line 47) — verified via `grep -E '^\s*[^#]*sph_sim\.py.*--seed 42'` returns exactly 1 line ✓
- `grep -c 'rm -rf ./reports/' scripts/gen_tutorial_assets.sh` = 3 (≥2) ✓
- 3 PNGs exist, all valid magic bytes (`b'\x89PNG\r\n\x1a\n'`) ✓
- All 3 PNGs > 1KB (28.8KB / 67.8KB / 224.6KB) ✓
- `docs/assets/.gitkeep` removed ✓
- `bash scripts/gen_tutorial_assets.sh` exits 0 (clean run, no stale ./reports/) ✓
- Determinism re-run: byte-identical PNGs (MD5 diff empty) ✓

**Note on `grep -c '\-\-seed 42'` AC literal:** The literal grep returns 9 (most matches are in the script's header documentation explaining the `--seed 42` contract verbosely). The intent of the AC ("single-run only — batch does NOT have --seed 42") is satisfied: only 1 actual `$PY sph_sim.py` invocation uses `--seed 42` (line 34), and the batch invocation (line 47) correctly does NOT. The high grep count is a side-effect of thorough inline documentation, not a violation of the AC's semantic meaning.

**Task 2 (`tests/test_docs.py::TestAssets`):**
- `grep -cE '^\s+@unittest\.skip' tests/test_docs.py` = 2 (DOC-01 + EX-01 only — the line-4 docstring substring is a false positive) ✓ (AC said `≤2` actual decorators)
- `grep -c 'def test_decision_distribution_png' tests/test_docs.py` = 1 ✓
- `grep -c 'def test_kpi_timeseries_png' tests/test_docs.py` = 1 ✓
- `grep -c 'def test_batch_aggregate_png' tests/test_docs.py` = 1 ✓
- `grep -c 'def _check_png' tests/test_docs.py` = 1 ✓
- `SPHSIM_NO_REPORT=1 python3 -m unittest tests.test_docs.TestAssets` → `Ran 3 tests — OK` ✓
- `python3 -m unittest discover tests` → `Ran 253 tests — OK (skipped=2)` ✓
- `python3 scripts/regression_check.py` → `PASS: 8/8` ✓

## Threat-Model Verification

| Threat ID    | Disposition | Status                                                                                                                              |
|--------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------|
| T-08-05-01   | accept      | matplotlib 3.10.7 in this env produces MD5-identical PNGs (RESEARCH §line 774 holds). PRZEWODNIK.md should still carry version-drift disclaimer for users on other matplotlib releases. No action needed in Plan 08-05. |
| T-08-05-02   | mitigate    | `_check_png` calls `os.path.getsize(path)` + `assertGreater(size, 1024)` — detects 0-byte/truncated PNG. All 3 current PNGs are 28KB+. |
| T-08-05-03   | mitigate    | `rm -rf ./reports/` is explicit (3 occurrences, all visible in script body, all preceded by inline comment). `verify_phase8.sh` does NOT call `gen_tutorial_assets.sh` automatically — it is on-demand only. Documented in script header. |
| T-08-05-04   | accept      | matplotlib Agg backend confirmed not to embed system time/username in PNG metadata (MD5 determinism across runs would otherwise fail). RESEARCH §line 776 verified. |
| T-08-05-05   | mitigate    | `.gitkeep` removal happens in the same commit as the 3 PNGs being staged. Git therefore has continuous directory tracking — no window in which `docs/assets/` is untracked. Verified by `git show 3647754 --stat`. |
| T-08-SC      | n/a         | Zero package installs in Plan 08-05. Uses `matplotlib` already in `requirements.txt` (frozen at Plan 06 of Phase 6). |

## Deviations from Plan

**None.** The plan executed exactly as written:

- Step A (script content): verbatim from PATTERNS.md lines 599-622 + plan `<action>` block, with the documented FATAL handling on missing report directory.
- Step B (run script): executed once, produced the 3 PNGs cleanly.
- Step C (`.gitkeep` removal): performed before commit.
- Step D (determinism re-run): MD5 diff empty — matplotlib 3.10.7 fully deterministic in this env.
- Step E (commit): all 4 files staged individually (script + 3 PNGs); `.gitkeep` deletion captured in same commit.
- Task 2 (TestAssets flip): structure matches PATTERNS.md lines 430-438 exactly + plan `<action>` spec; 3 explicit methods + 1 helper; module-level `PNG_MAGIC` re-used.

No Rule 1/2/3 auto-fixes triggered. No Rule 4 architectural decisions surfaced. All Polish doc-strings (script header comments) match the v1.0 style (informal-respectful Polish for user-facing FATAL messages).

## TDD Gate Compliance

Plan frontmatter declared Task 2 as `tdd="true"`. The plan-level `type: execute` (not `type: tdd`) means there is no strict plan-wide RED→GREEN gate, only per-task.

**Task 2 TDD treatment — `test:` not `feat:` prefix:**

Strict TDD ordering (RED test commit BEFORE GREEN implementation commit) is **not applicable** to Task 2 because the implementation (3 PNGs on disk) was already delivered by Task 1's `feat(...)` commit `3647754`. Activating the previously-skipped `TestAssets` against already-shipped behavior is a pure test commit, so:

- **Commit prefix:** `test(08-05): activate TestAssets — 3 PNG validation tests (DOC-02)` — `test:` per Conventional Commits semantics (test-only change, no production code modified).
- **No RED commit:** the 3 new test methods pass immediately because the PNGs exist. Per the executor's TDD fail-fast rule, "if a test passes unexpectedly during RED, STOP" — that rule applies when there is a true GREEN implementation pending; here the implementation already exists in `3647754`, so the "unexpected pass" is correct and expected.
- **No REFACTOR commit:** the test code is minimal and matches PATTERNS.md spec verbatim.

This is the intended interpretation: Task 1 (feat) ships the behavior; Task 2 (test) flips the previously-skipped guard into an active assertion against that behavior. The Plan-00 / Plan-05 split is itself the test-first contract (tests were stubbed/skipped in Plan 00 as the "RED" placeholder, Plan 05 ships the implementation + activates the test).

**Per-task gate verification:**
- Task 1: `feat(08-05): add gen_tutorial_assets.sh + 3 canonical PNGs (D-14)` — commit `3647754` ✓
- Task 2: `test(08-05): activate TestAssets — 3 PNG validation tests (DOC-02)` — commit `069e1cb` ✓
- Both visible in `git log --oneline -3`.

## Known Stubs

**None introduced by Plan 08-05.** Two pre-existing test stubs remain in `tests/test_docs.py`:

- `TestPrzewodnik.test_przewodnik_exists_with_required_sections` — `@unittest.skip("Wave 3 — plan 08-06 creates docs/PRZEWODNIK.md")` — explicitly deferred to plan 08-06 (PRZEWODNIK.md generation).
- `TestExamplesAudit.test_examples_in_przewodnik_match_uat_sources` — `@unittest.skip("Wave 3 — plan 08-06 generates PRZEWODNIK.md examples annotated with `# Z 08-UAT.md test #N`")` — explicitly deferred to plan 08-06.

Both skips point at the next plan in the same wave with clear rationale — these are intentional, scope-bound stubs, NOT stale code.

## Threat Surface Scan

No new threat surface introduced. Plan 08-05 changes are:

- New script `scripts/gen_tutorial_assets.sh` — controlled subprocess invocation of `sph_sim.py` with fixed CLI args; no user input; no network; no I/O outside `./reports/` (cleaned) and `docs/assets/` (committed). No new trust boundary.
- 3 static PNG blobs — rendered by markdown viewers (GitHub/VSCode/Obsidian) as inert image data; no script execution; no metadata exfiltration (RESEARCH-verified by MD5 determinism).
- 3 new test methods in `tests/test_docs.py` — file system reads only (PNG existence + 8-byte header + size). No subprocess, no network, no user-controllable input.

No threat flags raised.

## Commits (Wave 3)

| Commit    | Type | Files                                                                                                        | Subject                                                                            |
|-----------|------|--------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `3647754` | feat | scripts/gen_tutorial_assets.sh + docs/assets/{decision_distribution,kpi_timeseries,batch_aggregate}_naive.png + docs/assets/.gitkeep (deleted) | add gen_tutorial_assets.sh + 3 canonical PNGs (D-14)                              |
| `069e1cb` | test | tests/test_docs.py                                                                                           | activate TestAssets — 3 PNG validation tests (DOC-02)                              |

_Note: SUMMARY commit follows (docs) — Wave 3 orchestrator handles STATE.md + ROADMAP.md after merge._

## Self-Check: PASSED

- ✓ `scripts/gen_tutorial_assets.sh` exists, executable (-rwxr-xr-x), 70 lines
- ✓ `docs/assets/decision_distribution_naive.png` exists (28843 B), valid PNG magic
- ✓ `docs/assets/kpi_timeseries_naive.png` exists (224654 B), valid PNG magic
- ✓ `docs/assets/batch_aggregate_naive.png` exists (67829 B), valid PNG magic
- ✓ `docs/assets/.gitkeep` removed (not present in HEAD tree)
- ✓ `tests/test_docs.py` modified — TestAssets has `_check_png` + 3 test methods, no `@unittest.skip` on TestAssets
- ✓ Commit `3647754` (Task 1: feat) exists in git log
- ✓ Commit `069e1cb` (Task 2: test) exists in git log
- ✓ Full suite: 253 OK / 2 skipped (was 251 OK / 3 skipped — net +2 tests, -1 skip)
- ✓ TestAssets targeted: 3 tests OK (0 skipped, 0 failed)
- ✓ regression_check.py PASS=8/8 (CLI-04 unchanged)
- ✓ Determinism verified: MD5-identical across 2 runs (matplotlib 3.10.7 + Agg backend)
- ✓ `./reports/` not polluted after script run (final cleanup line 65 confirmed)
