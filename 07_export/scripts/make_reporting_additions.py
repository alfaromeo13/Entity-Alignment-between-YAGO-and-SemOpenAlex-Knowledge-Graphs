#!/usr/bin/env python3
"""Port the defensible, non-duplicative analyses found in 09_reporting."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from additional_statistics import OUT, build_additional
from external_identifier_validation import build_identifier_validation
from thesis_statistics import build_statistics

FIGURES = OUT / "figures"
BLUE = "#2563EB"
GREEN = "#16A34A"
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
    for divisor, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= divisor:
            return f"{value/divisor:.1f}{suffix}"
    return f"{value:,.0f}"


def baseline_frames(core):
    summary = core["summaries"]["baseline_summary"]
    total = int(summary["final_alignments"])
    proxy = int(summary["final_pairs_in_proxy_gold"])
    sources = pd.DataFrame(
        [
            ["Strict proxy", proxy, proxy / total],
            ["Embedding-ranked", total - proxy, (total - proxy) / total],
        ],
        columns=["Source", "Alignments", "Share"],
    )
    types = pd.DataFrame(core["summaries"]["baseline_types"]).rename(
        columns={"semopenalex_type": "Type", "count": "Alignments"}
    )
    return sources, types


def fig31_baseline_composition(core):
    sources, types = baseline_frames(core)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.9), gridspec_kw={"width_ratios": [1, 1.4]})

    left = 0
    colors = [GREEN, BLUE]
    for (_, row), color in zip(sources.iterrows(), colors):
        axes[0].barh(["Stage 05 baseline"], [row.Alignments], left=left, color=color, label=row.Source)
        axes[0].text(
            left + row.Alignments / 2,
            0,
            f"{human(row.Alignments)}\n{row.Share:.1%}",
            ha="center",
            va="center",
            color="white",
            weight="bold",
            fontsize=9,
        )
        left += row.Alignments
    axes[0].set_xlabel("Alignments")
    axes[0].legend(loc="lower center", bbox_to_anchor=(0.5, -0.30), ncol=2)
    clean(axes[0], "x")

    shown = types.nlargest(8, "Alignments").sort_values("Alignments")
    bars = axes[1].barh(shown.Type, shown.Alignments, color=PURPLE)
    axes[1].bar_label(bars, labels=[human(value) for value in shown.Alignments], padding=3, fontsize=7.5)
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Alignments (log scale)")
    clean(axes[1], "x")

    heading(
        fig,
        "Stage 05 baseline composition",
        f"Exact source and SemOpenAlex-type counts across all {int(sources.Alignments.sum()):,} taxonomy-aware strict baseline alignments.",
    )
    save(fig, "31_baseline_composition.pdf")


def score_histogram_frame(extra):
    rows = []
    for group, histogram in extra["final"]["score_histograms"].items():
        for row in histogram:
            rows.append([group, row["score_bin"], row["count"]])
    return pd.DataFrame(rows, columns=["Source group", "ABC score bin", "Count"])


def fig32_score_mixture(extra):
    frame = score_histogram_frame(extra)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    colors = {"Strict proxy": GREEN, "Ranked ambiguous": BLUE}
    full_bins = np.round(np.arange(0.30, 1.001, 0.01), 2)
    proxy_first_bin_share = None

    for group in ("Ranked ambiguous", "Strict proxy"):
        sub = (
            frame[frame["Source group"] == group]
            .set_index("ABC score bin")
            .reindex(full_bins, fill_value=0)
            .rename_axis("ABC score bin")
            .reset_index()
        )
        x_values = sub["ABC score bin"] + 0.005
        positive = sub.Count > 0
        if group == "Ranked ambiguous":
            axes[0].step(
                x_values[positive],
                sub.loc[positive, "Count"],
                where="mid",
                color=colors[group],
                linewidth=2,
                label=group,
            )
        else:
            axes[0].vlines(
                x_values[positive],
                1,
                sub.loc[positive, "Count"],
                color=colors[group],
                linewidth=2,
                alpha=0.55,
            )
            axes[0].scatter(
                x_values[positive],
                sub.loc[positive, "Count"],
                color=colors[group],
                s=24,
                zorder=3,
                label=group,
            )
        cumulative = sub.Count.cumsum() / sub.Count.sum()
        axes[1].step(
            x_values,
            cumulative,
            where="post",
            color=colors[group],
            linewidth=2,
            label=group,
        )
        if group == "Strict proxy":
            proxy_first = int(np.flatnonzero(positive.to_numpy())[0])
            proxy_first_bin_share = float(cumulative.iloc[proxy_first])

    axes[0].axvline(0.30, color=RED, linestyle="--", linewidth=1.4)
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Final ABC score")
    axes[0].set_ylabel("Alignments per 0.01 bin (log scale)")
    axes[0].legend()
    clean(axes[0], "both")

    axes[1].axvline(
        0.30,
        color=RED,
        linestyle="--",
        linewidth=1.4,
        label="Ranked-pair threshold 0.30",
    )
    if proxy_first_bin_share is not None:
        axes[1].annotate(
            f"{proxy_first_bin_share:.1%} of strict proxies\noccupy the first proxy bin",
            xy=(0.955, proxy_first_bin_share),
            xytext=(0.77, 0.72),
            fontsize=7.5,
            color=SLATE,
            arrowprops={"arrowstyle": "->", "color": SLATE, "linewidth": 0.8},
        )
    axes[1].set_xlabel("Final ABC score")
    axes[1].set_ylabel("Cumulative share within source group")
    axes[1].set_ylim(0, 1.02)
    axes[1].legend()
    clean(axes[1], "both")

    heading(
        fig,
        "The final-score distribution is a mixture of two selection mechanisms",
        "Strict proxies use fixed 1.0 embedding/profile markers, forcing ABC scores near 0.95–0.99; these are not calibrated probabilities.",
    )
    save(fig, "32_final_score_mixture.pdf")


def type_evolution_frame(core):
    labels = {
        "baseline": "Baseline",
        "A+B": "A+B",
        "C only": "C",
        "A+B+C final": "A+B+C",
    }
    columns = {
        "author_count": "Author",
        "work_count": "Work",
        "institution_count": "Institution",
        "source_count": "Source",
    }
    rows = []
    for row in core["summaries"]["systems"]:
        if row["system"] not in labels:
            continue
        for column, entity_type in columns.items():
            rows.append([labels[row["system"]], entity_type, int(row[column])])
    return pd.DataFrame(rows, columns=["System", "Type", "Alignments"])


def fig33_type_evolution(core):
    frame = type_evolution_frame(core)
    systems = ["Baseline", "A+B", "C", "A+B+C"]
    types = ["Author", "Work", "Institution", "Source"]
    palette = {"Author": BLUE, "Work": GREEN, "Institution": AMBER, "Source": PURPLE}
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.15, 1]})

    for entity_type in types:
        sub = frame[frame.Type == entity_type].set_index("System").loc[systems]
        axes[0].plot(
            systems,
            sub.Alignments,
            marker="o",
            markersize=6,
            linewidth=2,
            color=palette[entity_type],
            label=entity_type,
        )
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Alignments (log scale)")
    axes[0].legend(ncol=2)
    clean(axes[0], "y")

    pivot = frame.pivot(index="System", columns="Type", values="Alignments").loc[systems, types]
    change = (pivot.div(pivot.loc["Baseline"]) - 1) * 100
    display = change.loc[["A+B", "C", "A+B+C"]]
    annotations = display.map(lambda value: f"{value:+.1f}%")
    bound = max(5, float(np.nanmax(np.abs(display.to_numpy()))))
    sns.heatmap(
        display,
        annot=annotations,
        fmt="",
        cmap="RdYlGn",
        center=0,
        vmin=-bound,
        vmax=bound,
        linewidths=0.6,
        cbar_kws={"label": "Change from baseline (%)"},
        ax=axes[1],
    )
    axes[1].set_xlabel("SemOpenAlex entity type")
    axes[1].set_ylabel("")
    axes[1].tick_params(axis="y", rotation=0)

    heading(
        fig,
        "Entity-type evolution across experimental systems",
        "This is a coverage comparison, not an accuracy ranking; the heatmap reports count change relative to the Stage 05 baseline.",
    )
    save(fig, "33_entity_type_evolution.pdf")


def correlation_inputs(core):
    frames = []
    for group, rows in core["systems"]["samples"].items():
        if group not in {"Baseline-shared", "Final-only"}:
            continue
        frame = pd.DataFrame(rows)
        frame["Cohort"] = "Accepted ambiguous"
        frames.append(frame)
    rejected = pd.DataFrame(core["rejected"])
    rejected["Cohort"] = "Threshold rejected"
    frames.append(rejected)
    return pd.concat(frames, ignore_index=True)


def correlation_table(core):
    frame = correlation_inputs(core)
    columns = ["embedding_cosine", "profile_tfidf_score", "neighbor_tfidf_score", "abc_score"]
    rows = []
    for cohort, subset in frame.groupby("Cohort"):
        matrix = subset[columns].corr(method="pearson")
        for left in columns:
            for right in columns:
                rows.append([cohort, left, right, matrix.loc[left, right], len(subset)])
    return pd.DataFrame(rows, columns=["Cohort", "Score 1", "Score 2", "Pearson r", "Rows"])


def fig34_correlations(core):
    frame = correlation_inputs(core)
    columns = ["embedding_cosine", "profile_tfidf_score", "neighbor_tfidf_score", "abc_score"]
    labels = ["Embedding", "Profile", "Neighbor", "ABC"]
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.9))
    for ax, cohort in zip(axes, ("Accepted ambiguous", "Threshold rejected")):
        subset = frame[frame.Cohort == cohort]
        matrix = subset[columns].corr(method="pearson")
        sns.heatmap(
            matrix,
            annot=True,
            fmt=".2f",
            cmap="vlag",
            center=0,
            vmin=-1,
            vmax=1,
            square=True,
            linewidths=0.6,
            cbar=ax is axes[1],
            cbar_kws={"label": "Pearson correlation", "shrink": 0.75},
            xticklabels=labels,
            yticklabels=labels,
            ax=ax,
        )
        ax.set_title(f"{cohort} · n={len(subset):,}", loc="left")
        ax.tick_params(axis="x", rotation=30)
        ax.tick_params(axis="y", rotation=0)
    heading(
        fig,
        "Evidence correlations change across the decision boundary",
        "Accepted values use deterministic final-alignment samples; rejected values include every pair removed between thresholds 0.25 and 0.30.",
    )
    save(fig, "34_evidence_correlation_by_decision.pdf")


def identifier_frame(identifier_data):
    return pd.DataFrame(identifier_data["rows"])


def fig35_external_identifiers(identifier_data):
    frame = identifier_frame(identifier_data)
    order = ["source", "publisher", "funder", "institution", "concept"]
    sources = ["Strict proxy", "Ranked ambiguous"]
    overall_rows = []
    for entity_type, subset in frame.groupby("Type"):
        checkable = subset["Externally checkable"].sum()
        agree = subset["QID agreement"].sum()
        overall_rows.append(
            {
                "Type": entity_type,
                "Source": "Overall",
                "Final alignments": subset["Final alignments"].sum(),
                "Externally checkable": checkable,
                "QID agreement": agree,
                "Checkable share": checkable / subset["Final alignments"].sum(),
                "Agreement rate": agree / checkable if checkable else np.nan,
            }
        )
    combined = pd.concat([frame, pd.DataFrame(overall_rows)], ignore_index=True)
    rates = combined.pivot(index="Type", columns="Source", values="Agreement rate").loc[
        order, sources + ["Overall"]
    ]
    checkable = combined.pivot(
        index="Type", columns="Source", values="Externally checkable"
    ).loc[order, sources + ["Overall"]]
    annotations = rates.copy().astype(object)
    for entity_type in order:
        for source in sources + ["Overall"]:
            rate = rates.loc[entity_type, source]
            n = int(checkable.loc[entity_type, source])
            annotations.loc[entity_type, source] = (
                f"{rate:.1%}\n(n={n:,})" if pd.notna(rate) else "n/a"
            )

    coverage = (
        combined[combined.Source == "Overall"]
        .set_index("Type")
        .loc[order, ["Final alignments", "Externally checkable"]]
    )
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(11.8, 5.2),
        gridspec_kw={"width_ratios": [1.25, 1]},
    )
    sns.heatmap(
        rates * 100,
        annot=annotations,
        fmt="",
        cmap="RdYlGn",
        vmin=0,
        vmax=100,
        linewidths=0.7,
        cbar_kws={"label": "Wikidata-QID agreement (%)"},
        ax=axes[0],
    )
    axes[0].set_xlabel("Alignment source")
    axes[0].set_ylabel("SemOpenAlex type")
    axes[0].tick_params(axis="x", rotation=20)
    axes[0].tick_params(axis="y", rotation=0)

    y = np.arange(len(order))
    axes[1].barh(
        y,
        coverage["Final alignments"],
        color="#CBD5E1",
        label="All final alignments",
    )
    bars = axes[1].barh(
        y,
        coverage["Externally checkable"],
        color=PURPLE,
        label="With QIDs on both sides",
    )
    axes[1].set_yticks(y, order)
    axes[1].invert_yaxis()
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Alignment count (log scale)")
    axes[1].bar_label(
        bars,
        labels=[
            f"{value:,}" for value in coverage["Externally checkable"]
        ],
        padding=3,
        fontsize=7,
    )
    axes[1].legend(loc="lower center", bbox_to_anchor=(0.5, -0.28))
    clean(axes[1], "x")

    heading(
        fig,
        "External identifiers expose strongly type-dependent alignment reliability",
        "Partial validation only: agreement compares YAGO URI QIDs with SemOpenAlex owl:sameAs Wikidata QIDs where both are available.",
    )
    save(fig, "35_external_identifier_agreement.pdf")


def write_research_question_map(identifier_data):
    frame = identifier_frame(identifier_data)
    overall = frame.groupby("Type")[["Externally checkable", "QID agreement"]].sum()
    rates = overall["QID agreement"] / overall["Externally checkable"]
    lines = [
        "# Research-question evidence map",
        "",
        "This index maps the five questions in `Disposition of the Master.pdf` to the strongest generated evidence.",
        "",
        "## Q1 — preprocessing and transformation",
        "",
        "- Figures 01, 17–24, 36, 43–44 and 47–50: scale, raw RDF yield, observed predicates/types, formal ontology/schema, topology, distribution tails, namespaces and partitioning scale.",
        "- Tables 01, 09, 11–12, 28–30 and 33–37: encoded graph, relation, observed-type, formal-schema, ontology-provenance, distribution and partition statistics.",
        "- The methodological *how* belongs in prose; these figures establish the resulting scale and structure.",
        "",
        "## Q2 — normalized labels as candidate generators",
        "",
        "- Figures 06–08 and 25: candidate attrition, ambiguity tails, type-specific ambiguity and the largest label blocks.",
        "- Figure 31: strict-label proxy versus ranked-ambiguous baseline composition.",
        "- Labels are effective for narrowing the search space, but label equality must not be described as ground-truth identity.",
        "",
        "## Q3 — embeddings for ambiguous candidates",
        "",
        "- Figures 04–05, 39 and 51–53: final link-prediction comparison, model trade-offs, Hits@K/rank bands, plus YAGO and SemOpenAlex PBG training dynamics.",
        "- Tables 02 and 38 preserve the final metrics and derived aggregate rank bands.",
        "- Figures 09, 13–15, 26, 29, 32, 34 and 45: score selection, evidence distributions, type-specific confidence and decision-cohort interactions.",
        "- The evidence supports candidate reranking utility, not unrestricted all-vs-all alignment.",
        "",
        "## Q4 — type and predicate-profile filtering",
        "",
        "- Figures 06 and 10: exact filter attrition and rejected type-pair heatmap.",
        "- Figures 15, 28, 35 and 38: evidence/type behavior, accepted type matrix, external-ID agreement and aggregate bipartite flows.",
        "- The very low institution/concept QID agreement identifies a limitation of the current proxy bypass and broad unknown-profile handling.",
        "",
        "## Q5 — final scale, quality and limitations",
        "",
        "- Figures 11–16, 26–28, 31–38 and 40: system comparison, overlap, sensitivity, score behavior, final composition, coverage, flow and concrete externally checked cases.",
        "- Figures 41–42: alignment-aware neighborhood preservation and topology change after adding identity bridges, measured on the capped aligned-entity context graph.",
        "- Figure 46: exact composition of the direct identity assertions, reification provenance and evidence metadata in the final RDF export.",
        "- Tables 05–08, 13–14 and 16–38 provide the exact reportable values.",
        f"- External-QID subset: source {rates.get('source', float('nan')):.1%}, publisher {rates.get('publisher', float('nan')):.1%}, funder {rates.get('funder', float('nan')):.1%}, institution {rates.get('institution', float('nan')):.1%}, concept {rates.get('concept', float('nan')):.1%}.",
        "- These rates are subset diagnostics, not overall precision. A manually annotated stratified sample is still required for a defensible absolute precision estimate.",
        "",
        "## Remaining evidence gap",
        "",
        "The reproducible study package in `07_export/validation/study/` contains a blinded, stratified 500-pair annotation sheet but no human verdicts yet. The remaining evaluation step is to record correct / incorrect / uncertain judgments and run the provided summary script for weighted precision, confidence intervals, score reliability and error categories.",
    ]
    (OUT / "RESEARCH_QUESTION_EVIDENCE.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_tables(core, extra, identifier_data):
    table_dir = OUT / "tables"
    sources, types = baseline_frames(core)
    sources.to_csv(table_dir / "16_baseline_source_composition.csv", index=False)
    types.to_csv(table_dir / "17_baseline_type_composition.csv", index=False)
    score_histogram_frame(extra).to_csv(table_dir / "18_final_score_histogram.csv", index=False)
    type_evolution_frame(core).to_csv(table_dir / "19_entity_type_evolution.csv", index=False)
    correlation_table(core).to_csv(table_dir / "20_evidence_correlations.csv", index=False)
    identifier_frame(identifier_data).to_csv(
        table_dir / "21_external_identifier_validation.csv",
        index=False,
    )

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
    identifier_data = build_identifier_validation(args.refresh)
    fig31_baseline_composition(core)
    fig32_score_mixture(extra)
    fig33_type_evolution(core)
    fig34_correlations(core)
    fig35_external_identifiers(identifier_data)
    write_tables(core, extra, identifier_data)
    write_research_question_map(identifier_data)
    print(f"Total PDF figures: {len(list(FIGURES.glob('*.pdf')))}")
    print(f"Total CSV tables: {len(list((OUT / 'tables').glob('*.csv')))}")


if __name__ == "__main__":
    main()
