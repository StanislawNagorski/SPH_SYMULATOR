"""
Unit tests dla sphsim.agent.__init__ (Phase 4, Task 1 TDD RED).

Pokrywa:
  1. from sphsim.agent import wrap_with_agent działa bez ImportError
  2. wrap_with_agent jest callable
  3. 'wrap_with_agent' w __all__
  4. docstring modułu po polsku odnoszący się do Phase 4

Stdlib only: unittest + importlib.
"""

import os
import sys
import unittest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class TestAgentPackageInit(unittest.TestCase):
    """Testy importu pakietu sphsim.agent i eksportu wrap_with_agent."""

    def test_import_wrap_with_agent_no_error(self):
        """from sphsim.agent import wrap_with_agent nie rzuca ImportError."""
        try:
            from sphsim.agent import wrap_with_agent  # noqa: F401
        except ImportError as e:
            self.fail(f"ImportError przy from sphsim.agent import wrap_with_agent: {e}")

    def test_wrap_with_agent_is_callable(self):
        """wrap_with_agent musi być callable (fabryka closures)."""
        import sphsim.agent
        self.assertTrue(
            callable(sphsim.agent.wrap_with_agent),
            msg=f"sphsim.agent.wrap_with_agent nie jest callable: {type(sphsim.agent.wrap_with_agent)}",
        )

    def test_all_contains_wrap_with_agent(self):
        """sphsim.agent.__all__ musi zawierać 'wrap_with_agent'."""
        import sphsim.agent
        self.assertIn(
            'wrap_with_agent',
            sphsim.agent.__all__,
            msg=f"'wrap_with_agent' nie w __all__: {sphsim.agent.__all__}",
        )

    def test_module_docstring_exists(self):
        """Moduł sphsim.agent musi mieć docstring (policy: polski docstring Phase 4)."""
        import sphsim.agent
        self.assertIsNotNone(
            sphsim.agent.__doc__,
            msg="sphsim.agent nie ma docstringa",
        )
        self.assertGreater(
            len(sphsim.agent.__doc__),
            10,
            msg=f"Docstring za krótki: {sphsim.agent.__doc__!r}",
        )


if __name__ == '__main__':
    unittest.main()
