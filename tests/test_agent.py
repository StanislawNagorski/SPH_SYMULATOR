"""
Unit i integration tests dla sphsim.agent.rational (Phase 4, D-53/D-55/D-56/D-57/D-63/D-65/D-67).

Pokrywa 10 przypadków:
  1.  wrapper passthrough dla ABSTAIN — n_vetoed pozostaje 0
  2.  brak veto gdy E[zysk] > 0 — duże expected_P → wrapper zwraca COMMIT
  3.  veto gdy E[zysk] < 0 — małe expected_P → wrapper zwraca VETO, n_vetoed += 1
  4.  n_vetoed inkrementuje a n_abstain NIE — rozróżnione kategorie (D-63/D-65)
  5.  total_h == 0 fallback (D-55) — brak ZeroDivisionError, sensowna decyzja
  6.  phi[idx] >= 1.0 → VETO (D-57 guard) bez obliczania E[zysk]
  7.  idx >= len(phi) → VETO (D-57 guard)
  8.  strategy_incentive + wrapper = idempotent (D-56) — n_vetoed == 0 dla matching expected_P
  9.  --compare-agent JSON ma blok 'comparison' (integration test, CLI)
 10.  --no-agent → n_vetoed_total = 0 i agent_enabled == False (integration test, CLI)

Stdlib only: unittest + subprocess + json + os + sys + tempfile
(zgodne z PROJECT.md constraint stdlib-only).
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

# Pozwól uruchamiać test bezpośrednio: `python tests/test_agent.py`
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sphsim.agent.rational import wrap_with_agent
from sphsim.core.device import Device
from sphsim.strategies.incentive import strategy_incentive

PROJECT_ROOT = Path(_PROJECT_ROOT)
MONOLITH = PROJECT_ROOT / 'sph_sim.py'


def _make_device(phase=1, status='UP'):
    """Helper: tworzy Device z domyślnymi parametrami dla testów."""
    return Device(id=0, phase=phase, status=status)


def _stub_abstain(dev, l, s, phi, kappa, rho, h, p):
    """Stub strategy zawsze zwracający 'ABSTAIN'."""
    return 'ABSTAIN'


def _stub_commit(dev, l, s, phi, kappa, rho, h, p):
    """Stub strategy zawsze zwracający 'COMMIT'."""
    return 'COMMIT'


class TestWrapWithAgent(unittest.TestCase):
    """8 unit testów dla wrap_with_agent: passthrough, veto, guards D-55/D-56/D-57/D-63/D-65."""

    # --- Test 1: ABSTAIN passthrough ---

    def test_abstain_passthrough(self):
        """(1) Gdy strategia zwraca ABSTAIN, wrapper musi zwrócić 'ABSTAIN' i n_vetoed == 0.

        D-56: ABSTAIN passthrough — wrapper nie liczy E[zysk] dla ABSTAIN.
        """
        w = wrap_with_agent(_stub_abstain, 100.0)
        dev = _make_device(phase=2, status='UP')
        phi = [0.1, 0.1, 0.1, 0.1]
        rho = [5.0, 5.0, 5.0, 5.0]
        out = w(dev, [10, 10, 10, 10], 10, phi, 1.0, rho, lambda i: i, {})
        self.assertEqual(out, 'ABSTAIN',
                         msg=f"ABSTAIN passthrough: oczekiwane 'ABSTAIN', got {out!r}")
        self.assertEqual(dev.n_vetoed, 0,
                         msg=f"n_vetoed musi pozostać 0 przy ABSTAIN passthrough, got {dev.n_vetoed}")

    # --- Test 2: brak veto gdy E[zysk] > 0 ---

    def test_commit_positive_E_passthrough(self):
        """(2) Gdy strategia COMMIT i E[zysk] > 0 (duże expected_P), wrapper zwraca 'COMMIT', n_vetoed == 0.

        D-53: E[zysk] = (1-phi_i)*p_i - kappa - phi_i*rho_i; gdy > 0 → passthrough.
        """
        w = wrap_with_agent(_stub_commit, 1000.0)  # duże expected_P → net > 0
        dev = _make_device(phase=1, status='UP')
        phi = [0.1, 0.1, 0.1, 0.1]
        rho = [5.0, 5.0, 5.0, 5.0]
        out = w(dev, [10, 10, 10, 10], 10, phi, 1.0, rho, lambda i: i, {})
        self.assertEqual(out, 'COMMIT',
                         msg=f"Duże expected_P: oczekiwane 'COMMIT', got {out!r}")
        self.assertEqual(dev.n_vetoed, 0,
                         msg=f"n_vetoed == 0 przy COMMIT passthrough, got {dev.n_vetoed}")

    # --- Test 3: veto gdy E[zysk] < 0 ---

    def test_commit_negative_E_veto(self):
        """(3) Gdy strategia COMMIT i E[zysk] < 0 (małe expected_P), wrapper zwraca 'VETO',
        n_vetoed == 1, veto_phase_stats == {1: 1}.

        D-65: AGENT-02 — override COMMIT → VETO gdy net < 0.
        """
        w = wrap_with_agent(_stub_commit, 0.01)  # mikroskopijne expected_P → net < 0 (kappa=1.0)
        dev = _make_device(phase=1, status='UP')
        phi = [0.1, 0.1, 0.1, 0.1]
        rho = [5.0, 5.0, 5.0, 5.0]
        out = w(dev, [10, 10, 10, 10], 10, phi, 1.0, rho, lambda i: i, {})
        self.assertEqual(out, 'VETO',
                         msg=f"Małe expected_P: oczekiwane 'VETO', got {out!r}")
        self.assertEqual(dev.n_vetoed, 1,
                         msg=f"n_vetoed powinno być 1 po VETO, got {dev.n_vetoed}")
        self.assertEqual(dev.veto_phase_stats, {1: 1},
                         msg=f"veto_phase_stats == {{1: 1}}, got {dev.veto_phase_stats!r}")

    # --- Test 4: n_vetoed inkrementuje, n_abstain NIE ---

    def test_n_vetoed_increments_not_n_abstain(self):
        """(4) Po VETO: dev.n_vetoed == 1, dev.n_abstain == 0 — rozróżnione kategorie (D-63/D-65).

        n_abstain NIE powinno rosnąć przy VETO — osobny licznik.
        """
        w = wrap_with_agent(_stub_commit, 0.01)
        dev = _make_device(phase=1, status='UP')
        phi = [0.1, 0.1, 0.1, 0.1]
        rho = [5.0, 5.0, 5.0, 5.0]
        out = w(dev, [10, 10, 10, 10], 10, phi, 1.0, rho, lambda i: i, {})
        self.assertEqual(out, 'VETO',
                         msg=f"oczekiwane 'VETO', got {out!r}")
        self.assertEqual(dev.n_vetoed, 1,
                         msg=f"n_vetoed == 1 po VETO, got {dev.n_vetoed}")
        self.assertEqual(dev.n_abstain, 0,
                         msg=f"n_abstain musi pozostać 0 (wrapper NIE inkrementuje n_abstain), got {dev.n_abstain}")

    # --- Test 5: total_h == 0 fallback D-55 ---

    def test_total_h_zero_fallback_D55(self):
        """(5) Gdy wszystkie l == 0 (total_h = 0), wrapper stosuje fallback = 1.0 (D-55).

        Brak ZeroDivisionError. Decyzja to COMMIT lub VETO (nie crash).
        """
        w = wrap_with_agent(_stub_commit, 0.01)  # małe expected_P
        dev = _make_device(phase=1, status='UP')
        phi = [0.1, 0.1, 0.1, 0.1]
        rho = [5.0, 5.0, 5.0, 5.0]
        try:
            out = w(dev, [0, 0, 0, 0], 0, phi, 1.0, rho, lambda i: i, {})
        except ZeroDivisionError:
            self.fail("ZeroDivisionError — brakuje fallback total_h = 1.0 (D-55)")
        self.assertIn(out, ('COMMIT', 'VETO'),
                      msg=f"D-55 fallback: oczekiwane 'COMMIT' lub 'VETO', got {out!r}")

    # --- Test 6: phi[idx] >= 1.0 → VETO (D-57 guard) ---

    def test_phi_one_guard_D57(self):
        """(6) Gdy phi[idx] >= 1.0, wrapper zwraca 'VETO' bez obliczania E[zysk] (D-57 guard).

        Guard zapobiega obliczeniom dla zawsze-failing faz.
        """
        w = wrap_with_agent(_stub_commit, 100.0)  # duże expected_P — bez guardu byłby COMMIT
        dev = _make_device(phase=2, status='UP')
        phi = [0.1, 1.0, 0.1, 0.1]  # phi[1] = 1.0 → guard dla fazy 2
        rho = [5.0, 5.0, 5.0, 5.0]
        out = w(dev, [10, 10, 10, 10], 10, phi, 1.0, rho, lambda i: i, {})
        self.assertEqual(out, 'VETO',
                         msg=f"phi[idx] = 1.0: oczekiwane 'VETO', got {out!r}")
        self.assertEqual(dev.n_vetoed, 1,
                         msg=f"n_vetoed musi być 1 po guard VETO, got {dev.n_vetoed}")

    # --- Test 7: idx >= len(phi) → VETO (D-57 guard) ---

    def test_idx_out_of_range_guard_D57(self):
        """(7) Gdy dev.phase - 1 >= len(phi), wrapper zwraca 'VETO' (D-57 guard).

        Faza poza zakresem phi traktowana jako awaria konfiguracji → veto.
        """
        w = wrap_with_agent(_stub_commit, 100.0)
        dev = _make_device(phase=10, status='UP')  # idx = 9, len(phi) = 5 → out of range
        phi = [0.1, 0.1, 0.1, 0.1, 0.1]  # len = 5
        rho = [5.0, 5.0, 5.0, 5.0, 5.0]
        out = w(dev, [10, 10, 10, 10, 10], 10, phi, 1.0, rho, lambda i: i, {})
        self.assertEqual(out, 'VETO',
                         msg=f"idx >= len(phi): oczekiwane 'VETO', got {out!r}")

    # --- Test 8: incentive + wrapper idempotent (D-56) ---

    def test_incentive_plus_wrapper_idempotent_D56(self):
        """(8) wrap_with_agent(strategy_incentive, 100.0) na realistycznym Device — idempotent (D-56).

        Dla identycznych expected_P, incentive zwraca COMMIT gdy net > 0 → agent passthrough.
        n_vetoed == 0 po wielu wywołaniach z tym samym input'em.
        """
        expected_P = 100.0
        w = wrap_with_agent(strategy_incentive, expected_P)
        dev = _make_device(phase=1, status='UP')
        phi = [0.1, 0.2, 0.3, 0.4]
        rho = [2.0, 2.0, 2.0, 2.0]
        l = [50, 40, 30, 0]
        h = lambda i: float(i)  # h(i) = i^1 (alpha=1)
        p = {'expected_P': expected_P}

        # Wielokrotne wywołania z tym samym inputem — idempotent
        for iteration in range(3):
            w(dev, l, 10, phi, 0.25, rho, h, p)

        self.assertEqual(dev.n_vetoed, 0,
                         msg=f"incentive+wrapper powinno być idempotent (D-56), "
                             f"got n_vetoed={dev.n_vetoed} po 3 iteracjach")


class TestCLIIntegration(unittest.TestCase):
    """2 integration testy: --compare-agent JSON z blokiem 'comparison', --no-agent n_vetoed_total == 0."""

    def test_compare_agent_json_has_comparison_block(self):
        """(9) --compare-agent → JSON zawiera klucz 'comparison' z polami with_agent/without_agent/agent_helps.

        D-62: JSON structure: {"comparison": {"with_agent": {...}, "without_agent": {...},
              "delta": {...}, "agent_helps": true|false}}.
        Wzorzec subprocess z scripts/regression_check.py:79-99.
        """
        full_args = [
            sys.executable, str(MONOLITH),
            '--strategy', 'incentive', '--expected_P', '30', '--compare-agent',
            '--seed', '42', '--json',
        ]
        proc = subprocess.run(
            full_args,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0,
                         msg=f"--compare-agent exit code {proc.returncode}, stderr: {proc.stderr[:300]}")
        result = json.loads(proc.stdout)
        self.assertIn('comparison', result,
                      msg=f"JSON nie zawiera klucza 'comparison'. Klucze: {list(result.keys())}")
        comp = result['comparison']
        self.assertIn('with_agent', comp,
                      msg=f"'comparison' nie ma 'with_agent'. Klucze: {list(comp.keys())}")
        self.assertIn('without_agent', comp,
                      msg=f"'comparison' nie ma 'without_agent'. Klucze: {list(comp.keys())}")
        self.assertIn('agent_helps', comp,
                      msg=f"'comparison' nie ma 'agent_helps'. Klucze: {list(comp.keys())}")
        self.assertIn(comp['agent_helps'], (True, False),
                      msg=f"'agent_helps' musi być bool, got {comp['agent_helps']!r}")

    def test_no_agent_zero_vetoes(self):
        """(10) --no-agent → n_vetoed_total == 0 i agent_enabled == False (D-67 backwards compat).

        --no-agent wyłącza RationalAgent — brak veto, agent_enabled=False w metrics.
        Wzorzec subprocess z scripts/regression_check.py:79-99.
        """
        full_args = [
            sys.executable, str(MONOLITH),
            '--strategy', 'naive', '--zeta', '0.5', '--no-agent',
            '--seed', '42', '--json',
        ]
        proc = subprocess.run(
            full_args,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0,
                         msg=f"--no-agent exit code {proc.returncode}, stderr: {proc.stderr[:300]}")
        result = json.loads(proc.stdout)
        self.assertIn('metrics', result,
                      msg=f"JSON nie zawiera klucza 'metrics'. Klucze: {list(result.keys())}")
        metrics = result['metrics']
        self.assertEqual(metrics.get('n_vetoed_total'), 0,
                         msg=f"--no-agent: n_vetoed_total musi być 0, got {metrics.get('n_vetoed_total')!r}")
        self.assertEqual(metrics.get('agent_enabled'), False,
                         msg=f"--no-agent: agent_enabled musi być False, got {metrics.get('agent_enabled')!r}")


if __name__ == '__main__':
    unittest.main()
