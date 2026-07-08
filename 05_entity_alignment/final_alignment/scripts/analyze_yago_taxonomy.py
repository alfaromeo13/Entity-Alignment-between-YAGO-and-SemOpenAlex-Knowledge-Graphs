#!/usr/bin/env python3
"""Summarize the YAGO taxonomy roots used by the Stage 05 type-v2 classifier."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from type_system import CATEGORY_ROOTS, TaxonomyClassifier, file_sha256


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--taxonomy", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    classifier = TaxonomyClassifier(args.taxonomy)
    classes = set(classifier.parents)
    for parents in classifier.parents.values():
        classes.update(parents)

    category_counts: Counter[str] = Counter()
    combination_counts: Counter[str] = Counter()
    unmapped = 0
    for class_uri in classes:
        categories = classifier.categories_for_classes({class_uri})
        if categories:
            category_counts.update(categories)
            combination_counts["|".join(sorted(categories))] += 1
        else:
            unmapped += 1

    direct_parent_counts = Counter(
        parent
        for parents in classifier.parents.values()
        for parent in parents
    )
    report = {
        "taxonomy": str(args.taxonomy),
        "taxonomy_sha256": file_sha256(args.taxonomy),
        "distinct_classes": len(classes),
        "classes_with_declared_parent": len(classifier.parents),
        "subclass_edges": sum(
            len(parents) for parents in classifier.parents.values()
        ),
        "supported_roots": dict(CATEGORY_ROOTS),
        "root_reachable_class_counts_multilabel": dict(
            sorted(category_counts.items())
        ),
        "root_combination_counts": dict(
            combination_counts.most_common()
        ),
        "classes_not_reaching_supported_root": unmapped,
        "classes_with_multiple_direct_parents": sum(
            len(parents) > 1 for parents in classifier.parents.values()
        ),
        "maximum_direct_parent_count": max(
            (len(parents) for parents in classifier.parents.values()),
            default=0,
        ),
        "most_common_direct_parents": direct_parent_counts.most_common(30),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2), flush=True)
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
