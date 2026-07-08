#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

def append_file(src: Path, dst_handle, skip_header: bool = False):
    with src.open("r", encoding="utf-8") as f:
        first = True
        for line in f:
            if skip_header and first:
                first = False
                continue
            first = False
            dst_handle.write(line)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    shards_dir = Path(args.shards_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    shard_dirs = sorted([p for p in shards_dir.iterdir() if p.is_dir()])

    train_out = out_dir / "train.tsv"
    valid_out = out_dir / "valid.tsv"
    test_out = out_dir / "test.tsv"
    text_out = out_dir / "entity_text_raw.tsv"
    summary_out = out_dir / "merge_summary.json"
    failed_manifest = out_dir / "failed_shards.txt"
    success_manifest = out_dir / "successful_shards.txt"

    merged_stats = {
        "successful_shards": 0,
        "failed_shards": 0,
        "structural_triples_kept": 0,
        "text_literal_rows_written": 0,
        "filtered_subject_triples": 0,
        "skipped_helper_structural_triples": 0,
        "non_structural_triples_seen": 0,
        "malformed_lines": 0,
    }

    with train_out.open("w", encoding="utf-8") as f_train, \
         valid_out.open("w", encoding="utf-8") as f_valid, \
         test_out.open("w", encoding="utf-8") as f_test, \
         text_out.open("w", encoding="utf-8") as f_text, \
         failed_manifest.open("w", encoding="utf-8") as f_failed, \
         success_manifest.open("w", encoding="utf-8") as f_success:

        f_text.write("entity\tpredicate\ttext\n")

        for shard in shard_dirs:
            if (shard / "SUCCESS").exists():
                f_success.write(str(shard) + "\n")
                merged_stats["successful_shards"] += 1

                append_file(shard / "train.tsv", f_train)
                append_file(shard / "valid.tsv", f_valid)
                append_file(shard / "test.tsv", f_test)
                append_file(shard / "entity_text_raw.tsv", f_text, skip_header=True)

                with (shard / "stats.json").open("r", encoding="utf-8") as f:
                    s = json.load(f)

                merged_stats["structural_triples_kept"] += s.get("structural_triples_kept", 0)
                merged_stats["text_literal_rows_written"] += s.get("text_literal_rows_written", 0)
                merged_stats["filtered_subject_triples"] += s.get("filtered_subject_triples", 0)
                merged_stats["skipped_helper_structural_triples"] += s.get("skipped_helper_structural_triples", 0)
                merged_stats["non_structural_triples_seen"] += s.get("non_structural_triples_seen", 0)
                merged_stats["malformed_lines"] += s.get("malformed_lines", 0)

            else:
                f_failed.write(str(shard) + "\n")
                merged_stats["failed_shards"] += 1

    with summary_out.open("w", encoding="utf-8") as f:
        json.dump(merged_stats, f, indent=2)

    print(json.dumps(merged_stats, indent=2))

if __name__ == "__main__":
    main()