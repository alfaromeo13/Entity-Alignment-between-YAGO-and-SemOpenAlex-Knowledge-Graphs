#!/bin/bash
#SBATCH --job-name=ea_filter_merge
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=10G
#SBATCH --time=00:05:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_filter_merge_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_filter_merge_%j.err

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/filter_and_merge_alignments.py \
  --proxy-gold /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/gold/proxy_gold_exact_unique.tsv \
  --top1 /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/rankings/ambiguous_distmult_top1.tsv \
  --out /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/alignments_threshold030_typefiltered.tsv \
  --threshold 0.30
