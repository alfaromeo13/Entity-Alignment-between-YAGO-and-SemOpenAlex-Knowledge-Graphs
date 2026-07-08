#!/bin/bash
#SBATCH --job-name=ea_exact
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=250G
#SBATCH --time=01:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_exact_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_exact_%j.err

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/candidates

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/generate_exact_label_candidates.py \
  --yago /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/labels/yago_labels_norm.tsv \
  --semopenalex /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/labels/semopenalex_labels_norm.tsv \
  --out /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/candidates/exact_label_candidates.tsv \
  --stats-out /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/candidates/exact_label_candidate_stats.tsv \
  --max-label-freq 1000
