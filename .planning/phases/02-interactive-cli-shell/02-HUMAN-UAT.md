---
status: partial
phase: 02-interactive-cli-shell
source: [02-VERIFICATION.md]
started: 2026-05-25T18:04:11Z
updated: 2026-05-25T18:04:11Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. REPL UX with empty-line input (WR-01 from REVIEW.md)
expected: Pressing Enter on a blank prompt should be a no-op (not re-run the previous command). Currently `cmd.Cmd` default re-executes the last non-empty command — confirmed via `printf 'strategies\n\n\nexit\n' | python3 sph_sim.py --interactive` re-prints the strategies table 3 times. Whether this is acceptable Phase 2 behaviour or a blocker is a UX-policy decision. ROADMAP Success Criteria do not require emptyline to be a no-op. Project owner must decide: accept-as-is OR add a 2-line `def emptyline(self): return False` override in `sphsim/cli/repl.py` before shipping.
result: [pending]

### 2. Interactive readline line-editing and history persistence on real terminal
expected: User can navigate command history with up/down arrows. New REPL sessions reuse `~/.sphsim_history` (history written on clean exit). Line editing (left/right arrows, backspace, Ctrl-A/E) works as expected. readline behaviour is terminal-coupled — automated stdin-piped tests bypass the line-editing layer entirely. Only an interactive TTY session can confirm.
result: [pending]

### 3. Visual layout of intro banner and strategies table on a real 80-col terminal
expected: All Polish diacritics (`ą ć ę ł ń ó ś ź ż`) render correctly. Em-dash separator displays as `—` (not `?`, `--`, or mojibake). 62-char `=` banner separators fit within an 80-column terminal. Strategies-table columns align readably. Visual judgment from a real terminal — cannot be verified from stdout capture alone.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
