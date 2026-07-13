#!/usr/bin/env python3
"""Alignment-aware neighbor preservation and bridge-topology analysis.

The Stage 06 context files were built by scanning all train/valid/test triples,
but retain at most 40 context features per target entity. This script therefore
computes exact statistics over those stored, capped contexts—not over every
incident edge in the original terabyte-scale graphs.
"""

from __future__ import annotations

import argparse
import ast
import csv
import math
import pickle
import re
from array import array
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
OUT = ROOT / "07_export/visualizations"
FIGURES = OUT / "figures"
FINAL = (
    ROOT
    / "06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/"
    "abc_w060_035_005_t030.tsv"
)
YAGO_CONTEXT = (
    ROOT
    / "06_experiments/graph_neighbor_signal/data/strict/yago_neighbor_context.tsv"
)
SOA_CONTEXT = (
    ROOT
    / "06_experiments/graph_neighbor_signal/data/strict/semopenalex_neighbor_context.tsv"
)
CACHE_DIR = OUT / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE = CACHE_DIR / "structural_validation.pkl"

BLUE = "#2563EB"
GREEN = "#16A34A"
AMBER = "#D97706"
PURPLE = "#7C3AED"
SLATE = "#64748B"
INK = "#0F172A"
LIGHT = "#E2E8F0"


def simple_name(uri: str) -> str:
    uri = str(uri).strip("<>")
    tail = uri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
    return re.sub(r"[^A-Za-z0-9]+", " ", tail).lower().strip()


def add_unique(mapping: dict[str, int], key: str, value: int) -> None:
    previous = mapping.get(key)
    if previous is None:
        mapping[key] = value
    elif previous != value:
        mapping[key] = -1


def parse_context(value: str) -> list[str]:
    value = value.strip()
    if not value:
        return []
    if value.startswith("["):
        parsed = ast.literal_eval(value)
        return [str(item) for item in parsed]
    return value.split()


def load_alignments():
    yago_uri_to_id: dict[str, int] = {}
    soa_uri_to_id: dict[str, int] = {}
    yago_name_to_id: dict[str, int] = {}
    soa_name_to_id: dict[str, int] = {}
    entity_types = []
    source_groups = []

    with FINAL.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for identifier, row in enumerate(reader):
            yago = row["yago_entity"]
            soa = row["semopenalex_entity"]
            yago_uri_to_id[yago] = identifier
            soa_uri_to_id[soa] = identifier
            add_unique(yago_name_to_id, simple_name(yago), identifier)
            add_unique(soa_name_to_id, simple_name(soa), identifier)
            entity_types.append(row.get("semopenalex_uri_type") or "unknown")
            source_groups.append(
                "Strict proxy"
                if row.get("source") == "strict_proxy_gold"
                else "Ranked ambiguous"
            )

    return {
        "count": len(entity_types),
        "yago_uri_to_id": yago_uri_to_id,
        "soa_uri_to_id": soa_uri_to_id,
        "yago_name_to_id": yago_name_to_id,
        "soa_name_to_id": soa_name_to_id,
        "entity_types": entity_types,
        "source_groups": source_groups,
    }


def context_edges(path, uri_to_id, name_to_id):
    edges: set[tuple[int, int]] = set()
    profile_rows = 0
    profiles_with_context = 0
    mapped_neighbor_mentions = 0
    ambiguous_neighbor_mentions = 0
    unmapped_neighbor_mentions = 0

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            identifier = uri_to_id.get(row.get("entity", ""))
            if identifier is None:
                continue
            profile_rows += 1
            tokens = parse_context(row.get("neighbor_context", ""))
            neighbors = [token[4:] for token in tokens if token.startswith("nbr_")]
            if neighbors:
                profiles_with_context += 1
            for name in neighbors:
                neighbor = name_to_id.get(name)
                if neighbor is None:
                    unmapped_neighbor_mentions += 1
                    continue
                if neighbor < 0:
                    ambiguous_neighbor_mentions += 1
                    continue
                if neighbor == identifier:
                    continue
                mapped_neighbor_mentions += 1
                edges.add(
                    (identifier, neighbor)
                    if identifier < neighbor
                    else (neighbor, identifier)
                )

    return edges, {
        "profile_rows": profile_rows,
        "profiles_with_context": profiles_with_context,
        "mapped_neighbor_mentions": mapped_neighbor_mentions,
        "ambiguous_neighbor_mentions": ambiguous_neighbor_mentions,
        "unmapped_neighbor_mentions": unmapped_neighbor_mentions,
        "unique_aligned_neighbor_edges": len(edges),
    }


def adjacency(edges):
    result = defaultdict(set)
    for left, right in edges:
        result[left].add(right)
        result[right].add(left)
    return result


class UnionFind:
    def __init__(self, count: int):
        self.parent = array("i", range(count))
        self.size = array("i", [1]) * count
        self.components = count
        self.largest = 1 if count else 0

    def find(self, value: int) -> int:
        parent = self.parent
        root = value
        while parent[root] != root:
            root = parent[root]
        while parent[value] != value:
            next_value = parent[value]
            parent[value] = root
            value = next_value
        return root

    def union(self, left: int, right: int) -> None:
        left, right = self.find(left), self.find(right)
        if left == right:
            return
        if self.size[left] < self.size[right]:
            left, right = right, left
        self.parent[right] = left
        self.size[left] += self.size[right]
        self.components -= 1
        self.largest = max(self.largest, self.size[left])


def component_summary(count, edge_groups):
    structure = UnionFind(count)
    for edges in edge_groups:
        for left, right in edges:
            structure.union(left, right)
    return {
        "components": structure.components,
        "largest_component_pair_ids": structure.largest,
    }


def jaccard_band(value: float) -> str:
    if value == 0:
        return "0"
    if value <= 0.10:
        return "(0, 0.10]"
    if value <= 0.25:
        return "(0.10, 0.25]"
    if value <= 0.50:
        return "(0.25, 0.50]"
    if value < 1:
        return "(0.50, 1)"
    return "1"


def group_summary(rows, dimension):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[dimension]].append(row)
    result = []
    for group, values in sorted(grouped.items()):
        scores = np.array([row["jaccard"] for row in values])
        result.append(
            {
                "dimension": dimension,
                "group": group,
                "evaluable_pairs": len(values),
                "mean_jaccard": float(scores.mean()),
                "median_jaccard": float(np.median(scores)),
                "pairs_with_shared_neighbor": int((scores > 0).sum()),
                "shared_neighbor_rate": float((scores > 0).mean()),
                "perfect_jaccard_rate": float((scores == 1).mean()),
            }
        )
    return result


def build(refresh=False):
    if CACHE.exists() and not refresh:
        with CACHE.open("rb") as handle:
            return pickle.load(handle)

    metadata = load_alignments()
    count = metadata["count"]
    print(f"Loaded final alignments: {count:,}", flush=True)
    yago_edges, yago_scan = context_edges(
        YAGO_CONTEXT, metadata["yago_uri_to_id"], metadata["yago_name_to_id"]
    )
    print(f"YAGO aligned-neighbor edges: {len(yago_edges):,}", flush=True)
    soa_edges, soa_scan = context_edges(
        SOA_CONTEXT, metadata["soa_uri_to_id"], metadata["soa_name_to_id"]
    )
    print(f"SemOpenAlex aligned-neighbor edges: {len(soa_edges):,}", flush=True)

    yago_adj = adjacency(yago_edges)
    soa_adj = adjacency(soa_edges)
    evaluable = []
    band_counts = Counter()
    evidence_counts = Counter()
    for identifier in range(count):
        left = yago_adj.get(identifier, set())
        right = soa_adj.get(identifier, set())
        if left:
            evidence_counts["yago_nonempty"] += 1
        if right:
            evidence_counts["semopenalex_nonempty"] += 1
        if left and right:
            evidence_counts["both_nonempty"] += 1
        union = left | right
        if not union:
            continue
        common = left & right
        score = len(common) / len(union)
        band_counts[jaccard_band(score)] += 1
        evaluable.append(
            {
                "id": identifier,
                "entity_type": metadata["entity_types"][identifier],
                "source_group": metadata["source_groups"][identifier],
                "yago_degree": len(left),
                "semopenalex_degree": len(right),
                "shared_neighbors": len(common),
                "union_neighbors": len(union),
                "jaccard": score,
            }
        )

    yago_components = component_summary(count, [yago_edges])
    soa_components = component_summary(count, [soa_edges])
    merged_components = component_summary(count, [yago_edges, soa_edges])
    before_components = yago_components["components"] + soa_components["components"]
    after_components = merged_components["components"]
    topology = [
        {
            "state": "Before identity bridges",
            "nodes": 2 * count,
            "within_graph_edges": len(yago_edges) + len(soa_edges),
            "identity_bridges": 0,
            "total_edges": len(yago_edges) + len(soa_edges),
            "connected_components": before_components,
            "largest_component_nodes": max(
                yago_components["largest_component_pair_ids"],
                soa_components["largest_component_pair_ids"],
            ),
            "mean_component_size": 2 * count / before_components,
        },
        {
            "state": "After identity bridges",
            "nodes": 2 * count,
            "within_graph_edges": len(yago_edges) + len(soa_edges),
            "identity_bridges": count,
            "total_edges": len(yago_edges) + len(soa_edges) + count,
            "connected_components": after_components,
            "largest_component_nodes": 2
            * merged_components["largest_component_pair_ids"],
            "mean_component_size": 2 * count / after_components,
        },
    ]

    data = {
        "scope": (
            "Final aligned entities and the aligned neighbors recoverable from "
            "Stage 06 contexts capped at 40 predicate/neighbor features per entity."
        ),
        "alignment_count": count,
        "yago_scan": yago_scan,
        "semopenalex_scan": soa_scan,
        "evidence_counts": dict(evidence_counts),
        "jaccard_band_counts": dict(band_counts),
        "neighbor_groups": (
            group_summary(evaluable, "entity_type")
            + group_summary(evaluable, "source_group")
            + group_summary([{**row, "overall": "All"} for row in evaluable], "overall")
        ),
        "topology": topology,
        "component_details": {
            "yago": yago_components,
            "semopenalex": soa_components,
            "merged_pair_graph": merged_components,
        },
    }
    with CACHE.open("wb") as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return data


def style():
    sns.set_theme(style="whitegrid", context="paper")
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 150,
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.titlesize": 11.5,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#CBD5E1",
            "grid.color": LIGHT,
            "text.color": INK,
        }
    )


def heading(fig, title, subtitle):
    fig.suptitle(title, x=0.075, y=0.97, ha="left", fontsize=14, weight="bold")
    fig.text(0.075, 0.895, subtitle, ha="left", fontsize=8.4, color="#475569")


def fig41(data):
    order = ["0", "(0, 0.10]", "(0.10, 0.25]", "(0.25, 0.50]", "(0.50, 1)", "1"]
    counts = np.array([data["jaccard_band_counts"].get(key, 0) for key in order])
    shares = counts / counts.sum() if counts.sum() else counts
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.9), gridspec_kw={"width_ratios": [1.1, 1]})
    bars = axes[0].bar(order, shares, color=[SLATE, BLUE, BLUE, PURPLE, PURPLE, GREEN])
    axes[0].bar_label(bars, labels=[f"{value:.1%}" for value in shares], padding=3, fontsize=7.5)
    axes[0].set_ylabel("Share of structurally evaluable alignments")
    axes[0].set_xlabel("Aligned-neighbor Jaccard")
    axes[0].tick_params(axis="x", rotation=25)
    axes[0].grid(axis="y")
    sns.despine(ax=axes[0])

    groups = pd.DataFrame(data["neighbor_groups"])
    groups = groups[groups.dimension == "entity_type"].nlargest(8, "evaluable_pairs")
    groups = groups.sort_values("shared_neighbor_rate")
    bars = axes[1].barh(groups.group, groups.shared_neighbor_rate, color=AMBER)
    axes[1].bar_label(
        bars,
        labels=[
            f"{rate:.1%} · n={count:,}"
            for rate, count in zip(groups.shared_neighbor_rate, groups.evaluable_pairs)
        ],
        padding=3,
        fontsize=7.2,
    )
    axes[1].set_xlim(0, max(0.05, groups.shared_neighbor_rate.max() * 1.3))
    axes[1].set_xlabel("Pairs with at least one preserved aligned neighbor")
    axes[1].set_ylabel("")
    axes[1].grid(axis="x")
    sns.despine(ax=axes[1])
    heading(
        fig,
        "Alignment-aware neighborhood preservation",
        "Neighbor URIs are mapped through the final alignment into shared IDs; exact over stored one-hop contexts capped at 20 incident edges.",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / "41_neighbor_preservation.pdf", format="pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig42(data):
    frame = pd.DataFrame(data["topology"])
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.7))
    colors = [SLATE, GREEN]
    measures = [
        ("connected_components", "Connected components", True),
        ("largest_component_nodes", "Largest component (nodes)", True),
        ("mean_component_size", "Mean component size", False),
    ]
    for ax, (column, title, log_scale) in zip(axes, measures):
        bars = ax.bar(["Before", "After"], frame[column], color=colors, width=0.62)
        labels = [
            f"{value:,.2f}" if column == "mean_component_size" else f"{int(value):,}"
            for value in frame[column]
        ]
        ax.bar_label(bars, labels=labels, padding=4, fontsize=8)
        if log_scale and frame[column].min() > 0:
            ax.set_yscale("log")
        ax.set_title(title, loc="left")
        ax.grid(axis="y")
        sns.despine(ax=ax)
    heading(
        fig,
        f"Topology change created by {data['alignment_count']:,} identity bridges",
        "Before/after statistics on the aligned-entity context graph; within-source edges come from capped Stage 06 contexts, not the complete raw graph.",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / "42_bridge_topology_change.pdf", format="pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def write_tables(data):
    table_dir = OUT / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(data["neighbor_groups"]).to_csv(
        table_dir / "26_neighbor_preservation.csv", index=False
    )
    pd.DataFrame(data["topology"]).to_csv(
        table_dir / "27_bridge_topology.csv", index=False
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    style()
    data = build(args.refresh)
    fig41(data)
    fig42(data)
    write_tables(data)
    print(f"Wrote {FIGURES / '41_neighbor_preservation.pdf'}")
    print(f"Wrote {FIGURES / '42_bridge_topology_change.pdf'}")


if __name__ == "__main__":
    main()
