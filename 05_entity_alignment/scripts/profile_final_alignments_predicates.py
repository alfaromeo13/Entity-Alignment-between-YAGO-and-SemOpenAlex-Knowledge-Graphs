#!/usr/bin/env python3
import argparse
import csv
import os
import re
from collections import defaultdict, Counter

YAGO_PREFIX = "http://yago-knowledge.org/resource/"

SEMOPENALEX_TYPES = [
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
]

def clean_uri(uri):
    uri = uri.strip()
    if uri.startswith("<") and uri.endswith(">"):
        uri = uri[1:-1]
    return uri

def yago_full_to_pref(uri):
    uri = clean_uri(uri)
    if uri.startswith(YAGO_PREFIX):
        return "yago:" + uri[len(YAGO_PREFIX):]
    return uri

def semopenalex_type(uri):
    uri = clean_uri(uri)

    parts = uri.split("/")
    if "semopenalex.org" in parts:
        idx = parts.index("semopenalex.org")
        if idx + 1 < len(parts) and parts[idx + 1]:
            return parts[idx + 1]

    for t in SEMOPENALEX_TYPES:
        if f"/{t}/" in uri:
            return t

    return "unknown"

def parse_ttl_subject_predicate(line):
    line = line.strip()
    if not line or line.startswith("@prefix") or line.startswith("#"):
        return None, None

    parts = line.split()
    if len(parts) < 2:
        return None, None

    subj = parts[0]
    pred = parts[1]

    if not subj.startswith("yago:"):
        return None, None

    return subj, pred

def classify_yago_from_predicates(preds):
    p = set(preds)

    if any(x in p for x in [
        "schema:birthDate",
        "schema:deathDate",
        "schema:gender",
        "schema:birthPlace",
        "schema:deathPlace",
    ]):
        return "person_like"

    if any(x in p for x in [
        "schema:author",
        "schema:datePublished",
        "schema:publisher",
        "schema:isbn",
        "schema:issn",
        "schema:inLanguage",
        "schema:about",
    ]):
        return "creative_work_like"

    if any(x in p for x in [
        "schema:founder",
        "schema:foundingDate",
        "schema:member",
        "schema:parentOrganization",
        "schema:subOrganization",
        "schema:worksFor",
        "schema:affiliation",
    ]):
        return "organization_like"

    if any(x in p for x in [
        "schema:geo",
        "schema:latitude",
        "schema:longitude",
        "schema:containedInPlace",
        "schema:location",
        "schema:address",
    ]):
        return "place_like"

    if any(x in p for x in [
        "schema:startDate",
        "schema:endDate",
        "schema:organizer",
    ]):
        return "event_like"

    return "unknown"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alignments", required=True)
    ap.add_argument("--yago-files", nargs="+", required=True)
    ap.add_argument("--out-enriched", required=True)
    ap.add_argument("--out-predicate-summary", required=True)
    ap.add_argument("--out-type-pair-summary", required=True)
    ap.add_argument("--progress-every", type=int, default=20_000_000)
    args = ap.parse_args()

    needed_yago_pref = set()
    final_rows = []

    with open(args.alignments, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        base_fields = list(r.fieldnames)

        for row in r:
            yp = yago_full_to_pref(row["yago_entity"])
            needed_yago_pref.add(yp)
            final_rows.append(row)

    print(f"Loaded final alignments: {len(final_rows):,}", flush=True)
    print(f"Unique needed YAGO entities: {len(needed_yago_pref):,}", flush=True)

    yago_predicates = defaultdict(Counter)

    for path in args.yago_files:
        print(f"Scanning {path}", flush=True)
        scanned = 0
        hits = 0

        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                scanned += 1
                subj, pred = parse_ttl_subject_predicate(line)

                if subj in needed_yago_pref:
                    yago_predicates[subj][pred] += 1
                    hits += 1

                if scanned % args.progress_every == 0:
                    print(
                        f"{path}: scanned={scanned:,} hits={hits:,} entities_with_predicates={len(yago_predicates):,}",
                        flush=True,
                    )

        print(
            f"Finished {path}: scanned={scanned:,} hits={hits:,} entities_with_predicates={len(yago_predicates):,}",
            flush=True,
        )

    predicate_summary = Counter()
    type_pair_summary = Counter()

    extra_fields = [
        "semopenalex_uri_type",
        "yago_profile_type",
        "yago_predicate_count",
        "yago_top_predicates",
    ]

    fields = base_fields[:]
    for field in extra_fields:
        if field not in fields:
            fields.append(field)

    with open(args.out_enriched, "w", encoding="utf-8", newline="") as out:
        w = csv.DictWriter(out, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        w.writeheader()

        for row in final_rows:
            yp = yago_full_to_pref(row["yago_entity"])
            preds_counter = yago_predicates.get(yp, Counter())
            preds = list(preds_counter.keys())

            ytype = classify_yago_from_predicates(preds)
            stype = semopenalex_type(row["semopenalex_entity"])

            for pred, c in preds_counter.items():
                predicate_summary[(pred, stype)] += c

            type_pair_summary[(ytype, stype)] += 1

            top_preds = "|".join(
                [f"{p}:{c}" for p, c in preds_counter.most_common(20)]
            )

            row["semopenalex_uri_type"] = stype
            row["semopenalex_type"] = stype
            row["yago_profile_type"] = ytype
            row["yago_predicate_count"] = str(sum(preds_counter.values()))
            row["yago_top_predicates"] = top_preds

            w.writerow(row)

    with open(args.out_predicate_summary, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out, delimiter="\t")
        w.writerow(["yago_predicate", "semopenalex_type", "count"])
        for (pred, stype), c in predicate_summary.most_common():
            w.writerow([pred, stype, c])

    with open(args.out_type_pair_summary, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out, delimiter="\t")
        w.writerow(["yago_profile_type", "semopenalex_type", "count"])
        for (yt, st), c in type_pair_summary.most_common():
            w.writerow([yt, st, c])

    print(f"Wrote enriched alignments: {args.out_enriched}", flush=True)
    print(f"Wrote predicate summary: {args.out_predicate_summary}", flush=True)
    print(f"Wrote type pair summary: {args.out_type_pair_summary}", flush=True)

if __name__ == "__main__":
    main()