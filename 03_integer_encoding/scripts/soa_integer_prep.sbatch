#!/bin/bash
#SBATCH --job-name=soa_integer_prep
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=500G
#SBATCH --time=20:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/03_integer_encoding/logs/soa_integer_prep_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/03_integer_encoding/logs/soa_integer_prep_%j.err

set -euo pipefail

module --force purge
module load release/24.04 GCCcore/13.2.0 Python/3.11.5

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK

mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/03_integer_encoding/logs

python3 /data/horse/ws/jovu353i-kgalign/KGAlignment/03_integer_encoding/scripts/prepare_integer_dataset.py \
  --input-dir /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/semopenalex_clean \
  --output-dir /data/horse/ws/jovu353i-kgalign/KGAlignment/03_integer_encoding/semopenalex \
  --dataset-name semopenalex