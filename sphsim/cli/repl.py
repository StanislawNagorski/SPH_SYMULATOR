"""REPL — tryb interaktywny SPH symulatora (Phase 2).

Klasa SPHShell(cmd.Cmd) udostępnia 4 komendy bez prefiksu '/':
  - help        — lista komend (D-17, CLI-02)
  - exit        — zakończ sesję (D-20, CLI-03)
  - strategies  — lista wbudowanych strategii (D-29, STRAT-01)
  - strategy <nazwa>  — szczegóły strategii: opis, parametry, baseline KPI (D-25/D-26, STRAT-02)

Funkcja run_repl() jest jedynym publicznym entry-pointem — wywoływana z
sphsim/cli/main.py gdy args.interactive jest True (D-15).

Wszystkie komunikaty użytkownika po polsku (PROJECT.md constraint).
Stdlib only: cmd + readline + importlib + os + atexit (D-18, D-19).
"""
import atexit
import cmd
import importlib
import os
import readline  # noqa: F401 — side effect: cmd.Cmd używa readline dla line-editing na POSIX

from sphsim.strategies import STRATEGIES


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
    """Interaktywny REPL — 4 komendy bez slasha (D-17)."""

    intro = INTRO
    prompt = 'sph> '  # D-22 — krótkie, bez ANSI

    # ---- help (override cmd.Cmd auto-help — D-17, CLI-02) ----
    def do_help(self, arg):
        """Wyświetl listę dostępnych komend."""
        print("Dostępne komendy:")
        print("  help               — Wyświetl tę listę komend.")
        print("  exit               — Zakończ sesję (alternatywnie Ctrl+D).")
        print("  strategies         — Wyświetl listę wbudowanych strategii.")
        print("  strategy <nazwa>   — Wyświetl szczegóły strategii (parametry, baseline KPI).")

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

    # ---- strategies (D-29, STRAT-01) ----
    def do_strategies(self, arg):
        """Wyświetl listę wbudowanych strategii."""
        print("Dostępne strategie:")
        for name in STRATEGIES.keys():
            mod = importlib.import_module(f'sphsim.strategies.{name}')
            description = mod.STRATEGY_META['description']
            # Padding nazwy do 12 znaków, separator em-dash z otaczającymi spacjami (D-29).
            print(f"  {name:<12}— {description}")

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

        # Valid name — załaduj metadane dynamicznie.
        mod = importlib.import_module(f'sphsim.strategies.{name}')
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
