#!/bin/bash
#SBATCH --job-name=yago_pre
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=20G
#SBATCH --time=08:00:00
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/logs/yago_pre_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/logs/yago_pre_%j.err

set -euo pipefail

module load Java/21.0.8
export PATH=$HOME/apache-jena-6.0.0/bin:$PATH

BASE=/data/horse/ws/jovu353i-kgalign/KGAlignment
RAW=$BASE/01_raw/yago
OUT=$BASE/02_preprocessed/yago
PY=$BASE/02_preprocessed/scripts/preprocess_structural_stream.py
SH=$BASE/02_preprocessed/scripts/run_yago_preprocess.sh

bash "$SH" "$RAW" "$OUT" "$PY"
