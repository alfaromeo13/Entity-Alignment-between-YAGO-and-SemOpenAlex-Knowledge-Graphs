#!/usr/bin/env python3
import argparse
import csv

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--entity-prefix", required=True)
    ap.add_argument("--rel-prefix", required=True)
    args = ap.parse_args()

    n = 0
    bad = 0

    with open(args.input, encoding="utf-8", errors="replace") as f, open(args.out, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out, delimiter="\t")

        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) != 3:
                bad += 1
                continue

            h, r, t = p
            w.writerow([
                f"{args.entity_prefix}:{h}",
                f"{args.rel_prefix}:{r}",
                f"{args.entity_prefix}:{t}",
            ])

            n += 1
            if n % 10_000_000 == 0:
                print(f"written={n:,} bad={bad:,}", flush=True)

    print(f"Done. Written={n:,} bad={bad:,}", flush=True)
    print(f"Output: {args.out}", flush=True)

if __name__ == "__main__":
    main()
