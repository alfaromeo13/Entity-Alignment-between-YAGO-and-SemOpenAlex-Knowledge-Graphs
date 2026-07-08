#!/usr/bin/env python3
import argparse
import csv
from collections import Counter

def load_pairs(path):
    pairs = set()
    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            pairs.add((row["yago_entity"], row["semopenalex_entity"]))
    return pairs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", required=True)
    ap.add_argument("--proxy-gold", required=True)
    ap.add_argument("--out-summary", required=True)
    ap.add_argument("--out-type-dist", required=True)
    ap.add_argument("--out-source-dist", required=True)
    args = ap.parse_args()

    print("Loading proxy-gold...", flush=True)
    gold = load_pairs(args.proxy_gold)

    total = 0
    source_counts = Counter()
    type_counts = Counter()
    matched_gold = 0
    score_bins = Counter()

    with open(args.final, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")

        for row in r:
            total += 1
            pair = (row["yago_entity"], row["semopenalex_entity"])

            source = row.get("source", "unknown")
            source_counts[source] += 1
            
            entity_type = row.get("semopenalex_type") or row.get("semopenalex_uri_type") or "unknown"
            type_counts[entity_type] += 1

            if pair in gold:
                matched_gold += 1

            score = float(row.get("embedding_cosine", 0.0))
            if score >= 0.9:
                score_bins[">=0.90"] += 1
            elif score >= 0.7:
                score_bins["0.70-0.89"] += 1
            elif score >= 0.5:
                score_bins["0.50-0.69"] += 1
            elif score >= 0.3:
                score_bins["0.30-0.49"] += 1
            else:
                score_bins["<0.30"] += 1

    precision_proxy = matched_gold / total if total else 0.0
    recall_proxy = matched_gold / len(gold) if gold else 0.0

    with open(args.out_summary, "w", encoding="utf-8") as out:
        out.write(f"final_alignments\t{total}\n")
        out.write(f"proxy_gold_size\t{len(gold)}\n")
        out.write(f"final_pairs_in_proxy_gold\t{matched_gold}\n")
        out.write(f"proxy_precision_like\t{precision_proxy:.6f}\n")
        out.write(f"proxy_recall_like\t{recall_proxy:.6f}\n")
        out.write("\nscore_bins\n")
        for k in [">=0.90", "0.70-0.89", "0.50-0.69", "0.30-0.49", "<0.30"]:
            out.write(f"{k}\t{score_bins[k]}\n")

    with open(args.out_type_dist, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out, delimiter="\t")
        w.writerow(["semopenalex_type", "count"])
        for k, v in type_counts.most_common():
            w.writerow([k, v])

    with open(args.out_source_dist, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out, delimiter="\t")
        w.writerow(["source", "count"])
        for k, v in source_counts.most_common():
            w.writerow([k, v])

    print(f"Final alignments: {total:,}")
    print(f"Proxy-gold size: {len(gold):,}")
    print(f"Final pairs in proxy-gold: {matched_gold:,}")
    print(f"Proxy precision-like: {precision_proxy:.6f}")
    print(f"Proxy recall-like: {recall_proxy:.6f}")
    print(f"Wrote: {args.out_summary}")

if __name__ == "__main__":
    main()
