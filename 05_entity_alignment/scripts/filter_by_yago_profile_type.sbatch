#!/bin/bash
#SBATCH --job-name=ea_type_filter2
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=20G
#SBATCH --time=00:05:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_type_filter2_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_type_filter2_%j.err

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/filter_by_yago_profile_type.py \
  --input /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/alignments_threshold030_1to1_predicate_profile.tsv \
  --output /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/alignments_threshold030_1to1_profilefiltered.tsv \
  --rejected /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/alignments_threshold030_1to1_profilefiltered_rejected.tsv \
  --summary /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/evaluation/profile_type_filter_summary.tsv