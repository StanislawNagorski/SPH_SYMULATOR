"""
Unit i integration tests dla Phase 7 — CLI/REPL/parser side (BATCH-01).

Pokrywa 5 klas, każda jeden skip-placeholder (RED-W0):
  1. TestSeedsParser     — _parse_seeds_list grammar: single N → range,
                           lista → dedup, reject 0/ujemne/range-syntax/empty.
                           [Wave 1 — Plan 07-02 — args.py]
  2. TestArgsMutex       — --batch wymaga --seeds; --batch + --compare-agent
                           mutex; --seeds bez --batch mutex; --batch +
                           --interactive mutex.
                           [Wave 1 — Plan 07-02 — args.py]
  3. TestReplBatch       — REPL 'batch <strategia> --seeds N|lista [k=v]'
                           produkuje raport + polski error dla --seeds 0.
                           [Wave 4 — Plan 07-05 — repl.py]
  4. TestDeterminism     — ta sama lista seedów dwa razy → byte-identical
                           per-seed KPI (random.seed(S) reset).
                           [Wave 2 — Plan 07-03 — orchestrator]
  5. TestCliReplParity   — CLI --batch --seeds N == REPL batch ... --seeds N
                           (single source of truth dla aggregate).
                           [Wave 4 — Plan 07-05 — fake_args + run_batch reuse]

Stdlib only: unittest + subprocess + json + os + sys + tempfile + pathlib
(zgodne z PROJECT.md constraint).
"""
import argparse, json, os, re, shutil, subprocess, sys, unittest
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

PROJECT_ROOT = Path(_PROJECT_ROOT)
MONOLITH = PROJECT_ROOT / 'sph_sim.py'

from sphsim.cli.args import _parse_seeds_list, MAX_SEEDS


def _run_sph(*args, **kwargs):
    """Subprocess helper — uruchamia sph_sim.py z cwd=_PROJECT_ROOT (mirror tests/test_env.py)."""
    env = {**os.environ, 'SPHSIM_NO_REPORT': kwargs.pop('SPHSIM_NO_REPORT', '1')}
    return subprocess.run(
        [sys.executable, 'sph_sim.py', *args],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        **kwargs,
    )


class TestSeedsParser(unittest.TestCase):
    """BATCH-01: _parse_seeds_list grammar — single N → range, lista → dedup, reject 0/ujemne/range-syntax/empty/oversized."""

    def test_single_n(self):
        """'10' → [1..10]; '1' → [1]; '  42 ' → range(1,43) (whitespace strip)."""
        self.assertEqual(_parse_seeds_list('10'), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(_parse_seeds_list('1'), [1])
        self.assertEqual(_parse_seeds_list('  42 '), list(range(1, 43)))

    def test_list(self):
        """'1,5,42,100' → [1,5,42,100]; whitespace inside list tolerated."""
        self.assertEqual(_parse_seeds_list('1,5,42,100'), [1, 5, 42, 100])
        self.assertEqual(_parse_seeds_list('1, 5, 42'), [1, 5, 42])

    def test_dedup_preserve_order(self):
        """'1,1,2,1' → [1,2]; '5,1,5,42,1' → [5,1,42] (first-occurrence preserved)."""
        self.assertEqual(_parse_seeds_list('1,1,2,1'), [1, 2])
        self.assertEqual(_parse_seeds_list('5,1,5,42,1'), [5, 1, 42])

    def test_reject_zero(self):
        """'0' → ArgumentTypeError z 'dodatnie' w komunikacie."""
        with self.assertRaises(argparse.ArgumentTypeError) as ctx:
            _parse_seeds_list('0')
        self.assertIn('dodatnie', str(ctx.exception))

    def test_reject_negative(self):
        """'-5' → ArgumentTypeError (negative — z 'dodatnie' lub '-5' w komunikacie)."""
        with self.assertRaises(argparse.ArgumentTypeError) as ctx:
            _parse_seeds_list('-5')
        msg = str(ctx.exception)
        self.assertTrue('dodatnie' in msg or '-5' in msg,
                        msg=f"Brak 'dodatnie' lub '-5' w komunikacie: {msg!r}")

    def test_reject_non_int(self):
        """'abc', '1.5', '1,5,abc', '1..10' → ArgumentTypeError (każdy oddzielnie)."""
        with self.assertRaises(argparse.ArgumentTypeError):
            _parse_seeds_list('abc')
        with self.assertRaises(argparse.ArgumentTypeError):
            _parse_seeds_list('1.5')
        with self.assertRaises(argparse.ArgumentTypeError):
            _parse_seeds_list('1,5,abc')
        with self.assertRaises(argparse.ArgumentTypeError):
            _parse_seeds_list('1..10')

    def test_reject_empty(self):
        """'' → ArgumentTypeError z 'Pusta' w komunikacie."""
        with self.assertRaises(argparse.ArgumentTypeError) as ctx:
            _parse_seeds_list('')
        self.assertIn('Pusta', str(ctx.exception))

    def test_reject_oversized(self):
        """MAX_SEEDS+1 → ArgumentTypeError z 'limit' lub '1000' w komunikacie (T-7-02-01 DoS cap)."""
        # Single-N branch
        with self.assertRaises(argparse.ArgumentTypeError) as ctx:
            _parse_seeds_list(str(MAX_SEEDS + 1))
        msg = str(ctx.exception)
        self.assertTrue('limit' in msg or str(MAX_SEEDS) in msg,
                        msg=f"Brak 'limit' lub '{MAX_SEEDS}' w komunikacie: {msg!r}")
        # Comma-list branch (oversized after dedup)
        oversized_list = ','.join(str(i) for i in range(1, MAX_SEEDS + 2))
        with self.assertRaises(argparse.ArgumentTypeError) as ctx2:
            _parse_seeds_list(oversized_list)
        self.assertIn('limit', str(ctx2.exception))


class TestArgsMutex(unittest.TestCase):
    """BATCH-01: --batch wymaga --seeds; --batch + --compare-agent mutex; --seeds bez --batch mutex; --batch + --interactive mutex (Polish-only)."""

    def test_batch_requires_seeds(self):
        """--batch bez --seeds → exit 2 z 'wymaga --seeds'."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--batch', '--seed', '42')
        self.assertEqual(r.returncode, 2,
                         msg=f'Oczekiwano exit 2, got {r.returncode}. stderr={r.stderr[:300]}')
        combined = r.stderr + r.stdout
        self.assertIn('wymaga --seeds', combined,
                      msg=f"Brak 'wymaga --seeds' w komunikacie: {combined[:400]}")

    def test_seeds_requires_batch(self):
        """--seeds bez --batch → exit 2 z 'wymaga --batch'."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--seeds', '5', '--seed', '42')
        self.assertEqual(r.returncode, 2,
                         msg=f'Oczekiwano exit 2, got {r.returncode}. stderr={r.stderr[:300]}')
        combined = r.stderr + r.stdout
        self.assertIn('wymaga --batch', combined,
                      msg=f"Brak 'wymaga --batch' w komunikacie: {combined[:400]}")

    def test_batch_compare_mutex(self):
        """--batch + --compare-agent → exit 2 z 'wzajemnie wykluczające'."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5',
                     '--batch', '--seeds', '5', '--compare-agent', '--seed', '42')
        self.assertEqual(r.returncode, 2,
                         msg=f'Oczekiwano exit 2, got {r.returncode}. stderr={r.stderr[:300]}')
        combined = r.stderr + r.stdout
        self.assertIn('wzajemnie wykluczające', combined,
                      msg=f"Brak 'wzajemnie wykluczające' w komunikacie: {combined[:400]}")

    def test_batch_interactive_mutex(self):
        """--batch + --interactive → exit 2 z 'nie działa w trybie --interactive' (Polish-only, NO English fallback).

        Invocation supplies ONLY --interactive (NOT --strategy) so the top-level argparse
        add_mutually_exclusive_group(required=True) involving {--interactive, --strategy, --custom}
        is satisfied by --interactive alone — and the Phase-7 post-parse Polish p.error fires first.
        """
        r = _run_sph('--interactive', '--batch', '--seeds', '5', '--seed', '42')
        self.assertEqual(r.returncode, 2,
                         msg=f'Oczekiwano exit 2, got {r.returncode}. stderr={r.stderr[:300]}')
        combined = r.stderr + r.stdout
        self.assertIn('nie działa w trybie --interactive', combined,
                      msg=f"Brak Polish error 'nie działa w trybie --interactive' (English fallback NOT accepted): {combined[:400]}")


class TestReplBatch(unittest.TestCase):
    """BATCH-01: REPL komenda 'batch <strategia> --seeds N|lista [k=v]' produkuje raport + polski error dla --seeds 0."""

    def setUp(self):
        # Pre-clean reports dir — test isolation: ./reports/batch_* glob must reflect this test.
        shutil.rmtree(PROJECT_ROOT / 'reports', ignore_errors=True)

    def tearDown(self):
        shutil.rmtree(PROJECT_ROOT / 'reports', ignore_errors=True)

    def test_repl_batch_e2e(self):
        """REPL 'batch naive --seeds 3 zeta=0.75' produces reports/batch_<ts>/{report.md, batch_aggregate.png} + stderr banner."""
        # Allow report write — override the inherited SPHSIM_NO_REPORT=1 from tests/__init__.py
        # by setting empty string (write_batch_report checks `== '1'`).
        env = {**os.environ, 'SPHSIM_NO_REPORT': ''}
        p = subprocess.run(
            [sys.executable, 'sph_sim.py', '--interactive'],
            cwd=_PROJECT_ROOT, capture_output=True, text=True,
            input='batch naive --seeds 3 zeta=0.75\nexit\n',
            env=env,
        )
        self.assertEqual(p.returncode, 0, msg=f'REPL failed: stderr={p.stderr[:400]}')
        combined = p.stdout + p.stderr
        # Banner on stderr (caller emits, Phase 6 contract).
        self.assertIn('Raport batchowy zapisany do:', combined,
                      msg=f'Brak banner stderr: {combined[:400]}')
        # BATCH SUMMARY on stdout (format_batch_summary banner).
        self.assertIn('BATCH SUMMARY', p.stdout,
                      msg=f'Brak BATCH SUMMARY w stdout: {p.stdout[:400]}')

        # Artifact check — reports/batch_<ts>/ directory with report.md + batch_aggregate.png
        matches = sorted((PROJECT_ROOT / 'reports').glob('batch_*'))
        self.assertGreaterEqual(len(matches), 1,
                                msg=f'no batch_* dir found in {PROJECT_ROOT / "reports"}')
        latest = matches[-1]
        self.assertTrue((latest / 'report.md').exists(),
                        msg=f'report.md not found in {latest}')
        self.assertTrue((latest / 'batch_aggregate.png').exists(),
                        msg=f'batch_aggregate.png not found in {latest}')

    def test_repl_batch_invalid_seeds_no_crash(self):
        """REPL 'batch naive --seeds 0' prints Polish 'dodatnie' error, NO Python traceback, returns to prompt cleanly."""
        env = {**os.environ, 'SPHSIM_NO_REPORT': '1'}
        p = subprocess.run(
            [sys.executable, 'sph_sim.py', '--interactive'],
            cwd=_PROJECT_ROOT, capture_output=True, text=True,
            input='batch naive --seeds 0\nexit\n',
            env=env,
        )
        # REPL must exit cleanly even after error in do_batch (Pitfall 2 — REPL never crashes).
        self.assertEqual(p.returncode, 0,
                         msg=f'REPL crashed: returncode={p.returncode}, stderr={p.stderr[:400]}')
        # Polish error from _parse_seeds_list propagated via `print(str(e))` in do_batch.
        self.assertIn('dodatnie', p.stdout,
                      msg=f"Brak 'dodatnie' w stdout: {p.stdout[:400]}")
        # NO Python traceback in stdout/stderr — REPL must NOT propagate exceptions to user.
        combined = p.stdout + p.stderr
        self.assertNotIn('Traceback', combined,
                         msg=f'Python traceback leaked to user: {combined[:400]}')


class TestDeterminism(unittest.TestCase):
    """BATCH-01: ta sama lista seedów dwa razy → byte-identical per-seed KPI (random.seed(S) reset w SPHSimulator.__init__)."""

    def test_byte_identical(self):
        """Two CLI invocations with identical --seeds → byte-identical stdout (BATCH-01 determinism contract)."""
        r1 = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--batch', '--seeds', '1,2,3', '--no-agent', '--seed', '42')
        r2 = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--batch', '--seeds', '1,2,3', '--no-agent', '--seed', '42')
        self.assertEqual(r1.returncode, 0, msg=f'r1 failed: stderr={r1.stderr[:300]}')
        self.assertEqual(r2.returncode, 0, msg=f'r2 failed: stderr={r2.stderr[:300]}')
        self.assertEqual(r1.stdout, r2.stdout,
                         msg=f"stdout diverged:\n--- r1 ---\n{r1.stdout}\n--- r2 ---\n{r2.stdout}")

    def test_different_seeds_diverge(self):
        """Two CLI invocations with DIFFERENT --seeds → different stdout (paranoia: ensure test_byte_identical isn't trivial)."""
        r_a = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--batch', '--seeds', '1,2,3', '--no-agent', '--seed', '42')
        r_b = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--batch', '--seeds', '4,5,6', '--no-agent', '--seed', '42')
        self.assertEqual(r_a.returncode, 0, msg=f'r_a failed: stderr={r_a.stderr[:300]}')
        self.assertEqual(r_b.returncode, 0, msg=f'r_b failed: stderr={r_b.stderr[:300]}')
        self.assertNotEqual(r_a.stdout, r_b.stdout,
                            msg=f"different seeds produced identical stdout — seed list NOT being honored:\n{r_a.stdout[:400]}")


class TestCliReplParity(unittest.TestCase):
    """BATCH-01: CLI '--batch --seeds 3' i REPL 'batch <name> --seeds 3' produkują identyczne tabele KPI (single source of truth dla seedów + aggregate)."""

    def setUp(self):
        shutil.rmtree(PROJECT_ROOT / 'reports', ignore_errors=True)

    def tearDown(self):
        shutil.rmtree(PROJECT_ROOT / 'reports', ignore_errors=True)

    def test_identical_per_seed_row_count(self):
        """CLI `--batch --seeds 3` and REPL `batch naive --seeds 3` produce reports with same structural shape (3 per-seed rows + identical KPI header).

        Caveat (per Plan 07-05 <interfaces> note): REPL `do_batch` has no_agent=False
        (agent ON, mirror of do_compare/do_run), CLI invocation here uses --no-agent
        (agent OFF). Strict byte-equality of report.md is therefore impossible without
        a REPL --no-agent flag (v2 scope). This test asserts STRUCTURAL parity
        (per-seed row count + KPI table header) which is enough to detect any major
        regression like "REPL writes wrong seed count" or "REPL skips per-seed table".
        """
        # ── CLI half ──
        cli = _run_sph(
            '--strategy', 'naive', '--zeta', '0.75',
            '--batch', '--seeds', '3', '--no-agent', '--seed', '42',
            SPHSIM_NO_REPORT='',
        )
        self.assertEqual(cli.returncode, 0,
                         msg=f'CLI failed: returncode={cli.returncode}, stderr={cli.stderr[:400]}')
        cli_dirs = sorted((PROJECT_ROOT / 'reports').glob('batch_*'))
        self.assertGreaterEqual(len(cli_dirs), 1,
                                msg=f'CLI produced no batch_* dir; ls={list((PROJECT_ROOT / "reports").iterdir())}')
        cli_md = (cli_dirs[-1] / 'report.md').read_text(encoding='utf-8')

        # Pre-clean between halves to disambiguate which dir belongs to REPL.
        shutil.rmtree(PROJECT_ROOT / 'reports', ignore_errors=True)

        # ── REPL half ──
        env = {**os.environ, 'SPHSIM_NO_REPORT': ''}
        repl = subprocess.run(
            [sys.executable, 'sph_sim.py', '--interactive'],
            cwd=_PROJECT_ROOT, capture_output=True, text=True,
            input='batch naive --seeds 3 zeta=0.75\nexit\n',
            env=env,
        )
        self.assertEqual(repl.returncode, 0,
                         msg=f'REPL failed: returncode={repl.returncode}, stderr={repl.stderr[:400]}')
        repl_dirs = sorted((PROJECT_ROOT / 'reports').glob('batch_*'))
        self.assertGreaterEqual(len(repl_dirs), 1,
                                msg=f'REPL produced no batch_* dir; ls={list((PROJECT_ROOT / "reports").iterdir())}')
        repl_md = (repl_dirs[-1] / 'report.md').read_text(encoding='utf-8')

        # ── Parity assertions ──
        # Per-seed row count — extract rows starting with `| <positive int> |` (the per-seed table).
        # Pattern matches: '| 1 |', '| 5 |', '| 42 |' (positive integer in first col, must be at line start).
        cli_rows = re.findall(r'^\| [1-9]\d* \|', cli_md, re.MULTILINE)
        repl_rows = re.findall(r'^\| [1-9]\d* \|', repl_md, re.MULTILINE)
        self.assertEqual(len(cli_rows), 3,
                         msg=f'CLI per-seed rows ≠ 3 (got {len(cli_rows)}): {cli_rows}')
        self.assertEqual(len(repl_rows), 3,
                         msg=f'REPL per-seed rows ≠ 3 (got {len(repl_rows)}): {repl_rows}')

        # KPI table header parity — both reports MUST contain the canonical per-seed header
        # (single source of truth: same render_batch_report template).
        self.assertIn('avg_val_last100', cli_md,
                      msg='CLI report.md missing avg_val_last100 in per-seed table header')
        self.assertIn('avg_val_last100', repl_md,
                      msg='REPL report.md missing avg_val_last100 in per-seed table header')

        # Strategy name parity — both reports must reference strategy `naive`.
        self.assertIn('naive', cli_md, msg='CLI report.md missing strategy name')
        self.assertIn('naive', repl_md, msg='REPL report.md missing strategy name')


if __name__ == '__main__':
    unittest.main()
