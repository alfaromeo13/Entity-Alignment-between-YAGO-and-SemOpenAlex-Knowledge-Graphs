#!/bin/bash
#SBATCH --job-name=ea_merge_tfidf
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=20G
#SBATCH --time=00:05:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_merge_tfidf_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_merge_tfidf_%j.err

set -euo pipefail

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs
mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/merge_tfidf.py \
  --alignments /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/alignments_threshold030_1to1_profilefiltered.tsv \
  --tfidf-scores /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/tfidf_scores.tsv \
  --output /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/alignments_FINAL_production_tfidf.tsv