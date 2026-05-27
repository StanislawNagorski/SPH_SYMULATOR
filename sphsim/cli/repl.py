"""REPL — tryb interaktywny SPH symulatora (Phase 2 + Phase 3 + Phase 4 agent).

Klasa SPHShell(cmd.Cmd) udostępnia 7 komend bez prefiksu '/':
  - help        — lista komend (D-17, CLI-02)
  - exit        — zakończ sesję (D-20, CLI-03)
  - strategies  — lista wbudowanych i custom strategii (D-29/D-50, STRAT-01)
  - strategy <nazwa>             — szczegóły strategii (D-25/D-26, STRAT-02)
  - custom <ścieżka> [k=v ...]   — załaduj custom strategię z pliku .py (D-37/D-38, STRAT-03)
  - run <nazwa> [k=v ...]        — uruchom symulację built-in lub custom (D-41/D-42)
  - compare <nazwa> [k=v ...]    — porównaj strategię z/bez RationalAgent (D-61, AGENT-05)

Funkcja run_repl() jest jedynym publicznym entry-pointem — wywoływana z
sphsim/cli/main.py gdy args.interactive jest True (D-15).

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

    # ---- help (override cmd.Cmd auto-help — D-17, CLI-02; 6 komend po Phase 3) ----
    def do_help(self, arg):
        """Wyświetl listę dostępnych komend."""
        print("Dostępne komendy:")
        print("  help                            — Wyświetl tę listę komend.")
        print("  exit                            — Zakończ sesję (alternatywnie Ctrl+D).")
        print("  strategies                      — Wyświetl listę wbudowanych i custom strategii.")
        print("  strategy <nazwa>                — Wyświetl szczegóły strategii (parametry, baseline KPI).")
        print("  custom <ścieżka> [k=v ...]      — Załaduj custom strategię z pliku .py.")
        print("  run <nazwa> [k=v ...]           — Uruchom symulację (built-in lub custom).")
        print("  compare <nazwa> [k=v ...]       — Porównaj strategię z i bez RationalAgent (delta KPI).")

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
        fake_args = argparse.Namespace(
            strategy=name, nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, T=DEFAULT_T,
            kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, verbose=False, no_agent=False,
        )
        print(format_human(fake_args, res, DEFAULT_K1, False))

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


def run_repl():
    """Top-level entry-point REPL'a.

    Ładuje historię readline (cicho ignoruje FileNotFoundError i pokrewne
    OSError — D-19; Rule 2 robustness dla sandboxed środowisk),
    rejestruje atexit handler do zapisu historii, uruchamia cmdloop().
    """
    try:
        readline.read_history_file(HISTORY_FILE)
    except FileNotFoundError:
        pass  # D-19: silent na pierwsze uruchomienie
    except OSError:
        pass  # Rule 2: sandbox/permission errors — REPL działa bez historii

    atexit.register(_write_history_silent)

    SPHShell().cmdloop()
