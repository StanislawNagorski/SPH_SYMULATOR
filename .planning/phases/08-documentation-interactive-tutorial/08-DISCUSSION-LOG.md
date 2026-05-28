# Phase 8: Documentation + Interactive Tutorial - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-28
**Phase:** 8-documentation-interactive-tutorial
**Areas discussed:** Tutorial form factor + step UX + detection + navigation; PRZEWODNIK.md structure + examples + theory + outputs; tutorial coverage + side-effects + state; CLI `--tutorial` flag

---

## Tutorial Form Factor

| Option | Description | Selected |
|--------|-------------|----------|
| External paste-back script (per x_notes.txt) | Standalone `python tutorial.py` in separate terminal; user runs commands on real sph_sim and pastes output back; tutorial diffs and marks step done. Closest to written vision. | |
| REPL tutorial mode (per ROADMAP) | `tutorial` command inside existing REPL — guided flow in same window. Lower implementation cost; integrates with Phase 2 cmd.Cmd shell. | ✓ |
| Hybrid: REPL `tutorial` drives + user TYPES in same REPL | Inside REPL, prints task + command, waits for user to type it, inspects result. | |
| Both: REPL tutorial AND a separate paste-back script | Ship both flavors — casual users get REPL, power users get external script. | |

**User's choice:** REPL tutorial mode (per ROADMAP)
**Notes:** Resolves the ROADMAP-vs-`x_notes.txt` conflict in favor of the ROADMAP. The "user faktycznie wykonuje komendy" spirit from x_notes.txt is preserved via D-03 (next decision).

---

## Tutorial Step UX (execution model)

| Option | Description | Selected |
|--------|-------------|----------|
| Show command, user TYPES it themselves, tutorial detects & advances | Tutorial prints task + exact command; user types it at `sph>` prompt; tutorial inspects result and advances. Hands-on. | ✓ |
| Tutorial auto-executes each step, narrates what it did | User types `next` and tutorial runs the simulation itself. Passive reading. | |
| Per-step choice: 'shall I run it or do you type it?' | Maximum flexibility, more state to manage. | |
| Print command, say 'try it now', auto-run after delay/`next` | Hybrid; complex detection. | |

**User's choice:** Show command, user TYPES it themselves, tutorial detects & advances
**Notes:** Preserves the hands-on spirit of `x_notes.txt` without leaving the REPL — user learns commands by typing them, lowering barrier-to-entry while staying in one window.

---

## Detection / Verification

| Option | Description | Selected |
|--------|-------------|----------|
| Match expected command shape, then verify the simulation result | Tutorial holds a pattern (e.g., `batch <strategy> --seeds <N≥3>`); accepts valid variants; inspects KPI/files post-run. Forgiving + UAT-style. | ✓ |
| Exact command match — user must type the suggested command verbatim | Simple but punishes exploration. | |
| Just check that SOMETHING ran without error | Most permissive; no KPI verification. | |
| Don't detect — user types `next` to advance | Zero verification, zero false-negatives. | |

**User's choice:** Match expected command shape, then verify the simulation result
**Notes:** Aligns with `x_notes.txt` "inspiruj się istniejącymi testami UAT" — the `verify_phase*.sh` check() patterns are the model.

---

## Navigation / Controls

| Option | Description | Selected |
|--------|-------------|----------|
| `skip` + `exit` + `[N/M]` progress | Minimal commands; no resume across sessions; progress indicator visible. | |
| Above + `back` + `repeat` | Adds bidirectional navigation and re-show. | ✓ |
| Above + `resume` (persist progress to disk) | File at `~/.sphsim_tutorial_progress`. | |
| Just `skip` and `exit`, no progress indicator | Cleanest output but loses 'where am I'. | |

**User's choice:** Above + `back` (previous step) + `repeat` (re-show current step task)
**Notes:** No persistent cross-session resume (rejected as overkill for 15-min flow). `[krok N/M]` progress header included. `back` is safe per D-08 (state persists).

---

## PRZEWODNIK.md Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Hybrid: Quickstart → Walkthrough → Reference → Theory appendix | Top: 60s quickstart; middle: narrative mirroring 7 phases; bottom: alphabetical reference; appendix: SPH model recap. Serves browse and read-front-to-back. | ✓ (with note) |
| Pure linear walkthrough (story-shaped) | Top-to-bottom tutorial in document form; no reference. | |
| Pure reference manual (man-page style) | Sections per command; no narrative. | |
| Quickstart + reference only (skip walkthrough — REPL tutorial replaces it) | Avoid duplication with REPL tutorial. | |

**User's choice:** Hybrid (with note: "first lines are about tutorial")
**Notes:** PRZEWODNIK.md opens with a pointer to `python sph_sim.py --tutorial` before any other content (D-11 lead).

---

## Example Sourcing

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse exact commands from `07.1-comprehensive-uat/08-UAT.md` + verify_phase*.sh | Single source of truth; drift detected by existing CI gates. | ✓ |
| Fresh-written examples tailored for didactic flow | Optimized for teaching order; can rot silently when CLI changes. | |
| Mix: UAT commands for verification chapters, fresh for intro | Dual sourcing logic. | |

**User's choice:** Reuse exact commands from `07.1-comprehensive-uat/08-UAT.md` + verify_phase*.sh
**Notes:** Every fenced block in the guide should annotate its source (e.g., `# Z 08-UAT.md test #5`).

---

## Theory Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Short appendix: model recap + incentive compatibility + links out | ~1 page; deep math stays in PROMPT_DLA_AGENTA.txt + Raport.pdf. | ✓ |
| Just links — no theory in PRZEWODNIK.md | Pure operational guide. | |
| Deeper integrated theory — explain SPH-STP, φ/ρ, KPI derivation | Self-contained handout; risk of duplication with Raport.pdf. | |
| You decide — use judgment | Deferred call. | |

**User's choice:** Short appendix: model recap + incentive compatibility + links out
**Notes:** Keeps guide operational; theory link-out preserves academic context without duplication.

---

## Expected Outputs (PRZEWODNIK.md artefacts)

| Option | Description | Selected |
|--------|-------------|----------|
| Embed one canonical PNG + sample report.md excerpt for each major command | Committed under `docs/assets/`; deterministic via `--seed 42`. | ✓ |
| Commands only — no embedded outputs | Pure 'try and see' philosophy. | |
| Sample outputs as text/JSON only (no images) | Avoid binary files. | |

**User's choice:** Yes — embed one canonical PNG + sample report.md excerpt for each major command
**Notes:** Artefacts deterministic via `--seed 42`; matplotlib version drift acknowledged in guide.

---

## Tutorial Content Coverage

| Option | Description | Selected |
|--------|-------------|----------|
| Curated golden path mirroring v1.1 phases (~8-10 steps, ~15 min) | One step per REQ-ID category; matches ROADMAP 15-min budget. | ✓ |
| Full sweep — every CLI flag + every REPL command (~25+ steps, 30-45 min) | Comprehensive but exceeds time budget. | |
| Minimal smoke test — 3-4 steps (~5 min) | Skips flagship features (agent veto, batch). | |
| Layered: golden path with optional advanced branches per step | Significantly more content to maintain. | |

**User's choice:** Curated golden path mirroring v1.1 phases (~8-10 steps, ~15 min)
**Notes:** 8 steps target, ≤10 acceptable. Each step hits one REQ-ID category once.

---

## Tutorial Side Effects (reports directory policy)

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated `./reports/tutorial-<timestamp>/` parent dir for all tutorial outputs | Clean dir per session; small wiring change in write_report(). | ✓ |
| Normal `./reports/<timestamp>/` — mix with regular runs | No special handling; harder to clean up. | |
| Suppress side effects during tutorial — in-memory only | Contradicts Phase 6 always-on invariant; user misses report feature. | |
| Ask user upfront: 'tutorial will create 7 report dirs, ok?' | Extra friction at session start. | |

**User's choice:** Use a dedicated `./reports/tutorial-<timestamp>/` parent dir for all tutorial outputs
**Notes:** Requires `write_report()` / `write_batch_report()` to accept optional `base_dir` kwarg, default `None` to preserve backwards-compat.

---

## REPL State Across Tutorial Steps

| Option | Description | Selected |
|--------|-------------|----------|
| Persists naturally — each step builds on the previous shell state | Custom strategy loaded in step 4 still available in step 5. Matches REPL mental model. | ✓ |
| Each step starts from clean defaults | Predictable but contradicts how REPL actually works. | |
| Tutorial declares state per step — explicit `precondition` for each | More bookkeeping; more complexity. | |

**User's choice:** Persists naturally — each step builds on the previous shell state
**Notes:** `back` is safe because state is monotonic-ish (Phase 3 D-38 reload-aware `custom` handles re-loading cleanly).

---

## CLI `--tutorial` Flag Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| `--tutorial` enters the REPL already in tutorial mode | Equivalent to `--interactive` + auto-`tutorial`; mutex with `--strategy`/`--custom`/`--batch`. | ✓ |
| `--tutorial` runs a non-interactive scripted walkthrough | Contradicts hands-on design from D-03. | |
| `--tutorial` prints a 'how to start' message then enters REPL | More confusing; user has to type `tutorial` anyway. | |

**User's choice:** `--tutorial` enters the REPL already in tutorial mode
**Notes:** Reuses `run_repl()` from Phase 2 via new kwarg `start_in_tutorial=True`. Add 5th mutex member in `sphsim/cli/args.py`.

---

## Claude's Discretion

The user delegated these specific calls to the planner / executor:

- **Wrong-input handling policy during tutorial** (D-07) — pick a sensible policy (e.g., hint then allow `skip` after N tries, never auto-advance).
- **Polish tone** — keep informal-respectful tone consistent with existing REPL output ("Wpisz `help`", not "Proszę wpisać `help`").
- **Exact tutorial step count** (D-09) — 8 target; up to 10 acceptable; cap at 10.
- **Where `tutorial` appears in `do_help` listing** — alongside other REPL commands.
- **Root `README.md`** — optional; if planner thinks a thin pointer README helps, fine; else PRZEWODNIK.md is canonical.

## Deferred Ideas

Surfaced during discussion but explicitly out of Phase 8 scope:

- External paste-back tutorial script (the original `x_notes.txt` vision) — rejected here; future milestone candidate.
- Layered tutorial with optional "advanced" branches per step — rejected to stay inside 15-min budget.
- Cross-session tutorial progress persistence (`~/.sphsim_tutorial_progress`) — overkill now.
- Full-sweep tutorial (`--tutorial-deep` style) — exceeds time budget; revisit on demand.
- Deeper SPH math integrated in PRZEWODNIK.md — duplicates Raport.pdf.
- GitHub Pages / external doc hosting.
- i18n / English version of PRZEWODNIK.md (explicitly out of scope per PROJECT.md).
