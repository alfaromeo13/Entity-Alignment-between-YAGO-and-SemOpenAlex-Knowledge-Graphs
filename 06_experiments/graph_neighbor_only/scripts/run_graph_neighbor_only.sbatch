#!/bin/bash
#SBATCH --job-name=ea_c
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/06_experiments/graph_neighbor_only/logs/03_c_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/06_experiments/graph_neighbor_only/logs/03_c_%j.err

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
EXP=$ROOT/06_experiments/graph_neighbor_only
S05=$ROOT/05_entity_alignment/final_alignment
GOLD=$ROOT/05_entity_alignment/data/gold/proxy_gold_exact_unique.tsv
CAND=$EXP/data/ambiguous_candidate_pool_top10_min020.tsv
YAGO_NEIGHBORS=$EXP/data/yago_neighbor_context.tsv
SOA_NEIGHBORS=$EXP/data/semopenalex_neighbor_context.tsv
NEIGHBOR_SCORES=$EXP/outputs/ambiguous_graph_neighbor_scores.tsv

mkdir -p "$EXP/data" "$EXP/outputs/permissive" \
  "$EXP/outputs/strict" "$EXP/logs"

if [ ! -s "$CAND" ]; then
  python "$ROOT/06_experiments/type_text_enrichment/scripts/create_enriched_candidate_pool.py" \
    --input "$ROOT/05_entity_alignment/outputs/scores/ambiguous_distmult_embedding_scored.tsv" \
    --output "$CAND" \
    --min-embedding 0.20 \
    --top-k-per-yago 10
fi

if [ ! -s "$YAGO_NEIGHBORS" ] || [ ! -s "$SOA_NEIGHBORS" ]; then
  python "$EXP/scripts/build_candidate_neighbor_profiles.py" \
    --candidates "$CAND" \
    --yago-dir "$ROOT/02_preprocessed/yago" \
    --soa-dir "$ROOT/02_preprocessed/semopenalex_clean" \
    --yago-output "$YAGO_NEIGHBORS" \
    --soa-output "$SOA_NEIGHBORS" \
    --max-parts-per-entity 80
fi

if [ ! -s "$NEIGHBOR_SCORES" ]; then
  python "$EXP/scripts/score_candidate_neighbor_similarity.py" \
    --candidates "$CAND" \
    --yago-profiles "$YAGO_NEIGHBORS" \
    --soa-profiles "$SOA_NEIGHBORS" \
    --output "$NEIGHBOR_SCORES" \
    --batch-size 100000
fi

python "$EXP/scripts/rerank_graph_neighbor_candidates.py" \
  --scores "$NEIGHBOR_SCORES" \
  --yago-profiles "$S05/data/yago_type_profiles.tsv" \
  --permissive-all "$EXP/outputs/permissive/ranked.tsv" \
  --permissive-top1 "$EXP/outputs/permissive/top1.tsv" \
  --strict-all "$EXP/outputs/strict/ranked.tsv" \
  --strict-top1 "$EXP/outputs/strict/top1.tsv" \
  --summary "$EXP/outputs/rerank_summary.json" \
  --min-combined-score 0.20 \
  --embedding-weight 0.80 \
  --neighbor-weight 0.20

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
    --ranked-source embedding_graph_neighbor_top1_v2 \
    --proxy-evidence-column neighbor_tfidf_score \
    --output "$OUT/alignments_graph_neighbor_1to1.tsv" \
    --rejected-proxy "$OUT/proxy_rejected_by_type.tsv" \
    --summary "$OUT/merge_summary.json"

  python "$S05/scripts/audit_types.py" \
    --input "$OUT/alignments_graph_neighbor_1to1.tsv" \
    --output "$OUT/final_type_audit.json"

  python "$EXP/scripts/compare_baseline_vs_enriched.py" \
    --baseline "$BASE" \
    --enriched "$OUT/alignments_graph_neighbor_1to1.tsv" \
    --out-summary "$OUT/baseline_vs_c_summary.tsv"

  python "$ROOT/05_entity_alignment/scripts/evaluate_final_alignments.py" \
    --final "$OUT/alignments_graph_neighbor_1to1.tsv" \
    --proxy-gold "$GOLD" \
    --out-summary "$OUT/evaluation_summary.tsv" \
    --out-type-dist "$OUT/type_distribution.tsv" \
    --out-source-dist "$OUT/source_distribution.tsv"
done
