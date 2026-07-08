"""Additional supported statistics requested after the core thesis figure set."""

from __future__ import annotations

import csv
import json
import pickle
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from thesis_statistics import OUT, ROOT, pair_digest

CACHE_DIR = OUT / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE = CACHE_DIR / "additional_statistics.pkl"
FINAL = ROOT / "06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv"
PROXY = ROOT / "05_entity_alignment/data/gold/proxy_gold_exact_unique.tsv"


def uri_type(uri):
    match = re.search(
        r"/(author|work|institution|source|publisher|funder|concept|keyword|topic|field|subfield|domain|venue)/",
        uri,
    )
    return match.group(1) if match else "unknown"


def short_uri(uri):
    return uri.strip("<>").rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def type_profile(path):
    counts = Counter()
    total = 0
    with Path(path).open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 3:
                continue
            if fields[1] == "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>":
                counts[short_uri(fields[2])] += 1
                total += 1
    return {"total": total, "classes": dict(counts)}


def relation_sets(path):
    uris = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            uri, _ = line.rstrip("\n").split("\t")
            uris.append(uri.strip("<>"))
    return uris


class UnionFind:
    def __init__(self):
        self.parent = {}
        self.size = {}

    def add(self, value):
        if value not in self.parent:
            self.parent[value] = value
            self.size[value] = 1

    def find(self, value):
        parent = self.parent[value]
        while parent != self.parent[parent]:
            self.parent[parent] = self.parent[self.parent[parent]]
            parent = self.parent[parent]
        while value != parent:
            next_value = self.parent[value]
            self.parent[value] = parent
            value = next_value
        return parent

    def union(self, left, right):
        self.add(left)
        self.add(right)
        root_left, root_right = self.find(left), self.find(right)
        if root_left == root_right:
            return
        if self.size[root_left] < self.size[root_right]:
            root_left, root_right = root_right, root_left
        self.parent[root_right] = root_left
        self.size[root_left] += self.size[root_right]

    def components(self):
        result = Counter()
        for value in self.parent:
            result[self.find(value)] += 1
        return sorted(result.values(), reverse=True)


def sample_graph_stats(path, relation_dict):
    relation_names = {}
    with Path(relation_dict).open(encoding="utf-8") as handle:
        for line in handle:
            uri, identifier = line.rstrip("\n").split("\t")
            relation_names[int(identifier)] = short_uri(uri)
    degree = Counter()
    node_relations = defaultdict(set)
    uf = UnionFind()
    edges = 0
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 3:
                continue
            source, relation, target = map(int, fields)
            degree[source] += 1
            degree[target] += 1
            # Co-occurrence is defined over all predicates incident to an entity,
            # not only predicates for which it happens to be the subject.
            node_relations[source].add(relation)
            node_relations[target].add(relation)
            uf.union(source, target)
            edges += 1
    values = np.array(list(degree.values()), dtype=int)
    nodes = len(values)
    relation_nodes = Counter()
    cooccurrence = Counter()
    for relations in node_relations.values():
        ordered = sorted(relations)
        for relation in ordered:
            relation_nodes[relation] += 1
        for index, left in enumerate(ordered):
            for right in ordered[index + 1 :]:
                cooccurrence[(left, right)] += 1
    return {
        "nodes": nodes,
        "edges": edges,
        "average_degree": float(values.mean()),
        "median_degree": float(np.median(values)),
        "max_degree": int(values.max()),
        "density": float(2 * edges / (nodes * (nodes - 1))) if nodes > 1 else 0,
        "components": uf.components(),
        "degree_histogram": dict(Counter(map(int, values))),
        "relation_names": relation_names,
        "relation_nodes": dict(relation_nodes),
        "cooccurrence": [
            {"left": left, "right": right, "count": count}
            for (left, right), count in cooccurrence.items()
        ],
    }


def scan_final_and_proxy():
    rng = random.Random(20260629)
    final_hashes = set()
    matrix = Counter()
    lengths = {"YAGO": Counter(), "SemOpenAlex": Counter()}
    length_deltas = Counter()
    neighbor_pairs = []
    neighbor_seen = 0
    score_histograms = defaultdict(Counter)
    source_counts = Counter()
    with FINAL.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            final_hashes.add(pair_digest(row["yago_entity"], row["semopenalex_entity"]))
            yago_type = row.get("yago_profile_type") or "unknown"
            source_group = "Strict proxy" if row.get("source") == "strict_proxy_gold" else "Ranked ambiguous"
            source_counts[source_group] += 1
            abc_score = float(row.get("abc_score") or 0)
            score_bin = min(100, max(0, int(abc_score * 100)))
            score_histograms[source_group][score_bin] += 1
            # Strict proxy rows were deliberately assigned the source marker
            # "proxy_gold", not a YAGO profile type. Exclude them from the
            # semantic type matrix instead of presenting a source as a type.
            if yago_type != "proxy_gold":
                matrix[(yago_type, row.get("semopenalex_uri_type") or "unknown")] += 1
            yago_length = min(len(row.get("yago_label") or ""), 100)
            soa_length = min(len(row.get("semopenalex_label") or ""), 100)
            lengths["YAGO"][yago_length] += 1
            lengths["SemOpenAlex"][soa_length] += 1
            length_deltas[min(abs(yago_length - soa_length), 50)] += 1
            if row.get("source") != "strict_proxy_gold":
                neighbor_seen += 1
                values = (
                    float(row.get("neighbor_tfidf_score") or 0),
                    float(row.get("embedding_cosine") or 0),
                    float(row.get("profile_tfidf_score") or 0),
                    float(row.get("abc_score") or 0),
                )
                if len(neighbor_pairs) < 100_000:
                    neighbor_pairs.append(values)
                else:
                    index = rng.randrange(neighbor_seen)
                    if index < len(neighbor_pairs):
                        neighbor_pairs[index] = values
    proxy_total = Counter()
    proxy_hits = Counter()
    with PROXY.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            entity_type = uri_type(row["semopenalex_entity"])
            proxy_total[entity_type] += 1
            if pair_digest(row["yago_entity"], row["semopenalex_entity"]) in final_hashes:
                proxy_hits[entity_type] += 1
    return {
        "matrix": [
            {"yago_type": left, "soa_type": right, "count": count}
            for (left, right), count in matrix.items()
        ],
        "label_lengths": {
            dataset: [{"length": length, "count": count} for length, count in counts.items()]
            for dataset, counts in lengths.items()
        },
        "label_length_deltas": [
            {"difference": difference, "count": count}
            for difference, count in length_deltas.items()
        ],
        "proxy_total": dict(proxy_total),
        "proxy_hits": dict(proxy_hits),
        "neighbor_pairs": neighbor_pairs,
        "source_counts": dict(source_counts),
        "score_histograms": {
            group: [
                {"score_bin": index / 100, "count": count}
                for index, count in sorted(histogram.items())
            ]
            for group, histogram in score_histograms.items()
        },
    }


def top_ambiguous_labels():
    labels = {}
    path = ROOT / "05_entity_alignment/data/candidates/exact_label_candidate_stats.tsv"
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            label = row["norm_label"]
            frequency = int(row["semopenalex_freq"])
            if frequency > labels.get(label, 0):
                labels[label] = frequency
    return [
        {"label": label, "frequency": frequency}
        for label, frequency in sorted(labels.items(), key=lambda item: item[1], reverse=True)[:50]
    ]


def build_additional(refresh=False):
    if CACHE.exists() and not refresh:
        with CACHE.open("rb") as handle:
            return pickle.load(handle)
    yago_relations = relation_sets(ROOT / "03_integer_encoding/yago/relations.dict")
    soa_relations = relation_sets(ROOT / "03_integer_encoding/semopenalex/relations.dict")
    data = {
        "type_profiles": {
            "YAGO": type_profile(ROOT / "02_preprocessed/yago/test.tsv"),
            "SemOpenAlex": type_profile(ROOT / "02_preprocessed/semopenalex_clean/test.tsv"),
        },
        "predicate_overlap": {
            "shared": sorted(set(yago_relations) & set(soa_relations)),
            "yago_only": sorted(set(yago_relations) - set(soa_relations)),
            "soa_only": sorted(set(soa_relations) - set(yago_relations)),
        },
        "graph_samples": {
            "YAGO held-out": sample_graph_stats(
                ROOT / "03_integer_encoding/yago/test.tsv",
                ROOT / "03_integer_encoding/yago/relations.dict",
            ),
            "SemOpenAlex 100k sample": sample_graph_stats(
                ROOT / "03_integer_encoding/semopenalex/test_sample_100k.tsv",
                ROOT / "03_integer_encoding/semopenalex/relations.dict",
            ),
        },
        "final": scan_final_and_proxy(),
        "top_ambiguous_labels": top_ambiguous_labels(),
    }
    with CACHE.open("wb") as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return data
