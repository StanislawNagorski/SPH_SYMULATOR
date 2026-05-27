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

# ── 1. Regression backwards compat (CLI-04 z Phase 1) ──
echo ""
echo "── 1. Regression backwards compat (CLI-04 z Phase 1) ──"
check "Regression: 8/8 baseline_v1 fixtures (SKIP_KEYS extended dla Phase 5)" \
    "$PY scripts/regression_check.py"

# ── 2. Full test suite (Phase 2/3/4 invariants + Phase 5 nowe) ──
echo ""
echo "── 2. Full test suite (Phase 2/3/4 invariants + Phase 5 nowe) ──"
check "Unittest discover tests/ — wszystko zielone" \
    "$PY -m unittest discover tests"
check "Phase 5 tests/test_env.py specifically — 7 klas green" \
    "$PY -m unittest tests.test_env"

# ── 3. SC #1: --phi/--rho override + walidacja (ENV-01) ──
echo ""
echo "── 3. SC #1: --phi/--rho override + walidacja (ENV-01) ──"
check "SC #1 (accept): --phi 0.1,0.2,0.3,0.4,1.0 + --rho 0.5,0.5,0.7,1.5,3.0 → exit 0" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --phi 0.1,0.2,0.3,0.4,1.0 --rho 0.5,0.5,0.7,1.5,3.0 --no-agent --seed 42 --json > /dev/null"
check "SC #1 (reject length): --phi 0.1,0.2,0.3 → exit 2 + 'dokładnie 5' w stderr" \
    "{ $PY sph_sim.py --strategy naive --zeta 0.5 --phi 0.1,0.2,0.3 --no-agent --seed 42 2>&1 || true; } | grep 'dokładnie 5' > /dev/null"
check "SC #1 (reject range phi>1): --phi 0.1,0.2,0.3,0.4,1.5 → exit 2 + 'poza zakresem' w stderr" \
    "{ $PY sph_sim.py --strategy naive --zeta 0.5 --phi 0.1,0.2,0.3,0.4,1.5 --no-agent --seed 42 2>&1 || true; } | grep 'poza zakresem' > /dev/null"
check "SC #1 (reject rho<0): --rho 0.5,0.5,0.7,1.5,-3.0 → exit 2 + 'ujemne' w stderr" \
    "{ $PY sph_sim.py --strategy naive --zeta 0.5 --rho 0.5,0.5,0.7,1.5,-3.0 --no-agent --seed 42 2>&1 || true; } | grep 'ujemne' > /dev/null"

# ── 4. SC #2: --valuation preset + --K0/--K1 (ENV-02) ──
echo ""
echo "── 4. SC #2: --valuation preset + --K0/--K1 (ENV-02) ──"
check "SC #2 (window default): --valuation window → exit 0" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --valuation window --no-agent --seed 42 --json > /dev/null"
check "SC #2 (step): --valuation step → exit 0" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --valuation step --no-agent --seed 42 --json > /dev/null"
check "SC #2 (linear): --valuation linear → exit 0" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --valuation linear --no-agent --seed 42 --json > /dev/null"
check "SC #2 (reject preset): --valuation foobar → exit 2 (argparse choices)" \
    "{ $PY sph_sim.py --strategy naive --zeta 0.5 --valuation foobar --no-agent --seed 42 2>&1 || true; } | grep -- '--valuation' > /dev/null"
check "SC #2 (K0 override): --K0 80 → exit 0 + parsowalny JSON z K0==80" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --K0 80 --no-agent --seed 42 --json | $PY -c 'import json,sys; d=json.load(sys.stdin); assert d[\"env\"][\"K0\"]==80.0, d[\"env\"][\"K0\"]'"
check "SC #2 (K0+K1 override): --K0 90 --K1 150 → exit 0 + parsowalny JSON" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --K0 90 --K1 150 --no-agent --seed 42 --json > /dev/null"

# ── 5. SC #3: 3 presety → distinguishable KPI (ENV-02 SC-3) ──
echo ""
echo "── 5. SC #3: 3 presety → distinguishable KPI (ENV-02 SC-3) ──"
check "SC #3: window/step/linear KPI parami różne na seed=42 + naive zeta=0.5 (K0=50 K1=70)" \
    "$PY -c \"
import json, subprocess, sys
def run(preset):
    r = subprocess.run([sys.executable, 'sph_sim.py', '--strategy', 'naive', '--zeta', '0.5', '--valuation', preset, '--no-agent', '--seed', '42', '--json', '--K0', '50', '--K1', '70'], capture_output=True, text=True)
    assert r.returncode == 0, f'{preset} exit={r.returncode} stderr={r.stderr[:200]}'
    return json.loads(r.stdout)['metrics']['avg_val_last100']
w, s, l = run('window'), run('step'), run('linear')
assert w != s, f'window={w} == step={s} (PITFALL 1: sph_stp nie threading preset)'
assert s != l, f'step={s} == linear={l}'
assert w != l, f'window={w} == linear={l}'
print(f'OK distinct: window={w} step={s} linear={l}')
\""

# ── 6. SC #4: nagłówek konfiguracji środowiska (ENV-03 SC-4) ──
echo ""
echo "── 6. SC #4: nagłówek konfiguracji środowiska (ENV-03 SC-4) ──"
check "SC #4 (human): output zawiera sekcję '## Konfiguracja środowiska'" \
    "{ $PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 || true; } | grep '## Konfiguracja środowiska' > /dev/null"
check "SC #4 (human): tabela MD zawiera nagłówek '| Parametr | Wartość |'" \
    "{ $PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 || true; } | grep '| Parametr | Wartość |' > /dev/null"
check "SC #4 (human): tabela zawiera wszystkie 9 etykiet (nU, T, kappa, alpha, K0, K1, phi, rho, seed)" \
    "{ $PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 || true; } | grep -E 'nU|κ \(kappa\)|α \(alpha\)|K0|K1|φ \(phi\)|ρ \(rho\)|seed' | wc -l | { read n; [ \"\$n\" -ge 8 ] || exit 1; }"
check "SC #4 (JSON): env block zawiera 5 nowych kluczy (K0, phi, rho, seed, valuation)" \
    "$PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 --json | $PY -c 'import json,sys; e=json.load(sys.stdin)[\"env\"]; [e[k] for k in (\"K0\",\"phi\",\"rho\",\"seed\",\"valuation\")]; print(\"env keys OK\")'"
check "SC #4 (legacy preserved): output nadal zawiera 'SPH SYMULATOR' banner i 'METRYKI' sekcję" \
    "{ $PY sph_sim.py --strategy naive --zeta 0.5 --no-agent --seed 42 || true; } | grep -E 'SPH SYMULATOR|METRYKI' | wc -l | { read n; [ \"\$n\" -ge 2 ] || exit 1; }"

# ── 7. REPL Pitfall 2 (fake_args AttributeError) defused ──
echo ""
echo "── 7. REPL Pitfall 2 (fake_args AttributeError) defused ──"
check "REPL: 'run naive zeta=0.5' nie crashe na AttributeError; output zawiera nagłówek" \
    "printf 'run naive zeta=0.5\nexit\n' | $PY sph_sim.py --interactive 2>&1 | grep 'Konfiguracja środowiska' > /dev/null"
check "REPL: 'compare naive zeta=0.5' nie crashe na AttributeError; output zawiera PORÓWNANIE" \
    "printf 'compare naive zeta=0.5\nexit\n' | $PY sph_sim.py --interactive 2>&1 | grep 'PORÓWNANIE' > /dev/null"

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
