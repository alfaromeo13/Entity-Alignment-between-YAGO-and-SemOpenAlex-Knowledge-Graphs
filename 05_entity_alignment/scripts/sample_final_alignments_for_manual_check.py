#!/usr/bin/env python3
import argparse
import os
import pandas as pd


def write_sample(df, path, n, seed):
    if len(df) == 0:
        print(f"Skipping {path}: no rows")
        return
    sample_n = min(n, len(df))
    df.sample(n=sample_n, random_state=seed).to_csv(path, sep="\t", index=False)
    print(f"Wrote {sample_n:,} rows: {path}")


def main():
    ap = argparse.ArgumentParser(
        description="Create manual inspection samples from final alignment file."
    )
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--random-n", type=int, default=500)
    ap.add_argument("--embedding-n", type=int, default=200)
    ap.add_argument("--low-score-n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    print(f"Reading: {args.input}", flush=True)
    df = pd.read_csv(args.input, sep="\t", dtype=str, low_memory=False)

    if "embedding_cosine" not in df.columns:
        raise ValueError("Missing column: embedding_cosine")
    if "source" not in df.columns:
        raise ValueError("Missing column: source")

    df["embedding_cosine_num"] = pd.to_numeric(
        df["embedding_cosine"], errors="coerce"
    ).fillna(0.0)

    # 1. General random sample from the final production file
    write_sample(
        df,
        os.path.join(args.out_dir, "final_random_sample_500.tsv"),
        args.random_n,
        args.seed,
    )

    # 2. Random sample only from embedding-derived alignments
    embedding_df = df[df["source"] == "embedding_top1"].copy()
    write_sample(
        embedding_df,
        os.path.join(args.out_dir, "final_embedding_sample_200.tsv"),
        args.embedding_n,
        args.seed,
    )

    # 3. Lowest-score embedding alignments, useful for finding risky cases
    low_score_df = (
        embedding_df.sort_values("embedding_cosine_num", ascending=True)
        .head(args.low_score_n)
        .copy()
    )
    low_score_df.to_csv(
        os.path.join(args.out_dir, "final_low_score_embedding_200.tsv"),
        sep="\t",
        index=False,
    )
    print(
        f"Wrote {len(low_score_df):,} rows: "
        f"{os.path.join(args.out_dir, 'final_low_score_embedding_200.tsv')}"
    )

    # 4. Samples by SemOpenAlex type, if available
    if "semopenalex_type" in df.columns:
        for t in sorted(df["semopenalex_type"].dropna().unique()):
            sub = df[df["semopenalex_type"] == t].copy()
            if len(sub) == 0:
                continue
            safe_t = str(t).replace("/", "_")
            write_sample(
                sub,
                os.path.join(args.out_dir, f"final_sample_type_{safe_t}.tsv"),
                100,
                args.seed,
            )

    # 5. Small summary
    summary_path = os.path.join(args.out_dir, "manual_sample_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as out:
        out.write(f"Input file: {args.input}\n")
        out.write(f"Total final alignments: {len(df):,}\n\n")
        out.write("Source distribution:\n")
        out.write(df["source"].value_counts(dropna=False).to_string())
        out.write("\n\n")
        if "semopenalex_type" in df.columns:
            out.write("SemOpenAlex type distribution:\n")
            out.write(df["semopenalex_type"].value_counts(dropna=False).to_string())
            out.write("\n")
    print(f"Wrote summary: {summary_path}")


if __name__ == "__main__":
    main()