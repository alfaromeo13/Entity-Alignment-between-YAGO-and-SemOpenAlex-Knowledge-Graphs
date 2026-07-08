"""Compute and cache the statistical inputs used by the thesis figures."""

from __future__ import annotations

import csv
import hashlib
import json
import pickle
import random
import re
from array import array
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
OUT = ROOT / "07_export" / "visualizations"
CACHE_DIR = OUT / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE = CACHE_DIR / "thesis_statistics.pkl"

SYSTEM_FILES = {
    "Baseline": ROOT / "05_entity_alignment/final_alignment/outputs/strict/alignments_FINAL_tfidf.tsv",
    "A+B": ROOT / "06_experiments/type_text_enrichment/outputs/strict/alignments_type_text_enriched_1to1.tsv",
    "C only": ROOT / "06_experiments/graph_neighbor_only/outputs/strict/alignments_graph_neighbor_1to1.tsv",
    "A+B+C": ROOT / "06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv",
}
ABC_T025 = ROOT / "06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t025.tsv"
AMBIGUOUS_TOP1 = ROOT / "06_experiments/type_text_enrichment/outputs/strict/top1.tsv"


def read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def read_kv(path):
    result = {}
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 2 or not fields[0]:
                continue
            try:
                number = float(fields[1])
                result[fields[0]] = int(number) if number.is_integer() else number
            except ValueError:
                result[fields[0]] = fields[1]
    return result


def pair_digest(yago, semopenalex):
    digest = hashlib.blake2b(digest_size=16)
    digest.update(yago.encode("utf-8"))
    digest.update(b"\0")
    digest.update(semopenalex.encode("utf-8"))
    return digest.digest()


def reservoir_add(samples, group, row, seen, limit, rng):
    bucket = samples[group]
    if len(bucket) < limit:
        bucket.append(row)
    else:
        index = rng.randrange(seen[group])
        if index < limit:
            bucket[index] = row


def read_relation_names(path):
    names = {}
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            uri, identifier = line.rstrip("\n").split("\t")
            bare_uri = uri.strip("<>")
            value = bare_uri.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            names[int(identifier)] = {"name": value, "uri": bare_uri}
    return names


def relation_profile(test_path, dictionary_path):
    names = read_relation_names(dictionary_path)
    counts = Counter()
    total = 0
    with Path(test_path).open(encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) == 3:
                counts[int(fields[1])] += 1
                total += 1
    ordered = counts.most_common()
    shares = np.array([count / total for _, count in ordered], dtype=float)
    cumulative = np.cumsum(shares)
    sorted_counts = np.sort(np.array(list(counts.values()), dtype=float))
    n = len(sorted_counts)
    gini = (
        (2 * np.arange(1, n + 1) - n - 1) @ sorted_counts
        / (n * sorted_counts.sum())
        if n
        else 0
    )
    return {
        "total": total,
        "gini": float(gini),
        "relations": [
            {
                "relation": names.get(identifier, {}).get("name", str(identifier)),
                "relation_uri": names.get(identifier, {}).get("uri", ""),
                "relation_id": identifier,
                "count": count,
                "share": count / total,
                "cumulative": float(cumulative[index]),
            }
            for index, (identifier, count) in enumerate(ordered)
        ],
        "lorenz_population": (np.arange(n + 1) / n).tolist(),
        "lorenz_share": np.concatenate(([0.0], np.cumsum(sorted_counts) / sorted_counts.sum())).tolist(),
    }


def scan_systems(sample_limit=12_000):
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20260629)
    raw_paths = {}
    baseline_hashes = set()
    samples = defaultdict(list)
    seen = Counter()
    full_scores = ("embedding_cosine", "profile_tfidf_score", "neighbor_tfidf_score", "abc_score")
    score_sums = defaultdict(Counter)
    score_sumsq = defaultdict(Counter)
    type_sums = defaultdict(Counter)
    type_counts = Counter()
    source_counts = Counter()
    featured = {}
    featured_fragments = {
        "David Baker": "David_Baker__u0028_biochemist",
        "Emmanuelle Charpentier": "Emmanuelle_Charpentier_Q113171063",
        "Mohammed Abu": "Mohammed_Abu>",
        "Barbara Liskov": "Barbara_Liskov>",
    }

    for system_index, (system, path) in enumerate(SYSTEM_FILES.items()):
        raw = OUT / f".{system.lower().replace(' ', '_').replace('+', 'p')}.pairs128"
        raw_paths[system] = raw
        with path.open(encoding="utf-8", newline="") as handle, raw.open("wb") as out:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                digest = pair_digest(row["yago_entity"], row["semopenalex_entity"])
                out.write(digest)
                if system == "Baseline":
                    baseline_hashes.add(digest)
                if system != "A+B+C":
                    continue

                source = "Proxy-gold" if row.get("source") == "strict_proxy_gold" else "Ranked"
                membership = "Baseline-shared" if digest in baseline_hashes else "Final-only"
                group = "Proxy-gold" if source == "Proxy-gold" else membership
                numeric = {name: float(row.get(name) or 0.0) for name in full_scores}
                sample_row = {
                    "Group": group,
                    "Type": row.get("semopenalex_uri_type") or "unknown",
                    "Candidate count": int(float(row.get("yago_candidate_count") or 0)),
                    "Label frequency": int(float(row.get("semopenalex_label_freq") or 0)),
                    **numeric,
                }
                seen[group] += 1
                reservoir_add(samples, group, sample_row, seen, sample_limit, rng)
                source_counts[group] += 1
                entity_type = sample_row["Type"]
                type_counts[entity_type] += 1
                for name, value in numeric.items():
                    score_sums[group][name] += value
                    score_sumsq[group][name] += value * value
                    type_sums[entity_type][name] += value
                entity = row["yago_entity"]
                for label, fragment in featured_fragments.items():
                    if label not in featured and fragment in entity:
                        featured[label] = dict(row)

    arrays = []
    masks = []
    for bit, system in enumerate(SYSTEM_FILES):
        keys = np.fromfile(raw_paths[system], dtype="V16")
        arrays.append(keys)
        masks.append(np.full(len(keys), 1 << bit, dtype=np.uint8))
    all_keys = np.concatenate(arrays)
    all_masks = np.concatenate(masks)
    order = np.argsort(all_keys)
    sorted_keys = all_keys[order]
    sorted_masks = all_masks[order]
    starts = np.concatenate(([0], np.flatnonzero(sorted_keys[1:] != sorted_keys[:-1]) + 1))
    intersection_masks = np.bitwise_or.reduceat(sorted_masks, starts)
    intersection_counts = Counter(int(value) for value in intersection_masks)
    del all_keys, all_masks, sorted_keys, sorted_masks, order, arrays, masks

    for path in raw_paths.values():
        path.unlink(missing_ok=True)

    group_stats = {}
    for group, count in source_counts.items():
        group_stats[group] = {}
        for score in full_scores:
            mean = score_sums[group][score] / count
            variance = max(score_sumsq[group][score] / count - mean * mean, 0)
            group_stats[group][score] = {"mean": mean, "std": variance**0.5}
    type_means = {
        entity_type: {
            score: type_sums[entity_type][score] / count
            for score in full_scores
        }
        for entity_type, count in type_counts.items()
    }
    return {
        "intersection_counts": dict(intersection_counts),
        "samples": dict(samples),
        "group_counts": dict(source_counts),
        "group_stats": group_stats,
        "type_counts": dict(type_counts),
        "type_means": type_means,
        "featured": featured,
    }


def scan_rejected():
    rows = []
    with ABC_T025.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            score = float(row.get("abc_score") or 0)
            if score >= 0.30:
                continue
            rows.append(
                {
                    "Group": "Threshold-rejected",
                    "Type": row.get("semopenalex_uri_type") or "unknown",
                    "Candidate count": int(float(row.get("yago_candidate_count") or 0)),
                    "Label frequency": int(float(row.get("semopenalex_label_freq") or 0)),
                    "embedding_cosine": float(row.get("embedding_cosine") or 0),
                    "profile_tfidf_score": float(row.get("profile_tfidf_score") or 0),
                    "neighbor_tfidf_score": float(row.get("neighbor_tfidf_score") or 0),
                    "abc_score": score,
                }
            )
    return rows


def scan_ambiguity_by_type():
    counts = Counter()
    total = 0
    with AMBIGUOUS_TOP1.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            entity_type = row.get("semopenalex_uri_type") or "unknown"
            candidates = int(float(row.get("yago_candidate_count") or 0))
            band = (
                "1"
                if candidates <= 1
                else "2"
                if candidates == 2
                else "3–5"
                if candidates <= 5
                else "6–10"
                if candidates <= 10
                else "11–20"
                if candidates <= 20
                else "21+"
            )
            counts[(entity_type, band)] += 1
            total += 1
    return {
        "total": total,
        "counts": [
            {"type": entity_type, "band": band, "count": count}
            for (entity_type, band), count in counts.items()
        ],
    }


def parse_embedding_results():
    pattern = re.compile(
        r"Stats:\s+loss:\s+([-\d.e]+)\s+,\s+pos_rank:\s+([-\d.e]+)\s+,\s+"
        r"mrr:\s+([-\d.e]+)\s+,\s+r1:\s+([-\d.e]+)\s+,\s+"
        r"r10:\s+([-\d.e]+)\s+,\s+r50:\s+([-\d.e]+)\s+,\s+"
        r"auc:\s+([-\d.e]+)\s+,\s+count:\s+(\d+)"
    )
    files = {
        ("YAGO", "TransE"): ROOT / "04_embeddings/analysis/yago/yago_transe_official_eval.txt",
        ("YAGO", "DistMult"): ROOT / "04_embeddings/analysis/yago/yago_distmult_official_eval.txt",
        ("YAGO", "ComplEx"): ROOT / "04_embeddings/analysis/yago/yago_complex_official_eval.txt",
        ("SemOpenAlex", "TransE"): ROOT / "04_embeddings/analysis/semopenalex/semopenalex_transe_official_eval_50k.txt",
        ("SemOpenAlex", "DistMult"): ROOT / "04_embeddings/analysis/semopenalex/semopenalex_distmult_official_eval_50k.txt",
        ("SemOpenAlex", "ComplEx"): ROOT / "04_embeddings/analysis/semopenalex/semopenalex_complex_official_eval_50k.txt",
    }
    rows = []
    for (dataset, model), path in files.items():
        last = None
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = pattern.search(line)
                if match:
                    last = match
        values = [float(value) for value in last.groups()[:-1]]
        rows.append(
            {
                "Dataset": dataset,
                "Model": model,
                **dict(zip(("Loss", "Positive rank", "MRR", "Hits@1", "Hits@10", "Hits@50", "AUC"), values)),
                "Test triples": int(last.group(8)),
            }
        )
    return rows


def training_results():
    paths = {
        "TransE": ROOT / "04_embeddings/output/yago/transe_cos/training_stats.json",
        "DistMult": ROOT / "04_embeddings/output/yago/distmult_dot/training_stats.json",
        "ComplEx": ROOT / "04_embeddings/output/yago/complex_dot/training_stats.json",
    }
    output = []
    for model, path in paths.items():
        sums = defaultdict(Counter)
        weights = defaultdict(Counter)
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if "stats" not in row or "epoch_idx" not in row:
                    continue
                epoch = int(row["epoch_idx"]) + 1
                train_count = float(row["stats"]["count"])
                sums[epoch]["Loss"] += float(row["stats"]["metrics"]["loss"]) * train_count
                weights[epoch]["Loss"] += train_count
                evaluation = row.get("eval_stats_after") or {}
                eval_count = float(evaluation.get("count") or 0)
                for label, key in {"MRR": "mrr", "Hits@10": "r10", "AUC": "auc"}.items():
                    value = evaluation.get("metrics", {}).get(key)
                    if value is not None and eval_count:
                        sums[epoch][label] += float(value) * eval_count
                        weights[epoch][label] += eval_count
        for epoch in sorted(sums):
            for metric in ("Loss", "MRR", "Hits@10", "AUC"):
                if weights[epoch][metric]:
                    output.append(
                        {
                            "Model": model,
                            "Epoch": epoch,
                            "Metric": metric,
                            "Value": sums[epoch][metric] / weights[epoch][metric],
                        }
                    )
    return output


def _system_summary(system_scan):
    """Build the comparison table from the exact files scanned for the figures."""
    specifications = [
        (
            "baseline",
            1,
            ROOT / "05_entity_alignment/final_alignment/outputs/strict/evaluation_summary.tsv",
            ROOT / "05_entity_alignment/final_alignment/outputs/strict/type_distribution.tsv",
        ),
        (
            "A+B",
            2,
            ROOT / "06_experiments/type_text_enrichment/outputs/strict/evaluation_summary.tsv",
            ROOT / "06_experiments/type_text_enrichment/outputs/strict/type_distribution.tsv",
        ),
        (
            "C only",
            4,
            ROOT / "06_experiments/graph_neighbor_only/outputs/strict/evaluation_summary.tsv",
            ROOT / "06_experiments/graph_neighbor_only/outputs/strict/type_distribution.tsv",
        ),
        (
            "A+B+C final",
            8,
            ROOT / "06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030_eval_summary.tsv",
            ROOT / "06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030_types.tsv",
        ),
    ]
    intersection_counts = {
        int(mask): int(count)
        for mask, count in system_scan["intersection_counts"].items()
    }
    rows = []
    for system, bit, evaluation_path, types_path in specifications:
        evaluation = read_kv(evaluation_path)
        types_frame = pd.read_csv(types_path, sep="\t")
        type_column = (
            "semopenalex_type"
            if "semopenalex_type" in types_frame.columns
            else "semopenalex_uri_type"
        )
        count_column = "count" if "count" in types_frame.columns else "rows"
        type_counts = dict(zip(types_frame[type_column], types_frame[count_column]))
        total = int(evaluation["final_alignments"])
        shared = (
            total
            if bit == 1
            else sum(
                count
                for mask, count in intersection_counts.items()
                if mask & 1 and mask & bit
            )
        )
        rows.append(
            {
                "system": system,
                "rows": total,
                "pairs_in_proxy_gold": int(evaluation["final_pairs_in_proxy_gold"]),
                "proxy_precision_like": float(evaluation["proxy_precision_like"]),
                "proxy_recall_like": float(evaluation["proxy_recall_like"]),
                "shared_with_baseline": shared,
                "baseline_only": int(read_kv(specifications[0][2])["final_alignments"]) - shared,
                "system_only": total - shared,
                "author_count": int(type_counts.get("author", 0)),
                "work_count": int(type_counts.get("work", 0)),
                "institution_count": int(type_counts.get("institution", 0)),
                "source_count": int(type_counts.get("source", 0)),
                "low_embedding_count": int(evaluation.get("<0.30", 0)),
            }
        )
    return rows


def summary_tables(system_scan):
    return {
        "yago_dataset": read_json(ROOT / "03_integer_encoding/yago/dataset_stats.json"),
        "soa_dataset": read_json(ROOT / "03_integer_encoding/semopenalex/dataset_stats.json"),
        "yago_preprocessing": read_json(ROOT / "02_preprocessed/yago/stats.json"),
        "soa_preprocessing": read_json(ROOT / "02_preprocessed/semopenalex_clean/merge_summary.json"),
        "candidate_filtered": read_kv(
            ROOT / "05_entity_alignment/data/candidates/exact_label_candidates_filtered_summary.tsv"
        ),
        "baseline_summary": read_kv(
            ROOT / "05_entity_alignment/final_alignment/outputs/strict/evaluation_summary.tsv"
        ),
        "threshold_sweep": pd.read_csv(
            ROOT / "05_entity_alignment/outputs/final/threshold_sweep_summary.tsv", sep="\t"
        ).to_dict("records"),
        "systems": _system_summary(system_scan),
        "sensitivity": pd.read_csv(
            ROOT / "06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_sensitivity_summary.tsv",
            sep="\t",
        ).to_dict("records"),
        "baseline_types": pd.read_csv(
            ROOT / "05_entity_alignment/final_alignment/outputs/strict/type_distribution.tsv",
            sep="\t",
        ).to_dict("records"),
        "final_types": pd.read_csv(
            ROOT / "06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030_types.tsv",
            sep="\t",
        ).to_dict("records"),
    }


def build_statistics(refresh=False):
    OUT.mkdir(parents=True, exist_ok=True)
    if CACHE.exists() and not refresh:
        with CACHE.open("rb") as handle:
            return pickle.load(handle)
    system_scan = scan_systems()
    data = {
        "relations": {
            "YAGO": relation_profile(
                ROOT / "03_integer_encoding/yago/test.tsv",
                ROOT / "03_integer_encoding/yago/relations.dict",
            ),
            "SemOpenAlex": relation_profile(
                ROOT / "03_integer_encoding/semopenalex/test.tsv",
                ROOT / "03_integer_encoding/semopenalex/relations.dict",
            ),
        },
        "systems": system_scan,
        "rejected": scan_rejected(),
        "ambiguity_by_type": scan_ambiguity_by_type(),
        "embedding_results": parse_embedding_results(),
        "training": training_results(),
        "summaries": summary_tables(system_scan),
    }
    with CACHE.open("wb") as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return data
