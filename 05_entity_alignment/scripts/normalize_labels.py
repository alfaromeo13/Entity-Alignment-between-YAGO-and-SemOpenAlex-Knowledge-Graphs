#!/usr/bin/env python3
import argparse, csv, re, unicodedata

def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

ap = argparse.ArgumentParser()
ap.add_argument("--input", required=True)
ap.add_argument("--output", required=True)
args = ap.parse_args()

with open(args.input, encoding="utf-8") as f, open(args.output, "w", encoding="utf-8", newline="") as out:
    r = csv.DictReader(f, delimiter="\t")
    w = csv.writer(out, delimiter="\t")
    w.writerow(["entity", "label", "norm_label"])
    n = 0
    kept = 0
    for row in r:
        n += 1
        label = row["label"]
        nl = norm(label)
        if len(nl) < 3:
            continue
        w.writerow([row["entity"], label, nl])
        kept += 1
        if n % 5_000_000 == 0:
            print(f"processed={n:,} kept={kept:,}", flush=True)

print("done", kept)
