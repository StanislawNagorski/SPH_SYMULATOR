#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  verify_phase8.sh — phase exit gate dla Phase 8 (Documentation + Interactive Tutorial)
#  Plan 08-07 — Wave 5 closeout
#
#  Phase 8 covers TUT-01..TUT-06 + DOC-01 + DOC-02 + EX-01 + GATE-01.
#  Phase 8 exit gate runs all SC checks below; partial pass blocks merge.
#
#  Plan 07 will add: docs/PRZEWODNIK.md sections, docs/assets/*.png PNG magic,
#  --tutorial flag, tutorial smoke test, do_help contains tutorial,
#  full unittest discover.
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

# === Phase 8 checks land here in Plan 07 (verify_phase8 final assembly) ===

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
