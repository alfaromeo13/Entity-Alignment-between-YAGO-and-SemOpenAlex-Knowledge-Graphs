#!/usr/bin/env python3
import argparse
import csv
from collections import Counter

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-summary", required=True)
    ap.add_argument("--out-yago-dist", required=True)
    ap.add_argument("--progress-every", type=int, default=5_000_000)
    args = ap.parse_args()

    yago_counts = Counter()
    soa_entities = set()
    labels = set()

    rows = 0

    with open(args.input, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")

        for row in r:
            rows += 1
            yago_counts[row["yago_entity"]] += 1
            soa_entities.add(row["semopenalex_entity"])
            labels.add(row["norm_label"])

            if rows % args.progress_every == 0:
                print(
                    f"processed={rows:,} unique_yago={len(yago_counts):,} "
                    f"unique_soa={len(soa_entities):,} unique_labels={len(labels):,}",
                    flush=True,
                )

    # Candidate distribution per YAGO entity
    dist = Counter(yago_counts.values())

    with open(args.out_yago_dist, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out, delimiter="\t")
        w.writerow(["num_candidates_for_yago_entity", "num_yago_entities"])
        for k in sorted(dist):
            w.writerow([k, dist[k]])

    with open(args.out_summary, "w", encoding="utf-8") as out:
        out.write(f"candidate_rows\t{rows}\n")
        out.write(f"unique_yago_entities\t{len(yago_counts)}\n")
        out.write(f"unique_semopenalex_entities\t{len(soa_entities)}\n")
        out.write(f"unique_norm_labels\t{len(labels)}\n")
        out.write(f"avg_candidates_per_yago\t{rows / max(len(yago_counts), 1):.6f}\n")
        out.write(f"max_candidates_for_one_yago\t{max(yago_counts.values()) if yago_counts else 0}\n")

        for cutoff in [1, 2, 5, 10, 20, 50, 100]:
            n = sum(1 for c in yago_counts.values() if c <= cutoff)
            out.write(f"yago_entities_with_candidates_le_{cutoff}\t{n}\n")

    print(f"Finished. Rows={rows:,}")
    print(f"Unique YAGO entities={len(yago_counts):,}")
    print(f"Unique SemOpenAlex entities={len(soa_entities):,}")
    print(f"Unique normalized labels={len(labels):,}")
    print(f"Wrote: {args.out_summary}")
    print(f"Wrote: {args.out_yago_dist}")

if __name__ == "__main__":
    main()
