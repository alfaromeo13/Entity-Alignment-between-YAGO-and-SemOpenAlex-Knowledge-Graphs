#!/bin/bash
#SBATCH --job-name=ea_ab
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/06_experiments/type_text_enrichment/logs/01_ab_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/06_experiments/type_text_enrichment/logs/01_ab_%j.err

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
EXP=$ROOT/06_experiments/type_text_enrichment
S05=$ROOT/05_entity_alignment/final_alignment
GOLD=$ROOT/05_entity_alignment/data/gold/proxy_gold_exact_unique.tsv
CAND=$EXP/data/ambiguous_candidate_pool_top10_min020.tsv
YAGO_TEXT=$EXP/data/yago_text_profiles.tsv
SOA_TEXT=$EXP/data/semopenalex_text_profiles.tsv
PROFILE_SCORES=$EXP/outputs/ambiguous_profile_text_scores.tsv

mkdir -p "$EXP/data" "$EXP/outputs/permissive" \
  "$EXP/outputs/strict" "$EXP/logs"

if [ ! -s "$CAND" ]; then
  python "$EXP/scripts/create_enriched_candidate_pool.py" \
    --input "$ROOT/05_entity_alignment/outputs/scores/ambiguous_distmult_embedding_scored.tsv" \
    --output "$CAND" \
    --min-embedding 0.20 \
    --top-k-per-yago 10
fi

if [ ! -s "$YAGO_TEXT" ]; then
  python "$EXP/scripts/build_entity_text_profiles.py" \
    --input "$ROOT/02_preprocessed/yago/entity_text_raw.tsv" \
    --output "$YAGO_TEXT"
fi

if [ ! -s "$SOA_TEXT" ]; then
  python "$EXP/scripts/build_entity_text_profiles.py" \
    --input "$ROOT/02_preprocessed/semopenalex_clean/entity_text_raw.tsv" \
    --output "$SOA_TEXT"
fi

if [ ! -s "$PROFILE_SCORES" ]; then
  python "$EXP/scripts/score_profile_text_similarity.py" \
    --candidates "$CAND" \
    --yago-profiles "$YAGO_TEXT" \
    --semopenalex-profiles "$SOA_TEXT" \
    --output "$PROFILE_SCORES" \
    --batch-size 100000
fi

python "$EXP/scripts/rerank_type_text_candidates.py" \
  --candidates "$CAND" \
  --profile-scores "$PROFILE_SCORES" \
  --yago-profiles "$S05/data/yago_type_profiles.tsv" \
  --permissive-all "$EXP/outputs/permissive/ranked.tsv" \
  --permissive-top1 "$EXP/outputs/permissive/top1.tsv" \
  --strict-all "$EXP/outputs/strict/ranked.tsv" \
  --strict-top1 "$EXP/outputs/strict/top1.tsv" \
  --summary "$EXP/outputs/rerank_summary.json" \
  --min-combined-score 0.25 \
  --embedding-weight 0.65 \
  --profile-weight 0.35

for VARIANT in permissive strict; do
  OUT=$EXP/outputs/$VARIANT
  BASE=$S05/outputs/$VARIANT/alignments_FINAL_tfidf.tsv
  if [ "$VARIANT" = permissive ]; then
    POLICY=keep
  else
    POLICY=reject
  fi

  python "$EXP/scripts/merge_proxy_gold.py" \
    --proxy-gold "$GOLD" \
    --top1 "$OUT/top1.tsv" \
    --yago-profiles "$S05/data/yago_type_profiles.tsv" \
    --unresolved-policy "$POLICY" \
    --output "$OUT/alignments_type_text_enriched_1to1.tsv" \
    --rejected-proxy "$OUT/proxy_rejected_by_type.tsv" \
    --summary "$OUT/merge_summary.json"

  python "$S05/scripts/audit_types.py" \
    --input "$OUT/alignments_type_text_enriched_1to1.tsv" \
    --output "$OUT/final_type_audit.json"

  python "$EXP/scripts/compare_baseline_vs_enriched.py" \
    --baseline "$BASE" \
    --enriched "$OUT/alignments_type_text_enriched_1to1.tsv" \
    --out-summary "$OUT/baseline_vs_ab_summary.tsv"

  python "$ROOT/05_entity_alignment/scripts/evaluate_final_alignments.py" \
    --final "$OUT/alignments_type_text_enriched_1to1.tsv" \
    --proxy-gold "$GOLD" \
    --out-summary "$OUT/evaluation_summary.tsv" \
    --out-type-dist "$OUT/type_distribution.tsv" \
    --out-source-dist "$OUT/source_distribution.tsv"
done
