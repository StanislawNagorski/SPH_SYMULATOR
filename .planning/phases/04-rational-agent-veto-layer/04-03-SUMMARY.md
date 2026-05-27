---
phase: 04-rational-agent-veto-layer
plan: 03
subsystem: cli-output
tags: [python, cli, formatter, veto, agent, compare, json, sph]

# Dependency graph
requires:
  - phase: 04-01
    provides: veto_per_phase + n_vetoed_total in simulator.run() return dict
  - phase: 04-02
    provides: wrap_with_agent wrapper that produces 'VETO' decisions (parallel wave)
provides:
  - format_human with VETO conditional section (n_vetoed_total > 0 gate)
  - format_human comparison early-return branch (if 'comparison' in res)
  - format_compare: new public function — 5 KPI x 3 columns delta table + verdict
  - format_json with agent_enabled + auto-pass-through veto_per_phase/n_vetoed_total + comparison branch
affects:
  - 04-04-PLAN (main.py + run_compare — calls format_human with comparison res)
  - 04-05-PLAN (repl.py do_compare — calls format_human and format_compare via format_human)
  - 04-06-PLAN (regression_check.py — JSON schema now has agent_enabled field)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Comparison early-return guard at top of format_human: if 'comparison' in res: return format_compare(...)"
    - "Conditional VETO section: gracefully omitted when n_vetoed_total=0 — clean output for --no-agent"
    - "format_json split: 'comparison' in res triggers comparison top-level key; else metrics with agent_enabled appended"
    - "format_compare: 5 KPI x 3 col (with-agent | bez agenta | Δ) ASCII table + Polish verdict line"

key-files:
  created:
    - tests/test_output_veto.py
  modified:
    - sphsim/cli/output.py

key-decisions:
  - "D-66: VETO section in format_human conditional on n_vetoed_total>0 — gracefully omitted for --no-agent (clean output)"
  - "D-62: format_compare renders 5 KPI x 3 columns; verdict based on agent_helps boolean from comparison dict"
  - "D-67: format_json adds agent_enabled=not args.no_agent to metrics; 'comparison' in res replaces 'metrics' with 'comparison' top-level key"
  - "format_compare KPI order: avg_val_last100, cum_val_total, avg_net_profit, delivery_ratio, avg_providers_l100 (consistent with D-62 spec)"
  - "Verdict logic: agent_helps = with.avg_net_profit > without.avg_net_profit (dydaktycznie najistotniejsza metryka per Claude's Discretion)"

patterns-established:
  - "VETO section as conditional append — reuses sep variable from format_human, identical structural style to IC section"
  - "format_json: ** unpacking of res dict + additional agent_enabled key — avoids listing all keys explicitly, auto-passes new keys from simulator"

requirements-completed: [AGENT-04, AGENT-05]

# Metrics
duration: 4min
completed: 2026-05-27
---

# Phase 4 Plan 03: CLI Output Formatters — VETO section + format_compare + format_json — Summary

**output.py extended with conditional VETO section in format_human, new format_compare function (5 KPI × 3 columns delta table with Polish verdict), and format_json augmented with agent_enabled field and comparison branch**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-05-27T19:17:12Z
- **Completed:** 2026-05-27T19:20:42Z
- **Tasks:** 2 (TDD: RED → GREEN each)
- **Files modified:** 1 source file + 1 new test file

## Accomplishments

- `format_human` has conditional VETO section after IC section: only renders when `n_vetoed_total > 0` — clean output for `--no-agent` unchanged
- `format_human` has early-return comparison branch: `if 'comparison' in res: return format_compare(args, res['comparison'], K1)`
- New `format_compare(args, comp, K1)` function: 5 KPI × 3 columns (with-agent | bez agenta | Δ) ASCII table with Polish verdict `✓ TAK` / `✗ NIE` based on `agent_helps` boolean
- `format_json` extended with `agent_enabled: not args.no_agent` in metrics block; when `'comparison' in res`, replaces `metrics` with top-level `comparison` key (D-67)
- Backwards compatibility preserved: without comparison, all 7 existing metrics keys unchanged; veto_per_phase + n_vetoed_total auto-pass through via `**` unpacking of res dict
- 53 tests passing (41 pre-plan, 12 new in test_output_veto.py)

## Task Commits

Each task used TDD: RED (failing tests) followed by GREEN (implementation).

1. **TDD RED — all tests for both tasks** - `83439b5` (test)
2. **TDD GREEN — full output.py implementation** - `ef864c1` (feat)

_Note: RED commit covers both Task 1 and Task 2 tests together since they're tightly coupled (format_compare called from format_human). GREEN implements all features in one commit._

## Files Created/Modified

- `sphsim/cli/output.py` — Added: `format_compare` function (new, 5×3 delta table); extended `format_human` with VETO section + comparison branch; extended `format_json` with agent_enabled + comparison branch
- `tests/test_output_veto.py` — 12 unit tests covering all behaviors from plan spec (5 for format_human, 3 for format_compare, 4 for format_json)

## Decisions Made

- TDD RED commit covers both tasks together (tests/test_output_veto.py) — tight coupling of format_compare (called from format_human) makes split impractical without artificial stubbing
- `format_compare` placed before `format_human` in output.py — natural read order (called from format_human; Python requires definition before use)
- `format_json` uses `** unpacking` of res dict to auto-include new keys added by simulator (veto_per_phase, n_vetoed_total) — no explicit listing needed, forwards-compatible with any future keys added to simulator.run() result
- Verdict line in `format_compare` uses `n_vetoed_total` from `with_agent` dict (not from args) — cleaner since comparison knows its own veto count

## Deviations from Plan

None - plan executed exactly as written.

## Threat Mitigations Applied

- **T-04-09 (Repudiation — JSON backwards compat):** `format_json` uses `res.get('key', default)` pattern via `{**res_dict}` spread — existing keys bit-identical; new keys always present even with --no-agent (veto_per_phase={}, n_vetoed_total=0, agent_enabled=false)
- **T-04-12 (Spoofing — args without no_agent attribute):** format_json accesses `args.no_agent` directly; Plan 05 (REPL fake_args) must include `no_agent=False` — documented in 04-CONTEXT.md D-67

## Known Stubs

None — format_compare fully renders live comparison data; all KPI values flow through from simulator.run() results.

## Self-Check: PASSED

- `sphsim/cli/output.py` exists with all required patterns
- `tests/test_output_veto.py` exists with 12 tests
- Commits 83439b5 and ef864c1 verified in git log
- 53 tests passing (all pre-existing + 12 new)

---
*Phase: 04-rational-agent-veto-layer*
*Completed: 2026-05-27*
