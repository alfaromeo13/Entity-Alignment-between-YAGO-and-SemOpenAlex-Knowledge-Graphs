#!/usr/bin/env python3
import argparse
import csv

def clean_uri(x):
    x = x.strip()
    if x.startswith("<") and x.endswith(">"):
        x = x[1:-1]
    return f"<{x}>"

def load_dict(path, name):
    d = {}
    n = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) != 2:
                continue
            d[clean_uri(p[0])] = p[1]
            n += 1
            if n % 10_000_000 == 0:
                print(f"{name}: loaded {n:,}", flush=True)
    print(f"{name}: final loaded {len(d):,}", flush=True)
    return d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proxy-gold", required=True)
    ap.add_argument("--yago-dict", required=True)
    ap.add_argument("--sem-dict", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--relation", default="seed_aligned_with")
    args = ap.parse_args()

    yago = load_dict(args.yago_dict, "YAGO dict")
    sem = load_dict(args.sem_dict, "SemOpenAlex dict")

    written = 0
    missing_y = 0
    missing_s = 0
    rows = 0

    with open(args.proxy_gold, encoding="utf-8") as f, open(args.out, "w", encoding="utf-8", newline="") as out:
        r = csv.DictReader(f, delimiter="\t")
        w = csv.writer(out, delimiter="\t")

        for row in r:
            rows += 1
            yu = clean_uri(row["yago_entity"])
            su = clean_uri(row["semopenalex_entity"])

            yid = yago.get(yu)
            sid = sem.get(su)

            if yid is None:
                missing_y += 1
                continue
            if sid is None:
                missing_s += 1
                continue

            w.writerow([f"yago:{yid}", args.relation, f"sem:{sid}"])
            w.writerow([f"sem:{sid}", args.relation, f"yago:{yid}"])
            written += 2

    print(f"Proxy rows: {rows:,}", flush=True)
    print(f"Written seed edges: {written:,}", flush=True)
    print(f"Missing YAGO: {missing_y:,}", flush=True)
    print(f"Missing SemOpenAlex: {missing_s:,}", flush=True)
    print(f"Output: {args.out}", flush=True)

if __name__ == "__main__":
    main()
