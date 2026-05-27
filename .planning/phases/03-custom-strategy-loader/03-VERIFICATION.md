---
phase: 03-custom-strategy-loader
verified: 2026-05-27T18:30:00Z
status: passed
score: 5/5 ROADMAP Success Criteria verified
gates_green: true
re_verification: false
gates:
  verify_phase3_sh: PASS=20/FAIL=0
  unittest_discover: 22/22 OK
  test_loader: 21/21 OK
  regression_check: 8/8 PASS
  test_strategy_meta_consistency: 1/1 OK (Phase 2 invariant preserved)
requirements_satisfied:
  - STRAT-03
  - STRAT-04
  - STRAT-05
decisions_audited:
  - D-34
  - D-38
  - D-46
  - D-47
  - D-49
  - D-50
  - D-52
decision_drift:
  - decision: D-38
    note: "CONTEXT.md suggested `importlib.reload()` as fallback; RESEARCH.md (Pitfall #1) empirically overrode to always-fresh `spec_from_file_location`. Implementation follows RESEARCH override. This is documented drift, not silent drift."
  - decision: D-47
    note: "CONTEXT header reads '3-warstwowa walidacja' but the body enumerates 4 layers (import / callable / signature / meta). Implementation has 4 layers matching the body, not the header. Cosmetic CONTEXT typo, not implementation drift."
---

# Phase 3: Custom Strategy Loader — Verification Report

**Phase Goal (ROADMAP.md):**
> Użytkownik może napisać własną strategię w pliku `.py`, załadować ją do symulatora i uruchomić jak każdą wbudowaną.

**Verified:** 2026-05-27
**Status:** passed
**Score:** 5/5 ROADMAP Success Criteria + 3/3 requirements + all gates green

## Goal Achievement Summary

Cel Phase 3 jest osiągnięty: użytkownik może napisać dowolną strategię w pliku `.py`, załadować ją przez CLI (`--custom`) albo przez REPL (`custom <ścieżka>`), zobaczyć ją w `strategies` z suffixem `[custom]`, uruchomić przez `run <nazwa>`, i dostanie polskie komunikaty błędów z konkretem przy każdym z 4 layerów walidacji. Banner `[OSTRZEŻENIE] Ładuję arbitralny kod Pythona z: <abspath>` drukowany przed exec_module ostrzega o wykonaniu arbitralnego kodu. Template `examples/custom_strategy_template.py` istnieje, kompiluje się bez ostrzeżeń, ładuje przez loader, i daje deterministyczne wyniki na baseline'owym środowisku.

## Success Criteria Verification

| #  | Success Criterion                                                                                                                                                | Code Evidence                                                                                                                                                                                                                                                                                                                                                                                                              | Status     |
| -- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| 1  | `--custom <ścieżka>` (CLI) oraz `custom <ścieżka>` (REPL) ładują plik `.py` przez `importlib` i rejestrują strategię z nazwą wziętą z pliku                       | `sphsim/cli/args.py:43` (`mutex.add_argument('--custom', ...)`); `sphsim/cli/main.py:21-37` (early branch + `STRATEGIES[name] = strategy_fn`); `sphsim/cli/repl.py:135-170` (`do_custom`); `sphsim/strategies/loader.py:130` (`basename = os.path.splitext(...)[0]`) + `:145-157` (`spec_from_file_location` + `module_from_spec` + `exec_module`). Smoke: `python sph_sim.py --custom examples/.../template.py --seed 42 --json` → valid JSON ze `"strategy": "custom_strategy_template"`. | ✓ VERIFIED |
| 2  | Loader sprawdza obecność funkcji o wymaganej sygnaturze; każdy błąd → polski komunikat z konkretem (nazwa funkcji, oczekiwane argumenty)                          | `sphsim/strategies/loader.py`: Layer 1 path/spec (`:124-151` — `"Plik nie istnieje"`, `"nie wygląda na plik Pythona"`); Layer 2 callable (`:166-175` — `"Brak funkcji 'strategy_<basename>'... Oczekiwana sygnatura: ..."`); Layer 3 signature (`:177-187` — `"Funkcja ... ma sygnaturę ... Oczekiwana: (dev, l, s, phi, kappa, rho, h, p)"`); Layer 4 meta (`:50-109, :189-196` — 6 distinct error messages). Smoke (verify_phase3.sh §5): 4 layers each rzucają polski one-liner z konkretną nazwą. | ✓ VERIFIED |
| 3  | Plik `examples/custom_strategy_template.py` istnieje, zawiera komentarze po polsku, kompiluje się bez ostrzeżeń, ładuje się przez loader, daje sensowne wyniki   | Plik istnieje (52 linii, polskie komentarze sekcyjne na liniach 1-13, 16-27, 42-43). `python3 -W all -m py_compile examples/custom_strategy_template.py` exit 0 bez ostrzeżeń. `load_custom('examples/custom_strategy_template.py')` zwraca `('custom_strategy_template', <fn>, <meta>)`. CLI smoke: deterministyczny JSON output (KPI: `avg_val_last100=0.0`, `cum_val_total=100.0`, `delivery_ratio=0.7427`, 4-fazowy IC breakdown). Dwa runy seed=42 → identyczne pliki (`diff -q` PASS).  | ✓ VERIFIED |
| 4  | Załadowana custom strategia jest widoczna w `strategies` jako dodatkowy wiersz oznaczony jako "custom"                                                            | `sphsim/cli/repl.py:82-97` (`do_strategies` dispatch: `if name in BUILTIN_STRATEGIES` → built-in format, else → `print(f"  {name:<12}— {description} [custom]")`). Smoke (REPL pipe): `Dostępne strategie: ... custom_strategy_template— Szablon: COMMIT dla faz <= max_phase (przykład dydaktyczny) [custom]`.                                                                                                              | ✓ VERIFIED |
| 5  | Loader przy ładowaniu jasno komunikuje że wykonuje arbitralny Python z pliku użytkownika (świadome ostrzeżenie bezpieczeństwa)                                    | `sphsim/strategies/loader.py:142` (`print(f"[OSTRZEŻENIE] Ładuję arbitralny kod Pythona z: {abspath}")`) drukowane PRZED `spec_from_file_location` (`:146`). Smoke (verify_phase3.sh §4): banner jest linią #1 stdout PRZED jakimkolwiek JSON output'em. Test loadera: 21 testów obserwuje banner w każdym scenariuszu (errors też wyświetlają banner bo print jest przed exec).                                              | ✓ VERIFIED |

**Score: 5/5 — all ROADMAP Success Criteria verified with concrete code evidence + smoke test confirmation.**

## Requirements Verification

| ID       | Description                                                                                                                                                       | Source File(s)                                                                                                                                                                                                                              | Status      |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| STRAT-03 | Użytkownik może załadować custom strategię z pliku `.py` komendą `custom <ścieżka>` lub flagą `--custom <ścieżka>`                                                | `sphsim/cli/args.py:43` (CLI flag), `sphsim/cli/main.py:21-37` (CLI branch), `sphsim/cli/repl.py:135-170` (REPL command), `sphsim/strategies/loader.py:112-199` (`load_custom`)                                                              | ✓ SATISFIED |
| STRAT-04 | Loader waliduje że plik zawiera funkcję o wymaganej sygnaturze i jasno komunikuje błędy (brak funkcji, zła sygnatura, exception)                                  | `sphsim/strategies/loader.py:50-109` (`_validate_meta` — 6 polish messages), `:124-196` (`load_custom` 4 layers: path/spec/callable/sig/meta — 10 distinct polish messages with concrete details)                                              | ✓ SATISFIED |
| STRAT-05 | Projekt zawiera przykładowy szablon `examples/custom_strategy_template.py` z komentarzami po polsku                                                                | `examples/custom_strategy_template.py` (52 linii, polskie komentarze sekcyjne na liniach 1-13, 16-27, 42-43; `STRATEGY_META` z polskim description i polish param descriptions)                                                              | ✓ SATISFIED |

## Decision Drift Audit

Sampled 7 of 19 Phase 3 decisions (D-34, D-38, D-46, D-47, D-49, D-50, D-52) for implementation alignment:

| Decision | Locked Text (CONTEXT.md)                                                                                                                          | Actual Implementation                                                                                                          | Status                 |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------- |
| D-34     | Nazwa strategii = `os.path.splitext(os.path.basename(path))[0]`                                                                                   | `sphsim/strategies/loader.py:130` — verbatim implementation                                                                    | ✓ MATCH                |
| D-38     | Reload: CONTEXT suggested `importlib.reload(mod)` if in sys.modules, else fresh spec                                                              | `sphsim/strategies/loader.py:146` — ALWAYS fresh `spec_from_file_location`; `importlib.reload` not used. **Documented in RESEARCH.md Pitfall #1** (reload fails for synthetic dotted paths without `__path__`). | ⚠️ DRIFT (documented)  |
| D-46     | Loader pure (no STRATEGIES side-effect); custom moduły do `sphsim.custom.<basename>`                                                              | Loader returns `(basename, fn, meta)` tuple; `STRATEGIES[name] = fn` w wywołującym (`main.py:37`, `repl.py:164`); namespace `sphsim.custom.<basename>` (line `:145-155`)                                                                                                                  | ✓ MATCH                |
| D-47     | Header: "3-warstwowa walidacja"; Body: enumerates 4 layers (import / callable / signature / meta)                                                  | 4 layers w `load_custom` (`:144-196`). CONTEXT body matches; header has cosmetic typo "3-warstwowa".                                                                                                                                                                                       | ⚠️ COSMETIC (CONTEXT typo) |
| D-49     | `BUILTIN_STRATEGIES = frozenset(...)` snapshot Phase 1; collision check before register                                                           | `sphsim/strategies/__init__.py:26` — frozenset of 5 keys; `loader.py:133-137` — check `if basename in BUILTIN_STRATEGIES → LoaderError`                                                                                                                                                  | ✓ MATCH                |
| D-50     | `do_strategies` adds `[custom]` suffix; dispatch namespace `sphsim.strategies` vs `sphsim.custom`; argparse `--strategy choices = list(BUILTIN_STRATEGIES)` | `repl.py:82-97` (`do_strategies` z suffix + dispatch); `repl.py:100-132` (`do_strategy` dispatch); `repl.py:172-215` (`do_run` dispatch); `args.py:41` (`choices=list(BUILTIN_STRATEGIES)`)                                                                                                | ✓ MATCH                |
| D-52     | `examples/` jako katalog, brak `__init__.py`, tylko 1 plik tworzony                                                                               | `examples/custom_strategy_template.py` istnieje; `examples/__init__.py` NIE istnieje (`ls examples/` → tylko template + `__pycache__`)                                                                                                                                                                                                              | ✓ MATCH                |

**Audit verdict:** 5/7 perfect match, 1/7 documented drift (D-38 — RESEARCH override on empirical grounds, captured in code comment and Plan 01 traceability), 1/7 cosmetic CONTEXT typo (D-47 header vs body). **No silent drift.**

## Authoritative Gates

| Gate                                 | Command                                              | Result                       | Status     |
| ------------------------------------ | ---------------------------------------------------- | ---------------------------- | ---------- |
| Phase 3 exit gate                    | `bash scripts/verify_phase3.sh`                      | PASS=20 / FAIL=0             | ✓ PASS     |
| Full test discovery                  | `python3 -m unittest discover tests`                 | 22 tests OK                  | ✓ PASS     |
| Loader unit tests                    | `python3 -m unittest tests.test_loader`              | 21 tests OK                  | ✓ PASS     |
| Phase 1 regression (baseline_v1)     | `python3 scripts/regression_check.py`                | PASS 8/8                     | ✓ PASS     |
| Phase 2 invariant (meta ↔ argparse)  | `python3 -m unittest tests.test_strategy_meta_consistency` | 1 test OK              | ✓ PASS     |

All gates green. Backwards compatibility (Phase 1 CLI-04) preserved (8/8 baseline fixtures identical), Phase 2 invariant (STRATEGY_META ↔ argparse) preserved.

## Integration Smoke Tests (End-to-End)

| Test                                 | Command                                                                                                  | Result                                                                                                                                                       | Status |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ |
| CLI happy path                       | `python3 sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json`                       | Banner linia 1; JSON ze `"strategy": "custom_strategy_template"`, `avg_val_last100=0.0`, IC breakdown 4 fazy                                                  | ✓ PASS |
| CLI error: missing file              | `python3 sph_sim.py --custom /tmp/does_not_exist_phase3.py`                                              | `Plik nie istnieje: /tmp/does_not_exist_phase3.py` na stderr, exit code 1                                                                                    | ✓ PASS |
| REPL happy path                      | `printf 'custom .../template.py\nstrategies\nrun custom_strategy_template\nexit\n' | sph_sim --interactive` | Banner + `Załadowano custom strategię`; `strategies` listuje `custom_strategy_template ... [custom]`; `run` produkuje `Strategia: CUSTOM_STRATEGY_TEMPLATE` output + IC table | ✓ PASS |
| REPL reload (D-38)                   | Two `custom <path>` w sesji                                                                              | First: `Załadowano custom strategię 'custom_strategy_template'`. Second: `Przeładowano custom strategię 'custom_strategy_template'`.                          | ✓ PASS |
| CLI determinism                      | Two runs `--seed 42` → `diff -q`                                                                         | Identical JSON                                                                                                                                                | ✓ PASS |
| CLI `--param` effect                 | `--param max_phase=2` vs `--param max_phase=4` → `diff` (negation)                                       | Outputs differ                                                                                                                                                | ✓ PASS |
| Mutex enforcement                    | `--custom foo.py --strategy naive`                                                                       | argparse error `not allowed with argument`                                                                                                                    | ✓ PASS |
| Required mode                       | `python3 sph_sim.py` (no mode)                                                                          | argparse error `one of the arguments`                                                                                                                          | ✓ PASS |

## Threat Model Verification

| Threat ID | Type                       | Mitigation Required                                  | Mitigation Verified In Code                                                                                              | Status      |
| --------- | -------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------- |
| T-3-01    | Tampering/Elevation        | Banner pre-exec                                       | `loader.py:142` — banner printed before `spec.loader.exec_module(mod)` at `:157`                                          | ✓ MITIGATED |
| T-3-02    | Tampering                  | sys.modules namespace isolation                       | `loader.py:38, :145` — `CUSTOM_NAMESPACE_PREFIX = 'sphsim.custom'`; collision check `:133-137`                            | ✓ MITIGATED |
| T-3-03    | Tampering                  | Cleanup zombie module after failed exec               | `loader.py:158-164` — `sys.modules.pop(full_name, None)` in `except Exception`                                            | ✓ MITIGATED |
| T-3-04    | Spoofing                   | `*args` escape acceptable + meta enforcement          | `loader.py:180-187` — VAR_POSITIONAL bypass strict signature check; `:189-196` Layer 4 still enforced (test_var_pos)      | ✓ MITIGATED (accepted) |
| T-3-05    | Information Disclosure     | Banner shows absolute path                            | `loader.py:124, :142` — banner uses `os.path.abspath(os.path.expanduser(path))`                                            | ✓ MITIGATED |
| T-3-06    | Tampering                  | `--param` ignored without `--custom`                  | `main.py:17-19` — graceful warning to stderr; `args.param` doesn't reach built-in flow                                    | ✓ MITIGATED |
| T-3-07    | Repudiation                | Banner is the audit trail                             | Banner always printed (no `--no-warn` flag); strategy name in `format_human`/`format_json` output                          | ✓ ACCEPTED  |
| T-3-08    | DoS                        | User-controlled execution                             | `--custom` is opt-in; Ctrl+C in REPL                                                                                       | ✓ ACCEPTED  |
| T-3-09    | Spoofing                   | User can patch STRATEGIES manually                    | Out of security boundary (academic project)                                                                                | ✓ ACCEPTED  |
| T-3-10    | Information Disclosure     | Custom strategy can read env                          | Banner warns                                                                                                               | ✓ ACCEPTED  |
| T-3-11    | DoS                        | Infinite loop in custom strategy                      | Ctrl+C; out of scope                                                                                                       | ✓ ACCEPTED  |
| T-3-12    | Tampering                  | verify_phase3.sh /tmp/* hygiene                       | `verify_phase3.sh:40` — `trap 'rm -f /tmp/p3_*' EXIT`                                                                      | ✓ MITIGATED |
| T-3-SC    | Supply chain               | No external dependencies                              | stdlib-only (importlib, inspect, os, sys, cmd, readline, argparse, atexit)                                                 | ✓ N/A       |

All Phase 3 STRIDE threats have explicit mitigation or accepted-with-rationale. No silent threat exposure.

## Anti-Pattern Scan

Files modified in Phase 3:
- `sphsim/strategies/loader.py` (245 lines)
- `sphsim/strategies/__init__.py` (27 lines, +6 from Phase 2)
- `sphsim/cli/args.py` (66 lines, +5 from Phase 2)
- `sphsim/cli/main.py` (73 lines, +37 from Phase 2)
- `sphsim/cli/repl.py` (256 lines, +120 from Phase 2)
- `examples/custom_strategy_template.py` (52 lines, new)
- `scripts/verify_phase3.sh` (169 lines, new)
- `tests/test_loader.py` (21 test cases)

| Pattern               | Files Scanned                                              | Result                                          |
| --------------------- | ---------------------------------------------------------- | ----------------------------------------------- |
| `TODO/FIXME/XXX/TBD`  | All 8 modified files                                       | Zero matches                                    |
| `HACK/PLACEHOLDER`    | All 8 modified files                                       | Zero matches                                    |
| `pass`/stub functions | `loader.py`                                                | Only `class LoaderError(Exception): pass` (legit) |
| Empty returns         | `loader.py`                                                | None — every return path has substantive value  |

No anti-patterns found in Phase 3 production code or tests.

## Findings

1. **D-38 RESEARCH override is documented well** — the loader's reload mechanism uses always-fresh `spec_from_file_location` rather than CONTEXT's suggested fallback to `importlib.reload`. The rationale is in (a) `loader.py:9-15` docstring, (b) `loader.py:121` inline comment referencing "RESEARCH Pitfall #1", (c) `03-RESEARCH.md` Pitfall #1 with empirical evidence, (d) `03-01-PLAN.md` task decisions. This is *not* silent drift; it is research-justified override of a Claude's Discretion decision.

2. **D-47 header/body inconsistency in CONTEXT.md** — header says "3-warstwowa walidacja" but body enumerates 4 layers and implementation has 4 layers. Cosmetic typo in CONTEXT.md only; code is correct and well-commented at `loader.py:46, :160, :177, :189-196` with explicit "layer 1/2/3/4" markers.

3. **Banner is invariant across all error paths** — because `print(banner)` is at `loader.py:142`, BEFORE any error-throwing code, every loader failure scenario still shows the banner. This is intentional (per D-45) and provides traceability even when import explodes. Visible in test_loader.py output (every test logs the banner).

4. **Path normalization is conservative** — `os.path.abspath(os.path.expanduser(path))` at `loader.py:124` handles both `~/foo.py` and relative paths uniformly. Banner displays the resolved absolute path, so user knows exactly what file was loaded even if they passed a tilde or relative path.

5. **`format_human`/`format_json` get `args.strategy = name` quick fix at `main.py:40`** — because argparse mutex stores `--custom` value in `args.custom` and leaves `args.strategy` as None, the output formatters' "Strategia:" field would be empty. The quick fix overwrites `args.strategy = name` after load. Reasonable workaround documented inline.

6. **Future risk (Phase 4 boundary)** — Phase 4 (Rational Agent veto layer) will wrap strategies. The current loader returns `(basename, fn, meta)` as a tuple — Phase 4 will need to decide whether to wrap `fn` before or after registration. No blocker for Phase 3 itself, but worth flagging in Phase 4 context.

7. **`--param` graceful ignore** — `main.py:17-19` warns to stderr when `--param` is passed without `--custom` rather than rejecting via argparse. This is intentional graceful UX (D-39 Claude's Discretion) — built-in flow continues unaffected.

8. **Banner SIGPIPE pitfall handled in verify_phase3.sh** — `scripts/verify_phase3.sh:89-94` documents and avoids `grep -q` SIGPIPE issue with `pipefail` by using `grep ... > /dev/null` (reads full stream). Quality engineering.

## Verdict

**status: passed**

Phase 3 ships a complete custom strategy loader: CLI flag (`--custom`) + REPL command (`custom`) load arbitrary `.py` files via `importlib.util.spec_from_file_location`, the 4-layer validator emits Polish error messages with concrete details at every failure mode, the educational template ships and runs deterministically, the listing shows `[custom]` suffix, and the `[OSTRZEŻENIE]` banner announces arbitrary-code execution before exec. All 5 ROADMAP Success Criteria are satisfied with concrete code evidence and end-to-end smoke tests. All 3 requirements (STRAT-03/04/05) are mapped to working code. All authoritative gates green (20/20 phase exit, 22/22 unittest discover, 8/8 regression, 1/1 invariant). 7-sample decision drift audit shows zero silent drift — D-38 override is documented in RESEARCH and code comments; D-47 inconsistency is a cosmetic CONTEXT typo, not implementation drift. 13/13 threat-model entries either mitigated or accepted-with-rationale.

Phase 3 is ready for merge. No human verification items required — the entire surface area is testable via `verify_phase3.sh`.

---

_Verified: 2026-05-27T18:30:00Z_
_Verifier: Claude (gsd-verifier, goal-backward methodology)_
