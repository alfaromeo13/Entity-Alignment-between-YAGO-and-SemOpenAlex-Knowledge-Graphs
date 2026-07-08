#!/bin/bash
#SBATCH --job-name=ea_eval_final
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=30G
#SBATCH --time=00:10:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_eval_final_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_eval_final_%j.err

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/evaluation

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/evaluate_final_alignments.py \
  --final /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/alignments_FINAL_production_tfidf.tsv \
  --proxy-gold /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/gold/proxy_gold_exact_unique.tsv \
  --out-summary /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/evaluation/final_alignment_summary.tsv \
  --out-type-dist /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/evaluation/final_alignment_type_distribution.tsv \
  --out-source-dist /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/evaluation/final_alignment_source_distribution.tsv