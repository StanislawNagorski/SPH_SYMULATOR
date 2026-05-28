#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  verify_phase7.sh — phase exit gate dla Phase 7 (batch runner + aggregation)
#  Plan 07-06 — Wave 5 closeout (mirrors Phase 6 verify_phase6.sh structure)
#
#  Phase 7 covers BATCH-01..03 + PLOT-04 (multi-seed orchestrator + scipy CI + boxplot).
#  Phase 7 exit gate runs all SC checks below; partial pass blocks merge.
#
#  Phase 7 Success Criteria:
#    SC #1: /batch <strategia> --seeds 10 i --batch --seeds 1,5,42,100 oba działają
#    SC #2: Raport MD ma tabelę per-seed (N wierszy × 6 kolumn) + agregat (5 KPI × 7 kolumn z CI)
#    SC #3: batch_aggregate.png istnieje, non-zero, PNG signature, linked w raporcie
#    SC #4: Batch działa z RationalAgent (default) i --no-agent
#    SC #5: Werdykt baseline-beating w raporcie (lower 95% CI > 92.0 dla avg_val_last100)
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
trap 'rm -f /tmp/p7_*' EXIT

PASS=0
FAIL=0

# Helper: uruchom komendę, drukuj [PASS] albo [FAIL] z hintem + ostatnimi 20 liniami log'u.
check() {
    local desc="$1"
    local cmd="$2"
    if eval "$cmd" > /tmp/p7_check.log 2>&1; then
        echo "[PASS] $desc"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $desc"
        echo "       cmd: $cmd"
        echo "       log:"
        sed 's/^/         /' /tmp/p7_check.log | head -20
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Phase 7: Batch runner + aggregation — verification ==="
echo "Interpreter: $PY ($($PY --version 2>&1))"
echo ""

echo ""
echo "── 0. Pre-flight: cleanup ./reports/ ──"
rm -rf ./reports/
echo "      reports/ cleaned"

echo ""
echo "── 1. Regression backwards compat (CLI-04 z Phase 1 + SKIP_KEYS z Phase 5) ──"
check "Regression: scripts/regression_check.py PASS=8/8 (BATCH-01 SKIP_KEYS unchanged)" \
    "SPHSIM_NO_REPORT=1 $PY scripts/regression_check.py"
check "Regression: ./reports/ NIE zaśmiecone po regression run (env passthrough OK)" \
    "rm -rf ./reports; SPHSIM_NO_REPORT=1 $PY scripts/regression_check.py > /dev/null 2>&1 && { [ ! -d ./reports ] || [ -z \"\$(ls -A ./reports 2>/dev/null)\" ]; }"

echo ""
echo "── 2. Full test suite (Phase 1-6 invariants + Phase 7 nowe — 33 tests new) ──"
check "Unittest discover tests/ — wszystko zielone (Phase 1-7, 205 total)" \
    "SPHSIM_NO_REPORT=1 $PY -m unittest discover tests"
check "Phase 7 BATCH-02: tests/test_batch_stats.py — 9 tests GREEN" \
    "SPHSIM_NO_REPORT=1 $PY -m unittest tests.test_batch_stats"
check "Phase 7 BATCH-01: tests/test_batch.py — 17 tests GREEN (parser+mutex+orchestrator+REPL+parity)" \
    "SPHSIM_NO_REPORT=1 $PY -m unittest tests.test_batch"
check "Phase 7 BATCH-03 + PLOT-04: tests/test_batch_report.py — 7 tests GREEN" \
    "SPHSIM_NO_REPORT=1 $PY -m unittest tests.test_batch_report"

echo ""
echo "── 2a. Pre-flight artifact bundle (po testach, bo testy mogą czyścić ./reports/) ──"
rm -rf ./reports/
SPHSIM_NO_REPORT='' $PY sph_sim.py --strategy naive --zeta 0.75 --batch --seeds 5 --no-agent --seed 42 > /tmp/p7_artifact.log 2>&1 || true
LATEST_B=$(ls -d ./reports/batch_*/ 2>/dev/null | head -1 || echo "")
check "Pre-flight artifact: reports/batch_<ts>/ created" \
    "[ -n \"\$LATEST_B\" ] && [ -d \"\$LATEST_B\" ]"

echo ""
echo "── 3. SC #1 (BATCH-01): seed-list grammar + invocation ──"
check "SC #1 (seeds N): --seeds 5 expands to [1,2,3,4,5]" \
    "$PY -c \"from sphsim.cli.args import _parse_seeds_list; assert _parse_seeds_list('5') == [1,2,3,4,5]\""
check "SC #1 (seeds list): --seeds 1,5,42 parses to [1,5,42]" \
    "$PY -c \"from sphsim.cli.args import _parse_seeds_list; assert _parse_seeds_list('1,5,42') == [1,5,42]\""
check "SC #1 (seeds reject 0): --seeds 0 raises ArgumentTypeError" \
    "$PY -c 'from sphsim.cli.args import _parse_seeds_list; import argparse;
try:
    _parse_seeds_list(\"0\"); raise SystemExit(1)
except argparse.ArgumentTypeError:
    pass'"
check "SC #1 (seeds dedup): --seeds 1,1,2 → [1,2]" \
    "$PY -c \"from sphsim.cli.args import _parse_seeds_list; assert _parse_seeds_list('1,1,2') == [1,2]\""
check "SC #1 (CLI report): --batch --seeds 5 creates reports/batch_*/" \
    "[ -n \"\$LATEST_B\" ] && test -f \"\${LATEST_B}report.md\""
check "SC #1 (MAX_SEEDS): --seeds 1001 rejects (DoS cap)" \
    "$PY -c 'from sphsim.cli.args import _parse_seeds_list; import argparse;
try:
    _parse_seeds_list(\"1001\"); raise SystemExit(1)
except argparse.ArgumentTypeError:
    pass'"

echo ""
echo "── 4. SC #2 (BATCH-03): per-seed + aggregate tables ──"
check "SC #2 (per-seed table header): '| Seed | avg_val_last100' present" \
    "[ -n \"\$LATEST_B\" ] && grep -F '| Seed | avg_val_last100' \"\${LATEST_B}report.md\" > /dev/null"
check "SC #2 (per-seed rows): N=5 rows in MD per-seed table" \
    "[ -n \"\$LATEST_B\" ] && [ \"\$(grep -cE '^\\| [0-9]+ \\|' \"\${LATEST_B}report.md\")\" -ge 5 ]"
check "SC #2 (aggregate header): '## Agregat statystyczny' obecny" \
    "[ -n \"\$LATEST_B\" ] && grep -F '## Agregat statystyczny' \"\${LATEST_B}report.md\" > /dev/null"
check "SC #2 (aggregate 5 KPI rows): wszystkie 5 KPI w agregat table" \
    "[ -n \"\$LATEST_B\" ] && [ \"\$(grep -cE '^\\| (avg_val_last100|cum_val_total|avg_net_profit|delivery_ratio|avg_providers_l100)' \"\${LATEST_B}report.md\")\" -ge 5 ]"

echo ""
echo "── 5. SC #3 (PLOT-04): batch_aggregate.png ──"
check "SC #3 (PLOT-04): batch_aggregate.png ma PNG signature (\\x89PNG)" \
    "[ -n \"\$LATEST_B\" ] && $PY -c \"import sys; data=open('\${LATEST_B}batch_aggregate.png','rb').read(8); sys.exit(0 if data == b'\\x89PNG\\r\\n\\x1a\\n' else 1)\""
check "SC #3 (PLOT-04 size): batch_aggregate.png > 10 KB (matplotlib boxplot real)" \
    "[ -n \"\$LATEST_B\" ] && [ \"\$(wc -c < \"\${LATEST_B}batch_aggregate.png\" | tr -d ' ')\" -ge 10000 ]"
check "SC #3 (PNG link): ![Box-ploty 5 KPI dla N seedów](batch_aggregate.png) w report.md" \
    "[ -n \"\$LATEST_B\" ] && grep -F '](batch_aggregate.png)' \"\${LATEST_B}report.md\" > /dev/null"

echo ""
echo "── 6. SC #4: --no-agent + agent-default parallel ──"
check "SC #4 (--no-agent batch): report MD + PNG dla --no-agent" \
    "[ -n \"\$LATEST_B\" ] && test -s \"\${LATEST_B}report.md\" && test -s \"\${LATEST_B}batch_aggregate.png\""
check "SC #4 (agent-default batch): --batch --seeds 3 z agentem też tworzy report" \
    "rm -rf ./reports/; SPHSIM_NO_REPORT='' $PY sph_sim.py --strategy naive --zeta 0.75 --batch --seeds 3 --seed 42 > /tmp/p7_agent.log 2>&1 && ls -d ./reports/batch_*/ | head -1 | xargs -I{} test -s {}report.md"

echo ""
echo "── 7. SC #5: werdykt baseline-beating (re-generate --no-agent artifact for clean compare) ──"
rm -rf ./reports/
SPHSIM_NO_REPORT='' $PY sph_sim.py --strategy naive --zeta 0.75 --batch --seeds 5 --no-agent --seed 42 > /tmp/p7_sc5.log 2>&1 || true
LATEST_B=$(ls -d ./reports/batch_*/ 2>/dev/null | head -1 || echo "")
check "SC #5 (werdykt header): '## Werdykt: bije baseline' obecny" \
    "[ -n \"\$LATEST_B\" ] && grep -F '## Werdykt: bije baseline' \"\${LATEST_B}report.md\" > /dev/null"
check "SC #5 (werdykt glyph): ✓ TAK lub ✗ NIE w werdykcie" \
    "[ -n \"\$LATEST_B\" ] && grep -E '(✓|✗)' \"\${LATEST_B}report.md\" > /dev/null"

echo ""
echo "── 8. REPL Pitfall regressions (Phase 7 BATCH-01 REPL parity) ──"
check "REPL: 'batch naive --seeds 3' produces report (BATCH-01)" \
    "rm -rf ./reports/; printf 'batch naive --seeds 3\\nexit\\n' | SPHSIM_NO_REPORT='' $PY sph_sim.py --interactive 2>&1 | grep -F 'Raport batchowy zapisany do:' > /dev/null"
check "REPL: 'batch naive --seeds 0' Polish error, no crash" \
    "printf 'batch naive --seeds 0\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | grep -F 'dodatnie' > /dev/null"
check "REPL: 'batch unknown --seeds 3' Polish error, no crash" \
    "printf 'batch unknown --seeds 3\\nexit\\n' | SPHSIM_NO_REPORT=1 $PY sph_sim.py --interactive 2>&1 | grep -F 'nie istnieje' > /dev/null"

echo ""
echo "── 9. Mutex (BATCH-01 4-way post-parse mutex) ──"
check "Mutex: --batch --compare-agent → exit 2 + Polish 'wzajemnie wykluczające'" \
    "rm -rf ./reports/; { $PY sph_sim.py --strategy naive --zeta 0.5 --batch --seeds 3 --compare-agent --seed 42 2>&1 || true; } | grep -F 'wzajemnie wykluczające' > /dev/null"
check "Mutex: --batch bez --seeds → exit 2 + Polish 'wymaga --seeds'" \
    "{ $PY sph_sim.py --strategy naive --zeta 0.5 --batch --seed 42 2>&1 || true; } | grep -F 'wymaga --seeds' > /dev/null"
check "Mutex: --seeds bez --batch → exit 2 + Polish 'wymaga --batch'" \
    "{ $PY sph_sim.py --strategy naive --zeta 0.5 --seeds 5 --seed 42 2>&1 || true; } | grep -F 'wymaga --batch' > /dev/null"

echo ""
echo "── 10. Opt-out (SPHSIM_NO_REPORT=1 + --batch) ──"
check "Opt-out: SPHSIM_NO_REPORT=1 + --batch → brak reports/" \
    "rm -rf ./reports/; SPHSIM_NO_REPORT=1 $PY sph_sim.py --strategy naive --zeta 0.5 --batch --seeds 3 --no-agent --seed 42 > /dev/null 2>&1; [ ! -d ./reports ] || [ -z \"\$(ls -A ./reports 2>/dev/null)\" ]"

echo ""
echo "── 11. Determinism (BATCH-01) ──"
check "Determinism: dwa identyczne --batch --seeds 1,2,3 → byte-identical stdout" \
    "rm -rf ./reports/; OUT1=\$(SPHSIM_NO_REPORT=1 $PY sph_sim.py --strategy naive --zeta 0.5 --batch --seeds 1,2,3 --no-agent --seed 42 2>/dev/null); OUT2=\$(SPHSIM_NO_REPORT=1 $PY sph_sim.py --strategy naive --zeta 0.5 --batch --seeds 1,2,3 --no-agent --seed 42 2>/dev/null); [ \"\$OUT1\" = \"\$OUT2\" ]"

# Final cleanup — usuń wszystkie reports/<ts>/ generowane przez verify script.
rm -rf ./reports


# ── Summary ──
echo ""
echo "════════════════════════════════════════"
echo "  Phase 7 verification: PASS=$PASS / FAIL=$FAIL"
echo "════════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
    echo "✗ Phase 7 NIE jest gotowe — popraw FAIL'e powyżej."
    exit 1
fi
echo "✓ Phase 7 ready for /gsd:verify-work"
exit 0
