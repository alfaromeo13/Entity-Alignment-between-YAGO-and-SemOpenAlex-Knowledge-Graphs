#!/usr/bin/env python3
import argparse
import csv
import re

def clean_text(text):
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text

def is_latinish(text):
    if not text:
        return False
    good = sum(
        1 for c in text
        if c.isascii() and (c.isalpha() or c.isdigit() or c.isspace() or c in ".,'’()-&:/")
    )
    return good / max(len(text), 1) > 0.8

def better_label(new, old):
    if old is None:
        return True

    # Prefer shorter clean labels, usually better for names/titles.
    if len(new) < len(old):
        return True
    if len(new) == len(old) and new < old:
        return True
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--progress-every", type=int, default=5_000_000)
    args = ap.parse_args()

    best = {}
    rows = 0
    kept = 0

    with open(args.input, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            rows += 1

            try:
                ent = row["entity"].strip()
                text = clean_text(row["text"])
            except Exception:
                continue

            if not ent or not text:
                continue
            if not is_latinish(text):
                continue

            old = best.get(ent)
            if better_label(text, old):
                best[ent] = text

            kept += 1

            if rows % args.progress_every == 0:
                print(f"Processed rows: {rows:,} | kept text rows: {kept:,} | unique entities: {len(best):,}", flush=True)

    with open(args.output, "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out, delimiter="\t")
        writer.writerow(["entity", "label"])
        for ent, label in best.items():
            writer.writerow([ent, label])

    print(f"Finished: {args.input}")
    print(f"Rows processed: {rows:,}")
    print(f"Kept text rows: {kept:,}")
    print(f"Unique entities written: {len(best):,}")
    print(f"Wrote: {args.output}")

if __name__ == "__main__":
    main()
