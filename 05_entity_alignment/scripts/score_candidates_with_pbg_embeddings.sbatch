#!/bin/bash
#SBATCH --job-name=ea_emb_score
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=40G
#SBATCH --time=2-20:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_emb_score_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/logs/ea_emb_score_%j.err

module purge
module load release/23.04
module load GCCcore/10.2.0
module load Python/3.8.6
source /data/horse/ws/jovu353i-kgalign/venvs/pbg/bin/activate

python /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/scripts/score_candidates_with_pbg_embeddings.py \
  --candidates /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/data/candidates/exact_label_candidates_ambiguous_with_ids.tsv \
  --yago-emb /data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/output/yago/distmult_dot \
  --soa-emb /data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/output/semopenalex/distmult_dot \
  --yago-partitions 32 \
  --soa-partitions 128 \
  --out-scored /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/scores/ambiguous_distmult_embedding_scored.tsv \
  --out-top1 /data/horse/ws/jovu353i-kgalign/KGAlignment/05_entity_alignment/outputs/rankings/ambiguous_distmult_top1.tsv