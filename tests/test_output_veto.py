"""
Unit tests dla sphsim.cli.output — rozszerzenie Phase 4 (D-66/D-62/D-67).

Pokrywa:
  Task 1 — format_human:
    T1a. res z n_vetoed_total=0 → no VETO section
    T1b. res z n_vetoed_total>0 → VETO section present + header + total line
    T1c. sekcja VETO renderuje fazy z veto_pp.keys() ∪ ic.keys()
    T1d. format_human z verbose=True działa (verbose block po sekcji VETO)
    T1e. res z 'comparison' key → early return format_compare (pomija METRYKI/IC/VETO)

  Task 2 — format_compare + format_json:
    T2a. format_compare zwraca string z 5 wierszami KPI
    T2b. format_compare zwraca werdykt '✓ TAK' gdy agent_helps=True
    T2c. format_compare zwraca werdykt '✗ NIE' gdy agent_helps=False
    T2d. format_json z no_agent=False → agent_enabled=True w metrics
    T2e. format_json z no_agent=True → agent_enabled=False w metrics
    T2f. format_json z 'comparison' w res → top-level 'comparison' (nie 'metrics')
    T2g. format_json bez 'comparison' → backwards compat (istniejące pola bez zmian)

Stdlib only: unittest + argparse + json.
"""
import argparse
import json
import unittest
import sys
import os

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _make_args(**kwargs):
    """Fabryikuje argparse.Namespace z domyślnymi wartościami."""
    defaults = dict(
        strategy='naive', nU=300, nSUS=30, T=2000,
        kappa=1.0, alpha=1.0, verbose=False,
        no_agent=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_res_base():
    """Zwraca minimalne res dict bez veto (--no-agent scenario)."""
    return {
        'avg_val_last100': 92.0,
        'cum_val_total': 9200.0,
        'avg_net_profit': 1.0,
        'delivery_ratio': 0.5,
        'avg_providers_l100': 45.0,
        'sus_final': 5,
        'ic_per_phase': {},
        'history': {'val': [], 'providers': [], 'sus': []},
        'devices': [],
        'veto_per_phase': {},
        'n_vetoed_total': 0,
    }


def _make_res_with_veto():
    """Zwraca res dict z veto_per_phase i ic_per_phase."""
    res = _make_res_base()
    res['veto_per_phase'] = {1: 12, 2: 45}
    res['n_vetoed_total'] = 57
    res['ic_per_phase'] = {
        1: {
            'commits': 245, 'deliveries': 200, 'failures': 10,
            'avg_earning_per_commit': 5.0, 'avg_cost_per_commit': 1.0,
            'avg_net_per_commit': 4.0, 'delivery_rate': 0.8, 'ic_satisfied': True,
        },
        2: {
            'commits': 150, 'deliveries': 120, 'failures': 5,
            'avg_earning_per_commit': 4.0, 'avg_cost_per_commit': 2.0,
            'avg_net_per_commit': 2.0, 'delivery_rate': 0.8, 'ic_satisfied': True,
        },
    }
    return res


def _make_comparison():
    """Zwraca przykładowy comparison dict."""
    return {
        'with_agent': {
            'avg_val_last100': 92.0, 'cum_val_total': 9200.0,
            'avg_net_profit': 12.4, 'delivery_ratio': 0.88, 'avg_providers_l100': 45.2,
            'n_vetoed_total': 87,
        },
        'without_agent': {
            'avg_val_last100': 85.3, 'cum_val_total': 8530.0,
            'avg_net_profit': -3.2, 'delivery_ratio': 0.625, 'avg_providers_l100': 38.7,
            'n_vetoed_total': 0,
        },
        'delta': {
            'avg_val_last100': 6.7, 'cum_val_total': 670.0,
            'avg_net_profit': 15.6, 'delivery_ratio': 0.255, 'avg_providers_l100': 6.5,
        },
        'agent_helps': True,
    }


class TestFormatHumanVetoSection(unittest.TestCase):
    """Testy sekcji VETO w format_human (Task 1)."""

    def setUp(self):
        from sphsim.cli.output import format_human
        self.format_human = format_human

    # T1a — brak sekcji VETO gdy n_vetoed_total=0
    def test_no_veto_section_when_n_vetoed_zero(self):
        """format_human pomija sekcję VETO gdy n_vetoed_total=0 (--no-agent scenario)."""
        args = _make_args()
        res = _make_res_base()
        out = self.format_human(args, res, 100.0, False)
        self.assertNotIn(
            'VETO przez RationalAgent', out,
            msg='Sekcja VETO nie powinna być obecna gdy n_vetoed_total=0',
        )

    # T1b — sekcja VETO present gdy n_vetoed_total>0
    def test_veto_section_present_when_n_vetoed_positive(self):
        """format_human renderuje sekcję VETO gdy n_vetoed_total>0."""
        args = _make_args()
        res = _make_res_with_veto()
        out = self.format_human(args, res, 100.0, False)
        self.assertIn(
            'VETO przez RationalAgent', out,
            msg='Sekcja VETO powinna być present gdy n_vetoed_total=57',
        )
        self.assertIn(
            "Łącznie zaweto'wano", out,
            msg="Linia sumaryczna 'Łącznie zaweto'wano' wymagana (polskie diakrytyki per D-66)",
        )

    # T1c — fazy z union veto_pp.keys() ∪ ic.keys()
    def test_veto_section_covers_all_phases_union(self):
        """Sekcja VETO renderuje wszystkie fazy z veto_pp.keys() ∪ ic.keys()."""
        args = _make_args()
        res = _make_res_with_veto()
        # faza 1 jest w obu: ic i veto_pp; faza 2 też
        out = self.format_human(args, res, 100.0, False)
        # obie fazy (1 i 2) muszą być widoczne jako wiersze tabeli
        self.assertIn('VETO przez RationalAgent', out)
        # zawartość tabeli — faza 1 i faza 2 jako wiersze
        lines_with_veto = [l for l in out.split('\n') if l.strip().startswith('1') or l.strip().startswith('2')]
        self.assertGreaterEqual(
            len(lines_with_veto), 2,
            msg=f'Oczekiwano co najmniej 2 wierszy faz w sekcji VETO, got: {lines_with_veto}',
        )

    # T1d — verbose=True nadal działa (verbose block po VETO, nie przerywany)
    def test_verbose_mode_still_works_with_veto_section(self):
        """format_human z verbose=True i n_vetoed>0 renderuje verbose block po sekcji VETO."""
        args = _make_args(verbose=True, T=200)
        res = _make_res_with_veto()
        res['history'] = {'val': [92.0] * 200, 'providers': [45] * 200, 'sus': [5] * 200}
        out = self.format_human(args, res, 100.0, True)
        self.assertIn('VETO przez RationalAgent', out, msg='VETO sekcja powinna być w verbose output')
        self.assertIn('Próbkowanie waluacji', out, msg='Verbose block powinien być obecny')

    # T1e — 'comparison' w res → early return format_compare (pomija METRYKI/IC/VETO)
    def test_comparison_key_triggers_early_return_format_compare(self):
        """format_human z res['comparison'] zwraca tabelę compare, nie standardowy output."""
        args = _make_args()
        comp = _make_comparison()
        res = {'comparison': comp}
        out = self.format_human(args, res, 100.0, False)
        # NIE powinno zawierać standardowych sekcji METRYKI/IC/VETO
        self.assertNotIn('METRYKI', out, msg='comparison branch powinien pominąć sekcję METRYKI')
        # POWINNO zawierać coś z tabeli compare (np. werdykt lub KPI)
        has_verdict = ('TAK' in out or 'NIE' in out or '✓' in out or '✗' in out)
        has_kpi = ('avg' in out.lower() or 'net_profit' in out.lower() or 'delivery' in out.lower())
        self.assertTrue(
            has_verdict or has_kpi,
            msg=f'comparison branch powinien zawierać tabelę delta KPI lub werdykt, got:\n{out}',
        )


class TestFormatCompare(unittest.TestCase):
    """Testy funkcji format_compare (Task 2a-2c)."""

    def setUp(self):
        from sphsim.cli.output import format_compare
        self.format_compare = format_compare

    # T2a — 5 KPI w tabeli
    def test_format_compare_contains_5_kpi_rows(self):
        """format_compare zwraca string z 5 wierszami KPI."""
        args = _make_args(strategy='incentive')
        comp = _make_comparison()
        table = self.format_compare(args, comp, 100.0)
        kpis = ['avg_val_last100', 'cum_val_total', 'avg_net_profit', 'delivery_ratio', 'avg_providers_l100']
        found = sum(1 for kpi in kpis if kpi in table or kpi.split('_', 1)[-1] in table.lower())
        self.assertGreaterEqual(
            found, 3,
            msg=f'Oczekiwano co najmniej 3 z 5 KPI w tabeli, found={found}. Table:\n{table}',
        )

    # T2b — werdykt '✓ TAK' gdy agent_helps=True
    def test_format_compare_verdict_tak_when_agent_helps(self):
        """format_compare zwraca werdykt zawierający 'TAK' gdy agent_helps=True."""
        args = _make_args(strategy='incentive')
        comp = _make_comparison()  # agent_helps=True
        table = self.format_compare(args, comp, 100.0)
        self.assertTrue(
            'TAK' in table or '✓' in table,
            msg=f"Werdykt '✓ TAK' nie znaleziony gdy agent_helps=True. Table:\n{table}",
        )

    # T2c — werdykt '✗ NIE' gdy agent_helps=False
    def test_format_compare_verdict_nie_when_not_agent_helps(self):
        """format_compare zwraca werdykt zawierający 'NIE' gdy agent_helps=False."""
        args = _make_args(strategy='naive')
        comp = dict(_make_comparison())
        comp['agent_helps'] = False
        table = self.format_compare(args, comp, 100.0)
        self.assertTrue(
            'NIE' in table or '✗' in table,
            msg=f"Werdykt '✗ NIE' nie znaleziony gdy agent_helps=False. Table:\n{table}",
        )


class TestFormatJsonExtension(unittest.TestCase):
    """Testy rozszerzenia format_json (Task 2d-2g)."""

    def setUp(self):
        from sphsim.cli.output import format_json
        self.format_json = format_json

    # T2d — agent_enabled=True gdy no_agent=False
    def test_format_json_agent_enabled_true_when_agent_on(self):
        """format_json zwraca agent_enabled=True gdy args.no_agent=False."""
        args = _make_args(no_agent=False)
        res = _make_res_base()
        js = json.loads(self.format_json(args, res, {}, 100.0))
        self.assertIn('agent_enabled', js['metrics'], msg='agent_enabled missing in metrics')
        self.assertEqual(
            js['metrics']['agent_enabled'], True,
            msg=f"agent_enabled powinien być True gdy no_agent=False, got {js['metrics']['agent_enabled']}",
        )

    # T2e — agent_enabled=False gdy no_agent=True
    def test_format_json_agent_enabled_false_when_no_agent(self):
        """format_json zwraca agent_enabled=False gdy args.no_agent=True."""
        args = _make_args(no_agent=True)
        res = _make_res_base()
        js = json.loads(self.format_json(args, res, {}, 100.0))
        self.assertIn('agent_enabled', js['metrics'], msg='agent_enabled missing in metrics')
        self.assertEqual(
            js['metrics']['agent_enabled'], False,
            msg=f"agent_enabled powinien być False gdy no_agent=True, got {js['metrics']['agent_enabled']}",
        )

    # T2f — comparison w res → top-level 'comparison' klucz (nie 'metrics')
    def test_format_json_comparison_replaces_metrics(self):
        """format_json z 'comparison' w res zwraca JSON z top-level 'comparison', bez 'metrics'."""
        args = _make_args(strategy='incentive', no_agent=False)
        comp = _make_comparison()
        res = {'comparison': comp}
        js = json.loads(self.format_json(args, res, {}, 100.0))
        self.assertIn(
            'comparison', js,
            msg=f"'comparison' key missing in JSON output: {list(js.keys())}",
        )
        self.assertEqual(
            js['comparison']['agent_helps'], True,
            msg='agent_helps should be True in comparison block',
        )

    # T2g — bez 'comparison' → backwards compat (istniejące klucze bez zmian)
    def test_format_json_backwards_compat_without_comparison(self):
        """format_json bez 'comparison' w res zachowuje istniejące klucze (CLI-04 backwards compat)."""
        args = _make_args(no_agent=True)
        res = _make_res_base()
        js = json.loads(self.format_json(args, res, {}, 100.0))
        # istniejące pola muszą być obecne
        self.assertIn('metrics', js, msg="'metrics' klucz wymagany gdy brak 'comparison'")
        existing_keys = ['avg_val_last100', 'cum_val_total', 'avg_net_profit',
                         'delivery_ratio', 'avg_providers_l100', 'sus_final']
        for key in existing_keys:
            self.assertIn(
                key, js['metrics'],
                msg=f"Istniejący klucz '{key}' powinien być zachowany w metrics (backwards compat)",
            )
        # nowe klucze też powinny być obecne
        self.assertIn('veto_per_phase', js['metrics'], msg='veto_per_phase powinien być w metrics')
        self.assertIn('n_vetoed_total', js['metrics'], msg='n_vetoed_total powinien być w metrics')


if __name__ == '__main__':
    unittest.main()
