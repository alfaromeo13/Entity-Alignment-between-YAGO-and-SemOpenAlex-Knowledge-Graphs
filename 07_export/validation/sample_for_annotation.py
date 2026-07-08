#!/usr/bin/env python3
"""Create a reproducible, blinded, stratified alignment annotation sample."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

KEY_COLUMNS = [
    "annotation_id",
    "yago_entity",
    "semopenalex_entity",
    "yago_label",
    "semopenalex_label",
    "semopenalex_uri_type",
    "yago_profile_type",
    "source",
    "confidence_tier",
    "embedding_cosine",
    "profile_tfidf_score",
    "neighbor_tfidf_score",
    "abc_score",
    "score_band",
    "source_group",
    "stratum",
    "population_stratum_size",
    "sample_stratum_size",
    "inclusion_probability",
    "survey_weight",
]
ANNOTATION_COLUMNS = [
    "annotation_id",
    "yago_entity",
    "semopenalex_entity",
    "yago_url",
    "semopenalex_url",
    "yago_label",
    "semopenalex_label",
    "semopenalex_uri_type",
    "verdict",
    "error_category",
    "annotator",
    "evidence_url_1",
    "evidence_url_2",
    "notes",
]


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


def source_group(source: str) -> str:
    return "strict_proxy" if source == "strict_proxy_gold" else "ranked_ambiguous"


def bare_uri(value: str) -> str:
    value = value.strip()
    return value[1:-1] if value.startswith("<") and value.endswith(">") else value


def allocate(counts: Counter[str], total: int, minimum: int) -> dict[str, int]:
    if total > sum(counts.values()):
        total = sum(counts.values())
    strata = sorted(counts)
    allocation = {key: min(minimum, counts[key]) for key in strata}
    if sum(allocation.values()) > total:
        allocation = {key: 0 for key in strata}

    remaining = total - sum(allocation.values())
    while remaining:
        capacity = {key: counts[key] - allocation[key] for key in strata}
        active = [key for key in strata if capacity[key] > 0]
        if not active:
            break
        denominator = sum(capacity[key] for key in active)
        quotas = {key: remaining * capacity[key] / denominator for key in active}
        additions = {
            key: min(capacity[key], int(quotas[key])) for key in active
        }
        assigned = sum(additions.values())
        if assigned == 0:
            ranked = sorted(
                active,
                key=lambda key: (quotas[key] - int(quotas[key]), capacity[key], key),
                reverse=True,
            )
            additions[ranked[0]] = 1
            assigned = 1
        for key, value in additions.items():
            allocation[key] += value
        remaining -= assigned
    return allocation


def annotation_id(row: dict[str, str], seed: int) -> str:
    payload = (
        f"{seed}\0{row['yago_entity']}\0{row['semopenalex_entity']}"
    ).encode("utf-8")
    return "A-" + hashlib.sha256(payload).hexdigest()[:12].upper()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--sample-size", type=int, default=500)
    parser.add_argument("--minimum-per-stratum", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260629)
    args = parser.parse_args()
    if args.sample_size < 1 or args.minimum_per_stratum < 0:
        raise SystemExit("Sample size must be positive and minimum non-negative")

    rng = random.Random(args.seed)
    counts: Counter[str] = Counter()
    reservoirs: dict[str, list[dict[str, str]]] = defaultdict(list)

    with args.input.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {
            "yago_entity",
            "semopenalex_entity",
            "yago_label",
            "semopenalex_label",
            "semopenalex_uri_type",
            "source",
            "abc_score",
        }
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise SystemExit(f"Input is missing required columns: {sorted(missing)}")

        for row in reader:
            band = score_band(float(row["abc_score"]))
            group = source_group(row["source"])
            stratum = "|".join(
                (row.get("semopenalex_uri_type") or "unknown", group, band)
            )
            counts[stratum] += 1
            bucket = reservoirs[stratum]
            # Keeping at most the requested total per stratum is sufficient for
            # any later allocation and avoids retaining the 2M-row population.
            if len(bucket) < args.sample_size:
                bucket.append(dict(row))
            else:
                replacement = rng.randrange(counts[stratum])
                if replacement < args.sample_size:
                    bucket[replacement] = dict(row)

    allocation = allocate(counts, args.sample_size, args.minimum_per_stratum)
    selected: list[dict[str, str]] = []
    for stratum in sorted(allocation):
        sample_n = allocation[stratum]
        population_n = counts[stratum]
        rows = rng.sample(reservoirs[stratum], sample_n)
        for row in rows:
            row["annotation_id"] = annotation_id(row, args.seed)
            row["yago_url"] = bare_uri(row["yago_entity"])
            row["semopenalex_url"] = bare_uri(row["semopenalex_entity"])
            row["score_band"] = stratum.rsplit("|", 1)[-1]
            row["source_group"] = stratum.split("|")[1]
            row["stratum"] = stratum
            row["population_stratum_size"] = str(population_n)
            row["sample_stratum_size"] = str(sample_n)
            row["inclusion_probability"] = f"{sample_n / population_n:.12g}"
            row["survey_weight"] = f"{population_n / sample_n:.12g}"
            selected.append(row)
    rng.shuffle(selected)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    key_path = args.output_dir / "sample_key.tsv"
    with key_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=KEY_COLUMNS, delimiter="\t", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(selected)

    annotation_path = args.output_dir / "annotation.tsv"
    with annotation_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=ANNOTATION_COLUMNS, delimiter="\t", extrasaction="ignore"
        )
        writer.writeheader()
        for row in selected:
            writer.writerow(row)

    manifest = {
        "input": str(args.input),
        "seed": args.seed,
        "requested_sample_size": args.sample_size,
        "actual_sample_size": len(selected),
        "minimum_per_stratum": args.minimum_per_stratum,
        "population_size": sum(counts.values()),
        "stratification": ["semopenalex_uri_type", "source_group", "abc_score_band"],
        "population_stratum_counts": dict(sorted(counts.items())),
        "sample_stratum_counts": dict(sorted(allocation.items())),
        "verdict_values": ["correct", "incorrect", "uncertain"],
        "error_category_values": [
            "name_ambiguity",
            "incomplete_metadata",
            "missing_neighbors",
            "ontology_mismatch",
            "type_mismatch",
            "noisy_source_data",
            "other",
        ],
    }
    with (args.output_dir / "sampling_manifest.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)

    print(f"Population rows scanned: {sum(counts.values()):,}")
    print(f"Non-empty strata: {len(counts):,}")
    print(f"Sample rows: {len(selected):,}")
    print(f"Annotation sheet: {annotation_path}")
    print(f"Blinded key: {key_path}")


if __name__ == "__main__":
    main()
