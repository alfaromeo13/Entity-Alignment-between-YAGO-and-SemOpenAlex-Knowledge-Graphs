#!/usr/bin/env python3
"""Apply taxonomy-aware compatibility to the Stage 05 pre-profile file."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from type_system import compatibility_state, semopenalex_type

PROFILE_COLUMNS = [
    "yago_profile_type",
    "yago_profile_types",
    "yago_type_status",
    "yago_type_evidence",
    "yago_type_confidence",
    "yago_rdf_type_count",
    "yago_rdf_types",
    "yago_predicate_count",
    "yago_top_predicates",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--profiles", required=True, type=Path)
    parser.add_argument("--accepted", required=True, type=Path)
    parser.add_argument("--rejected", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument(
        "--unresolved-policy",
        required=True,
        choices=("keep", "reject"),
        help="Whether typed-but-unmapped and untyped entities survive the filter.",
    )
    args = parser.parse_args()

    alignments = pd.read_csv(args.input, sep="\t", dtype=str, low_memory=False)
    profiles = pd.read_csv(args.profiles, sep="\t", dtype=str, low_memory=False)
    expected = {"yago_entity", *PROFILE_COLUMNS}
    missing = expected - set(profiles.columns)
    if missing:
        raise SystemExit(f"Missing profile columns: {sorted(missing)}")

    duplicate_profiles = int(profiles["yago_entity"].duplicated().sum())
    if duplicate_profiles:
        raise SystemExit(f"Profile file has {duplicate_profiles:,} duplicate entities")

    alignments = alignments.merge(
        profiles[["yago_entity", *PROFILE_COLUMNS]],
        on="yago_entity",
        how="left",
        validate="many_to_one",
        indicator="_profile_join",
    )
    missing_profile = alignments["_profile_join"].eq("left_only")
    alignments.loc[missing_profile, "yago_profile_type"] = "untyped"
    alignments.loc[missing_profile, "yago_profile_types"] = "untyped"
    alignments.loc[missing_profile, "yago_type_status"] = "untyped"
    alignments.loc[missing_profile, "yago_type_evidence"] = "no_profile_row"
    alignments.loc[missing_profile, "yago_type_confidence"] = "0.0"
    for column in (
        "yago_rdf_type_count",
        "yago_rdf_types",
        "yago_predicate_count",
        "yago_top_predicates",
    ):
        alignments.loc[missing_profile, column] = (
            "0" if column.endswith("_count") else ""
        )
    alignments = alignments.drop(columns="_profile_join")

    if "semopenalex_type" in alignments.columns:
        inferred = alignments["semopenalex_entity"].map(semopenalex_type)
        supplied = alignments["semopenalex_type"].fillna("").str.lower()
        alignments["semopenalex_uri_type"] = supplied.where(
            supplied.ne(""),
            inferred,
        )
    else:
        alignments["semopenalex_uri_type"] = alignments[
            "semopenalex_entity"
        ].map(semopenalex_type)

    alignments["type_compatibility_v2"] = [
        compatibility_state(profile_types, status, soa_type)
        for profile_types, status, soa_type in zip(
            alignments["yago_profile_types"],
            alignments["yago_type_status"],
            alignments["semopenalex_uri_type"],
        )
    ]
    alignments["type_filter_policy_v2"] = args.unresolved_policy

    if (alignments["yago_profile_type"] == "unknown").any():
        raise RuntimeError("Literal unknown survived taxonomy-aware classification")

    reject_mask = alignments["type_compatibility_v2"].eq("incompatible")
    if args.unresolved_policy == "reject":
        reject_mask |= alignments["type_compatibility_v2"].eq("unresolved")

    accepted = alignments.loc[~reject_mask].copy()
    rejected = alignments.loc[reject_mask].copy()
    for path in (args.accepted, args.rejected, args.summary):
        path.parent.mkdir(parents=True, exist_ok=True)
    accepted.to_csv(args.accepted, sep="\t", index=False)
    rejected.to_csv(args.rejected, sep="\t", index=False)

    pair_counts = Counter(
        zip(
            alignments["yago_profile_type"],
            alignments["semopenalex_uri_type"],
            alignments["type_compatibility_v2"],
        )
    )
    summary = {
        "input": str(args.input),
        "profiles": str(args.profiles),
        "unresolved_policy": args.unresolved_policy,
        "input_rows": len(alignments),
        "accepted_rows": len(accepted),
        "rejected_rows": len(rejected),
        "missing_profile_rows": int(missing_profile.sum()),
        "literal_unknown_rows": 0,
        "compatibility_counts": alignments[
            "type_compatibility_v2"
        ].value_counts().sort_index().to_dict(),
        "status_counts": alignments[
            "yago_type_status"
        ].value_counts().sort_index().to_dict(),
        "evidence_counts": alignments[
            "yago_type_evidence"
        ].value_counts().sort_index().to_dict(),
        "type_pair_counts": [
            {
                "yago_profile_type": yago_type,
                "semopenalex_uri_type": soa_type,
                "compatibility": state,
                "count": count,
            }
            for (yago_type, soa_type, state), count in pair_counts.most_common()
        ],
    }
    with args.summary.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print(f"Input rows: {len(alignments):,}")
    print(f"Accepted rows: {len(accepted):,}")
    print(f"Rejected rows: {len(rejected):,}")
    print(f"Missing profile rows: {int(missing_profile.sum()):,}")
    print(f"Wrote: {args.accepted}")
    print(f"Wrote: {args.rejected}")
    print(f"Wrote: {args.summary}")


if __name__ == "__main__":
    main()
