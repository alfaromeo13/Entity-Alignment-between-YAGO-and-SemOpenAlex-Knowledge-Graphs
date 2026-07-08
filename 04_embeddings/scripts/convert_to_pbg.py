import argparse
import os
from collections import OrderedDict

import h5py
import numpy as np


class H5BucketWriter:
    def __init__(self, out_dir, P, buffer_edges=200_000, max_open=64):
        self.out_dir = out_dir
        self.P = P
        self.buffer_edges = buffer_edges
        self.max_open = max_open

        self.buffers = {}
        self.files = OrderedDict()

    def _path(self, lp, rp):
        return os.path.join(self.out_dir, f"edges_{lp}_{rp}.h5")

    def _get(self, lp, rp):
        key = (lp, rp)

        if key in self.files:
            self.files.move_to_end(key)
            return self.files[key]

        while len(self.files) >= self.max_open:
            _, (f, *_rest) = self.files.popitem(last=False)
            f.close()

        path = self._path(lp, rp)
        os.makedirs(self.out_dir, exist_ok=True)

        if os.path.exists(path):
            f = h5py.File(path, "a")
            d_lhs = f["lhs"]
            d_rhs = f["rhs"]
            d_rel = f["rel"]
        else:
            f = h5py.File(path, "w")
            d_lhs = f.create_dataset("lhs", (0,), maxshape=(None,), dtype=np.int64, chunks=True)
            d_rhs = f.create_dataset("rhs", (0,), maxshape=(None,), dtype=np.int64, chunks=True)
            d_rel = f.create_dataset("rel", (0,), maxshape=(None,), dtype=np.int64, chunks=True)

        self.files[key] = (f, d_lhs, d_rhs, d_rel)
        return self.files[key]

    def add(self, lhs, rel, rhs):
        lp = lhs % self.P
        rp = rhs % self.P
        key = (lp, rp)

        if key not in self.buffers:
            self.buffers[key] = ([], [], [])

        self.buffers[key][0].append(lhs)
        self.buffers[key][1].append(rhs)
        self.buffers[key][2].append(rel)

        if len(self.buffers[key][0]) >= self.buffer_edges:
            self.flush(lp, rp)

    def flush(self, lp, rp):
        key = (lp, rp)
        if key not in self.buffers or not self.buffers[key][0]:
            return

        lhs, rhs, rel = self.buffers[key]

        lhs = np.asarray(lhs, dtype=np.int64)
        rhs = np.asarray(rhs, dtype=np.int64)
        rel = np.asarray(rel, dtype=np.int64)

        f, d_lhs, d_rhs, d_rel = self._get(lp, rp)

        n0 = d_lhs.shape[0]
        n1 = n0 + len(lhs)

        d_lhs.resize((n1,))
        d_rhs.resize((n1,))
        d_rel.resize((n1,))

        d_lhs[n0:n1] = lhs
        d_rhs[n0:n1] = rhs
        d_rel[n0:n1] = rel

        self.buffers[key] = ([], [], [])

    def close(self):
        for (lp, rp) in list(self.buffers.keys()):
            self.flush(lp, rp)

        for f, *_ in self.files.values():
            f.close()


def write_entity_counts(out_dir, total_entities, P):
    for p in range(P):
        cnt = (total_entities - p + P - 1) // P if total_entities > p else 0
        with open(os.path.join(out_dir, f"entity_count_entity_{p}.txt"), "w") as f:
            f.write(str(cnt) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--entities", type=int, required=True)
    ap.add_argument("--partitions", type=int, default=128)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    print("Writing entity counts...")
    write_entity_counts(args.out, args.entities, args.partitions)

    writer = H5BucketWriter(args.out, args.partitions)

    print("Streaming triples...")
    with open(args.input, "r") as f:
        for i, line in enumerate(f, 1):
            s, p, o = line.strip().split("\t")
            writer.add(int(s), int(p), int(o))

            if i % 10_000_000 == 0:
                print(f"{i:,} triples processed")

    writer.close()
    print("Done.")


if __name__ == "__main__":
    main()