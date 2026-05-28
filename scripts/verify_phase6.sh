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

echo "── 0. Pre-flight: cleanup ./reports/ (Plan 05 owns body) ──"
echo ""
echo "── 1. Regression backwards compat (Plan 05 owns body) ──"
echo ""
echo "── 2. Full test suite (Plan 05 owns body) ──"
echo ""
echo "── 3. SC #1 REPORT-01: 3 pliki w reports/<ts>/ (Plan 05 owns body) ──"
echo ""
echo "── 4. SC #2 REPORT-02: sekcje MD + KPI table + baseline row (Plan 05 owns body) ──"
echo ""
echo "── 5. SC #3 PLOT-01/02: PNG generation (Plan 05 owns body) ──"
echo ""
echo "── 6. SC #4 PLOT-03: relatywne linki w MD (Plan 05 owns body) ──"
echo ""
echo "── 7. SC #5 REPORT-03: --compare-agent delta KPI section (Plan 05 owns body) ──"
echo ""
echo "── 8. SC #6 JSON stdout cleanliness (Plan 05 owns body) ──"
echo ""
echo "── 9. SPHSIM_NO_REPORT=1 opt-out (Plan 05 owns body) ──"
echo ""
echo "(Wave 0 skeleton — section banners only; Plan 05 fills check() bodies)"
echo ""

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
