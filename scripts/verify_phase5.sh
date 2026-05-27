#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  verify_phase5.sh — phase exit gate dla Phase 5 (configurable environment)
#  Plan 05-04 — Final audit script (skeleton from Plan 05-00)
#
#  Weryfikuje wszystkie 4 ROADMAP Phase 5 Success Criteria + regression:
#
#    SC #1: --phi/--rho override (length=5, range [0,1] dla φ, ≥0 dla ρ)
#    SC #2: --valuation window|step|linear preset + --K0/--K1 override
#    SC #3: 3 presety dają rozróżnialne KPI (ten sam seed+strategia)
#    SC #4: raport human/MD zawiera nU, T, κ, α, K0, K1, φ, ρ, seed w tabeli
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
trap 'rm -f /tmp/p5_*' EXIT

PASS=0
FAIL=0

# Helper: uruchom komendę, drukuj [PASS] albo [FAIL] z hintem + ostatnimi 20 liniami log'u.
check() {
    local desc="$1"
    local cmd="$2"
    if eval "$cmd" > /tmp/p5_check.log 2>&1; then
        echo "[PASS] $desc"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $desc"
        echo "       cmd: $cmd"
        echo "       log:"
        sed 's/^/         /' /tmp/p5_check.log | head -20
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Phase 5: Configurable environment — verification ==="
echo "Interpreter: $PY ($($PY --version 2>&1))"
echo ""
echo "── Phase 5 checks will be inserted by Plan 04 (Wave 4) ──"
echo "(Wave 0 skeleton — no checks implemented yet)"
echo ""

# ── Summary ──
echo ""
echo "════════════════════════════════════════"
echo "  Phase 5 verification: PASS=$PASS / FAIL=$FAIL"
echo "════════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
    echo "✗ Phase 5 NIE jest gotowe — popraw FAIL'e powyżej."
    exit 1
fi
echo "✓ Phase 5 ready for /gsd:verify-work"
exit 0
