#!/bin/bash
#SBATCH --job-name=soa_pass3
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=10G
#SBATCH --time=00:15:00
#SBATCH --array=0-9%4
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/logs/soa_pass3_%A_%a.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/logs/soa_pass3_%A_%a.err

set -euo pipefail

module purge
module load release/2026
module load GCCcore/14.3.0
module load Python/3.13.5
module load Java/21.0.8
export PATH=$HOME/apache-jena-6.0.0/bin:$PATH

MANIFEST="/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/manifests/semopenalex_pass3_manifest.txt"
PYTHON_SCRIPT="/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/scripts/preprocess_structural_stream.py"
SANITIZER_SCRIPT="/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/scripts/sanitize_trig_stream_pass3.py"
RUN_ONE="/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/scripts/run_semopenalex_one_file.sh"
BASE_OUT="/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/semopenalex_pass3_shards"

mkdir -p "$BASE_OUT"
mkdir -p /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/logs

INPUT_FILE="$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$MANIFEST")"

if [ -z "${INPUT_FILE:-}" ]; then
  echo "No input file for task ${SLURM_ARRAY_TASK_ID}" >&2
  exit 1
fi

SHARD_NAME="$(basename "$INPUT_FILE" .trig.gz)"
SHARD_OUT_DIR="${BASE_OUT}/${SHARD_NAME}"

echo "[+] PASS3 TASK ${SLURM_ARRAY_TASK_ID} processing ${INPUT_FILE}" >&2

"$RUN_ONE" "$INPUT_FILE" "$SHARD_OUT_DIR" "$PYTHON_SCRIPT" "$SANITIZER_SCRIPT"
