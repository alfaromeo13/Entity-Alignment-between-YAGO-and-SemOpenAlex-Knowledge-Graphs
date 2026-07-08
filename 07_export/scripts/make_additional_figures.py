#!/usr/bin/env python3
"""Generate supported additional statistical figures 17–30."""

from __future__ import annotations

import argparse
from collections import Counter
import math
from pathlib import Path
import re

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
import seaborn as sns

from additional_statistics import OUT, ROOT, build_additional, short_uri
from thesis_statistics import build_statistics

FIGURES = OUT / "figures"
BLUE = "#2563EB"
NAVY = "#172554"
CYAN = "#0891B2"
GREEN = "#16A34A"
AMBER = "#D97706"
RED = "#DC2626"
PURPLE = "#7C3AED"
SLATE = "#64748B"
LIGHT = "#E2E8F0"
INK = "#0F172A"


def style():
    sns.set_theme(style="whitegrid", context="paper")
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 150,
            "svg.fonttype": "none",
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.titlesize": 11.5,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#CBD5E1",
            "grid.color": "#E2E8F0",
            "grid.linewidth": 0.7,
            "legend.frameon": False,
            "text.color": INK,
        }
    )


def heading(fig, title, subtitle):
    fig.suptitle(title, x=0.075, y=0.97, ha="left", fontsize=14, weight="bold")
    fig.text(0.075, 0.915, subtitle, ha="left", fontsize=8.7, color="#475569")


def save(fig, name, rect=(0, 0, 1, 0.88)):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=rect)
    fig.savefig(FIGURES / name, format="svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def clean(ax, axis="x"):
    sns.despine(ax=ax)
    ax.grid(False)
    if axis:
        ax.grid(axis=axis, color="#E2E8F0", linewidth=0.7)


def human(value):
    for divisor, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= divisor:
            return f"{value/divisor:.1f}{suffix}"
    if value and abs(value) < 10 and not float(value).is_integer():
        return f"{value:.2f}"
    return f"{value:,.0f}"


def readable_class_name(value):
    """Turn YAGO's encoded local class names into thesis-readable labels."""
    value = re.sub(
        r"_u([0-9a-fA-F]{4})_",
        lambda match: chr(int(match.group(1), 16)),
        value,
    )
    return value.replace("_", " ")


def fig18_predicates(core):
    fig, axes = plt.subplots(1, 2, figsize=(12, 8))
    for ax, dataset, color in zip(axes, ("YAGO", "SemOpenAlex"), (BLUE, GREEN)):
        frame = pd.DataFrame(core["relations"][dataset]["relations"][:30]).sort_values("count")
        bars = ax.barh(frame.relation, frame["count"], color=color)
        ax.set_xscale("log")
        ax.set_xlabel("Held-out triple count (log scale)")
        ax.set_title(dataset, loc="left")
        ax.tick_params(axis="y", labelsize=7)
        clean(ax, "x")
    heading(
        fig,
        "Top 30 predicates reveal different graph semantics",
        "Exact distributions from the complete held-out graph splits.",
    )
    save(fig, "18_top30_predicates.svg")


def fig19_ontology(extra):
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.5))
    for ax, dataset, color in zip(axes, ("YAGO", "SemOpenAlex"), (BLUE, GREEN)):
        counts = Counter(extra["type_profiles"][dataset]["classes"])
        frame = pd.DataFrame(counts.most_common(15), columns=["Class", "Count"]).sort_values("Count")
        frame["Class"] = frame["Class"].map(readable_class_name)
        bars = ax.barh(frame.Class, frame.Count, color=color)
        ax.bar_label(bars, labels=[human(v) for v in frame.Count], padding=3, fontsize=7)
        ax.set_xscale("log")
        ax.set_xlabel("rdf:type triples (log scale)")
        ax.set_title(dataset, loc="left")
        clean(ax, "x")
    heading(
        fig,
        "Ontology/type profiles of the held-out graphs",
        "Top rdf:type objects show YAGO’s broad ontology versus SemOpenAlex’s scholarly specialization.",
    )
    save(fig, "19_ontology_type_profiles.svg")


def fig20_overlap(extra):
    overlap = extra["predicate_overlap"]
    counts = [len(overlap["yago_only"]), len(overlap["shared"]), len(overlap["soa_only"])]
    labels = ["Only YAGO", "Shared", "Only SemOpenAlex"]
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    bars = ax.bar(labels, counts, color=[BLUE, GREEN, CYAN], width=0.62)
    ax.bar_label(bars, labels=[str(value) for value in counts], padding=4, fontsize=10)
    shared = ", ".join(short_uri(uri) for uri in overlap["shared"])
    ax.text(0.5, 0.82, f"Shared predicates\n{shared}", transform=ax.transAxes, ha="center", va="top", fontsize=8.5, bbox={"boxstyle": "round,pad=0.4", "facecolor": "#F0FDF4", "edgecolor": GREEN})
    ax.set_ylabel("Predicate vocabulary size")
    clean(ax, "y")
    heading(
        fig,
        "Predicate vocabulary overlap is small",
        "Exact URI-level comparison of the 68 YAGO and 31 SemOpenAlex embedding predicates.",
    )
    save(fig, "20_predicate_overlap.svg")


def graph_stats_frame(extra):
    rows = []
    for dataset, stats in extra["graph_samples"].items():
        rows.append(
            [
                dataset,
                stats["nodes"],
                stats["edges"],
                stats["average_degree"],
                stats["median_degree"],
                stats["max_degree"],
                stats["density"],
                len(stats["components"]),
            ]
        )
    return pd.DataFrame(
        rows,
        columns=["Graph", "Nodes", "Edges", "Average degree", "Median degree", "Max degree", "Density", "Components"],
    )


def fig21_graph_stats(extra):
    frame = graph_stats_frame(extra)
    metrics = ["Nodes", "Edges", "Average degree", "Median degree", "Max degree", "Components"]
    long = frame.melt(id_vars="Graph", value_vars=metrics, var_name="Metric", value_name="Value")
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    sns.barplot(data=long, y="Metric", x="Value", hue="Graph", palette=[BLUE, GREEN], ax=ax)
    ax.set_xscale("log")
    for container in ax.containers:
        ax.bar_label(container, labels=[human(bar.get_width()) for bar in container], padding=3, fontsize=7)
    ax.set_xlabel("Value (log scale)")
    ax.set_ylabel("")
    ax.legend(title="")
    clean(ax, "x")
    heading(
        fig,
        "Graph-topology statistics on tractable evaluation graphs",
        "YAGO uses its full held-out split; SemOpenAlex uses the documented random 100k held-out sample—not the terabyte training graph.",
    )
    save(fig, "21_sample_graph_statistics.svg")


def fig22_degree(extra):
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    for dataset, color in (("YAGO held-out", BLUE), ("SemOpenAlex 100k sample", GREEN)):
        hist = extra["graph_samples"][dataset]["degree_histogram"]
        x = np.array(sorted(int(key) for key in hist))
        y = np.array([hist[int(key)] if int(key) in hist else hist[str(int(key))] for key in x])
        ax.loglog(x, y, marker="o", markersize=3, linewidth=1.5, color=color, label=dataset)
    ax.set_xlabel("Undirected degree")
    ax.set_ylabel("Node count")
    ax.legend()
    clean(ax, "both")
    heading(
        fig,
        "Degree distributions are strongly right-skewed",
        "Log–log view of evaluation-graph degrees; this supports heavy-tail language without claiming a fitted power law.",
    )
    save(fig, "22_degree_distribution.svg")


def fig23_components(extra):
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    for ax, dataset, color in zip(axes, ("YAGO held-out", "SemOpenAlex 100k sample"), (BLUE, GREEN)):
        sizes = np.array(extra["graph_samples"][dataset]["components"], dtype=int)
        ranks = np.arange(1, len(sizes) + 1)
        ax.loglog(ranks, sizes, color=color, linewidth=2)
        ax.scatter(ranks[: min(25, len(ranks))], sizes[: min(25, len(sizes))], color=color, s=12)
        ax.set_xlabel("Component rank")
        ax.set_ylabel("Nodes in component")
        ax.set_title(f"{dataset} · {len(sizes):,} components", loc="left")
        clean(ax, "both")
    heading(
        fig,
        "Connected-component size rank",
        "Component structure is computed on the same tractable evaluation graphs used for degree statistics.",
    )
    save(fig, "23_component_sizes.svg")


def fig24_labels(extra):
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.9), gridspec_kw={"width_ratios": [1.7, 1]})
    for dataset, color, linestyle in (("YAGO", BLUE, "-"), ("SemOpenAlex", GREEN, "--")):
        frame = pd.DataFrame(extra["final"]["label_lengths"][dataset]).sort_values("length")
        density = frame["count"] / frame["count"].sum()
        axes[0].plot(
            frame.length,
            density,
            linewidth=2,
            linestyle=linestyle,
            color=color,
            label=dataset,
        )
    axes[0].set_xlim(0, 80)
    axes[0].set_xlabel("Label length in characters")
    axes[0].set_ylabel("Fraction of final alignments")
    axes[0].legend()
    clean(axes[0], "both")

    deltas = pd.DataFrame(extra["final"]["label_length_deltas"]).sort_values("difference")
    deltas["share"] = deltas["count"] / deltas["count"].sum()
    display = deltas[deltas["difference"] <= 15]
    axes[1].bar(display["difference"], display["share"], color=CYAN, width=0.8)
    exact_share = deltas.loc[deltas["difference"] == 0, "share"].sum()
    axes[1].text(
        0.98,
        0.94,
        f"Equal length: {exact_share:.1%}",
        transform=axes[1].transAxes,
        ha="right",
        va="top",
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": LIGHT},
    )
    axes[1].set_xlabel("Absolute paired length difference")
    axes[1].set_ylabel("Fraction of final alignments")
    axes[1].set_xticks(range(0, 16, 3))
    clean(axes[1], "both")
    heading(
        fig,
        "Label-length distributions in the final aligned population",
        f"Exact lengths from all {sum(extra['final']['source_counts'].values()):,} final pairs; this describes aligned labels rather than every raw RDF literal.",
    )
    save(fig, "24_aligned_label_lengths.svg")


def fig25_ambiguous(extra):
    frame = pd.DataFrame(extra["top_ambiguous_labels"][:25]).sort_values("frequency")
    fig, ax = plt.subplots(figsize=(9, 7))
    bars = ax.barh(frame.label, frame.frequency, color=RED)
    ax.bar_label(bars, labels=[f"{v:,}" for v in frame.frequency], padding=3, fontsize=7)
    ax.set_xscale("log")
    ax.set_xlabel("SemOpenAlex entities sharing normalized label (log scale)")
    ax.tick_params(axis="y", labelsize=7.5)
    clean(ax, "x")
    heading(
        fig,
        "The most ambiguous normalized labels",
        "Computed across the complete candidate-label statistics file; generic labels create the largest candidate blocks.",
    )
    save(fig, "25_top_ambiguous_labels.svg")


def core_samples(core):
    frames = []
    for group, rows in core["systems"]["samples"].items():
        frame = pd.DataFrame(rows)
        frame["Group"] = group
        frames.append(frame)
    rejected = pd.DataFrame(core["rejected"])
    frames.append(rejected)
    return pd.concat(frames, ignore_index=True)


def fig26_confidence(core):
    frame = core_samples(core)
    accepted = frame[frame.Group.isin(["Baseline-shared", "Final-only"])]["abc_score"]
    rejected = frame[frame.Group == "Threshold-rejected"]["abc_score"]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    bins = np.linspace(0.20, 0.75, 45)
    axes[0].hist(accepted, bins=bins, density=True, alpha=0.65, color=BLUE, label="Accepted ambiguous")
    axes[0].hist(rejected, bins=bins, density=True, alpha=0.65, color=RED, label="Threshold rejected")
    axes[0].axvline(0.30, color=INK, linestyle="--", label="ABC threshold 0.30")
    axes[0].set_xlabel("ABC score")
    axes[0].set_ylabel("Density")
    axes[0].legend()
    clean(axes[0], "y")
    sns.ecdfplot(accepted, color=BLUE, linewidth=2, label="Accepted ambiguous", ax=axes[1])
    sns.ecdfplot(rejected, color=RED, linewidth=2, label="Threshold rejected", ax=axes[1])
    axes[1].axvline(0.30, color=INK, linestyle="--")
    axes[1].set_xlabel("ABC score")
    axes[1].set_ylabel("Cumulative share")
    axes[1].legend()
    clean(axes[1], "both")
    heading(
        fig,
        "Final-score separation around the selected threshold",
        "Rejected population contains every pair present at threshold 0.25 but removed at 0.30.",
    )
    save(fig, "26_confidence_distribution.svg")


def fig27_proxy(extra):
    totals = Counter(extra["final"]["proxy_total"])
    hits = Counter(extra["final"]["proxy_hits"])
    types = [name for name, value in totals.most_common(8)]
    frame = pd.DataFrame(
        [
            [entity_type, totals[entity_type], hits[entity_type], hits[entity_type] / totals[entity_type] * 100]
            for entity_type in types
        ],
        columns=["Type", "Proxy total", "Recovered", "Recall-like (%)"],
    )
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    x = np.arange(len(frame))
    axes[0].bar(x - 0.18, frame["Proxy total"], width=0.36, color="#94A3B8", label="Proxy total")
    axes[0].bar(x + 0.18, frame.Recovered, width=0.36, color=GREEN, label="Recovered in final")
    axes[0].set_xticks(x, frame.Type, rotation=35, ha="right")
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Pairs (log scale)")
    axes[0].legend()
    clean(axes[0], "y")
    bars = axes[1].bar(frame.Type, frame["Recall-like (%)"], color=PURPLE)
    axes[1].bar_label(bars, labels=[f"{v:.1f}%" for v in frame["Recall-like (%)"]], padding=3, fontsize=7.5)
    axes[1].tick_params(axis="x", rotation=35)
    axes[1].set_ylim(0, 105)
    axes[1].set_ylabel("Proxy recall-like (%)")
    clean(axes[1], "y")
    heading(
        fig,
        "Proxy-gold composition and recovery by entity type",
        "Type-specific recall-like uses the strict label-derived silver standard, not manually verified ground truth.",
    )
    save(fig, "27_proxy_gold_by_type.svg")


def fig28_matrix(extra):
    frame = pd.DataFrame(extra["final"]["matrix"])
    frame["yago_type"] = frame["yago_type"].replace(
        {"unknown": "unclassified_by_predicates"}
    )
    pivot = frame.pivot(index="yago_type", columns="soa_type", values="count").fillna(0)
    rows = pivot.sum(axis=1).nlargest(8).index
    cols = pivot.sum(axis=0).nlargest(10).index
    pivot = pivot.loc[rows, cols]
    annotations = pivot.map(lambda value: human(value) if value else "")
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.heatmap(
        np.log10(pivot + 1),
        annot=annotations,
        fmt="",
        cmap=sns.light_palette(BLUE, as_cmap=True),
        linewidths=0.5,
        cbar_kws={"label": "log10(alignments + 1)"},
        ax=ax,
    )
    ax.set_xlabel("SemOpenAlex URI type")
    ax.set_ylabel("YAGO profile type")
    ax.tick_params(axis="y", rotation=0)
    heading(
        fig,
        "Type matrix for the ambiguous final alignments",
        "Exact YAGO-profile × SemOpenAlex-URI counts; strict proxy rows are excluded because their profile field stores a source marker, not a type.",
    )
    save(fig, "28_alignment_type_matrix.svg")


def fig29_neighbor(extra):
    frame = pd.DataFrame(
        extra["final"]["neighbor_pairs"],
        columns=["Neighbor", "Embedding", "Profile", "ABC"],
    )
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
    cmap = LinearSegmentedColormap.from_list("neighbor", ["#FFFBEB", AMBER, "#78350F"])
    for ax, y, label in zip(axes, ("Embedding", "Profile", "ABC"), ("Embedding cosine", "Profile score", "ABC score")):
        hb = ax.hexbin(frame.Neighbor, frame[y], gridsize=45, bins="log", mincnt=1, cmap=cmap)
        correlation = frame[["Neighbor", y]].corr().iloc[0, 1]
        ax.text(0.05, 0.94, f"sample r={correlation:.3f}", transform=ax.transAxes, va="top", bbox={"facecolor": "white", "edgecolor": LIGHT})
        ax.set_xlabel("Graph-neighbor score")
        ax.set_ylabel(label)
        ax.set_xlim(0, max(0.25, frame.Neighbor.quantile(0.999)))
        clean(ax, None)
    fig.colorbar(hb, ax=axes, shrink=0.75, label="log density")
    heading(
        fig,
        "Graph-neighbor agreement with the stronger signals",
        "Deterministic 100,000-row sample of non-proxy final alignments; extreme neighbor outliers are clipped only on the display axis.",
    )
    fig.subplots_adjust(left=0.07, right=0.91, bottom=0.14, top=0.82, wspace=0.35)
    fig.savefig(FIGURES / "29_neighbor_agreement.svg", format="svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def cooccurrence_matrix(stats):
    relation_nodes = {int(key): value for key, value in stats["relation_nodes"].items()}
    top = [key for key, _ in sorted(relation_nodes.items(), key=lambda item: item[1], reverse=True)[:12]]
    position = {relation: index for index, relation in enumerate(top)}
    matrix = np.zeros((len(top), len(top)))
    for row in stats["cooccurrence"]:
        left, right = int(row["left"]), int(row["right"])
        if left not in position or right not in position:
            continue
        union = relation_nodes[left] + relation_nodes[right] - row["count"]
        similarity = row["count"] / union if union else 0
        matrix[position[left], position[right]] = similarity
        matrix[position[right], position[left]] = similarity
    np.fill_diagonal(matrix, np.nan)
    labels = [stats["relation_names"].get(relation, str(relation)) for relation in top]
    return matrix, labels


def fig30_cooccurrence(extra):
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    for ax, dataset in zip(axes, ("YAGO held-out", "SemOpenAlex 100k sample")):
        matrix, labels = cooccurrence_matrix(extra["graph_samples"][dataset])
        nonzero = matrix[np.isfinite(matrix) & (matrix > 0)]
        vmax = float(np.quantile(nonzero, 0.95)) if len(nonzero) else 1
        sns.heatmap(
            matrix,
            cmap=sns.light_palette(PURPLE, as_cmap=True),
            vmin=0,
            vmax=vmax,
            mask=np.isnan(matrix),
            xticklabels=labels,
            yticklabels=labels,
            square=True,
            cbar=True,
            cbar_kws={"label": "Jaccard similarity", "shrink": 0.7},
            ax=ax,
        )
        ax.set_title(dataset, loc="left")
        ax.tick_params(axis="x", rotation=55, labelsize=6.5)
        ax.tick_params(axis="y", labelsize=6.5)
    heading(
        fig,
        "Predicate co-occurrence within entity neighborhoods",
        "Off-diagonal cells show Jaccard similarity of incident-predicate entity sets; diagonals are intentionally masked.",
    )
    save(fig, "30_predicate_cooccurrence.svg")


def write_additional_tables(extra):
    table_dir = OUT / "tables"
    graph_stats_frame(extra).to_csv(table_dir / "11_sample_graph_statistics.csv", index=False)
    type_rows = []
    for dataset, profile in extra["type_profiles"].items():
        for class_name, count in profile["classes"].items():
            type_rows.append([dataset, class_name, count])
    pd.DataFrame(type_rows, columns=["Dataset", "Class", "rdf:type triples"]).to_csv(
        table_dir / "12_type_profiles.csv", index=False
    )
    totals = Counter(extra["final"]["proxy_total"])
    hits = Counter(extra["final"]["proxy_hits"])
    proxy = pd.DataFrame(
        [
            [name, totals[name], hits[name], hits[name] / totals[name]]
            for name in totals
        ],
        columns=["Type", "Proxy total", "Recovered", "Proxy recall-like"],
    )
    proxy.to_csv(table_dir / "13_proxy_gold_by_type.csv", index=False)
    matrix = pd.DataFrame(extra["final"]["matrix"])
    matrix["yago_type"] = matrix["yago_type"].replace(
        {"unknown": "unclassified_by_predicates"}
    )
    matrix.to_csv(table_dir / "14_final_alignment_matrix.csv", index=False)
    pd.DataFrame(extra["top_ambiguous_labels"]).to_csv(table_dir / "15_top_ambiguous_labels.csv", index=False)
    lines = [
        "# Thesis tables",
        "",
        "These CSV files are intended for native LaTeX tables, not screenshots.",
        "The Markdown below is a compact preview; the CSV files contain the complete results.",
        "",
    ]
    for path in sorted(table_dir.glob("*.csv")):
        frame = pd.read_csv(path)
        preview = frame.head(20).fillna("")
        headers = [str(column) for column in preview.columns]
        rows = [[str(value) for value in row] for row in preview.itertuples(index=False, name=None)]
        lines.extend(
            [
                f"## {path.stem}",
                "",
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join("---" for _ in headers) + " |",
                *["| " + " | ".join(row) + " |" for row in rows],
                "",
            ]
        )
    (OUT / "THESIS_TABLES.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    style()
    core = build_statistics(False)
    extra = build_additional(args.refresh)

    fig18_predicates(core)
    fig19_ontology(extra)
    fig20_overlap(extra)
    fig21_graph_stats(extra)
    fig22_degree(extra)
    fig23_components(extra)
    fig24_labels(extra)
    fig25_ambiguous(extra)
    fig26_confidence(core)
    fig27_proxy(extra)
    fig28_matrix(extra)
    fig29_neighbor(extra)
    fig30_cooccurrence(extra)
    write_additional_tables(extra)

    figures = sorted(path.name for path in FIGURES.glob("*.svg"))
    print(f"Total SVG figures: {len(figures)}")
    for name in figures:
        print(f"  {name}")


if __name__ == "__main__":
    main()
