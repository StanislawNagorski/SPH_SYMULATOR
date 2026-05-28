"""
Test stubs dla Phase 8 — Documentation (DOC-01, DOC-02, EX-01).

Wave 0 scaffolding: wszystkie testy są @unittest.skip z powodem wskazującym
na wave i plan, który dostarczy implementację. Stub body to self.fail() aby
usunięcie skip nie dawało fałszywego zielonego.

Pokrywa 3 klasy:
  1. TestPrzewodnik     — DOC-01: docs/PRZEWODNIK.md z wymaganymi sekcjami
  2. TestAssets         — DOC-02: docs/assets/*.png z prawidłową sygnaturą PNG
  3. TestExamplesAudit  — EX-01: przykłady w PRZEWODNIK.md zgodne z 08-UAT.md

Stdlib only: unittest + os + sys.
"""
import os
import sys
import unittest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# PNG magic bytes — reużywalne przez przyszłą implementację TestAssets.
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'


class TestPrzewodnik(unittest.TestCase):
    """DOC-01: docs/PRZEWODNIK.md istnieje i zawiera wymagane sekcje."""

    @unittest.skip("Wave 3 — plan 08-06 creates docs/PRZEWODNIK.md")
    def test_przewodnik_exists_with_required_sections(self):
        self.fail("not yet implemented — see skip reason")


class TestAssets(unittest.TestCase):
    """DOC-02: docs/assets/*.png istnieją i mają prawidłową sygnaturę PNG."""

    @unittest.skip("Wave 3 — plan 08-05 generates docs/assets/*.png")
    def test_assets_pngs_present_and_valid(self):
        self.fail("not yet implemented — see skip reason")


class TestExamplesAudit(unittest.TestCase):
    """EX-01: przykłady w PRZEWODNIK.md odpowiadają źródłom z 08-UAT.md (adnotacja # Z 08-UAT.md test #N)."""

    @unittest.skip("Wave 3 — plan 08-06 generates PRZEWODNIK.md examples annotated with `# Z 08-UAT.md test #N`")
    def test_examples_in_przewodnik_match_uat_sources(self):
        self.fail("not yet implemented — see skip reason")


if __name__ == '__main__':
    unittest.main()
