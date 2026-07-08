#!/usr/bin/env python3
"""Generate final-evaluation visualizations supported by PBG aggregate metrics."""

from __future__ import annotations

import argparse

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from thesis_statistics import OUT, build_statistics

FIGURES = OUT / "figures"
TABLES = OUT / "tables"
BLUE = "#2563EB"
GREEN = "#16A34A"
PURPLE = "#7C3AED"
AMBER = "#D97706"
RED = "#DC2626"
SLATE = "#64748B"
LIGHT = "#E2E8F0"
INK = "#0F172A"
MODEL_COLORS = {"TransE": BLUE, "DistMult": GREEN, "ComplEx": PURPLE}


def style() -> None:
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
    fig.savefig(FIGURES / filename, format="svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def evaluation_frame(core) -> pd.DataFrame:
    return pd.DataFrame(core["embedding_results"])


def fig51(frame: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.1))
    for ax, dataset in zip(axes, ("YAGO", "SemOpenAlex")):
        subset = frame[frame.Dataset == dataset]
        for row in subset.to_dict("records"):
            color = MODEL_COLORS[row["Model"]]
            offset = (
                (7, -27)
                if dataset == "SemOpenAlex" and row["Model"] == "ComplEx"
                else (7, 7)
            )
            ax.scatter(
                row["MRR"],
                row["Hits@10"],
                s=900 * row["AUC"] ** 2,
                color=color,
                alpha=0.78,
                edgecolor="white",
                linewidth=1.2,
            )
            ax.annotate(
                f"{row['Model']}\nAUC {row['AUC']:.3f}",
                (row["MRR"], row["Hits@10"]),
                xytext=offset,
                textcoords="offset points",
                fontsize=8,
                color=color,
                weight="bold",
            )
        xpad = max((subset.MRR.max() - subset.MRR.min()) * 0.35, 0.015)
        ypad = max((subset["Hits@10"].max() - subset["Hits@10"].min()) * 0.55, 0.012)
        ax.set_xlim(subset.MRR.min() - xpad, subset.MRR.max() + xpad * 2.2)
        ax.set_ylim(subset["Hits@10"].min() - ypad, subset["Hits@10"].max() + ypad * 2)
        ax.set_xlabel("Mean reciprocal rank")
        ax.set_ylabel("Hits@10")
        ax.set_title(f"{dataset} · evaluated triples {int(subset['Test triples'].iloc[0]):,}", loc="left")
        clean(ax)
    heading(
        fig,
        "Final link-prediction model trade-offs",
        "Higher and farther right is better; bubble area encodes AUC and labels report its exact value.",
    )
    save(fig, "51_link_prediction_tradeoff.svg")


def hits_curve_frame(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in frame.to_dict("records"):
        for k, column in ((1, "Hits@1"), (10, "Hits@10"), (50, "Hits@50")):
            rows.append(
                {
                    "Dataset": row["Dataset"],
                    "Model": row["Model"],
                    "K": k,
                    "Hits@K": row[column],
                    "Test triples": row["Test triples"],
                }
            )
    return pd.DataFrame(rows)


def fig52(curves: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.1), sharey=False)
    for ax, dataset in zip(axes, ("YAGO", "SemOpenAlex")):
        subset = curves[curves.Dataset == dataset]
        for model in ("TransE", "DistMult", "ComplEx"):
            model_rows = subset[subset.Model == model]
            ax.plot(
                model_rows.K,
                model_rows["Hits@K"],
                marker="o",
                markersize=5,
                linewidth=2,
                color=MODEL_COLORS[model],
                label=model,
            )
        ax.set_xscale("log")
        ax.set_xticks([1, 10, 50], ["1", "10", "50"])
        ax.set_xlabel("K")
        ax.set_ylabel("Hits@K")
        ax.set_ylim(max(0, subset["Hits@K"].min() - 0.08), 1.02)
        ax.set_title(dataset, loc="left")
        ax.legend(title="")
        clean(ax)
    heading(
        fig,
        "Final Hits@K curves",
        "Lines connect the three K values actually emitted by torchbiggraph_eval: 1, 10, and 50.",
    )
    save(fig, "52_hits_at_k_curves.svg")


def rank_band_frame(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in frame.to_dict("records"):
        bands = (
            ("Rank = 1", row["Hits@1"]),
            ("Ranks 2–10", row["Hits@10"] - row["Hits@1"]),
            ("Ranks 11–50", row["Hits@50"] - row["Hits@10"]),
            ("Rank > 50", 1 - row["Hits@50"]),
        )
        for band, share in bands:
            rows.append(
                {
                    "Dataset": row["Dataset"],
                    "Model": row["Model"],
                    "Rank band": band,
                    "Share": round(max(0.0, share), 6),
                    "Test triples": row["Test triples"],
                }
            )
    return pd.DataFrame(rows)


def fig53(bands: pd.DataFrame) -> None:
    band_order = ["Rank = 1", "Ranks 2–10", "Ranks 11–50", "Rank > 50"]
    colors = [GREEN, BLUE, AMBER, RED]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), sharex=True)
    for ax, dataset in zip(axes, ("YAGO", "SemOpenAlex")):
        subset = bands[bands.Dataset == dataset]
        models = ["TransE", "DistMult", "ComplEx"]
        left = np.zeros(len(models))
        for band, color in zip(band_order, colors):
            values = np.array(
                [
                    subset[
                        (subset.Model == model) & (subset["Rank band"] == band)
                    ].Share.iloc[0]
                    for model in models
                ]
            )
            bars = ax.barh(models, values, left=left, color=color, label=band)
            for bar, value in zip(bars, values):
                if value >= 0.045:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_y() + bar.get_height() / 2,
                        f"{value:.1%}",
                        ha="center",
                        va="center",
                        color="white" if band != "Ranks 11–50" else INK,
                        fontsize=7.5,
                        weight="bold",
                    )
            left += values
        ax.set_xlim(0, 1)
        ax.set_xlabel("Share of evaluated triples")
        ax.set_title(dataset, loc="left")
        clean(ax, "x")
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 0.02))
    heading(
        fig,
        "Where evaluated triples rank",
        "Aggregate bands derived from reported Hits@1, Hits@10, and Hits@50 rates; individual triple ranks were not logged.",
    )
    save(fig, "53_rank_band_composition.svg", rect=(0, 0.10, 1, 0.88))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    style()
    TABLES.mkdir(parents=True, exist_ok=True)
    frame = evaluation_frame(build_statistics(args.refresh))
    curves = hits_curve_frame(frame)
    bands = rank_band_frame(frame)
    bands.to_csv(TABLES / "38_link_prediction_rank_bands.csv", index=False)
    fig51(frame)
    fig52(curves)
    fig53(bands)
    print("Wrote Figures 51–53 and Table 38")


if __name__ == "__main__":
    main()
