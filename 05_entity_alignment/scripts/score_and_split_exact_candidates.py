#!/usr/bin/env python3
import argparse
import csv
from collections import Counter

def token_jaccard(a, b):
    sa, sb = set(a.lower().split()), set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-scored", required=True)
    ap.add_argument("--out-proxy-gold", required=True)
    ap.add_argument("--out-ambiguous", required=True)
    ap.add_argument("--progress-every", type=int, default=5_000_000)
    args = ap.parse_args()

    print("Pass 1: counting candidates per YAGO entity...", flush=True)
    yago_counts = Counter()
    rows = 0

    with open(args.input, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            rows += 1
            yago_counts[row["yago_entity"]] += 1
            if rows % args.progress_every == 0:
                print(f"counted rows={rows:,} unique_yago={len(yago_counts):,}", flush=True)

    print(f"Finished counting: rows={rows:,}, unique_yago={len(yago_counts):,}", flush=True)

    print("Pass 2: scoring and splitting...", flush=True)
    kept_proxy = 0
    kept_ambiguous = 0
    written = 0

    with open(args.input, encoding="utf-8") as f, \
         open(args.out_scored, "w", encoding="utf-8", newline="") as scored, \
         open(args.out_proxy_gold, "w", encoding="utf-8", newline="") as gold, \
         open(args.out_ambiguous, "w", encoding="utf-8", newline="") as amb:

        r = csv.DictReader(f, delimiter="\t")

        fieldnames = r.fieldnames + [
            "yago_candidate_count",
            "token_jaccard",
            "label_length_diff",
            "confidence_tier"
        ]

        sw = csv.DictWriter(scored, fieldnames=fieldnames, delimiter="\t")
        gw = csv.DictWriter(gold, fieldnames=fieldnames, delimiter="\t")
        aw = csv.DictWriter(amb, fieldnames=fieldnames, delimiter="\t")

        sw.writeheader()
        gw.writeheader()
        aw.writeheader()

        for row in r:
            ycnt = yago_counts[row["yago_entity"]]
            sfreq = int(row["semopenalex_label_freq"])

            tj = token_jaccard(row["yago_label"], row["semopenalex_label"])
            ldiff = abs(len(row["yago_label"]) - len(row["semopenalex_label"]))

            if ycnt == 1 and sfreq == 1:
                tier = "strict_proxy_gold"
            elif ycnt <= 5 and sfreq <= 5:
                tier = "high_confidence"
            else:
                tier = "ambiguous"

            row["yago_candidate_count"] = ycnt
            row["token_jaccard"] = f"{tj:.6f}"
            row["label_length_diff"] = ldiff
            row["confidence_tier"] = tier

            sw.writerow(row)
            written += 1

            if tier == "strict_proxy_gold":
                gw.writerow(row)
                kept_proxy += 1
            else:
                aw.writerow(row)
                kept_ambiguous += 1

            if written % args.progress_every == 0:
                print(
                    f"written={written:,} proxy_gold={kept_proxy:,} ambiguous={kept_ambiguous:,}",
                    flush=True
                )

    print("Done.", flush=True)
    print(f"Scored rows: {written:,}", flush=True)
    print(f"Strict proxy-gold rows: {kept_proxy:,}", flush=True)
    print(f"Ambiguous rows: {kept_ambiguous:,}", flush=True)

if __name__ == "__main__":
    main()
