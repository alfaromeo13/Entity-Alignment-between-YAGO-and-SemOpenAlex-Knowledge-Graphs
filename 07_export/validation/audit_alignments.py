#!/usr/bin/env python3
"""Exhaustively audit machine-testable properties of a final alignment TSV."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

SCORE_COLUMNS = (
    "embedding_cosine",
    "profile_tfidf_score",
    "neighbor_tfidf_score",
    "abc_score",
)
REQUIRED_COLUMNS = (
    "yago_entity",
    "semopenalex_entity",
    "yago_label",
    "semopenalex_label",
    "source",
    "semopenalex_uri_type",
    "abc_score",
)
YAGO_URI = re.compile(r"^https?://yago-knowledge\.org/resource/[^<>\s]+$")
SOA_URI = re.compile(
    r"^https?://semopenalex\.org/"
    r"(author|work|institution|source|publisher|funder|concept|keyword|topic|"
    r"field|subfield|domain|venue)/[^<>\s]+$"
)


def normalize_uri(raw: str) -> tuple[str, bool]:
    """Remove a balanced pair of RDF angle brackets and report balance."""
    value = raw.strip()
    starts = value.startswith("<")
    ends = value.endswith(">")
    if starts and ends:
        return value[1:-1], True
    return value, starts == ends


def score_band(value: float) -> str:
    if value < 0.45:
        return "[0.30,0.45)"
    if value < 0.60:
        return "[0.45,0.60)"
    if value < 0.75:
        return "[0.60,0.75)"
    if value < 0.90:
        return "[0.75,0.90)"
    return "[0.90,1.00]"


def add_example(examples: dict[str, list[dict[str, str]]], issue: str, row: dict[str, str], line: int) -> None:
    bucket = examples.setdefault(issue, [])
    if len(bucket) < 20:
        bucket.append(
            {
                "line": str(line),
                "yago_entity": row.get("yago_entity", ""),
                "semopenalex_entity": row.get("semopenalex_entity", ""),
            }
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    issues = Counter()
    sources = Counter()
    types = Counter()
    bands = Counter()
    examples: dict[str, list[dict[str, str]]] = {}
    seen_pairs: set[tuple[str, str]] = set()
    seen_yago: set[str] = set()
    seen_soa: set[str] = set()
    rows = 0

    with args.input.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames or ())
        if missing:
            raise SystemExit(f"Input is missing required columns: {sorted(missing)}")

        for line, row in enumerate(reader, start=2):
            rows += 1
            yago, yago_brackets_balanced = normalize_uri(row["yago_entity"])
            soa, soa_brackets_balanced = normalize_uri(row["semopenalex_entity"])
            pair = (yago, soa)

            if pair in seen_pairs:
                issues["duplicate_pair"] += 1
                add_example(examples, "duplicate_pair", row, line)
            else:
                seen_pairs.add(pair)
            if yago in seen_yago:
                issues["duplicate_yago_assignment"] += 1
                add_example(examples, "duplicate_yago_assignment", row, line)
            else:
                seen_yago.add(yago)
            if soa in seen_soa:
                issues["duplicate_semopenalex_assignment"] += 1
                add_example(examples, "duplicate_semopenalex_assignment", row, line)
            else:
                seen_soa.add(soa)

            if not yago_brackets_balanced or not YAGO_URI.fullmatch(yago):
                issues["malformed_yago_uri"] += 1
                add_example(examples, "malformed_yago_uri", row, line)
            soa_match = SOA_URI.fullmatch(soa) if soa_brackets_balanced else None
            if soa_match is None:
                issues["malformed_semopenalex_uri"] += 1
                add_example(examples, "malformed_semopenalex_uri", row, line)
            elif soa_match.group(1) != row["semopenalex_uri_type"].strip():
                issues["semopenalex_uri_type_mismatch"] += 1
                add_example(examples, "semopenalex_uri_type_mismatch", row, line)

            for column in REQUIRED_COLUMNS:
                if not row.get(column, "").strip():
                    issue = f"missing_{column}"
                    issues[issue] += 1
                    add_example(examples, issue, row, line)

            parsed_abc = None
            for column in SCORE_COLUMNS:
                raw = row.get(column, "").strip()
                try:
                    value = float(raw)
                except ValueError:
                    issues[f"invalid_{column}"] += 1
                    add_example(examples, f"invalid_{column}", row, line)
                    continue
                if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                    issues[f"out_of_range_{column}"] += 1
                    add_example(examples, f"out_of_range_{column}", row, line)
                if column == "abc_score":
                    parsed_abc = value

            sources[row.get("source", "") or "(missing)"] += 1
            types[row.get("semopenalex_uri_type", "") or "(missing)"] += 1
            if parsed_abc is not None and math.isfinite(parsed_abc):
                bands[score_band(parsed_abc)] += 1

    report = {
        "input": str(args.input),
        "rows_audited": rows,
        "unique_pairs": len(seen_pairs),
        "unique_yago_entities": len(seen_yago),
        "unique_semopenalex_entities": len(seen_soa),
        "issue_counts": dict(sorted(issues.items())),
        "source_counts": dict(sorted(sources.items())),
        "type_counts": dict(sorted(types.items())),
        "abc_score_band_counts": dict(bands),
        "interpretation": (
            "Machine-testable integrity audit only; zero issues does not establish "
            "semantic correctness or precision."
        ),
    }
    with (args.output_dir / "audit_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    with (args.output_dir / "audit_issue_examples.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fields = ["issue", "line", "yago_entity", "semopenalex_entity"]
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for issue in sorted(examples):
            for example in examples[issue]:
                writer.writerow({"issue": issue, **example})

    print(f"Audited rows: {rows:,}")
    print(f"Integrity issue instances: {sum(issues.values()):,}")
    print(f"Report: {args.output_dir / 'audit_report.json'}")


if __name__ == "__main__":
    main()
