#!/bin/bash
#SBATCH --job-name=ea_tfidf_safe
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=5G
#SBATCH --time=00:10:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_tfidf_safe_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_tfidf_safe_%j.err

set -euo pipefail

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs
mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/prepare_tfidf_input.py \
  --input /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/alignments_threshold030_1to1_profilefiltered.tsv \
  --output /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/tfidf_input.tsv \
  --only-embedding \
  --min-embedding 0.30

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/tfidf_rerank_safe.py \
  --input /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/tfidf_input.tsv \
  --output /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/tfidf_scores.tsv