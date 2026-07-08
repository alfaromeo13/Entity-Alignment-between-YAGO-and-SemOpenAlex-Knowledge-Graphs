#!/bin/bash
set -euo pipefail

RAW_DIR="$1"
OUT_DIR="$2"
PYTHON_SCRIPT="$3"

mkdir -p "$OUT_DIR"

find "$RAW_DIR" -type f -name "*.ttl" | sort | while read -r f; do
  echo "[+] Converting $f" >&2
  riot --syntax=turtle --output=ntriples "$f"
done | python3 -u "$PYTHON_SCRIPT" \
      --output-dir "$OUT_DIR" \
      --dataset-name yago