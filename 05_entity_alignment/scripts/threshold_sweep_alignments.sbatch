#!/bin/bash
#SBATCH --job-name=ea_thresh_sweep
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=20G
#SBATCH --time=00:05:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_thresh_sweep_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_thresh_sweep_%j.err

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/threshold_sweep_alignments.py \
  --top1 /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/rankings/ambiguous_distmult_top1.tsv \
  --out-summary /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/threshold_sweep_summary.tsv \
  --thresholds 0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.55,0.60
