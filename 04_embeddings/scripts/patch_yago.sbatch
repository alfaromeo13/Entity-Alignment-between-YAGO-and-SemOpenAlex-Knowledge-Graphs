#!/bin/bash
#SBATCH --job-name=pbg_patch_yago
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=30G
#SBATCH --time=00:10:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/logs/patch_yago_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/logs/patch_yago_%j.err

set -euo pipefail

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6

source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

python /data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/scripts/patch_pbg_ids.py \
  --edge-dir /data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/input/yago \
  --num-partitions 32
