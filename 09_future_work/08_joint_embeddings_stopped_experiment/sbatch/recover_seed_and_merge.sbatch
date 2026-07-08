#!/bin/bash
#SBATCH --job-name=joint_recover
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=80G
#SBATCH --time=12:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/logs/joint_recover_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/logs/joint_recover_%j.err

set -euo pipefail

module --force purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6

cd /data/horse/ws/jovu353i-kgalign/KGAlignment
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

export LD_LIBRARY_PATH="$(python -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR"))'):${LD_LIBRARY_PATH:-}"
export PYTHONNOUSERSITE=1

YAGO_DICT="/data/horse/ws/jovu353i-kgalign/KGAlignment/03_dglke/yago/entities.dict"
SEM_DICT="/data/horse/ws/jovu353i-kgalign/KGAlignment/03_dglke/semopenalex_julia/entities.dict"
PROXY_GOLD="/data/horse/ws/jovu353i-kgalign/KGAlignment/06_entity_alignment/data/gold/proxy_gold_exact_unique.tsv"

test -s 08_joint_embeddings/data/edges/yago_joint_edges.tsv
test -s 08_joint_embeddings/data/edges/semopenalex_joint_edges.tsv

python 08_joint_embeddings/scripts/build_proxy_seed_edges.py \
  --proxy-gold "$PROXY_GOLD" \
  --yago-dict "$YAGO_DICT" \
  --sem-dict "$SEM_DICT" \
  --out 08_joint_embeddings/data/seeds/proxy_gold_seed_edges.tsv \
  --relation "seed_aligned_with"

cat \
  08_joint_embeddings/data/edges/yago_joint_edges.tsv \
  08_joint_embeddings/data/edges/semopenalex_joint_edges.tsv \
  08_joint_embeddings/data/seeds/proxy_gold_seed_edges.tsv \
  > 08_joint_embeddings/data/edges/joint_proxy_gold_edges.tsv

wc -l 08_joint_embeddings/data/edges/yago_joint_edges.tsv
wc -l 08_joint_embeddings/data/edges/semopenalex_joint_edges.tsv
wc -l 08_joint_embeddings/data/seeds/proxy_gold_seed_edges.tsv
wc -l 08_joint_embeddings/data/edges/joint_proxy_gold_edges.tsv

head -5 08_joint_embeddings/data/edges/joint_proxy_gold_edges.tsv
tail -5 08_joint_embeddings/data/edges/joint_proxy_gold_edges.tsv
