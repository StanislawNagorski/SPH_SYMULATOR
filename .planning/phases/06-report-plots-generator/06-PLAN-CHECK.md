# Phase 6 Plan Check Report

**Date:** 2026-05-28
**Checker:** gsd-plan-checker (goal-backward)
**Phase:** 6 — Report + plots generator
**Plans checked:** 6 (06-00 … 06-05)
**CONTEXT.md present:** No (no user-locked decisions to honor; dimension 7 N/A)
**RESEARCH.md present:** Yes (with Architectural Responsibility Map → dim 7c active)
**PATTERNS.md present:** Yes → dim 12 active
**VALIDATION.md present:** Yes → dim 8 active
**Stance:** Adversarial. Hypothesis = plans will not deliver the goal until proven otherwise.

---

## Verdict: PASS WITH NOTES

All 6 SCs traceable end-to-end; Wave 2 parallelism is correctly engineered with disjoint touches; every RESEARCH §J pitfall has an explicit mitigation site; verify_phase6.sh promises ~36 checks against a ≥20 target. No BLOCKERs. Notes below are WARNINGS the executor should be aware of (mostly accuracy/copy-paste hygiene that will surface during execution, not goal-defeating).

---

## Dimension Scores (0-5)

| Dim | Score | Notes |
|-----|-------|-------|
| D1 — Goal-to-task traceability | 5 | Every SC chain bottoms out at a real plan/task; see trace table |
| D2 — Wave-2 parallelism safety | 5 | Touches genuinely disjoint; test-file split landed in Plan 00 stub taxonomy |
| D3 — Critical-constraint coverage | 5 | All 8 constraints sited, including Pitfall 6 `json=False` fake_args |
| D4 — Test ↔ SC coverage | 5 | VALIDATION.md per-task map satisfied; 14 tests in test_report after W3, 6 in test_plots, 3 in test_simulator_abstain |
| D5 — verify_phase6.sh completeness | 4 | All 6 SCs covered with margin (PASS≥20, target 36); minor warning on stat -f%z vs stat -c%s portability handled but slightly brittle |
| D6 — Atomic-commit / rollback safety | 3 | No explicit `<rollback>` element in any plan; relies on git-revert per-plan granularity; commit message templates per plan provide implicit boundary |
| D7 — N/A (no CONTEXT.md) | — | Dimension skipped (no user decisions to compare) |
| D7b — Scope reduction detection | 5 | No "v1/v2", "static-for-now", "deferred" language present; D-PH6 SKIP_KEYS is intentional Strategia-B mirror, not scope reduction |
| D7c — Architectural tier compliance | 5 | Each task assigns work to the tier the Responsibility Map names (Report tier owns mkdir/render/savefig; CLI/REPL tier owns call sites; Core tier owns abstain aggregation) |
| D8 — Nyquist compliance | 5 | VALIDATION.md exists; every implementation task has `<automated>` verify; sampling continuity OK; Wave 0 stub-test dependencies satisfied |
| D9 — Cross-plan data contracts | 4 | `_with_agent_full` private key is the only cross-plan data contract — explicitly threaded in 3 sites with format_json filter; one warning on filter blast radius |
| D10 — CLAUDE.md compliance | — | No `./CLAUDE.md` in repo root; dimension skipped |
| D11 — Research resolution | 5 | RESEARCH §N Open Questions 1+2 explicitly resolved in plans (compare history via `_with_agent_full`; env-var opt-out chosen). Q3-5 deferred with explicit rationale in Plan 03 / Plan 04 |
| D12 — Pattern compliance | 5 | Every new file references its PATTERNS analog; `format_config_header` reuse, `veto_phase_stats` mirror, `sphsim/agent/__init__.py` shape, `verify_phase5.sh` skeleton are all cited |

**Overall:** 4.9 / 5.0 weighted. PASS WITH NOTES.

---

## Critical Findings (BLOCKERS — must fix before execution)

**None.** No issue rises to BLOCKER under the goal-backward analysis. Every SC has a concrete chain of tasks producing it; no decision is reduced; no parallelism conflict identified; all pitfalls are sited.

---

## Recommendations (WARNINGS — should fix, not blocking)

### W-1 [scope_sanity] Plan 06-04 ma 2 auto tasks + 1 checkpoint = 3 task units; Plan 04 też ma `autonomous: false`

- **Plan:** 06-04
- **Severity:** WARNING (within target)
- **Description:** Plan 04 file count = 4 modified (`__init__.py`, `main.py`, `repl.py`, `output.py`); Task 1 alone touches 4 files including a substantial rewrite of `sphsim/report/__init__.py` (~110 LoC) plus 6 edits across main.py + 6 in repl.py + 1 in output.py. This is at the upper edge of "single task" scope. The checkpoint:human-verify task offloads visual validation correctly, so context budget is fine — but Task 1 is dense.
- **Fix hint:** Acceptable as-is given the work is mechanical (mostly insertions following dictated templates from RESEARCH §L). Executor should commit after each call-site wire-in if context starts pressing.

### W-2 [task_completeness] Plan 06-00 Task 2 verify command silently relies on `tests/__init__.py` not pre-existing

- **Plan:** 06-00
- **Task:** 2
- **Severity:** WARNING
- **Description:** Task 2 says "If `tests/__init__.py` exists (likely empty per Python package convention), APPEND…". Empirical check just now: `tests/__init__.py` is empty (size 0 per `cat` output). The "append vs create" branching is sound but the verify command at line 296 has subtle shell escaping (`{ [ ! -d ./reports ] || [ -z "$(ls -A ./reports 2>/dev/null)" ]; }`) — if the executor's shell tokenizer differs, the negation can flip. Mitigation already provided in Plan 02 Task 1 acceptance criteria mirror.
- **Fix hint:** Consider replacing with `find ./reports -mindepth 1 -maxdepth 1 -type d | head -1 | grep -q . && exit 1 || exit 0` for shell-portability. Not blocking — bash 3.x+ handles the original.

### W-3 [task_completeness] Plan 06-01 verify command (Task 1) uses a Python heredoc-style `-c "..."` with multi-line content

- **Plan:** 06-01
- **Task:** 1
- **Severity:** WARNING
- **Description:** Lines 251-260 inline a 9-line Python script via `python -c "..."`. The indented `from sphsim...` lines inside the bash heredoc will fail under Python 3 if leading whitespace is preserved (IndentationError). The same pattern appears in 06-02 verify (line 472-496) and 06-03 (305-339). Looking at the existing repo, `tests/test_env.py:_run_sph` style proves the team usually shells these out to small `tmpfile.py` scripts or uses single-line forms. The plans' embedded python -c blocks may need adjustment if shell preserves indentation.
- **Fix hint:** Either (a) verify the executor strips the leading 4-space indent the markdown source shows, or (b) reformat each `python -c "..."` block flush-left before invoking. The actual *acceptance_criteria* commands are well-formed; only the `<verify><automated>` blocks have this risk.

### W-4 [verification_derivation] verify_phase6.sh SC#6 banner check pipes stderr through stdout filter

- **Plan:** 06-05
- **Task:** 2
- **Severity:** WARNING
- **Description:** Check `"SC #6 (banner): 'Raport zapisany do:' obecny w stderr (NIE stdout)"` uses `2>&1 1>/dev/null | grep …` — this redirects stderr to where stdout was (terminal), then nulls stdout, but the pipe captures the *original stdout*, not stderr. The standard idiom is `cmd 2>&1 >/dev/null | grep …` (note order — same tokens, but spacing must be exact). Both work in bash if applied correctly; the plan's spelling `2>&1 1>/dev/null` is right but easy to miscopy. If the executor types `2>/dev/null 1>&2` accidentally, the check inverts and false-PASSes.
- **Fix hint:** Suggest the executor double-check this single line. The companion check ("--json stdout pure JSON despite banner") is the real safety net — if banner leaks into stdout, JSON parse fails and that check catches it.

### W-5 [task_completeness] No `<rollback>` element in any of the 6 plans

- **Plans:** All 6
- **Severity:** WARNING (process hygiene)
- **Description:** None of the plans declare an explicit `<rollback>` section. The repo uses worktrees (per `.planning/config.json` `use_worktrees: true`), so per-plan revert = per-worktree discard, which is implicitly atomic. But there's no captured "what to undo if Task N partially commits then breaks Task N+1." Wave 2 parallel plans (02 + 03) are particularly susceptible because the merge into main wave is non-trivial if one of them needs reverting.
- **Fix hint:** Add a one-liner per plan: "Rollback: `git restore <files_modified>`; verify by re-running quick test suite." Plans 02 and 03 should additionally note their disjoint file sets so rollback of one does not require rolling back the other.

### W-6 [scope_sanity] Plan 06-04 Task 1 mixes 4 substantial responsibilities in one task

- **Plan:** 06-04
- **Task:** 1
- **Severity:** WARNING
- **Description:** Task 1 simultaneously: (a) writes 110-LoC `__init__.py` with orchestrator + 2 helpers + 1 extract helper, (b) edits main.py at 4 call sites + 1 import + 1 run_compare return-dict mutation, (c) edits repl.py at 2 call sites + 2 fake_args extensions + 1 res_combined mutation + 1 import, (d) edits output.py format_json filter. Total: 4 files, ~14 edit sites, ~150 LoC churn. This is at the very top of the "single task" envelope. Task 2 separately handles the test side, which is the right split, but Task 1 itself could split (orchestrator vs wiring vs format_json) without losing atomic-coherence.
- **Fix hint:** Accept as-is given the wiring is mechanical and the verify is end-to-end. If execution stalls, planner should be ready to split Task 1 into 1a (orchestrator only) and 1b (wiring + format_json filter).

### W-7 [task_completeness] Plan 06-04 Task 2 `_run_sph` env override quirk

- **Plan:** 06-04
- **Task:** 2
- **Severity:** WARNING
- **Description:** `TestJsonStdoutClean.test_json_stdout_is_parseable_json_despite_banner` calls `_run_sph(..., SPHSIM_NO_REPORT='')`. Per Plan 00 Task 1 spec, `_run_sph` defaults `SPHSIM_NO_REPORT='1'` and accepts an `SPHSIM_NO_REPORT=''` override. The implementation in Plan 00 (line 156): `env = {**os.environ, 'SPHSIM_NO_REPORT': kwargs.pop('SPHSIM_NO_REPORT', '1')}`. Setting to `''` does NOT remove the variable; it sets it to empty string, which `os.environ.get('SPHSIM_NO_REPORT')` evaluates as truthy=False (empty string is falsy). So `write_report` proceeds. This is correct but subtle — emphasize in executor's mental model that the var is *defined as empty*, not deleted.
- **Fix hint:** Add a one-line comment in Plan 00 Task 1 helper acknowledging this semantics; the test in Plan 04 already exercises it correctly.

### W-8 [cross_plan_data_contracts] `_with_agent_full` filter in format_json affects all underscore-prefixed top-level keys forever

- **Plans:** 06-04 (consumer), 06-05 (regression preserves)
- **Severity:** WARNING (forward-compat)
- **Description:** `output.py` `format_json` extension `and not k.startswith('_')` silently strips ANY future underscore-prefixed top-level key from the JSON output. This is intentional (private-key convention) but is permanent ABI-level behavior change. If Phase 7+ adds a public key starting with `_` (unlikely but possible), it would be silently dropped.
- **Fix hint:** Document the underscore-prefix-private convention in the format_json docstring during Plan 04 Task 1 edit (Step 4). A single comment line suffices.

### W-9 [pattern_compliance] PATTERNS.md §1 mentions `sphsim/report/api.py` variant; plans correctly chose `__init__.py` inline

- **Plans:** 06-02, 06-04
- **Severity:** INFO (resolved correctly)
- **Description:** PATTERNS.md §1 noted that planner could put `write_report` body in either `__init__.py` or a separate `api.py`. Plans 02 + 04 chose inline `__init__.py`, mirroring the agent/__init__.py decision documented in PATTERNS §1. This is consistent — no action needed; flagged only for traceability.

---

## Goal-Backward Trace (per-SC chain)

### SC #1 — "Każde uruchomienie tworzy ./reports/<ts>/ z 3 plikami"

| Step | Plan | Task | Concrete output |
|------|------|------|-----------------|
| Wave 0 stub container | 06-00 | T1 | `tests/test_report.py::TestReportFiles` skip-stub |
| Wave 3 orchestrator | 06-04 | T1 | `sphsim/report/__init__.py::write_report` mkdir + 3-file write |
| Wave 3 CLI wire (4 sites) | 06-04 | T1 (Edits 3-6) | `main.py` write_report call after each sim.run / run_compare |
| Wave 3 REPL wire (2 sites) | 06-04 | T1 (Edits 3, 6) | `repl.py::do_run + do_compare` write_report call |
| Wave 3 test GREEN | 06-04 | T2 | `TestReportFiles::test_report_files_created_in_timestamp_dir` |
| Wave 4 exit gate | 06-05 | T2 (Section 3) | 4 check() invocations on `${LATEST}/{report.md,*.png}` |

**Chain status:** COMPLETE. End-to-end smoke in 06-04 Task 1 verify creates 3 files; 06-05 has 4 SC#1 checks.

### SC #2 — "report.md zawiera 6 sekcji + 5 KPI rows + baseline row"

| Step | Plan | Task | Concrete output |
|------|------|------|-----------------|
| Markdown renderer | 06-02 | T1 | `render_report` assembles 6 sections via private `_render_*` helpers |
| Section 1 reuse | 06-02 | T1 | imports `format_config_header` verbatim → `## Konfiguracja środowiska` |
| KPI table 5 rows | 06-02 | T1 | `_KPI_ROWS` tuple drives `_render_kpi_table` |
| Baseline row | 06-02 | T1 | `_render_baseline_comparison` loads `08-naive-zeta-0.75-baseline.json` |
| Test coverage | 06-02 | T2 | `TestReportSections` 5 GREEN tests |
| Exit gate | 06-05 | T2 (Section 4) | 5 check() invocations (sections + KPI keys + baseline + strategy + konfiguracja) |

**Chain status:** COMPLETE. _KPI_ROWS canonical tuple guarantees all 5 keys; baseline disclaimer string asserted.

### SC #3 — "PNG files for COMMIT/ABSTAIN/VETO bar chart + KPI timeseries with last-100 window"

| Step | Plan | Task | Concrete output |
|------|------|------|-----------------|
| Data gap fix (abstain) | 06-01 | T1 | `Device.abstain_phase_stats` + simulator aggregation → `abstain_per_phase` |
| Matplotlib plotters | 06-03 | T1 | `plot_decision_distribution` (3 bar groups) + `plot_kpi_timeseries` (twin-axis + axvspan) |
| Agg backend pin | 06-03 | T1 (Step 1) | `matplotlib.use('Agg')` BEFORE pyplot import (Pitfall 1) |
| close-figure discipline | 06-03 | T1 (Steps 2, 3) | `try: … finally: plt.close(fig)` in both functions (Pitfall 5) |
| Tests GREEN | 06-03 | T2 | `TestPlots` (4 tests, PNG magic-byte + size > 1KB) + `TestPlotDimensions` (2 tests) |
| Exit gate | 06-05 | T2 (Section 5) | 4 check() invocations (PNG signature, size thresholds) |

**Chain status:** COMPLETE. PLOT-01 ABSTAIN bars get real data from Plan 01; both plots verified with PNG signature.

### SC #4 — "PNG-i linkowane jako relatywne ścieżki, render w GitHub/VSCode/Obsidian"

| Step | Plan | Task | Concrete output |
|------|------|------|-----------------|
| MD link emission | 06-02 | T1 | `_render_plots_section` emits `![Rozkład decyzji per faza](decision_distribution.png)` + `![Przebieg KPI w czasie](kpi_timeseries.png)` |
| Test GREEN | 06-02 | T2 | `TestPlotLinks` 2 tests + negative assertions (no absolute, no http) |
| Manual visual check | 06-04 | T3 (checkpoint) | Human opens report.md in GitHub + VSCode + Obsidian, confirms inline render |
| Exit gate | 06-05 | T2 (Section 6) | 4 check() invocations (2 positive grep, 2 negative grep) |

**Chain status:** COMPLETE. Manual checkpoint is the right gate for cross-renderer visual fidelity; automated greps prevent regressions.

### SC #5 — "--compare-agent dodaje tabelę delta KPI"

| Step | Plan | Task | Concrete output |
|------|------|------|-----------------|
| Section 7 renderer | 06-02 | T1 | `_render_compare_section` emits `## Porównanie z RationalAgent` + delta table + werdykt |
| Section 7 test | 06-02 | T2 | `TestReportSections::test_compare_mode_adds_seventh_section` |
| `_with_agent_full` threading | 06-04 | T1 (Step 2-3) | `run_compare` + `do_compare` add `_with_agent_full` private key |
| Compare-mode CLI/REPL wire | 06-04 | T1 (Edits 3, 5 main + Edit 6 repl) | `write_report(mode='compare')` calls |
| Format_json strip | 06-04 | T1 (Step 4) | `not k.startswith('_')` filter preserves regression 8/8 |
| Compare-mode tests | 06-04 | T2 | `TestReportCompareMode` 2 tests (delta section + PNGs from with_agent history) |
| Exit gate | 06-05 | T2 (Section 7) | 5 check() invocations including compare-mode kpi_timeseries.png >10KB |

**Chain status:** COMPLETE. Open Question §N.1 resolved with `_with_agent_full` pattern; PNG threading verified by file-size check.

### SC #6 — "--json output zachowuje kompatybilność v1.0"

| Step | Plan | Task | Concrete output |
|------|------|------|-----------------|
| Banner-on-stderr | 06-04 | T1 (all 4 main + 2 repl wire-ins) | `print(..., file=sys.stderr)` after every write_report |
| Underscore filter | 06-04 | T1 (Step 4) | format_json strips `_with_agent_full` |
| SKIP_KEYS for abstain_per_phase | 06-01 | T2 + 06-05 T1 | regression_check.py SKIP_KEYS extended (Plan 01 intermediate, Plan 05 consolidate) |
| Env passthrough | 06-05 | T1 | `subprocess.run(..., env={**os.environ, 'SPHSIM_NO_REPORT': '1'})` |
| JSON stdout test | 06-04 | T2 | `TestJsonStdoutClean` 2 tests (stdout parses + underscore-key absent) |
| Exit gate | 06-05 | T2 (Section 8) | 4 check() invocations (JSON parse, banner-on-stderr, abstain_per_phase present, _with_agent_full absent) |

**Chain status:** COMPLETE. Regression 8/8 preservation is the canonical SC#6 oracle; PASS=8/8 asserted in 06-01 T2, 06-04 T1, 06-05 T1, and 06-05 T2.

---

## Pitfall Coverage Matrix (RESEARCH §J → plan/task)

| Pitfall | Description | Addressed in | Mechanism |
|---------|-------------|--------------|-----------|
| 1 | matplotlib GUI backend on macOS/SSH | 06-03 T1 Step 1 | `matplotlib.use('Agg')` BEFORE `import matplotlib.pyplot as plt` |
| 2 | PNG file lock on Windows when viewer open | 06-04 T1 (collision suffix) | Each run → new `<ts>-N` dir; never overwrites |
| 3 | `--json` stdout corrupted by report banner | 06-04 T1 (all 6 wire-ins) | `print(..., file=sys.stderr)` |
| 4 | Test pollution — 100+ `reports/` dirs in CI | 06-00 T2 (`tests/__init__.py` + `conftest.py`); 06-05 T1 (subprocess env passthrough) | Layered defense: setdefault env var in test pkg + subprocess env injection |
| 5 | matplotlib memory leak (figures not closed) | 06-03 T1 Steps 2, 3 | `try: … finally: plt.close(fig)` in BOTH plot functions |
| 6 | REPL `fake_args` missing fields | 06-04 T1 (Edits 2 + 4) | Add `json=False, compare_agent=...` to both REPL fake_args; PATTERNS §4 audit table referenced |
| 7 | Polish chars in filesystem path (defensive) | 06-03 T1 Step 1 | `plt.rcParams['font.sans-serif'] = ['DejaVu Sans', …]` fallback |

**All 7 pitfalls have explicit, sited mitigations.** No deferral, no implicit assumption.

---

## Wave-2 Parallelism Audit (Plans 02 + 03 disjoint touches)

| File | Plan 02 (markdown) | Plan 03 (plots) | Disjoint? |
|------|--------------------|-----------------|-----------|
| `sphsim/report/__init__.py` | CREATE (5-LoC shim) | (no touch) | ✓ |
| `sphsim/report/markdown.py` | CREATE | (no touch) | ✓ |
| `sphsim/report/plots.py` | (no touch) | CREATE | ✓ |
| `tests/test_report.py` | MODIFY (2 classes) | (no touch) | ✓ |
| `tests/test_plots.py` | (no touch) | MODIFY (2 classes) | ✓ |

**Confirmed.** The test-file split (Plan 00 Task 1 produces `test_report.py` AND `test_plots.py` separately) is the critical enabler. Without that split, both plans would race on `test_report.py`. Plan 00's interfaces section explicitly documents this as the reason.

**Cross-import check:** Plan 03 explicitly forbids `from sphsim.report.markdown import …` in `plots.py` (per Plan 03 Step 4 constraints). Plan 02 has zero matplotlib import in markdown.py (verified in acceptance_criteria line 507: `grep -c 'matplotlib' … = 0`). Parallel safety **proven**, not assumed.

---

## Verify_phase6.sh Completeness Audit (Plan 06-05)

| SC # | Check count promised | Plan 05 section | Body sample |
|------|----------------------|-----------------|-------------|
| Pre-flight | 1 | Section 0 | LATEST=$(ls -dt …) |
| Regression | 2 | Section 1 | `$PY scripts/regression_check.py` |
| Test suite | 4 | Section 2 | discover + 3 narrowed unittest |
| SC #1 | 4 | Section 3 | 3-file exists + count == 3 |
| SC #2 | 5 | Section 4 | grep H2 ≥6, KPI keys ≥5, baseline disclaimer, strategy row, konfiguracja header |
| SC #3 | 4 | Section 5 | 2× PNG magic-byte + 2× size thresholds |
| SC #4 | 4 | Section 6 | 2× positive grep + 2× negative grep |
| SC #5 | 5 | Section 7 | preflight + section 7 + delta header + werdykt + PNG > 10KB |
| SC #6 | 4 | Section 8 | JSON parse, banner stderr, abstain_per_phase present, _with_agent_full absent |
| REPL Pitfalls | 4 | Section 9 | 2× run + 2× compare (no AttributeError) |
| Opt-out | 3 | Section 10 | CLI single + CLI compare + regression |
| **Total** | **~36** | | Target ≥20, generous margin |

All 6 ROADMAP SCs covered with explicit per-SC sections + REPL Pitfalls 2/6 + opt-out. PASS=36 / FAIL=0 expected.

---

## Dependency Graph Audit

```
Wave 0:   06-00 (no deps)
            ↓
Wave 1:   06-01 (deps: 06-00)
            ↓
Wave 2:   06-02 (deps: 06-01)   ║   06-03 (deps: 06-01)   ← PARALLEL
            ↓                       ↓
Wave 3:   06-04 (deps: 06-02, 06-03)
            ↓
Wave 4:   06-05 (deps: 06-04)
```

- All `depends_on` arrays match wave numbers correctly.
- No cycles, no forward references, no missing-plan references.
- Wave 2 parallelism declared correctly (both depend ONLY on Wave 1, not on each other).

---

## Context Compliance

CONTEXT.md does not exist for Phase 6 → dimension 7 SKIPPED.

RESEARCH §A.5 and §N.1 substitute for missing CONTEXT.md by providing recommended defaults; plans honor every recommendation (timestamp format `%Y%m%d-%H%M%S`, env-var opt-out, baseline fixture path, `_with_agent_full` threading). No scope reduction, no deferred items leaking into plans.

---

## Final Notes for Executor

1. **Plan 06-04 has the highest risk surface** (4 files × 14 edit sites). Commit after every 2-3 edits if context drifts. The provided diff templates are accurate against current `main.py` (verified line 84 compare branch, line 100 single, line 119 compare-built-in, line 138 single-built-in match the actual code).
2. **Plan 06-04 Task 1 Step 4** (`output.py` format_json filter) is the load-bearing 1-line change for regression preservation. If you forget it, regression PASS drops to 7/8 because `_with_agent_full` leaks into compare-mode JSON.
3. **Plan 06-00 Task 2 `tests/__init__.py`** — empirically empty in current repo; "if exists APPEND" path is correct.
4. **Plan 06-01 Task 1** simulator edit position is critical: increment `abstain_phase_stats[dev.phase]` BEFORE `dev.status='DOWN'` (so `dev.phase` is the decision-time phase 1..F-1, not -1). The plan explicitly highlights this; respect the order.
5. **Plan 06-05 Task 1** SPHSIM_NO_REPORT injection is what makes regression NOT pollute `./reports/`. The CI deserves the cleanup belt-and-suspenders from Section 1's check #2.
6. **Plan 06-04 Task 3 (human-verify checkpoint)** — open report.md in 3 renderers; visual PNG fidelity in Polish glyphs is the only thing automation cannot prove.

---

## PLAN CHECK: PASS WITH NOTES

Plans are execution-ready. Proceed with `/gsd:execute-phase 6`. Carry the 9 WARNINGs above into executor's awareness; none of them prevent goal achievement.

**Expected outcome after full execution:**
- 6 new files (`sphsim/report/{__init__,markdown,plots}.py`, `tests/{conftest,test_report,test_plots,test_simulator_abstain}.py`, `scripts/verify_phase6.sh`)
- 4 modified production files (`sphsim/core/{device,simulator}.py`, `sphsim/cli/{main,repl,output}.py` — counting output.py)
- 2 modified scripts (`scripts/regression_check.py`, `.gitignore`)
- 1 modified `tests/__init__.py`
- 14 new tests in test_report (5+2+3+2+2), 6 in test_plots (4+2), 3 in test_simulator_abstain
- `verify_phase6.sh` PASS=36 / FAIL=0
- `regression_check.py` PASS=8/8 preserved with zero `./reports/` pollution

