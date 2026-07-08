#!/usr/bin/env python3
import argparse
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--embedding-weight", type=float, default=0.60)
    ap.add_argument("--profile-weight", type=float, default=0.35)
    ap.add_argument("--neighbor-weight", type=float, default=0.05)
    ap.add_argument("--min-score", type=float, default=0.25)
    args = ap.parse_args()

    print("Loading A+B alignments with neighbor scores...", flush=True)
    df = pd.read_csv(args.input, sep="\t", dtype=str, low_memory=False)

    df["embedding_cosine_num"] = pd.to_numeric(
        df.get("embedding_cosine", 0), errors="coerce"
    ).fillna(0.0)

    df["profile_tfidf_score_num"] = pd.to_numeric(
        df.get("profile_tfidf_score", 0), errors="coerce"
    ).fillna(0.0)

    df["neighbor_tfidf_score_num"] = pd.to_numeric(
        df.get("neighbor_tfidf_score", 0), errors="coerce"
    ).fillna(0.0)

    # Preserve strict proxy-gold links.
    proxy_mask = df["source"].eq("strict_proxy_gold")

    df["abc_score"] = (
        args.embedding_weight * df["embedding_cosine_num"]
        + args.profile_weight * df["profile_tfidf_score_num"]
        + args.neighbor_weight * df["neighbor_tfidf_score_num"]
    )

    # Keep all strict proxy-gold rows, and keep non-proxy rows above score threshold.
    filtered = df[
        proxy_mask | (df["abc_score"] >= args.min_score)
    ].copy()

    # Re-apply one-to-one globally, prioritizing proxy-gold first, then abc_score.
    filtered["proxy_priority"] = filtered["source"].eq("strict_proxy_gold").astype(int)

    filtered = filtered.sort_values(
        [
            "proxy_priority",
            "abc_score",
            "embedding_cosine_num",
            "profile_tfidf_score_num",
            "neighbor_tfidf_score_num",
        ],
        ascending=[False, False, False, False, False],
    )

    used_yago = set()
    used_soa = set()
    kept_rows = []

    for _, row in filtered.iterrows():
        y = row["yago_entity"]
        s = row["semopenalex_entity"]

        if y in used_yago or s in used_soa:
            continue

        used_yago.add(y)
        used_soa.add(s)
        kept_rows.append(row)

    out = pd.DataFrame(kept_rows)

    # Clean helper numeric columns, keep abc_score for analysis.
    drop_cols = [
        "embedding_cosine_num",
        "profile_tfidf_score_num",
        "neighbor_tfidf_score_num",
        "proxy_priority",
    ]
    out = out.drop(columns=[c for c in drop_cols if c in out.columns])

    out.to_csv(args.output, sep="\t", index=False)

    print(f"Input rows: {len(df):,}", flush=True)
    print(f"After score filter: {len(filtered):,}", flush=True)
    print(f"Final one-to-one rows: {len(out):,}", flush=True)
    print(f"Wrote: {args.output}", flush=True)


if __name__ == "__main__":
    main()
