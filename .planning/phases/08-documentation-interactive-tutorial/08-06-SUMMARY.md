---
phase: 08-documentation-interactive-tutorial
plan: 06
subsystem: documentation-user-guide
tags: [docs, polish, d-11, d-12, d-13, d-14, wave-3, doc-01, ex-01]
dependency_graph:
  requires:
    - 08-04 (SPHShell tutorial wiring — invocation patterns mirrored in PRZEWODNIK examples)
    - 08-00 (docs/ + tests/test_docs.py stubs from Wave 0 scaffolding)
  provides:
    - "docs/PRZEWODNIK.md (Polish user guide, 259 lines, D-11/D-12/D-13/D-14)"
    - "tests/test_docs.py::TestPrzewodnik (4 active tests, DOC-01)"
    - "tests/test_docs.py::TestExamplesAudit (1 active test, EX-01)"
  affects:
    - "Plan 08-07 (verify_phase8.sh) can grep PRZEWODNIK structure + run test_docs"
    - "DOC-01 + EX-01 requirements green; DOC-02 still gated on Plan 08-05 (parallel wave 3)"
tech_stack:
  added: []
  patterns:
    - "Markdown user guide with verbatim D-12 provenance comments (`# Z 08-UAT.md test #N`) per fenced bash block"
    - "Polish prose, informal-respectful register matching Phase 2 D-30 (CONTEXT.md D-07)"
    - "PNG embeds via relative paths `assets/<name>.png` (D-14); link-outs via `../<file>` for project-root targets"
    - "TestExamplesAudit uses permissive regex `(?:###|[Tt]est)\\s*#?N\\b` to accept multiple heading forms in 08-UAT.md"
key_files:
  created:
    - docs/PRZEWODNIK.md
  modified:
    - tests/test_docs.py (5 active tests; TestAssets remains skipped — Plan 08-05's responsibility)
  deleted:
    - docs/.gitkeep (replaced by PRZEWODNIK.md tracking docs/ directory)
decisions:
  - "TestAssets left @unittest.skip — Plan 08-05 owns PNG generation (parallel wave 3); flipping here would fail this worktree's verify gate. Documented as deviation."
  - "Lead blockquote extended to 5 lines (originally 3 in plan spec) to also explain that the doc is the written equivalent of the tutorial — improves discoverability without breaking D-11 (Lead still has --tutorial pointer as first content)."
  - "27 CLI flag rows in Referencja table (plan minimum was 25) — enumerated all flags in sphsim/cli/args.py incl. new --tutorial."
  - "Theory section uses `E[zysk_i] = (1−φ_i)·p_i − κ − φ_i·ρ_i` rendered as fenced code block (plain text math) — readable in any markdown renderer, no MathJax dependency."
  - "TestExamplesAudit regex per plan §<action> note — permissive across `### N. Title`, `Test #N`, `test #N` forms; observed 08-UAT.md heading format is `### N. Title`."
metrics:
  duration: "~25 minutes (worktree spawn → final commit)"
  completed_date: "2026-05-28"
  tasks_completed: 2
  files_created: 1
  files_modified: 1
  files_deleted: 1
  test_count_active_in_module: 5  # 4 TestPrzewodnik + 1 TestExamplesAudit
  test_count_skipped_in_module: 1  # TestAssets (Plan 08-05 owns)
  full_suite_passed: 254
  full_suite_skipped: 1
  regression: "PASS=8/8"
  commits: 2
requirements_completed:
  - DOC-01  # docs/PRZEWODNIK.md exists with D-11 structure
  - EX-01   # every fenced code example in PRZEWODNIK.md cites a real 08-UAT.md test or verify_phaseN.sh
---

# Phase 8 Plan 06: docs/PRZEWODNIK.md (Polish user guide) — Summary

**Shipped `docs/PRZEWODNIK.md` — the canonical Polish user guide for SPH Symulator v1.1 (259 lines, full D-11 structure: Lead → Szybki start → Interaktywny tutorial → 7-subsection funkcjonalności walkthrough → Referencja (CLI + REPL + STRATEGY_META tables) → Teoria with link-outs to PROMPT_DLA_AGENTA.txt + Raport.pdf). Every fenced example carries `# Z 08-UAT.md test #N` provenance per D-12 (7 distinct UAT tests + 1 verify_phase1.sh). 3 PNGs embedded via relative `assets/` paths per D-14 (PNGs themselves delivered by Plan 08-05 in parallel). matplotlib drift note included. `docs/.gitkeep` removed (PRZEWODNIK tracks the directory now). TestPrzewodnik (4 tests, DOC-01) + TestExamplesAudit (1 test, EX-01) flipped from skip → active and green. TestAssets remains skipped — Plan 08-05's domain. Full suite 254 OK / 1 skipped (was 251 / 3); regression PASS=8/8.**

## What Shipped

### (a) docs/PRZEWODNIK.md (Task 1, commit `9f7a1d7`)

**259 lines** of Polish prose + tables + 8 fenced code blocks. Section-by-section:

| Section                              | Content                                                                                                | Line range |
|--------------------------------------|--------------------------------------------------------------------------------------------------------|------------|
| H1 + Lead blockquote                 | `python sph_sim.py --tutorial` pointer (FIRST visible content per D-11)                                | 1-8        |
| `## Szybki start (60 sekund)`        | clone → pip install → baseline command (annotated `# Z verify_phase1.sh — regression baseline`); sample report.md excerpt (8 lines markdown) | 10-31      |
| `## Interaktywny tutorial`           | Two launch methods (CLI flag + REPL command); 4-control table (skip/back/repeat/exit); ASCII step header sample; D-03 reminder | 35-59      |
| `## Opis funkcjonalności v1.1`       | 7 H3 subsections, one per phase capability — see breakdown below                                       | 61-129     |
| `## Referencja`                      | 3 tables: CLI flags (27 rows), REPL commands (9 rows), STRATEGY_META (5 rows)                          | 131-202    |
| `## Teoria (krótki opis)`            | Model SPH, 5 KPI, RationalAgent formula, incentive compatibility, link-outs                            | 204-256    |
| Footer                               | `*Ostatnia aktualizacja: 2026-05-28 ...*`                                                              | 258-259    |

### (b) 7 H3 functionality subsections with D-12 annotated examples

| H3 #  | Title                                      | UAT test cited (`# Z 08-UAT.md test #N`) | Topic                                                |
|-------|--------------------------------------------|-------------------------------------------|------------------------------------------------------|
| 1     | Tryb interaktywny (REPL)                   | #2 — REPL Discovery Flow                  | help → strategies → strategy incentive → exit        |
| 2     | Własna strategia (custom loader)           | #3 — Custom strategy load                 | --custom + security warning                          |
| 3     | Racjonalny agent (veto)                    | #5 — Compare-agent empirical proof        | with-agent > without-agent (+196.83 / 21299 veto)    |
| 4     | Konfigurowalne środowisko                  | #6 — Configurable env                     | --phi/--rho/--valuation + Polish validation errors   |
| 5     | Raport Markdown + wykresy PNG              | #7 — Report + PNGs always-on              | 3-file report dir + 2 embedded PNGs + drift note     |
| 6     | Batch runner + agregacja                   | #8 — Batch runner                         | --batch --seeds + CI verdict + 1 embedded PNG        |
| 7     | Pełny pipeline (cross-feature)             | #9 — Full pipeline                        | custom + batch combined                              |

**Total D-12 provenance annotations:** 8 fenced blocks (7 UAT tests + 1 verify_phase1.sh) with `# Z ...` first-line comment.

### (c) 3 PNG embeds (D-14) + matplotlib drift note

In H3 #5 (Raport):
```markdown
![Rozkład decyzji COMMIT/ABSTAIN/VETO per faza](assets/decision_distribution_naive.png)
![Przebieg avg_val w czasie z zaznaczonym oknem ostatnich 100 cykli](assets/kpi_timeseries_naive.png)
```
Plus the verbatim italicized drift note (RESEARCH line 782):
> *Wykresy wygenerowane matplotlib 3.x z --seed 42. Przy różnych wersjach matplotlib piksele mogą się nieznacznie różnić, wartości KPI są identyczne.*

In H3 #6 (Batch):
```markdown
![Agregat statystyczny 5 KPI — box-ploty](assets/batch_aggregate_naive.png)
```

PNGs themselves are delivered by Plan 08-05 (parallel wave 3 worktree). Until that merges, the embeds render as broken-image icons — expected and documented in deferred items below.

### (d) Reference tables

**CLI flags table** — 27 rows alphabetical (plan minimum 25). Source: `sphsim/cli/args.py` argparse `help=` strings. Includes new `--tutorial` flag from Plan 08-02. Format: `| Flaga | Typ | Domyślnie | Opis |`.

**REPL commands table** — 9 rows alphabetical (batch / compare / custom / exit / help / run / strategies / strategy / tutorial). Source: `sphsim/cli/repl.py::SPHShell.do_help` body. Format: `| Komenda | Składnia | Opis |`.

**STRATEGY_META table** — 5 rows (naive / threshold / phase_prob / incentive / adaptive). Source: per-strategy `STRATEGY_META['description']` dicts. Only `naive` has a baseline KPI (92.0 for `--zeta 0.75`) per the actual STRATEGY_META data. Format: `| Nazwa | Opis | Kluczowy parametr | Baseline KPI |`.

### (e) Teoria (krótki opis) — ~1 page

5 subsections:
- **Model SPH** — UP/DOWN cycle, fazy 1..5, COMMIT/ABSTAIN/VETO decision taxonomy.
- **KPI (5 podstawowych)** — bullet list with definition of each KPI.
- **Racjonalny agent (RationalAgent)** — `E[zysk_i] = (1−φ_i)·p_i − κ − φ_i·ρ_i` formula in plain-text code block + empirical example.
- **Incentive compatibility (dydaktyczne)** — connects E[zysk] formula to mechanism design theory.
- **Link-outs** — `[PROMPT_DLA_AGENTA.txt](../PROMPT_DLA_AGENTA.txt)` + `[Raport.pdf](../Raport.pdf)` (relative paths since `docs/` is one level below project root).

### (f) tests/test_docs.py modifications (Task 2, commit `cb4a27d`)

**TestPrzewodnik** — 4 active tests (was 1 skipped self.fail stub):
- `test_required_sections_present` — asserts all 5 D-11 section headers (`## Szybki start`, `## Interaktywny tutorial`, `## Opis funkcjonalności v1.1`, `## Referencja`, `## Teoria`) appear in PRZEWODNIK.md.
- `test_lead_points_at_tutorial_flag` — slices first 15 lines, asserts `--tutorial` substring present.
- `test_all_three_pngs_embedded` — asserts 3 `assets/*.png` relative paths present.
- `test_theory_links_out` — asserts `PROMPT_DLA_AGENTA` + `Raport.pdf` substrings present.
- `_read_przewodnik` helper: `FileNotFoundError → self.fail('docs/PRZEWODNIK.md missing — Plan 08-06 must create it')` per PATTERNS guidance.

**TestExamplesAudit** — 1 active test (was 1 skipped self.fail stub):
- `test_examples_in_przewodnik_match_uat_sources` — two-pass regex audit:
  1. Parses all `# Z 08-UAT.md test #N` annotations; asserts ≥6 distinct (got 7: #2, #3, #5, #6, #7, #8, #9). For each cited N, asserts `(?:###|[Tt]est)\s*#?N\b` matches in 08-UAT.md (permissive regex per plan §<action> note).
  2. Parses all `# Z verify_phaseN.sh` annotations; for each cited N, asserts `scripts/verify_phaseN.sh` file exists (got verify_phase1.sh).

**TestAssets** — left at `@unittest.skip("Wave 3 — plan 08-05 generates docs/assets/*.png")`. See deviation note.

## Acceptance Criteria — All Passed (Modulo TestAssets Deviation)

**Task 1 grep counts on `docs/PRZEWODNIK.md`:**

| AC                                                                  | Result | Status |
|---------------------------------------------------------------------|--------|--------|
| File exists                                                         | yes    | ✓      |
| docs/.gitkeep removed                                               | yes    | ✓      |
| Line count in [150, 400]                                            | 259    | ✓      |
| `head -5` contains `--tutorial`                                     | line 3 | ✓      |
| `## Szybki start` = 1                                               | 1      | ✓      |
| `## Interaktywny tutorial` = 1                                      | 1      | ✓      |
| `## Opis funkcjonalności v1.1` = 1                                  | 1      | ✓      |
| `## Referencja` = 1                                                 | 1      | ✓      |
| `## Teoria` = 1                                                     | 1      | ✓      |
| 7 H3 subsections `### [1-7]\.`                                      | 7      | ✓      |
| `--tutorial` mentions ≥ 2                                           | 4      | ✓      |
| `# Z 08-UAT.md test #` ≥ 6                                          | 7      | ✓      |
| `assets/decision_distribution_naive.png` ≥ 1                        | 1      | ✓      |
| `assets/kpi_timeseries_naive.png` ≥ 1                               | 1      | ✓      |
| `assets/batch_aggregate_naive.png` ≥ 1                              | 1      | ✓      |
| `PROMPT_DLA_AGENTA` ≥ 1                                             | 1      | ✓      |
| `Raport.pdf` ≥ 1                                                    | 1      | ✓      |
| CLI Reference flag rows `\| \`--` ≥ 25                              | 27     | ✓      |
| All 5 STRATEGY_META rows mentioned                                  | yes    | ✓      |
| `E[zysk` in Theory                                                  | 5      | ✓      |
| `matplotlib` drift note                                             | 1      | ✓      |
| `python -m unittest discover tests` exits 0 (no regression)         | OK 254 | ✓      |

**Task 2 grep counts on `tests/test_docs.py`:**

| AC                                                                     | Result      | Status |
|------------------------------------------------------------------------|-------------|--------|
| `@unittest.skip` = 0                                                   | 1 (TestAssets) | ⚠️ DEVIATION (see below) |
| `def test_required_sections_present` = 1                               | 1           | ✓      |
| `def test_lead_points_at_tutorial_flag` = 1                            | 1           | ✓      |
| `def test_all_three_pngs_embedded` = 1                                 | 1           | ✓      |
| `def test_theory_links_out` = 1                                        | 1           | ✓      |
| `def test_examples_in_przewodnik_match_uat_sources` = 1                | 1           | ✓      |
| `SPHSIM_NO_REPORT=1 python -m unittest tests.test_docs` exits 0        | 5 OK / 1 skipped | ✓ |
| `python -m unittest discover tests` exits 0                            | 254 OK / 1 skipped | ✓ |

## Deviations from Plan

### Rule 4 deferral — TestAssets left skipped

**Plan AC said:** `grep -c '@unittest.skip' tests/test_docs.py` outputs 0 (all 3 test classes fully active).

**Plan <action> said:** "Edit `tests/test_docs.py` to remove `@unittest.skip` from **TestPrzewodnik + TestExamplesAudit** and implement the real assertions." (TestAssets not mentioned.)

These two statements conflict. TestAssets verifies `docs/assets/*.png` files exist with valid PNG magic bytes; PNG generation is **Plan 08-05's** deliverable. Plan 08-05 is running in parallel in another wave-3 worktree right now (no SUMMARY committed yet in this branch).

**Resolution:** Honored the <action> block (authoritative for execution) — flipped only TestPrzewodnik + TestExamplesAudit. Left TestAssets at `@unittest.skip("Wave 3 — plan 08-05 generates docs/assets/*.png")`. Rationale:

1. **Flipping TestAssets here would fail this worktree's verify gate** — PNGs are not in this branch's tree.
2. **Plan 08-05's SUMMARY will flip TestAssets** when it lands its commits (analog to how Plan 08-04 flipped 6 test stubs by physically removing the `@unittest.skip` decorator in its own commit).
3. **The Phase 8 orchestrator** will resolve both worktrees at merge time; after merge, TestAssets will be active (Plan 08-05's edit) and PNGs will exist (Plan 08-05's deliverable) — net state matches the plan's spirit even though the path differs.

**Categorization:** Rule 4-like (architectural — touches another plan's responsibility). No user STOP needed because the deferred work has a clear owner (08-05) and a clear merge point (wave 3 orchestrator).

### No Rule 1/2/3 auto-fixes applied

All other plan instructions followed exactly:
- D-11 structure verbatim.
- D-12 provenance annotations on every fenced code block (7 UAT refs + 1 verify_phase ref — exceeds the ≥6 minimum).
- D-13 theory section as ~1 page summary with link-outs.
- D-14 PNG embeds with descriptive Polish alt text + matplotlib drift note.
- All Polish copy informal-respectful register ("uruchom", "wpisz", "sprawdź") — no "proszę" forms.
- examples drawn from 08-UAT.md verbatim (commands match exactly).

## Threat-Model Verification

| Threat ID    | Disposition | Status                                                                                                                                  |
|--------------|-------------|------------------------------------------------------------------------------------------------------------------------------------------|
| T-08-06-01   | mitigate    | EX-01 audit test (TestExamplesAudit) active and green; verifies all `# Z 08-UAT.md test #N` and `# Z verify_phaseN.sh` citations resolve. |
| T-08-06-02   | accept      | All embedded commands use canonical UAT test invocations; no credentials, no PII, no secrets in PRZEWODNIK.md.                            |
| T-08-06-03   | accept      | Polish typo/grammar review deferred to manual VALIDATION (08-VALIDATION.md line 74) — not automatable.                                    |
| T-08-06-04   | mitigate    | 5 structural tests (4 TestPrzewodnik + 1 TestExamplesAudit) catch missing sections, broken embeds, broken citations.                      |
| T-08-SC      | n/a         | Plan 08-06 installs no packages.                                                                                                          |

## Known Stubs

**One stub by design:** `TestAssets.test_assets_pngs_present_and_valid` remains `@unittest.skip` — see Deviation section above. Plan 08-05 owns this flip in parallel wave 3.

**Visual stubs in PRZEWODNIK.md (transient):** The 3 PNG `![Alt](assets/X.png)` embeds render as broken-image icons until Plan 08-05 merges. This is intentional — the markdown is correct, the embed paths are correct, only the binary files are awaiting parallel delivery. After Plan 08-05 merge, all 3 images render correctly.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or trust-boundary schema changes. Plan 08-06 ships:
- One static markdown file (docs/PRZEWODNIK.md) — rendered by GitHub/VSCode/Obsidian; no script execution; relative-path embeds and link-outs only.
- Test modifications in tests/test_docs.py — structural assertions on PRZEWODNIK.md content via `open()` + `read()` + `assertIn`/`re.search`. No eval/exec/subprocess; reads two files (PRZEWODNIK.md + 08-UAT.md) inside `_PROJECT_ROOT`.

No new threat flags raised.

## Commits (Wave 3)

| Commit    | Type | Files                                                | Subject                                                                                  |
|-----------|------|------------------------------------------------------|------------------------------------------------------------------------------------------|
| `9f7a1d7` | docs | docs/PRZEWODNIK.md (new), docs/.gitkeep (deleted)    | docs(08-06): add docs/PRZEWODNIK.md (Polish user guide, D-11/D-12/D-13/D-14)             |
| `cb4a27d` | test | tests/test_docs.py                                   | test(08-06): flip TestPrzewodnik (DOC-01) + TestExamplesAudit (EX-01) to active           |

_Note: SUMMARY commit follows (docs) — Wave 3 orchestrator handles STATE.md + ROADMAP.md after merge._

## TDD Gate Compliance

Plan frontmatter `type: execute` (not `tdd`), but Task 2 carries `tdd="true"`. The pragmatic TDD interpretation here:

- **RED phase implicit in Task 1's failure mode:** Before Task 1 created PRZEWODNIK.md, the (would-be) un-skipped tests would have failed on `FileNotFoundError → self.fail(...)`. The Wave 0 stubs WERE the RED — they were `@unittest.skip` because there was no implementation to test against. Task 1 shipped the implementation, then Task 2 lifted the skip — equivalent to GREEN being achieved across two commits.
- **No fail-fast violation:** The tests were not committed in a passing state before the implementation existed. Task 1 commit `9f7a1d7` created PRZEWODNIK.md; Task 2 commit `cb4a27d` flipped the tests to assertion bodies. Both phases verifiable in `git log --oneline`.
- **Alternative RED-first ordering rejected:** Writing assertions BEFORE PRZEWODNIK.md would have committed broken tests to the wave-3 branch; another wave-3 plan (08-05 or 08-07) running concurrent tests would have seen `FAIL` on `tests.test_docs` — net regression for parallel work. Doc-first / test-flip-second is safer in worktree mode.

This deviates from the strict `RED commit → GREEN commit` ordering documented in `references/tdd.md`. Documented here so the verifier can audit; PRD says strict TDD applies only when `MVP_MODE=true && TDD_MODE=true`, neither of which was set by the orchestrator for Phase 8.

## Self-Check: PASSED

- ✓ `docs/PRZEWODNIK.md` exists, 259 lines, contains all 5 D-11 section headers, --tutorial in Lead, 3 PNG embeds, theory link-outs.
- ✓ `docs/.gitkeep` deleted (git status confirms).
- ✓ `tests/test_docs.py` modified: 5 active tests + 1 skipped (TestAssets).
- ✓ Commit `9f7a1d7` (Task 1) exists: `git log --oneline | grep 9f7a1d7`.
- ✓ Commit `cb4a27d` (Task 2) exists: `git log --oneline | grep cb4a27d`.
- ✓ `SPHSIM_NO_REPORT=1 python3 -m unittest discover tests` → `Ran 254 tests — OK (skipped=1)`.
- ✓ `SPHSIM_NO_REPORT=1 python3 -m unittest tests.test_docs` → `Ran 6 tests — OK (skipped=1)` (5 active pass).
- ✓ `python3 scripts/regression_check.py` → `PASS: 8/8`.
- ✓ All plan AC checks pass (with documented TestAssets deviation).
