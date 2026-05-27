---
phase: 3
slug: custom-strategy-loader
status: ratified
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-27
ratified: 2026-05-27
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (stdlib only — PROJECT.md constraint) |
| **Config file** | none (test discovery via `python -m unittest discover`) |
| **Quick run command** | `python -m unittest tests.test_loader` |
| **Full suite command** | `python -m unittest discover tests && python scripts/regression_check.py` |
| **Phase exit gate** | `bash scripts/verify_phase3.sh` (created in Plan 04 task 02) |
| **Estimated runtime** | ~10 seconds full suite + ~5 seconds verify_phase3.sh REPL smokes ≈ 15 sec |

---

## Sampling Rate

- **After every task commit:** Run `python -m unittest tests.test_loader` (when test_loader.py exists from Wave 1)
- **After every plan wave:** Run `python -m unittest discover tests && python scripts/regression_check.py`
- **Before `/gsd:verify-work`:** `bash scripts/verify_phase3.sh` returns 0 (gates 5 ROADMAP SCs + regression + invariant)
- **Max feedback latency:** 10 seconds for unit suite (loader+meta consistency); 15 seconds for full phase gate

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | STRAT-03, STRAT-04 | T-3-02 | `BUILTIN_STRATEGIES = frozenset(STRATEGIES.keys())` snapshot prevents collision detection drift after runtime custom registration | regression + smoke | `python -c "from sphsim.strategies import STRATEGIES, BUILTIN_STRATEGIES; assert isinstance(BUILTIN_STRATEGIES, frozenset) and BUILTIN_STRATEGIES == frozenset(STRATEGIES.keys()) == frozenset(['naive','threshold','phase_prob','incentive','adaptive'])" && python scripts/regression_check.py && python -m unittest tests.test_strategy_meta_consistency` | ✅ (BUILTIN_STRATEGIES — task 3-01-01) | ⬜ pending |
| 3-01-02 | 01 | 1 | STRAT-03, STRAT-04 | T-3-01, T-3-02, T-3-03, T-3-04, T-3-05 | Loader is pure (no STRATEGIES mutation), banner pre-import on stdout, 4-layer validation fails fast with Polish messages, `sys.modules` cleanup on failed exec; never uses `importlib.reload()` | unit + smoke | `python -c "from sphsim.strategies.loader import load_custom, parse_params_from_meta, LoaderError, EXPECTED_PARAMS; assert EXPECTED_PARAMS == ('dev','l','s','phi','kappa','rho','h','p') and isinstance(LoaderError('x'), Exception)" && python scripts/regression_check.py && python -m unittest tests.test_strategy_meta_consistency` | ✅ (loader.py — task 3-01-02) | ⬜ pending |
| 3-01-03 | 01 | 1 | STRAT-03, STRAT-04 | T-3-02, T-3-03, T-3-04 | 19+ unit cases pin D-47 4 layers + D-49 collision + D-38 reload (Pitfall #1) + Pitfall #2 zombie cleanup + parse_params_from_meta semantics; tearDown cleans tempdir + sys.modules + STRATEGIES snapshot restore | unit | `python -m unittest tests.test_loader -v && python -m unittest discover tests && python scripts/regression_check.py` | ✅ (tests/test_loader.py — task 3-01-03) | ⬜ pending |
| 3-02-01 | 02 | 2 | STRAT-03 | T-3-06 | argparse mutex gains 3rd member `--custom`; `--strategy` choices restricted to `BUILTIN_STRATEGIES` snapshot (D-50); `--param` outside mutex with `action='append'` default `[]` — graceful when paired with `--strategy` (warning only) | smoke + regression + invariant | `python -c "from sphsim.cli.args import parse_args; import sys; sys.argv = ['x', '--custom', 'foo.py', '--param', 'zeta=0.7', '--param', 'max_phase=3']; a = parse_args(); assert a.custom == 'foo.py' and a.param == ['zeta=0.7', 'max_phase=3'] and a.strategy is None" && python scripts/regression_check.py && python -m unittest tests.test_strategy_meta_consistency tests.test_loader` | ✅ (sphsim/cli/args.py — task 3-02-01) | ⬜ pending |
| 3-02-02 | 02 | 2 | STRAT-03 | T-3-01, T-3-05, T-3-06 | `if args.custom:` early branch wraps `load_custom` + `parse_params_from_meta` in try/except LoaderError → Polish stderr + `sys.exit(1)`; banner emerges on stdout PRE-simulation; `STRATEGIES[name] = strategy_fn` registration owned by caller (D-46); `--param` without `--custom` → stderr warning + built-in flow continues | integration + regression | `printf "def strategy_smoke_custom(dev,l,s,phi,kappa,rho,h,p): return 'COMMIT' if dev.status=='UP' else 'ABSTAIN'\nSTRATEGY_META = {'description':'smoke','params':[],'baseline_kpi':None}\n" > /tmp/smoke_custom.py && python sph_sim.py --custom /tmp/smoke_custom.py --seed 42 --json > /tmp/smoke_out.txt 2> /tmp/smoke_err.txt && head -1 /tmp/smoke_out.txt \| grep -q "^\[OSTRZEŻENIE\]" && tail -n +2 /tmp/smoke_out.txt \| python -c "import json, sys; d = json.loads(sys.stdin.read()); assert d['strategy'] == 'smoke_custom', d" && python sph_sim.py --custom /tmp/nope_does_not_exist.py --seed 42 2> /tmp/err2.txt; test $? -eq 1 && grep -q "Plik nie istnieje" /tmp/err2.txt && python scripts/regression_check.py && python -m unittest discover tests` | ✅ (sphsim/cli/main.py — task 3-02-02) | ⬜ pending |
| 3-03-01 | 03 | 2 | STRAT-03, STRAT-04 | T-3-01, T-3-02, T-3-09 | `SPHShell.do_custom` registers in STRATEGIES with reload-aware verb ("Załadowano"/"Przeładowano" — D-38 check BEFORE load_custom); `SPHShell.do_run` builds `SPHSimulator` with `DEFAULT_*` env (Phase 5 will override) + fake `argparse.Namespace` for `format_human`; LoaderError → stdout Polish one-liner, prompt returns (no crash) | integration + smoke | `printf "def strategy_repl_smoke(dev,l,s,phi,kappa,rho,h,p): return 'COMMIT' if dev.status=='UP' else 'ABSTAIN'\nSTRATEGY_META = {'description':'r','params':[],'baseline_kpi':None}\n" > /tmp/repl_smoke.py && printf "custom /tmp/repl_smoke.py\ncustom /tmp/repl_smoke.py\nrun repl_smoke\nrun naive zeta=0.7\nrun\nrun nieznana\nexit\n" \| python sph_sim.py --interactive > /tmp/repl_out.txt 2>&1 && grep -q "Załadowano custom strategię 'repl_smoke'" /tmp/repl_out.txt && grep -q "Przeładowano custom strategię 'repl_smoke'" /tmp/repl_out.txt && grep -q "Strategia: REPL_SMOKE" /tmp/repl_out.txt && grep -q "Strategia: NAIVE" /tmp/repl_out.txt && grep -q "Użycie: run <nazwa>" /tmp/repl_out.txt && grep -q "Strategia 'nieznana' nie istnieje" /tmp/repl_out.txt && python scripts/regression_check.py && python -m unittest discover tests` | ✅ (sphsim/cli/repl.py — task 3-03-01) | ⬜ pending |
| 3-03-02 | 03 | 2 | STRAT-03, STRAT-04 | T-3-02 | `do_help` lists 6 commands with Polish descriptions; `do_strategies` dispatches namespace `sphsim.strategies.<n>` (built-in) vs `sphsim.custom.<n>` (custom) per BUILTIN_STRATEGIES membership and appends ` [custom]` suffix; `do_strategy` uses the same dispatch for meta lookup | integration | `printf "def strategy_repl_smoke(dev,l,s,phi,kappa,rho,h,p): return 'COMMIT' if dev.status=='UP' else 'ABSTAIN'\nSTRATEGY_META = {'description':'r','params':[],'baseline_kpi':None}\n" > /tmp/repl_smoke.py && printf "help\nstrategies\ncustom /tmp/repl_smoke.py\nstrategies\nstrategy repl_smoke\nstrategy naive\nexit\n" \| python sph_sim.py --interactive > /tmp/repl_mod.txt 2>&1 && grep -q "custom <ścieżka>" /tmp/repl_mod.txt && grep -q "run <nazwa>" /tmp/repl_mod.txt && grep -q "repl_smoke.*\[custom\]" /tmp/repl_mod.txt && grep -q "Opis:.*zeta" /tmp/repl_mod.txt && python scripts/regression_check.py && python -m unittest discover tests` | ✅ (sphsim/cli/repl.py — task 3-03-02) | ⬜ pending |
| 3-04-01 | 04 | 3 | STRAT-05 | T-3-01 | Template Polish docstring + STRATEGY_META schema-conformant; `python -W all -m py_compile` clean (SC #3); CLI `--custom <template>` deterministic JSON (matches itself on rerun); REPL flow shows `[custom]` suffix and runs `run`; param `max_phase` measurably changes output (D-39/D-40 end-to-end) | acceptance + smoke + regression | `python -m py_compile examples/custom_strategy_template.py && python -c "from sphsim.strategies.loader import load_custom; n, fn, m = load_custom('examples/custom_strategy_template.py'); assert n == 'custom_strategy_template' and callable(fn) and m['description']" && python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json > /tmp/t_out.txt 2>/dev/null && head -1 /tmp/t_out.txt \| grep -q "^\[OSTRZEŻENIE\]" && tail -n +2 /tmp/t_out.txt \| python -c "import json, sys; d = json.loads(sys.stdin.read()); assert d['strategy'] == 'custom_strategy_template' and 'avg_val_last100' in d['metrics']" && python scripts/regression_check.py && python -m unittest discover tests` | ✅ (examples/custom_strategy_template.py — task 3-04-01) | ⬜ pending |
| 3-04-02 | 04 | 3 | STRAT-03, STRAT-04, STRAT-05 | T-3-01..T-3-06, T-3-12 | `scripts/verify_phase3.sh` mechanically verifies all 5 ROADMAP SCs (CLI+REPL load, Polish errors with concrete signature, template compile+load+run, [custom] suffix, banner pre-import) plus regression 8/8 + Phase 2 invariant + loader 19+ unit cases + mutex enforcement; exits 0 with "Phase 3 ready" on green | phase gate | `chmod +x scripts/verify_phase3.sh && bash scripts/verify_phase3.sh` | ✅ (scripts/verify_phase3.sh — task 3-04-02) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Verification clusters covered (cross-reference Validation Architecture from RESEARCH.md):**
- **Loader unit (D-47 layers 1–4 + D-49 collision + D-38 reload):** 19+ cases in `tests/test_loader.py` (task 3-01-03)
- **CLI integration:** `--custom` mutex + `--param` parsing + main.py early branch + Polish error stderr (tasks 3-02-01, 3-02-02)
- **REPL integration:** `do_custom` + `do_run` + `do_strategies` `[custom]` suffix + `do_strategy` dispatch + `do_help` listing (tasks 3-03-01, 3-03-02)
- **Regression (Phase 1 contract):** 8 baseline fixtures via `scripts/regression_check.py` — runs on every task; phase gate section 1
- **Invariant (Phase 2 contract):** `tests/test_strategy_meta_consistency.py` — unchanged, runs on every task; phase gate section 2
- **Template acceptance (SC #3):** `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json` deterministic (task 3-04-01; phase gate sections 3, 7)
- **Security banner (SC #5):** stdout starts with `[OSTRZEŻENIE] Ładuję arbitralny kod` (task 3-04-01 + phase gate section 4)

**Sampling continuity self-check:** zero consecutive tasks without `<automated>` verify — every one of the 9 tasks above ships its own automated command, and Plan 04 task 02 (verify_phase3.sh) is the consolidated phase gate.

---

## Wave 0 Requirements

- [x] `tests/test_loader.py` — created as part of Wave 1 (task 3-01-03), NOT a separate Wave 0; covers all 4 layers of D-47, D-49 collision, D-38 reload, parse_params_from_meta
- [x] `examples/custom_strategy_template.py` — created in Wave 3 (task 3-04-01); Plan 01 tests DO NOT depend on this template (they use tempfile fixtures generated per-test); template is the SC #3 acceptance artifact only
- [x] `tests/fixtures/custom_strategies/` — NOT created (planner's discretion declined); per-test `tempfile.mkdtemp` + `_write(name, content)` helper inside `tests/test_loader.py` is preferred (isolated, no shared mutable state between tests, no git commit churn)
- [x] No new framework install — stdlib `unittest` already in use (Phase 2)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Banner format readability (Polish, non-confusing) | STRAT-04 / SC #5 | Subjective UX call — `[OSTRZEŻENIE]` vs alternatives ("UWAGA", "WARNING") | Run `python sph_sim.py --custom examples/custom_strategy_template.py --seed 42`, confirm banner line is single, prefixed `[OSTRZEŻENIE]`, mentions absolute path; sprawdź czy nie miesza się z banner'em CLI (`=====` lines) |
| Template comments are pedagogically clear | STRAT-05 / SC #3 | Reviewer judgement on language quality | Read `examples/custom_strategy_template.py` end-to-end; confirm Polish inline comments cover dev/l/s/phi/kappa/rho/h/p (8 args), COMMIT/ABSTAIN values, STRATEGY_META schema; docstring tells user how to copy + rename + run |
| Error messages are actionable in Polish | STRAT-04 / SC #2 | Translation quality + concreteness across 4 D-47 layers | Trigger each of 4 D-47 layers via crafted bad-file fixtures; confirm message names the missing function (layer 2), expected signature with all 8 arg names (layer 3), specific malformation key (layer 4), file path (layer 1); brak "an error occurred" — wszystkie komunikaty zawierają konkret |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (9/9 tasks)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (every task has its own command + every wave aggregates discover + regression)
- [x] Wave 0 covers all MISSING references — addressed inline in Wave 1 (tests/test_loader.py created in 3-01-03) and Wave 3 (template in 3-04-01); no separate Wave 0 needed
- [x] No watch-mode flags (single-shot `unittest` runs only, single-shot `bash scripts/verify_phase3.sh`)
- [x] Feedback latency < 10s for unit suite (`python -m unittest tests.test_loader` ~2-3s; +regression ~5s = 7-8s); phase gate ~15s (includes REPL smokes)
- [x] `nyquist_compliant: true` set in frontmatter (line 5 — set above)

**Approval:** ratified by planner 2026-05-27. Ready for `/gsd:execute-phase 3`.
