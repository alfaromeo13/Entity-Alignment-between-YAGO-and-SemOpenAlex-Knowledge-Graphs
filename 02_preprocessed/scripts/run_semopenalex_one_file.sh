#!/bin/bash
set -euo pipefail

INPUT_FILE="$1"
SHARD_OUT_DIR="$2"
PYTHON_SCRIPT="$3"
SANITIZER_SCRIPT="$4"

mkdir -p "$SHARD_OUT_DIR"
TMP_DIR="${SHARD_OUT_DIR}/_tmp"
mkdir -p "$TMP_DIR"

RAW_BASENAME="$(basename "$INPUT_FILE")"
echo "$INPUT_FILE" > "$SHARD_OUT_DIR/source_file.txt"

rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
rm -f "$SHARD_OUT_DIR"/SUCCESS "$SHARD_OUT_DIR"/FAILED

if pigz -dc "$INPUT_FILE" \
    | python3 -u "$SANITIZER_SCRIPT" --log-json "$SHARD_OUT_DIR/sanitizer_dropped.jsonl" \
         >"$SHARD_OUT_DIR/sanitized.trig" 2>"$SHARD_OUT_DIR/sanitizer_stderr.log"
then
    :
else
    touch "$SHARD_OUT_DIR/FAILED"
    echo "[!] SANITIZER FAILED $RAW_BASENAME" >&2
    exit 1
fi

if riot --syntax=trig --output=nquads "$SHARD_OUT_DIR/sanitized.trig" 2>"$SHARD_OUT_DIR/riot_warnings.log" \
    | python3 -u "$PYTHON_SCRIPT" --output-dir "$TMP_DIR" --dataset-name semopenalex --progress-every 0 \
         >"$SHARD_OUT_DIR/python_stdout.log" 2>"$SHARD_OUT_DIR/python_stderr.log"
then
    mv "$TMP_DIR/train.tsv" "$SHARD_OUT_DIR/train.tsv"
    mv "$TMP_DIR/valid.tsv" "$SHARD_OUT_DIR/valid.tsv"
    mv "$TMP_DIR/test.tsv" "$SHARD_OUT_DIR/test.tsv"
    mv "$TMP_DIR/entity_text_raw.tsv" "$SHARD_OUT_DIR/entity_text_raw.tsv"
    mv "$TMP_DIR/stats.json" "$SHARD_OUT_DIR/stats.json"
    rm -rf "$TMP_DIR"
    touch "$SHARD_OUT_DIR/SUCCESS"
else
    rm -rf "$TMP_DIR"
    rm -f "$SHARD_OUT_DIR/train.tsv" "$SHARD_OUT_DIR/valid.tsv" "$SHARD_OUT_DIR/test.tsv" \
          "$SHARD_OUT_DIR/entity_text_raw.tsv" "$SHARD_OUT_DIR/stats.json"
    touch "$SHARD_OUT_DIR/FAILED"
    echo "[!] FAILED $RAW_BASENAME" >&2
    exit 1
fi