#!/bin/bash
#SBATCH --job-name=ea_norm_labels
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=20G
#SBATCH --time=02:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_norm_labels_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_norm_labels_%j.err

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/normalize_labels.py \
  --input /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/labels/yago_labels.tsv \
  --output /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/labels/yago_labels_norm.tsv

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/normalize_labels.py \
  --input /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/labels/semopenalex_labels.tsv \
  --output /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/labels/semopenalex_labels_norm.tsv
