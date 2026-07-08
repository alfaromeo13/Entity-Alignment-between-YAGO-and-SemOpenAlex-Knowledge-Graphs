#!/bin/bash
#SBATCH --job-name=ea_profiles
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/final_alignment/logs/01_profiles_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/final_alignment/logs/01_profiles_%j.err

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
CANDIDATES=$ROOT/06_experiments/type_text_enrichment/data/ambiguous_candidate_pool_top10_min020.tsv

mkdir -p "$EXP/data" "$EXP/outputs" "$EXP/logs" "$(dirname "$CANDIDATES")"

if [ ! -s "$CANDIDATES" ]; then
  python "$ROOT/06_experiments/type_text_enrichment/scripts/create_enriched_candidate_pool.py" \
    --input "$ROOT/05_entity_alignment/outputs/scores/ambiguous_distmult_embedding_scored.tsv" \
    --output "$CANDIDATES" \
    --min-embedding 0.20 \
    --top-k-per-yago 10
fi

python "$EXP/scripts/analyze_yago_taxonomy.py" \
  --taxonomy "$ROOT/01_raw/yago/yago-taxonomy.ttl" \
  --output "$EXP/outputs/yago_taxonomy_structure.json"

if [ -s "$EXP/data/yago_type_profiles.tsv" ] \
  && [ -s "$EXP/outputs/profile_build_audit.json" ]; then
  echo "Reusing completed taxonomy profiles and build audit"
else
  python "$EXP/scripts/build_yago_type_profiles.py" \
    --entities \
      "$ROOT/05_entity_alignment/outputs/final/alignments_threshold030_typefiltered_1to1.tsv" \
      "$CANDIDATES" \
      "$ROOT/05_entity_alignment/data/gold/proxy_gold_exact_unique.tsv" \
    --graph-dir "$ROOT/02_preprocessed/yago" \
    --taxonomy "$ROOT/01_raw/yago/yago-taxonomy.ttl" \
    --output "$EXP/data/yago_type_profiles.tsv" \
    --audit-output "$EXP/outputs/profile_build_audit.json"
fi

python "$EXP/scripts/audit_types.py" \
  --input "$EXP/data/yago_type_profiles.tsv" \
  --output "$EXP/outputs/profile_type_audit.json"
