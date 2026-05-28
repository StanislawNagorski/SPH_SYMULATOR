#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  verify_phase8.sh — phase exit gate dla Phase 8 (Documentation + Interactive Tutorial)
#  Plan 08-07 — Wave 4 closeout (mirrors verify_phase7.sh structure)
#
#  Phase 8 covers TUT-01..TUT-06 + DOC-01 + DOC-02 + EX-01 + GATE-01.
#  Phase 8 exit gate runs all SC checks below; partial pass blocks merge.
#
#  Phase 8 Success Criteria (ROADMAP goal):
#    "Nowy użytkownik bez znajomości projektu potrafi w ≤15 minut: przeczytać
#     docs/PRZEWODNIK.md i uruchomić --tutorial (lub `tutorial` w REPL),
#     przechodząc krok-po-kroku przez wszystkie zdolności v1.1 z opcją skip."
#
#  Categories (7):
#    A. docs/PRZEWODNIK.md istnieje + 5 wymaganych nagłówków + Lead pointer (DOC-01)
#    B. docs/assets/*.png — 3 PNGs z prawidłową sygnaturą magic bytes (DOC-02)
#    C. --tutorial CLI flag w pomocy + 5-way mutex + post-parse "Musisz podać" (TUT-05)
#    D. REPL tutorial command + 4 control verbs + non-skip ✓ zaliczone (TUT-01/02/03/04 + GATE-01)
#    E. Tutorial reports → ./reports/tutorial-<ts>/step-N-<topic>/ (TUT-06)
#    F. Source assertions (TUT-01: do_tutorial/precmd/postcmd/TutorialFlow/report_dir_override)
#    G. Regression PASS=8/8 + full unittest discover + Phase 8 modules (CLI-04 + DOC-01/02 + EX-01)
#
#  Re-runnable po każdej zmianie w sphsim/ jako pre-flight przed merge'em.
#  Stdlib + POSIX coreutils only — bez nowych zależności.
#
#  Exit code: 0 gdy wszystkie checks PASS, 1 gdy jakikolwiek FAIL.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

# Przejdź do project root (skrypt może być wywołany skądkolwiek).
cd "$(dirname "$0")/.."

# Wybierz interpreter Pythona — preferuj python, fallback na python3.
if command -v python >/dev/null 2>&1; then
    PY=python
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "FATAL: ani 'python' ani 'python3' nie ma w PATH" >&2
    exit 1
fi

# Cleanup tmp files na exit (trap — nawet przy FAIL).
trap 'rm -f /tmp/p8_*' EXIT

PASS=0
FAIL=0

# Helper: uruchom komendę, drukuj [PASS] albo [FAIL] z hintem + ostatnimi 20 liniami log'u.
check() {
    local desc="$1"
    local cmd="$2"
    if eval "$cmd" > /tmp/p8_check.log 2>&1; then
        echo "[PASS] $desc"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $desc"
        echo "       cmd: $cmd"
        echo "       log:"
        sed 's/^/         /' /tmp/p8_check.log | head -20
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Phase 8: Documentation + Interactive Tutorial — verification ==="
echo "Interpreter: $PY ($($PY --version 2>&1))"
echo ""

# Pre-flight cleanup
rm -rf ./reports/tutorial-* ./reports/batch_* ./reports/[0-9]*

echo ""
echo "── Category A. docs/PRZEWODNIK.md exists + 5 D-11 sections + Lead pointer (DOC-01) ──"
check "A1 (DOC-01): docs/PRZEWODNIK.md exists" \
    "test -f docs/PRZEWODNIK.md"
check "A2 (DOC-01 §1): '## Szybki start' section present" \
    "grep -F '## Szybki start' docs/PRZEWODNIK.md"
check "A3 (DOC-01 §2): '## Interaktywny tutorial' section present" \
    "grep -F '## Interaktywny tutorial' docs/PRZEWODNIK.md"
check "A4 (DOC-01 §3): '## Opis funkcjonalności v1.1' section present" \
    "grep -F '## Opis funkcjonalności v1.1' docs/PRZEWODNIK.md"
check "A5 (DOC-01 §4): '## Referencja' section present" \
    "grep -F '## Referencja' docs/PRZEWODNIK.md"
check "A6 (DOC-01 §5): '## Teoria' section present" \
    "grep -F '## Teoria' docs/PRZEWODNIK.md"
check "A7 (DOC-01 Lead): pierwsze 15 linii wskazują na --tutorial" \
    "head -15 docs/PRZEWODNIK.md | grep -F -- '--tutorial'"

echo ""
echo "── Category B. docs/assets/*.png — 3 PNGs z prawidłową sygnaturą magic bytes (DOC-02) ──"
check "B1 (DOC-02): docs/assets/decision_distribution_naive.png — valid PNG magic (\\x89PNG)" \
    "$PY -c \"import sys; d=open('docs/assets/decision_distribution_naive.png','rb').read(8); sys.exit(0 if d == b'\\x89PNG\\r\\n\\x1a\\n' else 1)\""
check "B2 (DOC-02): docs/assets/kpi_timeseries_naive.png — valid PNG magic (\\x89PNG)" \
    "$PY -c \"import sys; d=open('docs/assets/kpi_timeseries_naive.png','rb').read(8); sys.exit(0 if d == b'\\x89PNG\\r\\n\\x1a\\n' else 1)\""
check "B3 (DOC-02): docs/assets/batch_aggregate_naive.png — valid PNG magic (\\x89PNG)" \
    "$PY -c \"import sys; d=open('docs/assets/batch_aggregate_naive.png','rb').read(8); sys.exit(0 if d == b'\\x89PNG\\r\\n\\x1a\\n' else 1)\""

echo ""
echo "── Category C. --tutorial CLI flag + 5-way mutex + required-mode fallback (TUT-05) ──"
check "C1 (TUT-05): --tutorial widoczna w --help" \
    "$PY sph_sim.py --tutorial --help 2>&1 | grep -F -- '--tutorial'"
check "C2 (TUT-05 mutex): --tutorial --interactive → 'Flagi --tutorial i --interactive są wzajemnie wykluczające'" \
    "{ $PY sph_sim.py --tutorial --interactive 2>&1 || true; } | grep -F 'Flagi --tutorial i --interactive są wzajemnie wykluczające'"
check "C3 (TUT-05 mutex): --tutorial --strategy naive → 'Flaga --tutorial nie działa z --strategy'" \
    "{ $PY sph_sim.py --tutorial --strategy naive 2>&1 || true; } | grep -F 'Flaga --tutorial nie działa z --strategy'"
check "C4 (TUT-05 mutex): --tutorial --custom ... → 'Flaga --tutorial nie działa z --custom'" \
    "{ $PY sph_sim.py --tutorial --custom examples/custom_strategy_template.py 2>&1 || true; } | grep -F 'Flaga --tutorial nie działa z --custom'"
check "C5 (TUT-05 mutex): --tutorial --batch --seeds 5 → 'Flagi --tutorial i --batch są wzajemnie wykluczające'" \
    "{ $PY sph_sim.py --tutorial --batch --seeds 5 2>&1 || true; } | grep -F 'Flagi --tutorial i --batch są wzajemnie wykluczające'"
check "C6 (TUT-05 mutex): --tutorial --compare-agent → 'Flagi --tutorial i --compare-agent są wzajemnie wykluczające'" \
    "{ $PY sph_sim.py --tutorial --compare-agent 2>&1 || true; } | grep -F 'Flagi --tutorial i --compare-agent są wzajemnie wykluczające'"
check "C7 (TUT-05 fallback): bare sph_sim.py → 'Musisz podać jeden z trybów'" \
    "{ $PY sph_sim.py 2>&1 || true; } | grep -F 'Musisz podać jeden z trybów'"

echo ""
echo "── Category D. REPL tutorial command + 4 controls + non-skip ✓ zaliczone (TUT-01/02/03/04 + GATE-01) ──"
check "D1 (TUT-01 help): 'tutorial' widoczne w 'help' REPL listy" \
    "printf 'help\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | grep -F 'tutorial'"
check "D2 (TUT-01 banner + step1): 'tutorial' w REPL pokazuje banner i [krok 1/8" \
    "printf 'tutorial\\nexit\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | grep -F 'INTERAKTYWNY TUTORIAL' && printf 'tutorial\\nexit\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | grep -F '[krok 1/8'"
check "D3 (TUT-02 skip): 8 skipów dochodzi do 'pominięto — krok 8/8'" \
    "rm -rf ./reports/tutorial-* ./reports/batch_* ./reports/[0-9]*; printf 'tutorial\\nskip\\nskip\\nskip\\nskip\\nskip\\nskip\\nskip\\nskip\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | grep -F 'pominięto — krok 8/8'"
check "D4 (GATE-01 non-skip): step 1 verification fires '✓ zaliczone — krok 1/8' po 'run naive zeta=0.75'" \
    "rm -rf ./reports/tutorial-* ./reports/batch_* ./reports/[0-9]*; printf 'tutorial\\nrun naive zeta=0.75\\nexit\\nexit\\n' | SPHSIM_NO_REPORT='' $PY sph_sim.py --interactive 2>&1 | grep -F '✓ zaliczone — krok 1/8'"
check "D5 (TUT-03 back boundary): 'back' na kroku 1 → 'Już jesteś na pierwszym kroku.'" \
    "printf 'tutorial\\nback\\nexit\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | grep -F 'Już jesteś na pierwszym kroku.'"
check "D6 (TUT-04 Pitfall 1): 'exit' w tutorial nie kończy REPL — 'Tutorial opuszczony'" \
    "printf 'tutorial\\nexit\\nstrategies\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | grep -F 'Tutorial opuszczony'"
check "D7 (TUT-05 E2E): 'python sph_sim.py --tutorial' uruchamia tutorial — banner widoczny" \
    "printf 'exit\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --tutorial 2>&1 | grep -F 'INTERAKTYWNY TUTORIAL'"

echo ""
echo "── Category E. Tutorial reports → ./reports/tutorial-<ts>/step-N-<topic>/ (TUT-06) ──"
check "E1 (TUT-06): tutorial run tworzy ./reports/tutorial-<ts>/step-1-baseline/report.md" \
    "rm -rf ./reports/tutorial-* ./reports/batch_* ./reports/[0-9]*; printf 'tutorial\\nrun naive zeta=0.75\\nexit\\nexit\\n' | SPHSIM_NO_REPORT='' $PY sph_sim.py --interactive > /tmp/p8_tut.log 2>&1; ls -d ./reports/tutorial-*/step-1-baseline/ 2>/dev/null | head -1 | grep -F 'step-1-baseline' && ls ./reports/tutorial-*/step-1-baseline/report.md"
check "E2 (TUT-06 backwards-compat): non-tutorial run NIE tworzy tutorial-<ts>/ dir" \
    "rm -rf ./reports/tutorial-* ./reports/batch_* ./reports/[0-9]*; printf 'run naive zeta=0.75\\nexit\\n' | SPHSIM_NO_REPORT='' $PY sph_sim.py --interactive > /tmp/p8_nontut.log 2>&1; ls -d ./reports/[0-9]*/ > /dev/null 2>&1 && ! ls -d ./reports/tutorial-*/ > /dev/null 2>&1"

# Cleanup po Category E przed source-only checks
rm -rf ./reports/tutorial-* ./reports/batch_* ./reports/[0-9]*

echo ""
echo "── Category F. Source assertions (TUT-01 verification) ──"
check "F1 (TUT-01 src): sphsim/cli/repl.py ma 'def do_tutorial'" \
    "grep -E '^\\s*def do_tutorial' sphsim/cli/repl.py"
check "F2 (TUT-01 src): sphsim/cli/repl.py ma 'def precmd' (control verb interception)" \
    "grep -E '^\\s*def precmd' sphsim/cli/repl.py"
check "F3 (TUT-01 src): sphsim/cli/repl.py ma 'def postcmd' (step verification dispatch)" \
    "grep -E '^\\s*def postcmd' sphsim/cli/repl.py"
check "F4 (TUT-01 src): sphsim/cli/tutorial.py istnieje + ma 'class TutorialFlow'" \
    "test -f sphsim/cli/tutorial.py && grep -F 'class TutorialFlow' sphsim/cli/tutorial.py"
check "F5 (TUT-06 src): sphsim/report/__init__.py wspiera 'report_dir_override'" \
    "grep -F 'report_dir_override' sphsim/report/__init__.py"

echo ""
echo "── Category G. Regression + full unittest discover + Phase 8 modules (CLI-04 + DOC-01/02 + EX-01) ──"
check "G1 (CLI-04 regression): scripts/regression_check.py PASS: 8/8 (baseline JSON byte-identical)" \
    "$PY scripts/regression_check.py 2>&1 | grep -F 'PASS: 8/8'"
check "G2 (full suite): SPHSIM_NO_REPORT=1 python -m unittest discover tests → OK (all 23+ modules green)" \
    "SPHSIM_NO_REPORT=1 $PY -m unittest discover tests > /tmp/p8_discover.log 2>&1 && grep -E '^OK' /tmp/p8_discover.log"
check "G3 (Phase 8 modules): tests.test_tutorial + tests.test_docs → OK (TUT-01..TUT-06 + DOC-01/02 + EX-01)" \
    "SPHSIM_NO_REPORT=1 $PY -m unittest tests.test_tutorial tests.test_docs > /tmp/p8_phase8tests.log 2>&1 && grep -E '^OK' /tmp/p8_phase8tests.log"

# Category H — Final cleanup: usuń wszystkie reports/<ts>/ generowane przez smoke tests.
rm -rf ./reports/tutorial-* ./reports/batch_* ./reports/[0-9]*

# ── Summary ──
echo ""
echo "════════════════════════════════════════"
echo "  Phase 8 verification: PASS=$PASS / FAIL=$FAIL"
echo "════════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
    echo "✗ Phase 8 NIE jest gotowe — popraw FAIL'e powyżej."
    exit 1
fi
echo "✓ Phase 8 ready for /gsd:verify-work"
exit 0
