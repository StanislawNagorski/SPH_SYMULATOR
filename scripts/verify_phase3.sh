#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  verify_phase3.sh — phase exit gate dla Phase 3 (custom strategy loader)
#  Plan 03-04 — Final audit script
#
#  Weryfikuje wszystkie 5 ROADMAP Phase 3 Success Criteria + regression
#  + Phase 2 invariant + Plan 01 loader tests + mutex enforcement:
#
#    SC #1: --custom (CLI) + custom (REPL) ładują plik .py
#    SC #2: Loader sprawdza obecność funkcji + polskie komunikaty z konkretem
#    SC #3: examples/custom_strategy_template.py kompiluje + ładuje + uruchamia
#           deterministycznie + daje sensowne wyniki KPI
#    SC #4: custom strategia widoczna w `strategies` z suffixem [custom]
#    SC #5: Loader komunikuje banner [OSTRZEŻENIE] PRZED importem
#
#  Plus regression (CLI-04 backwards compat z Phase 1) i Phase 2 invariant
#  + Plan 01 loader 21/21 unit testów + pełny unittest discover.
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
trap 'rm -f /tmp/p3_*' EXIT

PASS=0
FAIL=0

# Helper: uruchom komendę, drukuj [PASS] albo [FAIL] z hintem + ostatnimi 20 liniami log'u.
check() {
    local desc="$1"
    local cmd="$2"
    if eval "$cmd" > /tmp/p3_check.log 2>&1; then
        echo "[PASS] $desc"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $desc"
        echo "       cmd: $cmd"
        echo "       log:"
        sed 's/^/         /' /tmp/p3_check.log | head -20
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Phase 3: Custom strategy loader — verification ==="
echo "Interpreter: $PY ($($PY --version 2>&1))"
echo ""

# ── 1. Regression backwards compat (Phase 1 contract) ──
echo "── 1. Regression backwards compat (Phase 1 contract) ──"
check "Regression: 8/8 baseline_v1 fixtures" "$PY scripts/regression_check.py"

# ── 2. Invariant + loader unit tests ──
echo ""
echo "── 2. Invariant + loader unit tests ──"
check "Phase 2 invariant: STRATEGY_META ↔ argparse" "$PY -m unittest tests.test_strategy_meta_consistency"
check "Phase 3 loader: 21 unit cases (test_loader)" "$PY -m unittest tests.test_loader"
check "Full test discover (wszystkie 22 testy)" "$PY -m unittest discover tests"

# ── 3. SC #3: examples/custom_strategy_template.py ──
echo ""
echo "── 3. SC #3: examples/custom_strategy_template.py ──"
check "Template kompiluje bez ostrzeżeń (py_compile -W all)" \
    "$PY -W all -m py_compile examples/custom_strategy_template.py"
check "Template ładuje się przez loader (basename + fn + meta)" \
    "$PY -c \"from sphsim.strategies.loader import load_custom; n,fn,m = load_custom('examples/custom_strategy_template.py'); assert n == 'custom_strategy_template' and callable(fn) and m['description']\""
check "Template uruchamia się przez CLI --custom (exit 0)" \
    "$PY sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json > /tmp/p3_template.txt 2>/dev/null"
check "Template output: valid JSON ze strategy=custom_strategy_template + avg_val_last100" \
    "tail -n +2 /tmp/p3_template.txt | $PY -c \"import json, sys; d = json.loads(sys.stdin.read()); assert d['strategy'] == 'custom_strategy_template' and 'avg_val_last100' in d['metrics']\""

# ── 4. SC #5: banner [OSTRZEŻENIE] pre-import ──
# Uwaga: pipefail + 'grep -q' powoduje SIGPIPE w upstream'ie gdy grep zamknie stdin
# wcześniej. Używamy `grep ... > /dev/null` (czyta cały stream, brak SIGPIPE).
echo ""
echo "── 4. SC #5: banner [OSTRZEŻENIE] pre-import ──"
check "Banner widoczny PRZED JSON outputem (linia 1 stdout)" \
    "$PY sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json 2>/dev/null | head -1 | grep '^\\[OSTRZEŻENIE\\] Ładuję arbitralny kod Pythona z:.*custom_strategy_template.py$' > /dev/null"

# ── 5. SC #2: polskie error messages z konkretem ──
# Loader celowo wychodzi exit code 1 przy błędach — owijamy w `{ ... ; true; }`
# żeby pipefail nie propagował niezerowego status'u python3 (grep ma wykryć ERROR
# STRING, nie exit code; semantyka SC #2 to "polski komunikat", nie "exit OK").
echo ""
echo "── 5. SC #2: polskie error messages z konkretem ──"
# Layer 1: nieistniejąca ścieżka → 'Plik nie istnieje'
check "Loader rzuca polski błąd dla nieistniejącej ścieżki" \
    "{ $PY sph_sim.py --custom /tmp/p3_nope_does_not_exist.py 2>&1 1>/dev/null || true; } | grep 'Plik nie istnieje' > /dev/null"

# Layer 3: zła sygnatura → 'Oczekiwana: (dev, l, s, phi, kappa, rho, h, p)'
cat > /tmp/p3_bad_sig.py <<'PYEOF'
def strategy_p3_bad_sig(dev, x, y):
    return 'COMMIT'
STRATEGY_META = {'description': 't', 'params': [], 'baseline_kpi': None}
PYEOF
check "Loader rzuca polski błąd dla złej sygnatury (Oczekiwana: 8 nazw)" \
    "{ $PY sph_sim.py --custom /tmp/p3_bad_sig.py 2>&1 1>/dev/null || true; } | grep 'Oczekiwana: (dev, l, s, phi, kappa, rho, h, p)' > /dev/null"

# Layer 2: brak funkcji → 'Brak funkcji'
cat > /tmp/p3_no_fn.py <<'PYEOF'
def inna_funkcja(dev, l, s, phi, kappa, rho, h, p):
    return 'COMMIT'
STRATEGY_META = {'description': 't', 'params': [], 'baseline_kpi': None}
PYEOF
check "Loader rzuca polski błąd dla braku funkcji strategy_<basename>" \
    "{ $PY sph_sim.py --custom /tmp/p3_no_fn.py 2>&1 1>/dev/null || true; } | grep 'Brak funkcji' > /dev/null"

# Layer 4: brak STRATEGY_META → 'nie eksportuje STRATEGY_META'
cat > /tmp/p3_no_meta.py <<'PYEOF'
def strategy_p3_no_meta(dev, l, s, phi, kappa, rho, h, p):
    return 'COMMIT'
PYEOF
check "Loader rzuca polski błąd dla braku STRATEGY_META" \
    "{ $PY sph_sim.py --custom /tmp/p3_no_meta.py 2>&1 1>/dev/null || true; } | grep 'nie eksportuje STRATEGY_META' > /dev/null"

# ── 6. SC #1 + SC #4: REPL custom + strategies [custom] + run ──
echo ""
echo "── 6. SC #1 + SC #4: REPL custom + strategies [custom] + run ──"
check "REPL ładuje custom + listuje z [custom] suffix" \
    "printf 'custom examples/custom_strategy_template.py\nstrategies\nexit\n' | $PY sph_sim.py --interactive 2>&1 | grep 'custom_strategy_template.*\\[custom\\]' > /dev/null"
check "REPL uruchamia custom przez run (Strategia: CUSTOM_STRATEGY_TEMPLATE w outputcie)" \
    "printf 'custom examples/custom_strategy_template.py\nrun custom_strategy_template max_phase=3\nexit\n' | $PY sph_sim.py --interactive 2>&1 | grep 'Strategia: CUSTOM_STRATEGY_TEMPLATE' > /dev/null"
check "REPL reload (D-38) drukuje 'Przeładowano custom strategię'" \
    "printf 'custom examples/custom_strategy_template.py\ncustom examples/custom_strategy_template.py\nexit\n' | $PY sph_sim.py --interactive 2>&1 | grep 'Przeładowano custom strategię' > /dev/null"

# ── 7. SC #1: CLI --custom determinism + param effect ──
echo ""
echo "── 7. SC #1: CLI --custom determinism + param effect ──"
check "Dwa uruchomienia template'a dają identyczny output (seed=42 reprodukcja)" \
    "$PY sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json 2>/dev/null | tail -n +2 > /tmp/p3_run1.json && $PY sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json 2>/dev/null | tail -n +2 > /tmp/p3_run2.json && diff -q /tmp/p3_run1.json /tmp/p3_run2.json"
check "Param --param max_phase= zmienia wynik (max_phase=2 vs max_phase=4)" \
    "$PY sph_sim.py --custom examples/custom_strategy_template.py --param max_phase=2 --seed 42 --json 2>/dev/null | tail -n +2 > /tmp/p3_mp2.json && $PY sph_sim.py --custom examples/custom_strategy_template.py --param max_phase=4 --seed 42 --json 2>/dev/null | tail -n +2 > /tmp/p3_mp4.json && ! diff -q /tmp/p3_mp2.json /tmp/p3_mp4.json > /dev/null"

# ── 8. D-44: mutex enforcement (interactive | strategy | custom) ──
echo ""
echo "── 8. D-44: mutex enforcement (interactive | strategy | custom) ──"
check "Mutex odrzuca --custom + --strategy jednocześnie" \
    "{ $PY sph_sim.py --custom foo.py --strategy naive 2>&1 || true; } | grep 'not allowed with argument' > /dev/null"
check "Mutex required: brak żadnego trybu → polski post-parse error (Phase 8: Plan 08-02 replaced argparse English fallback with Polish)" \
    "{ $PY sph_sim.py 2>&1 || true; } | grep 'Musisz podać jeden z trybów' > /dev/null"

# ── Summary ──
echo ""
echo "════════════════════════════════════════"
echo "  Phase 3 verification: PASS=$PASS / FAIL=$FAIL"
echo "════════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
    echo "✗ Phase 3 NIE jest gotowe — popraw FAIL'e powyżej."
    exit 1
fi
echo "✓ Phase 3 ready for /gsd:verify-work"
exit 0
