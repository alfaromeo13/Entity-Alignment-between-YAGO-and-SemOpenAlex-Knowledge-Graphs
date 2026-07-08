#!/usr/bin/env python3
"""Rerank Stage 06 A+B candidates with taxonomy-aware compatibility."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

STAGE05_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / "05_entity_alignment/final_alignment/scripts"
)
sys.path.insert(0, str(STAGE05_SCRIPTS))

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


def write_variant(
    dataframe: pd.DataFrame,
    policy: str,
    min_score: float,
    output_all: Path,
    output_top1: Path,
) -> dict[str, int]:
    keep_states = (
        {"compatible", "unresolved"}
        if policy == "permissive"
        else {"compatible"}
    )
    ranked = dataframe[
        dataframe["type_compatibility_v2"].isin(keep_states)
        & dataframe["combined_score"].ge(min_score)
    ].copy()
    ranked["type_filter_policy_v2"] = policy
    ranked = ranked.sort_values(
        [
            "yago_entity",
            "combined_score",
            "embedding_cosine",
            "profile_tfidf_score",
            "semopenalex_entity",
        ],
        ascending=[True, False, False, False, True],
        kind="mergesort",
    )
    top1 = ranked.groupby("yago_entity", sort=False, as_index=False).head(1)
    output_all.parent.mkdir(parents=True, exist_ok=True)
    output_top1.parent.mkdir(parents=True, exist_ok=True)
    ranked.to_csv(output_all, sep="\t", index=False)
    top1.to_csv(output_top1, sep="\t", index=False)
    return {
        "ranked_rows": len(ranked),
        "top1_rows": len(top1),
        "ranked_unresolved_rows": int(
            ranked["type_compatibility_v2"].eq("unresolved").sum()
        ),
        "top1_unresolved_rows": int(
            top1["type_compatibility_v2"].eq("unresolved").sum()
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--profile-scores", required=True, type=Path)
    parser.add_argument("--yago-profiles", required=True, type=Path)
    parser.add_argument("--permissive-all", required=True, type=Path)
    parser.add_argument("--permissive-top1", required=True, type=Path)
    parser.add_argument("--strict-all", required=True, type=Path)
    parser.add_argument("--strict-top1", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--min-combined-score", type=float, default=0.25)
    parser.add_argument("--embedding-weight", type=float, default=0.65)
    parser.add_argument("--profile-weight", type=float, default=0.35)
    args = parser.parse_args()

    print("Loading candidates...", flush=True)
    candidates = pd.read_csv(
        args.candidates, sep="\t", dtype=str, low_memory=False
    )
    scores = pd.read_csv(
        args.profile_scores, sep="\t", dtype=str, low_memory=False
    )
    profiles = pd.read_csv(
        args.yago_profiles, sep="\t", dtype=str, low_memory=False
    )
    pair_keys = ["yago_entity", "semopenalex_entity"]
    if scores.duplicated(pair_keys).any():
        raise SystemExit("Profile-score file contains duplicate entity pairs")
    if profiles["yago_entity"].duplicated().any():
        raise SystemExit("YAGO profile file contains duplicate entities")

    dataframe = candidates.merge(
        scores[[*pair_keys, "profile_tfidf_score"]],
        on=pair_keys,
        how="left",
        validate="one_to_one",
        indicator="_score_join",
    )
    missing_score_rows = int(dataframe["_score_join"].eq("left_only").sum())
    dataframe = dataframe.drop(columns="_score_join")
    dataframe = dataframe.merge(
        profiles[["yago_entity", *PROFILE_COLUMNS]],
        on="yago_entity",
        how="left",
        validate="many_to_one",
        indicator="_profile_join",
    )
    missing_profile = dataframe["_profile_join"].eq("left_only")
    missing_profile_rows = int(missing_profile.sum())
    dataframe.loc[missing_profile, "yago_profile_type"] = "untyped"
    dataframe.loc[missing_profile, "yago_profile_types"] = "untyped"
    dataframe.loc[missing_profile, "yago_type_status"] = "untyped"
    dataframe.loc[missing_profile, "yago_type_evidence"] = "no_profile_row"
    dataframe.loc[missing_profile, "yago_type_confidence"] = "0.0"
    for column in (
        "yago_rdf_type_count",
        "yago_rdf_types",
        "yago_predicate_count",
        "yago_top_predicates",
    ):
        dataframe.loc[missing_profile, column] = (
            "0" if column.endswith("_count") else ""
        )
    dataframe = dataframe.drop(columns="_profile_join")

    dataframe["embedding_cosine"] = pd.to_numeric(
        dataframe["embedding_cosine"], errors="coerce"
    ).fillna(0.0)
    dataframe["profile_tfidf_score"] = pd.to_numeric(
        dataframe["profile_tfidf_score"], errors="coerce"
    ).fillna(0.0)
    dataframe["semopenalex_uri_type"] = dataframe[
        "semopenalex_entity"
    ].map(semopenalex_type)
    dataframe["type_compatibility_v2"] = [
        compatibility_state(profile_types, status, soa_type)
        for profile_types, status, soa_type in zip(
            dataframe["yago_profile_types"],
            dataframe["yago_type_status"],
            dataframe["semopenalex_uri_type"],
        )
    ]
    dataframe["combined_score"] = (
        args.embedding_weight * dataframe["embedding_cosine"]
        + args.profile_weight * dataframe["profile_tfidf_score"]
    )
    if (dataframe["yago_profile_type"] == "unknown").any():
        raise RuntimeError("Literal unknown survived taxonomy-aware classification")

    variants = {
        "permissive": write_variant(
            dataframe,
            "permissive",
            args.min_combined_score,
            args.permissive_all,
            args.permissive_top1,
        ),
        "strict": write_variant(
            dataframe,
            "strict",
            args.min_combined_score,
            args.strict_all,
            args.strict_top1,
        ),
    }
    summary = {
        "candidates": str(args.candidates),
        "profile_scores": str(args.profile_scores),
        "yago_profiles": str(args.yago_profiles),
        "candidate_rows": len(dataframe),
        "candidate_yago_entities": int(dataframe["yago_entity"].nunique()),
        "missing_score_rows_filled_zero": missing_score_rows,
        "missing_profile_rows_explicitly_untyped": missing_profile_rows,
        "literal_unknown_rows": 0,
        "min_combined_score": args.min_combined_score,
        "embedding_weight": args.embedding_weight,
        "profile_weight": args.profile_weight,
        "compatibility_counts": dataframe[
            "type_compatibility_v2"
        ].value_counts().sort_index().to_dict(),
        "status_counts": dataframe[
            "yago_type_status"
        ].value_counts().sort_index().to_dict(),
        "evidence_counts": dataframe[
            "yago_type_evidence"
        ].value_counts().sort_index().to_dict(),
        "variants": variants,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    with args.summary.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
