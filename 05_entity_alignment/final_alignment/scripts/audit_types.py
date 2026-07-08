#!/usr/bin/env python3
"""Audit Stage 05 taxonomy-aware outputs and reject literal ``unknown``."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def counts(dataframe: pd.DataFrame, column: str) -> dict[str, int]:
    if column not in dataframe:
        return {}
    return dataframe[column].fillna("<missing>").value_counts().sort_index().to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    dataframe = pd.read_csv(args.input, sep="\t", dtype=str, low_memory=False)
    type_columns = [
        column
        for column in ("yago_profile_type", "yago_profile_types")
        if column in dataframe
    ]
    literal_unknown = 0
    for column in type_columns:
        literal_unknown += int(
            dataframe[column]
            .fillna("")
            .str.split("|", regex=False)
            .map(lambda values: "unknown" in values)
            .sum()
        )
    if literal_unknown:
        raise SystemExit(
            f"Audit failed: found {literal_unknown:,} literal unknown values"
        )

    unique_yago = (
        int(dataframe["yago_entity"].nunique())
        if "yago_entity" in dataframe
        else None
    )
    unique_semopenalex = (
        int(dataframe["semopenalex_entity"].nunique())
        if "semopenalex_entity" in dataframe
        else None
    )
    duplicate_yago = (
        int(dataframe["yago_entity"].duplicated().sum())
        if "yago_entity" in dataframe
        else None
    )
    duplicate_semopenalex = (
        int(dataframe["semopenalex_entity"].duplicated().sum())
        if "semopenalex_entity" in dataframe
        else None
    )
    if duplicate_yago:
        raise SystemExit(
            f"Audit failed: found {duplicate_yago:,} duplicate YAGO entities"
        )
    if duplicate_semopenalex:
        raise SystemExit(
            "Audit failed: found "
            f"{duplicate_semopenalex:,} duplicate SemOpenAlex entities"
        )

    report: dict[str, object] = {
        "input": str(args.input),
        "rows": len(dataframe),
        "unique_yago_entities": unique_yago,
        "unique_semopenalex_entities": unique_semopenalex,
        "duplicate_yago_entities": duplicate_yago,
        "duplicate_semopenalex_entities": duplicate_semopenalex,
        "literal_unknown_values": 0,
        "type_status_counts": counts(dataframe, "yago_type_status"),
        "type_evidence_counts": counts(dataframe, "yago_type_evidence"),
        "compatibility_counts": counts(dataframe, "type_compatibility_v2"),
        "primary_type_counts": counts(dataframe, "yago_profile_type"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2), flush=True)
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
