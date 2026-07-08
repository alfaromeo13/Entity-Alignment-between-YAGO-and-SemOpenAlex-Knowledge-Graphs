#!/usr/bin/env python3
import argparse
import csv
from collections import Counter

BAD_PAIRS = {
    ("place_like", "author"),
    ("place_like", "work"),
    ("place_like", "concept"),
    ("place_like", "source"),
    ("creative_work_like", "author"),
    ("creative_work_like", "institution"),
    ("person_like", "work"),
    ("person_like", "institution"),
    ("person_like", "source"),
    ("person_like", "publisher"),
    ("person_like", "concept"),
    ("organization_like", "author"),
    ("organization_like", "work"),
    ("event_like", "author"),
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--rejected", required=True)
    ap.add_argument("--summary", required=True)
    args = ap.parse_args()

    kept = 0
    rejected = 0
    pair_counts = Counter()
    reject_counts = Counter()

    with open(args.input, encoding="utf-8") as f, \
         open(args.output, "w", encoding="utf-8", newline="") as out, \
         open(args.rejected, "w", encoding="utf-8", newline="") as rej:

        r = csv.DictReader(f, delimiter="\t")
        w = csv.DictWriter(out, fieldnames=r.fieldnames, delimiter="\t")
        rw = csv.DictWriter(rej, fieldnames=r.fieldnames, delimiter="\t")
        w.writeheader()
        rw.writeheader()

        for row in r:
            yt = row["yago_profile_type"]
            st = row["semopenalex_uri_type"]
            pair_counts[(yt, st)] += 1

            if (yt, st) in BAD_PAIRS:
                rw.writerow(row)
                rejected += 1
                reject_counts[(yt, st)] += 1
            else:
                w.writerow(row)
                kept += 1

    with open(args.summary, "w", encoding="utf-8", newline="") as out:
        sw = csv.writer(out, delimiter="\t")
        sw.writerow(["metric", "value"])
        sw.writerow(["kept", kept])
        sw.writerow(["rejected", rejected])
        sw.writerow([])
        sw.writerow(["rejected_yago_profile_type", "rejected_semopenalex_type", "count"])
        for (yt, st), c in reject_counts.most_common():
            sw.writerow([yt, st, c])

    print(f"Kept: {kept:,}")
    print(f"Rejected: {rejected:,}")
    print(f"Wrote: {args.output}")
    print(f"Wrote rejected: {args.rejected}")
    print(f"Wrote summary: {args.summary}")

if __name__ == "__main__":
    main()
