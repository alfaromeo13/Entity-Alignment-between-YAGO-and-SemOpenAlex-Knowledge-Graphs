#!/bin/bash
#SBATCH --job-name=ea_abc
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=18:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/06_experiments/graph_neighbor_signal/logs/02_abc_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/06_experiments/graph_neighbor_signal/logs/02_abc_%j.err

set -euo pipefail

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
unset LD_PRELOAD || true
PYTHON_EXE=$(command -v python)
PYTHON_ROOT=$(cd "$(dirname "$PYTHON_EXE")/.." && pwd)
export LD_LIBRARY_PATH="$PYTHON_ROOT/lib:${LD_LIBRARY_PATH:-}"
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

ROOT=/data/horse/ws/jovu353i-kgalign/KGAlignment
EXP=$ROOT/06_experiments/graph_neighbor_signal
AB=$ROOT/06_experiments/type_text_enrichment
S05=$ROOT/05_entity_alignment/final_alignment
GOLD=$ROOT/05_entity_alignment/data/gold/proxy_gold_exact_unique.tsv
ALIGNMENT_VARIANT=${ALIGNMENT_VARIANT:-strict}

if [ "$ALIGNMENT_VARIANT" != permissive ] && [ "$ALIGNMENT_VARIANT" != strict ]; then
  echo "ALIGNMENT_VARIANT must be permissive or strict" >&2
  exit 2
fi

ALIGN=$AB/outputs/$ALIGNMENT_VARIANT/alignments_type_text_enriched_1to1.tsv
BASE=$S05/outputs/$ALIGNMENT_VARIANT/alignments_FINAL_tfidf.tsv
OUT=$EXP/outputs/$ALIGNMENT_VARIANT
DATA=$EXP/data/$ALIGNMENT_VARIANT

mkdir -p "$OUT/sensitivity" "$DATA" "$EXP/logs"
cd "$ROOT"

python "$EXP/scripts/build_neighbor_context_profiles.py" \
  --alignments "$ALIGN" \
  --yago-dir "$ROOT/02_preprocessed/yago" \
  --soa-dir "$ROOT/02_preprocessed/semopenalex_clean" \
  --yago-output "$DATA/yago_neighbor_context.tsv" \
  --soa-output "$DATA/semopenalex_neighbor_context.tsv" \
  --max-parts-per-entity 40

python "$EXP/scripts/score_neighbor_context_similarity.py" \
  --alignments "$ALIGN" \
  --yago-profiles "$DATA/yago_neighbor_context.tsv" \
  --soa-profiles "$DATA/semopenalex_neighbor_context.tsv" \
  --output "$OUT/alignments_type_text_with_neighbor_scores.tsv" \
  --batch-size 100000

python "$EXP/scripts/summarize_neighbor_scores.py" \
  --input "$OUT/alignments_type_text_with_neighbor_scores.tsv" \
  --baseline "$BASE" \
  --output "$OUT/neighbor_score_summary.tsv"

python "$EXP/scripts/run_abc_sensitivity.py" \
  --input "$OUT/alignments_type_text_with_neighbor_scores.tsv" \
  --baseline "$BASE" \
  --proxy-gold "$GOLD" \
  --out-dir "$OUT/sensitivity"

python "$S05/scripts/audit_types.py" \
  --input "$OUT/sensitivity/abc_w060_035_005_t030.tsv" \
  --output "$OUT/final_type_audit.json"
