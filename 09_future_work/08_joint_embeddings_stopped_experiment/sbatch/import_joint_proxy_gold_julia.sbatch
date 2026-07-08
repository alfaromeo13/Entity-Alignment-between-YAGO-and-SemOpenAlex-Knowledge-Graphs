#!/bin/bash
#SBATCH --job-name=joint_import
#SBATCH --partition=julia
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=4T
#SBATCH --time=2-00:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/logs/joint_import_julia_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/logs/joint_import_julia_%j.err

set -euo pipefail

module --force purge
module load release/24.04
module load Python/3.8.6

cd /data/horse/ws/jovu353i-kgalign/KGAlignment
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

export LD_LIBRARY_PATH="$(python -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR"))'):${LD_LIBRARY_PATH:-}"
export PYTHONNOUSERSITE=1

rm -rf 08_joint_embeddings/data/imported
mkdir -p 08_joint_embeddings/data/imported

torchbiggraph_import_from_tsv \
  --lhs-col 0 \
  --rel-col 1 \
  --rhs-col 2 \
  08_joint_embeddings/configs/joint_proxy_gold_distmult_p16.py \
  08_joint_embeddings/data/edges/joint_proxy_gold_edges.tsv
