#!/usr/bin/env python3
import argparse
import csv
import re
import unicodedata

from sklearn.feature_extraction.text import TfidfVectorizer


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    text = text.encode("ascii", "ignore").decode("utf-8")
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def collect_needed_entities(candidates_path):
    yago_needed = set()
    soa_needed = set()
    total = 0

    with open(candidates_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            total += 1
            yago_needed.add(row["yago_entity"])
            soa_needed.add(row["semopenalex_entity"])

    print(f"Candidate rows: {total:,}", flush=True)
    print(f"Needed YAGO profiles: {len(yago_needed):,}", flush=True)
    print(f"Needed SemOpenAlex profiles: {len(soa_needed):,}", flush=True)

    return yago_needed, soa_needed


def load_needed_profiles(path, needed):
    profiles = {}

    print(f"Loading only needed profiles from: {path}", flush=True)

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        cols = reader.fieldnames or []

        if "entity" not in cols:
            raise ValueError(f"{path} missing column 'entity'. Found: {cols}")

        text_col = None
        for c in ["text_profile", "profile_text", "text", "label", "entity_text"]:
            if c in cols:
                text_col = c
                break

        if text_col is None:
            raise ValueError(f"{path} has no usable text column. Found: {cols}")

        for row in reader:
            ent = row["entity"]
            if ent not in needed:
                continue

            txt = normalize(row.get(text_col, ""))
            if txt:
                profiles[ent] = txt

    print(f"Loaded profiles: {len(profiles):,}", flush=True)
    return profiles


def rowwise_cosine_scores(left_vec, right_vec):
    return left_vec.multiply(right_vec).sum(axis=1).A1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--yago-profiles", required=True)
    ap.add_argument("--semopenalex-profiles", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--batch-size", type=int, default=100000)
    args = ap.parse_args()

    yago_needed, soa_needed = collect_needed_entities(args.candidates)

    yago_profiles = load_needed_profiles(args.yago_profiles, yago_needed)
    soa_profiles = load_needed_profiles(args.semopenalex_profiles, soa_needed)

    print("Preparing text corpus for TF-IDF fit...", flush=True)

    corpus = []
    with open(args.candidates, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            y = row["yago_entity"]
            s = row["semopenalex_entity"]

            ytxt = yago_profiles.get(y) or normalize(row.get("yago_label", ""))
            stxt = soa_profiles.get(s) or normalize(row.get("semopenalex_label", ""))

            if ytxt:
                corpus.append(ytxt)
            if stxt:
                corpus.append(stxt)

    if not corpus:
        raise ValueError("No text found for TF-IDF fitting.")

    print(f"TF-IDF corpus size: {len(corpus):,}", flush=True)

    vectorizer = TfidfVectorizer(
        lowercase=False,
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
    )

    print("Fitting TF-IDF...", flush=True)
    vectorizer.fit(corpus)
    del corpus

    print(f"Writing scores to: {args.output}", flush=True)

    with open(args.candidates, encoding="utf-8") as f, open(
        args.output, "w", encoding="utf-8", newline=""
    ) as out:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = list(reader.fieldnames or []) + ["profile_tfidf_score"]

        writer = csv.DictWriter(out, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()

        batch_rows = []
        left_texts = []
        right_texts = []
        processed = 0

        def flush_batch():
            nonlocal processed, batch_rows, left_texts, right_texts

            if not batch_rows:
                return

            left_vec = vectorizer.transform(left_texts)
            right_vec = vectorizer.transform(right_texts)
            scores = rowwise_cosine_scores(left_vec, right_vec)

            for row, score in zip(batch_rows, scores):
                row["profile_tfidf_score"] = f"{float(score):.8f}"
                writer.writerow(row)

            processed += len(batch_rows)
            print(f"Scored rows: {processed:,}", flush=True)

            batch_rows = []
            left_texts = []
            right_texts = []

        for row in reader:
            y = row["yago_entity"]
            s = row["semopenalex_entity"]

            ytxt = yago_profiles.get(y) or normalize(row.get("yago_label", ""))
            stxt = soa_profiles.get(s) or normalize(row.get("semopenalex_label", ""))

            if not ytxt or not stxt:
                row["profile_tfidf_score"] = "0.00000000"
                writer.writerow(row)
                processed += 1
                continue

            batch_rows.append(row)
            left_texts.append(ytxt)
            right_texts.append(stxt)

            if len(batch_rows) >= args.batch_size:
                flush_batch()

        flush_batch()

    print("Done.", flush=True)


if __name__ == "__main__":
    main()