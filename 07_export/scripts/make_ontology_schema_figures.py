#!/usr/bin/env python3
"""Generate formal ontology and semantic predicate-connectivity analyses."""

from __future__ import annotations

import argparse
import hashlib
from collections import Counter, defaultdict, deque
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd
from rdflib import Graph, OWL, RDF, RDFS, SH, URIRef
from rdflib.collection import Collection
import seaborn as sns

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
OUT = ROOT / "07_export/visualizations"
FIGURES = OUT / "figures"
TABLES = OUT / "tables"
YAGO_SCHEMA = ROOT / "01_raw/yago/yago-schema.ttl"
YAGO_TAXONOMY = ROOT / "01_raw/yago/yago-taxonomy.ttl"
SOA_SCHEMA = ROOT / "01_raw/semopenalex/semopenalex-ontology.ttl"

BLUE = "#2563EB"
GREEN = "#16A34A"
PURPLE = "#7C3AED"
AMBER = "#D97706"
SLATE = "#64748B"
LIGHT = "#E2E8F0"
INK = "#0F172A"


def local_name(value) -> str:
    text = str(value)
    return text.rsplit("#", 1)[-1].rsplit("/", 1)[-1].replace("_", " ")


def namespace(value) -> str:
    text = str(value)
    if "#" in text:
        return text.rsplit("#", 1)[0] + "#"
    return text.rsplit("/", 1)[0] + "/"


def graph_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ranges_from_property(graph: Graph, prop) -> list[tuple[str, URIRef]]:
    result = [
        ("object", value) for value in graph.objects(prop, SH["class"])
    ] + [
        ("datatype", value) for value in graph.objects(prop, SH.datatype)
    ]
    for alternatives in graph.objects(prop, SH["or"]):
        try:
            members = Collection(graph, alternatives)
        except ValueError:
            continue
        for member in members:
            result.extend(
                ("object", value)
                for value in graph.objects(member, SH["class"])
            )
            result.extend(
                ("datatype", value)
                for value in graph.objects(member, SH.datatype)
            )
    return result


def shape_signatures(dataset: str, graph: Graph) -> list[dict[str, str]]:
    rows = []
    for shape in set(graph.subjects(RDF.type, SH.NodeShape)):
        domains = list(graph.objects(shape, SH.targetClass)) or [shape]
        for prop in graph.objects(shape, SH.property):
            paths = list(graph.objects(prop, SH.path))
            ranges = ranges_from_property(graph, prop) or [("unspecified", None)]
            for domain in domains:
                for predicate in paths:
                    for kind, range_value in ranges:
                        rows.append(
                            {
                                "Dataset": dataset,
                                "Domain URI": str(domain),
                                "Domain": local_name(domain),
                                "Predicate URI": str(predicate),
                                "Predicate": local_name(predicate),
                                "Range URI": str(range_value) if range_value else "",
                                "Range": local_name(range_value) if range_value else "Unspecified",
                                "Property kind": kind,
                                "Predicate namespace": namespace(predicate),
                            }
                        )
    return rows


def hierarchy_summary(graph: Graph) -> dict[str, int]:
    edges = {
        (str(child), str(parent))
        for child, parent in graph.subject_objects(RDFS.subClassOf)
        if isinstance(child, URIRef) and isinstance(parent, URIRef)
    }
    nodes = {value for edge in edges for value in edge}
    children = {child for child, _ in edges}
    parents = {parent for _, parent in edges}
    roots = parents - children
    adjacency = defaultdict(list)
    for child, parent in edges:
        adjacency[parent].append(child)
    depth = {root: 0 for root in roots}
    queue = deque(roots)
    while queue:
        parent = queue.popleft()
        for child in adjacency[parent]:
            if child not in depth:
                depth[child] = depth[parent] + 1
                queue.append(child)
    return {
        "hierarchy_nodes": len(nodes),
        "subclass_edges": len(edges),
        "root_classes": len(roots),
        # Maximum shortest distance from a root. Visiting each node once makes
        # the measure robust to cycles and multiple inheritance.
        "maximum_observed_depth": max(depth.values(), default=0),
    }


def schema_summary(dataset: str, graph: Graph, hierarchy: Graph, signatures):
    shapes = set(graph.subjects(RDF.type, SH.NodeShape))
    declared_classes = set(graph.subjects(RDF.type, OWL.Class)) | set(
        graph.subjects(RDF.type, RDFS.Class)
    )
    declared_object_properties = set(
        graph.subjects(RDF.type, OWL.ObjectProperty)
    )
    declared_datatype_properties = set(
        graph.subjects(RDF.type, OWL.DatatypeProperty)
    )
    declared_annotation_properties = set(
        graph.subjects(RDF.type, OWL.AnnotationProperty)
    )
    predicates = defaultdict(set)
    for row in signatures:
        predicates[row["Predicate URI"]].add(row["Property kind"])
    property_counts = Counter()
    for kinds in predicates.values():
        if kinds == {"object"}:
            property_counts["Object properties"] += 1
        elif kinds == {"datatype"}:
            property_counts["Datatype properties"] += 1
        elif "object" in kinds and "datatype" in kinds:
            property_counts["Mixed-range properties"] += 1
        else:
            property_counts["Unspecified properties"] += 1
    used_namespaces = {
        row["Predicate namespace"] for row in signatures
    }
    hierarchy_values = hierarchy_summary(hierarchy)
    values = {
        "Node shapes": len(shapes),
        "Declared classes": len(declared_classes),
        "Declared object properties": len(declared_object_properties),
        "Declared datatype properties": len(declared_datatype_properties),
        "Declared annotation properties": len(declared_annotation_properties),
        "Unique constrained predicates": len(predicates),
        "SHACL object-range predicates": property_counts["Object properties"],
        "SHACL datatype-range predicates": property_counts["Datatype properties"],
        "SHACL mixed-range predicates": property_counts["Mixed-range properties"],
        "Shape-property constraints": len(
            list(graph.triples((None, SH.property, None)))
        ),
        "Predicate namespaces reused": len(used_namespaces),
        **hierarchy_values,
    }
    return [
        {"Dataset": dataset, "Metric": metric, "Value": value}
        for metric, value in values.items()
    ]


def build_data():
    yago_schema = Graph().parse(YAGO_SCHEMA, format="turtle")
    yago_taxonomy = Graph().parse(YAGO_TAXONOMY, format="turtle")
    soa_schema = Graph().parse(SOA_SCHEMA, format="turtle")
    # YAGO's core schema and large taxonomy jointly define its class hierarchy.
    yago_hierarchy = yago_schema + yago_taxonomy
    yago_signatures = shape_signatures("YAGO", yago_schema)
    soa_signatures = shape_signatures("SemOpenAlex", soa_schema)
    inventory = (
        schema_summary("YAGO", yago_schema, yago_hierarchy, yago_signatures)
        + schema_summary("SemOpenAlex", soa_schema, soa_schema, soa_signatures)
    )
    provenance = pd.DataFrame(
        [
            ["YAGO schema", str(YAGO_SCHEMA.relative_to(ROOT)), graph_sha256(YAGO_SCHEMA)],
            ["YAGO taxonomy", str(YAGO_TAXONOMY.relative_to(ROOT)), graph_sha256(YAGO_TAXONOMY)],
            ["SemOpenAlex ontology", str(SOA_SCHEMA.relative_to(ROOT)), graph_sha256(SOA_SCHEMA)],
        ],
        columns=["Source", "Path", "SHA-256"],
    )
    return (
        pd.DataFrame(inventory),
        pd.DataFrame(yago_signatures + soa_signatures),
        provenance,
    )


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
    fig.suptitle(title, x=0.065, y=0.98, ha="left", fontsize=14, weight="bold")
    fig.text(0.065, 0.925, subtitle, ha="left", fontsize=8.4, color="#475569")


def grouped_metric(ax, inventory, metrics, title, log=False):
    frame = inventory[inventory.Metric.isin(metrics)].copy()
    frame["Metric"] = pd.Categorical(frame["Metric"], metrics)
    frame = frame.sort_values("Metric")
    frame["Display metric"] = (
        frame["Metric"]
        .astype(str)
        .str.replace("_", " ")
        .str.title()
        .str.replace("Shacl", "SHACL", regex=False)
    )
    sns.barplot(
        data=frame,
        y="Display metric",
        x="Value",
        hue="Dataset",
        palette={"YAGO": BLUE, "SemOpenAlex": GREEN},
        ax=ax,
    )
    if log:
        ax.set_xscale("log")
    for container in ax.containers:
        ax.bar_label(
            container,
            labels=[f"{bar.get_width():,.0f}" for bar in container],
            padding=3,
            fontsize=7,
        )
    ax.set_title(title, loc="left")
    ax.set_xlabel("Count" + (" (log scale)" if log else ""))
    ax.set_ylabel("")
    ax.legend(title="", fontsize=7)
    sns.despine(ax=ax)


def fig43(inventory):
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.5))
    grouped_metric(
        axes[0],
        inventory,
        ["Node shapes", "Declared classes", "Shape-property constraints"],
        "Core schema",
    )
    grouped_metric(
        axes[1],
        inventory,
        [
            "Declared object properties",
            "Declared datatype properties",
            "Declared annotation properties",
            "SHACL object-range predicates",
            "SHACL datatype-range predicates",
        ],
        "Property semantics",
    )
    grouped_metric(
        axes[2],
        inventory,
        ["hierarchy_nodes", "subclass_edges", "maximum_observed_depth"],
        "Class hierarchy",
        log=True,
    )
    heading(
        fig,
        "Formal RDF schema comparison: YAGO and SemOpenAlex",
        "Parsed from YAGO 4.5 schema/taxonomy and the pinned official SemOpenAlex OWL/SHACL ontology; hierarchy and core-schema counts are deliberately separated.",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(
        FIGURES / "43_formal_schema_comparison.pdf",
        format="pdf",
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


PRIORITY_DOMAINS = {
    "YAGO": [
        "Person",
        "CreativeWork",
        "Organization",
        "Place",
        "Event",
        "Book",
        "EducationalOrganization",
    ],
    "SemOpenAlex": [
        "Author",
        "Work",
        "Authorship",
        "Institution",
        "Source",
        "Publisher",
        "Concept",
    ],
}


def selected_object_signatures(signatures, dataset, maximum=14):
    subset = signatures[
        (signatures.Dataset == dataset)
        & (signatures["Property kind"] == "object")
        & (signatures.Domain.isin(PRIORITY_DOMAINS[dataset]))
    ].drop_duplicates(["Domain", "Predicate", "Range"])
    ordering = {name: index for index, name in enumerate(PRIORITY_DOMAINS[dataset])}
    subset = subset.assign(
        domain_order=subset.Domain.map(ordering),
        key=subset.Predicate.str.lower(),
    ).sort_values(["domain_order", "key", "Range"])
    # Round-robin selection prevents one richly described class (for example
    # YAGO Person or SemOpenAlex Work) from occupying the entire figure.
    selected = []
    for rank in range(2):
        for domain in PRIORITY_DOMAINS[dataset]:
            rows = subset[subset.Domain == domain]
            if rank < len(rows):
                selected.append(rows.iloc[rank])
            if len(selected) == maximum:
                break
    return pd.DataFrame(selected, columns=subset.columns)


def draw_signature_network(ax, frame, color, title):
    rows = frame.to_dict("records")
    count = len(rows)
    row_y = np.linspace(0.90, 0.10, count) if count else []
    domain_rows = defaultdict(list)
    range_rows = defaultdict(list)
    for y, row in zip(row_y, rows):
        domain_rows[row["Domain"]].append(y)
        range_rows[row["Range"]].append(y)
    domain_names = list(domain_rows)
    range_names = list(range_rows)
    domain_y = {
        name: y
        for name, y in zip(
            domain_names,
            np.linspace(0.88, 0.12, len(domain_names)) if domain_names else [],
        )
    }
    range_y = {
        name: y
        for name, y in zip(
            range_names,
            np.linspace(0.90, 0.10, len(range_names)) if range_names else [],
        )
    }
    for y, row in zip(row_y, rows):
        ax.add_patch(
            FancyArrowPatch(
                (0.24, domain_y[row["Domain"]]),
                (0.47, y),
                arrowstyle="-",
                color="#CBD5E1",
                linewidth=1,
                connectionstyle="arc3,rad=0.05",
            )
        )
        ax.add_patch(
            FancyArrowPatch(
                (0.65, y),
                (0.82, range_y[row["Range"]]),
                arrowstyle="-|>",
                mutation_scale=8,
                color=color,
                alpha=0.65,
                linewidth=1.2,
                connectionstyle="arc3,rad=0.05",
            )
        )
        ax.add_patch(
            FancyBboxPatch(
                (0.47, y - 0.018),
                0.18,
                0.036,
                boxstyle="round,pad=0.006",
                facecolor="#F8FAFC",
                edgecolor=color,
                linewidth=0.8,
            )
        )
        ax.text(0.56, y, row["Predicate"], ha="center", va="center", fontsize=5.8)
    for name, y in domain_y.items():
        ax.add_patch(
            FancyBboxPatch(
                (0.03, y - 0.026),
                0.21,
                0.052,
                boxstyle="round,pad=0.008",
                facecolor=color,
                edgecolor="white",
            )
        )
        ax.text(0.135, y, name, ha="center", va="center", fontsize=7, color="white", weight="bold")
    for name, y in range_y.items():
        ax.add_patch(
            FancyBboxPatch(
                (0.82, y - 0.026),
                0.16,
                0.052,
                boxstyle="round,pad=0.008",
                facecolor="#F1F5F9",
                edgecolor=color,
            )
        )
        ax.text(0.90, y, name, ha="center", va="center", fontsize=6.6)
    ax.text(0.135, 0.99, "Domain class", ha="center", va="top", weight="bold", fontsize=8)
    ax.text(0.56, 0.99, "Object property", ha="center", va="top", weight="bold", fontsize=8)
    ax.text(0.90, 0.99, "Range class", ha="center", va="top", weight="bold", fontsize=8)
    ax.set_title(title, loc="left")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.axis("off")


def fig44(signatures):
    fig, axes = plt.subplots(1, 2, figsize=(14, 8.2))
    draw_signature_network(
        axes[0],
        selected_object_signatures(signatures, "YAGO"),
        BLUE,
        "YAGO",
    )
    draw_signature_network(
        axes[1],
        selected_object_signatures(signatures, "SemOpenAlex"),
        GREEN,
        "SemOpenAlex",
    )
    heading(
        fig,
        "Semantic predicate connectivity in the two RDF schemas",
        "Selected alignment-relevant SHACL signatures show the formal domain → object property → range structure; the complete signatures are exported in Table 29.",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(
        FIGURES / "44_predicate_connectivity.pdf",
        format="pdf",
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.parse_args()
    style()
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    inventory, signatures, provenance = build_data()
    inventory.to_csv(TABLES / "28_formal_schema_inventory.csv", index=False)
    signatures.to_csv(TABLES / "29_semantic_predicate_signatures.csv", index=False)
    provenance.to_csv(TABLES / "30_ontology_source_provenance.csv", index=False)
    fig43(inventory)
    fig44(signatures)
    print(f"Wrote {FIGURES / '43_formal_schema_comparison.pdf'}")
    print(f"Wrote {FIGURES / '44_predicate_connectivity.pdf'}")


if __name__ == "__main__":
    main()
