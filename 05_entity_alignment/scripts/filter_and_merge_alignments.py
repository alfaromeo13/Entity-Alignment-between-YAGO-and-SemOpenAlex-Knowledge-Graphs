#!/usr/bin/env python3
import argparse
import csv
import re

def semopenalex_type(uri):
    types = [
        "author",
        "work",
        "institution",
        "source",
        "publisher",
        "funder",
        "concept",
        "keyword",
        "topic",
        "field",
        "subfield",
        "domain",
        "venue",
    ]

    for t in types:
        if f"/{t}/" in uri:
            return t

    return "unknown"

def looks_like_person_label(label):
    label = label.strip()
    toks = label.split()
    if len(toks) < 2 or len(toks) > 5:
        return False
    bad_words = {
        "university", "school", "church", "city", "county", "province", "river",
        "lake", "mount", "company", "journal", "film", "album", "song", "rail",
        "line", "station", "ministry", "hospital", "theory", "newspaper"
    }
    low = label.lower()
    if any(w in low for w in bad_words):
        return False
    return all(t[:1].isupper() or "." in t for t in toks)

def compatible(yago_label, soa_uri):
    st = semopenalex_type(soa_uri)

    # Strong safe rule:
    # If SemOpenAlex is author, YAGO should look person-like.
    if st == "author":
        return looks_like_person_label(yago_label)

    # If YAGO looks person-like, avoid matching it to works/concepts/institutions.
    if looks_like_person_label(yago_label) and st != "author":
        return False

    # Otherwise allow for now; stricter type inference can be added later.
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proxy-gold", required=True)
    ap.add_argument("--top1", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--threshold", type=float, default=0.35)
    args = ap.parse_args()

    total_proxy = 0
    total_top1 = 0
    kept_top1 = 0
    rejected_score = 0
    rejected_type = 0

    with open(args.out, "w", encoding="utf-8", newline="") as out:
        fieldnames = [
            "yago_entity", "semopenalex_entity", "norm_label", "yago_label",
            "semopenalex_label", "semopenalex_type", "source",
            "embedding_cosine", "confidence_tier"
        ]
        w = csv.DictWriter(out, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()

        # Add strict proxy-gold as accepted exact alignments.
        with open(args.proxy_gold, encoding="utf-8") as f:
            r = csv.DictReader(f, delimiter="\t")
            for row in r:
                total_proxy += 1
                st = semopenalex_type(row["semopenalex_entity"])
                w.writerow({
                    "yago_entity": row["yago_entity"],
                    "semopenalex_entity": row["semopenalex_entity"],
                    "norm_label": row["norm_label"],
                    "yago_label": row["yago_label"],
                    "semopenalex_label": row["semopenalex_label"],
                    "semopenalex_type": st,
                    "source": "strict_proxy_gold",
                    "embedding_cosine": "1.00000000",
                    "confidence_tier": "strict_proxy_gold",
                })

        # Add accepted embedding predictions.
        with open(args.top1, encoding="utf-8") as f:
            r = csv.DictReader(f, delimiter="\t")
            for row in r:
                total_top1 += 1
                score = float(row["embedding_cosine"])

                if score < args.threshold:
                    rejected_score += 1
                    continue

                if not compatible(row["yago_label"], row["semopenalex_entity"]):
                    rejected_type += 1
                    continue

                st = semopenalex_type(row["semopenalex_entity"])
                kept_top1 += 1

                w.writerow({
                    "yago_entity": row["yago_entity"],
                    "semopenalex_entity": row["semopenalex_entity"],
                    "norm_label": row["norm_label"],
                    "yago_label": row["yago_label"],
                    "semopenalex_label": row["semopenalex_label"],
                    "semopenalex_type": st,
                    "source": "embedding_top1",
                    "embedding_cosine": row["embedding_cosine"],
                    "confidence_tier": row["confidence_tier"],
                })

    print(f"Proxy-gold accepted: {total_proxy:,}")
    print(f"Top1 predictions total: {total_top1:,}")
    print(f"Top1 accepted after filters: {kept_top1:,}")
    print(f"Rejected by score: {rejected_score:,}")
    print(f"Rejected by type: {rejected_type:,}")
    print(f"Wrote: {args.out}")

if __name__ == "__main__":
    main()
