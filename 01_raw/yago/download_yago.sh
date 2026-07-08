#!/bin/bash
set -euo pipefail

# Download and unpack YAGO 4.5 into this folder.
# Default source:
#   https://yago-knowledge.org/data/yago4.5/yago-4.5.0.2.zip

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BASE_URL=https://yago-knowledge.org/data/yago4.5
YAGO_ARCHIVE=${YAGO_ARCHIVE:-yago-4.5.0.2.zip}
ZIP_PATH="$SCRIPT_DIR/$YAGO_ARCHIVE"

cd "$SCRIPT_DIR"

if [[ -e yago-facts.ttl || -e yago-beyond-wikipedia.ttl || -e yago-schema.ttl || -e yago-taxonomy.ttl ]]; then
  echo "YAGO files already exist in $SCRIPT_DIR"
  echo "Not overwriting them. Use an empty folder if you want to test another archive."
  exit 0
fi

echo "Downloading $BASE_URL/$YAGO_ARCHIVE"
curl --fail --location --retry 5 --continue-at - \
  --output "$ZIP_PATH" \
  "$BASE_URL/$YAGO_ARCHIVE"

unzip -j "$ZIP_PATH" "*.ttl" "*.ntx" -d "$SCRIPT_DIR"
rm -f "$ZIP_PATH"

echo "YAGO download completed. Files:"
ls -lh yago-*.ttl yago-*.ntx 2>/dev/null || true
