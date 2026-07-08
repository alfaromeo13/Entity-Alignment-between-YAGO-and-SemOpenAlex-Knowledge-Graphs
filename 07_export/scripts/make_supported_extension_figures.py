#!/usr/bin/env python3
"""Generate supported high-value additions from the final alignment catalog."""

from __future__ import annotations

import argparse
import csv
import pickle
import textwrap
from array import array
from collections import defaultdict
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
TABLES = OUT / "tables"
FINAL = (
    ROOT
    / "06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/"
    "abc_w060_035_005_t030.tsv"
)
CACHE_DIR = OUT / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE = CACHE_DIR / "supported_extensions.pkl"

BLUE = "#2563EB"
GREEN = "#16A34A"
CYAN = "#0891B2"
AMBER = "#D97706"
PURPLE = "#7C3AED"
SLATE = "#64748B"
LIGHT = "#E2E8F0"
INK = "#0F172A"


def build(refresh=False):
    if CACHE.exists() and not refresh:
        with CACHE.open("rb") as handle:
            return pickle.load(handle)
    scores = defaultdict(lambda: array("f"))
    total = 0
    ranked = 0
    with FINAL.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            total += 1
            if row.get("source") == "strict_proxy_gold":
                continue
            ranked += 1
            entity_type = row.get("semopenalex_uri_type") or "unknown"
            scores[entity_type].append(float(row.get("abc_score") or 0))
    data = {"total": total, "ranked": ranked, "scores": dict(scores)}
    with CACHE.open("wb") as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return data


def style():
    sns.set_theme(style="whitegrid", context="paper")
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 150,
            "svg.fonttype": "none",
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#CBD5E1",
            "grid.color": LIGHT,
            "text.color": INK,
        }
    )


def heading(fig, title, subtitle):
    fig.suptitle(title, x=0.07, y=0.97, ha="left", fontsize=14, weight="bold")
    fig.text(0.07, 0.895, subtitle, ha="left", fontsize=8.4, color="#475569")


def confidence_table(data):
    rows = []
    for entity_type, values in sorted(data["scores"].items()):
        scores = np.frombuffer(values, dtype=np.float32)
        rows.append(
            {
                "Entity type": entity_type,
                "Ranked ambiguous alignments": len(scores),
                "Mean ABC score": float(scores.mean()),
                "P10": float(np.quantile(scores, 0.10)),
                "Median": float(np.median(scores)),
                "P90": float(np.quantile(scores, 0.90)),
                "Minimum": float(scores.min()),
                "Maximum": float(scores.max()),
            }
        )
    return pd.DataFrame(rows)


def fig45(data):
    eligible = {
        entity_type: np.frombuffer(values, dtype=np.float32)
        for entity_type, values in data["scores"].items()
        if len(values) >= 100
    }
    order = sorted(eligible, key=lambda key: len(eligible[key]), reverse=True)
    columns = 2
    rows = (len(order) + columns - 1) // columns
    fig, axes = plt.subplots(rows, columns, figsize=(11.5, 2.25 * rows), sharex=True)
    axes = np.atleast_1d(axes).ravel()
    bins = np.linspace(0.30, 0.90, 61)
    palette = [BLUE, GREEN, PURPLE, AMBER, CYAN, SLATE, "#DB2777", "#0F766E"]
    for ax, entity_type, color in zip(axes, order, palette):
        values = eligible[entity_type]
        counts, edges = np.histogram(values, bins=bins)
        density = counts / counts.sum()
        centers = (edges[:-1] + edges[1:]) / 2
        ax.fill_between(centers, density, color=color, alpha=0.22)
        ax.plot(centers, density, color=color, linewidth=1.8)
        median = float(np.median(values))
        ax.axvline(median, color=color, linestyle="--", linewidth=1)
        ax.set_title(
            f"{entity_type.title()} · n={len(values):,} · median={median:.3f}",
            loc="left",
            fontsize=9.3,
        )
        ax.set_ylabel("Share")
        sns.despine(ax=ax)
    for ax in axes[len(order) :]:
        ax.axis("off")
    for ax in axes[-columns:]:
        ax.set_xlabel("ABC score")
    heading(
        fig,
        "Final ABC-score distributions differ by entity type",
        "Ranked ambiguous alignments only; strict exact-label proxy rows are excluded because their synthetic high scores would obscure type difficulty.",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    fig.savefig(
        FIGURES / "45_confidence_by_entity_type.svg",
        format="svg",
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def rdf_composition(total):
    groups = [
        ("Direct identity assertion", 1, "owl:sameAs"),
        (
            "Standard reification structure",
            5,
            "rdf:Statement + kg:Alignment types; rdf:subject/predicate/object",
        ),
        (
            "Numerical evidence",
            4,
            "embedding, profile, neighbor, and ABC scores",
        ),
        (
            "Categorical metadata",
            3,
            "SemOpenAlex type, selection source, confidence tier",
        ),
    ]
    triples_per_alignment = sum(row[1] for row in groups)
    return pd.DataFrame(
        [
            {
                "Group": group,
                "Triples per alignment": per_alignment,
                "Total triples": per_alignment * total,
                "Share": per_alignment / triples_per_alignment,
                "Contents": contents,
            }
            for group, per_alignment, contents in groups
        ]
    )


def fig46(composition, total):
    frame = composition.copy()
    colors = [PURPLE, GREEN, BLUE, AMBER]
    fig, (ax, detail_ax) = plt.subplots(
        1,
        2,
        figsize=(12, 5.6),
        gridspec_kw={"width_ratios": [1.05, 1.35], "wspace": 0.16},
    )

    ax.text(
        0,
        0.97,
        "One alignment produces 13 RDF triples",
        transform=ax.transAxes,
        fontsize=11,
        weight="bold",
        va="top",
    )
    left = 0
    for (_, row), color in zip(frame.iterrows(), colors):
        width = int(row["Triples per alignment"])
        ax.barh(0, width, left=left, color=color, height=0.42)
        ax.text(
            left + width / 2,
            0,
            f"{width}\n{row['Share']:.1%}",
            ha="center",
            va="center",
            color="white",
            weight="bold",
            fontsize=8,
        )
        left += width
    ax.set_xlim(0, left)
    ax.set_ylim(-0.6, 1.15)
    ax.set_yticks([])
    ax.set_xlabel("Triples per alignment")
    ax.set_xticks(range(0, left + 1))
    ax.grid(axis="x", alpha=0.55)
    sns.despine(ax=ax, left=True)
    ax.text(
        0,
        0.78,
        f"{total:,}",
        fontsize=18,
        weight="bold",
        color=INK,
    )
    ax.text(0, 0.62, "direct identity links", fontsize=8.5, color=SLATE)
    ax.text(
        left * 0.52,
        0.78,
        f"{int(frame['Total triples'].sum()):,}",
        fontsize=18,
        weight="bold",
        color=INK,
    )
    ax.text(
        left * 0.52,
        0.62,
        "triples in each serialization",
        fontsize=8.5,
        color=SLATE,
    )

    detail_ax.set_xlim(0, 1)
    detail_ax.set_ylim(0, 1)
    detail_ax.axis("off")
    detail_ax.text(
        0,
        0.97,
        "What each semantic layer contains",
        transform=detail_ax.transAxes,
        fontsize=11,
        weight="bold",
        va="top",
    )
    y_positions = [0.82, 0.61, 0.40, 0.19]
    for (_, row), color, y in zip(frame.iterrows(), colors, y_positions):
        detail_ax.add_patch(
            plt.Rectangle(
                (0.0, y - 0.045),
                0.025,
                0.09,
                transform=detail_ax.transAxes,
                facecolor=color,
                edgecolor="none",
            )
        )
        detail_ax.text(
            0.045,
            y + 0.025,
            row.Group,
            transform=detail_ax.transAxes,
            fontsize=9,
            weight="bold",
            va="center",
        )
        detail_ax.text(
            0.98,
            y + 0.025,
            f"{int(row['Triples per alignment'])}/alignment · {row['Total triples'] / 1e6:.2f}M total",
            transform=detail_ax.transAxes,
            fontsize=8,
            color=SLATE,
            ha="right",
            va="center",
        )
        detail_ax.text(
            0.045,
            y - 0.025,
            textwrap.fill(str(row.Contents), width=66),
            transform=detail_ax.transAxes,
            fontsize=7.6,
            color=SLATE,
            va="top",
        )
    heading(
        fig,
        "Composition of the final alignment RDF export",
        "Each owl:sameAs link is accompanied by standard reification and evidence metadata; Turtle and TriG contain equivalent statements.",
    )
    fig.subplots_adjust(left=0.07, right=0.97, bottom=0.10, top=0.80, wspace=0.16)
    fig.savefig(
        FIGURES / "46_rdf_export_composition.svg",
        format="svg",
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    style()
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    data = build(args.refresh)
    confidence = confidence_table(data)
    composition = rdf_composition(data["total"])
    confidence.to_csv(TABLES / "31_confidence_by_entity_type.csv", index=False)
    composition.to_csv(TABLES / "32_rdf_export_composition.csv", index=False)
    fig45(data)
    fig46(composition, data["total"])
    print(f"Wrote {FIGURES / '45_confidence_by_entity_type.svg'}")
    print(f"Wrote {FIGURES / '46_rdf_export_composition.svg'}")


if __name__ == "__main__":
    main()
