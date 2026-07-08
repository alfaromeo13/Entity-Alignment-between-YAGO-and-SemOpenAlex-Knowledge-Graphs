#!/usr/bin/env python3
"""Build Stage 05 taxonomy-aware profiles without a silent ``unknown``."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from type_system import (
    RDF_TYPE,
    TaxonomyClassifier,
    file_sha256,
    normalize_uri,
    short_name,
)

OUTPUT_COLUMNS = [
    "yago_entity",
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


def load_entities(paths: list[Path], column: str) -> set[str]:
    entities: set[str] = set()
    for path in paths:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if column not in (reader.fieldnames or ()):
                raise SystemExit(f"{path} does not contain column {column!r}")
            for row in reader:
                value = row.get(column, "").strip()
                if value:
                    entities.add(value)
        print(f"Loaded targets after {path}: {len(entities):,}", flush=True)
    return entities


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entities", required=True, nargs="+", type=Path)
    parser.add_argument("--entity-column", default="yago_entity")
    parser.add_argument("--graph-dir", required=True, type=Path)
    parser.add_argument("--taxonomy", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--audit-output", required=True, type=Path)
    parser.add_argument("--progress-every", type=int, default=100_000_000)
    args = parser.parse_args()

    targets = load_entities(args.entities, args.entity_column)
    classifier = TaxonomyClassifier(args.taxonomy)
    print(
        f"Loaded taxonomy parents for {len(classifier.parents):,} classes",
        flush=True,
    )

    rdf_types: dict[str, set[str]] = defaultdict(set)
    predicates: dict[str, Counter[str]] = defaultdict(Counter)
    scanned = 0
    matched = 0
    malformed = 0
    for split in ("train.tsv", "valid.tsv", "test.tsv"):
        path = args.graph_dir / split
        print(f"Scanning {path}", flush=True)
        with path.open(encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle, delimiter="\t")
            for row in reader:
                scanned += 1
                if args.progress_every and scanned % args.progress_every == 0:
                    print(
                        f"Scanned={scanned:,} matched={matched:,} "
                        f"typed_targets={len(rdf_types):,}",
                        flush=True,
                    )
                if len(row) != 3:
                    malformed += 1
                    continue
                subject, predicate, obj = row
                if subject not in targets:
                    continue
                matched += 1
                predicate_uri = normalize_uri(predicate)
                predicates[subject][short_name(predicate_uri)] += 1
                if predicate_uri == RDF_TYPE:
                    rdf_types[subject].add(normalize_uri(obj))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    category_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    evidence_counts: Counter[str] = Counter()
    unmapped_classes: Counter[str] = Counter()
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, delimiter="\t")
        writer.writeheader()
        for entity in sorted(targets):
            entity_types = rdf_types.get(entity, set())
            entity_predicates = predicates.get(entity, Counter())
            classification = classifier.classify(
                entity_types,
                set(entity_predicates),
            )
            if "unknown" in classification["yago_profile_types"].split("|"):
                raise RuntimeError(f"Silent unknown category created for {entity}")
            category_counts.update(classification["yago_profile_types"].split("|"))
            status_counts[classification["yago_type_status"]] += 1
            evidence_counts[classification["yago_type_evidence"]] += 1
            if classification["yago_type_evidence"] == "typed_unmapped":
                unmapped_classes.update(entity_types)
            writer.writerow(
                {
                    "yago_entity": entity,
                    **classification,
                    "yago_rdf_type_count": len(entity_types),
                    "yago_rdf_types": "|".join(sorted(entity_types)),
                    "yago_predicate_count": sum(entity_predicates.values()),
                    "yago_top_predicates": ",".join(
                        name for name, _ in entity_predicates.most_common(20)
                    ),
                }
            )
    temporary.replace(args.output)

    audit = {
        "inputs": [str(path) for path in args.entities],
        "graph_dir": str(args.graph_dir),
        "taxonomy": str(args.taxonomy),
        "taxonomy_sha256": file_sha256(args.taxonomy),
        "target_entities": len(targets),
        "graph_rows_scanned": scanned,
        "matched_outgoing_triples": matched,
        "malformed_graph_rows": malformed,
        "entities_with_rdf_type": len(rdf_types),
        "entities_with_outgoing_predicates": len(predicates),
        "category_counts_multilabel": dict(sorted(category_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "top_unmapped_rdf_classes": unmapped_classes.most_common(100),
        "literal_unknown_count": 0,
    }
    with args.audit_output.open("w", encoding="utf-8") as handle:
        json.dump(audit, handle, indent=2, ensure_ascii=False)
    print(f"Wrote profiles: {args.output}", flush=True)
    print(f"Wrote audit: {args.audit_output}", flush=True)
    print(f"Status counts: {dict(status_counts)}", flush=True)


if __name__ == "__main__":
    main()
