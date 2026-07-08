#!/bin/bash
#SBATCH --job-name=ea_stage05
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/final_alignment/logs/02_stage05_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/final_alignment/logs/02_stage05_%j.err

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
EXP=$ROOT/05_entity_alignment/final_alignment
INPUT=$ROOT/05_entity_alignment/outputs/final/alignments_threshold030_typefiltered_1to1.tsv
PROFILES=$EXP/data/yago_type_profiles.tsv
GOLD=$ROOT/05_entity_alignment/data/gold/proxy_gold_exact_unique.tsv

mkdir -p "$EXP/outputs/permissive" \
  "$EXP/outputs/strict" "$EXP/logs"

for VARIANT in permissive strict; do
  if [ "$VARIANT" = permissive ]; then
    POLICY=keep
  else
    POLICY=reject
  fi
  OUT=$EXP/outputs/$VARIANT

  python "$EXP/scripts/apply_stage05_type_filter.py" \
    --input "$INPUT" \
    --profiles "$PROFILES" \
    --accepted "$OUT/typefiltered.tsv" \
    --rejected "$OUT/typefiltered_rejected.tsv" \
    --summary "$OUT/type_filter_summary.json" \
    --unresolved-policy "$POLICY"

  python "$ROOT/05_entity_alignment/scripts/prepare_tfidf_input.py" \
    --input "$OUT/typefiltered.tsv" \
    --output "$OUT/tfidf_input.tsv" \
    --only-embedding \
    --min-embedding 0.30

  python "$ROOT/05_entity_alignment/scripts/tfidf_rerank_safe.py" \
    --input "$OUT/tfidf_input.tsv" \
    --output "$OUT/tfidf_scores.tsv"

  python "$ROOT/05_entity_alignment/scripts/merge_tfidf.py" \
    --alignments "$OUT/typefiltered.tsv" \
    --tfidf-scores "$OUT/tfidf_scores.tsv" \
    --output "$OUT/alignments_FINAL_tfidf.tsv" \
    --high-embedding-threshold 0.40 \
    --low-embedding-threshold 0.30 \
    --tfidf-threshold 0.85

  python "$EXP/scripts/audit_types.py" \
    --input "$OUT/alignments_FINAL_tfidf.tsv" \
    --output "$OUT/final_type_audit.json"

  python "$ROOT/05_entity_alignment/scripts/evaluate_final_alignments.py" \
    --final "$OUT/alignments_FINAL_tfidf.tsv" \
    --proxy-gold "$GOLD" \
    --out-summary "$OUT/evaluation_summary.tsv" \
    --out-type-dist "$OUT/type_distribution.tsv" \
    --out-source-dist "$OUT/source_distribution.tsv"
done
