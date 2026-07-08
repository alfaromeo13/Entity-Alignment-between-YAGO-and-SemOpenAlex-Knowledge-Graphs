#!/usr/bin/env python3
import argparse
import os
import math
import h5py
import numpy as np

def read_bucket_count(path: str) -> int:
    with h5py.File(path, "r") as f:
        return len(f["lhs"])

def write_bucket(out_path: str, lhs, rhs, rel, format_version=1):
    with h5py.File(out_path, "w") as f:
        f.create_dataset("lhs", data=lhs, compression="gzip")
        f.create_dataset("rhs", data=rhs, compression="gzip")
        f.create_dataset("rel", data=rel, compression="gzip")
        f.attrs["format_version"] = format_version

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--num-partitions", type=int, required=True)
    ap.add_argument("--target-total", type=int, required=True)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    os.makedirs(args.output_dir, exist_ok=True)

    bucket_paths = []
    counts = []

    # First pass: collect counts from the full converted test set
    for i in range(args.num_partitions):
        for j in range(args.num_partitions):
            path = os.path.join(args.input_dir, f"edges_{i}_{j}.h5")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Missing expected bucket file: {path}")
            c = read_bucket_count(path)
            bucket_paths.append((i, j, path))
            counts.append(c)

    counts = np.array(counts, dtype=np.int64)
    total_edges = int(counts.sum())

    if total_edges == 0:
        raise ValueError("Input dataset has zero edges.")

    print(f"Input total edges: {total_edges}")
    print(f"Requested sample size: {args.target_total}")

    # Proportional allocation per bucket
    raw_targets = counts * (args.target_total / total_edges)
    base_targets = np.floor(raw_targets).astype(np.int64)

    remainder = int(args.target_total - base_targets.sum())
    if remainder > 0:
        frac = raw_targets - base_targets
        order = np.argsort(-frac)
        for idx in order[:remainder]:
            if counts[idx] > base_targets[idx]:
                base_targets[idx] += 1

    sampled_total = int(base_targets.sum())
    print(f"Planned sampled total: {sampled_total}")

    # Second pass: write sampled buckets, preserving full grid
    written = 0
    nonempty = 0

    for idx, (i, j, path) in enumerate(bucket_paths):
        target = int(base_targets[idx])

        with h5py.File(path, "r") as f:
            lhs = f["lhs"][:]
            rhs = f["rhs"][:]
            rel = f["rel"][:]
            fmt = f.attrs.get("format_version", 1)

        n = len(lhs)
        if target > n:
            target = n

        if target == 0:
            lhs_s = np.array([], dtype=lhs.dtype)
            rhs_s = np.array([], dtype=rhs.dtype)
            rel_s = np.array([], dtype=rel.dtype)
        elif target == n:
            lhs_s, rhs_s, rel_s = lhs, rhs, rel
            nonempty += 1
        else:
            sel = np.sort(rng.choice(n, size=target, replace=False))
            lhs_s = lhs[sel]
            rhs_s = rhs[sel]
            rel_s = rel[sel]
            nonempty += 1

        out_path = os.path.join(args.output_dir, f"edges_{i}_{j}.h5")
        write_bucket(out_path, lhs_s, rhs_s, rel_s, format_version=fmt)
        written += len(lhs_s)

        if (idx + 1) % 500 == 0:
            print(f"Processed {idx + 1} / {len(bucket_paths)} buckets")

    print(f"Finished.")
    print(f"Buckets written: {len(bucket_paths)}")
    print(f"Non-empty sampled buckets: {nonempty}")
    print(f"Total sampled edges written: {written}")

if __name__ == "__main__":
    main()
