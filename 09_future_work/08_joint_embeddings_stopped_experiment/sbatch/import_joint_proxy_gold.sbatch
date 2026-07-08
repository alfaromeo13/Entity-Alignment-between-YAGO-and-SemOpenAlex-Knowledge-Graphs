#!/bin/bash
#SBATCH --job-name=joint_import
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=300G
#SBATCH --time=2-00:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/logs/joint_import_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/logs/joint_import_%j.err

set -euo pipefail

cd /data/horse/ws/jovu353i-kgalign/KGAlignment
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

rm -rf 08_joint_embeddings/data/imported
mkdir -p 08_joint_embeddings/data/imported

torchbiggraph_import_from_tsv \
  --lhs-col 0 \
  --rel-col 1 \
  --rhs-col 2 \
  08_joint_embeddings/configs/joint_proxy_gold_distmult.py \
  08_joint_embeddings/data/edges/joint_proxy_gold_edges.tsv
