#!/bin/bash
#SBATCH --job-name=joint_prep
#SBATCH --partition=julia
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=2T
#SBATCH --time=1-00:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/logs/joint_prep_julia_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/logs/joint_prep_julia_%j.err

set -euo pipefail

module --force purge
module load release/24.04
module load GCCcore/11.3.0
module load Python/3.10.4

cd /data/horse/ws/jovu353i-kgalign/KGAlignment
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

export LD_LIBRARY_PATH="$(python -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR"))'):${LD_LIBRARY_PATH:-}"
export PYTHONNOUSERSITE=1

echo "Python:"
which python
python --version

YAGO_EDGES="/data/horse/ws/jovu353i-kgalign/KGAlignment/03_dglke/yago/train.tsv"
SEM_EDGES="/data/horse/ws/jovu353i-kgalign/KGAlignment/03_dglke/semopenalex_julia/train.tsv"
YAGO_DICT="/data/horse/ws/jovu353i-kgalign/KGAlignment/03_dglke/yago/entities.dict"
SEM_DICT="/data/horse/ws/jovu353i-kgalign/KGAlignment/03_dglke/semopenalex_julia/entities.dict"
PROXY_GOLD="/data/horse/ws/jovu353i-kgalign/KGAlignment/06_entity_alignment/data/gold/proxy_gold_exact_unique.tsv"

rm -f 08_joint_embeddings/data/edges/yago_joint_edges.tsv
rm -f 08_joint_embeddings/data/edges/semopenalex_joint_edges.tsv
rm -f 08_joint_embeddings/data/seeds/proxy_gold_seed_edges.tsv
rm -f 08_joint_embeddings/data/edges/joint_proxy_gold_edges.tsv

python 08_joint_embeddings/scripts/prefix_edges.py \
  --input "$YAGO_EDGES" \
  --out 08_joint_embeddings/data/edges/yago_joint_edges.tsv \
  --entity-prefix "yago" \
  --rel-prefix "yago_rel"

python 08_joint_embeddings/scripts/prefix_edges.py \
  --input "$SEM_EDGES" \
  --out 08_joint_embeddings/data/edges/semopenalex_joint_edges.tsv \
  --entity-prefix "sem" \
  --rel-prefix "sem_rel"

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

echo "Line counts:"
wc -l 08_joint_embeddings/data/edges/yago_joint_edges.tsv
wc -l 08_joint_embeddings/data/edges/semopenalex_joint_edges.tsv
wc -l 08_joint_embeddings/data/seeds/proxy_gold_seed_edges.tsv
wc -l 08_joint_embeddings/data/edges/joint_proxy_gold_edges.tsv

echo "Head:"
head -5 08_joint_embeddings/data/edges/joint_proxy_gold_edges.tsv

echo "Tail:"
tail -5 08_joint_embeddings/data/edges/joint_proxy_gold_edges.tsv

echo "Done joint preparation."
