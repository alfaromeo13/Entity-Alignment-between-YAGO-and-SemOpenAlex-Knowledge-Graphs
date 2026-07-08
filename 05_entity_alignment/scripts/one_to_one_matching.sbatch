#!/bin/bash
#SBATCH --job-name=ea_1to1
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=30G
#SBATCH --time=00:15:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_1to1_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_1to1_%j.err

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/one_to_one_matching.py \
  --input /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/alignments_threshold030_typefiltered.tsv \
  --output /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/final/alignments_threshold030_typefiltered_1to1.tsv