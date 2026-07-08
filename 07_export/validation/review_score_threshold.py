#!/usr/bin/env python3
"""Extract and summarize non-proxy rows removed by an ABC score threshold."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

NUMERIC_COLUMNS = (
    "embedding_cosine",
    "profile_tfidf_score",
    "neighbor_tfidf_score",
    "combined_score",
    "abc_score",
    "token_jaccard",
    "semopenalex_label_freq",
    "yago_candidate_count",
)


def quantiles(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    ordered = sorted(values)

    def value_at(fraction: float) -> float:
        index = round(fraction * (len(ordered) - 1))
        return ordered[index]

    return {
        "minimum": ordered[0],
        "p10": value_at(0.10),
        "median": value_at(0.50),
        "p90": value_at(0.90),
        "maximum": ordered[-1],
        "mean": sum(ordered) / len(ordered),
    }


def stable_key(row: dict[str, str], seed: int) -> bytes:
    text = (
        f"{seed}\0{row['yago_entity']}\0{row['semopenalex_entity']}"
    )
    return hashlib.blake2b(text.encode("utf-8"), digest_size=16).digest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--upper-threshold", type=float, default=0.30)
    parser.add_argument("--all-output", required=True, type=Path)
    parser.add_argument("--sample-output", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    parser.add_argument("--sample-size", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260702)
    args = parser.parse_args()

    removed: list[dict[str, str]] = []
    type_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()
    evidence_counts: Counter[str] = Counter()
    numeric = {column: [] for column in NUMERIC_COLUMNS}
    zero_neighbor = 0
    exact_token_overlap = 0

    with args.input.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        for row in reader:
            if row.get("source") == "strict_proxy_gold":
                continue
            score = float(row.get("abc_score") or 0)
            if score >= args.upper_threshold:
                continue
            removed.append(row)
            type_counts[row.get("semopenalex_uri_type", "")] += 1
            confidence_counts[row.get("confidence_tier", "")] += 1
            evidence_counts[row.get("yago_type_evidence", "")] += 1
            if float(row.get("neighbor_tfidf_score") or 0) == 0:
                zero_neighbor += 1
            if float(row.get("token_jaccard") or 0) == 1:
                exact_token_overlap += 1
            for column in NUMERIC_COLUMNS:
                numeric[column].append(float(row.get(column) or 0))

    args.all_output.parent.mkdir(parents=True, exist_ok=True)
    args.sample_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    with args.all_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(removed)

    sample = sorted(
        removed,
        key=lambda row: stable_key(row, args.seed),
    )[: args.sample_size]
    with args.sample_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(sample)

    report = {
        "input": str(args.input),
        "upper_threshold_exclusive": args.upper_threshold,
        "removed_rows": len(removed),
        "sample_rows": len(sample),
        "sample_seed": args.seed,
        "semopenalex_type_counts": dict(type_counts.most_common()),
        "confidence_tier_counts": dict(confidence_counts.most_common()),
        "yago_type_evidence_counts": dict(evidence_counts.most_common()),
        "zero_neighbor_score_rows": zero_neighbor,
        "zero_neighbor_score_share": (
            zero_neighbor / len(removed) if removed else 0
        ),
        "token_jaccard_one_rows": exact_token_overlap,
        "token_jaccard_one_share": (
            exact_token_overlap / len(removed) if removed else 0
        ),
        "numeric_summaries": {
            column: quantiles(values) for column, values in numeric.items()
        },
        "interpretation": (
            "Boundary evidence review only. Membership below the score "
            "threshold does not establish that an alignment is incorrect."
        ),
    }
    with args.summary_output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    print(f"Removed rows: {len(removed):,}")
    print(f"Wrote all rows: {args.all_output}")
    print(f"Wrote sample: {args.sample_output}")
    print(f"Wrote summary: {args.summary_output}")


if __name__ == "__main__":
    main()
