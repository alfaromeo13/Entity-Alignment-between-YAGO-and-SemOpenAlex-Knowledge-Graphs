#!/usr/bin/env python3
"""Generate non-duplicate distribution and partition-scale extensions."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from additional_statistics import build_additional
from thesis_statistics import OUT, ROOT, build_statistics

FIGURES = OUT / "figures"
TABLES = OUT / "tables"
BLUE = "#2563EB"
GREEN = "#16A34A"
PURPLE = "#7C3AED"
AMBER = "#D97706"
CYAN = "#0891B2"
SLATE = "#64748B"
LIGHT = "#E2E8F0"
INK = "#0F172A"


def style() -> None:
    sns.set_theme(style="whitegrid", context="paper")
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 150,
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#CBD5E1",
            "grid.color": LIGHT,
            "text.color": INK,
        }
    )


def heading(fig, title: str, subtitle: str) -> None:
    fig.suptitle(title, x=0.07, y=0.98, ha="left", fontsize=14, weight="bold")
    fig.text(0.07, 0.925, subtitle, ha="left", fontsize=8.4, color="#475569")


def clean(ax, axis="both") -> None:
    sns.despine(ax=ax)
    ax.grid(False)
    if axis:
        ax.grid(axis=axis, color=LIGHT, linewidth=0.7)


def save(fig, filename: str, rect=(0, 0, 1, 0.88)) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=rect)
    fig.savefig(FIGURES / filename, format="pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def human(value: float) -> str:
    for divisor, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= divisor:
            return f"{value / divisor:.2f}{suffix}"
    return f"{value:,.0f}"


def relation_rank_table(core) -> pd.DataFrame:
    rows = []
    for dataset, profile in core["relations"].items():
        for rank, relation in enumerate(profile["relations"], start=1):
            rows.append(
                {
                    "Dataset": dataset,
                    "Rank": rank,
                    "Predicate": relation["relation"],
                    "Predicate URI": relation.get("relation_uri", ""),
                    "Held-out occurrences": relation["count"],
                    "Share": relation["share"],
                    "Cumulative share": relation["cumulative"],
                }
            )
    return pd.DataFrame(rows)


def fig47(rank_table: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.8, 5.6))
    for dataset, color, marker in (
        ("YAGO", BLUE, "o"),
        ("SemOpenAlex", GREEN, "s"),
    ):
        frame = rank_table[rank_table.Dataset == dataset]
        ax.loglog(
            frame.Rank,
            frame["Held-out occurrences"],
            color=color,
            marker=marker,
            markersize=3.5,
            linewidth=1.8,
            label=f"{dataset} · {len(frame)} observed predicates",
        )
    ax.set_xlabel("Predicate frequency rank")
    ax.set_ylabel("Held-out occurrences")
    ax.legend()
    clean(ax)
    heading(
        fig,
        "Full predicate rank–frequency curves",
        "All held-out predicates on log–log axes; the shape is descriptive and no Zipf model is fitted.",
    )
    save(fig, "47_relation_rank_frequency.pdf")


def degree_ccdf_table(extra) -> pd.DataFrame:
    rows = []
    for dataset, stats in extra["graph_samples"].items():
        histogram = {
            int(degree): int(count)
            for degree, count in stats["degree_histogram"].items()
        }
        total = sum(histogram.values())
        tail = 0
        ccdf = {}
        for degree in sorted(histogram, reverse=True):
            tail += histogram[degree]
            ccdf[degree] = tail / total
        for degree in sorted(histogram):
            rows.append(
                {
                    "Dataset": dataset,
                    "Degree threshold": degree,
                    "Nodes at degree": histogram[degree],
                    "Nodes with degree at least threshold": round(ccdf[degree] * total),
                    "CCDF": ccdf[degree],
                }
            )
    return pd.DataFrame(rows)


def fig48(ccdf: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.8, 5.6))
    for dataset, color in (
        ("YAGO held-out", BLUE),
        ("SemOpenAlex 100k sample", GREEN),
    ):
        frame = ccdf[ccdf.Dataset == dataset]
        ax.loglog(
            frame["Degree threshold"],
            frame.CCDF,
            color=color,
            linewidth=2,
            label=dataset,
        )
    ax.set_xlabel("Degree threshold d")
    ax.set_ylabel("P(degree ≥ d)")
    ax.legend()
    ax.set_ylim(bottom=max(ccdf.CCDF.min() * 0.8, 1e-8), top=1.05)
    clean(ax)
    heading(
        fig,
        "Entity-degree complementary cumulative distributions",
        "Tail probabilities use the Figure 22 scope: full YAGO held-out and the SemOpenAlex 100k sample.",
    )
    save(fig, "48_degree_ccdf.pdf")


def namespace_label(uri: str) -> str:
    mappings = (
        ("http://schema.org/", "schema.org"),
        ("https://semopenalex.org/ontology/", "SemOpenAlex ontology"),
        ("http://yago-knowledge.org/resource/", "YAGO"),
        ("http://www.w3.org/1999/02/22-rdf-syntax-ns#", "RDF"),
        ("http://www.w3.org/2000/01/rdf-schema#", "RDFS"),
        ("http://www.w3.org/2002/07/owl#", "OWL"),
        ("http://www.w3.org/2004/02/skos/core#", "SKOS"),
        ("http://purl.org/spar/cito/", "CiTO"),
        ("http://purl.org/dc/terms/", "Dublin Core"),
        ("http://www.w3.org/ns/org#", "W3C ORG"),
        ("https://dbpedia.org/ontology/", "DBpedia"),
    )
    for prefix, label in mappings:
        if uri.startswith(prefix):
            return label
    if "#" in uri:
        return uri.rsplit("#", 1)[0] + "#"
    return uri.rsplit("/", 1)[0] + "/"


def namespace_and_entropy(core) -> tuple[pd.DataFrame, pd.DataFrame]:
    namespace_rows = []
    entropy_rows = []
    for dataset, profile in core["relations"].items():
        namespace_counts = Counter()
        predicate_counts = Counter()
        for relation in profile["relations"]:
            uri = relation.get("relation_uri", "")
            if not uri:
                raise RuntimeError(
                    "Relation URI metadata is absent from the statistics cache; "
                    "rerun this script once with --refresh."
                )
            count = int(relation["count"])
            namespace_counts[namespace_label(uri)] += count
            predicate_counts[uri] += count
        total = sum(predicate_counts.values())
        probabilities = np.array(list(predicate_counts.values()), dtype=float) / total
        entropy = float(-(probabilities * np.log2(probabilities)).sum())
        maximum = math.log2(len(predicate_counts)) if len(predicate_counts) > 1 else 0
        entropy_rows.append(
            {
                "Dataset": dataset,
                "Observed predicates": len(predicate_counts),
                "Shannon entropy (bits)": entropy,
                "Maximum entropy (bits)": maximum,
                "Normalized entropy": entropy / maximum if maximum else 0,
                "Effective predicates (2^H)": 2**entropy,
                "Gini coefficient": profile["gini"],
            }
        )
        for name, count in namespace_counts.most_common():
            namespace_rows.append(
                {
                    "Dataset": dataset,
                    "Predicate namespace": name,
                    "Held-out occurrences": count,
                    "Share": count / total,
                }
            )
    return pd.DataFrame(namespace_rows), pd.DataFrame(entropy_rows)


def fig49(namespaces: pd.DataFrame, entropy: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), gridspec_kw={"width_ratios": [1.45, 1]})
    order = (
        namespaces.groupby("Predicate namespace")["Held-out occurrences"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    colors = [BLUE, GREEN, PURPLE, AMBER, CYAN, SLATE, "#DB2777"]
    left = np.zeros(2)
    datasets = ["YAGO", "SemOpenAlex"]
    for index, name in enumerate(order):
        values = np.array(
            [
                namespaces[
                    (namespaces.Dataset == dataset)
                    & (namespaces["Predicate namespace"] == name)
                ].Share.sum()
                for dataset in datasets
            ]
        )
        axes[0].barh(datasets, values, left=left, color=colors[index % len(colors)], label=name)
        left += values
    axes[0].set_xlim(0, 1)
    axes[0].set_xlabel("Share of held-out triples")
    axes[0].set_title("Predicate namespace composition", loc="left")
    handles, labels = axes[0].get_legend_handles_labels()
    clean(axes[0], "x")

    bars = axes[1].bar(
        entropy.Dataset,
        entropy["Normalized entropy"],
        color=[BLUE, GREEN],
        width=0.58,
    )
    axes[1].bar_label(
        bars,
        labels=[
            f"{row['Normalized entropy']:.3f}\nH={row['Shannon entropy (bits)']:.2f} bits"
            for _, row in entropy.iterrows()
        ],
        padding=4,
        fontsize=8,
    )
    axes[1].set_ylim(0, 1.12)
    axes[1].set_ylabel("Normalized predicate entropy")
    axes[1].set_title("Frequency diversity", loc="left")
    clean(axes[1], "y")
    heading(
        fig,
        "Predicate namespace composition and frequency entropy",
        "Namespace shares preserve predicate occurrences; entropy summarizes frequency diversity and complements the Lorenz/Gini view in Figure 03.",
    )
    fig.legend(
        handles,
        labels,
        fontsize=7,
        loc="lower center",
        bbox_to_anchor=(0.33, 0.015),
        ncol=4,
    )
    save(fig, "49_predicate_namespace_entropy.pdf", rect=(0, 0.18, 1, 0.88))


def partition_scale_table() -> pd.DataFrame:
    rows = []
    for dataset, relative in (
        ("YAGO", "yago/distmult_dot"),
        ("SemOpenAlex", "semopenalex/distmult_dot"),
    ):
        output = ROOT / "04_embeddings/output" / relative
        config = json.loads((output / "config.json").read_text(encoding="utf-8"))
        stats = json.loads(
            (
                ROOT
                / f"03_integer_encoding/{dataset.lower()}/dataset_stats.json"
            ).read_text(encoding="utf-8")
        )
        partitions = int(config["entities"]["entity"]["num_partitions"])
        checkpoints = sorted(output.glob("embeddings_entity_*.h5"))
        sizes = np.array([path.stat().st_size for path in checkpoints], dtype=float)
        rows.append(
            {
                "Dataset": dataset,
                "Entity partitions": partitions,
                "Partition-pair buckets": partitions**2,
                "Entities": int(stats["num_entities"]),
                "Train triples": int(stats["train_triples"]),
                "Embedding dimension": int(config["dimension"]),
                "Batch size": int(config["batch_size"]),
                "Epochs": int(config["num_epochs"]),
                "Mean entities per partition": int(stats["num_entities"]) / partitions,
                "Arithmetic mean triples per partition-pair bucket": int(stats["train_triples"]) / partitions**2,
                "Checkpoint partition files": len(checkpoints),
                "Median checkpoint GiB per partition": float(np.median(sizes) / 2**30),
                "Minimum checkpoint GiB": float(sizes.min() / 2**30),
                "Maximum checkpoint GiB": float(sizes.max() / 2**30),
            }
        )
    return pd.DataFrame(rows)


def fig50(scale: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 5))
    colors = [BLUE, GREEN]
    metrics = [
        ("Entity partitions", "Entity partitions"),
        ("Partition-pair buckets", "Possible partition pairs"),
    ]
    for ax, (column, title) in zip(axes[:2], metrics):
        bars = ax.bar(scale.Dataset, scale[column], color=colors, width=0.58)
        ax.bar_label(bars, labels=[f"{int(value):,}" for value in scale[column]], padding=4)
        ax.set_title(title, loc="left")
        ax.set_ylabel("Count")
        ax.set_ylim(0, scale[column].max() * 1.18)
        clean(ax, "y")
    x = np.arange(len(scale))
    width = 0.36
    first = axes[2].bar(
        x - width / 2,
        scale["Mean entities per partition"],
        width,
        color=PURPLE,
        label="Entities / partition",
    )
    second = axes[2].bar(
        x + width / 2,
        scale["Arithmetic mean triples per partition-pair bucket"],
        width,
        color=AMBER,
        label="Triples / pair bucket",
    )
    axes[2].bar_label(first, labels=[human(value) for value in first.datavalues], padding=3, fontsize=7.5)
    axes[2].bar_label(second, labels=[human(value) for value in second.datavalues], padding=3, fontsize=7.5)
    axes[2].set_xticks(x, scale.Dataset)
    axes[2].set_yscale("log")
    axes[2].set_ylabel("Arithmetic average (log scale)")
    axes[2].set_title("Average partition scale", loc="left")
    axes[2].legend(fontsize=7)
    clean(axes[2], "y")
    heading(
        fig,
        "PyTorch-BigGraph partitioning scale",
        "Exact configurations and dataset totals; per-partition values are arithmetic averages, not a measured triple-load distribution. Figure 39 reports observed SemOpenAlex partition-loss variation.",
    )
    save(fig, "50_pbg_partitioning_scale.pdf")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    style()
    TABLES.mkdir(parents=True, exist_ok=True)
    core = build_statistics(args.refresh)
    extra = build_additional(args.refresh)
    rank_table = relation_rank_table(core)
    ccdf = degree_ccdf_table(extra)
    namespaces, entropy = namespace_and_entropy(core)
    scale = partition_scale_table()
    rank_table.to_csv(TABLES / "33_relation_rank_frequency.csv", index=False)
    ccdf.to_csv(TABLES / "34_degree_ccdf.csv", index=False)
    namespaces.to_csv(TABLES / "35_predicate_namespace_composition.csv", index=False)
    entropy.to_csv(TABLES / "36_predicate_entropy.csv", index=False)
    scale.to_csv(TABLES / "37_pbg_partitioning_scale.csv", index=False)
    fig47(rank_table)
    fig48(ccdf)
    fig49(namespaces, entropy)
    fig50(scale)
    print("Wrote Figures 47–50 and Tables 33–37")


if __name__ == "__main__":
    main()
