#!/bin/bash
set -euo pipefail

SHARDS_DIR="/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/semopenalex_shards"
MANIFEST="/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/manifests/semopenalex_failed_manifest.txt"

mkdir -p "$(dirname "$MANIFEST")"

find "$SHARDS_DIR" -name FAILED | sort | while read -r f; do
  d="$(dirname "$f")"
  cat "$d/source_file.txt"
done > "$MANIFEST"

wc -l "$MANIFEST" >&2
echo "$MANIFEST"