#!/bin/bash
set -euo pipefail

RAW_DIR="/data/horse/ws/jovu353i-kgalign/KGAlignment/01_raw/semopenalex"
MANIFEST="/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/manifests/semopenalex_full_manifest.txt"

mkdir -p "$(dirname "$MANIFEST")"

find "$RAW_DIR" -type f -name "*.trig.gz" | sort > "$MANIFEST"

wc -l "$MANIFEST" >&2
echo "$MANIFEST"