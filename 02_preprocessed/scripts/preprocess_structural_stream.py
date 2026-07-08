#!/usr/bin/env python3

"""
Stream-based RDF preprocessing script.

This script reads normalized RDF statements from standard input. RDF parsing
is performed beforehand by Apache Jena riot, which converts the original
Turtle (YAGO) and TriG (SemOpenAlex) files into N-Triples or N-Quads.

The script transforms RDF data into two outputs:

1. Structural triples:
   subject<TAB>predicate<TAB>object

   Entity-to-entity graph edges used later for graph embedding training.

2. Textual data:
   entity<TAB>predicate<TAB>text

   Selected textual attributes such as labels, names, titles,
   descriptions, comments, and alternative names used later for
   candidate generation and entity alignment.

Additional responsibilities include:
- filtering schema and helper resources,
- removing dataset-specific non-entity records,
- generating deterministic train/validation/test splits,
- collecting preprocessing statistics.

This is the core preprocessing component used by both the YAGO and
SemOpenAlex pipelines.
"""

import os
import re
import sys
import csv
import json
import argparse

NT_NQ_RE = re.compile(r'^\s*(<[^>]*>)\s+(<[^>]*>)\s+(.+?)(?:\s+<[^>]*>)?\s*\.\s*$')
LITERAL_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"(?:@[A-Za-z0-9\-]+|\^\^<[^>]*>)?$')

# Dataset-specific helper predicates that do not represent meaningful graph structure for embedding training.
SEMOPENALEX_EXCLUDED_PREDICATES = {
    "<https://semopenalex.org/ontology/countsByYear>",
    "<http://purl.org/dc/terms/created>",
    "<http://purl.org/dc/terms/modified>",
}

# Predicates whose literal values are retained for later entity alignment and candidate generation.
TEXT_PREDICATES = {
    "<http://www.w3.org/2000/01/rdf-schema#label>",
    "<http://www.w3.org/2004/02/skos/core#prefLabel>",
    "<http://www.w3.org/2004/02/skos/core#altLabel>",
    "<http://schema.org/name>",
    "<http://schema.org/description>",
    "<http://www.w3.org/2000/01/rdf-schema#comment>",
    "<http://purl.org/dc/terms/title>",
    "<http://purl.org/dc/terms/description>",
    "<http://xmlns.com/foaf/0.1/name>",
    "<http://xmlns.com/foaf/0.1/givenName>",
    "<http://xmlns.com/foaf/0.1/familyName>",
    "<https://semopenalex.org/ontology/alternativeName>",
}

# SemOpenAlex entity URIs that are considered real entities and are allowed to appear as graph nodes.
SEMOPENALEX_ENTITY_PREFIXES = (
    "<https://semopenalex.org/author/",
    "<https://semopenalex.org/work/",
    "<https://semopenalex.org/institution/",
    "<https://semopenalex.org/source/",
    "<https://semopenalex.org/publisher/",
    "<https://semopenalex.org/funder/",
    "<https://semopenalex.org/concept/",
    "<https://semopenalex.org/topic/",
    "<https://semopenalex.org/domain/",
    "<https://semopenalex.org/field/",
    "<https://semopenalex.org/subfield/",
    "<https://semopenalex.org/keyword/",
    "<https://semopenalex.org/venue/",
)

GENERIC_BAD_SUBJECT_PREFIXES = (
    "<http://www.w3.org/2002/07/owl#",
    "<http://www.w3.org/2000/01/rdf-schema#",
    "<http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "<http://www.w3.org/2001/XMLSchema#",
    "<http://purl.org/dc/terms/",
    "<http://xmlns.com/foaf/0.1/",
    "<http://schema.org/",
    "<https://schema.org/",
)

SEMOPENALEX_BAD_SUBJECT_PREFIXES = (
    "<https://semopenalex.org/ontology/",
    "<https://semopenalex.org/countsByYear/",
    "<https://semopenalex.org/authorship/",
    "<https://semopenalex.org/abstract/",
    "<https://semopenalex.org/authorposition/",
    "<https://semopenalex.org/conceptscore/",
    "<https://semopenalex.org/hostvenue/",
)

YAGO_BAD_SUBJECT_PREFIXES = (
    "<http://yago-knowledge.org/schema#",
    "<https://yago-knowledge.org/schema#",
    "<http://www.w3.org/2002/07/owl#",
    "<http://www.w3.org/2000/01/rdf-schema#",
    "<http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "<http://www.w3.org/2001/XMLSchema#",
)

def parse_nt_line(line: str):
    m = NT_NQ_RE.match(line.rstrip("\n"))
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3)

def parse_literal(o: str):
    m = LITERAL_RE.match(o)
    if not m:
        return None
    text = m.group(1)
    text = text.replace('\\"', '"').replace("\\\\", "\\")
    text = re.sub(r"\s+", " ", text).strip()
    return text if text else None

def is_iri(x: str) -> bool:
    return x.startswith("<") and x.endswith(">")

def starts_with_any(value: str, prefixes) -> bool:
    return any(value.startswith(p) for p in prefixes)

def semopenalex_is_entity(uri: str) -> bool:
    return starts_with_any(uri, SEMOPENALEX_ENTITY_PREFIXES)

def is_allowed_subject(s: str, dataset_name: str) -> bool:
    if dataset_name == "semopenalex":
        if starts_with_any(s, GENERIC_BAD_SUBJECT_PREFIXES):
            return False
        if starts_with_any(s, SEMOPENALEX_BAD_SUBJECT_PREFIXES):
            return False
        return semopenalex_is_entity(s)
    elif dataset_name == "yago":
        return not starts_with_any(s, YAGO_BAD_SUBJECT_PREFIXES)
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--dataset-name", required=True, choices=["semopenalex", "yago"])
    ap.add_argument("--sample-mod", type=int, default=1000)
    ap.add_argument("--valid-mod", type=int, default=0)
    ap.add_argument("--test-mod", type=int, default=1)
    ap.add_argument("--progress-every", type=int, default=10_000_000)
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    train_path = os.path.join(args.output_dir, "train.tsv")
    valid_path = os.path.join(args.output_dir, "valid.tsv")
    test_path = os.path.join(args.output_dir, "test.tsv")
    text_raw_path = os.path.join(args.output_dir, "entity_text_raw.tsv")
    stats_path = os.path.join(args.output_dir, "stats.json")

    total_in = 0
    malformed = 0
    kept_structural = 0
    filtered_subject = 0
    non_structural = 0
    text_literal_rows = 0
    skipped_helper_structural = 0

    relation_counts = {}
    text_predicate_counts = {}

    with open(train_path, "w", encoding="utf-8", newline="") as f_train, \
         open(valid_path, "w", encoding="utf-8", newline="") as f_valid, \
         open(test_path, "w", encoding="utf-8", newline="") as f_test, \
         open(text_raw_path, "w", encoding="utf-8", newline="") as f_text:

        train_writer = csv.writer(f_train, delimiter="\t")
        valid_writer = csv.writer(f_valid, delimiter="\t")
        test_writer = csv.writer(f_test, delimiter="\t")
        text_writer = csv.writer(f_text, delimiter="\t")

        text_writer.writerow(["entity", "predicate", "text"])

        for line in sys.stdin:
            total_in += 1
            parsed = parse_nt_line(line)
            if parsed is None:
                malformed += 1
                continue

            s, p, o = parsed

            if not is_iri(s):
                non_structural += 1
                continue

            if not is_allowed_subject(s, args.dataset_name):
                filtered_subject += 1
                continue

            # Structural triple
            if is_iri(o):
                if args.dataset_name == "semopenalex" and p in SEMOPENALEX_EXCLUDED_PREDICATES:
                    skipped_helper_structural += 1
                    continue

                kept_structural += 1
                relation_counts[p] = relation_counts.get(p, 0) + 1

                bucket = kept_structural % args.sample_mod
                if bucket == args.valid_mod:
                    valid_writer.writerow([s, p, o])
                elif bucket == args.test_mod:
                    test_writer.writerow([s, p, o])
                else:
                    train_writer.writerow([s, p, o])

            # Literal triple
            else:
                non_structural += 1
                lit = parse_literal(o)
                if lit is not None and p in TEXT_PREDICATES:
                    text_writer.writerow([s, p, lit])
                    text_literal_rows += 1
                    text_predicate_counts[p] = text_predicate_counts.get(p, 0) + 1

            if total_in % 10_000_000 == 0:
                print(
                    f"Read {total_in:,}, kept_structural {kept_structural:,}, "
                    f"text_rows {text_literal_rows:,}, "
                    f"filtered_subject {filtered_subject:,}, "
                    f"skipped_helper_structural {skipped_helper_structural:,}, "
                    f"non_structural {non_structural:,}, "
                    f"malformed {malformed:,}",
                    file=sys.stderr,
                    flush=True
                )

    top_rel = sorted(relation_counts.items(), key=lambda x: x[1], reverse=True)[:25]
    top_text_preds = sorted(text_predicate_counts.items(), key=lambda x: x[1], reverse=True)[:25]

    stats = {
        "dataset": args.dataset_name,
        "total_lines_read": total_in,
        "structural_triples_kept": kept_structural,
        "text_literal_rows_written": text_literal_rows,
        "filtered_subject_triples": filtered_subject,
        "skipped_helper_structural_triples": skipped_helper_structural,
        "non_structural_triples_seen": non_structural,
        "malformed_lines": malformed,
        "unique_relations": len(relation_counts),
        "unique_text_predicates": len(text_predicate_counts),
        "top_25_relations": top_rel,
        "top_25_text_predicates": top_text_preds,
        "split": {
            "sample_mod": args.sample_mod,
            "valid_mod": args.valid_mod,
            "test_mod": args.test_mod,
        },
    }

    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(json.dumps(stats, indent=2), file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()