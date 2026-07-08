#!/usr/bin/env python3
import argparse
import pandas as pd


def load_pairs(path):
    df = pd.read_csv(path, sep="\t", dtype=str, low_memory=False)
    pairs = set(zip(df["yago_entity"], df["semopenalex_entity"]))
    return df, pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--enriched", required=True)
    ap.add_argument("--out-summary", required=True)
    args = ap.parse_args()

    baseline_df, baseline_pairs = load_pairs(args.baseline)
    enriched_df, enriched_pairs = load_pairs(args.enriched)

    shared = baseline_pairs & enriched_pairs
    baseline_only = baseline_pairs - enriched_pairs
    enriched_only = enriched_pairs - baseline_pairs

    rows = [
        ["baseline_rows", len(baseline_df)],
        ["enriched_rows", len(enriched_df)],
        ["shared_pairs", len(shared)],
        ["baseline_only_pairs", len(baseline_only)],
        ["enriched_only_pairs", len(enriched_only)],
    ]

    out = pd.DataFrame(rows, columns=["metric", "value"])
    out.to_csv(args.out_summary, sep="\t", index=False)

    print(out.to_string(index=False))
    print(f"Wrote: {args.out_summary}")


if __name__ == "__main__":
    main()