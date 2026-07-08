#!/usr/bin/env python3
import argparse
import csv

def parse_dict_line(line):
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 2:
        return None, None

    # Supports both:
    # id<TAB>entity
    # entity<TAB>id
    if parts[0].isdigit():
        return parts[1], int(parts[0])
    if parts[1].isdigit():
        return parts[0], int(parts[1])

    return None, None

def collect_needed(candidate_path):
    yago = set()
    soa = set()
    rows = 0

    with open(candidate_path, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            rows += 1
            yago.add(row["yago_entity"])
            soa.add(row["semopenalex_entity"])
            if rows % 5_000_000 == 0:
                print(f"collect rows={rows:,} yago={len(yago):,} soa={len(soa):,}", flush=True)

    return yago, soa

def scan_dict(dict_path, needed, name):
    out = {}
    rows = 0

    with open(dict_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            rows += 1
            ent, eid = parse_dict_line(line)
            if ent in needed:
                out[ent] = eid

            if rows % 20_000_000 == 0:
                print(f"{name} dict scanned={rows:,} found={len(out):,}/{len(needed):,}", flush=True)

            if len(out) == len(needed):
                break

    print(f"{name}: found {len(out):,}/{len(needed):,}", flush=True)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--yago-dict", required=True)
    ap.add_argument("--soa-dict", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    print("Collecting needed entities from candidates...", flush=True)
    needed_yago, needed_soa = collect_needed(args.candidates)
    print(f"Needed YAGO: {len(needed_yago):,}", flush=True)
    print(f"Needed SemOpenAlex: {len(needed_soa):,}", flush=True)

    print("Scanning YAGO dictionary...", flush=True)
    yago_map = scan_dict(args.yago_dict, needed_yago, "YAGO")

    print("Scanning SemOpenAlex dictionary...", flush=True)
    soa_map = scan_dict(args.soa_dict, needed_soa, "SemOpenAlex")

    missing = 0
    written = 0

    with open(args.candidates, encoding="utf-8") as f, \
         open(args.output, "w", encoding="utf-8", newline="") as out:

        r = csv.DictReader(f, delimiter="\t")
        fieldnames = r.fieldnames + ["yago_id", "semopenalex_id"]
        w = csv.DictWriter(out, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()

        for row in r:
            yid = yago_map.get(row["yago_entity"])
            sid = soa_map.get(row["semopenalex_entity"])

            if yid is None or sid is None:
                missing += 1
                continue

            row["yago_id"] = yid
            row["semopenalex_id"] = sid
            w.writerow(row)
            written += 1

            if written % 5_000_000 == 0:
                print(f"written={written:,} missing={missing:,}", flush=True)

    print(f"Done. Written={written:,} Missing={missing:,}")
    print(f"Wrote: {args.output}")

if __name__ == "__main__":
    main()