#!/usr/bin/env python3
import argparse
import csv

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
    toks = label.strip().split()
    if len(toks) < 2 or len(toks) > 5:
        return False
    bad = {
        "university", "school", "church", "city", "county", "province", "river",
        "lake", "mount", "company", "journal", "film", "album", "song", "rail",
        "line", "station", "ministry", "hospital", "theory", "newspaper"
    }
    low = label.lower()
    if any(w in low for w in bad):
        return False
    return all(t[:1].isupper() or "." in t for t in toks)

def compatible(yago_label, soa_uri):
    st = semopenalex_type(soa_uri)
    y_person = looks_like_person_label(yago_label)
    if st == "author":
        return y_person
    if y_person and st != "author":
        return False
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top1", required=True)
    ap.add_argument("--out-summary", required=True)
    ap.add_argument("--thresholds", default="0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.55,0.60")
    args = ap.parse_args()

    thresholds = [float(x) for x in args.thresholds.split(",")]
    counts = {t: {"score_pass": 0, "type_pass": 0, "type_fail": 0} for t in thresholds}

    total = 0
    score_min = 999
    score_max = -999

    with open(args.top1, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            total += 1
            score = float(row["embedding_cosine"])
            score_min = min(score_min, score)
            score_max = max(score_max, score)
            is_compat = compatible(row["yago_label"], row["semopenalex_entity"])

            for t in thresholds:
                if score >= t:
                    counts[t]["score_pass"] += 1
                    if is_compat:
                        counts[t]["type_pass"] += 1
                    else:
                        counts[t]["type_fail"] += 1

            if total % 500000 == 0:
                print(f"processed={total:,}", flush=True)

    with open(args.out_summary, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out, delimiter="\t")
        w.writerow([
            "threshold",
            "total_top1",
            "score_pass",
            "type_pass",
            "type_fail",
            "score_pass_pct",
            "type_pass_pct_of_total",
            "type_fail_pct_of_score_pass",
            "score_min",
            "score_max"
        ])

        for t in thresholds:
            score_pass = counts[t]["score_pass"]
            type_pass = counts[t]["type_pass"]
            type_fail = counts[t]["type_fail"]

            w.writerow([
                t,
                total,
                score_pass,
                type_pass,
                type_fail,
                f"{score_pass / total:.6f}",
                f"{type_pass / total:.6f}",
                f"{type_fail / max(score_pass, 1):.6f}",
                f"{score_min:.8f}",
                f"{score_max:.8f}",
            ])

    print(f"Done. Total={total:,}")
    print(f"Score range: {score_min:.8f} to {score_max:.8f}")
    print(f"Wrote: {args.out_summary}")

if __name__ == "__main__":
    main()
