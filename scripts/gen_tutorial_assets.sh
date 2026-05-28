#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  gen_tutorial_assets.sh — regenerate docs/assets/*.png deterministically
#  (D-14: naive --zeta 0.75 --seed 42 for byte-identical PNGs across runs)
#
#  Outputs (3 canonical PNGs anchoring docs/PRZEWODNIK.md):
#    - docs/assets/decision_distribution_naive.png  (single-run, --seed 42)
#    - docs/assets/kpi_timeseries_naive.png         (single-run, --seed 42)
#    - docs/assets/batch_aggregate_naive.png        (batch, seeds 1..5)
#
#  IMPORTANT: do NOT pass --seed 42 to the batch command — `--seeds 5`
#  already implies range(1,6) deterministically. Adding --seed 42 would
#  reseed the FIRST run to 42 instead of using seeds 1..5 as designed.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
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

mkdir -p docs/assets/

# Clean any previous local reports/ to make `ls -d ./reports/<latest>/` unambiguous.
rm -rf ./reports/tutorial-* ./reports/batch_* ./reports/[0-9]*

# 1. Single-run → decision_distribution + kpi_timeseries from naive --zeta 0.75 --seed 42
SPHSIM_NO_REPORT='' $PY sph_sim.py --strategy naive --zeta 0.75 --seed 42 --no-agent > /tmp/p8_gen_single.log 2>&1
LATEST=$(ls -d ./reports/[0-9]*/ 2>/dev/null | tail -1)
if [ -z "$LATEST" ]; then
    echo "FATAL: single-run did not produce a report directory" >&2
    cat /tmp/p8_gen_single.log >&2
    exit 1
fi
cp "${LATEST}decision_distribution.png" docs/assets/decision_distribution_naive.png
cp "${LATEST}kpi_timeseries.png"        docs/assets/kpi_timeseries_naive.png

# 2. Batch-run → batch_aggregate from `naive --zeta 0.75 --batch --seeds 5` (seeds 1..5)
# DO NOT pass --seed 42 here (it would seed the FIRST run to 42, not what we want).
rm -rf ./reports/tutorial-* ./reports/batch_* ./reports/[0-9]*
SPHSIM_NO_REPORT='' $PY sph_sim.py --strategy naive --zeta 0.75 --batch --seeds 5 --no-agent > /tmp/p8_gen_batch.log 2>&1
LATEST_B=$(ls -d ./reports/batch_*/ 2>/dev/null | tail -1)
if [ -z "$LATEST_B" ]; then
    echo "FATAL: batch run did not produce a batch_*/ directory" >&2
    cat /tmp/p8_gen_batch.log >&2
    exit 1
fi
cp "${LATEST_B}batch_aggregate.png" docs/assets/batch_aggregate_naive.png

# 3. Verify PNG magic bytes on all 3
for f in docs/assets/decision_distribution_naive.png \
         docs/assets/kpi_timeseries_naive.png \
         docs/assets/batch_aggregate_naive.png; do
    $PY -c "import sys; d=open('$f','rb').read(8); sys.exit(0 if d==b'\\x89PNG\\r\\n\\x1a\\n' else 1)" \
        || { echo "FAIL: $f is not a valid PNG" >&2; exit 1; }
done

# 4. Clean up temporary reports/ — only docs/assets/ should persist
rm -rf ./reports/tutorial-* ./reports/batch_* ./reports/[0-9]*
rm -f /tmp/p8_gen_*.log

echo "docs/assets/ regenerated OK (3 PNGs, deterministic --seed 42)."
