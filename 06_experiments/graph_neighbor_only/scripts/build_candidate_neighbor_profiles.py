#!/usr/bin/env python3
import argparse
import csv
import os
import re
from collections import defaultdict


def simple_name(uri: str) -> str:
    uri = str(uri).strip("<>")
    tail = uri.rsplit("/", 1)[-1]
    tail = tail.rsplit("#", 1)[-1]
    tail = re.sub(r"[_\-]+", " ", tail)
    tail = re.sub(r"[^A-Za-z0-9 ]+", " ", tail)
    tail = re.sub(r"\s+", " ", tail).strip().lower()
    return tail


def load_candidate_entities(path):
    yago = set()
    soa = set()

    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            yago.add(row["yago_entity"])
            soa.add(row["semopenalex_entity"])

    return yago, soa


def scan_graph(graph_dir, targets, max_parts):
    profiles = defaultdict(list)

    for split in ["train.tsv", "valid.tsv", "test.tsv"]:
        path = os.path.join(graph_dir, split)
        print(f"Scanning: {path}", flush=True)

        with open(path, encoding="utf-8") as f:
            r = csv.reader(f, delimiter="\t")
            for row in r:
                if len(row) != 3:
                    continue

                s, p, o = row
                pred = simple_name(p)

                if s in targets and len(profiles[s]) < max_parts:
                    profiles[s].append("out_" + pred)
                    profiles[s].append("neighbor_" + simple_name(o))

                if o in targets and len(profiles[o]) < max_parts:
                    profiles[o].append("in_" + pred)
                    profiles[o].append("neighbor_" + simple_name(s))

    return profiles


def write_profiles(path, targets, profiles):
    with open(path, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out, delimiter="\t")
        w.writerow(["entity", "neighbor_context"])
        for ent in sorted(targets):
            w.writerow([ent, " ".join(profiles.get(ent, []))])

    print(f"Wrote: {path}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--yago-dir", required=True)
    ap.add_argument("--soa-dir", required=True)
    ap.add_argument("--yago-output", required=True)
    ap.add_argument("--soa-output", required=True)
    ap.add_argument("--max-parts-per-entity", type=int, default=80)
    args = ap.parse_args()

    yago_targets, soa_targets = load_candidate_entities(args.candidates)

    print(f"YAGO candidate entities: {len(yago_targets):,}", flush=True)
    print(f"SemOpenAlex candidate entities: {len(soa_targets):,}", flush=True)

    yago_profiles = scan_graph(args.yago_dir, yago_targets, args.max_parts_per_entity)
    soa_profiles = scan_graph(args.soa_dir, soa_targets, args.max_parts_per_entity)

    write_profiles(args.yago_output, yago_targets, yago_profiles)
    write_profiles(args.soa_output, soa_targets, soa_profiles)


if __name__ == "__main__":
    main()
