#!/usr/bin/env python3
import argparse
import csv
import re
import unicodedata
from collections import defaultdict


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    text = text.encode("ascii", "ignore").decode("utf-8")
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def weight_for_predicate(predicate: str) -> int:
    p = predicate.lower()

    if "preflabel" in p or "label" in p or "name" in p or "title" in p:
        return 4

    if "altlabel" in p or "alternativename" in p:
        return 2

    if "description" in p or "comment" in p:
        return 1

    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-parts-per-entity", type=int, default=30)
    args = ap.parse_args()

    profiles = defaultdict(list)

    print(f"Reading: {args.input}", flush=True)

    with open(args.input, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            entity = row.get("entity")
            predicate = row.get("predicate", "")
            text = row.get("text", "")

            if not entity or not text:
                continue

            weight = weight_for_predicate(predicate)
            if weight <= 0:
                continue

            text = normalize_text(text)
            if not text:
                continue

            profiles[entity].extend([text] * weight)

    with open(args.output, "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out, delimiter="\t")
        writer.writerow(["entity", "text_profile"])

        for entity, parts in profiles.items():
            profile = " ".join(parts[: args.max_parts_per_entity])
            writer.writerow([entity, profile])

    print(f"Entities with profiles: {len(profiles):,}", flush=True)
    print(f"Wrote: {args.output}", flush=True)


if __name__ == "__main__":
    main()