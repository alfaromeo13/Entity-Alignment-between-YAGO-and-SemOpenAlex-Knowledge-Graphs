#!/usr/bin/env python3
import argparse
import csv
import hashlib
import os
import re
from urllib.parse import urlsplit


FLOAT_LEXICAL = re.compile(
    r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$"
)
FORBIDDEN_IRI_CHARACTERS = frozenset('<>"{}|^`\\')


def normalize_iri(raw, field):
    value = str(raw).strip()
    starts = value.startswith("<")
    ends = value.endswith(">")
    if starts != ends:
        raise ValueError(f"{field} has unbalanced angle brackets: {raw!r}")
    if starts:
        value = value[1:-1]
    if (
        not value
        or not urlsplit(value).scheme
        or any(ord(char) <= 0x20 or char in FORBIDDEN_IRI_CHARACTERS for char in value)
    ):
        raise ValueError(f"{field} is not a valid absolute RDF IRI: {raw!r}")
    return value


def rdf_literal(s):
    escaped = []
    replacements = {
        "\\": "\\\\",
        '"': '\\"',
        "\t": "\\t",
        "\b": "\\b",
        "\n": "\\n",
        "\r": "\\r",
        "\f": "\\f",
    }
    for character in str(s):
        codepoint = ord(character)
        if character in replacements:
            escaped.append(replacements[character])
        elif codepoint < 0x20 or 0x7F <= codepoint <= 0x9F:
            escaped.append(f"\\u{codepoint:04X}")
        else:
            escaped.append(character)
    return "".join(escaped)


def float_literal(s):
    value = str(s).strip() or "0"
    if not FLOAT_LEXICAL.fullmatch(value):
        raise ValueError(f"Invalid finite numeric score: {s!r}")
    return value


def ensure_parent(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_prefixes(out):
    out.write("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n")
    out.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
    out.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")
    out.write("@prefix kg: <https://kgalign.example.org/schema/> .\n\n")


def alignment_iri(yago, sao):
    digest = hashlib.sha256(f"{yago}\0{sao}".encode("utf-8")).hexdigest()
    return f"https://kgalign.example.org/alignment/{digest}"


def write_alignment(out, t, indent=""):
    # Keep the directly usable identity link and describe the assertion through
    # a stable RDF reification resource. Scores are properties of the alignment,
    # not properties of the YAGO entity.
    out.write(f"{indent}<{t['yago']}> owl:sameAs <{t['sao']}> .\n\n")
    out.write(f"{indent}<{t['alignment']}> a rdf:Statement, kg:Alignment ;\n")
    out.write(f"{indent}    rdf:subject <{t['yago']}> ;\n")
    out.write(f"{indent}    rdf:predicate owl:sameAs ;\n")
    out.write(f"{indent}    rdf:object <{t['sao']}> ;\n")
    out.write(f"{indent}    kg:embeddingScore \"{t['embedding']}\"^^xsd:float ;\n")
    out.write(f"{indent}    kg:profileTfidfScore \"{t['profile_tfidf']}\"^^xsd:float ;\n")
    out.write(f"{indent}    kg:neighborTfidfScore \"{t['neighbor_tfidf']}\"^^xsd:float ;\n")
    out.write(f"{indent}    kg:abcScore \"{t['abc_score']}\"^^xsd:float ;\n")
    out.write(f"{indent}    kg:semopenalexType \"{t['soa_type']}\" ;\n")
    out.write(f"{indent}    kg:source \"{t['source']}\" ;\n")
    out.write(f"{indent}    kg:confidence \"{t['conf']}\" .\n\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out-ttl", required=True)
    ap.add_argument("--out-trig", required=True)
    ap.add_argument("--graph", required=True)
    args = ap.parse_args()

    ensure_parent(args.out_ttl)
    ensure_parent(args.out_trig)

    count = 0
    graph = normalize_iri(args.graph, "--graph")

    with open(args.input, encoding="utf-8") as f, \
         open(args.out_ttl, "w", encoding="utf-8") as ttl, \
         open(args.out_trig, "w", encoding="utf-8") as trig:

        reader = csv.DictReader(f, delimiter="\t")
        required = {"yago_entity", "semopenalex_entity"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Input is missing required columns: {sorted(missing)}")

        write_prefixes(ttl)
        write_prefixes(trig)
        trig.write(f"<{graph}> {{\n")

        for line_number, row in enumerate(reader, start=2):
            t = {
                "yago": normalize_iri(
                    row["yago_entity"], f"yago_entity at TSV line {line_number}"
                ),
                "sao": normalize_iri(
                    row["semopenalex_entity"],
                    f"semopenalex_entity at TSV line {line_number}",
                ),
                "embedding": float_literal(row.get("embedding_cosine", "0")),
                "profile_tfidf": float_literal(row.get("profile_tfidf_score", row.get("tfidf_score", "0"))),
                "neighbor_tfidf": float_literal(row.get("neighbor_tfidf_score", "0")),
                "abc_score": float_literal(row.get("abc_score", "0")),
                "source": rdf_literal(row.get("source", "unknown")),
                "conf": rdf_literal(row.get("confidence_tier", "unknown")),
                "soa_type": rdf_literal(row.get("semopenalex_uri_type", row.get("semopenalex_type", "unknown"))),
            }
            t["alignment"] = alignment_iri(t["yago"], t["sao"])

            write_alignment(ttl, t)
            write_alignment(trig, t, indent="  ")
            count += 1

        trig.write("}\n")

    print(f"Loaded alignments: {count:,}")
    print(f"Data triples per serialization: {count * 13:,}")
    print(f"Wrote TTL: {args.out_ttl}")
    print(f"Wrote TRIG: {args.out_trig}")


if __name__ == "__main__":
    main()
