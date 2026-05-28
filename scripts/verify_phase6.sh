#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  verify_phase6.sh — phase exit gate dla Phase 6 (report + plots generator)
#  Plan 06-00 — Wave 0 skeleton (Plan 05 owns SC check() bodies)
#
#  Phase 6 covers REPORT-01..03 + PLOT-01..03 (matplotlib + markdown render).
#  Phase 6 exit gate runs all SC checks below; partial pass blocks merge.
#
#  Phase 6 Success Criteria:
#    SC #1: Każde uruchomienie symulacji tworzy ./reports/<ts>/ z 3 plikami (report.md + 2 PNG)
#    SC #2: report.md zawiera sekcje: konfiguracja, strategia, KPI table, rozkład decyzji, baseline
#    SC #3: decision_distribution.png + kpi_timeseries.png — wykresy renderują się (non-zero PNG)
#    SC #4: PNG-i linkowane z report.md jako relatywne ścieżki ![](decision_distribution.png)
#    SC #5: --compare-agent dodaje tabelę delta KPI (with vs without agent)
#    SC #6: --json output zachowuje kompatybilność v1.0 (stdout = czysty JSON, banner na stderr)
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
trap 'rm -f /tmp/p6_*' EXIT

PASS=0
FAIL=0

# Helper: uruchom komendę, drukuj [PASS] albo [FAIL] z hintem + ostatnimi 20 liniami log'u.
check() {
    local desc="$1"
    local cmd="$2"
    if eval "$cmd" > /tmp/p6_check.log 2>&1; then
        echo "[PASS] $desc"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $desc"
        echo "       cmd: $cmd"
        echo "       log:"
        sed 's/^/         /' /tmp/p6_check.log | head -20
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Phase 6: Report + plots generator — verification ==="
echo "Interpreter: $PY ($($PY --version 2>&1))"
echo ""

echo ""
echo "── 0. Pre-flight: cleanup ./reports/ ──"
rm -rf ./reports/
echo "      reports/ cleaned"

echo ""
echo "── 1. Regression backwards compat (CLI-04 z Phase 1, env passthrough Plan 05) ──"
check "Regression: 8/8 baseline_v1 fixtures (SKIP_KEYS extended for Phase 6)" \
    "$PY scripts/regression_check.py"
check "Regression: ./reports/ NIE zaśmiecone po regression run (env passthrough OK)" \
    "rm -rf ./reports; $PY scripts/regression_check.py > /dev/null 2>&1 && { [ ! -d ./reports ] || [ -z \"\$(ls -A ./reports 2>/dev/null)\" ]; }"

echo ""
echo "── 2. Full test suite (Phase 1-5 invariants + Phase 6 nowe) ──"
echo "      (tests may rmtree ./reports/* via tearDown — artifact generation moved AFTER tests)"
check "Unittest discover tests/ — wszystko zielone (Phase 1-6)" \
    "SPHSIM_NO_REPORT=1 $PY -m unittest discover tests"
check "Phase 6 tests/test_report.py — testy GREEN" \
    "SPHSIM_NO_REPORT=1 $PY -m unittest tests.test_report"
check "Phase 6 tests/test_plots.py — testy GREEN (Pillow opcjonalny)" \
    "SPHSIM_NO_REPORT=1 $PY -m unittest tests.test_plots"
check "Phase 6 tests/test_simulator_abstain.py — testy GREEN" \
    "SPHSIM_NO_REPORT=1 $PY -m unittest tests.test_simulator_abstain"

echo ""
echo "── 2a. Pre-flight artifact bundle (po testach, bo TestJsonStdoutClean tearDown czyści reports/) ──"
rm -rf ./reports/
SPHSIM_NO_REPORT='' $PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json > /tmp/p6_single.json 2> /tmp/p6_single.err || {
    echo "[FAIL] preflight: sph_sim.py single-run nie udało się"
    echo "       stderr:"; sed 's/^/         /' /tmp/p6_single.err
    FAIL=$((FAIL + 1))
}
LATEST=$(ls -dt ./reports/*/ 2>/dev/null | head -1)
if [ -z "$LATEST" ]; then
    echo "[FAIL] preflight: brak ./reports/<ts>/ po sph_sim.py — Plan 04 wire-in może nie działać"
    FAIL=$((FAIL + 1))
else
    echo "[PASS] preflight: LATEST=$LATEST"
    PASS=$((PASS + 1))
fi

echo ""
echo "── 3. SC #1: REPORT-01 — 3 pliki w reports/<ts>/ ──"
check "SC #1: report.md istnieje + non-empty" \
    "test -n \"$LATEST\" && test -s \"${LATEST}report.md\""
check "SC #1: decision_distribution.png istnieje + non-empty" \
    "test -n \"$LATEST\" && test -s \"${LATEST}decision_distribution.png\""
check "SC #1: kpi_timeseries.png istnieje + non-empty" \
    "test -n \"$LATEST\" && test -s \"${LATEST}kpi_timeseries.png\""
check "SC #1: katalog ma EXACTLY 3 pliki (no extras)" \
    "test -n \"$LATEST\" && [ \"\$(ls \"$LATEST\" | wc -l | tr -d ' ')\" = '3' ]"

echo ""
echo "── 4. SC #2: REPORT-02 — 6 sekcji MD + 5 KPI rows + baseline row ──"
check "SC #2 (sekcje): grep '^## ' znajduje >=6 nagłówków H2" \
    "test -n \"$LATEST\" && [ \"\$(grep -c '^## ' \"${LATEST}report.md\")\" -ge 6 ]"
check "SC #2 (KPI): wszystkie 5 KPI keys w MD (>=5 dopasowań)" \
    "test -n \"$LATEST\" && [ \"\$(grep -cE '\\| (avg_val_last100|cum_val_total|avg_net_profit|delivery_ratio|avg_providers_l100)' \"${LATEST}report.md\")\" -ge 5 ]"
check "SC #2 (baseline disclaimer): fixture path obecny" \
    "test -n \"$LATEST\" && grep -F '08-naive-zeta-0.75-baseline.json' \"${LATEST}report.md\" > /dev/null"
check "SC #2 (strategia): args.strategy w sekcji 2" \
    "test -n \"$LATEST\" && grep -F 'Strategia | \`naive\`' \"${LATEST}report.md\" > /dev/null"
check "SC #2 (konfiguracja): nagłówek '## Konfiguracja środowiska'" \
    "test -n \"$LATEST\" && grep -F '## Konfiguracja środowiska' \"${LATEST}report.md\" > /dev/null"

echo ""
echo "── 5. SC #3: PLOT-01/PLOT-02 — PNG signature walidne ──"
check "SC #3 (PLOT-01): decision_distribution.png ma PNG signature (\\x89PNG)" \
    "test -n \"$LATEST\" && $PY -c \"import sys; data=open('${LATEST}decision_distribution.png','rb').read(8); sys.exit(0 if data == b'\\x89PNG\\r\\n\\x1a\\n' else 1)\""
check "SC #3 (PLOT-02): kpi_timeseries.png ma PNG signature" \
    "test -n \"$LATEST\" && $PY -c \"import sys; data=open('${LATEST}kpi_timeseries.png','rb').read(8); sys.exit(0 if data == b'\\x89PNG\\r\\n\\x1a\\n' else 1)\""
check "SC #3 (PLOT-01): decision_distribution.png > 5 KB (matplotlib render real)" \
    "test -n \"$LATEST\" && [ \"\$(wc -c < \"${LATEST}decision_distribution.png\" | tr -d ' ')\" -ge 5000 ]"
check "SC #3 (PLOT-02): kpi_timeseries.png > 10 KB (T=1000 line points)" \
    "test -n \"$LATEST\" && [ \"\$(wc -c < \"${LATEST}kpi_timeseries.png\" | tr -d ' ')\" -ge 10000 ]"

echo ""
echo "── 6. SC #4: PLOT-03 — relatywne MD image links ──"
check "SC #4 (link 1): ![Rozkład decyzji per faza](decision_distribution.png) obecny" \
    "test -n \"$LATEST\" && grep -F '![Rozkład decyzji per faza](decision_distribution.png)' \"${LATEST}report.md\" > /dev/null"
check "SC #4 (link 2): ![Przebieg KPI w czasie](kpi_timeseries.png) obecny" \
    "test -n \"$LATEST\" && grep -F '![Przebieg KPI w czasie](kpi_timeseries.png)' \"${LATEST}report.md\" > /dev/null"
check "SC #4 (negative): brak absolutnych ścieżek w MD links" \
    "test -n \"$LATEST\" && ! grep -E '\\]\\(/' \"${LATEST}report.md\" > /dev/null"
check "SC #4 (negative): brak http:// w MD links" \
    "test -n \"$LATEST\" && ! grep -E '\\]\\(http' \"${LATEST}report.md\" > /dev/null"

echo ""
echo "── 7. SC #5: REPORT-03 — --compare-agent dodaje delta KPI section ──"
rm -rf ./reports/
SPHSIM_NO_REPORT='' $PY sph_sim.py --strategy naive --zeta 0.5 --compare-agent --seed 42 --json > /tmp/p6_compare.json 2> /tmp/p6_compare.err || true
LATEST_C=$(ls -dt ./reports/*/ 2>/dev/null | head -1)
check "SC #5 (preflight): compare-mode utworzyl reports/<ts>/" \
    "test -n \"$LATEST_C\" && test -s \"${LATEST_C}report.md\""
check "SC #5 (sekcja 7): '## Porównanie z RationalAgent' obecna" \
    "test -n \"$LATEST_C\" && grep -F '## Porównanie z RationalAgent' \"${LATEST_C}report.md\" > /dev/null"
check "SC #5 (delta table header): '| with-agent | bez agenta |' obecny" \
    "test -n \"$LATEST_C\" && grep -F '| with-agent | bez agenta |' \"${LATEST_C}report.md\" > /dev/null"
check "SC #5 (werdykt): linia '**Werdykt:**' obecna" \
    "test -n \"$LATEST_C\" && grep -F '**Werdykt:**' \"${LATEST_C}report.md\" > /dev/null"
check "SC #5 (PNG present): kpi_timeseries.png z compare > 10 KB (with_agent history threading)" \
    "test -n \"$LATEST_C\" && [ \"\$(wc -c < \"${LATEST_C}kpi_timeseries.png\" | tr -d ' ')\" -ge 10000 ]"

echo ""
echo "── 8. SC #6: JSON stdout cleanliness (Pitfall 3 — banner na stderr) ──"
check "SC #6 (--json stdout): pure JSON parseable mimo banner-on-stderr" \
    "rm -rf ./reports/; SPHSIM_NO_REPORT='' $PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json 2>/dev/null | $PY -c 'import json,sys; json.loads(sys.stdin.read())'"
check "SC #6 (banner): 'Raport zapisany do:' obecny w stderr (NIE stdout)" \
    "rm -rf ./reports/; SPHSIM_NO_REPORT='' $PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json 2>&1 1>/dev/null | grep -F 'Raport zapisany do:' > /dev/null"
check "SC #6 (env keys): JSON output zawiera abstain_per_phase w metrics (Plan 01)" \
    "SPHSIM_NO_REPORT=1 $PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json | $PY -c \"import json,sys; d=json.load(sys.stdin)['metrics']; assert 'abstain_per_phase' in d, sorted(d.keys()); print('abstain_per_phase keys:', sorted(d['abstain_per_phase'].keys()))\""
check "SC #6 (no leak): _with_agent_full NIE w compare JSON output" \
    "rm -rf ./reports/; SPHSIM_NO_REPORT=1 $PY sph_sim.py --strategy naive --zeta 0.5 --compare-agent --seed 42 --json | $PY -c \"import json,sys; d=json.load(sys.stdin); assert '_with_agent_full' not in d, sorted(d.keys()); print('private key correctly stripped')\""

echo ""
echo "── 9. REPL Pitfall 2 (Phase 5) + Pitfall 6 (Phase 6 fake_args) defused ──"
check "REPL Pitfall 2: 'run naive zeta=0.5' nie crashe; output zawiera 'Konfiguracja środowiska'" \
    "printf 'run naive zeta=0.5\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | grep 'Konfiguracja środowiska' > /dev/null"
check "REPL Pitfall 2: 'compare naive zeta=0.5' nie crashe; output zawiera 'PORÓWNANIE'" \
    "printf 'compare naive zeta=0.5\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | grep 'PORÓWNANIE' > /dev/null"
check "REPL Pitfall 6: 'run naive zeta=0.5' z opt-out NIE crashe na AttributeError" \
    "printf 'run naive zeta=0.5\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | { ! grep 'AttributeError' > /dev/null; }"
check "REPL Pitfall 6: 'compare naive zeta=0.5' z opt-out NIE crashe na AttributeError" \
    "printf 'compare naive zeta=0.5\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | { ! grep 'AttributeError' > /dev/null; }"

echo ""
echo "── 10. Opt-out: SPHSIM_NO_REPORT=1 → brak side effects ──"
check "Opt-out (CLI single): NIE tworzy reports/<ts>/ pod SPHSIM_NO_REPORT=1" \
    "rm -rf ./reports; SPHSIM_NO_REPORT=1 $PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json > /dev/null 2>&1 && { [ ! -d ./reports ] || [ -z \"\$(ls -A ./reports 2>/dev/null)\" ]; }"
check "Opt-out (CLI compare): NIE tworzy reports/<ts>/ pod SPHSIM_NO_REPORT=1 + --compare-agent" \
    "rm -rf ./reports; SPHSIM_NO_REPORT=1 $PY sph_sim.py --strategy naive --zeta 0.5 --compare-agent --seed 42 --json > /dev/null 2>&1 && { [ ! -d ./reports ] || [ -z \"\$(ls -A ./reports 2>/dev/null)\" ]; }"
check "Opt-out (regression): scripts/regression_check.py nie zaśmieca reports/" \
    "rm -rf ./reports; $PY scripts/regression_check.py > /dev/null 2>&1 && { [ ! -d ./reports ] || [ -z \"\$(ls -A ./reports 2>/dev/null)\" ]; }"

# Final cleanup — usuń wszystkie reports/<ts>/ generowane przez verify script.
rm -rf ./reports


# ── Summary ──
echo ""
echo "════════════════════════════════════════"
echo "  Phase 6 verification: PASS=$PASS / FAIL=$FAIL"
echo "════════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
    echo "✗ Phase 6 NIE jest gotowe — popraw FAIL'e powyżej."
    exit 1
fi
echo "✓ Phase 6 ready for /gsd:verify-work"
exit 0
