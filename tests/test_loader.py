"""
Unit tests dla sphsim.strategies.loader (Phase 3, D-46 / D-47 / D-49).

Pokrywa 4 warstwy walidacji loadera + happy path + reload + collision + parser:
  1. Import errors (SyntaxError, runtime exception w top-level)
  2. Brak / non-callable strategii
  3. Sygnatura mismatch + escape przez *args
  4. STRATEGY_META schema violations
  5. Happy path: load + return (name, fn, meta)
  6. Reload (D-38): drugie wywołanie — fresh spec, sys.modules replaced
     (RESEARCH Pitfall #1)
  7. Collision z BUILTIN_STRATEGIES (D-49) → LoaderError
  8. sys.modules cleanup po failed exec (RESEARCH Pitfall #2)
  9. parse_params_from_meta: typed conversion, unknown key, bad value,
     malformed token warning, value-with-`=` (D-39/D-40/D-43)

Każdy test izolowany przez setUp/tearDown z tempfile.mkdtemp + cleanup
`sphsim.custom.*` z sys.modules + restore snapshot STRATEGIES.

Stdlib only: unittest + tempfile + textwrap + os + sys + time + shutil
+ io + contextlib (zgodne z PROJECT.md constraint stdlib-only).
"""
import io
import os
import shutil
import sys
import tempfile
import textwrap
import time
import unittest
from contextlib import redirect_stdout

# Pozwól uruchamiać test bezpośrednio: `python tests/test_loader.py`
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sphsim.strategies import STRATEGIES, BUILTIN_STRATEGIES
from sphsim.strategies.loader import (
    EXPECTED_PARAMS,
    LoaderError,
    load_custom,
    parse_params_from_meta,
)


class TestLoader(unittest.TestCase):
    """4-warstwowa walidacja loadera + reload + collision + param parser
    (D-46/D-47/D-49/D-39/D-40/D-43)."""

    def setUp(self):
        # Izolowany katalog roboczy per test — bez kolizji nazw między testami.
        self.tmpdir = tempfile.mkdtemp(prefix='test_loader_')
        # Snapshot STRATEGIES — jeśli który test by zarejestrował coś runtime'owo
        # (loader sam tego NIE robi per D-46, ale defensywnie).
        self._snapshot_strategies = set(STRATEGIES.keys())

    def tearDown(self):
        # Posprzątaj tempdir.
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        # Usuń ewentualne wpisy STRATEGIES dodane podczas testu.
        for k in list(STRATEGIES.keys()):
            if k not in self._snapshot_strategies:
                del STRATEGIES[k]
        # Usuń ewentualne moduły z syntetycznego namespace sphsim.custom.*
        for k in list(sys.modules.keys()):
            if k.startswith('sphsim.custom.'):
                del sys.modules[k]

    # ── Helpers ────────────────────────────────────────────────────────────
    def _write(self, name, content):
        """Zapisz plik `name` w tempdir z `content` po dedent. Zwraca path."""
        path = os.path.join(self.tmpdir, name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(textwrap.dedent(content))
        return path

    def _write_valid(self, basename):
        """Minimal valid strategy file — tam gdzie szczegóły walidacji nie są pointem."""
        content = f"""\
            def strategy_{basename}(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'

            STRATEGY_META = {{
                'description': 'test',
                'params': [],
                'baseline_kpi': None,
            }}
        """
        return self._write(f'{basename}.py', content)

    # ── Happy path ─────────────────────────────────────────────────────────
    def test_happy_path_loads_validates_returns(self):
        """load_custom dla validnego pliku zwraca (basename, callable, dict z description)."""
        path = self._write_valid('happy')
        name, fn, meta = load_custom(path)
        self.assertEqual(name, 'happy', msg=f'basename should be "happy", got {name!r}')
        self.assertTrue(callable(fn), msg='Returned fn must be callable')
        self.assertEqual(meta['description'], 'test',
                         msg=f'meta description should be "test", got {meta["description"]!r}')
        self.assertEqual(meta['params'], [], msg='Empty params expected for minimal valid')
        self.assertIsNone(meta['baseline_kpi'], msg='baseline_kpi should be None')

    # ── D-47 Layer 1: Import errors ────────────────────────────────────────
    def test_syntax_error_in_user_file(self):
        """SyntaxError w user file → LoaderError z 'Błąd podczas importu' i 'SyntaxError'."""
        path = self._write('syntaxbroken.py', "def broken(:\n    pass\n")
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        msg = cm.exception.args[0]
        self.assertIn('Błąd podczas importu', msg,
                      msg=f'LoaderError msg should mention "Błąd podczas importu", got: {msg!r}')
        self.assertIn('SyntaxError', msg,
                      msg=f'LoaderError msg should mention "SyntaxError", got: {msg!r}')

    def test_path_not_exists(self):
        """Nieistniejąca ścieżka → LoaderError z 'Plik nie istnieje'."""
        path = os.path.join(self.tmpdir, 'does_not_exist.py')
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        msg = cm.exception.args[0]
        self.assertIn('Plik nie istnieje', msg,
                      msg=f'LoaderError should mention "Plik nie istnieje", got: {msg!r}')

    def test_rejects_non_py_extension(self):
        """Plik .txt → LoaderError 'nie wygląda na plik Pythona' (Pitfall #3 spec=None)."""
        path = self._write('not_python.txt', "def strategy_not_python(dev,l,s,phi,kappa,rho,h,p): return 'COMMIT'\n")
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        msg = cm.exception.args[0]
        self.assertIn('nie wygląda na plik Pythona', msg,
                      msg=f'LoaderError should mention "nie wygląda na plik Pythona", got: {msg!r}')

    # ── D-47 Layer 2: Missing function / non-callable ──────────────────────
    def test_missing_function(self):
        """Brak strategy_<basename> → LoaderError z 'Brak funkcji' + 8 nazw args."""
        path = self._write('no_fn.py', """\
            STRATEGY_META = {'description':'x', 'params':[], 'baseline_kpi':None}
        """)
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        msg = cm.exception.args[0]
        self.assertIn("Brak funkcji 'strategy_no_fn'", msg,
                      msg=f'LoaderError should mention missing function name, got: {msg!r}')
        # 8 nazw arg muszą być w komunikacie żeby user wiedział co naprawić.
        for arg_name in EXPECTED_PARAMS:
            self.assertIn(arg_name, msg,
                          msg=f'LoaderError should list expected arg "{arg_name}", got: {msg!r}')

    def test_non_callable_attribute(self):
        """strategy_X = 42 (non-callable) → LoaderError z 'Brak funkcji' (callable check przed signature)."""
        path = self._write('not_callable.py', """\
            strategy_not_callable = 42
            STRATEGY_META = {'description':'x', 'params':[], 'baseline_kpi':None}
        """)
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        msg = cm.exception.args[0]
        self.assertIn("Brak funkcji 'strategy_not_callable'", msg,
                      msg=f'LoaderError should mention "Brak funkcji" for non-callable, got: {msg!r}')

    # ── D-47 Layer 3: Signature mismatch + var-pos escape ──────────────────
    def test_wrong_signature(self):
        """def strategy_wrong_sig(dev, x, y, z) → LoaderError 'Oczekiwana: (dev, l, s, ...)'."""
        path = self._write('wrong_sig.py', """\
            def strategy_wrong_sig(dev, x, y, z):
                return 'COMMIT'
            STRATEGY_META = {'description':'x', 'params':[], 'baseline_kpi':None}
        """)
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        msg = cm.exception.args[0]
        self.assertIn('Oczekiwana: (dev, l, s, phi, kappa, rho, h, p)', msg,
                      msg=f'LoaderError should mention expected signature, got: {msg!r}')

    def test_var_positional_accepted(self):
        """def strategy_var_pos(*args) → load_custom succeeds (wrapper escape)."""
        path = self._write('var_pos.py', """\
            def strategy_var_pos(*args):
                return 'COMMIT'
            STRATEGY_META = {'description':'wrapper', 'params':[], 'baseline_kpi':None}
        """)
        name, fn, meta = load_custom(path)
        self.assertEqual(name, 'var_pos',
                         msg=f'var_pos wrapper should load — basename "var_pos", got {name!r}')
        self.assertTrue(callable(fn), msg='var_pos wrapper fn must be callable')
        self.assertEqual(meta['description'], 'wrapper')

    # ── D-47 Layer 4: STRATEGY_META validation ─────────────────────────────
    def test_missing_meta(self):
        """Brak STRATEGY_META → LoaderError zawierający 'STRATEGY_META'."""
        path = self._write('no_meta.py', """\
            def strategy_no_meta(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'
        """)
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        msg = cm.exception.args[0]
        self.assertIn('STRATEGY_META', msg,
                      msg=f'LoaderError should mention STRATEGY_META missing, got: {msg!r}')

    def test_malformed_meta_not_dict(self):
        """STRATEGY_META = 'string' → LoaderError zawierający 'musi być dict'."""
        path = self._write('bad_meta_str.py', """\
            def strategy_bad_meta_str(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'
            STRATEGY_META = "not a dict"
        """)
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        msg = cm.exception.args[0]
        self.assertIn('musi być dict', msg,
                      msg=f'LoaderError should mention "musi być dict", got: {msg!r}')

    def test_meta_missing_keys(self):
        """STRATEGY_META = {'description':'x'} → LoaderError z 'brakuje klucza'."""
        path = self._write('partial_meta.py', """\
            def strategy_partial_meta(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'
            STRATEGY_META = {'description': 'x'}
        """)
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        msg = cm.exception.args[0]
        self.assertIn('brakuje klucza', msg,
                      msg=f'LoaderError should mention "brakuje klucza", got: {msg!r}')

    def test_meta_params_not_list(self):
        """STRATEGY_META['params'] = 'not list' → LoaderError."""
        path = self._write('params_not_list.py', """\
            def strategy_params_not_list(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'
            STRATEGY_META = {
                'description': 'x',
                'params': 'not list',
                'baseline_kpi': None,
            }
        """)
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        msg = cm.exception.args[0]
        self.assertIn("musi być list", msg,
                      msg=f'LoaderError should mention params "musi być list", got: {msg!r}')

    def test_meta_param_tuple_wrong_arity(self):
        """params containing 3-tuple → LoaderError 'krotką 4-elementową'."""
        path = self._write('bad_tuple.py', """\
            def strategy_bad_tuple(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'
            STRATEGY_META = {
                'description': 'x',
                'params': [('foo', int, 1)],
                'baseline_kpi': None,
            }
        """)
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        msg = cm.exception.args[0]
        self.assertIn('krotką 4-elementową', msg,
                      msg=f'LoaderError should mention "krotką 4-elementową", got: {msg!r}')

    # ── D-49: Builtin name collision ───────────────────────────────────────
    def test_builtin_name_collision(self):
        """Plik nazwany naive.py → LoaderError 'koliduje z wbudowaną'."""
        path = self._write_valid('naive')
        with self.assertRaises(LoaderError) as cm:
            load_custom(path)
        msg = cm.exception.args[0]
        self.assertIn('koliduje z wbudowaną', msg,
                      msg=f'LoaderError should mention "koliduje z wbudowaną", got: {msg!r}')

    # ── D-38: Reload picks up changes (Pitfall #1) ─────────────────────────
    def test_reload_picks_up_changes(self):
        """load_custom dwa razy na tym samym pliku — drugi raz widzi nowy kod (fresh spec)."""
        path = os.path.join(self.tmpdir, 'reload_me.py')
        v1 = textwrap.dedent("""\
            def strategy_reload_me(dev, l, s, phi, kappa, rho, h, p):
                return 'COMMIT'
            STRATEGY_META = {'description': 'v1', 'params': [], 'baseline_kpi': None}
        """)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(v1)
        _, _, meta1 = load_custom(path)
        self.assertEqual(meta1['description'], 'v1',
                         msg=f'First load should see v1, got {meta1["description"]!r}')

        # Sleep żeby mtime się zmienił na ext4/HFS+ (1s resolution).
        time.sleep(1.1)

        v2 = textwrap.dedent("""\
            def strategy_reload_me(dev, l, s, phi, kappa, rho, h, p):
                return 'ABSTAIN'
            STRATEGY_META = {'description': 'v2', 'params': [], 'baseline_kpi': None}
        """)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(v2)
        _, _, meta2 = load_custom(path)
        self.assertEqual(meta2['description'], 'v2',
                         msg=(f'Second load should see v2 after edit (D-38 fresh spec), '
                              f'got {meta2["description"]!r} — possibly cached/reload bug'))

    # ── Pitfall #2: sys.modules cleanup after failed exec ──────────────────
    def test_failed_load_cleans_sys_modules(self):
        """Plik rzucający Exception top-level → LoaderError + sys.modules zombie cleanup."""
        path = self._write('boom.py', """\
            raise ZeroDivisionError('init')
        """)
        with self.assertRaises(LoaderError):
            load_custom(path)
        self.assertNotIn('sphsim.custom.boom', sys.modules,
                         msg=('sys.modules["sphsim.custom.boom"] should be cleaned up '
                              'after failed exec (Pitfall #2)'))

    # ── parse_params_from_meta tests (D-39/D-40/D-43) ──────────────────────
    def test_param_typed_from_meta(self):
        """parse_params: 'zeta=0.75' + 'max_phase=4' → typed dict z float/int."""
        meta = {
            'description': 'x',
            'params': [
                ('zeta', float, 0.5, 'd'),
                ('max_phase', int, 3, 'd'),
            ],
            'baseline_kpi': None,
        }
        out = parse_params_from_meta(['zeta=0.75', 'max_phase=4'], meta, 'fake')
        self.assertEqual(out['zeta'], 0.75,
                         msg=f'zeta should be 0.75 (float), got {out["zeta"]!r}')
        self.assertEqual(out['max_phase'], 4,
                         msg=f'max_phase should be 4 (int), got {out["max_phase"]!r}')
        # Type identity — float i int verbatim z STRATEGY_META.
        self.assertIsInstance(out['zeta'], float, msg='zeta type must be float')
        self.assertIsInstance(out['max_phase'], int, msg='max_phase type must be int')

    def test_param_unknown(self):
        """parse_params: nieznany klucz → LoaderError z 'Nieznany parametr' + lista dostępnych."""
        meta = {
            'description': 'x',
            'params': [('zeta', float, 0.5, 'd')],
            'baseline_kpi': None,
        }
        with self.assertRaises(LoaderError) as cm:
            parse_params_from_meta(['foo=1'], meta, 'fake')
        msg = cm.exception.args[0]
        self.assertIn("Nieznany parametr 'foo'", msg,
                      msg=f'LoaderError should mention "Nieznany parametr \'foo\'", got: {msg!r}')
        self.assertIn('Dostępne:', msg,
                      msg=f'LoaderError should list available params, got: {msg!r}')

    def test_param_conversion_error(self):
        """parse_params: 'zeta=0.75x' (bad float) → LoaderError 'Nie można skonwertować'."""
        meta = {
            'description': 'x',
            'params': [('zeta', float, 0.5, 'd')],
            'baseline_kpi': None,
        }
        with self.assertRaises(LoaderError) as cm:
            parse_params_from_meta(['zeta=0.75x'], meta, 'fake')
        msg = cm.exception.args[0]
        self.assertIn('Nie można skonwertować', msg,
                      msg=f'LoaderError should mention "Nie można skonwertować", got: {msg!r}')
        self.assertIn("'zeta'", msg,
                      msg=f'LoaderError should mention param name "zeta", got: {msg!r}')

    def test_param_malformed_token_warns(self):
        """parse_params: token bez '=' → warning stdout + zwraca defaults (D-43 graceful)."""
        meta = {
            'description': 'x',
            'params': [('zeta', float, 0.5, 'd')],
            'baseline_kpi': None,
        }
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = parse_params_from_meta(['zeta'], meta, 'fake')
        out_str = buf.getvalue()
        self.assertIn("Pominięto token 'zeta'", out_str,
                      msg=f'Stdout should warn about malformed token, got: {out_str!r}')
        # Default value preserved.
        self.assertEqual(result['zeta'], 0.5,
                         msg=f'zeta default 0.5 should remain after malformed token, got {result!r}')

    def test_param_value_contains_equals(self):
        """parse_params: 'json_key=k=v' → split na PIERWSZY '=' (D-39), value = 'k=v'."""
        meta = {
            'description': 'x',
            'params': [('json_key', str, '', 'd')],
            'baseline_kpi': None,
        }
        out = parse_params_from_meta(['json_key=k=v'], meta, 'fake')
        self.assertEqual(out['json_key'], 'k=v',
                         msg=(f'Value with "=" inside should be preserved (D-39 split-first), '
                              f'got {out["json_key"]!r}'))


if __name__ == '__main__':
    unittest.main()
