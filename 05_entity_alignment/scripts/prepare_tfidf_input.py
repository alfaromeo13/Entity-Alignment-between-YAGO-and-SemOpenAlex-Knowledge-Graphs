#!/usr/bin/env python3
import argparse
import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="Prepare TF-IDF input from profile-filtered alignment file."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Input alignment TSV, usually alignments_threshold030_1to1_profilefiltered.tsv",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output TF-IDF input TSV",
    )

    parser.add_argument(
        "--only-embedding",
        action="store_true",
        help="If set, only prepare rows where source == embedding_top1.",
    )

    parser.add_argument(
        "--min-embedding",
        type=float,
        default=0.30,
        help="Minimum embedding_cosine score to include. Default: 0.30",
    )

    args = parser.parse_args()

    print(f"Reading: {args.input}", flush=True)

    df = pd.read_csv(
        args.input,
        sep="\t",
        dtype=str,
        low_memory=False,
    )

    required_cols = [
        "yago_entity",
        "semopenalex_entity",
        "yago_label",
        "semopenalex_label",
        "source",
        "embedding_cosine",
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["embedding_cosine_num"] = pd.to_numeric(
        df["embedding_cosine"],
        errors="coerce",
    ).fillna(0.0)

    before = len(df)

    if args.only_embedding:
        df = df[df["source"] == "embedding_top1"].copy()

    df = df[df["embedding_cosine_num"] >= args.min_embedding].copy()

    df["left"] = df["yago_label"].fillna("").astype(str)
    df["right"] = df["semopenalex_label"].fillna("").astype(str)

    out = df[
        [
            "yago_entity",
            "semopenalex_entity",
            "left",
            "right",
        ]
    ].copy()

    out.columns = ["yago", "sao", "left", "right"]

    out.to_csv(args.output, sep="\t", index=False)

    print(f"Input rows: {before:,}", flush=True)
    print(f"Output rows: {len(out):,}", flush=True)
    print(f"Wrote: {args.output}", flush=True)


if __name__ == "__main__":
    main()