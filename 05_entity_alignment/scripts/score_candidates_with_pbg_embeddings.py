#!/usr/bin/env python3
import argparse
import csv
import glob
import os
from collections import defaultdict

import h5py
import numpy as np

class PBGEmbeddings:
    def __init__(self, path, num_partitions):
        self.path = path
        self.num_partitions = num_partitions
        self.files = {}
        self.datasets = {}

    def _find_file(self, part):
        pattern = os.path.join(self.path, f"embeddings_entity_{part}.v*.h5")
        files = sorted(glob.glob(pattern))
        if not files:
            raise FileNotFoundError(f"No embedding file for partition {part}: {pattern}")
        # choose newest/highest version lexicographically
        return files[-1]

    def _open_part(self, part):
        if part in self.datasets:
            return self.datasets[part]

        fn = self._find_file(part)
        hf = h5py.File(fn, "r")

        if "embeddings" in hf:
            ds = hf["embeddings"]
        else:
            # fallback: find first 2D dataset
            ds = None
            def visitor(name, obj):
                nonlocal ds
                if ds is None and isinstance(obj, h5py.Dataset) and len(obj.shape) == 2:
                    ds = obj
            hf.visititems(visitor)
            if ds is None:
                raise RuntimeError(f"No 2D embedding dataset found in {fn}")

        self.files[part] = hf
        self.datasets[part] = ds
        return ds

    def get(self, eid):
        # This matches the modulo partitioning used by the PBG conversion pipeline.
        part = eid % self.num_partitions
        offset = eid // self.num_partitions
        ds = self._open_part(part)
        return np.asarray(ds[offset], dtype=np.float32)

def cosine(a, b):
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--yago-emb", required=True)
    ap.add_argument("--soa-emb", required=True)
    ap.add_argument("--yago-partitions", type=int, required=True)
    ap.add_argument("--soa-partitions", type=int, required=True)
    ap.add_argument("--out-scored", required=True)
    ap.add_argument("--out-top1", required=True)
    ap.add_argument("--progress-every", type=int, default=1_000_000)
    args = ap.parse_args()

    yemb = PBGEmbeddings(args.yago_emb, args.yago_partitions)
    semb = PBGEmbeddings(args.soa_emb, args.soa_partitions)

    current_yago = None
    current_rows = []

    total = 0
    groups = 0

    def flush_group(rows, top_writer):
        if not rows:
            return
        best = max(rows, key=lambda r: float(r["embedding_cosine"]))
        top_writer.writerow(best)

    with open(args.candidates, encoding="utf-8") as f, \
         open(args.out_scored, "w", encoding="utf-8", newline="") as scored, \
         open(args.out_top1, "w", encoding="utf-8", newline="") as top1:

        r = csv.DictReader(f, delimiter="\t")
        fieldnames = r.fieldnames + ["embedding_cosine"]

        sw = csv.DictWriter(scored, fieldnames=fieldnames, delimiter="\t")
        tw = csv.DictWriter(top1, fieldnames=fieldnames, delimiter="\t")
        sw.writeheader()
        tw.writeheader()

        for row in r:
            total += 1
            y = row["yago_entity"]

            if current_yago is None:
                current_yago = y

            if y != current_yago:
                flush_group(current_rows, tw)
                groups += 1
                current_rows = []
                current_yago = y

            yid = int(row["yago_id"])
            sid = int(row["semopenalex_id"])

            try:
                ye = yemb.get(yid)
                se = semb.get(sid)
                score = cosine(ye, se)
            except Exception as e:
                score = 0.0

            row["embedding_cosine"] = f"{score:.8f}"
            sw.writerow(row)
            current_rows.append(dict(row))

            if total % args.progress_every == 0:
                print(f"scored={total:,} yago_groups={groups:,}", flush=True)

        flush_group(current_rows, tw)

    print(f"Done. Scored rows={total:,}")
    print(f"Wrote scored: {args.out_scored}")
    print(f"Wrote top1: {args.out_top1}")

if __name__ == "__main__":
    main()
