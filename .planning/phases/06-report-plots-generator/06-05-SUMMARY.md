---
phase: 06-report-plots-generator
plan: 05
subsystem: phase-exit-gate
tags: [regression, env-passthrough, verify-script, exit-gate, opt-out, skip-keys, macos-portability]

# Dependency graph
requires:
  - phase: 06-report-plots-generator/01
    provides: "scripts/regression_check.py SKIP_KEYS extended with 'abstain_per_phase' (Phase 6 D-PH6 mirror Phase 4 D-67) — Plan 01 intermediate"
  - phase: 06-report-plots-generator/04
    provides: "write_report orchestrator + banner-on-stderr + SPHSIM_NO_REPORT opt-out + format_json _with_agent_full strip — all 6 ROADMAP SCs reachable"
  - phase: 06-report-plots-generator/00
    provides: "scripts/verify_phase6.sh Wave-0 skeleton (header + check() function + PASS/FAIL counters + final summary block)"
  - phase: 05-cli-deconstruction/04
    provides: "scripts/verify_phase5.sh exit-gate template — copied verbatim shape (check() + banner pattern + final summary)"
provides:
  - "scripts/regression_check.py: subprocess env passthrough (SPHSIM_NO_REPORT=1) — 8 baseline runs no longer create 24 PNG/MD files; PASS 8/8 preserved"
  - "scripts/regression_check.py: SKIP_KEYS rationale comment consolidated to 3 canonical paragraphs (Phase 4 / Phase 5 / Phase 6) — Plan 01 intermediate duplication removed"
  - "scripts/verify_phase6.sh: 39 check() invocations covering all 6 ROADMAP Phase 6 SCs + regression + tests + REPL Pitfalls 2/6 + opt-out — 40/40 PASS (incl. preflight)"
  - "scripts/verify_phase6.sh: portable file-size assertion via `wc -c < file | tr -d ' '` instead of `stat -f%z || stat -c%s` (macOS/Linux divergence sidestepped)"
  - "scripts/verify_phase6.sh: section reordering — regression + tests FIRST (since TestJsonStdoutClean.tearDown rmtrees ./reports/*), THEN preflight artifact bundle, THEN per-SC checks"
  - "scripts/verify_phase6.sh: final `rm -rf ./reports` cleanup — verify script leaves project root pristine"
  - "06-VERIFICATION.md handoff document — full Phase 6 verification state for /gsd:verify-work"
affects:
  - "Phase 6 exit gate is now a single green-or-red decision (PASS=40/FAIL=0 means SHIP; any FAIL means do not merge)"
  - "Future Phase 7+ verify scripts can copy this 10-section + preflight-after-tests pattern verbatim"

# Tech tracking
tech-stack:
  added: []  # Stdlib only — no new dependencies. wc/grep/test/printf are POSIX coreutils already in use.
  patterns:
    - "Test-order safety via reordering: when a test's tearDown wipes shared fs state (./reports/), produce gate artifacts AFTER the test suite runs, not before. Document the dependency inline in script comments so future maintainers do not re-break it."
    - "subprocess.run env passthrough: `env={**os.environ, 'SPHSIM_NO_REPORT': '1'}` inherits parent env (PATH/PYTHONPATH propagate normally) while injecting opt-out — eliminates ./reports/ pollution during the 8 baseline regression runs without touching INVOCATIONS or generate_baseline.py."
    - "Portable file-size assertion: `wc -c < FILE | tr -d ' '` works on macOS BSD and GNU coreutils alike (POSIX shell). `stat -f%z` (BSD) and `stat -c%s` (GNU) are mutually exclusive — using them with `||` fallback produces noisy stderr on the failing variant and breaks under set -e."
    - "Pipe-safe grep pattern: `{ cmd || true; } | grep PATTERN > /dev/null` (copied verbatim from verify_phase5.sh:78 onward) — ensures cmd's non-zero exit does not collapse the pipeline before grep gets a chance to scan."

key-files:
  created:
    - path: .planning/phases/06-report-plots-generator/06-05-SUMMARY.md
      role: "Plan 05 execution summary (this file)"
    - path: .planning/phases/06-report-plots-generator/06-VERIFICATION.md
      role: "Phase 6 verification state handoff for /gsd:verify-work — mirrors Phase 5 shape"
  modified:
    - path: scripts/regression_check.py
      what: |
        - Added `import os` (line 27) — needed for os.environ.
        - subprocess.run() now passes env={**os.environ, 'SPHSIM_NO_REPORT': '1'} (line 113) so 8 baseline runs do not pollute ./reports/.
        - Consolidated SKIP_KEYS rationale comment (lines 35-48) into 3 canonical paragraphs (Phase 4 / Phase 5 / Phase 6), removing duplicated Phase 4 paragraph from Plan 01 intermediate.
        - SKIP_KEYS tuple itself unchanged (9 entries — Phase 4 ×3 + Phase 5 ×5 + Phase 6 ×1).
    - path: scripts/verify_phase6.sh
      what: |
        - Replaced Plan 00's 10 placeholder section-banner echoes (~25 lines) with full body (~140 lines of check() invocations + preflight + cleanup).
        - 39 check() invocations + 1 inline preflight PASS counter = 40 total checks.
        - Section order: 0 cleanup → 1 regression (×2) → 2 tests (×4) → 2a preflight artifact bundle (×1 inline) → 3 SC#1 (×4) → 4 SC#2 (×5) → 5 SC#3 (×4) → 6 SC#4 (×4) → 7 SC#5 (×5) → 8 SC#6 (×4) → 9 REPL Pitfalls (×4) → 10 Opt-out (×3) → final `rm -rf ./reports`.
        - File header docstring (Plan 00 listing 6 SCs) UNCHANGED.
        - check() function definition + PASS/FAIL counters + trap + final summary block UNCHANGED.

decisions:
  - "D-PH6-PLAN05-ENV: subprocess env passthrough chosen over alternative `del os.environ['REPORT_HOME']` style — keeps the opt-out signal explicit at the call site (visible in the env= keyword), avoids parent-shell side effects, single line addition."
  - "D-PH6-PLAN05-WC: portable file-size assertion uses `wc -c < FILE` instead of `stat -f%z || stat -c%s` — eliminates per-OS branching and produces clean error output when the file is absent (the `|| stat -c%s` fallback emits `stat: illegal option -- c` on macOS even when the BSD variant succeeded)."
  - "D-PH6-PLAN05-REORDER: preflight artifact bundle moved AFTER the test suite (section 2a, not section 0) because `tests/test_report.py::TestJsonStdoutClean.tearDown` rmtrees children of `./reports/` after subprocess tests. Discovered when initial section-order draft produced FAIL=15 in sections 3-6; reorder fix gives PASS=40 / FAIL=0."
  - "D-PH6-PLAN05-COMMENT: SKIP_KEYS rationale comment normalized to 3 paragraphs separated by `#` (empty comment lines) — matches PATTERNS §6 evolution diagram. Plan 01's intermediate had two Phase 4 paragraphs (one inline + one summary); consolidated into one Phase 4 paragraph."

metrics:
  duration: ~25 minutes
  commits:
    - hash: 581ecb8
      type: feat
      what: "regression_check.py env passthrough + SKIP_KEYS comment consolidation"
      files: 1
    - hash: 58cdf1b
      type: feat
      what: "verify_phase6.sh flesh-out — 39 check() invocations covering 6 SCs + regression + tests + REPL + opt-out"
      files: 1
  tests_added: 0  # Plan 05 only modifies infrastructure (regression + verify); test suite count stays at 172.
  tests_passing_total: 172  # full unittest discover tests/ post-Plan-05 — no regressions.
  checks_added_to_verify_phase6: 39  # plus 1 inline preflight PASS counter = 40 total in the script.
  verify_phase6_result: "PASS=40 / FAIL=0"
  regression_check_result: "PASS: 8/8 (with no ./reports/ pollution)"
  completed_at: 2026-05-28T09:41:00Z
---

# Phase 6 Plan 05: Phase exit gate (regression env passthrough + verify_phase6.sh full check coverage) Summary

**One-liner:** Closed Phase 6 by extending `scripts/regression_check.py` with subprocess env passthrough (`env={**os.environ, 'SPHSIM_NO_REPORT': '1'}` — eliminates 24-file ./reports/ pollution from the 8 baseline runs) and fleshing out `scripts/verify_phase6.sh` with 39 check() invocations covering all 6 ROADMAP Phase 6 Success Criteria + regression + full test suite + REPL Pitfalls 2/6 + opt-out — gate result: **PASS=40 / FAIL=0**, exit 0, "Phase 6 ready for /gsd:verify-work".

## What Built

### Task 1 — `scripts/regression_check.py` env passthrough + comment consolidation

**Files modified:** `scripts/regression_check.py` (+13 / -6 = 7 net lines)

Three surgical edits:

1. **Added `import os`** (line 27, alphabetical in the stdlib block) — needed for `os.environ`. The module had no prior `os` import despite using `pathlib` for path ops.

2. **subprocess.run env passthrough** (line 113, in `run_invocation`):
   ```python
   # BEFORE
   result = subprocess.run(
       full_args,
       cwd=str(PROJECT_ROOT),
       capture_output=True,
       text=True,
       check=True,
   )

   # AFTER
   # Phase 6 — opt-out side effects in regression: SPHSIM_NO_REPORT=1 forwarded
   # do każdego subprocess'a tak, że 8 baseline runs NIE tworzy 24 plików w ./reports/.
   # RESEARCH §G.18-G.19 + Pitfall 4 mitigation. os.environ dziedziczone, więc
   # lokalne dev env (PATH, PYTHONPATH) propagują się normalnie.
   result = subprocess.run(
       full_args,
       cwd=str(PROJECT_ROOT),
       capture_output=True,
       text=True,
       check=True,
       env={**os.environ, 'SPHSIM_NO_REPORT': '1'},
   )
   ```

3. **SKIP_KEYS rationale comment consolidated** (lines 35-48) — Plan 01's intermediate left two Phase 4 paragraphs (one inline at the original D-67 introduction, one summary above the tuple). Plan 05 merges them into one canonical Phase 4 paragraph, keeping the Phase 5 + Phase 6 paragraphs intact. The 9-entry SKIP_KEYS tuple itself is **unchanged**.

**Verification of Task 1:**
- `python3 scripts/regression_check.py` → `PASS: 8/8` (regression contract preserved).
- After regression run: `./reports/` is **not created** (env passthrough works end-to-end).
- `grep -c 'SPHSIM_NO_REPORT' scripts/regression_check.py` = 2 (comment + injection).
- `grep -c 'env={\*\*os.environ' scripts/regression_check.py` = 1.
- SKIP_KEYS length = 9; `'abstain_per_phase'` preserved from Plan 01.
- Full test suite (`SPHSIM_NO_REPORT=1 python3 -m unittest discover tests`) → 172/172 PASS.

### Task 2 — `scripts/verify_phase6.sh` flesh out (39 check() invocations)

**Files modified:** `scripts/verify_phase6.sh` (+126 / -11 lines; 4061 → 13131 bytes)

Replaced Plan 00's 10 placeholder section-banner echoes with the full body. Section layout (matches verify_phase5.sh template + Phase 6 specifics):

| § | Section | Checks | What it verifies |
|---|---------|--------|------------------|
| 0  | Pre-flight cleanup    | (rm -rf)    | starts from a clean ./reports/ |
| 1  | Regression backwards compat | 2     | regression PASS 8/8 + no pollution from env passthrough |
| 2  | Full test suite       | 4           | unittest discover + test_report + test_plots + test_simulator_abstain |
| 2a | Preflight artifact bundle | 1 (inline) | single sph_sim.py run creates ./reports/<ts>/ with 3 files |
| 3  | SC #1 (REPORT-01)     | 4           | 3 files exist + EXACTLY 3 file count |
| 4  | SC #2 (REPORT-02)     | 5           | ≥6 H2 sections + ≥5 KPI rows + baseline disclaimer + strategia row + Konfiguracja header |
| 5  | SC #3 (PLOT-01/02)    | 4           | PNG signature × 2 + file-size minimums (5 KB / 10 KB) |
| 6  | SC #4 (PLOT-03)       | 4           | relative MD links × 2 + no abs paths + no http links |
| 7  | SC #5 (REPORT-03)     | 5           | compare-mode adds section 7 + table header + werdykt + non-tiny PNG |
| 8  | SC #6 (JSON cleanliness) | 4        | --json stdout parses + banner on stderr + abstain_per_phase present + _with_agent_full stripped |
| 9  | REPL Pitfalls 2/6     | 4           | run/compare REPL commands do not crash on AttributeError + emit expected output |
| 10 | Opt-out               | 3           | SPHSIM_NO_REPORT=1 → no ./reports/ from single/compare/regression |
|    | Final cleanup         | (rm -rf)    | leaves project root pristine |

**Total: 39 check() invocations + 1 inline preflight PASS = 40 PASS / 0 FAIL.**

**Two architectural fixes during implementation:**

1. **Section reordering (D-PH6-PLAN05-REORDER):** Initial draft placed preflight (single sph_sim.py run) FIRST, then regression + tests, then SC checks consuming the preflight `LATEST` directory. Result: PASS=25 / FAIL=15. Root cause: `tests/test_report.py::TestJsonStdoutClean.tearDown` rmtrees children of `./reports/` after subprocess tests. Fix: move preflight artifact bundle to section 2a, AFTER the test suite runs. New result: PASS=40 / FAIL=0.

2. **Portable file-size assertion (D-PH6-PLAN05-WC):** Initial draft used `stat -f%z FILE 2>/dev/null || stat -c%s FILE` for cross-platform support. Problem: on macOS the `-c%s` fallback runs even when `-f%z` succeeded (the `||` only checks exit status, and when the file is missing BOTH fail noisily). Fix: switched to `wc -c < FILE | tr -d ' '` — POSIX, single-form, works on macOS BSD + GNU coreutils, produces clean numeric output.

**Verification of Task 2:**
- `bash scripts/verify_phase6.sh` → exits 0 with `Phase 6 verification: PASS=40 / FAIL=0` + `✓ Phase 6 ready for /gsd:verify-work`.
- `grep -cE '^check ' scripts/verify_phase6.sh` = 39 (target ≥30 — generous margin).
- All 6 SCs covered: SC #1 / #2 / #3 / #4 / #5 / #6 grep counts: 6 / 7 / 6 / 6 / 7 / 6.
- `test -x scripts/verify_phase6.sh` — executable bit preserved.
- After verify run: `./reports/` does NOT exist (final `rm -rf` cleanup works).

## Deviations from Plan

**None.** Both tasks executed as planned. Two during-implementation discoveries documented as decisions:

- **D-PH6-PLAN05-REORDER** — moved preflight artifact bundle to after section 2 (tests) because `TestJsonStdoutClean.tearDown` wipes `./reports/` children. Not a deviation from PLAN.md's intent (which assumed the preflight artifacts would survive section 2); a refinement based on observed test behavior.
- **D-PH6-PLAN05-WC** — switched from `stat -f%z || stat -c%s` (PLAN.md suggested form) to `wc -c < FILE`. PLAN.md's stat form was a Linux-first reflex; macOS BSD stat's incompatibility with `-c%s` produced false negatives. Fix is portable across both.

Both refinements made inside the same Task 2 implementation; no re-planning needed.

## Gate Verification (full PLAN.md sequence)

```
=== Step 1: regression_check.py ===
PASS: 8/8
  (no pollution after regression)

=== Step 2: verify_phase6.sh ===
exit=0
  Phase 6 verification: PASS=40 / FAIL=0
✓ Phase 6 ready for /gsd:verify-work

=== Step 3: full test suite ===
Ran 172 tests in 13.940s
OK

=== Step 4: final pollution check ===
FINAL: no ./reports/ pollution after gate
```

All four gate steps green. Phase 6 is shippable.

## ROADMAP Phase 6 Success Criteria — Coverage Matrix

| SC # | REQ ID | Description | Checks in verify_phase6.sh | Status |
|------|--------|-------------|----------------------------|--------|
| #1 | REPORT-01 | Każde uruchomienie → ./reports/<ts>/ z 3 plikami | 4 (3 file existence + exact count) | PASS |
| #2 | REPORT-02 | report.md zawiera sekcje + KPI + baseline | 5 (sekcje ≥6, KPI ≥5, baseline, strategia, konfiguracja) | PASS |
| #3 | PLOT-01/02 | 2 PNG-i renderują się | 4 (2× signature, 2× size minimum) | PASS |
| #4 | PLOT-03 | Relatywne MD image links | 4 (2× positive grep, 2× negative grep) | PASS |
| #5 | REPORT-03 | --compare-agent → delta KPI section | 5 (preflight + 4 content checks) | PASS |
| #6 | (JSON compat) | --json stdout zachowuje v1.0 compatibility | 4 (parseable JSON + banner-on-stderr + abstain key + no _with_agent_full leak) | PASS |

Plus 6 supporting checks (regression × 2, tests × 4) and 7 hardening checks (REPL × 4, opt-out × 3) — total 40 PASS.

## Files / Artifacts

| File | Status | Note |
|------|--------|------|
| scripts/regression_check.py | modified | +13/-6 lines; env passthrough + comment consolidation; behavior PASS 8/8 with zero pollution |
| scripts/verify_phase6.sh | modified | +126/-11 lines; 39 check() invocations covering 6 SCs + regression + tests + REPL + opt-out; PASS 40/0 |
| .planning/phases/06-report-plots-generator/06-05-SUMMARY.md | created | this file |
| .planning/phases/06-report-plots-generator/06-VERIFICATION.md | created | Phase 6 handoff document for /gsd:verify-work |

## Suggested commit message (already used per-task)

Task 1: `feat(06-05): regression_check.py env passthrough + SKIP_KEYS comment consolidation`
Task 2: `feat(06-05): flesh out verify_phase6.sh with all SC check() invocations (PASS=40/FAIL=0)`

Final docs commit (by orchestrator, or this agent after both tasks): `docs(06-05): complete Phase 6 Plan 05 — exit gate green (PASS=40/FAIL=0)`

## Self-Check: PASSED

- [x] `scripts/regression_check.py` exists and modified (env passthrough verified live).
- [x] `scripts/verify_phase6.sh` exists, executable, 39 check() invocations.
- [x] Commit 581ecb8 exists in git log.
- [x] Commit 58cdf1b exists in git log.
- [x] regression_check.py PASS 8/8 with no ./reports/ pollution.
- [x] verify_phase6.sh exits 0 with PASS=40 / FAIL=0.
- [x] Full test suite 172/172 PASS.
- [x] No ./reports/ pollution remaining in project root after gate.
- [x] No STATE.md / ROADMAP.md modifications (orchestrator owns those writes).
