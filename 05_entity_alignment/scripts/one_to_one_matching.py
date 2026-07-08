#!/usr/bin/env python3
import argparse
import csv

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    rows = []

    with open(args.input, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        fieldnames = r.fieldnames

        for row in r:
            row["_score"] = float(row["embedding_cosine"])
            rows.append(row)

    # Highest-confidence matches first.
    # proxy-gold has score 1.0, so it is protected naturally.
    rows.sort(key=lambda x: x["_score"], reverse=True)

    used_yago = set()
    used_soa = set()
    kept = 0
    skipped = 0

    with open(args.output, "w", encoding="utf-8", newline="") as out:
        w = csv.DictWriter(out, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()

        for row in rows:
            y = row["yago_entity"]
            s = row["semopenalex_entity"]

            if y in used_yago or s in used_soa:
                skipped += 1
                continue

            used_yago.add(y)
            used_soa.add(s)

            row.pop("_score", None)
            w.writerow(row)
            kept += 1

    print(f"Input rows: {len(rows):,}")
    print(f"Kept one-to-one alignments: {kept:,}")
    print(f"Skipped conflicts: {skipped:,}")
    print(f"Wrote: {args.output}")

if __name__ == "__main__":
    main()
