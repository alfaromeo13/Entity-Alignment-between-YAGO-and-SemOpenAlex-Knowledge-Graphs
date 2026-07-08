#!/usr/bin/env python3
import argparse
import csv
import re
import unicodedata

from sklearn.feature_extraction.text import TfidfVectorizer


def normalize(text):
    text = unicodedata.normalize("NFKD", str(text))
    text = text.encode("ascii", "ignore").decode("utf-8")
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_profiles(path):
    d = {}
    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            ent = row["entity"]
            txt = normalize(row.get("neighbor_context", ""))
            d[ent] = txt
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alignments", required=True)
    ap.add_argument("--yago-profiles", required=True)
    ap.add_argument("--soa-profiles", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--batch-size", type=int, default=100000)
    args = ap.parse_args()

    print("Loading neighbor profiles...", flush=True)
    yago_profiles = load_profiles(args.yago_profiles)
    soa_profiles = load_profiles(args.soa_profiles)

    corpus = []
    with open(args.alignments, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            yt = yago_profiles.get(row["yago_entity"], "")
            st = soa_profiles.get(row["semopenalex_entity"], "")
            if yt:
                corpus.append(yt)
            if st:
                corpus.append(st)

    print(f"Corpus size: {len(corpus):,}", flush=True)

    vectorizer = TfidfVectorizer(
        lowercase=False,
        analyzer="word",
        ngram_range=(1, 2),
        min_df=1,
    )

    if corpus:
        vectorizer.fit(corpus)
    else:
        raise ValueError("No neighbor context available.")

    with open(args.alignments, encoding="utf-8") as f, open(
        args.output, "w", encoding="utf-8", newline=""
    ) as out:
        r = csv.DictReader(f, delimiter="\t")
        fieldnames = list(r.fieldnames or []) + ["neighbor_tfidf_score"]
        w = csv.DictWriter(out, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()

        rows = []
        left = []
        right = []
        done = 0

        def flush():
            nonlocal rows, left, right, done
            if not rows:
                return

            lv = vectorizer.transform(left)
            rv = vectorizer.transform(right)
            scores = lv.multiply(rv).sum(axis=1).A1

            for row, score in zip(rows, scores):
                row["neighbor_tfidf_score"] = f"{float(score):.8f}"
                w.writerow(row)

            done += len(rows)
            print(f"Scored {done:,}", flush=True)
            rows, left, right = [], [], []

        for row in r:
            yt = yago_profiles.get(row["yago_entity"], "")
            st = soa_profiles.get(row["semopenalex_entity"], "")

            rows.append(row)
            left.append(yt)
            right.append(st)

            if len(rows) >= args.batch_size:
                flush()

        flush()

    print(f"Wrote: {args.output}", flush=True)


if __name__ == "__main__":
    main()
