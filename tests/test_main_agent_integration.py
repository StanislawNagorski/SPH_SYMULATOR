"""
Integration tests dla sphsim/cli/main.py — wrap_with_agent integration + run_compare (Phase 4, D-58/D-60).

Pokrywa 5 przypadków:
  1. Domyślny tryb (bez --no-agent) → agent_enabled = True w JSON metrics
  2. --no-agent → agent_enabled = False, n_vetoed_total = 0
  3. --compare-agent → JSON ma top-level 'comparison' z polami with_agent, without_agent, delta, agent_helps
  4. --compare-agent human output zawiera werdykt TAK/NIE lub checkmarka
  5. --custom (custom strategia) → agent default-on (D-58)

Stdlib only: unittest + subprocess + json + sys + os
"""
import json
import os
import sys
import subprocess
import unittest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _run_sph(*args, **kwargs):
    """Uruchamia sph_sim.py z podanymi argumentami."""
    return subprocess.run(
        [sys.executable, 'sph_sim.py'] + list(args),
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        **kwargs
    )


def _json_from_output(r):
    """Parsuje JSON z stdout (skip nagłówków jeśli potrzeba)."""
    raw = r.stdout
    start = raw.find('{')
    if start == -1:
        raise ValueError(f'Brak JSON w stdout: {raw[:300]}')
    return json.loads(raw[start:])


class TestMainAgentIntegration(unittest.TestCase):
    """Tests dla integracji wrap_with_agent w main.py."""

    def test_default_agent_enabled_true(self):
        """Bez --no-agent: JSON metrics.agent_enabled == True (D-58 default-on)."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 0,
                         msg=f'rc={r.returncode}, stderr={r.stderr[:300]}')
        d = _json_from_output(r)
        self.assertIn('metrics', d, msg=f'Brak klucza "metrics" w JSON: {list(d.keys())}')
        self.assertEqual(d['metrics']['agent_enabled'], True,
                         msg=f'agent_enabled powinno być True bez --no-agent, got {d["metrics"]["agent_enabled"]}')

    def test_no_agent_flag_disables_agent(self):
        """--no-agent → metrics.agent_enabled == False, n_vetoed_total == 0."""
        r = _run_sph('--strategy', 'naive', '--zeta', '0.5', '--no-agent', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 0,
                         msg=f'rc={r.returncode}, stderr={r.stderr[:300]}')
        d = _json_from_output(r)
        self.assertIn('metrics', d, msg=f'Brak "metrics" w JSON: {list(d.keys())}')
        self.assertEqual(d['metrics']['agent_enabled'], False,
                         msg=f'agent_enabled powinno być False z --no-agent, got {d["metrics"]["agent_enabled"]}')
        self.assertEqual(d['metrics']['n_vetoed_total'], 0,
                         msg=f'n_vetoed_total powinno być 0 z --no-agent, got {d["metrics"]["n_vetoed_total"]}')

    def test_compare_agent_json_has_comparison_block(self):
        """--compare-agent → JSON top-level 'comparison' z polami with_agent, without_agent, delta, agent_helps."""
        r = _run_sph('--strategy', 'incentive', '--expected_P', '30', '--compare-agent', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 0,
                         msg=f'rc={r.returncode}, stderr={r.stderr[:300]}')
        d = _json_from_output(r)
        self.assertIn('comparison', d,
                      msg=f'Brak klucza "comparison" w JSON top-level: {list(d.keys())}')
        comp = d['comparison']
        self.assertIn('with_agent', comp, msg=f'Brak "with_agent" w comparison: {list(comp.keys())}')
        self.assertIn('without_agent', comp, msg=f'Brak "without_agent" w comparison: {list(comp.keys())}')
        self.assertIn('delta', comp, msg=f'Brak "delta" w comparison: {list(comp.keys())}')
        self.assertIn('agent_helps', comp, msg=f'Brak "agent_helps" w comparison: {list(comp.keys())}')
        self.assertIsInstance(comp['agent_helps'], bool,
                              msg=f'agent_helps powinno być bool, got {type(comp["agent_helps"])}')

    def test_compare_agent_human_output_has_verdict(self):
        """--compare-agent (human output) zawiera werdykt '✓ TAK' lub '✗ NIE'."""
        r = _run_sph('--strategy', 'incentive', '--expected_P', '30', '--compare-agent', '--seed', '42')
        self.assertEqual(r.returncode, 0,
                         msg=f'rc={r.returncode}, stderr={r.stderr[:400]}')
        has_verdict = ('✓' in r.stdout or '✗' in r.stdout or
                       'TAK' in r.stdout or 'NIE' in r.stdout)
        self.assertTrue(has_verdict,
                        msg=f'Brak werdyktu (TAK/NIE/✓/✗) w human output: {r.stdout[:500]}')

    def test_custom_strategy_agent_default_on(self):
        """--custom z custom strategią → agent default-on (D-58): agent_enabled == True."""
        r = _run_sph('--custom', 'examples/custom_strategy_template.py', '--seed', '42', '--json')
        self.assertEqual(r.returncode, 0,
                         msg=f'rc={r.returncode}, stderr={r.stderr[:300]}')
        d = _json_from_output(r)
        self.assertIn('metrics', d, msg=f'Brak "metrics" w JSON: {list(d.keys())}')
        self.assertEqual(d['metrics']['agent_enabled'], True,
                         msg=f'agent_enabled powinno być True dla --custom bez --no-agent (D-58), got {d["metrics"]["agent_enabled"]}')


class TestRunCompareFunction(unittest.TestCase):
    """Tests dla funkcji run_compare w main.py (importowana bezpośrednio)."""

    def test_run_compare_imported_from_main(self):
        """run_compare istnieje jako top-level funkcja w sphsim.cli.main."""
        from sphsim.cli import main as main_module
        self.assertTrue(hasattr(main_module, 'run_compare'),
                        msg='run_compare brakuje w sphsim.cli.main — wymagane przez plan 04-04')

    def test_run_compare_returns_comparison_block(self):
        """run_compare zwraca dict z kluczem 'comparison' zawierającym wymagane pola."""
        import argparse
        from sphsim.cli.main import run_compare
        from sphsim.strategies import STRATEGIES
        from sphsim.config import DEFAULT_K0, DEFAULT_F, DEFAULT_T, DEFAULT_KAPPA, DEFAULT_ALPHA
        from sphsim.config import DEFAULT_NU, DEFAULT_NSUS, DEFAULT_PHI, DEFAULT_RHO, DEFAULT_K1

        raw_fn = STRATEGIES['naive']
        fake_args = argparse.Namespace(
            nU=DEFAULT_NU, nSUS=DEFAULT_NSUS, K1=DEFAULT_K1, T=200,
            kappa=DEFAULT_KAPPA, alpha=DEFAULT_ALPHA, seed=42,
            expected_P=100.0,
            phi=DEFAULT_PHI, rho=DEFAULT_RHO,  # Phase 5 ENV-01: wymagane przez run_compare
        )
        K1 = DEFAULT_K1
        params = {'zeta': 0.5, 'max_phase': 3, 'probs': '0.9,0.7,0.5,0.3,0.0',
                  's_target': 10, 'expected_P': 100.0}
        result = run_compare(fake_args, raw_fn, 'naive', params, K1)

        self.assertIn('comparison', result,
                      msg=f'run_compare nie zwróciło klucza "comparison": {list(result.keys())}')
        comp = result['comparison']
        for key in ('with_agent', 'without_agent', 'delta', 'agent_helps'):
            self.assertIn(key, comp, msg=f'Brak "{key}" w comparison dict: {list(comp.keys())}')
        self.assertIsInstance(comp['agent_helps'], bool,
                              msg=f'agent_helps powinno być bool, got {type(comp["agent_helps"])}')
        # delta ma 5 wymaganych KPI
        for kpi in ('avg_val_last100', 'cum_val_total', 'avg_net_profit', 'delivery_ratio', 'avg_providers_l100'):
            self.assertIn(kpi, comp['delta'],
                          msg=f'KPI "{kpi}" brakuje w delta dict: {list(comp["delta"].keys())}')


if __name__ == '__main__':
    unittest.main()
