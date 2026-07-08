#!/bin/bash
#SBATCH --job-name=typev2_visuals
#SBATCH --partition=barnard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --time=12:00:00
#SBATCH --chdir=/data/horse/ws/jovu353i-kgalign/KGAlignment
#SBATCH --output=/data/horse/ws/jovu353i-kgalign/KGAlignment/07_export/logs/visualizations_%j.out
#SBATCH --error=/data/horse/ws/jovu353i-kgalign/KGAlignment/07_export/logs/visualizations_%j.err

set -euo pipefail

ROOT=/data/horse/ws/jovu353i-kgalign/KGAlignment
export MPLCONFIGDIR="${TMPDIR:-/tmp}/kgalign-matplotlib-${SLURM_JOB_ID:-local}"
mkdir -p "$MPLCONFIGDIR"

"$ROOT/07_export/.venv/bin/python" \
  "$ROOT/07_export/scripts/generate_all_visualizations.py" --refresh
