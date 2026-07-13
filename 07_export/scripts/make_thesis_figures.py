#!/usr/bin/env python3
"""Create the final 16 statistical figures and thesis-ready tables."""

from __future__ import annotations

import argparse
import json
import math
import re
import textwrap
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
import seaborn as sns

from thesis_statistics import OUT, ROOT, build_statistics, read_kv

FIGURES = OUT / "figures"
BLUE = "#2563EB"
NAVY = "#172554"
CYAN = "#0891B2"
GREEN = "#16A34A"
AMBER = "#D97706"
ORANGE = "#EA580C"
RED = "#DC2626"
PURPLE = "#7C3AED"
SLATE = "#64748B"
LIGHT = "#E2E8F0"
INK = "#0F172A"
MODEL = {"TransE": "#94A3B8", "DistMult": BLUE, "ComplEx": PURPLE}
GROUP = {
    "Proxy-gold": GREEN,
    "Baseline-shared": BLUE,
    "Final-only": PURPLE,
    "Threshold-rejected": RED,
}


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
            "axes.labelsize": 9.5,
            "axes.edgecolor": "#CBD5E1",
            "xtick.color": "#475569",
            "ytick.color": "#475569",
            "text.color": INK,
            "grid.color": "#E2E8F0",
            "grid.linewidth": 0.7,
            "legend.frameon": False,
        }
    )


def title(fig, heading, subtitle):
    fig.suptitle(heading, x=0.075, y=0.97, ha="left", fontsize=14, weight="bold")
    fig.text(0.075, 0.915, subtitle, ha="left", fontsize=8.7, color="#475569")


def save(fig, name, rect=(0, 0, 1, 0.88)):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=rect)
    fig.savefig(FIGURES / name, format="pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def clean(ax, axis="x"):
    sns.despine(ax=ax)
    ax.grid(False)
    if axis:
        ax.grid(axis=axis, color="#E2E8F0", linewidth=0.7)
    ax.set_axisbelow(True)


def human(value):
    for divisor, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= divisor:
            return f"{value/divisor:.1f}{suffix}"
    return f"{value:,.0f}"


def candidate_counts():
    raw = proxy = ambiguous = None
    for line in (
        ROOT / "05_entity_alignment/logs/ea_exact_29043615.out"
    ).read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.search(r"Candidate pairs:\s*([\d,]+)", line)
        if match:
            raw = int(match.group(1).replace(",", ""))
    for line in (
        ROOT / "05_entity_alignment/logs/ea_score_exact_29044935.out"
    ).read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.search(r"Strict proxy-gold rows:\s*([\d,]+)", line)
        if match:
            proxy = int(match.group(1).replace(",", ""))
        match = re.search(r"Ambiguous rows:\s*([\d,]+)", line)
        if match:
            ambiguous = int(match.group(1).replace(",", ""))
    threshold = pd.read_csv(
        ROOT / "05_entity_alignment/outputs/final/threshold_sweep_summary.tsv", sep="\t"
    )
    filtered = read_kv(
        ROOT / "05_entity_alignment/data/candidates/exact_label_candidates_filtered_summary.tsv"
    )
    baseline = read_kv(
        ROOT / "05_entity_alignment/final_alignment/outputs/strict/evaluation_summary.tsv"
    )
    row30 = threshold.loc[threshold.threshold == 0.30].iloc[0]
    return pd.DataFrame(
        [
            ["Raw exact-label pairs", raw],
            ["After label/frequency filters", filtered["candidate_rows"]],
            ["Ambiguous pair rows", ambiguous],
            ["Embedding top-1", int(row30.total_top1)],
            ["Embedding score ≥ 0.30", int(row30.score_pass)],
            ["Type-compatible at 0.30", int(row30.type_pass)],
            ["Final Stage 05 one-to-one", baseline["final_alignments"]],
        ],
        columns=["Stage", "Count"],
    ), proxy


def rejection_frame():
    with (
        ROOT
        / "05_entity_alignment/final_alignment/outputs/strict/type_filter_summary.json"
    ).open(encoding="utf-8") as handle:
        summary = json.load(handle)
    rows = [
        [
            row["yago_profile_type"],
            row["semopenalex_uri_type"],
            int(row["count"]),
        ]
        for row in summary["type_pair_counts"]
        if row["compatibility"] != "compatible"
    ]
    return pd.DataFrame(rows, columns=["YAGO profile", "SemOpenAlex type", "Rejected"])


def fig01_scale(data):
    s = data["summaries"]
    y, o = s["yago_dataset"], s["soa_dataset"]
    yp, op = s["yago_preprocessing"], s["soa_preprocessing"]
    records = [
        ["Encoded entities", "YAGO", y["num_entities"]],
        ["Encoded entities", "SemOpenAlex", o["num_entities"]],
        ["Relations", "YAGO", y["num_relations"]],
        ["Relations", "SemOpenAlex", o["num_relations"]],
        ["Structural triples", "YAGO", yp["structural_triples_kept"]],
        ["Structural triples", "SemOpenAlex", op["structural_triples_kept"]],
        ["Text literal rows", "YAGO", yp["text_literal_rows_written"]],
        ["Text literal rows", "SemOpenAlex", op["text_literal_rows_written"]],
    ]
    frame = pd.DataFrame(records, columns=["Measure", "Dataset", "Count"])
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.5))
    for ax, measure in zip(axes.flat, frame.Measure.unique()):
        sub = frame[frame.Measure == measure]
        for index, row in enumerate(sub.itertuples()):
            ax.scatter(row.Count, index, s=95, color=BLUE if row.Dataset == "YAGO" else GREEN)
            ax.text(row.Count * 1.12, index, f"{row.Count:,}", va="center", fontsize=8)
        ax.set_yticks([0, 1], ["YAGO", "SemOpenAlex"])
        ax.set_xscale("log")
        ax.set_title(measure, loc="left")
        clean(ax, "x")
    title(
        fig,
        "Scale and composition of the two embedding graphs",
        "Exact counts from preprocessing and integer encoding; logarithmic axes preserve comparisons across orders of magnitude.",
    )
    save(fig, "01_dataset_scale.pdf")


def fig02_relation_pareto(data):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.8))
    for ax, dataset, color in zip(axes, ("YAGO", "SemOpenAlex"), (BLUE, GREEN)):
        frame = pd.DataFrame(data["relations"][dataset]["relations"][:12])
        positions = np.arange(len(frame))
        ax.bar(positions, frame.share * 100, color=color, alpha=0.9)
        ax.set_xticks(positions, frame.relation, rotation=55, ha="right", fontsize=7.5)
        ax.set_ylabel("Share of held-out triples (%)")
        ax.set_title(f"{dataset} · {data['relations'][dataset]['total']:,} triples", loc="left")
        twin = ax.twinx()
        twin.plot(positions, frame.cumulative * 100, color=INK, marker="o", linewidth=1.6)
        twin.set_ylim(0, 105)
        twin.set_ylabel("Cumulative coverage (%)")
        twin.grid(False)
        clean(ax, "y")
    title(
        fig,
        "Predicate concentration in the complete held-out graphs",
        "Pareto bars show individual relation shares; black curves show cumulative coverage.",
    )
    save(fig, "02_relation_pareto.pdf")


def fig03_relation_lorenz(data):
    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    ax.plot([0, 1], [0, 1], linestyle="--", color=SLATE, label="Equal relation frequency")
    for dataset, color in (("YAGO", BLUE), ("SemOpenAlex", GREEN)):
        profile = data["relations"][dataset]
        ax.plot(
            profile["lorenz_population"],
            profile["lorenz_share"],
            linewidth=2.5,
            color=color,
            label=f"{dataset} · Gini={profile['gini']:.3f}",
        )
    ax.set_xlabel("Cumulative share of relation types")
    ax.set_ylabel("Cumulative share of triples")
    ax.legend()
    ax.set_aspect("equal")
    clean(ax, "both")
    title(
        fig,
        "Relation-frequency inequality",
        "Lorenz curves quantify how strongly each graph is dominated by a small number of predicates.",
    )
    save(fig, "03_relation_lorenz.pdf")


def fig04_embedding(data):
    frame = pd.DataFrame(data["embedding_results"])
    metrics = ["MRR", "Hits@1", "Hits@10", "Hits@50", "AUC"]
    long = frame.melt(
        id_vars=["Dataset", "Model"],
        value_vars=metrics,
        var_name="Metric",
        value_name="Score",
    )
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True)
    for ax, dataset in zip(axes, ("YAGO", "SemOpenAlex")):
        sub = long[long.Dataset == dataset]
        sns.pointplot(
            data=sub,
            x="Metric",
            y="Score",
            hue="Model",
            palette=MODEL,
            markers=["o", "s", "D"],
            linestyles=["-", "-", "-"],
            ax=ax,
        )
        ax.set_ylim(0.3, 1.03)
        ax.set_title(dataset, loc="left")
        ax.set_xlabel("")
        ax.set_ylabel("Link-prediction score" if dataset == "YAGO" else "")
        clean(ax, "y")
        if dataset == "YAGO":
            ax.legend(title="")
        else:
            ax.get_legend().remove()
    title(
        fig,
        "Embedding benchmark: model quality depends on the metric",
        "DistMult leads MRR and Hits@1; TransE remains strongest on YAGO AUC and Hits@50.",
    )
    save(fig, "04_embedding_benchmark.pdf")


def fig05_training(data):
    frame = pd.DataFrame(data["training"])
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7))
    for ax, metric in zip(axes.flat, ("Loss", "MRR", "Hits@10", "AUC")):
        sub = frame[frame.Metric == metric]
        sns.lineplot(
            data=sub,
            x="Epoch",
            y="Value",
            hue="Model",
            palette=MODEL,
            marker="o",
            linewidth=2,
            ax=ax,
        )
        if metric == "Loss":
            ax.set_yscale("log")
        ax.set_title(metric, loc="left")
        ax.set_ylabel("")
        clean(ax, "y")
        if ax is axes[0, 0]:
            ax.legend(title="")
        else:
            ax.get_legend().remove()
    title(
        fig,
        "YAGO training dynamics and convergence",
        "Partition statistics are weighted by evaluated examples before aggregation by epoch.",
    )
    save(fig, "05_training_dynamics.pdf")


def fig06_attrition(counts, proxy):
    fig, (ax, info_ax) = plt.subplots(
        1,
        2,
        figsize=(11.5, 5.5),
        sharey=True,
        gridspec_kw={"width_ratios": [3.7, 1.8], "wspace": 0.04},
    )
    values = counts.Count.to_numpy()
    colors = [NAVY, BLUE, CYAN, PURPLE, AMBER, ORANGE, GREEN]
    ax.barh(counts.Stage, values, color=colors)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlabel("Rows / predicted pairs (log scale)")
    clean(ax, "x")

    # Keep textual diagnostics in a separate panel: placing them between bars
    # makes their location unstable on the logarithmic x-axis.
    info_ax.set_xlim(0, 1)
    info_ax.axis("off")
    info_ax.text(
        0.03,
        1.015,
        "Rows",
        transform=info_ax.transAxes,
        fontsize=8,
        weight="bold",
        color=INK,
    )
    info_ax.text(
        0.43,
        1.015,
        "Change from preceding row",
        transform=info_ax.transAxes,
        fontsize=8,
        weight="bold",
        color=INK,
    )
    info_ax.plot(
        [0.38, 0.38],
        [-0.02, 1.02],
        transform=info_ax.transAxes,
        color=LIGHT,
        linewidth=1,
        clip_on=False,
    )
    row_transform = info_ax.get_yaxis_transform()
    for index, value in enumerate(values):
        info_ax.text(
            0.03,
            index,
            f"{value:,}",
            transform=row_transform,
            va="center",
            fontsize=8,
            color=INK,
        )
        if index == 0:
            change = "Starting candidate set"
        elif index < len(values) - 1:
            change = f"{value / values[index - 1]:.1%} retained"
        else:
            change = f"Proxy branch merged\n({proxy:,} rows)"
        info_ax.text(
            0.43,
            index,
            change,
            transform=row_transform,
            va="center",
            fontsize=7.5,
            color=SLATE,
            linespacing=1.15,
        )
    title(
        fig,
        "Candidate attrition from 328.8 million blocked pairs to the baseline",
        "Absolute counts and conditional retention rates reveal where most computational reduction occurs.",
    )
    save(fig, "06_candidate_attrition.pdf")


def fig07_ambiguity_ccdf():
    frame = pd.read_csv(
        ROOT / "05_entity_alignment/data/candidates/exact_label_candidates_filtered_yago_distribution.tsv",
        sep="\t",
    ).sort_values("num_candidates_for_yago_entity")
    total = frame.num_yago_entities.sum()
    frame["at_least"] = frame.num_yago_entities[::-1].cumsum()[::-1] / total * 100
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    ax.step(frame.num_candidates_for_yago_entity, frame.at_least, where="post", color=PURPLE, linewidth=2.4)
    ax.fill_between(frame.num_candidates_for_yago_entity, frame.at_least, step="post", alpha=0.12, color=PURPLE)
    for x in (2, 5, 10, 20):
        value = frame.loc[frame.num_candidates_for_yago_entity >= x, "num_yago_entities"].sum() / total * 100
        ax.scatter([x], [value], color=PURPLE)
        ax.annotate(f"≥{x}: {value:.1f}%", (x, value), xytext=(5, 6), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Candidate count k")
    ax.set_ylabel("YAGO entities with at least k candidates (%)")
    ax.set_xlim(1, 50)
    ax.set_ylim(0, 105)
    clean(ax, "both")
    title(
        fig,
        "Candidate ambiguity has a long tail",
        "Complementary cumulative distribution over all 3,926,910 filtered YAGO entities.",
    )
    save(fig, "07_candidate_ambiguity_ccdf.pdf")


def fig08_ambiguity_type(data):
    frame = pd.DataFrame(data["ambiguity_by_type"]["counts"])
    top_types = frame.groupby("type")["count"].sum().nlargest(10).index
    bands = ["2", "3–5", "6–10", "11–20", "21+"]
    pivot = (
        frame[frame.type.isin(top_types)]
        .pivot(index="type", columns="band", values="count")
        .fillna(0)
        .reindex(columns=bands)
    )
    proportions = pivot.div(pivot.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(9.5, 6))
    sns.heatmap(
        proportions,
        cmap=sns.light_palette(PURPLE, as_cmap=True),
        annot=True,
        fmt=".1f",
        linewidths=0.5,
        cbar_kws={"label": "Within-type share (%)"},
        ax=ax,
    )
    ax.set_xlabel("Candidates for the YAGO entity")
    ax.set_ylabel("SemOpenAlex type")
    title(
        fig,
        "Ambiguity differs substantially by entity type",
        f"Full scan of {data['ambiguity_by_type']['total']:,} enriched top-1 candidate rows.",
    )
    save(fig, "08_ambiguity_by_type.pdf")


def fig09_threshold(data):
    frame = pd.DataFrame(data["summaries"]["threshold_sweep"])
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    axes[0].plot(frame.threshold, frame.score_pass, marker="o", color=BLUE, label="Score pass")
    axes[0].plot(frame.threshold, frame.type_pass, marker="o", color=GREEN, label="Type pass")
    axes[0].plot(frame.threshold, frame.type_fail, marker="o", color=RED, label="Type rejected")
    axes[0].axvline(0.30, color=INK, linestyle="--", linewidth=1)
    axes[0].set_xlabel("Embedding threshold")
    axes[0].set_ylabel("Candidate count")
    axes[0].legend()
    clean(axes[0], "both")
    axes[1].plot(frame.threshold, frame.score_pass_pct * 100, marker="o", color=BLUE, label="Score-pass rate")
    axes[1].plot(frame.threshold, frame.type_pass_pct_of_total * 100, marker="o", color=GREEN, label="Type-pass rate")
    axes[1].plot(frame.threshold, frame.type_fail_pct_of_score_pass * 100, marker="o", color=RED, label="Type-fail among score-pass")
    axes[1].axvline(0.30, color=INK, linestyle="--", linewidth=1)
    axes[1].set_xlabel("Embedding threshold")
    axes[1].set_ylabel("Rate (%)")
    axes[1].legend(fontsize=7.5)
    clean(axes[1], "both")
    title(
        fig,
        "Threshold selection controls both coverage and semantic rejection",
        "The Stage 05 sweep supports the selected 0.30 embedding threshold without pretending to estimate true precision.",
    )
    save(fig, "09_threshold_tradeoff.pdf")


def fig10_rejection_heatmap(rejections):
    pivot = rejections.pivot(
        index="YAGO profile", columns="SemOpenAlex type", values="Rejected"
    ).fillna(0)
    order_rows = pivot.sum(axis=1).sort_values(ascending=False).index
    order_cols = pivot.sum(axis=0).sort_values(ascending=False).index
    pivot = pivot.loc[order_rows, order_cols]
    annotations = pivot.map(lambda value: f"{int(value):,}" if value else "")
    fig, ax = plt.subplots(figsize=(10, 5.8))
    sns.heatmap(
        np.log10(pivot + 1),
        cmap=sns.light_palette(RED, as_cmap=True),
        annot=annotations,
        fmt="",
        linewidths=0.6,
        cbar_kws={"label": "log10(rejected + 1)"},
        ax=ax,
    )
    ax.set_xlabel("SemOpenAlex target type")
    ax.set_ylabel("YAGO profile type")
    title(
        fig,
        "Semantic rejection matrix",
        "Counts show which profile/type combinations were explicitly removed as implausible.",
    )
    save(fig, "10_semantic_rejection_heatmap.pdf")


def systems_frame(data):
    frame = pd.DataFrame(data["summaries"]["systems"])
    frame["System"] = frame.system.replace(
        {"baseline": "Baseline", "A+B+C final": "A+B+C"}
    )
    return frame


def fig11_systems(data):
    frame = systems_frame(data)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    colors = ["#94A3B8", BLUE, AMBER, GREEN]
    bars = axes[0].bar(frame.System, frame.rows, color=colors)
    axes[0].bar_label(bars, labels=[f"{v/1e6:.3f}M" for v in frame.rows], padding=4, fontsize=8)
    axes[0].set_ylabel("Predicted alignments")
    clean(axes[0], "y")
    x = np.arange(len(frame))
    axes[1].plot(x, frame.proxy_precision_like, marker="o", color=PURPLE, linewidth=2, label="Proxy precision-like")
    axes[1].plot(x, frame.proxy_recall_like, marker="s", color=AMBER, linestyle="--", linewidth=2, label="Proxy recall-like")
    axes[1].set_xticks(x, frame.System)
    axes[1].set_ylim(0.48, 0.75)
    axes[1].set_ylabel("Silver-standard diagnostic")
    axes[1].legend()
    clean(axes[1], "y")
    title(
        fig,
        "Ablation results: profile text drives expansion; neighbor evidence is weaker",
        "System size is shown beside proxy diagnostics so coverage changes are not mistaken for verified quality.",
    )
    save(fig, "11_ablation_comparison.pdf")


def mask_label(mask):
    systems = list(("Baseline", "A+B", "C", "A+B+C"))
    return " ∩ ".join(name for bit, name in enumerate(systems) if mask & (1 << bit))


def fig12_upset(data):
    counts = {
        int(mask): count for mask, count in data["systems"]["intersection_counts"].items()
    }
    selected = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:12]
    masks = [mask for mask, _ in selected]
    values = [count for _, count in selected]
    fig = plt.figure(figsize=(12, 6.8))
    grid = fig.add_gridspec(2, 1, height_ratios=[3, 1.45], hspace=0.05)
    ax_bar = fig.add_subplot(grid[0])
    ax_matrix = fig.add_subplot(grid[1], sharex=ax_bar)
    x = np.arange(len(selected))
    bars = ax_bar.bar(x, values, color=NAVY)
    ax_bar.bar_label(bars, labels=[human(v) for v in values], padding=3, fontsize=7.5)
    ax_bar.set_ylabel("Distinct alignment pairs")
    ax_bar.tick_params(axis="x", labelbottom=False)
    clean(ax_bar, "y")
    rows = ["Baseline", "A+B", "C", "A+B+C"]
    for row_index, row_name in enumerate(rows):
        ax_matrix.text(-0.65, row_index, row_name, ha="right", va="center", fontsize=8.5)
    for col, mask in enumerate(masks):
        active = []
        for row in range(4):
            is_active = bool(mask & (1 << row))
            ax_matrix.scatter(col, row, s=55 if is_active else 20, color=NAVY if is_active else "#CBD5E1", zorder=3)
            if is_active:
                active.append(row)
        if len(active) > 1:
            ax_matrix.plot([col, col], [min(active), max(active)], color=NAVY, linewidth=2)
    ax_matrix.set_ylim(-0.6, 3.6)
    ax_matrix.invert_yaxis()
    ax_matrix.set_xlim(-0.8, len(selected) - 0.3)
    ax_matrix.axis("off")
    title(
        fig,
        "Exact four-system intersection structure",
        "UpSet counts use deterministic 128-bit pair identifiers across all Baseline, A+B, C-only and A+B+C outputs.",
    )
    fig.subplots_adjust(left=0.15, right=0.98, bottom=0.08, top=0.84)
    fig.savefig(FIGURES / "12_system_upset.pdf", format="pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def score_samples(data):
    frames = []
    for group, rows in data["systems"]["samples"].items():
        frame = pd.DataFrame(rows)
        frame["Group"] = group
        frames.append(frame)
    rejected = pd.DataFrame(data["rejected"])
    frames.append(rejected)
    return pd.concat(frames, ignore_index=True)


def fig13_raincloud(data):
    frame = score_samples(data)
    metrics = {
        "embedding_cosine": "Embedding",
        "profile_tfidf_score": "Profile text",
        "neighbor_tfidf_score": "Graph neighbor",
    }
    long = frame.melt(
        id_vars="Group",
        value_vars=list(metrics),
        var_name="Evidence",
        value_name="Score",
    )
    long.Evidence = long.Evidence.replace(metrics)
    groups = ["Proxy-gold", "Baseline-shared", "Final-only", "Threshold-rejected"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 5.2), sharey=True)
    for ax, evidence in zip(axes, metrics.values()):
        sub = long[long.Evidence == evidence]
        sns.violinplot(
            data=sub,
            x="Group",
            y="Score",
            hue="Group",
            order=groups,
            hue_order=groups,
            palette=GROUP,
            dodge=False,
            legend=False,
            inner=None,
            cut=0,
            linewidth=0.8,
            ax=ax,
        )
        sns.boxplot(
            data=sub,
            x="Group",
            y="Score",
            order=groups,
            width=0.20,
            showfliers=False,
            boxprops={"facecolor": "white", "zorder": 3},
            ax=ax,
        )
        point_sample = sub.sample(min(1000, len(sub)), random_state=20260629)
        sns.stripplot(
            data=point_sample,
            x="Group",
            y="Score",
            order=groups,
            color=INK,
            alpha=0.10,
            size=1.5,
            jitter=0.22,
            ax=ax,
        )
        ax.set_title(evidence, loc="left")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=35)
        clean(ax, "y")
    axes[0].set_ylabel("Similarity score")
    axes[1].set_ylabel("")
    axes[2].set_ylabel("")
    title(
        fig,
        "Evidence distributions for accepted, new and rejected alignments",
        "Violin widths show density; embedded boxplots show median and quartiles; points are deterministic display samples.",
    )
    save(fig, "13_evidence_rainclouds.pdf")


def fig14_interactions(data):
    sample = score_samples(data)
    accepted = sample[sample.Group.isin(["Baseline-shared", "Final-only"])].copy()
    accepted["Decision"] = "Accepted ambiguous"
    rejected = sample[sample.Group == "Threshold-rejected"].copy()
    rejected["Decision"] = "Threshold rejected"
    frame = pd.concat([accepted, rejected], ignore_index=True)
    pairs = [
        ("embedding_cosine", "profile_tfidf_score", "Embedding", "Profile"),
        ("embedding_cosine", "neighbor_tfidf_score", "Embedding", "Neighbor"),
        ("profile_tfidf_score", "neighbor_tfidf_score", "Profile", "Neighbor"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(13, 8), sharex="col", sharey="col")
    cmaps = {
        "Accepted ambiguous": LinearSegmentedColormap.from_list("accept", ["#EFF6FF", BLUE, NAVY]),
        "Threshold rejected": LinearSegmentedColormap.from_list("reject", ["#FEF2F2", RED, "#7F1D1D"]),
    }
    for row_index, decision in enumerate(("Accepted ambiguous", "Threshold rejected")):
        sub = frame[frame.Decision == decision]
        for col, (x, y, xlabel, ylabel) in enumerate(pairs):
            ax = axes[row_index, col]
            ax.hexbin(sub[x], sub[y], gridsize=38, mincnt=1, bins="log", cmap=cmaps[decision])
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            if col == 0:
                ax.text(-0.32, 0.5, decision, transform=ax.transAxes, rotation=90, va="center", ha="center", weight="bold", color=BLUE if row_index == 0 else RED)
            clean(ax, None)
    title(
        fig,
        "Signal interactions separate accepted and threshold-rejected candidates",
        "Accepted panels use final ambiguous samples; rejected panels use every pair removed between ABC thresholds 0.25 and 0.30.",
    )
    save(fig, "14_score_interactions.pdf")


def fig15_type_contributions(data):
    counts = data["systems"]["type_counts"]
    means = data["systems"]["type_means"]
    types = [name for name, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:8]]
    records = []
    for entity_type in types:
        records.extend(
            [
                [entity_type, "Embedding", means[entity_type]["embedding_cosine"] * 0.60],
                [entity_type, "Profile", means[entity_type]["profile_tfidf_score"] * 0.35],
                [entity_type, "Neighbor", means[entity_type]["neighbor_tfidf_score"] * 0.05],
            ]
        )
    pivot = pd.DataFrame(records, columns=["Type", "Component", "Contribution"]).pivot(
        index="Type", columns="Component", values="Contribution"
    ).loc[types]
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    left = np.zeros(len(pivot))
    for component, color in (("Embedding", BLUE), ("Profile", PURPLE), ("Neighbor", AMBER)):
        ax.barh(pivot.index, pivot[component], left=left, color=color, label=component)
        left += pivot[component].to_numpy()
    ax.invert_yaxis()
    ax.set_xlabel("Mean weighted contribution to ABC score")
    ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.25))
    clean(ax, "x")
    title(
        fig,
        "The balance of evidence differs across entity types",
        "Means use all final A+B+C alignments; graph-neighbor evidence is constrained by its 5% weight.",
    )
    save(fig, "15_evidence_by_type.pdf")


def load_error_samples():
    frame = pd.read_csv(
        ROOT / "07_export/validation/study/sample_key.tsv",
        sep="\t",
    )
    frame["Sample"] = np.select(
        [
            frame.source_group.eq("strict_proxy"),
            frame.score_band.eq("[0.30,0.45)"),
            frame.score_band.eq("[0.45,0.60)"),
        ],
        [
            "Strict proxy",
            "Ranked 0.30–0.45",
            "Ranked 0.45–0.60",
        ],
        default="Ranked ≥0.60",
    )
    return frame


def fig16_error_analysis():
    frame = load_error_samples()
    sample_order = [
        "Strict proxy",
        "Ranked 0.30–0.45",
        "Ranked 0.45–0.60",
        "Ranked ≥0.60",
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.1))
    sns.boxplot(
        data=frame,
        x="Sample",
        y="abc_score",
        order=sample_order,
        color="#93C5FD",
        showfliers=False,
        ax=axes[0, 0],
    )
    axes[0, 0].set_title("A · Final combined score", loc="left")
    axes[0, 0].set_ylabel("ABC score")
    axes[0, 0].tick_params(axis="x", rotation=25)
    clean(axes[0, 0], "y")
    sns.boxplot(
        data=frame,
        x="Sample",
        y="embedding_cosine",
        order=sample_order,
        color="#C4B5FD",
        showfliers=False,
        ax=axes[0, 1],
    )
    axes[0, 1].set_title("B · Embedding similarity", loc="left")
    axes[0, 1].set_ylabel("Embedding cosine")
    axes[0, 1].tick_params(axis="x", rotation=25)
    clean(axes[0, 1], "y")
    type_counts = (
        frame.groupby(["Sample", "semopenalex_uri_type"]).size().rename("Count").reset_index()
    )
    entity_types = sorted(type_counts.semopenalex_uri_type.unique())
    proportions = (
        type_counts.pivot(index="Sample", columns="semopenalex_uri_type", values="Count")
        .reindex(index=sample_order, columns=entity_types)
        .fillna(0)
    )
    proportions = proportions.div(proportions.sum(axis=1), axis=0) * 100
    type_colors = sns.color_palette("tab10", n_colors=len(entity_types))
    proportions.plot(
        kind="bar",
        stacked=True,
        color=type_colors,
        width=0.68,
        ax=axes[1, 0],
    )
    axes[1, 0].set_title("C · SemOpenAlex entity-type composition", loc="left")
    axes[1, 0].set_ylabel("Within-sample type share (%)")
    axes[1, 0].tick_params(axis="x", rotation=25)
    handles, labels = axes[1, 0].get_legend_handles_labels()
    axes[1, 0].get_legend().remove()
    clean(axes[1, 0], "y")
    frame["Label length"] = frame.yago_label.fillna("").str.len()
    sns.boxplot(
        data=frame,
        x="Sample",
        y="Label length",
        order=sample_order,
        color="#FCD34D",
        showfliers=False,
        ax=axes[1, 1],
    )
    axes[1, 1].set_title("D · YAGO label length", loc="left")
    axes[1, 1].tick_params(axis="x", rotation=25)
    clean(axes[1, 1], "y")
    fig.legend(
        handles,
        labels,
        title="SemOpenAlex entity type",
        loc="lower center",
        bbox_to_anchor=(0.5, 0.005),
        ncol=4,
        fontsize=7.5,
        title_fontsize=8,
    )
    title(
        fig,
        "Validation-sample cohorts expose different review risks",
        "The current 500-pair stratified sample is compared by selection source and ABC-score band; no verdicts are implied.",
    )
    save(fig, "16_error_analysis.pdf", rect=(0, 0.09, 1, 0.88))


def write_tables(data, counts, rejections):
    table_dir = OUT / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    s = data["summaries"]
    dataset = pd.DataFrame(
        [
            [
                "YAGO",
                s["yago_dataset"]["num_entities"],
                s["yago_dataset"]["num_relations"],
                s["yago_preprocessing"]["structural_triples_kept"],
                s["yago_preprocessing"]["text_literal_rows_written"],
            ],
            [
                "SemOpenAlex",
                s["soa_dataset"]["num_entities"],
                s["soa_dataset"]["num_relations"],
                s["soa_preprocessing"]["structural_triples_kept"],
                s["soa_preprocessing"]["text_literal_rows_written"],
            ],
        ],
        columns=["Dataset", "Entities", "Relations", "Structural triples", "Text literal rows"],
    )
    dataset.to_csv(table_dir / "01_dataset_statistics.csv", index=False)
    pd.DataFrame(data["embedding_results"]).to_csv(table_dir / "02_link_prediction.csv", index=False)
    counts.to_csv(table_dir / "03_candidate_attrition.csv", index=False)
    pd.DataFrame(s["threshold_sweep"]).to_csv(table_dir / "04_threshold_sweep.csv", index=False)
    systems_frame(data).to_csv(table_dir / "05_system_comparison.csv", index=False)
    pd.DataFrame(s["sensitivity"]).to_csv(table_dir / "06_sensitivity.csv", index=False)
    sample = score_samples(data)
    evidence = sample.groupby("Group")[
        ["embedding_cosine", "profile_tfidf_score", "neighbor_tfidf_score", "abc_score"]
    ].agg(["count", "mean", "std", "median", "min", "max"])
    evidence.columns = [
        f"{score}_{statistic}" for score, statistic in evidence.columns
    ]
    evidence.reset_index().to_csv(
        table_dir / "07_evidence_descriptives.csv", index=False
    )
    pd.DataFrame(s["final_types"]).to_csv(table_dir / "08_final_type_distribution.csv", index=False)
    relation_rows = []
    for dataset_name, profile in data["relations"].items():
        for row in profile["relations"]:
            relation_rows.append({"Dataset": dataset_name, **row})
    pd.DataFrame(relation_rows).to_csv(table_dir / "09_relation_distribution.csv", index=False)
    rejections.to_csv(table_dir / "10_semantic_rejections.csv", index=False)
    lines = [
        "# Thesis tables",
        "",
        "These CSV files are intended for native LaTeX tables, not screenshots.",
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
    OUT.mkdir(parents=True, exist_ok=True)
    style()
    data = build_statistics(args.refresh)
    counts, proxy = candidate_counts()
    rejections = rejection_frame()

    fig01_scale(data)
    fig02_relation_pareto(data)
    fig03_relation_lorenz(data)
    fig04_embedding(data)
    fig05_training(data)
    fig06_attrition(counts, proxy)
    fig07_ambiguity_ccdf()
    fig08_ambiguity_type(data)
    fig09_threshold(data)
    fig10_rejection_heatmap(rejections)
    fig11_systems(data)
    fig12_upset(data)
    fig13_raincloud(data)
    fig14_interactions(data)
    fig15_type_contributions(data)
    fig16_error_analysis()
    write_tables(data, counts, rejections)

    figures = sorted(FIGURES.glob("*.pdf"))
    print(f"Generated {len(figures)} statistical PDF figures")
    for path in figures:
        print(f"  {path.name}")
    print(f"Tables: {OUT / 'tables'}")
    print(f"Table preview: {OUT / 'THESIS_TABLES.md'}")


if __name__ == "__main__":
    main()
