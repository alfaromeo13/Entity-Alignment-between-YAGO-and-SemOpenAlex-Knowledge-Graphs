#!/usr/bin/env python3
import argparse
import csv
from collections import defaultdict

def load_semopenalex(path):
    by_label = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            nl = row["norm_label"]
            if nl:
                by_label[nl].append((row["entity"], row["label"]))
    return by_label

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yago", required=True)
    ap.add_argument("--semopenalex", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stats-out", required=True)
    ap.add_argument("--max-label-freq", type=int, default=1000,
                    help="Skip only labels that would create huge meaningless explosions.")
    args = ap.parse_args()

    print("Loading SemOpenAlex labels...", flush=True)
    soa = load_semopenalex(args.semopenalex)
    print(f"Loaded normalized SemOpenAlex labels: {len(soa):,}", flush=True)

    total_pairs = 0
    skipped_labels = 0

    with open(args.out, "w", encoding="utf-8", newline="") as out, \
         open(args.stats_out, "w", encoding="utf-8", newline="") as stats, \
         open(args.yago, encoding="utf-8") as yf:

        w = csv.writer(out, delimiter="\t")
        sw = csv.writer(stats, delimiter="\t")

        w.writerow(["yago_entity", "semopenalex_entity", "norm_label", "yago_label", "semopenalex_label", "semopenalex_label_freq"])
        sw.writerow(["norm_label", "semopenalex_freq", "status"])

        yr = csv.DictReader(yf, delimiter="\t")

        for i, yrow in enumerate(yr, 1):
            nl = yrow["norm_label"]
            if not nl or nl not in soa:
                continue

            matches = soa[nl]
            freq = len(matches)

            if freq > args.max_label_freq:
                skipped_labels += 1
                sw.writerow([nl, freq, "skipped_too_frequent"])
                continue

            sw.writerow([nl, freq, "used"])

            for sent, slabel in matches:
                w.writerow([yrow["entity"], sent, nl, yrow["label"], slabel, freq])
                total_pairs += 1

            if i % 5_000_000 == 0:
                print(f"Processed YAGO rows={i:,} | candidate_pairs={total_pairs:,}", flush=True)

    print(f"Finished. Candidate pairs: {total_pairs:,}", flush=True)
    print(f"Skipped high-frequency labels: {skipped_labels:,}", flush=True)
    print(f"Wrote: {args.out}", flush=True)
    print(f"Wrote stats: {args.stats_out}", flush=True)

if __name__ == "__main__":
    main()
