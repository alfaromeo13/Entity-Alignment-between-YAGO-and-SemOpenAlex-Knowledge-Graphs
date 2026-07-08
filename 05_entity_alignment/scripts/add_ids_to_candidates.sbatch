#!/bin/bash
#SBATCH --job-name=ea_add_ids
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=20G
#SBATCH --time=01:10:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_add_ids_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_add_ids_%j.err

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs
mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/candidates

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/add_ids_to_candidates.py \
  --candidates /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/candidates/exact_label_candidates_ambiguous.tsv \
  --yago-dict /data/horse/ws/jovu353i-kgalign/KGAlignment/03_integer_encoding/yago/entities.dict \
  --soa-dict /data/horse/ws/jovu353i-kgalign/KGAlignment/03_integer_encoding/semopenalex/entities.dict \
  --output /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/candidates/exact_label_candidates_ambiguous_with_ids.tsv