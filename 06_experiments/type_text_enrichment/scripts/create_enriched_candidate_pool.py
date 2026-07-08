#!/usr/bin/env python3
import argparse
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--min-embedding", type=float, default=0.20)
    ap.add_argument("--top-k-per-yago", type=int, default=10)
    args = ap.parse_args()

    print(f"Reading: {args.input}", flush=True)

    df = pd.read_csv(args.input, sep="\t", dtype=str, low_memory=False)
    df["embedding_cosine"] = pd.to_numeric(df["embedding_cosine"], errors="coerce").fillna(0.0)

    before = len(df)

    df = df[df["embedding_cosine"] >= args.min_embedding].copy()

    df = df.sort_values(
        ["yago_entity", "embedding_cosine"],
        ascending=[True, False],
    )

    df = df.groupby("yago_entity", as_index=False).head(args.top_k_per_yago)

    df.to_csv(args.output, sep="\t", index=False)

    print(f"Input rows: {before:,}", flush=True)
    print(f"Output rows: {len(df):,}", flush=True)
    print(f"Wrote: {args.output}", flush=True)


if __name__ == "__main__":
    main()