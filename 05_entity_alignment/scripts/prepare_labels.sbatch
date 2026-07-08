#!/bin/bash
#SBATCH --job-name=ea_labels
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=100G
#SBATCH --time=10:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_labels_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_labels_%j.err

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/labels
mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/prepare_entity_labels.py \
  --input /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/yago/entity_text_raw.tsv \
  --output /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/labels/yago_labels.tsv

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/prepare_entity_labels.py \
  --input /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/semopenalex_clean/entity_text_raw.tsv \
  --output /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/labels/semopenalex_labels.tsv