#!/usr/bin/env python3
import argparse
import re
import unicodedata

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    text = text.encode("ascii", "ignore").decode("utf-8")
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    print(f"Reading: {args.input}", flush=True)

    df = pd.read_csv(
        args.input,
        sep="\t",
        dtype=str,
        low_memory=False,
    )

    required_cols = ["yago", "sao", "left", "right"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. Found columns: {list(df.columns)}"
        )

    df["left"] = df["left"].fillna("").astype(str).map(normalize)
    df["right"] = df["right"].fillna("").astype(str).map(normalize)

    before = len(df)

    df = df[
        (df["left"].str.strip() != "")
        & (df["right"].str.strip() != "")
    ].copy()

    print(f"Input rows: {before:,}", flush=True)
    print(f"Rows with non-empty text: {len(df):,}", flush=True)

    if len(df) == 0:
        raise ValueError("No non-empty text pairs found after normalization.")

    vectorizer = TfidfVectorizer(
        lowercase=False,
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
    )

    all_text = df["left"].tolist() + df["right"].tolist()

    print("Fitting TF-IDF vectorizer...", flush=True)
    vectorizer.fit(all_text)

    print("Transforming left/right text...", flush=True)
    left_vec = vectorizer.transform(df["left"])
    right_vec = vectorizer.transform(df["right"])

    df["tfidf_score"] = left_vec.multiply(right_vec).sum(axis=1).A1

    out = df[["yago", "sao", "tfidf_score"]].copy()
    out.to_csv(args.output, sep="\t", index=False)

    print(f"Rows scored: {len(out):,}", flush=True)
    print(f"Wrote: {args.output}", flush=True)


if __name__ == "__main__":
    main()