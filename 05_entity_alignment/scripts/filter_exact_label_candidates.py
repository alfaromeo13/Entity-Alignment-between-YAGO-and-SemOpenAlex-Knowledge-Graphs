#!/usr/bin/env python3
import argparse
import csv

GENERIC_LABELS = {
    "film", "taxon", "company", "protein", "flag", "article", "study",
    "journal", "book", "city", "village", "town", "province", "state",
    "country", "school", "university", "hospital", "church", "station",
    "river", "lake", "mountain", "album", "song", "single", "game",
    "football", "club", "team", "politician", "writer", "artist",
    "actor", "actress", "author", "researcher", "professor",
    "introduction", "unknown", "none", "null", "na"
}

def token_count(s):
    return len(s.split())

def keep(row, max_freq, min_chars, min_tokens):
    nl = row["norm_label"].strip()
    freq = int(row["semopenalex_label_freq"])

    if freq > max_freq:
        return False
    if len(nl) < min_chars:
        return False
    if token_count(nl) < min_tokens:
        return False
    if nl in GENERIC_LABELS:
        return False
    if nl.isdigit():
        return False

    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-freq", type=int, default=50)
    ap.add_argument("--min-chars", type=int, default=5)
    ap.add_argument("--min-tokens", type=int, default=2)
    ap.add_argument("--progress-every", type=int, default=5_000_000)
    args = ap.parse_args()

    seen = 0
    kept = 0

    with open(args.input, encoding="utf-8") as f, \
         open(args.output, "w", encoding="utf-8", newline="") as out:

        r = csv.DictReader(f, delimiter="\t")
        w = csv.DictWriter(out, fieldnames=r.fieldnames, delimiter="\t")
        w.writeheader()

        for row in r:
            seen += 1
            if keep(row, args.max_freq, args.min_chars, args.min_tokens):
                w.writerow(row)
                kept += 1

            if seen % args.progress_every == 0:
                print(f"processed={seen:,} kept={kept:,}", flush=True)

    print(f"Finished. Processed={seen:,} Kept={kept:,}")
    print(f"Wrote: {args.output}")

if __name__ == "__main__":
    main()
