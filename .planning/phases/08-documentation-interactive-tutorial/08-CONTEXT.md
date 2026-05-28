# Phase 8: Documentation + Interactive Tutorial - Context

**Gathered:** 2026-05-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 delivers two artefacts that lower the barrier-to-entry for a new user (student/instructor) to v1.1:

1. **`docs/PRZEWODNIK.md`** — single Polish written guide (hybrid: tutorial-pointer → quickstart → walkthrough → CLI/REPL reference → short theory appendix), with embedded canonical PNGs and sample `report.md` excerpts under `docs/assets/`.
2. **REPL `tutorial` mode** + **`--tutorial` CLI flag** — guided, hands-on, in-REPL walkthrough of v1.1 capabilities (strategies → custom → agent → env → report → batch), curated to ~8–10 steps, ≤15 minutes total.

**Out of scope** (deliberate, redirected during discussion):
- External paste-back script in separate terminal (`x_notes.txt` alternative — explicitly rejected in favor of REPL mode per ROADMAP).
- Non-interactive scripted demo via `--tutorial` (rejected — contradicts the hands-on design).
- Cross-session tutorial progress persistence (e.g., `~/.sphsim_tutorial_progress`) — overkill for a 15-min flow.
- Theory deep-dive (SPH-STP derivation, φ/ρ math) in PRZEWODNIK.md — leave that to `PROMPT_DLA_AGENTA.txt` + `Raport.pdf`.
- Adding new REQ-IDs — phase satisfies the ROADMAP goal verbatim; REQ traceability already at 27/27 from prior phases.

</domain>

<decisions>
## Implementation Decisions

### Tutorial form factor & invocation

- **D-01 (form factor):** REPL `tutorial` command inside the existing `cmd.Cmd` SPHShell (Phase 2) — NOT an external paste-back script. Resolves the ROADMAP-vs-`x_notes.txt` conflict in favor of the ROADMAP. Rationale: one-window UX, leverages existing infra (history, prompt, dispatch), and avoids two-terminal cognitive load.
- **D-02 (CLI parity):** `python sph_sim.py --tutorial` enters the REPL already in tutorial mode (semantically `--interactive` + auto-`tutorial`). Mutually exclusive with `--strategy`/`--custom`/`--batch`/`--compare-agent` in `sphsim/cli/args.py` (4-way-plus mutex extension). Implementation note: reuses `run_repl()` entry from Phase 2; tutorial mode is a state flag on `SPHShell`.

### Tutorial step UX & control flow

- **D-03 (execution model):** User TYPES each command themselves at the `sph>` prompt — tutorial does NOT auto-execute. Tutorial prints the task description + the exact command to type, then waits. This preserves the hands-on spirit of `x_notes.txt` ("user wykonuje zadania") inside the REPL.
- **D-04 (detection — UAT-style verification):** After the user runs the command, tutorial verifies completion by (a) matching expected command shape (forgiving — accepts equivalent variants, e.g., `batch <strategy> --seeds <N≥3>` for the batch step), and (b) inspecting the simulation result (KPI in expected range, report directory created, exit status). On success print Polish `✓ zaliczone — krok N/M` and advance.
- **D-05 (controls):** Tutorial-internal commands available alongside the normal sph> prompt during tutorial: `skip` (next step, no verification), `back` (previous step — safe because state persists, see D-08), `repeat` (re-show current step task), `exit` (leave tutorial, drop back to bare REPL keeping all loaded state). Each step shows progress header `[krok N/M — <topic>]`.
- **D-06 (no cross-session resume):** Tutorial state is in-memory only. Re-entering `tutorial` after `exit` starts from step 1. No `~/.sphsim_tutorial_progress` file. Rationale: 15-min flow doesn't justify the persistence complexity (corrupt-state edge cases, version mismatch, etc.).
- **D-07 (Claude's Discretion — wrong-input handling):** Not explicitly decided. Planner/executor should choose a sensible policy (e.g., on shape mismatch, print a hint pointing back to the displayed command; after N hints, allow `skip` but don't force it). Should not silently auto-advance.
- **D-08 (REPL state persists across tutorial steps):** Each step builds on the cumulative SPHShell state. Custom strategy loaded in step 4 is still in `STRATEGIES` for step 5 and beyond. After `exit` mid-tutorial, the REPL session continues with everything still loaded. Matches the natural REPL mental model and lets users naturally extend exploration without re-loading.

### Tutorial content scope

- **D-09 (curated golden path — ~8 steps, ≤15 min):** Tutorial mirrors the v1.1 phase progression so each step hits one REQ-ID category once. Initial step layout (planner refines as needed):
  1. Baseline anchor: `naive --zeta 0.75` → KPI=92 (verifies CLI-04 + sanity-check setup).
  2. Browse strategies: `strategies`, then `strategy incentive` (STRAT-01/02).
  3. Run a different built-in strategy (STRAT-02 → simulation invocation).
  4. Load custom: `custom examples/custom_strategy_template.py` (STRAT-03/05).
  5. Rational agent veto: `compare incentive` → user sees with-agent vs without-agent delta KPI (AGENT-01..05).
  6. Override env: `--phi`/`--rho` or `--valuation step` demonstrating ENV-01/02/03.
  7. Open / inspect the generated `report.md` + PNGs (REPORT-01..03, PLOT-01..03).
  8. Batch run: `batch naive --seeds 5` and inspect aggregate (BATCH-01..03, PLOT-04).
- **D-10 (tutorial side effects):** Tutorial uses a dedicated parent dir for reports: `./reports/tutorial-<timestamp>/step-N-<topic>/`. Requires `write_report()` to accept an optional base-dir override (small wiring change, kept backwards-compatible — default behavior unchanged for non-tutorial invocations). Rationale: user gets ONE clean dir per tutorial session — easy to inspect / delete — without polluting the normal `./reports/` timestamped namespace.

### PRZEWODNIK.md structure

- **D-11 (overall shape):** Hybrid layout, with first lines pointing at the REPL tutorial:
  1. **Lead** (literally first lines): "Najszybszy sposób żeby zacząć — uruchom `python sph_sim.py --tutorial` i przejdź interaktywnie przez wszystkie zdolności v1.1."
  2. **Quickstart** (~60s): clone → `pip install -r requirements.txt` → baseline command → expected output snippet.
  3. **Walkthrough** mirroring the 7 v1.1 phases (interactive shell → custom strategies → rational agent → configurable env → reports/plots → batch). One narrative section per phase.
  4. **Reference**: alphabetical CLI flag table, REPL command table, STRATEGY_META summary table for 5 builtins.
  5. **Theory appendix** (short): SPH cycle (UP/DOWN, fazy 1..5, COMMIT/ABSTAIN), what `RationalAgent` does and WHY (E[zysk]<0 → ABSTAIN as dydaktyczny dowód incentive compatibility), links out to `PROMPT_DLA_AGENTA.txt` and `Raport.pdf` for full math.
- **D-12 (example sourcing — single source of truth):** All command examples in PRZEWODNIK.md are pulled VERBATIM from existing verified scenarios — `.planning/phases/07.1-comprehensive-uat/08-UAT.md` (10 cross-phase tests, all passing) and `scripts/verify_phase*.sh` (the 6 phase exit gates already shipped). Rationale: matches `x_notes.txt` "inspiruj się istniejącymi testami UAT", users can paste any example and it will work, drift detected by the existing CI gates.
- **D-13 (theory depth — short appendix only):** ~1 page summary in PRZEWODNIK.md; deep math stays in `PROMPT_DLA_AGENTA.txt` and `Raport.pdf`. Avoids duplication and keeps the guide operational.
- **D-14 (expected outputs embedded):** PRZEWODNIK.md embeds canonical PNGs + sample `report.md` excerpts so users see what success looks like before running. Committed under `docs/assets/`:
  - `docs/assets/decision_distribution_naive.png` (from `naive --zeta 0.75 --seed 42`)
  - `docs/assets/kpi_timeseries_naive.png` (same source)
  - `docs/assets/batch_aggregate_naive.png` (from `batch naive --seeds 5 --seed-base 1 zeta=0.75` or equivalent)
  - Sample `report.md` excerpts inline as fenced markdown blocks (no separate file)
  - All artefacts deterministic via `--seed 42` so regeneration matches byte-for-byte (modulo matplotlib version drift — note in guide).

### Claude's Discretion

- **D-07 wrong-input handling policy** — see decisions above. Pick something sensible: probably "hint then allow skip after N tries, never auto-advance".
- **Polish tone** — formal vs informal. Project style (REPL output) leans informal but respectful ("Wpisz `help`", not "Proszę wpisać `help`"). Keep that tone in tutorial copy + PRZEWODNIK.md unless researcher finds a reason to change it.
- **Exact tutorial step count** — 8 is target; 9–10 acceptable if planner finds a natural split (e.g., separate `strategies` browse from `run <name>`). Cap at 10 to stay inside the 15-min budget.
- **Where the `tutorial` command appears in `help`** — alongside other REPL commands; update `do_help` to add the new line.
- **Whether to add a root `README.md`** — not in scope here; PRZEWODNIK.md is the canonical doc. If the planner thinks a thin pointer README makes sense, that's fine but optional.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §Phase 8 — Phase goal (≤15 min onboarding, PRZEWODNIK.md + REPL `tutorial` + `--tutorial` flag).
- `.planning/REQUIREMENTS.md` — 27/27 REQ-IDs already mapped to Phases 1–7; Phase 8 adds no new REQ-IDs but its tutorial must EXERCISE one example per category.
- `.planning/PROJECT.md` — Project constraints: Polish-only user-facing content, Python 3.7+ stdlib-first (matplotlib is the only required new dep, already added in Phase 6/7), backwards-compat with v1.0 CLI.
- `x_notes.txt` (project root) — **User's direct written intent for this phase**. The "external paste-back script" alternative was rejected in favor of REPL mode (D-01), but the "user faktycznie wykonuje komendy" spirit drives D-03 (user types commands) and D-12 (UAT-anchored examples).

### Inspiration & test-anchored examples (D-12 enforces these as canonical example source)
- `.planning/phases/07.1-comprehensive-uat/08-UAT.md` — 10 cross-phase E2E scenarios, all passing 2026-05-28. PRZEWODNIK.md examples pulled from here.
- `.planning/phases/07.1-comprehensive-uat/08-COMPREHENSIVE-UAT.md` — coverage matrix (which test hits which phase).
- `scripts/verify_phase1.sh`, `scripts/verify_phase3.sh`, `scripts/verify_phase4.sh`, `scripts/verify_phase5.sh`, `scripts/verify_phase6.sh`, `scripts/verify_phase7.sh` — 32+ check() invocations across the six phase exit gates. Tutorial step shape-match patterns (D-04) should be informed by what these scripts assert.

### Theory references (PRZEWODNIK.md theory appendix links out to these — D-13)
- `PROMPT_DLA_AGENTA.txt` (project root) — Authoritative source for SPH model, cycle math (UP/DOWN, fazy, COMMIT/ABSTAIN), KPI definitions, baseline result table.
- `Raport.pdf` (project root) — Project report; full math + experimental results.

### Code surfaces the tutorial integrates with
- `sphsim/cli/repl.py` — `SPHShell(cmd.Cmd)` — tutorial mode lives here (new `do_tutorial` + state machine). All Phase 2 D-17..D-22 + Phase 3 D-50 + Phase 4 D-61 + Phase 7 do_batch conventions apply.
- `sphsim/cli/args.py` — `_build_parser` already has 4-way mutex (`--strategy` / `--custom` / `--batch` / `--compare-agent`); `--tutorial` must extend it. Polish error messages per existing pattern.
- `sphsim/cli/main.py` — early-branch dispatcher (`--interactive`, `--batch`, `--compare-agent` each branch); `--tutorial` adds a 4th early branch routing to `run_repl(start_in_tutorial=True)`.
- `sphsim/report/__init__.py` — `write_report()`, `write_batch_report()` — D-10 requires an optional base-dir override (default unchanged → backwards-compat).
- `sphsim/strategies/__init__.py` — `STRATEGIES` registry (built-in + custom) — tutorial inspects this for "is custom strategy loaded?" detection.
- `examples/custom_strategy_template.py` — used by tutorial step 4 (D-09); already exists from Phase 3, Polish-commented.

### Codebase maps (background — read selectively, don't re-read whole)
- `.planning/codebase/STRUCTURE.md` — **stale** (still describes v1.0 monolith). Use phase 1–7 CONTEXT.md + actual `sphsim/` directory tree for accurate structure.
- `.planning/codebase/ARCHITECTURE.md` — high-level module layout (refer for "where to add new code" patterns).
- `.planning/codebase/CONVENTIONS.md` — naming, language, error message style.

### Prior phase decisions carried forward (don't re-decide)
- `.planning/phases/02-interactive-cli-shell/02-CONTEXT.md` — D-17 (no `/` prefix in REPL), D-20 (`exit` farewell), D-22 (`sph>` prompt), D-30 (default unknown-command message).
- `.planning/phases/03-custom-strategy-loader/03-CONTEXT.md` — D-38 (reload-aware `custom`), D-46/50 (`sphsim.custom.*` namespace dispatch), D-48 (LoaderError → polski one-liner).
- `.planning/phases/04-rational-agent-veto-layer/04-CONTEXT.md` — D-58 (agent default-on), D-61/62 (`compare` two-run dispatch + delta dict).
- Phase 5/6/7 decisions captured in their respective ROADMAP entries and STATE.md (no separate CONTEXT.md — phases planned without discuss-phase).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`sphsim/cli/repl.py::SPHShell`** — `cmd.Cmd` subclass; tutorial mode is a state flag + a new `do_tutorial(arg)` method. Use existing `do_help` table extension pattern (just add one more line); use existing `default()` pattern for unknown-during-tutorial input.
- **`sphsim/cli/repl.py::do_run`/`do_compare`/`do_batch`** — these are the commands the tutorial walks the user through. Tutorial does NOT re-implement them — user types them and the SAME methods run.
- **`sphsim/cli/args.py::_parse_seeds_list`** — already factored out for REPL reuse (Plan 07-02). `--tutorial` flag parsing slots into the same mutex framework.
- **`sphsim/cli/main.py` early branches** — `--interactive` (→ `run_repl()`), `--batch` (→ `run_batch`), `--compare-agent` (→ `run_compare`). Add 4th: `--tutorial` (→ `run_repl(start_in_tutorial=True)`).
- **`sphsim/report/__init__.py::write_report` / `write_batch_report`** — accept current single dir convention `./reports/<timestamp>/`. Add an optional `base_dir` kw-arg with `None` default to preserve backwards-compat (D-10).
- **`examples/custom_strategy_template.py`** — Polish-commented starter from Phase 3, loaded by tutorial step 4 verbatim (D-09).
- **`scripts/verify_phase*.sh` + `.planning/phases/07.1-comprehensive-uat/08-UAT.md`** — single source of truth for tutorial command shapes AND PRZEWODNIK.md examples (D-04 + D-12).

### Established Patterns

- **Polish polish (Phase 2 D-17 + PROJECT.md constraint):** All tutorial output strings, PRZEWODNIK.md prose, and help text in Polish. REPL prompt stays `sph>`. Error messages match existing tone ("Strategia 'X' nie istnieje. Dostępne: …").
- **REPL state mutation pattern (Phase 3):** Tutorial inspects `STRATEGIES.keys()` to detect "user loaded custom" (step 4 verification). Per D-08, state persists across steps — don't reset.
- **No `/` prefix (Phase 2 D-17):** Tutorial mode commands (`skip`, `back`, `repeat`, `exit`) follow this. They are *new* tutorial-mode commands distinct from existing REPL commands like `run`/`compare`; planner decides whether they live on `SPHShell` directly (always available) or only inside tutorial state (cmd-Cmd intercept).
- **Always-on reports invariant (Phase 6):** Tutorial respects this — every `run`/`compare`/`batch` typed during tutorial DOES create a report (just under the `tutorial-<timestamp>/step-N-*/` parent per D-10).
- **`fake_args = argparse.Namespace(...)` REPL pattern (Phase 2/3/4/5/6/7):** Tutorial doesn't need its own variant — the user's typed `run`/`compare`/`batch` commands go through the existing dispatchers which already build `fake_args` correctly.
- **4-way CLI mutex (Phase 7):** Add `--tutorial` as a 5th mutex member with Polish error matching existing style.
- **Deterministic seeding (project-wide):** PRZEWODNIK.md sample artefacts use `--seed 42` (same as REPL `do_run` default) so users can regenerate locally and get the same PNG/MD content.

### Integration Points

- **`SPHShell.__init__`** — add `self._tutorial_state` (None when not in tutorial; a small TutorialFlow object when active). `cmdloop()` and `default()` consult it to decide if input is a tutorial control verb (`skip`/`back`/`repeat`) vs a regular REPL command.
- **`SPHShell.do_help`** — extend to include `tutorial` line. When in tutorial mode, `help` could additionally show `skip`/`back`/`repeat`/`exit` (Claude's Discretion).
- **`sphsim/cli/main.py`** — fourth early-branch for `--tutorial`; reuses `run_repl()` with a new kwarg.
- **`sphsim/report/__init__.py`** — base-dir override threaded through to `write_report` and `write_batch_report`; default `None` → existing behavior, set by tutorial to `./reports/tutorial-<ts>/step-N-<topic>/`.
- **`docs/`** — does not yet exist. Phase 8 creates `docs/PRZEWODNIK.md` + `docs/assets/*.png`.
- **`scripts/verify_phase8.sh`** — phase exit gate (mirroring scripts/verify_phase{1,3,4,5,6,7}.sh): checks `docs/PRZEWODNIK.md` exists with required sections, `docs/assets/*.png` committed, `--tutorial` flag parses, `tutorial` REPL command runs at least one step end-to-end (non-interactive smoke test via `printf "tutorial\nskip\nskip\n…\nexit\n" | python sph_sim.py --interactive`).

</code_context>

<specifics>
## Specific Ideas

- **Tutorial opening message:** Polish banner like the existing INTRO in `repl.py` — friendly, mentions ≤15 min, lists the controls (`skip`/`back`/`repeat`/`exit`), gives a "Wciśnij Enter żeby zacząć." prompt before step 1.
- **Step progress header style:** `[krok 3/8 — Custom strategie]` shown before each task. Matches Phase 6 report header tone.
- **Verification success line:** `✓ zaliczone — krok N/M` (no emoji-spam; checkmark only). On `skip`: `⤼ pominięto — krok N/M`. On unknown input during tutorial: re-show the expected command + a hint (Claude's Discretion exact wording).
- **First line of PRZEWODNIK.md (D-11 lead):** literally a pointer to `python sph_sim.py --tutorial` before any other content.
- **PRZEWODNIK.md examples (D-12):** every fenced code block in the guide carries a comment line like `# Z 08-UAT.md test #5 — Compare-agent empirical proof` so drift is obvious and users can find the source.
- **`docs/assets/` canonical artefacts (D-14):** all generated from the same baseline (`naive --zeta 0.75 --seed 42`) so users running the corresponding tutorial step see identical KPIs.

</specifics>

<deferred>
## Deferred Ideas

These came up during discussion but belong elsewhere. Don't lose them:

- **External paste-back tutorial script (from `x_notes.txt` original vision)** — rejected here in favor of REPL mode. If a future milestone (v1.2?) wants a self-grading homework checker for instructors, that's where it goes.
- **Layered tutorial with optional "advanced" branches per step** — rejected to keep ≤15 min budget. Could be a v1.2 addition once the baseline tutorial is validated.
- **Cross-session tutorial progress persistence (`~/.sphsim_tutorial_progress`)** — overkill now; revisit if user feedback shows tutorials get interrupted often.
- **Full-sweep tutorial (every CLI flag + every REPL command)** — rejected as exceeding the 15-min budget. Could ship as `--tutorial-deep` later.
- **Interactive theory walkthrough (deeper SPH math in PRZEWODNIK.md)** — rejected; `Raport.pdf` and `PROMPT_DLA_AGENTA.txt` are the right home for that.
- **GitHub Pages / external doc hosting** — out of scope; PRZEWODNIK.md is a committed file in repo. Revisit at milestone boundary.
- **Root `README.md` at project root** — left to planner's discretion (Claude's Discretion in D-07/Polish tone block).
- **i18n / English version of PRZEWODNIK.md** — explicitly out of scope per PROJECT.md (polski everywhere).

</deferred>

---

*Phase: 8-documentation-interactive-tutorial*
*Context gathered: 2026-05-28*
