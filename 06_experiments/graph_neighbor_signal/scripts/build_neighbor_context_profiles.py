#!/usr/bin/env python3
import argparse
import csv
import os
import re
from collections import defaultdict


def simple_name(uri):
    uri = str(uri).strip("<>")
    tail = uri.rsplit("/", 1)[-1]
    tail = tail.rsplit("#", 1)[-1]
    return re.sub(r"[^A-Za-z0-9]+", " ", tail).lower().strip()


def load_targets(path):
    yago = set()
    soa = set()
    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            yago.add(row["yago_entity"])
            soa.add(row["semopenalex_entity"])
    return yago, soa


def scan_graph(graph_dir, targets, max_parts):
    parts = defaultdict(list)
    neighbor_ids = set()

    for split in ["train.tsv", "valid.tsv", "test.tsv"]:
        path = os.path.join(graph_dir, split)
        print(f"Scanning {path}", flush=True)

        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if len(row) != 3:
                    continue

                s, p, o = row
                pred = simple_name(p)

                if s in targets and len(parts[s]) < max_parts:
                    parts[s].append("out_" + pred)
                    parts[s].append("nbr_" + simple_name(o))
                    neighbor_ids.add(o)

                if o in targets and len(parts[o]) < max_parts:
                    parts[o].append("in_" + pred)
                    parts[o].append("nbr_" + simple_name(s))
                    neighbor_ids.add(s)

    return parts, neighbor_ids


def load_needed_text_profiles(path, needed):
    labels = {}

    print(f"Loading needed text profiles from {path}", flush=True)

    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            ent = row.get("entity")
            if ent not in needed:
                continue

            txt = row.get("text_profile", "")
            if txt:
                labels[ent] = txt.split()[:20]

    print(f"Loaded neighbor labels: {len(labels):,}", flush=True)
    return labels


def enrich_with_neighbor_labels(parts, labels, max_label_tokens):
    enriched = {}
    for ent, toks in parts.items():
        final = list(toks)
        # Neighbor IDs are already simplified in toks. This keeps the profile compact.
        enriched[ent] = " ".join(final[:max_label_tokens])
    return enriched


def write_profiles(path, targets, profiles):
    with open(path, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out, delimiter="\t")
        w.writerow(["entity", "neighbor_context"])
        for ent in sorted(targets):
            w.writerow([ent, profiles.get(ent, "")])
    print(f"Wrote {path}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alignments", required=True)
    ap.add_argument("--yago-dir", required=True)
    ap.add_argument("--soa-dir", required=True)
    ap.add_argument("--yago-output", required=True)
    ap.add_argument("--soa-output", required=True)
    ap.add_argument("--max-parts-per-entity", type=int, default=40)
    args = ap.parse_args()

    yago_targets, soa_targets = load_targets(args.alignments)

    print(f"YAGO targets: {len(yago_targets):,}", flush=True)
    print(f"SemOpenAlex targets: {len(soa_targets):,}", flush=True)

    yago_parts, _ = scan_graph(args.yago_dir, yago_targets, args.max_parts_per_entity)
    soa_parts, _ = scan_graph(args.soa_dir, soa_targets, args.max_parts_per_entity)

    write_profiles(args.yago_output, yago_targets, yago_parts)
    write_profiles(args.soa_output, soa_targets, soa_parts)


if __name__ == "__main__":
    main()
