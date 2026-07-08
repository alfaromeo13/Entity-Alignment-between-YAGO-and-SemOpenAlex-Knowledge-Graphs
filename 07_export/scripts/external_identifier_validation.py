"""Build a partial external-identifier validation set from raw SemOpenAlex RDF."""

from __future__ import annotations

import csv
import gzip
import pickle
import re
from collections import Counter

from additional_statistics import FINAL, OUT, ROOT

CACHE_DIR = OUT / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE = CACHE_DIR / "external_identifier_validation.pkl"

RAW_FILES = {
    "concept": ROOT / "01_raw/semopenalex/concepts/concepts-semopenalex-2025-02-10.trig.gz",
    "institution": ROOT / "01_raw/semopenalex/institutions/institutions-semopenalex-2025-02-10.trig.gz",
    "funder": ROOT / "01_raw/semopenalex/funders/funders-semopenalex-2025-02-10.trig.gz",
    "publisher": ROOT / "01_raw/semopenalex/publishers/publishers-semopenalex-2025-02-10.trig.gz",
    "source": ROOT / "01_raw/semopenalex/sources/sources-semopenalex-2025-02-10.trig.gz",
}

WIKIDATA = re.compile(r"https?://www\.wikidata\.org/(?:entity|wiki)/(Q\d+)")
YAGO_QID = re.compile(r"(Q\d+)")


def semopenalex_wikidata_map(entity_type, path):
    subject = None
    result = {}
    subject_pattern = re.compile(
        rf"^    <https://semopenalex\.org/{re.escape(entity_type)}/([^>]+)> a "
    )
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = subject_pattern.match(line)
            if match:
                subject = match.group(1)
                continue
            match = WIKIDATA.search(line)
            if match and subject:
                result[subject] = match.group(1)
    return result


def build_identifier_validation(refresh=False):
    if CACHE.exists() and not refresh:
        with CACHE.open("rb") as handle:
            return pickle.load(handle)

    mappings = {
        entity_type: semopenalex_wikidata_map(entity_type, path)
        for entity_type, path in RAW_FILES.items()
    }
    counts = Counter()
    preferred_examples = {}
    preferred_labels = {
        "nature and conservation",
        "scientific reports",
    }
    with FINAL.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            entity_type = row.get("semopenalex_uri_type") or "unknown"
            if entity_type not in mappings:
                continue
            source = (
                "Strict proxy"
                if row.get("source") == "strict_proxy_gold"
                else "Ranked ambiguous"
            )
            counts[(entity_type, source, "total")] += 1
            semopenalex_match = re.search(
                rf"/{re.escape(entity_type)}/([^>]+)>?$",
                row["semopenalex_entity"],
            )
            yago_qids = YAGO_QID.findall(row["yago_entity"])
            if (
                not semopenalex_match
                or not yago_qids
                or semopenalex_match.group(1) not in mappings[entity_type]
            ):
                continue
            counts[(entity_type, source, "checkable")] += 1
            expected = mappings[entity_type][semopenalex_match.group(1)]
            agrees = expected in yago_qids
            if agrees:
                counts[(entity_type, source, "agree")] += 1
            label = (row.get("semopenalex_label") or "").strip().lower()
            if label in preferred_labels:
                preferred_examples[label] = {
                    "yago_entity": row["yago_entity"],
                    "semopenalex_entity": row["semopenalex_entity"],
                    "yago_label": row.get("yago_label") or "",
                    "semopenalex_label": row.get("semopenalex_label") or "",
                    "semopenalex_type": entity_type,
                    "source": source,
                    "embedding_cosine": float(row.get("embedding_cosine") or 0),
                    "profile_tfidf_score": float(row.get("profile_tfidf_score") or 0),
                    "neighbor_tfidf_score": float(row.get("neighbor_tfidf_score") or 0),
                    "abc_score": float(row.get("abc_score") or 0),
                    "yago_qid": yago_qids[-1],
                    "semopenalex_qid": expected,
                    "agrees": agrees,
                }

    rows = []
    for entity_type in RAW_FILES:
        for source in ("Strict proxy", "Ranked ambiguous"):
            total = counts[(entity_type, source, "total")]
            checkable = counts[(entity_type, source, "checkable")]
            agree = counts[(entity_type, source, "agree")]
            rows.append(
                {
                    "Type": entity_type,
                    "Source": source,
                    "Final alignments": total,
                    "Externally checkable": checkable,
                    "QID agreement": agree,
                    "Checkable share": checkable / total if total else 0,
                    "Agreement rate": agree / checkable if checkable else None,
                }
            )
    data = {
        "rows": rows,
        "mapping_counts": {
            entity_type: len(mapping)
            for entity_type, mapping in mappings.items()
        },
        "preferred_examples": preferred_examples,
    }
    with CACHE.open("wb") as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return data
