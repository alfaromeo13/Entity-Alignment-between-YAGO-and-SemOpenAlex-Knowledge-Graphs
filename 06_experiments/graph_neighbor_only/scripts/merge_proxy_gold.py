#!/usr/bin/env python3
"""Type-filter and greedily merge proxy-gold with taxonomy-aware top-1 pairs."""

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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proxy-gold", required=True, type=Path)
    parser.add_argument("--top1", required=True, type=Path)
    parser.add_argument("--yago-profiles", required=True, type=Path)
    parser.add_argument(
        "--unresolved-policy",
        required=True,
        choices=("keep", "reject"),
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--rejected-proxy", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument(
        "--ranked-source",
        default="embedding_type_text_top1_v2",
        help="Source label assigned to accepted non-proxy top-1 rows.",
    )
    parser.add_argument(
        "--proxy-evidence-column",
        choices=("profile_tfidf_score", "neighbor_tfidf_score"),
        default="profile_tfidf_score",
        help="Evidence column fixed to 1.0 for exact-label proxy rows.",
    )
    args = parser.parse_args()

    proxy_input = pd.read_csv(
        args.proxy_gold, sep="\t", dtype=str, low_memory=False
    )
    top1 = pd.read_csv(args.top1, sep="\t", dtype=str, low_memory=False)
    profiles = pd.read_csv(
        args.yago_profiles, sep="\t", dtype=str, low_memory=False
    )
    if profiles["yago_entity"].duplicated().any():
        raise SystemExit("YAGO profile file contains duplicate entities")
    proxy = proxy_input.merge(
        profiles[["yago_entity", *PROFILE_COLUMNS]],
        on="yago_entity",
        how="left",
        validate="many_to_one",
        indicator="_profile_join",
    )
    missing_profile = proxy["_profile_join"].eq("left_only")
    proxy.loc[missing_profile, "yago_profile_type"] = "untyped"
    proxy.loc[missing_profile, "yago_profile_types"] = "untyped"
    proxy.loc[missing_profile, "yago_type_status"] = "untyped"
    proxy.loc[missing_profile, "yago_type_evidence"] = "no_profile_row"
    proxy.loc[missing_profile, "yago_type_confidence"] = "0.0"
    for column in (
        "yago_rdf_type_count",
        "yago_rdf_types",
        "yago_predicate_count",
        "yago_top_predicates",
    ):
        proxy.loc[missing_profile, column] = (
            "0" if column.endswith("_count") else ""
        )
    proxy = proxy.drop(columns="_profile_join")

    proxy["source"] = "strict_proxy_gold"
    proxy["source_priority_v2"] = 0
    proxy["embedding_cosine"] = "1.00000000"
    proxy[args.proxy_evidence_column] = "1.00000000"
    proxy["combined_score"] = "1.00000000"
    proxy["semopenalex_uri_type"] = proxy["semopenalex_entity"].map(
        semopenalex_type
    )
    proxy["type_compatibility_v2"] = [
        compatibility_state(profile_types, status, soa_type)
        for profile_types, status, soa_type in zip(
            proxy["yago_profile_types"],
            proxy["yago_type_status"],
            proxy["semopenalex_uri_type"],
        )
    ]
    proxy["type_filter_policy_v2"] = args.unresolved_policy
    proxy_reject_mask = proxy["type_compatibility_v2"].eq("incompatible")
    if args.unresolved_policy == "reject":
        proxy_reject_mask |= proxy["type_compatibility_v2"].eq("unresolved")
    rejected_proxy = proxy.loc[proxy_reject_mask].copy()
    proxy = proxy.loc[~proxy_reject_mask].copy()

    top1["source"] = args.ranked_source
    top1["source_priority_v2"] = 1
    allowed_top1_states = (
        {"compatible", "unresolved"}
        if args.unresolved_policy == "keep"
        else {"compatible"}
    )
    unexpected_top1 = ~top1["type_compatibility_v2"].isin(
        allowed_top1_states
    )
    if unexpected_top1.any():
        raise SystemExit(
            f"Top1 contains {int(unexpected_top1.sum()):,} rows that violate "
            f"the {args.unresolved_policy!r} policy"
        )

    columns = list(dict.fromkeys([*proxy.columns, *top1.columns]))
    for column in columns:
        if column not in proxy:
            proxy[column] = ""
        if column not in top1:
            top1[column] = ""
    merged = pd.concat(
        [proxy[columns], top1[columns]],
        ignore_index=True,
    )
    merged["_combined_score_num"] = pd.to_numeric(
        merged["combined_score"], errors="coerce"
    ).fillna(0.0)
    merged = merged.sort_values(
        [
            "source_priority_v2",
            "_combined_score_num",
            "yago_entity",
            "semopenalex_entity",
        ],
        ascending=[True, False, True, True],
        kind="mergesort",
    )

    selected_indices: list[int] = []
    used_yago: set[str] = set()
    used_soa: set[str] = set()
    for index, yago_entity, soa_entity in merged[
        ["yago_entity", "semopenalex_entity"]
    ].itertuples():
        if yago_entity in used_yago or soa_entity in used_soa:
            continue
        selected_indices.append(index)
        used_yago.add(yago_entity)
        used_soa.add(soa_entity)

    output = merged.loc[selected_indices].drop(columns="_combined_score_num")
    if output["yago_entity"].duplicated().any():
        raise RuntimeError("YAGO one-to-one invariant failed")
    if output["semopenalex_entity"].duplicated().any():
        raise RuntimeError("SemOpenAlex one-to-one invariant failed")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.rejected_proxy.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, sep="\t", index=False)
    rejected_proxy.to_csv(args.rejected_proxy, sep="\t", index=False)

    source_counts = output["source"].value_counts().sort_index().to_dict()
    summary = {
        "unresolved_policy": args.unresolved_policy,
        "proxy_input_rows": len(proxy_input),
        "proxy_eligible_rows": len(proxy),
        "proxy_rejected_by_type_rows": len(rejected_proxy),
        "proxy_missing_profile_rows": int(missing_profile.sum()),
        "proxy_input_compatibility_counts": pd.concat(
            [proxy, rejected_proxy], ignore_index=True
        )["type_compatibility_v2"].value_counts().sort_index().to_dict(),
        "proxy_eligible_unique_yago": int(proxy["yago_entity"].nunique()),
        "proxy_eligible_unique_semopenalex": int(
            proxy["semopenalex_entity"].nunique()
        ),
        "top1_input_rows": len(top1),
        "final_one_to_one_rows": len(output),
        "final_unique_yago": int(output["yago_entity"].nunique()),
        "final_unique_semopenalex": int(
            output["semopenalex_entity"].nunique()
        ),
        "final_source_counts": source_counts,
        "eligible_proxy_priority_explicit": True,
        "ranked_source": args.ranked_source,
        "proxy_evidence_column": args.proxy_evidence_column,
    }
    with args.summary.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2), flush=True)
    print(f"Wrote: {args.output}")
    print(f"Wrote: {args.rejected_proxy}")
    print(f"Wrote: {args.summary}")


if __name__ == "__main__":
    main()
