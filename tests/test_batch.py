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
import json, os, subprocess, sys, unittest
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

PROJECT_ROOT = Path(_PROJECT_ROOT)
MONOLITH = PROJECT_ROOT / 'sph_sim.py'


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
    """BATCH-01: _parse_seeds_list grammar — single N → range, lista → dedup, reject 0/ujemne/range-syntax/empty."""

    def test_placeholder(self):
        self.skipTest("Wave 1 — Plan 07-02 — _parse_seeds_list converter w args.py")


class TestArgsMutex(unittest.TestCase):
    """BATCH-01: --batch wymaga --seeds; --batch + --compare-agent mutex; --seeds bez --batch mutex; --batch + --interactive mutex."""

    def test_placeholder(self):
        self.skipTest("Wave 1 — Plan 07-02 — post-parse mutex w args.py")


class TestReplBatch(unittest.TestCase):
    """BATCH-01: REPL komenda 'batch <strategia> --seeds N|lista [k=v]' produkuje raport + polski error dla --seeds 0."""

    def test_placeholder(self):
        self.skipTest("Wave 4 — Plan 07-05 — SPHShell.do_batch w repl.py")


class TestDeterminism(unittest.TestCase):
    """BATCH-01: ta sama lista seedów dwa razy → byte-identical per-seed KPI (random.seed(S) reset w SPHSimulator.__init__)."""

    def test_placeholder(self):
        self.skipTest("Wave 2 — Plan 07-03 — run_batch orchestrator deterministic loop")


class TestCliReplParity(unittest.TestCase):
    """BATCH-01: CLI '--batch --seeds 3' i REPL 'batch <name> --seeds 3' produkują identyczne tabele KPI (single source of truth dla seedów + aggregate)."""

    def test_placeholder(self):
        self.skipTest("Wave 4 — Plan 07-05 — REPL fake_args + run_batch reuse")


if __name__ == '__main__':
    unittest.main()
