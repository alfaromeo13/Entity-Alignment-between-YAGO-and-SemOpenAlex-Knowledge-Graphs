#!/bin/bash
#SBATCH --job-name=ea_filter_exact
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=5G
#SBATCH --time=00:50:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_filter_exact_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_filter_exact_%j.err

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/filter_exact_label_candidates.py \
  --input /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/candidates/exact_label_candidates.tsv \
  --output /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/candidates/exact_label_candidates_filtered.tsv \
  --max-freq 50 \
  --min-chars 5 \
  --min-tokens 2
