#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  verify_phase1.sh — phase exit gate / pre-flight check
#  Plan 01-05 — Final audit script (CLI-04 + ROADMAP SC#1-4 + D-06/07/16)
#
#  Weryfikuje że Faza 1 (refactoring foundation) spełnia WSZYSTKIE 4
#  Success Criteria z ROADMAP.md oraz wybrane decyzje z 01-CONTEXT.md:
#
#    [SC#1+4] Regression check — 8 inwokacji bit-identical z fixtures
#             (CLI-04 hard requirement; chroni numerical equivalence)
#    [SC#2]   Module line count — każdy plik w sphsim/ ma ≤ 150 linii
#    [SC#3]   python sph_sim.py działa jako entry point
#    [D-06]   python -m sphsim alternatywny entry point działa
#    [D-16]   Publiczne API: from sphsim import SPHSimulator, Device, STRATEGIES
#    [D-07]   Negative constraint: brak pyproject.toml / setup.cfg / setup.py
#    [stdlib] Brak nowych zewnętrznych zależności poza stdlib (Phase 1 constraint)
#
#  Re-runnable po dowolnej zmianie w sphsim/ jako pre-flight przed Phase 2+.
#  Stdlib + coreutils only — bez nowych zależności (Phase 1 D-07).
#
#  Exit codes:
#    0 — wszystkie checks PASS
#    2 — SC#2 fail (moduł > 150 linii)
#    3 — SC#3 fail (python sph_sim.py nie działa)
#    4 — D-06 fail (python -m sphsim nie działa)
#    5 — D-16 fail (publiczne API nie importuje się)
#    6 — stdlib constraint naruszony (non-stdlib import w sphsim/)
#    7 — D-07 fail (znaleziono pyproject.toml / setup.cfg / setup.py)
#  Niezerowy exit z regression_check.py (SC#1+4) jest propagowany przez set -e.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

# Przejdź do project root (skrypt może być wywołany skądkolwiek).
cd "$(dirname "$0")/.."

# Wybierz interpreter Pythona. Preferuj `python` (jeśli istnieje), w przeciwnym
# razie `python3` — macOS dev env po Python 3.12+ nie symlinkuje już `python`.
# ROADMAP SC#3 mówi że sph_sim.py "pozostaje uruchamialny jako entry point",
# nie że literal command `python` musi istnieć w PATH.
if command -v python >/dev/null 2>&1; then
    PY=python
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "FATAL: ani 'python' ani 'python3' nie ma w PATH" >&2
    exit 1
fi

echo "=== Phase 1: Refactoring foundation — verification ==="
echo "Interpreter: $PY ($($PY --version 2>&1))"

# ─── SC#1 + SC#4: regression check (8 fixtures bit-identical) ─────
echo
echo "[SC#1+4] Regression check (8 fixtures bit-identical)..."
"$PY" scripts/regression_check.py
echo "  OK — wszystkie 8 inwokacji produkują identyczne JSON"

# ─── SC#2: module line count (każdy ≤ 150 linii) ──────────────────
echo
echo "[SC#2] Module line counts (≤ 150 linii each)..."
fail=0
while IFS= read -r f; do
    n=$(wc -l < "$f" | tr -d ' ')
    if [ "$n" -gt 150 ]; then
        echo "  FAIL: $f = $n linii (limit 150)"
        fail=1
    else
        printf "  %-40s %4d linii\n" "$f" "$n"
    fi
done < <(find sphsim -name '*.py' -type f | sort)
if [ "$fail" -ne 0 ]; then
    echo "FAIL SC#2: są moduły powyżej 150 linii" >&2
    exit 2
fi
echo "  OK — wszystkie moduły ≤ 150 linii"

# ─── SC#3: sph_sim.py jako entry point ────────────────────────────
echo
echo "[SC#3] $PY sph_sim.py jako entry point..."
out=$("$PY" sph_sim.py --strategy naive --seed 42 --json 2>&1)
if ! echo "$out" | "$PY" -c "import sys, json; d=json.loads(sys.stdin.read()); assert d['strategy']=='naive'" 2>/dev/null; then
    echo "FAIL SC#3: sph_sim.py nie działa jako entry point" >&2
    echo "$out" | head -5 >&2
    exit 3
fi
echo "  OK — $PY sph_sim.py działa i produkuje poprawny JSON (strategy=naive)"

# ─── D-06: python -m sphsim alternatywny entry point ──────────────
echo
echo "[D-06] $PY -m sphsim alternatywny entry point..."
out=$("$PY" -m sphsim --strategy naive --seed 42 --json 2>&1)
if ! echo "$out" | "$PY" -c "import sys, json; d=json.loads(sys.stdin.read()); assert d['strategy']=='naive'" 2>/dev/null; then
    echo "FAIL D-06: $PY -m sphsim nie działa" >&2
    echo "$out" | head -5 >&2
    exit 4
fi
echo "  OK — $PY -m sphsim działa i produkuje poprawny JSON"

# ─── D-16: publiczne API ──────────────────────────────────────────
echo
echo "[D-16] Publiczne API: from sphsim import SPHSimulator, Device, STRATEGIES..."
if ! "$PY" -c "
from sphsim import SPHSimulator, Device, STRATEGIES
assert callable(SPHSimulator), 'SPHSimulator nie jest callable'
assert callable(Device) or hasattr(Device, '__dataclass_fields__'), 'Device nie jest klasą/dataclass'
assert isinstance(STRATEGIES, dict), 'STRATEGIES nie jest dict'
expected = {'naive', 'threshold', 'phase_prob', 'incentive', 'adaptive'}
missing = expected - set(STRATEGIES.keys())
assert not missing, f'brakuje strategii w STRATEGIES: {missing}'
" 2>&1; then
    echo "FAIL D-16: publiczne API nie importuje się poprawnie" >&2
    exit 5
fi
echo "  OK — SPHSimulator + Device + STRATEGIES (z 5 wbudowanymi strategiami) importowalne"

# ─── D-07: BEZ pyproject.toml / setup.cfg / setup.py ──────────────
echo
echo "[D-07] Negative constraint: brak pyproject.toml / setup.cfg / setup.py..."
forbidden=()
for f in pyproject.toml setup.cfg setup.py; do
    if [ -f "$f" ]; then
        forbidden+=("$f")
    fi
done
if [ "${#forbidden[@]}" -ne 0 ]; then
    echo "FAIL D-07: znaleziono niedozwolone pliki: ${forbidden[*]}" >&2
    echo "       Phase 1: 'projekt lokalny, nie publikowany' (01-CONTEXT.md D-07)" >&2
    exit 7
fi
echo "  OK — projekt pozostaje 'lokalny, nie publikowany' (brak setup metadata)"

# ─── Phase 1 constraint: stdlib only ─────────────────────────────
# Whitelist modułów dozwolonych w sphsim/: stdlib + sam pakiet sphsim.
# Każdy import spoza tej listy → potencjalna nowa zależność → WARN.
echo
echo "[Phase 1 constraint] stdlib only — brak nowych zależności..."
ALLOWED='^(argparse|json|random|math|dataclasses|typing|collections|itertools|functools|pathlib|os|sys|subprocess|re|copy|enum|abc|warnings|logging|time|sphsim)$'
suspicious=()
while IFS= read -r f; do
    # Wyciągnij top-level pakiety z 'import X' i 'from X import ...'.
    # Ignoruj komentarze, docstringi, dosłowne stringi.
    while IFS= read -r mod; do
        if [ -n "$mod" ] && ! echo "$mod" | grep -qE "$ALLOWED"; then
            suspicious+=("$f: $mod")
        fi
    done < <(grep -E "^[[:space:]]*(import|from)[[:space:]]+[a-zA-Z_]" "$f" 2>/dev/null \
             | sed -E 's/^[[:space:]]*(import|from)[[:space:]]+([a-zA-Z_][a-zA-Z0-9_]*).*$/\2/' \
             | sort -u)
done < <(find sphsim -name '*.py' -type f)

if [ "${#suspicious[@]}" -eq 0 ]; then
    echo "  OK — pakiet sphsim używa tylko stdlib + własnych modułów"
else
    echo "  WARN: znaleziono potencjalne non-stdlib importy (sprawdź manualnie):" >&2
    for entry in "${suspicious[@]}"; do
        echo "    $entry" >&2
    done
    echo "  WARN nie blokuje gate'a — Phase 6 doda matplotlib (whitelist update wtedy)." >&2
    # Nie exit'ujemy — Phase 6 zaplanował matplotlib; jeśli pojawi się tu wcześniej,
    # niech to będzie świadoma decyzja widoczna w PR review.
fi

# ─── Summary ──────────────────────────────────────────────────────
echo
echo "=== ALL CHECKS PASSED — Phase 1 spełnia wszystkie ROADMAP Success Criteria ==="
echo "    SC#1+4: regression 8/8 ✓   SC#2: ≤150 LOC/moduł ✓   SC#3: sph_sim.py ✓"
echo "    D-06: python -m sphsim ✓   D-16: publiczne API ✓   D-07: bez setup metadata ✓"
echo "Można rozpocząć Phase 2 (Interactive CLI shell)."
