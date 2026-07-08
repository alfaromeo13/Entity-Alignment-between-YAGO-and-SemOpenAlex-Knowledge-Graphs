#!/usr/bin/env python3
import argparse
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alignments", required=True)
    ap.add_argument("--tfidf-scores", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--high-embedding-threshold", type=float, default=0.40)
    ap.add_argument("--low-embedding-threshold", type=float, default=0.30)
    ap.add_argument("--tfidf-threshold", type=float, default=0.85)
    args = ap.parse_args()

    df_main = pd.read_csv(args.alignments, sep="\t")
    df_tfidf = pd.read_csv(args.tfidf_scores, sep="\t")

    df = df_main.merge(
        df_tfidf[["yago", "sao", "tfidf_score"]],
        left_on=["yago_entity", "semopenalex_entity"],
        right_on=["yago", "sao"],
        how="left",
    )

    df["tfidf_score"] = df["tfidf_score"].fillna(0.0)
    df["embedding_cosine"] = df["embedding_cosine"].astype(float)

    filtered = df[
        (df["embedding_cosine"] >= args.high_embedding_threshold)
        |
        (
            (df["tfidf_score"] >= args.tfidf_threshold)
            & (df["embedding_cosine"] >= args.low_embedding_threshold)
        )
    ].copy()

    drop_cols = [c for c in ["yago", "sao"] if c in filtered.columns]
    filtered = filtered.drop(columns=drop_cols)

    filtered.to_csv(args.output, sep="\t", index=False)

    print(f"Original rows: {len(df):,}")
    print(f"After TF-IDF filtering: {len(filtered):,}")
    print(f"Wrote: {args.output}")

if __name__ == "__main__":
    main()