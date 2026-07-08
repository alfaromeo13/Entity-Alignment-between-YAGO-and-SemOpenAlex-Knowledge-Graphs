#!/usr/bin/env python3

import os
import csv
import json
import argparse
from collections import OrderedDict

def load_mapping(path):
    mapping = OrderedDict()
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) != 2:
                continue
            value, idx = row
            mapping[value] = int(idx)
    return mapping

def write_mapping(mapping, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        for value, idx in mapping.items():
            writer.writerow([value, idx])

def get_or_add(mapping, key):
    if key not in mapping:
        mapping[key] = len(mapping)
    return mapping[key]

def scan_file(path, entity2id, relation2id):
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) != 3:
                continue
            s, p, o = row
            get_or_add(entity2id, s)
            get_or_add(relation2id, p)
            get_or_add(entity2id, o)
            count += 1
    return count

def map_file(src_path, dst_path, entity2id, relation2id):
    count = 0
    with open(src_path, "r", encoding="utf-8") as fin, \
         open(dst_path, "w", encoding="utf-8", newline="") as fout:
        reader = csv.reader(fin, delimiter="\t")
        writer = csv.writer(fout, delimiter="\t")
        for row in reader:
            if len(row) != 3:
                continue
            s, p, o = row
            writer.writerow([entity2id[s], relation2id[p], entity2id[o]])
            count += 1
    return count

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--dataset-name", required=True)
    ap.add_argument("--reuse-mappings-from", default=None)
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    train_in = os.path.join(args.input_dir, "train.tsv")
    valid_in = os.path.join(args.input_dir, "valid.tsv")
    test_in  = os.path.join(args.input_dir, "test.tsv")

    train_out = os.path.join(args.output_dir, "train.tsv")
    valid_out = os.path.join(args.output_dir, "valid.tsv")
    test_out  = os.path.join(args.output_dir, "test.tsv")

    ent_map_out = os.path.join(args.output_dir, "entities.dict")
    rel_map_out = os.path.join(args.output_dir, "relations.dict")
    stats_out = os.path.join(args.output_dir, "dataset_stats.json")

    if args.reuse_mappings_from:
        entity2id = load_mapping(os.path.join(args.reuse_mappings_from, "entities.dict"))
        relation2id = load_mapping(os.path.join(args.reuse_mappings_from, "relations.dict"))
    else:
        entity2id = OrderedDict()
        relation2id = OrderedDict()

        train_scan = scan_file(train_in, entity2id, relation2id)
        valid_scan = scan_file(valid_in, entity2id, relation2id)
        test_scan = scan_file(test_in, entity2id, relation2id)

        write_mapping(entity2id, ent_map_out)
        write_mapping(relation2id, rel_map_out)

    if args.reuse_mappings_from:
        write_mapping(entity2id, ent_map_out)
        write_mapping(relation2id, rel_map_out)

    train_count = map_file(train_in, train_out, entity2id, relation2id)
    valid_count = map_file(valid_in, valid_out, entity2id, relation2id)
    test_count  = map_file(test_in, test_out, entity2id, relation2id)

    stats = {
        "dataset": args.dataset_name,
        "num_entities": len(entity2id),
        "num_relations": len(relation2id),
        "train_triples": train_count,
        "valid_triples": valid_count,
        "test_triples": test_count,
        "reuse_mappings_from": args.reuse_mappings_from,
    }

    with open(stats_out, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()