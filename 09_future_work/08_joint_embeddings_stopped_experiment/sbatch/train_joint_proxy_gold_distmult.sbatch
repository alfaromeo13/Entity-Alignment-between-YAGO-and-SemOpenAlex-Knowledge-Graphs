#!/bin/bash
#SBATCH --job-name=joint_dmult
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=380G
#SBATCH --time=7-00:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/logs/joint_distmult_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/logs/joint_distmult_%j.err

set -euo pipefail

cd /data/horse/ws/jovu353i-kgalign/KGAlignment
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

torchbiggraph_train 08_joint_embeddings/configs/joint_proxy_gold_distmult.py
