#!/bin/bash
#SBATCH --job-name=ea_pred_profile
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=10G
#SBATCH --time=01:10:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_pred_profile_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_pred_profile_%j.err

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/profile_final_alignments_predicates.py \
  --alignments /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/alignments_threshold030_typefiltered_1to1.tsv \
  --yago-files \
    /data/horse/ws/jovu353i-kgalign/KGAlignment/01_raw/yago/yago-facts.ttl \
    /data/horse/ws/jovu353i-kgalign/KGAlignment/01_raw/yago/yago-beyond-wikipedia.ttl \
    /data/horse/ws/jovu353i-kgalign/KGAlignment/01_raw/yago/yago-meta-facts.ntx \
  --out-enriched /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/alignments_threshold030_1to1_predicate_profile.tsv \
  --out-predicate-summary /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/evaluation/yago_predicate_semopenalex_type_summary.tsv \
  --out-type-pair-summary /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/evaluation/yago_profile_semopenalex_type_summary.tsv