#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  verify_phase4.sh — phase exit gate dla Phase 4 (rational agent veto layer)
#  Plan 04-07 — Final audit script
#
#  Weryfikuje wszystkie 5 ROADMAP Phase 4 Success Criteria + regression
#  + Phase 2/3 invariants + test suite + mutex enforcement + REPL + custom:
#
#    SC #1: Każda strategia default-wrapped w RationalAgent (agent_enabled==true)
#    SC #2: --no-agent escape hatch (agent_enabled==false, n_vetoed_total==0)
#    SC #3: veto_per_phase w JSON i human-readable (VETO przez RationalAgent sekcja)
#    SC #4: --compare-agent tabela delta KPI (with/without/delta/agent_helps)
#    SC #5: Empiryczny dowód agent_helps==true dla naive --zeta 0.95 (high COMMIT rate
#            → wiele veto candidates → with-agent ma wyższy avg_net_profit)
#
#  UWAGA SC #5: NIE używamy `incentive --expected_P 30` jako demo — per D-56
#  incentive jest idempotent (n_vetoed≈0, delta≈0). Używamy `naive --zeta 0.95`
#  (wysoki COMMIT rate gwarantuje wiele veto candidates gdy E[zysk]<0).
#
#  Plus regression backwards compat (CLI-04 z Phase 1) + Phase 2/3 invariants
#  + tests/test_agent.py (10 przypadków) + pełny unittest discover (123+ testów)
#  + mutex enforcement (D-60) + REPL 7 komend (compare) + custom strategy + agent.
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
trap 'rm -f /tmp/p4_*' EXIT

PASS=0
FAIL=0

# Helper: uruchom komendę, drukuj [PASS] albo [FAIL] z hintem + ostatnimi 20 liniami log'u.
check() {
    local desc="$1"
    local cmd="$2"
    if eval "$cmd" > /tmp/p4_check.log 2>&1; then
        echo "[PASS] $desc"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $desc"
        echo "       cmd: $cmd"
        echo "       log:"
        sed 's/^/         /' /tmp/p4_check.log | head -20
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Phase 4: Rational Agent veto layer — verification ==="
echo "Interpreter: $PY ($($PY --version 2>&1))"
echo ""

# ── 1. Regression backwards compat (Phase 1 CLI-04 contract) ──
echo "── 1. Regression backwards compat (Phase 1 CLI-04 contract) ──"
# regression_check.py dodaje --no-agent do każdej inwokacji (D-59/D-67 Strategia B)
# + SKIP_KEYS filtruje 3 nowe klucze (veto_per_phase, n_vetoed_total, agent_enabled)
check "Regression: 8/8 baseline_v1 fixtures (PASS: 8/8)" \
    "$PY scripts/regression_check.py"

# ── 2. Test suite — Phase 2/3 invariants + Phase 4 nowe ──
echo ""
echo "── 2. Test suite — Phase 2/3 invariants + Phase 4 nowe ──"
check "Phase 2 invariant: STRATEGY_META ↔ argparse" \
    "$PY -m unittest tests.test_strategy_meta_consistency"
check "Phase 3 loader: 21 unit cases (test_loader)" \
    "$PY -m unittest tests.test_loader"
check "Phase 4 agent: 10 unit+integration cases (test_agent)" \
    "$PY -m unittest tests.test_agent"
check "Full test discover (wszystkie 123+ testy)" \
    "$PY -m unittest discover tests"

# ── 3. SC #1: agent default-wrapped (bez --no-agent) ──
echo ""
echo "── 3. SC #1: agent default-wrapped (bez --no-agent) ──"
# JSON struktura: d['metrics']['agent_enabled']
check "SC #1 (naive): agent_enabled==true w domyślnym uruchomieniu" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --seed 42 --json 2>/dev/null | \
     $PY -c \"import json,sys; d=json.load(sys.stdin); assert d['metrics']['agent_enabled'] is True, f'agent_enabled={d[\\\"metrics\\\"][\\\"agent_enabled\\\"]}'\" "
check "SC #1 (incentive): agent_enabled==true dla strategii incentive" \
    "$PY sph_sim.py --strategy incentive --expected_P 30 --seed 42 --json 2>/dev/null | \
     $PY -c \"import json,sys; d=json.load(sys.stdin); assert d['metrics']['agent_enabled'] is True, f'agent_enabled={d[\\\"metrics\\\"][\\\"agent_enabled\\\"]}'\" "

# ── 4. SC #2: --no-agent escape hatch ──
echo ""
echo "── 4. SC #2: --no-agent escape hatch ──"
check "SC #2 (naive --no-agent): agent_enabled==false" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json 2>/dev/null | \
     $PY -c \"import json,sys; d=json.load(sys.stdin); m=d['metrics']; assert m['agent_enabled'] is False and m['n_vetoed_total']==0, f'enabled={m[\\\"agent_enabled\\\"]}, vetoed={m[\\\"n_vetoed_total\\\"]}'\" "
check "SC #2 (incentive --no-agent): agent_enabled==false" \
    "$PY sph_sim.py --strategy incentive --expected_P 100 --no-agent --seed 42 --json 2>/dev/null | \
     $PY -c \"import json,sys; d=json.load(sys.stdin); assert d['metrics']['agent_enabled'] is False, 'agent powinien byc wylaczony'\" "

# ── 5. SC #3: veto_per_phase w JSON i human-readable ──
echo ""
echo "── 5. SC #3: veto_per_phase w JSON i human-readable ──"
# phase_prob z probs=1.0,1.0,1.0,1.0,0.0 → wiele COMMIT przy E[zysk]<0 → dużo veto
check "SC #3 (JSON): veto_per_phase jest dict, n_vetoed_total >= 0" \
    "$PY sph_sim.py --strategy phase_prob --probs 1.0,1.0,1.0,1.0,0.0 --seed 42 --json 2>/dev/null | \
     $PY -c \"import json,sys; d=json.load(sys.stdin); m=d['metrics']; assert isinstance(m['veto_per_phase'], dict) and isinstance(m['n_vetoed_total'], int), f'veto_per_phase={type(m[\\\"veto_per_phase\\\"])}, n_vetoed_total={type(m[\\\"n_vetoed_total\\\"])}'\" "
check "SC #3 (JSON): pole agent_enabled istnieje" \
    "$PY sph_sim.py --strategy phase_prob --probs 1.0,1.0,1.0,1.0,0.0 --seed 42 --json 2>/dev/null | \
     $PY -c \"import json,sys; d=json.load(sys.stdin); assert 'agent_enabled' in d['metrics'], 'brak pola agent_enabled'\" "
# Sekcja VETO widoczna w human-readable gdy n_vetoed > 0
# Uwaga: pipefail + 'grep -q' powoduje SIGPIPE. Używamy `grep ... > /dev/null`.
check "SC #3 (human): sekcja 'VETO przez RationalAgent' widoczna" \
    "$PY sph_sim.py --strategy phase_prob --probs 1.0,1.0,1.0,1.0,0.0 --seed 42 2>/dev/null | \
     grep 'VETO przez RationalAgent' > /dev/null"

# ── 6. SC #4: --compare-agent delta KPI table ──
echo ""
echo "── 6. SC #4: --compare-agent delta KPI table ──"
check "SC #4 (JSON): comparison block z with_agent/without_agent/delta/agent_helps" \
    "$PY sph_sim.py --strategy incentive --expected_P 30 --compare-agent --seed 42 --json 2>/dev/null | \
     $PY -c \"import json,sys; d=json.load(sys.stdin); c=d['comparison']; assert 'with_agent' in c and 'without_agent' in c and 'delta' in c and 'agent_helps' in c, f'brakujace klucze: {list(c.keys())}'\" "
check "SC #4 (human): werdykt ✓ TAK lub ✗ NIE widoczny" \
    "$PY sph_sim.py --strategy incentive --expected_P 30 --compare-agent --seed 42 2>/dev/null | \
     grep -E '✓ TAK|✗ NIE' > /dev/null"
check "SC #4 (REPL compare): werdykt w trybie interaktywnym" \
    "printf 'compare incentive expected_P=30\nexit\n' | $PY sph_sim.py --interactive 2>&1 | \
     grep -E '✓ TAK|✗ NIE' > /dev/null"

# ── 7. SC #5: empiryczny demo scenario — agent_helps == true ──
echo ""
echo "── 7. SC #5: empiryczny dowód agent_helps==true (naive --zeta 0.95) ──"
# UWAGA: NIE używamy `incentive --expected_P 30` — per D-56 incentive jest idempotent
# (n_vetoed≈0, delta≈0). Używamy `naive --zeta 0.95` — wysoki COMMIT rate gwarantuje
# wiele veto candidates gdy E[zysk]<0, więc with-agent ma wyższy avg_net_profit.
check "SC #5: agent_helps==True dla naive --zeta 0.95 (high-COMMIT-rate strategy)" \
    "$PY sph_sim.py --strategy naive --zeta 0.95 --compare-agent --seed 42 --json 2>/dev/null | \
     $PY -c \"import json,sys; raw=sys.stdin.read(); d=json.loads(raw[raw.find('{'):]); \
ah=d['comparison']['agent_helps']; delta=d['comparison']['delta']['avg_net_profit']; \
assert ah is True, f'SC#5 FAILED: agent_helps={ah}, delta avg_net_profit={delta:.4f} (oczekiwano >0)'\" "

# ── 8. Argparse mutex enforcement (D-60) ──
echo ""
echo "── 8. Argparse mutex enforcement (D-60) ──"
# Owijamy w `{ ... || true; }` bo argparse wychodzi z kodem 2 (FAIL bez ||true → pipefail)
check "Mutex: --compare-agent + --no-agent → polski błąd 'wykluczające'" \
    "{ $PY sph_sim.py --strategy naive --zeta 0.5 --compare-agent --no-agent 2>&1 || true; } | \
     grep 'wykluczające' > /dev/null"
check "Mutex: --interactive + --compare-agent → błąd 'nie działa'" \
    "{ $PY sph_sim.py --interactive --compare-agent 2>&1 || true; } | \
     grep -E 'interactive|wykluczające|nie działa' > /dev/null"

# ── 9. REPL 7 komend — Phase 4 dodaje compare ──
echo ""
echo "── 9. REPL 7 komend (Phase 4 dodaje compare) ──"
check "REPL help zawiera 'compare <nazwa>'" \
    "printf 'help\nexit\n' | $PY sph_sim.py --interactive 2>&1 | \
     grep 'compare <nazwa>' > /dev/null"

# ── 10. Custom strategy + agent integration (D-58, Phase 3 carry-forward) ──
echo ""
echo "── 10. Custom strategy + agent integration (D-58 carry-forward) ──"
# Custom strategia też domyślnie wrapped (D-58: agent default-on dla custom too)
check "D-58: custom strategy ma agent_enabled==true" \
    "$PY sph_sim.py --custom examples/custom_strategy_template.py --seed 42 --json 2>/dev/null | \
     tail -n +2 | \
     $PY -c \"import json,sys; d=json.load(sys.stdin); assert d['metrics']['agent_enabled'] is True, f'agent_enabled={d[\\\"metrics\\\"][\\\"agent_enabled\\\"]}'\" "
check "D-58: custom strategy z --compare-agent ma comparison block" \
    "$PY sph_sim.py --custom examples/custom_strategy_template.py --compare-agent --seed 42 --json 2>/dev/null | \
     tail -n +2 | \
     $PY -c \"import json,sys; d=json.load(sys.stdin); assert 'comparison' in d, f'brak klucza comparison: {list(d.keys())}'\" "

# ── Summary ──
echo ""
echo "════════════════════════════════════════"
echo "  Phase 4 verification: PASS=$PASS / FAIL=$FAIL"
echo "════════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
    echo "✗ Phase 4 NIE jest gotowe — popraw FAIL'e powyżej."
    exit 1
fi
echo "✓ Phase 4 ready for /gsd:verify-work"
exit 0
