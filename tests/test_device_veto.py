"""
Unit tests dla rozszerzenia Device o n_vetoed + veto_phase_stats (Phase 4, D-63/D-64).

Pokrywa:
  1. Device ma pole n_vetoed: int = 0 (dataclass field)
  2. Device.__post_init__ inicjalizuje veto_phase_stats = {}
  3. veto_phase_stats jest per-instance (nie shared dict)
  4. n_vetoed jest widoczny w dataclasses.fields(Device)
  5. Istniejące pola licznikowe nie zostały zepsute

Stdlib only: unittest + dataclasses (zgodne z PROJECT.md constraint stdlib-only).
"""
import unittest
from dataclasses import fields

import os
import sys
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from sphsim.core.device import Device


class TestDeviceVetoFields(unittest.TestCase):
    """Testy rozszerzenia Device o veto bookkeeping (D-63)."""

    def test_n_vetoed_default_zero(self):
        """Nowe pole n_vetoed: int = 0 — default wartość = 0."""
        d = Device(id=0, phase=1, status='UP')
        self.assertEqual(d.n_vetoed, 0,
                         msg=f'n_vetoed should be 0 by default, got {d.n_vetoed!r}')

    def test_veto_phase_stats_empty_dict(self):
        """__post_init__ inicjalizuje veto_phase_stats = {} (pusty dict)."""
        d = Device(id=0, phase=1, status='UP')
        self.assertIsInstance(d.veto_phase_stats, dict,
                              msg='veto_phase_stats should be a dict')
        self.assertEqual(d.veto_phase_stats, {},
                         msg=f'veto_phase_stats should be empty dict, got {d.veto_phase_stats!r}')

    def test_veto_phase_stats_per_instance(self):
        """veto_phase_stats jest per-instance — modyfikacja jednego nie psuje drugiego (T-04-01)."""
        d1 = Device(id=0, phase=1, status='UP')
        d2 = Device(id=1, phase=2, status='UP')
        d1.veto_phase_stats[1] = 5
        self.assertEqual(d2.veto_phase_stats, {},
                         msg='Modifying d1.veto_phase_stats must not affect d2')

    def test_n_vetoed_in_dataclass_fields(self):
        """n_vetoed musi być widoczny w dataclasses.fields(Device)."""
        field_names = [f.name for f in fields(Device)]
        self.assertIn('n_vetoed', field_names,
                      msg=f'n_vetoed missing in fields: {field_names}')

    def test_existing_counters_intact(self):
        """Istniejące pola licznikowe (n_commit, n_abstain, n_delivered, n_failed) nie zepsute."""
        d = Device(id=0, phase=1, status='UP')
        self.assertEqual(d.n_commit, 0)
        self.assertEqual(d.n_abstain, 0)
        self.assertEqual(d.n_delivered, 0)
        self.assertEqual(d.n_failed, 0)

    def test_phase_stats_still_initialized(self):
        """Istniejący phase_stats nadal inicjalizowany w __post_init__."""
        d = Device(id=0, phase=1, status='UP')
        self.assertEqual(d.phase_stats, {},
                         msg='phase_stats should still be {} after adding veto_phase_stats')

    def test_n_vetoed_mutable(self):
        """n_vetoed jest mutowalny (wrapper agenta może go inkrementować)."""
        d = Device(id=0, phase=1, status='UP')
        d.n_vetoed += 1
        self.assertEqual(d.n_vetoed, 1,
                         msg='n_vetoed should be incrementable')

    def test_veto_phase_stats_mutable(self):
        """veto_phase_stats przyjmuje wpisy {phase: count}."""
        d = Device(id=0, phase=2, status='UP')
        d.veto_phase_stats[2] = d.veto_phase_stats.get(2, 0) + 1
        self.assertEqual(d.veto_phase_stats, {2: 1},
                         msg='veto_phase_stats should accept {phase: count} entries')


if __name__ == '__main__':
    unittest.main()
