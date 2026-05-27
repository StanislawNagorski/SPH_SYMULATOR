#!/usr/bin/env python3
# ──────────────────────────────────────────────────────────────
#  REGRESJA BACKWARDS-COMPAT (Phase 1 — Refactoring Foundation)
#  Plan: 01-01, Task 2 (D-08, D-11)
#
#  Skrypt regresji: re-uruchamia 8 inwokacji v1.0 i porównuje
#  z committed fixtures w tests/fixtures/baseline_v1/.
#
#  Używany przez plany 02–05 po KAŻDEJ zmianie w sph_sim.py
#  (lub przyszłym pakiecie sphsim/) jako oracle prawdy dla
#  REQ CLI-04 (backwards compatibility hard requirement).
#
#  Exit code:
#    0  — wszystkie 8 inwokacji match (bit-identical)
#    1  — choć jedna różnica względem fixture
#    2  — błąd uruchomienia (subprocess / parsing JSON / I/O)
#
#  Porównanie: exact equality dla wszystkich pól (włącznie
#  z floatami). Fixtures są generowane przez ten sam interpreter
#  z tego samego seeda — każda różnica oznacza realny regress.
#
#  Stdlib only — Python 3.7+. Bez pytest, bez kolorów.
# ──────────────────────────────────────────────────────────────

import argparse
import json
import subprocess
import sys
from pathlib import Path

# DRY: ta sama lista co w generate_baseline.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_baseline import INVOCATIONS, PROJECT_ROOT, FIXTURES_DIR, MONOLITH  # noqa: E402

# Phase 4 D-67 (Strategia B): zamiast regenerować baseline_v1/*.json fixtures lub dodawać --no-agent
# do INVOCATIONS, ignorujemy 3 nowe klucze (wprowadzone w Phase 4 jako agent veto layer) przy
# compare z fixtures. To zachowuje semantykę "fixtures są oracle dla istniejących pól metrics"
# bez konieczności regeneracji ani touch'owania generate_baseline.py.
# Phase 4 D-67: trzy nowe klucze w metrics są ignorowane przy compare z baseline_v1 fixtures —
# fixtures są oracle dla v1.0 zachowania i nie zawierają tych pól. Pola obecne tylko w actual output.
SKIP_KEYS = ('veto_per_phase', 'n_vetoed_total', 'agent_enabled')


def deep_diff(expected, actual, path=''):
    """Rekurencyjnie porównuje dwa obiekty (dict/list/scalar).
    Zwraca listę stringów opisujących różnice. Pusta lista = identyczne.
    Porównuje EXACT EQUALITY — bez tolerance dla floatów.
    Phase 4 D-67 (Strategia B): klucze z SKIP_KEYS są ignorowane w każdym dict."""
    diffs = []

    # Type mismatch
    if type(expected) is not type(actual):
        diffs.append(
            f"{path or '(root)'}: typ expected={type(expected).__name__} "
            f"got={type(actual).__name__} (expected_val={expected!r}, got_val={actual!r})"
        )
        return diffs

    if isinstance(expected, dict):
        ek = set(expected.keys()) - set(SKIP_KEYS)
        ak = set(actual.keys()) - set(SKIP_KEYS)
        for k in sorted(ek - ak):
            diffs.append(f"{path}.{k}: KEY MISSING w actual (expected={expected[k]!r})")
        for k in sorted(ak - ek):
            diffs.append(f"{path}.{k}: KEY EXTRA w actual (got={actual[k]!r})")
        for k in sorted(ek & ak):
            sub = f"{path}.{k}" if path else k
            diffs.extend(deep_diff(expected[k], actual[k], sub))
        return diffs

    if isinstance(expected, list):
        if len(expected) != len(actual):
            diffs.append(
                f"{path or '(root)'}: list length expected={len(expected)} got={len(actual)}"
            )
            # nie iterujemy dalej — różnica długości już sygnalizuje regres
            return diffs
        for i, (ev, av) in enumerate(zip(expected, actual)):
            diffs.extend(deep_diff(ev, av, f"{path}[{i}]"))
        return diffs

    # Scalar (str / int / float / bool / None) — exact equality
    if expected != actual:
        diffs.append(f"{path or '(root)'}: expected={expected!r}, got={actual!r}")
    return diffs


def run_invocation(args):
    """Uruchamia sph_sim.py z podanymi flagami + '--no-agent --seed 42 --json'.
    --no-agent gwarantuje że istniejące metryki są bit-identyczne z baseline_v1 fixtures
    (Phase 4 D-67 Strategia B: INVOCATIONS w generate_baseline.py pozostają bez zmian,
    regression_check dodaje --no-agent lokalnie aby agent default-on nie zmieniał metryk).
    Zwraca (dict, None) przy sukcesie lub (None, error_str) przy błędzie."""
    full_args = [sys.executable, str(MONOLITH), *args, '--no-agent', '--seed', '42', '--json']
    try:
        result = subprocess.run(
            full_args,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        return None, f"subprocess exit {e.returncode}: {e.stderr.strip()}"
    except FileNotFoundError as e:
        return None, f"file not found: {e}"

    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as e:
        return None, f"stdout nie jest JSON: {e}"


def load_fixture(slug):
    """Wczytuje committed fixture. Zwraca (dict, None) lub (None, error)."""
    path = FIXTURES_DIR / f"{slug}.json"
    if not path.exists():
        return None, f"fixture brakuje: {path}"
    try:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f), None
    except (OSError, json.JSONDecodeError) as e:
        return None, f"błąd wczytania {path}: {e}"


def main():
    parser = argparse.ArgumentParser(
        description='Regression check: 8 inwokacji v1.0 vs committed fixtures'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='Drukuj per-invocation status (OK/FAIL) zamiast samego summary'
    )
    args = parser.parse_args()

    if not MONOLITH.exists():
        print(f"FATAL: nie znaleziono monolitu {MONOLITH}", file=sys.stderr)
        return 2

    if not FIXTURES_DIR.exists():
        print(f"FATAL: katalog fixtures nie istnieje: {FIXTURES_DIR}", file=sys.stderr)
        print("       Uruchom najpierw: python scripts/generate_baseline.py", file=sys.stderr)
        return 2

    total = len(INVOCATIONS)
    failed_slugs = []
    runtime_errors = []

    for i, (slug, inv_args) in enumerate(INVOCATIONS, start=1):
        # Load fixture
        expected, err = load_fixture(slug)
        if err:
            runtime_errors.append((slug, err))
            if args.verbose:
                print(f"[{i}/{total}] {slug} -> FAIL ({err})", file=sys.stderr)
            continue

        # Run current monolith
        actual, err = run_invocation(inv_args)
        if err:
            runtime_errors.append((slug, err))
            if args.verbose:
                print(f"[{i}/{total}] {slug} -> FAIL ({err})", file=sys.stderr)
            continue

        # Deep diff
        diffs = deep_diff(expected, actual)
        if diffs:
            failed_slugs.append(slug)
            if args.verbose:
                print(f"[{i}/{total}] {slug} -> FAIL ({len(diffs)} różnic)",
                      file=sys.stderr)
            # Zawsze drukuj diff'y (nawet bez --verbose) — peer review widzi co się zmieniło
            for d in diffs:
                print(f"  diff [{slug}] {d}", file=sys.stderr)
        else:
            if args.verbose:
                print(f"[{i}/{total}] {slug} -> OK", file=sys.stderr)

    # Summary
    passed = total - len(failed_slugs) - len(runtime_errors)

    if runtime_errors:
        print(f"\nFAIL: {passed}/{total} (runtime errors:"
              f" {', '.join(s for s, _ in runtime_errors)})", file=sys.stderr)
        return 2

    if failed_slugs:
        print(f"\nFAIL: {passed}/{total} (regresja w: {', '.join(failed_slugs)})",
              file=sys.stderr)
        return 1

    print(f"PASS: {passed}/{total}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
