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
import argparse, json, os, subprocess, sys, unittest
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

    def test_placeholder(self):
        self.skipTest("Wave 4 — Plan 07-05 — SPHShell.do_batch w repl.py")


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

    def test_placeholder(self):
        self.skipTest("Wave 4 — Plan 07-05 — REPL fake_args + run_batch reuse")


if __name__ == '__main__':
    unittest.main()
