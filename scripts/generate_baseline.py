#!/usr/bin/env python3
# ──────────────────────────────────────────────────────────────
#  GENERATOR FIXTURES BASELINE (Phase 1 — Refactoring Foundation)
#  Plan: 01-01 (D-08, D-09, D-10, D-11)
#
#  Uruchamia 8 referencyjnych inwokacji `sph_sim.py --json` na
#  PRZEDREFACTOROWYM monolicie (v1.0) i zapisuje wynik JSON do
#  `tests/fixtures/baseline_v1/<slug>.json` (pretty-printed,
#  sort_keys=True → deterministyczny git diff).
#
#  Wygenerowane fixtures są autorytatywnym oracle prawdy dla
#  `scripts/regression_check.py`. Po refactorze (plany 02–05)
#  KAŻDY ponowny run regression_check musi zwracać exit code 0
#  inaczej CLI-04 (backwards compat) jest złamany.
#
#  Skrypt jest deterministyczny: dwa kolejne uruchomienia tworzą
#  bit-identyczne pliki (gwarantowane przez --seed 42, sort_keys).
#
#  Stdlib only — Python 3.7+.
# ──────────────────────────────────────────────────────────────

import json
import subprocess
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# 8 INWOKACJI Z D-09 (docstring sph_sim.py:11–18 + baseline)
# ──────────────────────────────────────────────────────────────
# Każda krotka: (slug, [args_bez_seed_i_json])
# Skrypt ZAWSZE dokłada '--seed 42 --json' do każdej inwokacji.
INVOCATIONS = [
    ('01-naive-zeta-0.5',
     ['--strategy', 'naive', '--zeta', '0.5']),
    ('02-threshold-max-phase-3',
     ['--strategy', 'threshold', '--max_phase', '3']),
    ('03-phase-prob-default',
     ['--strategy', 'phase_prob', '--probs', '0.9,0.7,0.5,0.3,0.0']),
    ('04-incentive-expected-P-100',
     ['--strategy', 'incentive', '--expected_P', '100']),
    ('05-adaptive-s-target-10',
     ['--strategy', 'adaptive', '--s_target', '10']),
    ('06-naive-zeta-0.4-custom-env',
     ['--strategy', 'naive', '--zeta', '0.4',
      '--nU', '200', '--nSUS', '20', '--K1', '120', '--T', '1000']),
    ('07-phase-prob-custom-kappa-alpha',
     ['--strategy', 'phase_prob', '--probs', '1.0,0.8,0.6,0.2,0.0',
      '--kappa', '0.5', '--alpha', '0']),
    ('08-naive-zeta-0.75-baseline',
     ['--strategy', 'naive', '--zeta', '0.75']),
]

# Pełne human-readable komendy do MANIFEST.txt (dla peer review)
COMMANDS_HUMAN = [
    'python sph_sim.py --strategy naive --zeta 0.5 --seed 42 --json',
    'python sph_sim.py --strategy threshold --max_phase 3 --seed 42 --json',
    'python sph_sim.py --strategy phase_prob --probs 0.9,0.7,0.5,0.3,0.0 --seed 42 --json',
    'python sph_sim.py --strategy incentive --expected_P 100 --seed 42 --json',
    'python sph_sim.py --strategy adaptive --s_target 10 --seed 42 --json',
    'python sph_sim.py --strategy naive --zeta 0.4 --nU 200 --nSUS 20 --K1 120 --T 1000 --seed 42 --json',
    'python sph_sim.py --strategy phase_prob --probs 1.0,0.8,0.6,0.2,0.0 --kappa 0.5 --alpha 0 --seed 42 --json',
    'python sph_sim.py --strategy naive --zeta 0.75 --seed 42 --json',
]

# Project root = parent katalogu scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_ROOT / 'tests' / 'fixtures' / 'baseline_v1'
MANIFEST_PATH = FIXTURES_DIR / 'MANIFEST.txt'
MONOLITH = PROJECT_ROOT / 'sph_sim.py'


def run_invocation(slug, args):
    """Uruchamia sph_sim.py z podanymi flagami + '--seed 42 --json',
    parsuje stdout jako JSON, zwraca dict."""
    full_args = [sys.executable, str(MONOLITH), *args, '--seed', '42', '--json']
    result = subprocess.run(
        full_args,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def main():
    if not MONOLITH.exists():
        print(f"FATAL: nie znaleziono monolitu {MONOLITH}", file=sys.stderr)
        sys.exit(2)

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    total = len(INVOCATIONS)

    for i, (slug, args) in enumerate(INVOCATIONS, start=1):
        try:
            data = run_invocation(slug, args)
        except subprocess.CalledProcessError as e:
            print(f"[{i}/{total}] {slug} -> FAIL (subprocess exit {e.returncode})",
                  file=sys.stderr)
            print(f"  stderr: {e.stderr}", file=sys.stderr)
            sys.exit(2)
        except json.JSONDecodeError as e:
            print(f"[{i}/{total}] {slug} -> FAIL (nie JSON: {e})", file=sys.stderr)
            sys.exit(2)

        fixture_path = FIXTURES_DIR / f"{slug}.json"
        # sort_keys=True + indent=2 + LF + końcowy newline → deterministyczny diff
        payload = json.dumps(data, indent=2, sort_keys=True) + '\n'
        fixture_path.write_text(payload, encoding='utf-8')

        avg_val = data.get('metrics', {}).get('avg_val_last100', '?')
        print(f"[{i}/{total}] {slug} -> OK (avg_val_last100={avg_val})",
              file=sys.stderr)

    # MANIFEST.txt — slug -> pełna komenda (peer review widoczność)
    manifest_lines = []
    for (slug, _args), human_cmd in zip(INVOCATIONS, COMMANDS_HUMAN):
        manifest_lines.append(f"{slug}.json | {human_cmd}")
    MANIFEST_PATH.write_text('\n'.join(manifest_lines) + '\n', encoding='utf-8')

    print(f"\nGenerated {total} fixtures + MANIFEST.txt w {FIXTURES_DIR}",
          file=sys.stderr)


if __name__ == '__main__':
    main()
