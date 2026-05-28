"""REPL — tryb interaktywny SPH symulatora (Phase 2 + Phase 3 + Phase 4 agent + Phase 7 batch + Phase 8 tutorial).

Klasa SPHShell(cmd.Cmd) udostępnia 7 komend bez prefiksu '/' (8 z dodatkiem `tutorial`):
  - help        — lista komend (D-17, CLI-02)
  - exit        — zakończ sesję (D-20, CLI-03)
  - strategies  — lista wbudowanych i custom strategii (D-29/D-50, STRAT-01)
  - strategy <nazwa>             — szczegóły strategii (D-25/D-26, STRAT-02)
  - tutorial                     — interaktywny tutorial v1.1 (Phase 8 Plan 08-04, TUT-01)
  - custom <ścieżka> [k=v ...]   — załaduj custom strategię z pliku .py (D-37/D-38, STRAT-03)
  - run <nazwa> [k=v ...]        — uruchom symulację built-in lub custom (D-41/D-42)
  - compare <nazwa> [k=v ...]    — porównaj strategię z/bez RationalAgent (D-61, AGENT-05)
  - batch <nazwa> --seeds N|lista [k=v ...] — uruchom strategię na wielu seedach (Phase 7 BATCH-01)

Funkcja run_repl(start_in_tutorial=False) jest jedynym publicznym entry-pointem —
wywoływana z sphsim/cli/main.py gdy args.interactive lub args.tutorial jest True
(D-15 + Phase 8 Plan 08-02 wiring).

Tutorial mode (Phase 8): __init__ + precmd + postcmd współpracują z TutorialFlow
(sphsim/cli/tutorial.py) żeby udostępnić skip/back/repeat/exit + auto-weryfikację
kroków. Pitfall 1: precmd przejmuje `exit` przed do_exit gdy tutorial active.

Wszystkie komunikaty użytkownika po polsku (PROJECT.md constraint).
Stdlib only: cmd + readline + importlib + os + sys + argparse + atexit (D-18, D-19); plugin loader (D-46).
"""
import argparse
import atexit
import cmd
import importlib
import os
import sys
import readline  # noqa: F401 — side effect: cmd.Cmd używa readline dla line-editing na POSIX

from sphsim.strategies import STRATEGIES
from sphsim.strategies import BUILTIN_STRATEGIES
from sphsim.strategies.loader import load_custom, parse_params_from_meta, LoaderError
from sphsim.core.simulator import SPHSimulator
from sphsim.agent import wrap_with_agent
from sphsim.cli.output import format_human
from sphsim.config import (
    DEFAULT_NU, DEFAULT_NSUS, DEFAULT_K0, DEFAULT_K1, DEFAULT_F,
    DEFAULT_T, DEFAULT_KAPPA, DEFAULT_ALPHA, DEFAULT_PHI, DEFAULT_RHO,
)
# Phase 6 REPORT-01/03: side-effect raport po do_run / do_compare; banner na stderr.
from sphsim.report import write_report
# Phase 8 (Plan 08-04): tutorial state machine — pure dispatch + per-step content.
from sphsim.cli.tutorial import TutorialFlow, STEP_TOPICS, STEP_TASKS, check_step


HISTORY_FILE = os.path.expanduser('~/.sphsim_history')

INTRO = (
    "==============================================================\n"
    "  MEDIACJA TRANSFERU PŁATNYCH USŁUG — Symulator Strategii\n"
    "  v1.1 (tryb interaktywny)\n"
    "  Autorzy: Stanisław Nagórski, Mikołaj Rutkowski\n"
    "  Na podstawie: J. Konorski, MPE cz. 2, KT WETI\n"
    "==============================================================\n"
    "  Wpisz `help` żeby zobaczyć dostępne komendy.\n"
    "  Wpisz `exit` lub Ctrl+D żeby zakończyć.\n"
    "=============================================================="
)


class SPHShell(cmd.Cmd):
    """Interaktywny REPL — 7 komend bez slasha (D-17, Phase 4 dodaje compare)."""

    intro = INTRO
    prompt = 'sph> '  # D-22 — krótkie, bez ANSI

    # ---- __init__ (Phase 8 Plan 08-04) ----
    # NOTE: super().__init__() jest krytyczne — cmd.Cmd inicjalizuje cmdqueue, use_rawinput,
    # readline integration. Bez super() override'y precmd/postcmd nie dostają dispatchu.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tutorial_state = None  # TutorialFlow | None — active gdy do_tutorial wywołane
        self._last_sim_result = None  # set przez do_run/do_compare/do_batch na success path

    # ---- precmd (Phase 8 Plan 08-04, D-05, TUT-02..04) ----
    # Intercept skip/back/repeat/exit BEFORE cmd.Cmd dispatch gdy tutorial active.
    # Zwraca '' żeby short-circuit'ować standardową komendę (Pitfall 1: exit collision).
    def precmd(self, line):
        if self._tutorial_state is None:
            return line
        stripped = line.strip()
        ts = self._tutorial_state

        if stripped == 'skip':
            step = ts.step
            ts.hint_count = 0
            if ts.step < ts.total:
                ts.step += 1
                print(f'⤼ pominięto — krok {step}/{ts.total}')
                self._show_tutorial_step()
            else:
                print(f'⤼ pominięto — krok {step}/{ts.total}. Tutorial zakończony.')
                self._tutorial_state = None
            return ''

        if stripped == 'back':
            if ts.step > 1:
                ts.step -= 1
                ts.hint_count = 0
                print(f'↩ cofnięto do kroku {ts.step}/{ts.total}')
                self._show_tutorial_step()
            else:
                print('Już jesteś na pierwszym kroku.')
            return ''

        if stripped == 'repeat':
            self._show_tutorial_step()
            return ''

        if stripped == 'exit':
            print(f'Tutorial opuszczony na kroku {ts.step}/{ts.total}. '
                  f'Stan REPL zachowany (załadowane strategie, historia). '
                  f'Wpisz `exit` ponownie żeby zakończyć REPL.')
            self._tutorial_state = None
            return ''

        return line

    # ---- postcmd (Phase 8 Plan 08-04, RESEARCH §Pattern 3) ----
    # Verify step completion po wykonaniu komendy. Pitfall 2: skip empty lines
    # (precmd short-circuit produkuje ''). Pitfall 3: consume _last_sim_result.
    def postcmd(self, stop, line):
        if not line.strip() or self._tutorial_state is None or stop:
            return stop
        ts = self._tutorial_state
        result = self._last_sim_result

        passed = check_step(
            ts.step, line.strip(), result,
            STRATEGIES, BUILTIN_STRATEGIES,
            tutorial_flow=ts,
        )

        if passed:
            step = ts.step
            ts.hint_count = 0
            self._last_sim_result = None  # Pitfall 3: consume po verification
            if ts.step < ts.total:
                ts.step += 1
                print(f'\n✓ zaliczone — krok {step}/{ts.total}')
                self._show_tutorial_step()
            else:
                print(f'\n✓ zaliczone — krok {step}/{ts.total}. Tutorial ukończony!')
                self._tutorial_state = None
        else:
            # Hint only when meaningful attempt: sim-producing step (result != None)
            # OR display-only step (2/4/7 — no sim dependency).
            if result is not None or ts.step in (2, 4, 7):
                ts.hint_count += 1
                self._last_sim_result = None  # reset niezależnie od passed/failed
                if ts.hint_count <= ts.MAX_HINTS:
                    self._show_step_hint(ts.step)
                else:
                    print('Wskazówka: Wpisz `skip` żeby przejść do następnego kroku bez weryfikacji.')

        return stop

    # ---- help (override cmd.Cmd auto-help — D-17, CLI-02; +tutorial po Phase 8) ----
    def do_help(self, arg):
        """Wyświetl listę dostępnych komend."""
        print("Dostępne komendy:")
        print("  help                            — Wyświetl tę listę komend.")
        print("  exit                            — Zakończ sesję (alternatywnie Ctrl+D).")
        print("  strategies                      — Wyświetl listę wbudowanych i custom strategii.")
        print("  strategy <nazwa>                — Wyświetl szczegóły strategii (parametry, baseline KPI).")
        print("  tutorial                        — Uruchom interaktywny tutorial v1.1 (≤15 min).")
        print("  custom <ścieżka> [k=v ...]      — Załaduj custom strategię z pliku .py.")
        print("  run <nazwa> [k=v ...]           — Uruchom symulację (built-in lub custom).")
        print("  compare <strategia> [k=v ...]   — Porównaj strategię z i bez RationalAgent (delta KPI).")
        print("  batch <nazwa> --seeds N|lista [k=v ...] — Uruchom strategię na wielu seedach (agregat statystyczny).")

    # ---- exit (D-20, CLI-03) ----
    def do_exit(self, arg):
        """Zakończ sesję."""
        print("Do widzenia.")
        return True

    # ---- EOF / Ctrl+D — deleguje do do_exit (Claude's Discretion: single source of truth) ----
    def do_EOF(self, arg):
        """Obsługa Ctrl+D — zakończ sesję."""
        # Pusta linia, żeby pożegnanie nie skleiło się z resztkowym promptem.
        print('')
        return self.do_exit(arg)

    # ---- strategies (D-29, STRAT-01; D-50 dispatch + [custom] suffix) ----
    def do_strategies(self, arg):
        """Wyświetl listę wbudowanych i custom strategii."""
        print("Dostępne strategie:")
        for name in STRATEGIES.keys():
            # D-50 dispatch namespace: built-in żyją w sphsim.strategies.<name>,
            # custom w sphsim.custom.<name> (D-46 private namespace z loadera).
            if name in BUILTIN_STRATEGIES:
                mod = importlib.import_module(f'sphsim.strategies.{name}')
                description = mod.STRATEGY_META['description']
                # Padding nazwy do 12 znaków, separator em-dash (D-29).
                print(f"  {name:<12}— {description}")
            else:
                mod = importlib.import_module(f'sphsim.custom.{name}')
                description = mod.STRATEGY_META['description']
                # D-50: suffix ` [custom]` po opisie (SC #4 ROADMAP).
                print(f"  {name:<12}— {description} [custom]")

    # ---- strategy <name> (D-25/D-26/D-31/D-32, STRAT-02) ----
    def do_strategy(self, arg):
        """Wyświetl szczegóły strategii: opis, parametry, baseline KPI."""
        name = arg.strip()

        if name == '':
            # D-32 verbatim
            print("Użycie: strategy <nazwa>. Wpisz 'strategies' żeby zobaczyć listę.")
            return

        if name not in STRATEGIES:
            # D-31 — live list z STRATEGIES.keys() (Phase 3 custom strategie naturalnie się pojawią)
            available = ', '.join(STRATEGIES.keys())
            print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
            return

        # Valid name — załaduj metadane dynamicznie (D-50 dispatch namespace).
        ns = 'sphsim.strategies' if name in BUILTIN_STRATEGIES else 'sphsim.custom'
        mod = importlib.import_module(f'{ns}.{name}')
        meta = mod.STRATEGY_META

        # Description section
        print(f"Opis: {meta['description']}")

        # Params section
        print("Parametry:")
        for param_name, param_type, default, desc in meta['params']:
            print(f"  {param_name}: {param_type.__name__} = {default!r} — {desc}")

        # Baseline KPI section (opcjonalne — D-26)
        baseline = meta.get('baseline_kpi')
        if baseline is not None:
            print("Baseline KPI:")
            print(f"  {baseline['invocation']} → avg_val_last100 = {baseline['avg_val_last100']}")

    # ---- custom <path> [k=v ...] (D-37/D-38/D-43/D-46/D-48, STRAT-03) ----
    def do_custom(self, arg):
        """Załaduj custom strategię z pliku .py. Składnia: custom <ścieżka> [param=wartość ...]"""
        # D-43 pozycyjne parsing: split na whitespace; pierwszy token = ścieżka,
        # reszta = tokeny k=v. Ścieżki ze spacjami NIE są wspierane.
        parts = arg.split()
        if not parts:
            print("Użycie: custom <ścieżka> [param=wartość ...].")
            return
        path, *param_tokens = parts

        # D-38 reload detection: sprawdź `sys.modules` PRZED loaderem, bo loader
        # zarejestruje fresh module nadpisując istniejący wpis.
        basename_check = os.path.splitext(os.path.basename(os.path.abspath(os.path.expanduser(path))))[0]
        was_loaded = f'sphsim.custom.{basename_check}' in sys.modules

        # D-48: LoaderError → polski one-liner na stdout (NIE stderr, NIE crash REPL'a).
        try:
            name, fn, meta = load_custom(path)
        except LoaderError as e:
            print(e.args[0])
            return

        try:
            params = parse_params_from_meta(param_tokens, meta, name)
        except LoaderError as e:
            print(e.args[0])
            return

        # D-46: rejestracja w wywołującym (loader jest pure).
        STRATEGIES[name] = fn

        # D-38: reload-aware komunikat (verbatim "Załadowano custom" / "Przeładowano custom").
        if was_loaded:
            print(f"Przeładowano custom strategię '{name}'.")
        else:
            print(f"Załadowano custom strategię '{name}'.")

    # ---- run <name> [k=v ...] (D-41/D-42/D-50) ----
    def do_run(self, arg):
        """Uruchom symulację: run <nazwa> [param=wartość ...]"""
        tokens = arg.split()
        if not tokens:
            # D-42 verbatim
            print("Użycie: run <nazwa> [param=wartość ...]. Wpisz 'strategies' żeby zobaczyć dostępne.")
            return
        name, *kv_tokens = tokens

        if name not in STRATEGIES:
            # D-42 verbatim — live STRATEGIES.keys() (custom widoczne po `custom <path>`).
            available = ', '.join(STRATEGIES.keys())
            print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
            return

        # D-50 dispatch namespace: built-in w sphsim.strategies.<name>,
        # custom w sphsim.custom.<name> (D-46 private namespace z loadera).
        ns = 'sphsim.strategies' if name in BUILTIN_STRATEGIES else 'sphsim.custom'
        mod = importlib.import_module(f'{ns}.{name}')
        meta = mod.STRATEGY_META

        try:
            params = parse_params_from_meta(kv_tokens, meta, name)
        except LoaderError as e:
            print(e.args[0])
            return

        # D-58: agent default-on w REPL run. Opakowuje strategię przed budową SPHSimulator.
        # expected_P pochodzi z params dict (D-54 — wspólne źródło prawdy dla incentive + agenta).
        strategy_fn = wrap_with_agent(STRATEGIES[name], params.get('expected_P', DEFAULT_K0))

        # D-41: build SPHSimulator z DEFAULT_* env params (Phase 5 doda override).
        # Seed=42 hardcoded dla determinizmu w sesji REPL'a.
        sim = SPHSimulator(
            nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, K0=DEFAULT_K0, K1=DEFAULT_K1, F=DEFAULT_F,
            T=DEFAULT_T, kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA,
            phi=DEFAULT_PHI, rho=DEFAULT_RHO,
            strategy_fn=strategy_fn, params=params, seed=42,
        )
        res = sim.run()

        # D-41: format_human wymaga args-like Namespace (strategy/nU/nSUS/T/kappa/alpha/verbose).
        # no_agent=False: defensive consistency z format_json (Plan 03 T-04-20 mitigation).
        # phi/rho/K0/valuation/seed: wymagane przez format_config_header (ENV-03, Pitfall 2 fix).
        # Phase 6 (Pitfall 6 defensive consistency): json=False, compare_agent=False
        # — write_report + markdown.py używają tych atrybutów.
        fake_args = argparse.Namespace(
            strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
            kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
            phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window',
            seed=42, json=False, compare_agent=False,
        )
        # Phase 6 REPORT-01: side-effect raport po sukcesie sim.run().
        report_dir = write_report(fake_args, res, params, DEFAULT_K1, mode='single')
        if report_dir:
            print(f'Raport zapisany do: {report_dir}/report.md', file=sys.stderr)
        print(format_human(fake_args, res, DEFAULT_K1, False))

    # ---- compare <name> [k=v ...] (D-61, AGENT-05) ----
    def do_compare(self, arg):
        """Porównaj strategię z i bez RationalAgent: compare <nazwa> [param=wartość ...]"""
        tokens = arg.split()
        if not tokens:
            # D-61 — komunikat identyczny w stylu do do_run D-42.
            print("Użycie: compare <nazwa> [param=wartość ...]. Wpisz 'strategies' żeby zobaczyć dostępne.")
            return
        name, *kv_tokens = tokens

        if name not in STRATEGIES:
            # D-31 style — live STRATEGIES.keys() (custom widoczne po `custom <path>`).
            available = ', '.join(STRATEGIES.keys())
            print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
            return

        # D-50 dispatch namespace: built-in w sphsim.strategies.<name>,
        # custom w sphsim.custom.<name> (D-46 private namespace z loadera).
        ns = 'sphsim.strategies' if name in BUILTIN_STRATEGIES else 'sphsim.custom'
        mod = importlib.import_module(f'{ns}.{name}')
        meta = mod.STRATEGY_META

        try:
            params = parse_params_from_meta(kv_tokens, meta, name)
        except LoaderError as e:
            print(e.args[0])
            return

        # D-54: expected_P pochodzi z params dict (wspólne źródło prawdy).
        raw_strategy_fn = STRATEGIES[name]
        expected_P = params.get('expected_P', DEFAULT_K0)

        # D-61: oba run'y z tym samym seed=42 (Claude's Discretion — determinizm porównania).
        common = dict(
            nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, K0=DEFAULT_K0, K1=DEFAULT_K1, F=DEFAULT_F,
            T=DEFAULT_T, kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA,
            phi=DEFAULT_PHI, rho=DEFAULT_RHO, params=params, seed=42,
        )

        # Run 1: z agentem (D-58 wrapper default-on).
        sim_with = SPHSimulator(strategy_fn=wrap_with_agent(raw_strategy_fn, expected_P), **common)
        res_with = sim_with.run()

        # Run 2: bez agenta (surowa strategia).
        sim_without = SPHSimulator(strategy_fn=raw_strategy_fn, **common)
        res_without = sim_without.run()

        # D-62: 5 KPI delta dict.
        KPIS = ['avg_val_last100', 'cum_val_total', 'avg_net_profit', 'delivery_ratio', 'avg_providers_l100']
        comparison_block = {
            'with_agent': {k: v for k, v in res_with.items() if k not in ('history', 'devices')},
            'without_agent': {k: v for k, v in res_without.items() if k not in ('history', 'devices')},
            'delta': {k: res_with[k] - res_without[k] for k in KPIS},
            'agent_helps': res_with['avg_net_profit'] > res_without['avg_net_profit'],
        }

        # Render przez format_human → format_compare (Plan 03 dispatcher).
        # fake_args musi mieć no_agent=False (T-04-20 defensive consistency).
        # phi/rho/K0/valuation/seed: wymagane przez format_config_header (ENV-03, Pitfall 2 fix).
        # Phase 6 PLOT-02: _with_agent_full carries history dla compare-mode PNG (RESEARCH §N.1).
        res_combined = {
            'comparison': comparison_block,
            '_with_agent_full': res_with,
        }
        # Phase 6 (Pitfall 6 defensive consistency): json=False, compare_agent=True (explicit
        # compare-mode marker dla markdown.py _render_strategy_params dispatch).
        # Phase 7 (Pitfall 7 defensive consistency): expected_P=params.get(...) — choć compare
        # nie używa go w fake_args (wrap inline), trzymamy w Namespace żeby Pitfall 7 audit
        # invariant (PATTERNS §4) trzymał się jednolicie w obu trybach REPL'a.
        fake_args = argparse.Namespace(
            strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
            kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
            phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window',
            seed=42, json=False, compare_agent=True,
            expected_P=params.get('expected_P', DEFAULT_K0),
        )
        # Phase 6 REPORT-03: side-effect raport porównawczy.
        report_dir = write_report(fake_args, res_combined, params, DEFAULT_K1, mode='compare')
        if report_dir:
            print(f'Raport porównawczy zapisany do: {report_dir}/report.md', file=sys.stderr)
        print(format_human(fake_args, res_combined, DEFAULT_K1, False))

    # ---- batch <name> --seeds N|lista [k=v ...] (Phase 7 BATCH-01, RESEARCH §C.5) ----
    def do_batch(self, arg):
        """Uruchom strategię na wielu seedach: batch <nazwa> --seeds N|lista [param=wartość ...]"""
        tokens = arg.split()
        if not tokens:
            # Mirror do_run/do_compare empty-arg style; jedna polska linia użycia.
            print("Użycie: batch <nazwa> --seeds N|lista [param=wartość ...]. "
                  "Np.: batch naive --seeds 10  |  batch naive --seeds 1,5,42 zeta=0.75")
            return

        # Separate `--seeds VALUE` from name + k=v tokens. While-loop pattern z RESEARCH §C.5
        # — obsługuje dowolną kolejność tokenów (np. `naive --seeds 5 zeta=0.75` lub `--seeds 5 naive`).
        seeds_value = None
        other_tokens = []
        i = 0
        while i < len(tokens):
            if tokens[i] == '--seeds' and i + 1 < len(tokens):
                seeds_value = tokens[i + 1]
                i += 2
            else:
                other_tokens.append(tokens[i])
                i += 1

        if seeds_value is None:
            print("Komenda `batch` wymaga --seeds N lub --seeds lista (np. --seeds 1,5,42).")
            return

        # Reuse _parse_seeds_list — single source of truth z sphsim/cli/args.py (Plan 07-02).
        # Deferred import: zero cold-start cost dla użytkowników, którzy nigdy nie wywołują batch.
        # Pitfall 2 — REPL must NEVER crash; argparse.ArgumentTypeError catch jest krytyczny.
        try:
            from sphsim.cli.args import _parse_seeds_list
            seeds_list = _parse_seeds_list(seeds_value)
        except argparse.ArgumentTypeError as e:
            print(str(e))
            return

        if not other_tokens:
            print("Komenda `batch` wymaga nazwy strategii. Wpisz 'strategies' żeby zobaczyć dostępne.")
            return
        name, *kv_tokens = other_tokens

        # Strategy validation (verbatim z do_compare:246-262 — D-31 styl).
        if name not in STRATEGIES:
            available = ', '.join(STRATEGIES.keys())
            print(f"Strategia '{name}' nie istnieje. Dostępne: {available}.")
            return

        # D-50 dispatch namespace: built-in w sphsim.strategies.<name>,
        # custom w sphsim.custom.<name> (D-46 private namespace z loadera).
        ns = 'sphsim.strategies' if name in BUILTIN_STRATEGIES else 'sphsim.custom'
        mod = importlib.import_module(f'{ns}.{name}')
        meta = mod.STRATEGY_META
        try:
            params = parse_params_from_meta(kv_tokens, meta, name)
        except LoaderError as e:
            print(e.args[0])
            return

        # fake_args — ALL fields wymagane przez write_batch_report / render_batch_report /
        # format_config_header / format_batch_summary / run_batch (PATTERNS §4 field audit).
        # Pitfall 7 (D-54 propagation): expected_P z params.get fallback do DEFAULT_K0 — NIE
        # hardcode'ujemy 100.0, żeby custom strategie deklarujące expected_P w meta propagowały.
        fake_args = argparse.Namespace(
            strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
            kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
            phi=DEFAULT_PHI, rho=DEFAULT_RHO, K0=DEFAULT_K0, valuation='window',
            seed=42, json=False, compare_agent=False,
            # Phase 7 additions:
            batch=True,
            seeds=seeds_list,
            expected_P=params.get('expected_P', DEFAULT_K0),
        )

        # Deferred imports — single source of truth z CLI path (main.py:93-101).
        from sphsim.batch import run_batch
        from sphsim.report import write_batch_report
        from sphsim.cli.output import format_batch_summary

        raw_strategy_fn = STRATEGIES[name]
        per_seed_results, aggregate = run_batch(fake_args, raw_strategy_fn, params, DEFAULT_K1)
        report_dir = write_batch_report(fake_args, per_seed_results, aggregate, params,
                                        DEFAULT_K1, seeds_list)
        if report_dir:
            print(f'Raport batchowy zapisany do: {report_dir}/report.md', file=sys.stderr)
        print(format_batch_summary(fake_args, aggregate, DEFAULT_K1))

    # ---- tutorial helpers (Phase 8 Plan 08-04) ----
    def _show_tutorial_step(self):
        """Wyświetl bieżący krok tutoriala (tytuł + opis). Wywoływane z do_tutorial,
        precmd (skip/back/repeat) oraz postcmd (auto-advance po passed)."""
        ts = self._tutorial_state
        if ts is None:
            return
        task = STEP_TASKS.get(ts.step)
        if task is None:
            print(f'[BŁĄD] Nieznany krok {ts.step} — przerywam tutorial.')
            self._tutorial_state = None
            return
        print(f'\n[krok {ts.step}/{ts.total} — {task.title}]')
        print('══════════════════════════════════════════════════════════')
        print(task.description)
        print('══════════════════════════════════════════════════════════')
        # Note: step 6 jest soft-pass informational step (Plan 03 / Open Question #2
        # resolution). Zero filesystem snapshot — check_step(6, line, ...) zwraca
        # True dla dowolnej non-empty linii.

    def _show_step_hint(self, step_n):
        """Wyświetl hint dla bieżącego kroku gdy postcmd failed verification."""
        task = STEP_TASKS.get(step_n)
        if task is None:
            return
        print(f'\nNie rozpoznano polecenia dla kroku {step_n}. Oczekiwano:')
        print(f'  {task.expected_command_hint}')
        print('Spróbuj jeszcze raz lub wpisz `skip` żeby pominąć.')

    # ---- tutorial (Phase 8 Plan 08-04, TUT-01) ----
    def do_tutorial(self, arg):
        """Uruchom interaktywny tutorial v1.1 (~8 kroków, ≤15 min)."""
        if self._tutorial_state is not None:
            print('Tutorial już jest aktywny. Wpisz `repeat` żeby zobaczyć bieżący krok, `exit` żeby wyjść.')
            return
        self._tutorial_state = TutorialFlow()
        # Header banner explains exit-word disambiguation (Researcher Open Question #2).
        print(
            '\n'
            '══════════════════════════════════════════════════════════\n'
            '  INTERAKTYWNY TUTORIAL SPH SYMULATORA v1.1\n'
            '  ~8 kroków, ≤15 minut\n'
            '  Sterowanie: skip | back | repeat | exit\n'
            '  `exit` wraca do REPL (stan zachowany), nie kończy sesji.\n'
            '  Wpisz `exit` ponownie żeby zakończyć REPL.\n'
            '══════════════════════════════════════════════════════════'
        )
        self._show_tutorial_step()

    # ---- default — nieznana komenda (D-30) ----
    def default(self, line):
        """Override cmd.Cmd default — Polski komunikat dla nieznanych komend."""
        # cmd.Cmd przekazuje surową linię (bez trailing newline w większości wersji),
        # ale dla bezpieczeństwa stripujemy.
        text = line.strip() if isinstance(line, str) else str(line)
        print(f"Nieznana komenda: '{text}'. Wpisz 'help' żeby zobaczyć dostępne komendy.")


def _write_history_silent():
    """Helper dla atexit — zapis historii, cicho ignoruj błędy I/O.

    Sandboxowane / read-only środowiska (CI, containers) mogą blokować
    zapis do ~/.sphsim_history — to nie powinno zatruwać zwykłego wyjścia
    z REPL'a.
    """
    try:
        readline.write_history_file(HISTORY_FILE)
    except OSError:
        pass


def run_repl(start_in_tutorial: bool = False):
    """Top-level entry-point REPL'a.

    Ładuje historię readline (cicho ignoruje FileNotFoundError i pokrewne
    OSError — D-19; Rule 2 robustness dla sandboxed środowisk),
    rejestruje atexit handler do zapisu historii, uruchamia cmdloop().

    Args:
        start_in_tutorial: gdy True (Phase 8 Plan 08-04, TUT-05), wstrzykuje
            'tutorial' do cmdqueue przed cmdloop() — REPL natychmiast wchodzi
            w tryb tutorial po wyświetleniu INTRO banneru. Wywoływane przez
            main.py gdy args.tutorial=True (Plan 08-02 wiring).
    """
    try:
        readline.read_history_file(HISTORY_FILE)
    except FileNotFoundError:
        pass  # D-19: silent na pierwsze uruchomienie
    except OSError:
        pass  # Rule 2: sandbox/permission errors — REPL działa bez historii

    atexit.register(_write_history_silent)

    shell = SPHShell()
    if start_in_tutorial:
        # cmdqueue jest konsumowany PRZED stdin (cmd.Cmd contract — RESEARCH §Pattern 6).
        # INTRO banner wyświetla się normalnie, potem dispatcher uruchamia do_tutorial.
        shell.cmdqueue.append('tutorial')
    shell.cmdloop()
