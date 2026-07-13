#!/usr/bin/env python3
"""Generate the final data-grounded visual narrative figures 36–40."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch, FancyBboxPatch
import numpy as np
import pandas as pd
import seaborn as sns

from additional_statistics import OUT, ROOT, build_additional
from external_identifier_validation import build_identifier_validation
from thesis_statistics import build_statistics

FIGURES = OUT / "figures"
BLUE = "#2563EB"
GREEN = "#16A34A"
CYAN = "#0891B2"
AMBER = "#D97706"
RED = "#DC2626"
PURPLE = "#7C3AED"
SLATE = "#64748B"
INK = "#0F172A"
LIGHT = "#E2E8F0"


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
            "grid.linewidth": 0.7,
            "legend.frameon": False,
            "text.color": INK,
        }
    )


def heading(fig, title, subtitle):
    fig.suptitle(title, x=0.075, y=0.97, ha="left", fontsize=14, weight="bold")
    fig.text(0.075, 0.915, subtitle, ha="left", fontsize=8.7, color="#475569")


def clean(ax, axis="x"):
    sns.despine(ax=ax)
    ax.grid(False)
    if axis:
        ax.grid(axis=axis, color=LIGHT, linewidth=0.7)


def save(fig, name, rect=(0, 0, 1, 0.88)):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=rect)
    fig.savefig(FIGURES / name, format="pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def human(value):
    for divisor, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= divisor:
            return f"{value/divisor:.2f}{suffix}"
    return f"{value:,.0f}"


def processing_frame(core):
    summaries = core["summaries"]
    rows = []
    for dataset, stats in (
        ("YAGO", summaries["yago_preprocessing"]),
        ("SemOpenAlex", summaries["soa_preprocessing"]),
    ):
        categories = {
            "Structural kept": int(stats.get("structural_triples_kept", 0)),
            "Literal/non-structural": int(stats.get("non_structural_triples_seen", 0)),
            "Filtered subject": int(stats.get("filtered_subject_triples", 0)),
            "Helper relation removed": int(stats.get("skipped_helper_structural_triples", 0)),
            "Malformed": int(stats.get("malformed_lines", 0)),
        }
        total = int(stats.get("total_lines_read") or sum(categories.values()))
        for category, count in categories.items():
            rows.append([dataset, category, count, total, count / total if total else 0])
    return pd.DataFrame(
        rows,
        columns=["Dataset", "Outcome", "Statements", "Processed statements", "Share"],
    )


def fig36_rdf_yield(core):
    frame = processing_frame(core)
    order = [
        "Structural kept",
        "Literal/non-structural",
        "Filtered subject",
        "Helper relation removed",
        "Malformed",
    ]
    colors = {
        "Structural kept": BLUE,
        "Literal/non-structural": GREEN,
        "Filtered subject": AMBER,
        "Helper relation removed": PURPLE,
        "Malformed": RED,
    }
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.5, 1]})
    for y, dataset in enumerate(("YAGO", "SemOpenAlex")):
        subset = frame[frame.Dataset == dataset].set_index("Outcome")
        left = 0
        total = subset["Processed statements"].iloc[0]
        for category in order:
            value = subset.loc[category, "Statements"]
            share = value / total * 100 if total else 0
            axes[0].barh(
                dataset,
                share,
                left=left / total * 100 if total else 0,
                color=colors[category],
                label=category if y == 0 else None,
            )
            if value / total >= 0.12:
                axes[0].text(
                    (left + value / 2) / total * 100,
                    y,
                    f"{human(value)}\n{value/total:.1%}",
                    ha="center",
                    va="center",
                    color="white",
                    weight="bold",
                    fontsize=8,
                )
            elif value / total >= 0.02:
                axes[0].text(
                    (left + value) / total * 100 + 1,
                    y,
                    f"{human(value)}\n{value/total:.1%}",
                    ha="left",
                    va="center",
                    color=colors[category],
                    weight="bold",
                    fontsize=7,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.88, "pad": 1.5},
                )
            left += value
        axes[0].text(101.5, y, f"total {human(total)}", va="center", fontsize=8.5, weight="bold")
    axes[0].set_xlim(0, 116)
    axes[0].set_xlabel("Share of processed RDF statements (%)")
    axes[0].legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=3)
    clean(axes[0], "x")

    summaries = core["summaries"]
    products = pd.DataFrame(
        [
            ["YAGO", "Structural graph", summaries["yago_preprocessing"]["structural_triples_kept"]],
            ["YAGO", "Text rows extracted", summaries["yago_preprocessing"]["text_literal_rows_written"]],
            ["SemOpenAlex", "Structural graph", summaries["soa_preprocessing"]["structural_triples_kept"]],
            ["SemOpenAlex", "Text rows extracted", summaries["soa_preprocessing"]["text_literal_rows_written"]],
        ],
        columns=["Dataset", "Product", "Count"],
    )
    sns.barplot(
        data=products,
        x="Count",
        y="Product",
        hue="Dataset",
        palette={"YAGO": BLUE, "SemOpenAlex": GREEN},
        ax=axes[1],
    )
    axes[1].set_xscale("log")
    for container in axes[1].containers:
        axes[1].bar_label(
            container,
            labels=[human(bar.get_width()) for bar in container],
            padding=3,
            fontsize=7,
        )
    axes[1].set_xlabel("Written rows (log scale)")
    axes[1].set_ylabel("")
    axes[1].legend(title="")
    clean(axes[1], "x")
    heading(
        fig,
        "From raw RDF statements to alignment-ready evidence",
        "Exact preprocessing counters: 1.78B YAGO and 24.42B SemOpenAlex statements were classified into structural, literal and filtered outcomes.",
    )
    save(fig, "36_rdf_processing_yield.pdf")


def catalog_counts():
    directories = {
        "concept": "concepts",
        "institution": "institutions",
        "source": "sources",
        "publisher": "publishers",
        "funder": "funders",
        "keyword": "keywords",
        "topic": "topics",
        "subfield": "subfields",
        "field": "fields",
        "domain": "domains",
    }
    result = {}
    pattern = re.compile(r"Items \(lines\) processed:\s*([\d,]+)")
    for entity_type, directory in directories.items():
        path = ROOT / f"01_raw/semopenalex/{directory}/{directory}-transformation-summary.txt"
        match = pattern.search(path.read_text(encoding="utf-8"))
        if match:
            result[entity_type] = int(match.group(1).replace(",", ""))
    return result


def coverage_frame(core):
    available = catalog_counts()
    aligned = {}
    for row in core["summaries"]["final_types"]:
        entity_type = row.get("semopenalex_type")
        count = row.get("count")
        if entity_type is None or count is None:
            raise KeyError(
                "Final type summary requires semopenalex_type/count columns"
            )
        aligned[entity_type] = int(count)
    rows = []
    for entity_type, total in available.items():
        count = aligned.get(entity_type, 0)
        rows.append([entity_type, total, count, count / total if total else 0])
    return pd.DataFrame(
        rows,
        columns=["Type", "SemOpenAlex items", "Final alignments", "Target-side coverage"],
    )


def fig37_coverage(core):
    frame = coverage_frame(core)
    frame = frame[frame["Final alignments"] > 0].sort_values("Target-side coverage")
    fig, ax = plt.subplots(figsize=(9.5, 5.7))
    y = np.arange(len(frame))
    ax.hlines(y, 0, frame["Target-side coverage"] * 100, color=LIGHT, linewidth=6)
    ax.scatter(
        frame["Target-side coverage"] * 100,
        y,
        s=100,
        color=CYAN,
        edgecolor="white",
        linewidth=1.2,
        zorder=3,
    )
    for index, (_, row) in enumerate(frame.iterrows()):
        ax.text(
            row["Target-side coverage"] * 100 + 0.25,
            index,
            f"{row['Target-side coverage']:.2%}  ({int(row['Final alignments']):,}/{int(row['SemOpenAlex items']):,})",
            va="center",
            fontsize=8,
        )
    ax.set_yticks(y, frame.Type.str.title())
    ax.set_xlabel("SemOpenAlex entities aligned to YAGO (%)")
    ax.set_xlim(0, max(frame["Target-side coverage"] * 100) * 1.32)
    clean(ax, "x")
    heading(
        fig,
        "Target-side alignment coverage varies sharply by entity type",
        "Coverage uses complete SemOpenAlex catalog counts where transformation summaries report item totals; authors and works are excluded.",
    )
    save(fig, "37_target_catalog_coverage.pdf")


def flow_frame(extra):
    frame = pd.DataFrame(extra["final"]["matrix"])
    frame["yago_type"] = frame["yago_type"].replace(
        {"unknown": "unclassified_by_predicates"}
    )
    frame = frame[frame["count"] >= 100].copy()
    left_order = frame.groupby("yago_type")["count"].sum().sort_values(ascending=False).index.tolist()
    right_order = frame.groupby("soa_type")["count"].sum().sort_values(ascending=False).index.tolist()
    return frame, left_order, right_order


def node_intervals(frame, key, order):
    totals = frame.groupby(key)["count"].sum()
    weights = np.sqrt(totals.loc[order].to_numpy(dtype=float))
    gap = 0.035
    usable = 0.82 - gap * (len(order) - 1)
    heights = weights / weights.sum() * usable
    result = {}
    top = 0.91
    for name, height in zip(order, heights):
        result[name] = [top - height, top]
        top -= height + gap
    return result


def ribbon(ax, x0, x1, y0a, y0b, y1a, y1b, color, alpha):
    control = (x0 + x1) / 2
    vertices = [
        (x0, y0a),
        (control, y0a),
        (control, y1a),
        (x1, y1a),
        (x1, y1b),
        (control, y1b),
        (control, y0b),
        (x0, y0b),
        (x0, y0a),
    ]
    codes = [
        MplPath.MOVETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.LINETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CLOSEPOLY,
    ]
    ax.add_patch(PathPatch(MplPath(vertices, codes), facecolor=color, edgecolor="none", alpha=alpha))


def fig38_bipartite(extra):
    frame, left_order, right_order = flow_frame(extra)
    left_nodes = node_intervals(frame, "yago_type", left_order)
    right_nodes = node_intervals(frame, "soa_type", right_order)
    left_offsets = {name: interval[0] for name, interval in left_nodes.items()}
    right_offsets = {name: interval[0] for name, interval in right_nodes.items()}
    left_totals = frame.groupby("yago_type")["count"].sum()
    right_totals = frame.groupby("soa_type")["count"].sum()
    left_scale = {
        name: (interval[1] - interval[0]) / left_totals[name]
        for name, interval in left_nodes.items()
    }
    right_scale = {
        name: (interval[1] - interval[0]) / right_totals[name]
        for name, interval in right_nodes.items()
    }
    colors = {
        "person_like": BLUE,
        "unclassified_by_predicates": SLATE,
        "creative_work_like": GREEN,
        "place_like": AMBER,
        "organization_like": PURPLE,
    }
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    for row in frame.sort_values("count", ascending=False).to_dict("records"):
        h0 = row["count"] * left_scale[row["yago_type"]]
        h1 = row["count"] * right_scale[row["soa_type"]]
        y0a, y0b = left_offsets[row["yago_type"]], left_offsets[row["yago_type"]] + h0
        y1a, y1b = right_offsets[row["soa_type"]], right_offsets[row["soa_type"]] + h1
        ribbon(ax, 0.26, 0.74, y0a, y0b, y1a, y1b, colors.get(row["yago_type"], CYAN), 0.30)
        left_offsets[row["yago_type"]] += h0
        right_offsets[row["soa_type"]] += h1
    for name, (bottom, top) in left_nodes.items():
        node_color = colors.get(name, CYAN)
        node_height = top - bottom
        node_center = (bottom + top) / 2
        display_height = max(node_height, 0.024)
        display_bottom = node_center - display_height / 2
        ax.add_patch(FancyBboxPatch((0.16, display_bottom), 0.10, display_height, boxstyle="round,pad=0.004", facecolor=node_color, edgecolor="white"))
        ax.text(0.145, (bottom+top)/2, name.replace("_", " "), ha="right", va="center", fontsize=8.5)
        ax.text(0.21, node_center, human(left_totals[name]), ha="center", va="center", color="white", weight="bold", fontsize=7.5, zorder=5)
    for name, (bottom, top) in right_nodes.items():
        node_height = top - bottom
        node_center = (bottom + top) / 2
        display_height = max(node_height, 0.024)
        display_bottom = node_center - display_height / 2
        ax.add_patch(FancyBboxPatch((0.74, display_bottom), 0.10, display_height, boxstyle="round,pad=0.004", facecolor=CYAN, edgecolor="white"))
        ax.text(0.855, (bottom+top)/2, name, ha="left", va="center", fontsize=8.5)
        ax.text(0.79, node_center, human(right_totals[name]), ha="center", va="center", color="white", weight="bold", fontsize=7.5, zorder=5)
    ax.text(0.21, 0.955, "YAGO predicate-profile category", ha="center", weight="bold", fontsize=11)
    ax.text(0.79, 0.955, "SemOpenAlex URI type", ha="center", weight="bold", fontsize=11)
    heading(
        fig,
        "Bipartite flow of the ambiguous final alignments",
        "“Unclassified by predicates” means the YAGO heuristic abstained—not that the URI or SemOpenAlex type is unknown.",
    )
    fig.subplots_adjust(left=0.04, right=0.96, bottom=0.03, top=0.86)
    fig.savefig(FIGURES / "38_bipartite_alignment_flow.pdf", format="pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def semopenalex_training():
    paths = {
        "TransE": ROOT / "04_embeddings/output/semopenalex/transe_cos/training_stats.json",
        "DistMult": ROOT / "04_embeddings/output/semopenalex/distmult_dot/training_stats.json",
        "ComplEx": ROOT / "04_embeddings/output/semopenalex/complex_dot/training_stats.json",
    }
    summary = []
    distribution = []
    for model, path in paths.items():
        rows = defaultdict(list)
        weights = defaultdict(list)
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if "stats" not in row or "epoch_idx" not in row:
                    continue
                epoch = int(row["epoch_idx"]) + 1
                rows[epoch].append(float(row["stats"]["metrics"]["loss"]))
                weights[epoch].append(float(row["stats"]["count"]))
        for epoch in sorted(rows):
            values = np.array(rows[epoch])
            count_weights = np.array(weights[epoch])
            summary.append(
                [
                    model,
                    epoch,
                    np.average(values, weights=count_weights),
                    np.quantile(values, 0.10),
                    np.quantile(values, 0.90),
                    len(values),
                ]
            )
            if epoch == max(rows):
                distribution.extend([[model, value] for value in values])
    return (
        pd.DataFrame(summary, columns=["Model", "Epoch", "Weighted loss", "P10", "P90", "Partitions"]),
        pd.DataFrame(distribution, columns=["Model", "Partition loss"]),
    )


def fig39_pbg():
    summary, distribution = semopenalex_training()
    palette = {"TransE": SLATE, "DistMult": BLUE, "ComplEx": PURPLE}
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.9))
    for model, subset in summary.groupby("Model"):
        subset = subset.sort_values("Epoch")
        axes[0].plot(subset.Epoch, subset["Weighted loss"], marker="o", linewidth=2, color=palette[model], label=model)
        axes[0].fill_between(subset.Epoch, subset.P10, subset.P90, color=palette[model], alpha=0.12)
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Training loss")
    axes[0].set_yscale("log")
    axes[0].set_xticks([1, 2, 3])
    axes[0].legend()
    clean(axes[0], "both")
    sns.boxenplot(
        data=distribution,
        x="Model",
        y="Partition loss",
        hue="Model",
        palette=palette,
        legend=False,
        showfliers=False,
        ax=axes[1],
    )
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Final-epoch partition loss")
    axes[1].set_yscale("log")
    clean(axes[1], "y")
    heading(
        fig,
        "PyTorch-BigGraph training behavior on SemOpenAlex",
        "Weighted epoch means and 10–90% partition bands use all 16,384 partition statistics per model and epoch on the 9.62B-triple graph.",
    )
    save(fig, "39_semopenalex_pbg_training.pdf")


def case_node(ax, x, y, width, height, title, subtitle, color):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.015",
            facecolor=color,
            edgecolor="white",
            linewidth=1.2,
        )
    )
    ax.text(x + width / 2, y + height * 0.62, title, ha="center", va="center", color="white", weight="bold", fontsize=9)
    ax.text(x + width / 2, y + height * 0.28, subtitle, ha="center", va="center", color="white", fontsize=7.5)


def fig40_cases(identifier_data):
    examples = identifier_data["preferred_examples"]
    cases = [
        ("Externally confirmed", examples["nature and conservation"], GREEN),
        ("Externally contradicted", examples["scientific reports"], RED),
    ]
    fig, axes = plt.subplots(2, 1, figsize=(12, 7.5))
    for ax, (case_title, row, status_color) in zip(axes, cases):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        case_node(ax, 0.04, 0.35, 0.28, 0.34, row["yago_label"], f"YAGO · {row['yago_qid']}", BLUE)
        case_node(
            ax,
            0.68,
            0.35,
            0.28,
            0.34,
            row["semopenalex_label"],
            f"SemOpenAlex {row['semopenalex_type']} · {row['semopenalex_qid']}",
            GREEN,
        )
        ax.annotate(
            "",
            xy=(0.68, 0.52),
            xytext=(0.32, 0.52),
            arrowprops={"arrowstyle": "->", "lw": 3, "color": status_color},
        )
        ax.text(0.50, 0.60, "predicted owl:sameAs", ha="center", color=status_color, weight="bold", fontsize=10)
        result = "QIDs AGREE" if row["agrees"] else "QIDs DISAGREE"
        ax.text(0.50, 0.42, result, ha="center", color=status_color, weight="bold", fontsize=10)
        scores = (
            f"embedding {row['embedding_cosine']:.3f}   ·   "
            f"profile {row['profile_tfidf_score']:.3f}   ·   "
            f"neighbor {row['neighbor_tfidf_score']:.3f}   ·   "
            f"ABC {row['abc_score']:.3f}"
        )
        ax.text(0.50, 0.17, scores, ha="center", fontsize=8.5, color="#475569")
        ax.text(0.04, 0.85, case_title, ha="left", weight="bold", fontsize=11, color=status_color)
    heading(
        fig,
        "Two real alignments show why aggregate scores need external validation",
        "Both pairs come directly from the final A+B+C file; Wikidata QIDs provide independent identity evidence for these examples.",
    )
    save(fig, "40_alignment_case_studies.pdf")


def write_tables(core, extra):
    table_dir = OUT / "tables"
    processing_frame(core).to_csv(table_dir / "22_rdf_processing_outcomes.csv", index=False)
    coverage_frame(core).to_csv(table_dir / "23_target_catalog_coverage.csv", index=False)
    flow_frame(extra)[0].to_csv(table_dir / "24_bipartite_alignment_flows.csv", index=False)
    semopenalex_training()[0].to_csv(table_dir / "25_semopenalex_pbg_training.csv", index=False)
    lines = [
        "# Thesis tables",
        "",
        "These CSV files are intended for native LaTeX tables, not screenshots.",
        "The Markdown below is a compact preview; the CSV files contain the complete results.",
        "",
    ]
    for path in sorted(table_dir.glob("*.csv")):
        table = pd.read_csv(path)
        preview = table.head(20).fillna("")
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
    extra = build_additional(False)
    identifiers = build_identifier_validation(args.refresh)
    fig36_rdf_yield(core)
    fig37_coverage(core)
    fig38_bipartite(extra)
    fig39_pbg()
    fig40_cases(identifiers)
    write_tables(core, extra)
    print(f"Total PDF figures: {len(list(FIGURES.glob('*.pdf')))}")
    print(f"Total CSV tables: {len(list((OUT / 'tables').glob('*.csv')))}")


if __name__ == "__main__":
    main()
