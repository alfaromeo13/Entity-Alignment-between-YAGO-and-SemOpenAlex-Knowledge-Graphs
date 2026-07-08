#!/usr/bin/env python3
"""Summarize stratified human judgments with weighted precision estimates."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

VERDICTS = {"correct", "incorrect", "uncertain"}
ERROR_CATEGORIES = {
    "name_ambiguity",
    "incomplete_metadata",
    "missing_neighbors",
    "ontology_mismatch",
    "type_mismatch",
    "noisy_source_data",
    "other",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def wilson(successes: float, n: float, z: float = 1.95996398454) -> tuple[float, float]:
    if n <= 0:
        return (math.nan, math.nan)
    p = successes / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def summarize_group(rows: list[dict[str, str]]) -> dict[str, float | int]:
    decided = [row for row in rows if row["verdict"] in {"correct", "incorrect"}]
    weights = [float(row["survey_weight"]) for row in decided]
    correct_weight = sum(
        weight for row, weight in zip(decided, weights) if row["verdict"] == "correct"
    )
    total_weight = sum(weights)
    estimate = correct_weight / total_weight if total_weight else math.nan
    effective_n = (
        total_weight * total_weight / sum(weight * weight for weight in weights)
        if weights
        else 0.0
    )
    low, high = wilson(estimate * effective_n, effective_n)
    return {
        "annotations": len(rows),
        "decided": len(decided),
        "uncertain": sum(row["verdict"] == "uncertain" for row in rows),
        "weighted_precision": estimate,
        "ci95_low_approx": low,
        "ci95_high_approx": high,
        "kish_effective_n": effective_n,
    }


def json_safe(value: object) -> object:
    """Replace non-finite floats with JSON null recursively."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--annotations", required=True, nargs="+", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    key_rows = read_tsv(args.key)
    key = {row["annotation_id"]: row for row in key_rows}
    if len(key) != len(key_rows):
        raise SystemExit("The key contains duplicate annotation_id values")

    by_annotator: dict[str, dict[str, str]] = {}
    merged: list[dict[str, str]] = []
    errors: list[str] = []
    for path in args.annotations:
        judgments: dict[str, str] = {}
        for line, annotation in enumerate(read_tsv(path), start=2):
            identifier = annotation.get("annotation_id", "")
            verdict = annotation.get("verdict", "").strip().lower()
            category = annotation.get("error_category", "").strip().lower()
            if not verdict:
                continue
            if identifier not in key:
                errors.append(f"{path}:{line}: unknown annotation_id {identifier!r}")
                continue
            if verdict not in VERDICTS:
                errors.append(f"{path}:{line}: invalid verdict {verdict!r}")
                continue
            if verdict == "incorrect" and category not in ERROR_CATEGORIES:
                errors.append(
                    f"{path}:{line}: incorrect verdict requires a valid error_category"
                )
                continue
            if verdict != "incorrect" and category:
                errors.append(
                    f"{path}:{line}: error_category is only valid for incorrect verdicts"
                )
                continue
            if identifier in judgments:
                errors.append(f"{path}:{line}: duplicate annotation_id {identifier}")
                continue
            judgments[identifier] = verdict
            row = {**key[identifier], **annotation}
            row["verdict"] = verdict
            row["error_category"] = category
            row["_sheet"] = path.name
            merged.append(row)
        by_annotator[path.name] = judgments

    if errors:
        raise SystemExit("Invalid annotations:\n" + "\n".join(errors[:50]))
    if not args.allow_incomplete:
        incomplete = [
            f"{name}: {len(judgments)}/{len(key)}"
            for name, judgments in by_annotator.items()
            if len(judgments) != len(key)
        ]
        if incomplete:
            raise SystemExit(
                "Incomplete annotation sheets (use --allow-incomplete only for an "
                "interim report):\n" + "\n".join(incomplete)
            )
    if not merged:
        raise SystemExit("No completed judgments were found")

    # Each independently completed sheet contributes one judgment. With
    # multiple sheets this estimates average annotator judgment; agreement is
    # reported separately rather than silently resolving disagreements.
    dimensions = {
        "overall": lambda row: "all",
        "entity_type": lambda row: row["semopenalex_uri_type"],
        "source": lambda row: row["source_group"],
        "score_band": lambda row: row["score_band"],
    }
    metric_rows = []
    report: dict[str, object] = {}
    for dimension, getter in dimensions.items():
        groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in merged:
            groups[getter(row)].append(row)
        summaries = {group: summarize_group(rows) for group, rows in sorted(groups.items())}
        report[dimension] = summaries
        for group, summary in summaries.items():
            metric_rows.append({"dimension": dimension, "group": group, **summary})

    category_weight = Counter()
    for row in merged:
        if row["verdict"] == "incorrect":
            category_weight[row["error_category"]] += float(row["survey_weight"])
    category_total = sum(category_weight.values())
    error_summary = [
        {
            "error_category": category,
            "weighted_count": weight,
            "weighted_share_of_errors": weight / category_total if category_total else math.nan,
        }
        for category, weight in category_weight.most_common()
    ]
    report["error_categories"] = error_summary

    agreement = []
    names = list(by_annotator)
    for index, left_name in enumerate(names):
        for right_name in names[index + 1 :]:
            left, right = by_annotator[left_name], by_annotator[right_name]
            overlap = sorted(set(left) & set(right))
            overlap = [
                identifier
                for identifier in overlap
                if left[identifier] != "uncertain" and right[identifier] != "uncertain"
            ]
            if not overlap:
                continue
            observed = sum(left[i] == right[i] for i in overlap) / len(overlap)
            left_correct = sum(left[i] == "correct" for i in overlap) / len(overlap)
            right_correct = sum(right[i] == "correct" for i in overlap) / len(overlap)
            expected = left_correct * right_correct + (1 - left_correct) * (1 - right_correct)
            kappa = (observed - expected) / (1 - expected) if expected < 1 else math.nan
            agreement.append(
                {
                    "annotator_1": left_name,
                    "annotator_2": right_name,
                    "overlap_decided": len(overlap),
                    "raw_agreement": observed,
                    "cohen_kappa": kappa,
                }
            )
    report["inter_annotator_agreement"] = agreement
    report["notes"] = [
        "Precision excludes uncertain judgments; uncertain counts are reported.",
        "Intervals are approximate 95% Wilson intervals using Kish effective sample size.",
        "ABC score bands show empirical reliability; ABC is not assumed to be a probability.",
    ]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "validation_summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(json_safe(report), handle, indent=2, ensure_ascii=False, allow_nan=False)

    with (args.output_dir / "precision_by_group.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fields = [
            "dimension",
            "group",
            "annotations",
            "decided",
            "uncertain",
            "weighted_precision",
            "ci95_low_approx",
            "ci95_high_approx",
            "kish_effective_n",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(metric_rows)

    with (args.output_dir / "weighted_error_categories.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fields = ["error_category", "weighted_count", "weighted_share_of_errors"]
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(error_summary)

    overall = report["overall"]["all"]  # type: ignore[index]
    print(f"Judgments summarized: {len(merged):,}")
    print(
        "Weighted precision: "
        f"{overall['weighted_precision']:.3%} "
        f"(approx. 95% CI {overall['ci95_low_approx']:.3%}–"
        f"{overall['ci95_high_approx']:.3%})"
    )
    print(f"Summary: {args.output_dir / 'validation_summary.json'}")


if __name__ == "__main__":
    main()
