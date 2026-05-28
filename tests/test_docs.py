"""
Testy dla Phase 8 — Documentation (DOC-01, DOC-02, EX-01).

Trzy klasy:
  1. TestPrzewodnik     — DOC-01: docs/PRZEWODNIK.md z wymaganymi sekcjami
                         (Plan 08-06 dostarcza plik; tu strukturalna walidacja).
  2. TestAssets         — DOC-02: docs/assets/*.png z prawidłową sygnaturą PNG
                         (Plan 08-05 dostarcza pliki; tu nadal @unittest.skip
                         dopóki Plan 08-05 nie wyląduje w wave 3 merge).
  3. TestExamplesAudit  — EX-01: każda adnotacja `# Z 08-UAT.md test #N` lub
                         `# Z verify_phaseN.sh` w docs/PRZEWODNIK.md odpowiada
                         realnemu nagłówkowi/skryptowi (Plan 08-06).

Stdlib only: unittest + os + sys + re.
"""
import os
import re
import sys
import unittest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# PNG magic bytes — reużywalne przez TestAssets (Plan 08-05).
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'


class TestPrzewodnik(unittest.TestCase):
    """DOC-01: docs/PRZEWODNIK.md istnieje i zawiera wymagane sekcje (D-11)."""

    def _read_przewodnik(self):
        path = os.path.join(_PROJECT_ROOT, 'docs', 'PRZEWODNIK.md')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            self.fail('docs/PRZEWODNIK.md missing — Plan 08-06 must create it')

    def test_required_sections_present(self):
        src = self._read_przewodnik()
        for header in ['## Szybki start', '## Interaktywny tutorial',
                       '## Opis funkcjonalności v1.1', '## Referencja', '## Teoria']:
            self.assertIn(header, src, msg=f'Missing required section: {header}')

    def test_lead_points_at_tutorial_flag(self):
        src = self._read_przewodnik()
        # Lead is first ~15 lines after H1 (blockquote pointer per D-11).
        lead_chunk = '\n'.join(src.split('\n')[:15])
        self.assertIn('--tutorial', lead_chunk,
                      msg='Lead must point at `python sph_sim.py --tutorial` per D-11')

    def test_all_three_pngs_embedded(self):
        src = self._read_przewodnik()
        for png in ['assets/decision_distribution_naive.png',
                    'assets/kpi_timeseries_naive.png',
                    'assets/batch_aggregate_naive.png']:
            self.assertIn(png, src, msg=f'PNG embed missing: {png}')

    def test_theory_links_out(self):
        src = self._read_przewodnik()
        self.assertIn('PROMPT_DLA_AGENTA', src,
                      msg='Theory section must link to PROMPT_DLA_AGENTA.txt')
        self.assertIn('Raport.pdf', src,
                      msg='Theory section must link to Raport.pdf')


class TestAssets(unittest.TestCase):
    """DOC-02: docs/assets/*.png istnieją i mają prawidłową sygnaturę PNG."""

    @unittest.skip("Wave 3 — plan 08-05 generates docs/assets/*.png")
    def test_assets_pngs_present_and_valid(self):
        self.fail("not yet implemented — see skip reason")


class TestExamplesAudit(unittest.TestCase):
    """EX-01: każda adnotacja `# Z 08-UAT.md test #N` lub `# Z verify_phaseN.sh`
    w docs/PRZEWODNIK.md odpowiada realnemu źródłu (heading w 08-UAT.md lub
    plik skryptu w scripts/)."""

    def test_examples_in_przewodnik_match_uat_sources(self):
        przewodnik_path = os.path.join(_PROJECT_ROOT, 'docs', 'PRZEWODNIK.md')
        uat_path = os.path.join(_PROJECT_ROOT, '.planning', 'phases',
                                '07.1-comprehensive-uat', '08-UAT.md')
        with open(przewodnik_path, 'r', encoding='utf-8') as f:
            przewodnik = f.read()
        with open(uat_path, 'r', encoding='utf-8') as f:
            uat = f.read()

        # Find all `# Z 08-UAT.md test #N — ...` annotations
        pattern = re.compile(r'#\s*Z\s+08-UAT\.md\s+test\s+#(\d+)', re.IGNORECASE)
        cited_tests = sorted(set(int(m.group(1)) for m in pattern.finditer(przewodnik)))
        self.assertGreaterEqual(
            len(cited_tests), 6,
            msg=f'Expected >=6 distinct 08-UAT.md test references, '
                f'got {len(cited_tests)}: {cited_tests}',
        )

        # For each cited test number, verify 08-UAT.md actually has that test.
        # Observed heading format (verified during planning): `### N. Title` for
        # the 10 numbered tests, e.g. `### 1. Baseline Numerical Anchor`. Inline
        # cross-references may also use `Test #N` or `test #N`. The regex below
        # accepts any of these forms via a permissive alternation.
        for tn in cited_tests:
            heading_re = re.compile(rf'(?:###|[Tt]est)\s*#?{tn}\b')
            found = bool(heading_re.search(uat))
            self.assertTrue(
                found,
                msg=f'PRZEWODNIK.md cites 08-UAT.md test #{tn} but no matching '
                    f'heading (### N. ... | Test #N | test #N) found in 08-UAT.md',
            )

        # Also accept `# Z verify_phaseN.sh` citations — each must map to
        # a real script file in scripts/verify_phaseN.sh.
        verify_pattern = re.compile(r'#\s*Z\s+verify_phase(\d+)\.sh', re.IGNORECASE)
        verify_refs = set(int(m.group(1)) for m in verify_pattern.finditer(przewodnik))
        for vn in verify_refs:
            script_path = os.path.join(_PROJECT_ROOT, 'scripts', f'verify_phase{vn}.sh')
            self.assertTrue(
                os.path.exists(script_path),
                msg=f'PRZEWODNIK.md cites scripts/verify_phase{vn}.sh but file missing',
            )


if __name__ == '__main__':
    unittest.main()
