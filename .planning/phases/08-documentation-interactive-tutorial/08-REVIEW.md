---
phase: 08-documentation-interactive-tutorial
reviewed: 2026-05-29T11:30:00Z
depth: standard
scope: gap-closure (commits cab7bfc..HEAD — UAT Gaps 1/2/4 in 08-08, Gap 3 in 08-09, Gap 5 in 08-10)
files_reviewed: 7
files_reviewed_list:
  - sphsim/cli/args.py
  - sphsim/cli/repl.py
  - sphsim/cli/tutorial.py
  - tests/test_tutorial.py
  - scripts/verify_phase8.sh
  - scripts/verify_phase3.sh
  - docs/PRZEWODNIK.md
findings:
  critical: 0
  warning: 3
  info: 5
  total: 8
status: issues_found
---

# Phase 8 (Gap-Closure Pass): Code Review Report

**Reviewed:** 2026-05-29T11:30:00Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found
**Scope:** Gap-closure commits only. Prior REVIEW (2026-05-28) covered the
initial Phase 8 implementation (commits up to 90bcb52). This pass covers the
five UAT gap-closure changes between `cab7bfc` and HEAD:

| Commit       | Closure target                                                  |
|--------------|-----------------------------------------------------------------|
| `cab7bfc`    | UAT Gap 1+2+4 — tutorial banner pointer + controls footer + typo guard |
| `c76ce02`    | UAT Gap 4 regression test                                       |
| `b672654`    | UAT Gap 3 — 8 → 9 step split (step 2 → list + step 3 details)  |
| `9bc907d`    | UAT Gap 3 — repl.py hint-set + banner literal                  |
| `963e7cd`    | UAT Gap 3 — test alignment to 9-step contract                  |
| `25beb53`    | UAT Gap 3 — verify_phase8.sh D2/D3/D4 to 9-step                 |
| `36de02a`    | UAT Gap 3 — sample step heading in PRZEWODNIK.md                |
| `df3779d`    | UAT Gap 5 — auto-promote no-mode → --interactive + banner       |
| `89a1bd1`    | UAT Gap 5 — test flip                                           |
| `64ec057`    | UAT Gap 5 — verify_phase8.sh C7 + verify_phase3.sh retro grep   |

## Summary

The gap-closure changes are tightly scoped, well-tested, and preserve the
8-step → 9-step renumbering across all consumers (state machine, REPL hint
set, tests, verify scripts, user-guide sample). The three substantive new
behaviors:

1. **UAT Gap 4 (`_last_command_unknown` short-circuit)** — solid: the flag is
   set in `default()`, read+reset in `postcmd` before `check_step` can advance
   soft-pass steps 7/8 on garbage input. Regression test
   `test_soft_pass_step_rejects_unknown_command` covers the canonical case.
2. **UAT Gap 3 (step 2 split into 2+3)** — the renumbering is consistent: the
   state machine, `STEP_TOPICS`, `STEP_TASKS`, hint set, verify-script
   counters, sample heading in `PRZEWODNIK.md`, and `_run_repl_interactive`
   skip-count tests all agree on 9 steps.
3. **UAT Gap 5 (auto-promote no-mode → `--interactive`)** — pragmatic, but the
   banner has two minor coherence defects (see WR-01 below).

No new BLOCKER defects were introduced. The defects found are quality issues
(stale comments referring to pre-split step numbers, banner inconsistency
with no-mode contract) and one moderately interesting flow issue with
`_last_command_unknown` lifecycle when entering tutorial after typing a typo
*outside* tutorial.

The prior CR-01 (`emptyline()` re-run) remains correctly fixed and the
regression test `test_cr01_tutorial_banner_shown_exactly_once` continues to
guard it.

## Warnings

### WR-01: Auto-promote banner advertises `--interactive` as an alternate mode while already running it

**File:** `sphsim/cli/args.py:204-215`
**Commits:** `df3779d`
**Issue:** When the user invokes `python sph_sim.py` with no mode flag, the
post-parse block first prints "Nie podano trybu — uruchamiam tryb
interaktywny (REPL)." (line 209) and then lists `--interactive` as the first
entry under "Dostępne tryby:" (line 211). The plan-08-10 source comment at
line 207 says the banner enumerates "the 4 alternate modes" — but the printed
list has 5 entries because `--interactive` is included. This is internally
inconsistent (the comment promises 4, the code prints 5) and pedagogically
confusing for a new user: they are told they are already in interactive mode,
then told it is one of the modes they could choose. Tests assert presence of
each flag string but do not assert the count, so this slipped through.

A second, smaller issue: the four genuinely alternate entries use two
different spacing widths after the flag name (`--strategy NAZWA` has two
spaces before `Pojedyncza`, `--custom PLIK.py` has two spaces before
`Załaduj`, but `--batch --seeds N` has two spaces before `Uruchom`, and
`--tutorial` has six spaces before `Interaktywny`). Cosmetic but visible in
the terminal.

**Fix:** Either remove the `--interactive` row (matches the comment) or
update the comment to "the 4 alternate modes plus the current one".
Recommended — drop the redundant row, since the prefix message already tells
the user they are in `--interactive`:

```python
print("Nie podano trybu — uruchamiam tryb interaktywny (REPL).", file=sys.stderr)
print("Pozostałe tryby (do użycia z linii poleceń):", file=sys.stderr)
print("  --strategy NAZWA   Pojedyncza symulacja wbudowanej strategii (np. naive).", file=sys.stderr)
print("  --custom PLIK.py   Załaduj i uruchom własną strategię z pliku .py.", file=sys.stderr)
print("  --batch --seeds N  Uruchom strategię na wielu seedach z agregatem.", file=sys.stderr)
print("  --tutorial         Interaktywny tutorial v1.1 (~9 kroków, ≤15 min).", file=sys.stderr)
```

If the row stays, normalize the alignment so the descriptions start at the
same column.

### WR-02: `_last_command_unknown` flag is not reset on the control-verb branch of `precmd`, so a typo *before* entering tutorial leaks one stale True into the first turn after `do_tutorial`

**File:** `sphsim/cli/repl.py:104-147, 152-160`
**Commits:** `cab7bfc`
**Issue:** `precmd` resets `_last_command_unknown = False` at line 146 only
on the regular-dispatch path. The four control-verb branches
(`skip`/`back`/`repeat`/`exit`, lines 110-141) return `''` without touching
the flag. Combined with the early-return at `postcmd` line 153 (which fires
when `_tutorial_state is None`), the following sequence leaks a stale `True`
into the first tutorial step:

```
sph> blablabla         # outside tutorial — default() sets flag True,
                       # postcmd early-returns at line 153 because
                       # _tutorial_state is None → flag NOT cleared
sph> tutorial          # precmd line 105: _tutorial_state is None → return
                       # line; flag still True. do_tutorial activates state.
                       # postcmd: _tutorial_state is now not None →
                       # falls through line 153 check → line 158 sees
                       # flag True → returns early WITHOUT calling
                       # check_step for line='tutorial'.
sph> run naive zeta=0.75   # normal dispatch — line 146 resets flag — works
```

The functional impact is null today because `check_step(1, 'tutorial', ...)`
would have returned False anyway (step 1 wants `run naive ...`), but the
mechanism is fragile: any future step whose `check_step` accepts the literal
string `'tutorial'` would be falsely refused after this leak. The fix is
trivially local.

This same fragility means: typing a typo *inside* tutorial, then immediately
typing `skip`/`back`/`repeat`/`exit`, leaves the flag set across the control
verb's `postcmd` early-return (line 153 `not line.strip()` fires because
precmd returned `''`). The flag persists until the next non-control command
triggers the reset on line 146. Not currently exploitable because postcmd's
early-return on `not line.strip()` runs *before* line 158, so the stale flag
has no read path. But this is a single-edit-away regression risk.

**Fix:** Centralize the reset to fire unconditionally at the top of `precmd`
(before any branching), removing the need to remember to reset on every code
path:

```python
def precmd(self, line):
    # Flag belongs to "the line just dispatched" — reset for every new line,
    # regardless of tutorial state or control-verb interception.
    self._last_command_unknown = False
    if self._tutorial_state is None:
        return line
    stripped = line.strip()
    ts = self._tutorial_state
    # ... rest unchanged; delete the line 146 reset
```

### WR-03: Step 3 (`strategy-details`) `check_step` accepts `strategy strategies` and other nonsense names — verification is purely structural

**File:** `sphsim/cli/tutorial.py:295-296`
**Commits:** `b672654`
**Issue:** Post-split, step 3 verification is
`len(tokens) >= 2 and tokens[0] == 'strategy'`. There is no check that
`tokens[1]` is in `strategies_keys`. Adversarial inputs that pass include:

- `strategy strategies` — looks like a typo but advances
- `strategy 9999` — pure noise
- `strategy --tutorial` — flag-shaped junk

Because step 3 fires `do_strategy` *before* `check_step` (cmd.Cmd dispatch
order), the REPL has already printed `Strategia '<bogus>' nie istnieje.
Dostępne: ...` to the user. Then `check_step` returns True and the tutorial
auto-advances with `✓ zaliczone — krok 3/9`. The user sees two contradictory
messages back-to-back: "doesn't exist" + "step passed".

The symmetric concern on step 4 is correctly guarded
(`tokens[1] in builtin_strategies`, line 302); step 3 should mirror this
with `tokens[1] in strategies_keys` (not `builtin_strategies`, because by
step 3 the user may have already loaded a custom from step 5 in a prior
session — though step 3 precedes step 5 so this is unlikely in practice).

**Fix:**

```python
# Step 3 (strategy-details) — accept any registered name (built-in or custom).
if step_n == 3:
    return (
        len(tokens) >= 2
        and tokens[0] == 'strategy'
        and tokens[1] in strategies_keys
    )
```

Add a unit-test row to `TestTutorialFlow.test_check_step3_strategy_details`:

```python
self.assertFalse(
    check_step(3, 'strategy bogus', None, {'naive'}, frozenset({'naive'})),
    msg="step 3 should reject unknown strategy names"
)
```

## Info

### IN-01: Stale step-number comments referencing the pre-split 8-step contract

**Files:**
- `sphsim/cli/repl.py:610` — `# Note: step 6 jest soft-pass informational step` (post-split, step 6 is `compare`, a hard-pass step; the soft-pass `env` step is now step 7).
- `sphsim/cli/tutorial.py:255` — `step_n: tutorial step number (1..8).` (should be `1..9`).
- `sphsim/cli/tutorial.py:33` — `Order MUST match RESEARCH §Step Verification Map (lines 439-452).` — research line numbers likely drifted after the split; verify or drop the line reference.

**Issue:** These comments will mislead the next maintainer reading the file.
None of them affect runtime, but a code-search for "step 6" or "1..8" in
the tutorial subtree will now return stale hits.

**Fix:** Quick comment refresh, no behavior change:

```python
# repl.py:610
# Note: step 7 jest soft-pass informational step (env override —
# Open Question #2 resolution). Zero filesystem snapshot — check_step(7,
# line, ...) zwraca True dla dowolnej non-empty linii.

# tutorial.py:255
step_n: tutorial step number (1..9).
```

### IN-02: `verify_phase8.sh` D3 sends 10 skips for a 9-step tutorial; the 10th lands outside tutorial state and produces "Nieznana komenda: 'skip'"

**File:** `scripts/verify_phase8.sh:122`
**Commits:** `25beb53`
**Issue:** The printf payload contains 10 `skip` lines:
`'tutorial\nskip\nskip\nskip\nskip\nskip\nskip\nskip\nskip\nskip\nexit\n'`.
9 skips suffice to walk steps 1→9 and then clear `_tutorial_state` on the
9th invocation (when `ts.step == ts.total`). The 10th `skip` is dispatched
to the REPL as a regular command, fails `do_*` resolution, and triggers
`default()`, printing `Nieznana komenda: 'skip'`. The grep still finds
`pominięto — krok 9/9` and the check passes, but the test log will silently
include the extra error line.

**Fix:** Drop the 10th `skip`:

```bash
"... ; printf 'tutorial\\nskip\\nskip\\nskip\\nskip\\nskip\\nskip\\nskip\\nskip\\nskip\\nexit\\n' | ..."
#                                                                             ^^^^^^^ remove one
```

### IN-03: Step 7 (`env`) and step 8 (`report`) `expected_command_hint` strings cannot reach the user via the hint path

**File:** `sphsim/cli/tutorial.py:165-169, 184`
**Issue:** Both steps are soft-pass (`check_step` returns `bool(line)` for
any non-empty input). The only way `_show_step_hint` can fire is if
`check_step` returned False. For steps 7/8 that requires an empty line, but
`postcmd` line 153 already early-returns on `not line.strip()`. So the
`expected_command_hint` fields for step 7 (a multi-line
`python sph_sim.py --strategy ...` invocation) and step 8 (`skip`) are dead
data — they cannot reach the user via the hint path.

This is documented intent (soft-pass means no hint), but the fields suggest
otherwise. Either delete them or comment-mark them as for-documentation-only.

**Fix:** Add a one-line comment on `STEP_TASKS[7]` and `STEP_TASKS[8]`:

```python
# Note: expected_command_hint is documentation-only for steps 7/8 —
# soft-pass check_step never fires the hint code path.
```

### IN-04: `test_soft_pass_step_rejects_unknown_command` requires exactly 6 skips to reach step 7; brittle to future step renumbering

**File:** `tests/test_tutorial.py:209-227`
**Commits:** `c76ce02`
**Issue:** The test hard-codes the skip count
(`'tutorial\nskip\nskip\nskip\nskip\nskip\nskip\ntojesttypo\n...'`) to reach
step 7 (env — first soft-pass step). The docstring correctly notes "the
first soft-pass step shifted from old 6 to new 7 after splitting step 2",
but if a future change adds or removes a step before the first soft-pass,
this count breaks silently — the test will then either type the typo on a
hard-pass step (and the new `[krok N/9` assertion fails with a confusing
diff) or on the wrong soft-pass step.

**Fix:** Either compute the skip count from `STEP_TOPICS` at import time,
or add a one-line invariant comment so the next maintainer sees the
contract:

```python
# Invariant: number of skip lines below must equal
# (first-soft-pass-step-number - 1). Step 7 (env) is the first soft-pass.
# If STEP_TOPICS reorders, recount here.
```

### IN-05: `verify_phase3.sh` C7 (line 156) and `verify_phase8.sh` C7 (line 113) now share the same Phase 8 contract — document the cross-phase coupling

**Files:**
- `scripts/verify_phase3.sh:155-156`
- `scripts/verify_phase8.sh:112-113`
**Commits:** `64ec057`
**Issue:** Both checks now depend on Phase 8 UAT Gap 5 behavior
("Nie podano trybu" banner) to pass — Phase 3's verification script will
fail if anyone ever reverts Phase 8's auto-promote contract. The comment on
verify_phase3.sh line 155 acknowledges this (`(Phase 8 UAT Gap 5)`), but a
maintainer touching only Phase 3 code may not realize their failing test is
flagging a Phase 8 regression. This is the cost of retrofitting Phase 3's
mutex-required gate to the new contract, and is acceptable, but worth a
short note in `08-VERIFICATION.md` so the cross-phase coupling is recorded.

**Fix:** Document the coupling in the phase-08 verification artifact, or add
an inline comment in `verify_phase3.sh:155` pointing readers to the
authoritative test in `verify_phase8.sh:112`.

---

_Reviewed: 2026-05-29T11:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Scope: gap-closure commits cab7bfc..HEAD only — prior REVIEW.md (2026-05-28) covered the initial Phase 8 implementation through commit 90bcb52._
