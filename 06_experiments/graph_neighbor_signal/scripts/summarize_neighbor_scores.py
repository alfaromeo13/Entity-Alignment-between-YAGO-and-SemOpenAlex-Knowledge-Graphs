#!/usr/bin/env python3
import argparse
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.input, sep="\t", dtype=str, low_memory=False)
    base = pd.read_csv(
        args.baseline,
        sep="\t",
        dtype=str,
        usecols=["yago_entity", "semopenalex_entity"],
    )

    base_pairs = set(zip(base["yago_entity"], base["semopenalex_entity"]))
    df["neighbor_tfidf_score_num"] = pd.to_numeric(
        df["neighbor_tfidf_score"], errors="coerce"
    ).fillna(0.0)

    pairs = list(zip(df["yago_entity"], df["semopenalex_entity"]))
    df["group"] = ["shared_with_baseline" if p in base_pairs else "enriched_only" for p in pairs]

    rows = []
    for group, sub in df.groupby("group"):
        rows.append([group, "rows", len(sub)])
        for threshold in [0.0, 0.05, 0.10, 0.20, 0.30, 0.50]:
            rows.append([
                group,
                f"neighbor_score_ge_{threshold}",
                int((sub["neighbor_tfidf_score_num"] >= threshold).sum()),
            ])

    out = pd.DataFrame(rows, columns=["group", "metric", "value"])
    out.to_csv(args.output, sep="\t", index=False)

    print(out.to_string(index=False))
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
