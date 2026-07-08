#!/bin/bash
#SBATCH --job-name=pbg_train_soa
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=200G
#SBATCH --time=7-00:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/logs/%x_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/logs/%x_%j.err

set -euo pipefail

if [ -z "${PBG_CONFIG:-}" ]; then
  echo "PBG_CONFIG is not set"
  exit 1
fi

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

torchbiggraph_train "$PBG_CONFIG"
