---
phase: 06-report-plots-generator
verified: 2026-05-28T00:00:00Z
status: ready-for-verify
score: pending /gsd:verify-work (Plan 05 self-attestation)
overrides_applied: 0
re_verification: false
---

# Phase 6: Report + Plots Generator — Verification Handoff

**Phase Goal:** Każde uruchomienie symulacji produkuje katalog `./reports/<ts>/` z `report.md` (sześć sekcji w polskim Markdown, tabela KPI z baseline) + dwa wykresy PNG (decision_distribution.png + kpi_timeseries.png), bez nowych flag CLI — defaultowo zawsze, z opt-out `SPHSIM_NO_REPORT=1`, bez naruszania v1.0 regression baseline.
**Plan 05 Self-Attestation:** 2026-05-28
**Status:** READY FOR /gsd:verify-work
**Re-verification:** No — initial verification

---

## Executive Summary

Phase 6 fully delivers all 6 ROADMAP Success Criteria. Plan 05's exit gate (`scripts/verify_phase6.sh`) runs end-to-end with **PASS=40 / FAIL=0**, including all six SCs, full test suite (172 tests, 0 skipped), v1.0 regression baseline (PASS 8/8), REPL Pitfalls 2 and 6 defusion, and SPHSIM_NO_REPORT=1 opt-out coverage. The `scripts/regression_check.py` now passes `env={**os.environ, 'SPHSIM_NO_REPORT': '1'}` into every subprocess, eliminating the 24-file `./reports/` pollution that 8 baseline runs would otherwise create. The 9-entry SKIP_KEYS tuple (Phase 4 ×3 + Phase 5 ×5 + Phase 6 ×1 `abstain_per_phase`) and rationale comment are in canonical 3-paragraph form. After the full gate runs, the project root is clean (no leftover `./reports/`).

This document is the Plan 05 self-attestation handoff; final adjudication is owned by `/gsd:verify-work`.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Every `python3 sph_sim.py ...` (no flags) creates `./reports/<ts>/` with exactly 3 files (report.md + 2 PNG) | VERIFIED | verify_phase6.sh §3 SC#1 — 4 checks all PASS; live: ./reports/<ts>/ contains [report.md, decision_distribution.png, kpi_timeseries.png] |
| 2 | report.md contains 6 H2 sections + 5 KPI rows + baseline disclaimer + Strategia row + Konfiguracja header | VERIFIED | verify_phase6.sh §4 SC#2 — 5 checks all PASS; grep counts: H2≥6 (6 actual), KPI≥5 (10 actual incl. baseline comparison rows), baseline path present, Strategia row present, Konfiguracja header present |
| 3 | Both PNGs (decision_distribution + kpi_timeseries) are valid PNG-89 with realistic file size | VERIFIED | verify_phase6.sh §5 SC#3 — 4 checks all PASS; PNG signature `\x89PNG\r\n\x1a\n` verified on both files; decision_distribution.png > 5 KB; kpi_timeseries.png > 10 KB |
| 4 | report.md links PNGs via relative paths only (`![alt](file.png)`), no absolute paths, no http:// links | VERIFIED | verify_phase6.sh §6 SC#4 — 4 checks all PASS; positive greps for both relative links + negative greps for `]\(/` (abs) and `]\(http` (network) |
| 5 | `--compare-agent` mode adds a `## Porównanie z RationalAgent` section with delta KPI table + werdykt line | VERIFIED | verify_phase6.sh §7 SC#5 — 5 checks all PASS; compare-mode produces non-empty report.md with section 7 header, `with-agent | bez agenta` table header, `**Werdykt:**` line, and non-tiny kpi_timeseries.png (>10 KB threaded with_agent history) |
| 6 | `--json` stdout remains pure JSON (v1.0 compat); banner goes to stderr; abstain_per_phase present in metrics; _with_agent_full stripped from JSON output | VERIFIED | verify_phase6.sh §8 SC#6 — 4 checks all PASS; `json.loads(stdout)` succeeds with `SPHSIM_NO_REPORT=''`; `Raport zapisany do:` only on stderr; abstain_per_phase keys ['1','2','3','4'] present; `_with_agent_full` NOT in compare JSON top-level |

**Score:** 6/6 truths verified — Phase 6 goal achieved.

---

## Per-SC Verdict Table

| SC | REQ | Description | Verdict | Evidence |
|----|-----|-------------|---------|---------|
| SC-1 | REPORT-01 | Każde uruchomienie tworzy `./reports/<ts>/` z 3 plikami (report.md + 2 PNG); brak dodatkowych flag (default on, opt-out via SPHSIM_NO_REPORT=1) | PASS | verify_phase6.sh §3 — 4 checks PASS; `sphsim/report/__init__.py write_report` orchestrator (Plan 04) wires all 5 entry points (main.py × 4 + repl.py × 2) |
| SC-2 | REPORT-02 | report.md zawiera sekcje: konfiguracja, strategia, KPI table, rozkład decyzji, baseline | PASS | verify_phase6.sh §4 — 5 checks PASS; 6 H2 sections actual (≥6 required); 10 KPI rows (5 in KPI table + 5 in baseline comparison); fixture path `08-naive-zeta-0.75-baseline.json` present; `Strategia | \`naive\`` row present; `## Konfiguracja środowiska` header present (preserved from Phase 5 format_config_header) |
| SC-3 | PLOT-01/02 | `decision_distribution.png` + `kpi_timeseries.png` — wykresy renderują się (non-zero PNG) | PASS | verify_phase6.sh §5 — 4 checks PASS; PNG-89 signature `\x89PNG\r\n\x1a\n` on both; size > 5 KB (decision) / > 10 KB (kpi); matplotlib Agg backend (Plan 03) produces real renders |
| SC-4 | PLOT-03 | PNG-i linkowane z `report.md` jako relatywne ścieżki `![](decision_distribution.png)` | PASS | verify_phase6.sh §6 — 4 checks PASS; positive greps for `![Rozkład decyzji per faza](decision_distribution.png)` and `![Przebieg KPI w czasie](kpi_timeseries.png)`; negative greps for `]\(/` and `]\(http` (no abs paths, no network links) |
| SC-5 | REPORT-03 | `--compare-agent` dodaje tabelę delta KPI (with vs without agent) | PASS | verify_phase6.sh §7 — 5 checks PASS; compare-mode preflight creates ./reports/<ts>/; section 7 `## Porównanie z RationalAgent` present; delta table header `\| with-agent \| bez agenta \|` present; `**Werdykt:**` line present; kpi_timeseries.png > 10 KB (with_agent history threading via _with_agent_full private key) |
| SC-6 | (JSON) | `--json` output zachowuje kompatybilność v1.0 (stdout = czysty JSON, banner na stderr) | PASS | verify_phase6.sh §8 — 4 checks PASS; `json.loads(stdout)` succeeds with banner on stderr (Pitfall 3 defused via print(..., file=sys.stderr) in Plan 04 callers); abstain_per_phase keys present in metrics; `_with_agent_full` stripped from JSON via `not k.startswith('_')` filter in format_json |

**Total: 6/6 SCs PASS** — across 26 SC-specific check() invocations within verify_phase6.sh.

---

## Per-Pitfall Defusion Table

| Pitfall | Description | Defusion Status | Code Evidence |
|---------|-------------|----------------|---------------|
| Pitfall 1 | Plot generation blocking (matplotlib Agg backend) — interactive backends would block tests / require display | DEFUSED | `sphsim/report/plots.py` imports `matplotlib` with explicit `matplotlib.use('Agg')` before pyplot; verified by test_plots.py running headless. |
| Pitfall 2 | REPL `fake_args` missing args (D-PH5 from Phase 5) — running REPL `run`/`compare` would crash on AttributeError when accessing config fields | DEFUSED | verify_phase6.sh §9 — 2 checks PASS; `printf 'run naive zeta=0.5\nexit\n' \| python3 sph_sim.py --interactive` outputs Konfiguracja środowiska + PORÓWNANIE without AttributeError. Plan 04 extended `fake_args` in repl.py `do_run` AND `do_compare` to carry all required fields. |
| Pitfall 3 | `--json` stdout pollution (banner) — write_report banner printed to stdout would break JSON parsing | DEFUSED | verify_phase6.sh §8 SC#6 — 4 checks PASS; banner emitted via `print('Raport zapisany do: ...', file=sys.stderr)` by all 5 entry-point callers (main.py × 4 + repl.py × 2 per Plan 04). `json.loads(stdout)` succeeds; grep for banner on stderr (1>/dev/null) succeeds. |
| Pitfall 4 | `./reports/` pollution during regression / tests — 8 baseline runs would create 24 files in project root | DEFUSED | verify_phase6.sh §1 + §10 — 5 checks PASS; `regression_check.py` passes `env={**os.environ, 'SPHSIM_NO_REPORT': '1'}` (Plan 05 Task 1) so subprocesses never call write_report's mkdir branch; tests use `tests/__init__.py` env autoset + per-test tearDown. After full verify run, ./reports/ does NOT exist. |
| Pitfall 5 | SKIP_KEYS contract violation — regression check would fail when new metrics dict keys (abstain_per_phase) appear in actual but not baseline | DEFUSED | `regression_check.py` SKIP_KEYS tuple includes `'abstain_per_phase'` (Plan 01); rationale comment consolidated to 3 canonical paragraphs (Plan 05). Regression PASS 8/8 confirmed live. |
| Pitfall 6 | `_with_agent_full` private key leak — compare-mode return dict carries full res_with for plot threading, but stdout JSON must remain pure v1.0 shape | DEFUSED | `sphsim/cli/output.py format_json` filter `not k.startswith('_')` strips `_with_agent_full` BEFORE serialization (Plan 04); verify_phase6.sh §8 SC#6 check 4 confirms `'_with_agent_full' not in json.load(stdout)` for `--compare-agent --json` invocation. |

**Total: 6/6 pitfalls DEFUSED** with code-level + live-execution evidence.

---

## Required Artifacts

| Artifact | Purpose | Status | Details |
|----------|---------|--------|---------|
| `sphsim/report/__init__.py` | `write_report` orchestrator: mkdir + plot + render + write + opt-out + banner | VERIFIED (Plan 04) | Side-effect orchestrator wraps pure renderers; SPHSIM_NO_REPORT opt-out; exception isolation envelope; 5 entry-point wires |
| `sphsim/report/markdown.py` | `render_report(args, res, params, K1, mode)` — pure-function MD assembler, 6 + optional 7th section | VERIFIED (Plan 02) | Returns string; no side effects; 14 tests in test_report.py |
| `sphsim/report/plots.py` | `plot_decision_distribution` + `plot_kpi_timeseries` — matplotlib Agg PNG generators | VERIFIED (Plan 03) | Pure functions take path arg; backend 'Agg' set at module load; 6 tests in test_plots.py |
| `sphsim/cli/main.py` | 4 entry-point wires (custom-compare, custom-single, built-in-compare, built-in-single) calling write_report + stderr banner | VERIFIED (Plan 04) | Each branch calls write_report and prints `Raport zapisany do: <path>` to stderr |
| `sphsim/cli/repl.py` | 2 entry-point wires (do_run, do_compare) with extended fake_args + write_report call | VERIFIED (Plan 04) | fake_args carries phi/rho/K0/valuation/seed/strategy/zeta; do_compare returns dict with `_with_agent_full` for plot threading |
| `sphsim/cli/output.py` | `format_json` filter extended with `not k.startswith('_')` — strips _with_agent_full from JSON | VERIFIED (Plan 04) | SC#6 stdout cleanliness + regression baseline equality preserved |
| `sphsim/core/simulator.py` | `run()` return dict extended with `abstain_per_phase` (per-phase ABSTAIN counts) | VERIFIED (Plan 01) | Plan 01 added field; test_simulator_abstain.py verifies per-phase counts |
| `scripts/regression_check.py` | SKIP_KEYS includes `abstain_per_phase`; subprocess env={**os.environ, 'SPHSIM_NO_REPORT': '1'} | VERIFIED (Plan 01 + Plan 05) | 9-entry tuple; env passthrough confirmed live (PASS 8/8 + zero pollution) |
| `scripts/verify_phase6.sh` | Phase exit gate with all 6 SCs + regression + tests + REPL + opt-out | VERIFIED (Plan 05) | 39 check() invocations + 1 inline preflight = 40 PASS / 0 FAIL; exits 0 |
| `tests/test_report.py` | Render + write_report + JSON-cleanliness tests (14 tests, 0 skipped) | VERIFIED (Plan 02 + Plan 04) | Includes TestJsonStdoutClean.tearDown that rmtrees ./reports/* (Plan 05 verify reorders around this) |
| `tests/test_plots.py` | PNG render tests (6 tests, Pillow optional) | VERIFIED (Plan 03) | Verifies PNG signature + non-empty output |
| `tests/test_simulator_abstain.py` | abstain_per_phase regression-net (3 tests) | VERIFIED (Plan 01) | Counts ABSTAIN per phase 1-4; replaces v1.0 baseline absence for this field |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `main.py` run_single | `write_report(args, res, params, K1, mode='single')` | direct call | WIRED | Plan 04 — all 4 main.py branches wired |
| `main.py` run_compare | `write_report(args, res_combined, params, K1, mode='compare')` | dict `_with_agent_full` key | WIRED | Compare branch threads full with_agent res via `_with_agent_full` private key |
| `repl.py` do_run | `write_report(fake_args, res, params, K1, mode='single')` | fake_args constructor | WIRED | Plan 04 — fake_args has all required fields (Pitfall 2 defused) |
| `repl.py` do_compare | `write_report(fake_args, res_combined, params, K1, mode='compare')` | fake_args + `_with_agent_full` | WIRED | Pitfall 6 defused — fake_args extension carries strategy/zeta/seed/K0/phi/rho/valuation |
| `output.py format_json` | strips `_*` keys from top-level dict before json.dumps | filter comprehension | WIRED | SC#6 + no-leak both PASS |
| `regression_check.py subprocess.run` | child sees `SPHSIM_NO_REPORT=1` | `env={**os.environ, ...}` | WIRED | Plan 05 — 8 baseline runs produce zero ./reports/ files |
| `verify_phase6.sh check()` | `eval "$cmd" > /tmp/p6_check.log 2>&1` | PASS/FAIL counters | WIRED | 39 check() invocations executed; trap cleans /tmp/p6_* on exit |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `report.md` Strategia row | `args.strategy` | argparse from CLI | Yes — live: `Strategia \| \`naive\`` row present | FLOWING |
| `report.md` Konfiguracja section | format_config_header output from args.phi/rho/K0/seed/valuation | Phase 5 format_config_header reused verbatim | Yes — live: 9-row config table present | FLOWING |
| `report.md` KPI table | `res['metrics']` from SPHSimulator.run() | core simulator | Yes — 5 KPI rows in main table + 5 rows in baseline comparison = 10 grep matches | FLOWING |
| `decision_distribution.png` | `res['decisions_per_phase']` dict counts | core simulator | Yes — matplotlib bar chart with phase 1-4 grouping; PNG > 5 KB | FLOWING |
| `kpi_timeseries.png` (single mode) | `res['history']['val']` + `res['history']['providers']` | core simulator over T steps | Yes — line chart for T=1000 points; PNG > 10 KB | FLOWING |
| `kpi_timeseries.png` (compare mode) | both `res['history']` AND `_with_agent_full['history']` | run_compare threading via private dict key | Yes — overlapping line series for with-agent vs no-agent; PNG > 10 KB confirmed | FLOWING |
| `## Porównanie z RationalAgent` section | `res['comparison']` (with vs without agent KPI deltas) | format_compare in output.py | Yes — table header + 5 delta rows + Werdykt line all present in compare-mode report.md | FLOWING |

No stub data, no hardcoded empty defaults, no placeholder rendering. All values flow from real simulator output.

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Single-mode report creation | `rm -rf ./reports && python3 sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json > /dev/null` | `./reports/<ts>/` contains exactly 3 files | PASS |
| Compare-mode report creation | `rm -rf ./reports && python3 sph_sim.py --strategy naive --zeta 0.5 --compare-agent --seed 42 --json > /dev/null` | report.md includes `## Porównanie z RationalAgent` + delta table + Werdykt | PASS |
| Opt-out (CLI single) | `SPHSIM_NO_REPORT=1 python3 sph_sim.py ... --json > /dev/null` | No ./reports/ created | PASS |
| Opt-out (CLI compare) | `SPHSIM_NO_REPORT=1 python3 sph_sim.py ... --compare-agent --json > /dev/null` | No ./reports/ created | PASS |
| Opt-out (regression) | `SPHSIM_NO_REPORT=1 python3 scripts/regression_check.py` (or default — env passthrough) | PASS 8/8 + no ./reports/ | PASS |
| Banner on stderr only | `python3 sph_sim.py ... --json 2>/dev/null \| python3 -c "import json,sys; json.loads(sys.stdin.read())"` | exit 0 (JSON parses despite banner emission) | PASS |
| Banner on stderr NOT stdout | `python3 sph_sim.py ... --json 2>&1 1>/dev/null \| grep 'Raport zapisany do:'` | match found | PASS |
| _with_agent_full stripped from JSON | `python3 sph_sim.py ... --compare-agent --json \| python3 -c "import json,sys; assert '_with_agent_full' not in json.load(sys.stdin)"` | exit 0 | PASS |
| abstain_per_phase in JSON metrics | `python3 sph_sim.py ... --json \| python3 -c "import json,sys; assert 'abstain_per_phase' in json.load(sys.stdin)['metrics']"` | exit 0 | PASS |
| REPL `run` command | `printf 'run naive zeta=0.5\nexit\n' \| python3 sph_sim.py --interactive` | Output contains `Konfiguracja środowiska`, no AttributeError | PASS |
| REPL `compare` command | `printf 'compare naive zeta=0.5\nexit\n' \| python3 sph_sim.py --interactive` | Output contains `PORÓWNANIE`, no AttributeError | PASS |

---

## Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| `scripts/verify_phase6.sh` | `bash scripts/verify_phase6.sh` | exit 0; PASS=40 / FAIL=0; final line `✓ Phase 6 ready for /gsd:verify-work` | PASS |
| `scripts/regression_check.py` | `python3 scripts/regression_check.py` | `PASS: 8/8`; no ./reports/ pollution | PASS |
| Full test suite | `SPHSIM_NO_REPORT=1 python3 -m unittest discover tests` | `Ran 172 tests` / `OK` | PASS |
| Project-root cleanliness | `{ [ ! -d ./reports ] \|\| [ -z "$(ls -A ./reports)" ]; }` after gate | exit 0 — no pollution | PASS |

---

## Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|---------|
| REPORT-01 | Auto-create ./reports/<ts>/ with report.md + 2 PNG on every run, no flags | SATISFIED | SC#1 4/4 checks PASS; write_report wires at all 5 entry points |
| REPORT-02 | report.md has 6 sections (config, strategia, KPI, rozkład, wykresy, baseline) | SATISFIED | SC#2 5/5 checks PASS; render_report assembles all 6 sections |
| REPORT-03 | --compare-agent adds delta KPI section with werdykt | SATISFIED | SC#5 5/5 checks PASS; compare-mode render_report emits 7th section |
| PLOT-01 | decision_distribution.png renders via matplotlib Agg | SATISFIED | SC#3 2/2 PNG signature + size checks PASS for decision plot |
| PLOT-02 | kpi_timeseries.png renders with T-step history | SATISFIED | SC#3 2/2 PNG signature + size checks PASS for kpi plot |
| PLOT-03 | report.md links PNGs via relative paths only | SATISFIED | SC#4 4/4 checks PASS (2 positive + 2 negative greps) |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | — |

No TBD, FIXME, XXX, placeholder, or stub patterns found in Phase 6 modified files. No `return None`-on-success-paths, no empty handler, no hardcoded empty data observed.

---

## Anti-Regression Invariants

| Invariant | Check | Result |
|-----------|-------|--------|
| v1.0 baseline preserved (CLI-04) | `python3 scripts/regression_check.py` | PASS: 8/8 (with env passthrough — no ./reports/ pollution) |
| Phase 4 rational agent veto unchanged | `python3 -m unittest tests.test_agent` (inside discover) | included in 172/172 OK |
| Phase 5 env config invariants | `python3 -m unittest tests.test_env` (inside discover) | included in 172/172 OK |
| Phase 6 report tests | `python3 -m unittest tests.test_report tests.test_plots tests.test_simulator_abstain` | included in 172/172 OK |
| Polish UX (D-17) preserved | All error messages + section headers verified in Polish | Confirmed: `Konfiguracja środowiska`, `Porównanie z RationalAgent`, `Werdykt`, `Raport zapisany do:`, `Rozkład decyzji per faza`, `Przebieg KPI w czasie` |
| Banner on stderr (Pitfall 3) | grep 'Raport zapisany do:' in stderr only | Confirmed via SC#6 banner check |
| _with_agent_full not leaked (Pitfall 6) | `_with_agent_full` absent from compare JSON top-level | Confirmed via SC#6 no-leak check |
| ./reports/ pollution = 0 | After full gate: `ls -A ./reports/ 2>/dev/null` | empty / no dir |

---

## Human Verification Required

None. All Phase 6 success criteria are programmatically verifiable through:
- file existence + size checks (SC#1, SC#3),
- grep on report.md content (SC#2, SC#4, SC#5),
- PNG signature byte-comparison (SC#3),
- JSON parsing of subprocess stdout (SC#6),
- unit test pass/fail (test suite),
- subprocess regression equality (regression_check.py).

A human-verify checkpoint was completed during Plan 04 (sample report visual inspection); Plan 05 only adds infrastructure layer.

---

## Gaps Summary

No gaps. All 6 ROADMAP Success Criteria are verified with live codebase evidence. All 6 pitfalls identified in 06-RESEARCH.md are confirmed defused with code-level + live-execution evidence. The verify_phase6.sh exit gate runs deterministic (PASS=40 / FAIL=0) on macOS Python 3.14.3 with stdlib + matplotlib; no platform-specific code paths.

---

## Plan-by-Plan Contribution Summary

| Plan | Wave | Contribution | Output |
|------|------|--------------|--------|
| 06-00 | 0 | Scaffolding — empty sphsim/report/ module + verify_phase6.sh skeleton + tests skip stubs | Header + Plan signposts |
| 06-01 | 1 | abstain_per_phase added to simulator.run() return dict; SKIP_KEYS extended | Plan 01 commit f4c08f7 |
| 06-02 | 2 | render_report pure-function MD assembler (6 sections + optional 7th) | Plan 02 commit (markdown.py created) |
| 06-03 | 3 | plot_decision_distribution + plot_kpi_timeseries matplotlib Agg generators | Plan 03 commit (plots.py created) |
| 06-04 | 3 | write_report orchestrator + 5 entry-point wires + banner-on-stderr + opt-out + _with_agent_full strip | Plan 04 commits (Wave 3) |
| 06-05 | 4 | regression_check.py env passthrough + verify_phase6.sh full check coverage | Plan 05 commits 581ecb8 + 58cdf1b |

All 5 plans landed; all artifacts committed; phase exit gate green.

---

_Plan 05 self-attestation: 2026-05-28_
_Attestor: Claude executor (worktree-agent-a11bce7a)_
_Final adjudication: /gsd:verify-work_
