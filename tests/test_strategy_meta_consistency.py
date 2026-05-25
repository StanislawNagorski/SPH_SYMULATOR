"""
Invariant test (D-25): STRATEGY_META['params'] ↔ argparse add_argument.

Dla każdej z 5 wbudowanych strategii (`sphsim.strategies.STRATEGIES`) sprawdza,
że każdy parametr zadeklarowany w `STRATEGY_META['params']` ma odpowiadające
`add_argument` w `sphsim/cli/args.py` z identyczną nazwą (dest), typem
(identity check on the type callable) i defaultem (equality).

Brak takiego testu sprawia, że invariant D-25 jest tylko aspiracją —
ktoś mógłby zmienić `default=0.5` na `default=0.6` w argparse bez aktualizacji
`STRATEGY_META`, a REPL `strategy <name>` pokazałby użytkownikowi błędną wartość.

Test używa wyłącznie stdlib (unittest + importlib + argparse + sys + unittest.mock)
— zero zależności (PROJECT.md constraint stdlib-only utrzymany).
"""
import argparse
import importlib
import os
import sys
import unittest
from unittest.mock import patch

# Pozwól uruchamiać test bezpośrednio: `python tests/test_strategy_meta_consistency.py`
# (bez tego sys.path nie zawiera project root i `import sphsim.cli.args` failuje
# ModuleNotFoundError). Przy uruchomieniu przez `python -m unittest ...` z root'u
# linia jest no-op'em (root już w sys.path).
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _capture_parser():
    """
    Zwraca instancję `argparse.ArgumentParser` zbudowaną przez
    `sphsim.cli.args.parse_args()`, bez wykonania faktycznego parsowania
    sys.argv ani crashowania na required mutex group.

    Mechanika (Option C z plan <interfaces>):
    1. Monkey-patch `argparse.ArgumentParser.parse_args` tak, by przed
       wywołaniem oryginału zapisać `self` (instancję parsera) do dict.
    2. Podstawiamy `sys.argv = ['x', '--strategy', 'naive']` żeby spełnić
       mutex `--interactive | --strategy` (D-27) — wybieramy `--strategy naive`
       jako waliding choice z STRATEGIES.
    3. Wymuszamy świeży import modułu (`sphsim.cli.args` może być już w
       sys.modules po wcześniejszych testach), więc `parse_args()` zbuduje
       parser de novo i monkey-patched `parse_args` zarejestruje instancję.
    """
    captured = {}
    original = argparse.ArgumentParser.parse_args

    def capture(self, *a, **kw):
        captured['parser'] = self
        return original(self, *a, **kw)

    old_argv = sys.argv
    sys.argv = ['x', '--strategy', 'naive']
    try:
        with patch.object(argparse.ArgumentParser, 'parse_args', capture):
            # Import wewnątrz with-block, żeby na pewno trafić w patcha
            # (parse_args jest funkcją modułu, ale wywołuje metodę klasy).
            from sphsim.cli.args import parse_args
            parse_args()
    finally:
        sys.argv = old_argv

    if 'parser' not in captured:
        raise RuntimeError(
            "Nie udało się przechwycić ArgumentParser — "
            "sphsim.cli.args.parse_args() nie wywołało parser.parse_args()."
        )
    return captured['parser']


class TestStrategyMetaConsistency(unittest.TestCase):
    """
    Weryfikuje invariant D-25 dla wszystkich 5 wbudowanych strategii.

    Dla każdego parametru w STRATEGY_META['params'] (krotka 4-elementowa
    (name, type, default, description)) musi istnieć add_argument
    w argparse z tą samą nazwą (dest), typem (identyczność) i defaultem
    (równość).
    """

    def test_strategy_meta_matches_argparse(self):
        """STRATEGY_META params per strategia ↔ argparse add_argument (D-25)."""
        parser = _capture_parser()
        actions_by_dest = {a.dest: a for a in parser._actions}

        from sphsim.strategies import STRATEGIES

        # Asercja sanity: 5 strategii znanych z Phase 1.
        self.assertEqual(
            set(STRATEGIES.keys()),
            {'naive', 'threshold', 'phase_prob', 'incentive', 'adaptive'},
            msg='STRATEGIES keys odbiegają od oczekiwanych 5 strategii Phase 1.'
        )

        for name in STRATEGIES.keys():
            mod = importlib.import_module(f'sphsim.strategies.{name}')
            self.assertTrue(
                hasattr(mod, 'STRATEGY_META'),
                msg=f"{name}: moduł sphsim.strategies.{name} nie eksportuje STRATEGY_META",
            )
            meta = mod.STRATEGY_META
            self.assertIsInstance(
                meta, dict,
                msg=f"{name}: STRATEGY_META musi być dict, otrzymano {type(meta).__name__}",
            )
            self.assertIn(
                'params', meta,
                msg=f"{name}: STRATEGY_META brakuje klucza 'params'",
            )
            params = meta['params']
            self.assertIsInstance(
                params, list,
                msg=f"{name}: STRATEGY_META['params'] musi być list, otrzymano {type(params).__name__}",
            )

            for tup in params:
                # Sprawdzamy kształt krotki przed unpackiem żeby błąd był czytelny.
                self.assertEqual(
                    len(tup), 4,
                    msg=(
                        f"{name}: każdy element STRATEGY_META['params'] musi być "
                        f"krotką 4-elementową (name, type, default, description), "
                        f"otrzymano {tup!r}"
                    ),
                )
                pname, ptype, pdefault, pdesc = tup

                # Missing-in-argparse
                self.assertIn(
                    pname, actions_by_dest,
                    msg=(
                        f"{name}: STRATEGY_META declares '{pname}' but argparse "
                        f"has no such add_argument"
                    ),
                )
                action = actions_by_dest[pname]

                # Type-mismatch
                self.assertIs(
                    action.type, ptype,
                    msg=(
                        f"{name}/{pname}: STRATEGY_META type="
                        f"{getattr(ptype, '__name__', ptype)}, argparse type="
                        f"{getattr(action.type, '__name__', action.type)}"
                    ),
                )

                # Default-mismatch
                self.assertEqual(
                    action.default, pdefault,
                    msg=(
                        f"{name}/{pname}: STRATEGY_META default={pdefault!r}, "
                        f"argparse default={action.default!r}"
                    ),
                )

                # Sanity: opis musi być str (nie sprawdzamy treści — to nie jest
                # invariant D-25, tylko higiena kontraktu STRATEGY_META).
                self.assertIsInstance(
                    pdesc, str,
                    msg=(
                        f"{name}/{pname}: STRATEGY_META description musi być str, "
                        f"otrzymano {type(pdesc).__name__}"
                    ),
                )


if __name__ == '__main__':
    unittest.main()
