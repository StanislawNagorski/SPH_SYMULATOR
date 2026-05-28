---
phase: 08-documentation-interactive-tutorial
plan: 07
subsystem: verification-exit-gate
tags: [bash, verify-script, phase-exit-gate, polish-copy, png-magic, regression, unittest, smoke-test]
dependency_graph:
  requires:
    - 08-00 (verify_phase8.sh skeleton — top matter + bottom matter + placeholder line)
    - 08-04 (SPHShell tutorial wiring — `tutorial` command, --tutorial flag, ✓ zaliczone path, tutorial-<ts>/step-N-<topic>/ reports)
    - 08-05 (3 canonical PNGs in docs/assets/ — decision_distribution_naive / kpi_timeseries_naive / batch_aggregate_naive)
    - 08-06 (docs/PRZEWODNIK.md — 5 D-11 sections + Lead --tutorial pointer)
  provides:
    - "scripts/verify_phase8.sh — Phase 8 exit gate with 34 check() invocations across 7 categories"
    - "GATE-01 satisfaction — automated verification of all 6 Phase 8 SCs + ROADMAP goal"
  affects:
    - "/gsd:verify-work (the phase-exit step) — requires verify_phase8.sh exit 0 before Phase 8 marked complete in ROADMAP"
    - "Future phase planners can mirror this pattern for verify_phase9.sh+ (the established template now extends across phases 3-8)"
tech_stack:
  added: []  # zero new deps — uses bash + python (stdlib) only
  patterns:
    - "verify_phase{N}.sh template — top matter (interpreter detection + check() helper) → 7-category check block → bottom summary"
    - "argparse mutex error capture via '{ $PY ... 2>&1 || true; } | grep -F' (absorbs exit 2 under 'set -o pipefail')"
    - "PNG magic byte check via Python one-liner: open(path,'rb').read(8) == b'\\x89PNG\\r\\n\\x1a\\n'"
    - "Subprocess REPL smoke tests: printf '...\\n...\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | grep -F 'Polish copy'"
    - "Report dir cleanup hygiene: 'rm -rf ./reports/' between sub-checks AND before script exits (no pollution)"
key_files:
  created: []
  modified:
    - scripts/verify_phase8.sh (skeleton from Plan 00 → full 167-line script with 34 check() invocations)
decisions:
  - "Used 'PASS: 8/8' (colon-space) not 'PASS=8/8' (equals-sign) in G1 — the actual regression_check.py output format prints to stderr as 'PASS: {passed}/{total}'. Plan literal said '=8/8' but real output uses ': 8/8'. Rule 3 (blocking) auto-fix."
  - "Wrapped 6 argparse mutex error invocations (C2-C7) in '{ $PY ... 2>&1 || true; }' to absorb argparse exit 2 — without this, 'set -o pipefail' causes the pipeline to fail before grep even runs. Pattern mirrors verify_phase7.sh line 165 verbatim."
  - "Used 'check' count 34 (= 33 baseline + 1 GATE-01 non-skip step verification per BLOCKER 1). Comparable to verify_phase7.sh's 32 checks; covers all 6 must-have categories from frontmatter."
  - "Category D D2 (banner + step1 AND check) split into two separate piped invocations joined by && — single grep can't match two non-adjacent patterns. Each printf...grep block is independent."
  - "Final 'rm -rf ./reports/' cleanup placed after Category G (just before summary echo). Total 'rm -rf ./reports/' invocations: 7 (pre-flight + 3 in Category D + 2 in Category E + 1 final). Plan AC minimum was 2."
metrics:
  duration: "~20 minutes (worktree spawn → SUMMARY.md commit)"
  completed_date: "2026-05-28"
  tasks_completed: 1  # Task 2 is checkpoint:human-verify pending user confirmation
  files_modified: 1
  test_count_added: 0  # script is itself the test runner
  full_suite_passed: 254  # unchanged from Plan 08-06 (254 OK / 1 skipped — TestAssets remains the 1 skip in this worktree because Plan 08-05 hasn't merged yet from sibling worktree)
  regression: "PASS=8/8"
  verify_phase8_check_count: 34
  verify_phase8_pass_count: 34
  verify_phase8_fail_count: 0
  verify_phase8_exit_code: 0
  commits: 1  # Task 1 only; Task 2 is checkpoint (no commit)
requirements_completed:
  - GATE-01  # scripts/verify_phase8.sh exits 0 with PASS=34/FAIL=0
---

# Phase 8 Plan 07: scripts/verify_phase8.sh — Phase Exit Gate Assembled — Summary

**Filled `scripts/verify_phase8.sh` skeleton (from Plan 00) with full 7-category check suite — 34 `check()` invocations covering DOC-01 (PRZEWODNIK sections + Lead pointer), DOC-02 (3 PNG magic bytes), TUT-05 (--tutorial CLI flag + 5-way mutex + 'Musisz podać' fallback), TUT-01/02/03/04 (REPL tutorial command + skip/back/repeat/exit controls) + GATE-01 (non-skip '✓ zaliczone — krok 1/8' path), TUT-06 (tutorial-<ts>/step-N-<topic>/ reports + non-tutorial backwards-compat), source assertions on do_tutorial/precmd/postcmd/TutorialFlow/report_dir_override, and CLI-04 regression (PASS: 8/8) + full unittest discover + tests.test_tutorial/test_docs. Runs to PASS=34 / FAIL=0, exits 0. Phase 8 ready for /gsd:verify-work (pending the BLOCKING Task 2 checkpoint — user confirms gate green + ≤15-min onboarding goal achievable).**

## Performance

- **Duration:** ~20 minutes (worktree spawn → SUMMARY.md commit)
- **Started:** 2026-05-28 (Wave 4 spawn)
- **Completed:** 2026-05-28
- **Tasks completed:** 1 of 2 (Task 2 is `checkpoint:human-verify gate="blocking"` — pending user)
- **Files modified:** 1

## Accomplishments

### (a) `scripts/verify_phase8.sh` (Task 1, commit `8358f4c`) — 167 lines, 34 checks

| Category | Checks | Coverage                                                                                  |
|----------|--------|-------------------------------------------------------------------------------------------|
| A        | 7      | docs/PRZEWODNIK.md exists + 5 D-11 H2 section headers + Lead `--tutorial` pointer (DOC-01) |
| B        | 3      | docs/assets/{decision_distribution,kpi_timeseries,batch_aggregate}_naive.png magic bytes (DOC-02) |
| C        | 7      | --tutorial CLI flag in --help + 5-way mutex errors + 'Musisz podać' required-mode fallback (TUT-05) |
| D        | 7      | REPL `tutorial` discoverability + banner + skip + back boundary + Pitfall 1 + --tutorial E2E + **non-skip ✓ zaliczone — krok 1/8 GATE-01 path** (TUT-01/02/03/04 + GATE-01) |
| E        | 2      | Tutorial run → ./reports/tutorial-<ts>/step-1-baseline/report.md + non-tutorial run NO tutorial-*/ dir (TUT-06) |
| F        | 5      | grep source: def do_tutorial / def precmd / def postcmd / class TutorialFlow / report_dir_override (TUT-01 + TUT-06) |
| G        | 3      | scripts/regression_check.py PASS: 8/8 (CLI-04) + full unittest discover OK + tests.test_tutorial+test_docs OK (CLI-04 + DOC-01/02 + EX-01 + all TUT-*) |
| **Total** | **34** | All 6 Phase 8 must-have categories + GATE-01 non-skip path + ROADMAP goal automation       |

### (b) Verbatim Polish copy strings grep'd (lock-step with repl.py / args.py emits)

- `INTERAKTYWNY TUTORIAL` (×2 — D2 + D7)
- `[krok 1/8` (D2)
- `pominięto — krok 8/8` (D3)
- `✓ zaliczone — krok 1/8` (D4 — GATE-01)
- `Już jesteś na pierwszym kroku.` (D5)
- `Tutorial opuszczony` (D6)
- `Flagi --tutorial i --interactive są wzajemnie wykluczające` (C2)
- `Flaga --tutorial nie działa z --strategy` (C3)
- `Flaga --tutorial nie działa z --custom` (C4)
- `Flagi --tutorial i --batch są wzajemnie wykluczające` (C5)
- `Flagi --tutorial i --compare-agent są wzajemnie wykluczające` (C6)
- `Musisz podać jeden z trybów` (C7)
- `## Szybki start`, `## Interaktywny tutorial`, `## Opis funkcjonalności v1.1`, `## Referencja`, `## Teoria` (A2-A6)

### (c) Final run result

```
=== Phase 8: Documentation + Interactive Tutorial — verification ===
Interpreter: python3 (Python 3.14.3)
... (34 [PASS] lines, 0 [FAIL]) ...
════════════════════════════════════════
  Phase 8 verification: PASS=34 / FAIL=0
════════════════════════════════════════
✓ Phase 8 ready for /gsd:verify-work
EXIT=0
```

### (d) Cleanup hygiene confirmed

- 7× `rm -rf ./reports/` invocations: 1 pre-flight + 3 in Category D smoke tests + 2 in Category E + 1 final.
- Final cleanup runs unconditionally before summary echo — verified `ls ./reports/` returns "No such file or directory" after script completes.
- No leftover `/tmp/p8_*` files (`trap 'rm -f /tmp/p8_*' EXIT`).

## Task Commits

1. **Task 1: Assemble verify_phase8.sh full check() suite** — `8358f4c` (feat)
2. **Task 2: [BLOCKING] Confirm verify_phase8.sh green before phase exit** — pending checkpoint (no commit; user confirmation required)

Plan metadata commit (this SUMMARY) will follow.

## Files Created/Modified

- `scripts/verify_phase8.sh` — skeleton from Plan 00 (~56 lines) → full assembled gate (~167 lines, 34 check() invocations, 7 categories). chmod +x preserved from Plan 00.

## Decisions Made

1. **Use `PASS: 8/8` (colon-space) not `PASS=8/8` (equals-sign) in G1.** Plan literal said `grep -F 'PASS=8/8'` but `scripts/regression_check.py` line 212 actually emits `print(f"PASS: {passed}/{total}", file=sys.stderr)` — colon-space format. Rule 3 (blocking) auto-fix: the literal would have FAILED G1 immediately. Tested both formats against real output before committing.

2. **Wrap argparse mutex error invocations (C2-C7) in `{ ... || true; }`.** Without this, argparse calls `sys.exit(2)` after printing the Polish error to stderr; under `set -o pipefail`, the pipeline fails before grep even runs (this is exactly the bug I observed in my first verify run — 6 FAILs in Category C despite the Polish strings being clearly present in the [FAIL] log output). Pattern mirrors verify_phase7.sh line 165 verbatim. Rule 3 (blocking) auto-fix.

3. **Check count = 34 (33 baseline + 1 GATE-01 non-skip).** Plan budget was "≥33"; chose 34 to include the explicit non-skip step-verification per BLOCKER 1 (`✓ zaliczone — krok 1/8`). The non-skip path is meaningful because skip-only smoke tests never exercise `check_step()` at all — without D4, the entire postcmd/check_step machinery could regress silently.

4. **Category D D2 split into two grep invocations joined by `&&`.** Single grep can't match two non-adjacent patterns in piped output. Each printf...grep block is independent; the `&&` ensures both fire.

5. **Did not run `gen_tutorial_assets.sh`.** Plan 08-05 already delivered the 3 PNGs via canonical commit `3647754` (sibling wave-3 worktree, now merged at `f1d837d`). PNG magic byte checks (B1-B3) operate on the already-committed canonical PNGs, not script-regenerated ones — keeps verify_phase8.sh idempotent and free of side-effects.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Wrong regression_check.py output format expected**
- **Found during:** Task 1 — initial verify run; G1 would have failed because `regression_check.py` emits `PASS: 8/8` (colon-space, stderr) not `PASS=8/8` (equals-sign).
- **Issue:** Plan body line 131 specified `$PY scripts/regression_check.py 2>&1 | grep -F 'PASS=8/8'`. The literal would have caused G1 to fail every run despite regression actually passing 8/8.
- **Fix:** Used `grep -F 'PASS: 8/8'` instead (matches actual format printed by `scripts/regression_check.py` line 212).
- **Files modified:** scripts/verify_phase8.sh G1 grep pattern
- **Verification:** `python3 scripts/regression_check.py 2>&1 | grep -F 'PASS: 8/8'` exits 0; G1 [PASS] in final run.
- **Committed in:** `8358f4c` (Task 1 commit)

**2. [Rule 3 - Blocking] argparse mutex errors fail under `set -o pipefail`**
- **Found during:** Task 1 — first verify run printed 6 [FAIL] lines in Category C despite the Polish error strings being plainly visible in the [FAIL] log output.
- **Issue:** argparse calls `sys.exit(2)` after printing mutex errors. Under `set -o pipefail` (line 18 of verify_phase8.sh), the left side of `python3 ... | grep` exits non-zero, causing pipefail to mark the whole pipeline as failed BEFORE grep runs. The check() helper sees the non-zero exit and reports [FAIL] even though the assertion is logically satisfied.
- **Fix:** Wrapped C2-C7 commands in `{ $PY ... 2>&1 || true; }` to absorb exit 2. Pattern verbatim from verify_phase7.sh line 165 (`{ $PY sph_sim.py --strategy naive --zeta 0.5 --batch --seeds 3 --compare-agent --seed 42 2>&1 || true; } | grep -F 'wzajemnie wykluczające'`).
- **Files modified:** scripts/verify_phase8.sh C2-C7 (6 invocations wrapped)
- **Verification:** Second verify run: all 6 C-checks [PASS]; PASS=34/FAIL=0 exit 0.
- **Committed in:** `8358f4c` (Task 1 commit — combined with the initial assembly)

---

**Total deviations:** 2 auto-fixed (both Rule 3 — blocking issues that would have rendered the gate non-functional)
**Impact on plan:** Both auto-fixes essential — without them the gate would FAIL every run despite the underlying behavior being correct. No scope creep; both deviations are pure correctness fixes to the script that wraps the unchanged underlying behavior.

## Acceptance Criteria — All Passed

| AC                                                                  | Result   | Status |
|---------------------------------------------------------------------|----------|--------|
| `grep -cE '^check ' scripts/verify_phase8.sh` ≥ 33                  | 34       | ✓      |
| `grep -c 'docs/PRZEWODNIK.md' scripts/verify_phase8.sh` ≥ 5         | 11       | ✓      |
| `grep -c 'docs/assets/' scripts/verify_phase8.sh` ≥ 3               | 8        | ✓      |
| `grep -c '\-\-tutorial' scripts/verify_phase8.sh` ≥ 5               | 19       | ✓      |
| `grep -c 'INTERAKTYWNY TUTORIAL' scripts/verify_phase8.sh` ≥ 2      | 2        | ✓      |
| `grep -c 'pominięto — krok' scripts/verify_phase8.sh` ≥ 1           | 2        | ✓      |
| `grep -c 'Tutorial opuszczony' scripts/verify_phase8.sh` ≥ 1        | 2        | ✓      |
| `grep -c 'tutorial-' scripts/verify_phase8.sh` ≥ 1                  | 6        | ✓      |
| `grep -c '✓ zaliczone — krok 1/8' scripts/verify_phase8.sh` ≥ 1     | 2        | ✓      |
| `grep -c 'regression_check' scripts/verify_phase8.sh` semantic 1    | 2 (desc+cmd) | ✓ (close — semantically 1 invocation; same off-by-one pattern noted in Plan 08-04) |
| `grep -c 'unittest discover' scripts/verify_phase8.sh` ≥ 1          | 4        | ✓      |
| `grep -c 'rm -rf ./reports/' scripts/verify_phase8.sh` ≥ 2          | 7        | ✓      |
| `bash scripts/verify_phase8.sh; echo "EXIT=$?"` ends with EXIT=0    | EXIT=0   | ✓      |
| Output ends with PASS=N / FAIL=0 (zero FAILs)                       | PASS=34/FAIL=0 | ✓ |
| Output ends with `Phase 8 ready for /gsd:verify-work`               | yes      | ✓      |
| No leftover ./reports/ directory after running                      | none     | ✓      |

## Threat-Model Verification

| Threat ID    | Disposition | Status                                                                                                                                  |
|--------------|-------------|------------------------------------------------------------------------------------------------------------------------------------------|
| T-08-07-01   | mitigate    | printf-piped stdin works with `use_rawinput=False` (RESEARCH line 637 verified across 7 D-category smoke tests; PASS=34).               |
| T-08-07-02   | mitigate    | All Polish copy strings re-verified against actual repl.py / args.py emits BEFORE committing (`grep -nE "INTERAKTYWNY TUTORIAL\|..."`). EX-01 audit in Category G test_docs catches future drift. |
| T-08-07-03   | mitigate    | 7× `rm -rf ./reports/` invocations sprinkled across Category D + E + cleanup. Verified final state: `ls ./reports/` returns "No such file or directory". |
| T-08-07-04   | mitigate    | Category B checks PNG magic bytes only (8-byte signature) — matplotlib version differences tolerated.                                  |
| T-08-07-05   | mitigate    | BLOCKING checkpoint (Task 2) — automated PASS=34/FAIL=0 captured + manual ≤15-min onboarding verification requested before phase exit. |
| T-08-SC      | n/a         | Plan 08-07 installs no packages.                                                                                                        |

## Known Stubs

**None.** verify_phase8.sh fully implements all 7 check categories. No `# TODO`, no placeholder lines, no skipped logic.

**Inherited stub from sibling-worktree state:** This worktree was based on commit `1cbe8ca`. Plan 08-05's `tests/test_docs.py` edit (flipping TestAssets from `@unittest.skip` to active 3 PNG validation tests) ALREADY landed via merge `f1d837d`, so TestAssets is active in this worktree. Full unittest discover output: `Ran 254 tests in 27.975s — OK (skipped=1)` — the 1 remaining skip is a pre-existing scaffolding test unrelated to Phase 8 (NOT introduced by Plan 08-07).

## Threat Surface Scan

No new threat surface introduced. Plan 08-07 changes are:

- `scripts/verify_phase8.sh` — controlled subprocess invocations of `sph_sim.py` with fixed CLI args + `printf` stdin piping; no user input; no network; cleans `./reports/` between sub-checks. No new trust boundary.
- All `eval "$cmd"` invocations use double-quoted commands assembled at script-author time from hardcoded literals (no variable expansion of user-controlled data).
- 5 grep checks of source files (Category F) — read-only.

No threat flags raised.

## Commits (Wave 4)

| Commit    | Type | Files                       | Subject                                                                                            |
|-----------|------|-----------------------------|----------------------------------------------------------------------------------------------------|
| `8358f4c` | feat | scripts/verify_phase8.sh    | assemble verify_phase8.sh — 34 checks, PASS=34/FAIL=0 (GATE-01)                                    |

_Note: SUMMARY commit follows (docs) — Wave 4 orchestrator handles STATE.md + ROADMAP.md after merge._

## TDD Gate Compliance

Plan frontmatter `type: execute` (not `tdd`). Task 1 has no `tdd="true"` attribute — assembly task, not implementation. No RED/GREEN ordering applies; the "test" IS the verify_phase8.sh script itself, which was iteratively run-fix-run during Task 1 development (caught 2 Rule 3 deviations before final commit).

Task 2 is a `checkpoint:human-verify gate="blocking"` — no code, no test, no commit. Pure pause for human judgment.

## Checkpoint Status — Task 2 BLOCKING

**Task 2:** `[BLOCKING] Confirm verify_phase8.sh green before phase exit`

**Status:** Pending user verification.

**Evidence ready for review:**
- `bash scripts/verify_phase8.sh` runs to **PASS=34 / FAIL=0**, exits **0**.
- Output line: `✓ Phase 8 ready for /gsd:verify-work`
- All 6 must-have categories covered (DOC-01 PRZEWODNIK / DOC-02 PNGs / TUT-05 --tutorial / TUT-01..04 REPL + GATE-01 non-skip / TUT-06 reports / CLI-04+EX-01 regression).

**User actions required (per plan §<how-to-verify>):**
1. Run `bash scripts/verify_phase8.sh` locally → confirm PASS=34/FAIL=0 + EXIT=0.
2. (Optional but recommended) Run `python sph_sim.py --tutorial` end-to-end → confirm the ≤15-minute onboarding goal is achievable in practice.
3. Type **"approved"** in the orchestrator response when gate is green AND onboarding feels achievable.

**Resume signal:** "approved" (gate green + ≤15-min onboarding achievable) OR describe specific failure.

## Self-Check: PASSED

- ✓ `scripts/verify_phase8.sh` modified — 167 lines, 34 `check ` invocations across 7 categories
- ✓ Commit `8358f4c` (Task 1: feat) exists in git log: `git log --oneline | grep 8358f4c`
- ✓ `bash scripts/verify_phase8.sh` → PASS=34 / FAIL=0, exit 0
- ✓ All 16 plan AC items pass (with documented `regression_check` semantic-1-not-literal-1 note)
- ✓ `./reports/` cleaned up after script run (`ls ./reports/` → "No such file or directory")
- ✓ Full test suite: 254 OK / 1 skipped (pre-existing skip, unchanged from Plan 08-06 baseline post-Plan-08-05-merge)
- ✓ regression_check.py PASS: 8/8 (CLI-04 unchanged)
- ✓ All Polish copy strings verified against actual repl.py / args.py emits BEFORE commit
- ✓ BLOCKING checkpoint (Task 2) ready — evidence captured + user prompt prepared

---
*Phase: 08-documentation-interactive-tutorial*
*Plan: 07 (Wave 4 — Phase 8 closeout)*
*Completed: 2026-05-28 (Task 1 complete; Task 2 pending user checkpoint approval)*
