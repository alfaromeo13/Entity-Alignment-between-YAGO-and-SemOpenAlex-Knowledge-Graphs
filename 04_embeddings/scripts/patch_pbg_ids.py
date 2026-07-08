#!/usr/bin/env python3
import argparse
import os
import h5py

def remap_dataset(ds, num_partitions, chunk):
    n = ds.shape[0]
    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        block = ds[start:end]
        block //= num_partitions
        ds[start:end] = block

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edge-dir", required=True)
    ap.add_argument("--num-partitions", type=int, required=True)
    ap.add_argument("--chunk", type=int, default=5_000_000)
    args = ap.parse_args()

    patched = 0

    for fname in sorted(os.listdir(args.edge_dir)):
        if not fname.startswith("edges_") or not fname.endswith(".h5"):
            continue

        path = os.path.join(args.edge_dir, fname)
        with h5py.File(path, "r+") as f:
            if "lhs" not in f or "rhs" not in f or "rel" not in f:
                continue

            remap_dataset(f["lhs"], args.num_partitions, args.chunk)
            remap_dataset(f["rhs"], args.num_partitions, args.chunk)

            f.attrs["format_version"] = 1

        patched += 1
        if patched % 100 == 0:
            print(f"Patched {patched} files")

    print(f"Done. Patched {patched} files.")

if __name__ == "__main__":
    main()
