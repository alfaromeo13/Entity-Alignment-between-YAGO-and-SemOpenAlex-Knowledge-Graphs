#!/bin/bash
#SBATCH --job-name=joint_import_p8
#SBATCH --partition=julia
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=6T
#SBATCH --time=5-00:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/logs/joint_import_p8_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/logs/joint_import_p8_%j.err

set -euo pipefail

module --force purge
module load release/24.04
module load GCCcore/11.3.0
module load Python/3.10.4

cd /data/horse/ws/jovu353i-kgalign/KGAlignment
source /data/horse/ws/jovu353i-kgalign/venvs/pbg_julia/bin/activate

export LD_LIBRARY_PATH="/data/horse/ws/jovu353i-kgalign/venvs/pbg_julia/lib:${LD_LIBRARY_PATH:-}"
export PYTHONNOUSERSITE=1

which python
python --version
python -c "import sys; print(sys.executable)"
python -c "import torchbiggraph; print('torchbiggraph ok')"

rm -rf 08_joint_embeddings/data/imported_p8
mkdir -p 08_joint_embeddings/data/imported_p8

torchbiggraph_import_from_tsv \
  --lhs-col 0 \
  --rel-col 1 \
  --rhs-col 2 \
  08_joint_embeddings/configs/joint_distmult_p8.py \
  08_joint_embeddings/data/edges/joint_proxy_gold_edges.tsv
