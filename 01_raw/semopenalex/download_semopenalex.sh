#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ONTOLOGY_URL=https://raw.githubusercontent.com/metaphacts/semopenalex/main/ontologies/semopenalex-ontology.ttl
ONTOLOGY_PATH=$SCRIPT_DIR/semopenalex-ontology.ttl
ONTOLOGY_TMP=$ONTOLOGY_PATH.tmp

cleanup() {
  rm -f "$ONTOLOGY_TMP"
}
trap cleanup EXIT

echo "Starting SemOpenAlex downloads..."

echo "Downloading official SemOpenAlex ontology..."
curl --fail --location --retry 3 \
  "$ONTOLOGY_URL" \
  --output "$ONTOLOGY_TMP"
mv "$ONTOLOGY_TMP" "$ONTOLOGY_PATH"
echo "Finished ontology: $ONTOLOGY_PATH"

folders=(
  authors
  concepts
  domains
  fields
  funders
  institutions
  keywords
  publishers
  sources
  subfields
  topics
  works
)

for f in "${folders[@]}"; do
  echo "Downloading folder: $f"
  aws s3 sync --no-sign-request "s3://semopenalex/$f/" "$SCRIPT_DIR/$f/"
  echo "Finished: $f"
done

echo "All downloads completed!"
