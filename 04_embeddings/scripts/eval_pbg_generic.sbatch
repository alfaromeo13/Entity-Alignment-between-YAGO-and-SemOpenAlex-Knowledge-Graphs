#!/bin/bash
#SBATCH --job-name=pbg_eval
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=100G
#SBATCH --time=4-00:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/logs/%x_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/logs/%x_%j.err

set -euo pipefail

if [ -z "${PBG_EVAL_CONFIG:-}" ]; then
  echo "PBG_EVAL_CONFIG is not set"
  exit 1
fi

if [ -z "${PBG_EVAL_TXT:-}" ]; then
  echo "PBG_EVAL_TXT is not set"
  exit 1
fi

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

mkdir -p "$(dirname "$PBG_EVAL_TXT")"

torchbiggraph_eval "$PBG_EVAL_CONFIG" | tee "$PBG_EVAL_TXT"
