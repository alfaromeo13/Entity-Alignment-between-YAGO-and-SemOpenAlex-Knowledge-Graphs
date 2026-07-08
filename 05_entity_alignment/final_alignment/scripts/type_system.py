#!/usr/bin/env python3
"""Shared taxonomy-aware YAGO type logic for the isolated Stage 05 correction."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

CATEGORY_ROOTS = (
    ("person_like", "http://schema.org/Person"),
    ("creative_work_like", "http://schema.org/CreativeWork"),
    ("organization_like", "http://schema.org/Organization"),
    ("place_like", "http://schema.org/Place"),
    ("event_like", "http://schema.org/Event"),
    ("product_like", "http://schema.org/Product"),
    ("intangible_like", "http://schema.org/Intangible"),
    ("organism_like", "http://schema.org/Taxon"),
)
CATEGORY_ORDER = {name: index for index, (name, _) in enumerate(CATEGORY_ROOTS)}

PREDICATE_HINTS = {
    "person_like": {
        "birthdate",
        "deathdate",
        "birthplace",
        "deathplace",
        "gender",
        "givenname",
        "familyname",
        "spouse",
        "alumni",
        "award",
        "nationality",
        "children",
        "doctoraladvisor",
    },
    "creative_work_like": {
        "author",
        "creator",
        "datepublished",
        "inlanguage",
        "isbn",
        "issn",
        "musicby",
        "director",
        "producer",
        "publisher",
        "genre",
        "about",
        "actor",
        "lyricist",
        "performer",
        "notablework",
    },
    "organization_like": {
        "founder",
        "foundingdate",
        "parentorganization",
        "suborganization",
        "member",
        "affiliation",
        "worksfor",
        "employee",
        "subsidiary",
        "ownedby",
        "parentbody",
        "sponsor",
    },
    "place_like": {
        "geo",
        "latitude",
        "longitude",
        "location",
        "address",
        "containedinplace",
        "country",
        "capital",
        "neighbors",
    },
    "event_like": {
        "startdate",
        "enddate",
        "organizer",
        "participant",
        "superevent",
    },
    "product_like": {"manufacturer", "material", "model"},
    "intangible_like": {
        "beliefsystem",
        "knowslanguage",
        "academicdegree",
        "conferredby",
    },
    "organism_like": {"parenttaxon", "taxonrank"},
}

SOA_TYPES = (
    "author",
    "work",
    "institution",
    "source",
    "publisher",
    "funder",
    "concept",
    "keyword",
    "topic",
    "field",
    "subfield",
    "domain",
    "venue",
)

ALLOWED_CATEGORIES = {
    "author": {"person_like"},
    "work": {"creative_work_like"},
    "institution": {"organization_like", "place_like"},
    "source": {"creative_work_like", "organization_like"},
    "venue": {"creative_work_like", "organization_like", "place_like"},
    "publisher": {"organization_like"},
    "funder": {"organization_like"},
    "concept": {"intangible_like", "organism_like", "creative_work_like"},
    "keyword": {"intangible_like", "organism_like", "creative_work_like"},
    "topic": {"intangible_like", "organism_like", "creative_work_like"},
    "field": {"intangible_like", "creative_work_like"},
    "subfield": {"intangible_like", "creative_work_like"},
    "domain": {"intangible_like", "creative_work_like"},
}

PREFIX_RE = re.compile(r"^@prefix\s+([^:]*):\s+<([^>]+)>\s*\.\s*$")


def normalize_uri(value: str) -> str:
    text = str(value).strip()
    if text.startswith("<") and text.endswith(">"):
        return text[1:-1]
    return text


def short_name(value: str) -> str:
    text = normalize_uri(value)
    return text.rsplit("#", 1)[-1].rsplit("/", 1)[-1].lower()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expand_term(token: str, prefixes: dict[str, str]) -> str | None:
    value = token.strip().rstrip(";,")
    if value.startswith("<") and value.endswith(">"):
        return value[1:-1]
    if ":" not in value or value.startswith(('"', "'")):
        return None
    prefix, local = value.split(":", 1)
    namespace = prefixes.get(prefix)
    return namespace + local if namespace is not None else None


class TaxonomyClassifier:
    """Resolve YAGO classes to one or more stable schema-root categories."""

    def __init__(self, taxonomy_path: Path):
        self.taxonomy_path = taxonomy_path
        self.parents: dict[str, set[str]] = defaultdict(set)
        prefixes: dict[str, str] = {}
        with taxonomy_path.open(encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                prefix_match = PREFIX_RE.match(line)
                if prefix_match:
                    prefixes[prefix_match.group(1)] = prefix_match.group(2)
                    continue
                fields = line.split()
                if len(fields) < 4 or fields[1] != "rdfs:subClassOf":
                    continue
                child = expand_term(fields[0], prefixes)
                parent = expand_term(fields[2], prefixes)
                if child and parent:
                    self.parents[child].add(parent)
        self.root_by_category = dict(CATEGORY_ROOTS)

    @lru_cache(maxsize=None)
    def ancestors(self, class_uri: str) -> frozenset[str]:
        result = {class_uri}
        pending = [class_uri]
        while pending:
            current = pending.pop()
            for parent in self.parents.get(current, ()):
                if parent not in result:
                    result.add(parent)
                    pending.append(parent)
        return frozenset(result)

    def categories_for_classes(self, class_uris: set[str]) -> set[str]:
        categories: set[str] = set()
        for class_uri in class_uris:
            ancestors = self.ancestors(class_uri)
            for category, root in CATEGORY_ROOTS:
                if root in ancestors:
                    categories.add(category)
        return categories

    def classify(
        self,
        class_uris: set[str],
        predicates: set[str],
    ) -> dict[str, str]:
        categories = self.categories_for_classes(class_uris)
        if categories:
            evidence = "taxonomy"
            status = "resolved"
        else:
            categories = {
                category
                for category, hints in PREDICATE_HINTS.items()
                if predicates & hints
            }
            if categories:
                evidence = "predicate_fallback"
                status = "resolved"
            elif class_uris:
                categories = {"other_typed"}
                evidence = "typed_unmapped"
                status = "other_typed"
            else:
                categories = {"untyped"}
                evidence = "no_rdf_type"
                status = "untyped"

        ordered = sorted(
            categories,
            key=lambda value: (CATEGORY_ORDER.get(value, 10_000), value),
        )
        confidence = {
            "taxonomy": "1.0",
            "predicate_fallback": "0.5",
            "typed_unmapped": "0.0",
            "no_rdf_type": "0.0",
        }[evidence]
        return {
            "yago_profile_type": ordered[0],
            "yago_profile_types": "|".join(ordered),
            "yago_type_status": status,
            "yago_type_evidence": evidence,
            "yago_type_confidence": confidence,
        }


def semopenalex_type(uri: str) -> str:
    value = normalize_uri(uri)
    for entity_type in SOA_TYPES:
        if f"/{entity_type}/" in value:
            return entity_type
    return "unrecognized_uri_type"


def compatibility_state(profile_types: str, type_status: str, soa_type: str) -> str:
    categories = {value for value in str(profile_types).split("|") if value}
    if type_status in {"other_typed", "untyped"}:
        return "unresolved"
    allowed = ALLOWED_CATEGORIES.get(soa_type)
    if allowed is None:
        return "unresolved"
    return "compatible" if categories & allowed else "incompatible"
