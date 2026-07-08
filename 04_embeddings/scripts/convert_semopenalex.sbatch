#!/bin/bash
#SBATCH --job-name=pbg_convert
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=256G
#SBATCH --time=10:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/logs/convert_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/logs/convert_%j.err

set -euo pipefail

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6

source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

python /data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/scripts/convert_to_pbg.py \
  --input /data/horse/ws/jovu353i-kgalign/KGAlignment/03_integer_encoding/semopenalex/train.tsv \
  --out /data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/input/semopenalex \
  --entities 1936550634 \
  --partitions 128
