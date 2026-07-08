#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path

VARIANTS = [
    ("abc_w060_035_005_t025", 0.60, 0.35, 0.05, 0.25),
    ("abc_w055_035_010_t025", 0.55, 0.35, 0.10, 0.25),
    ("abc_w065_030_005_t025", 0.65, 0.30, 0.05, 0.25),
    ("abc_w060_035_005_t030", 0.60, 0.35, 0.05, 0.30),
    ("abc_w060_035_005_t020", 0.60, 0.35, 0.05, 0.20),
]

def run(cmd):
    print(" ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--proxy-gold", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []

    for name, ew, pw, nw, threshold in VARIANTS:
        final = out_dir / f"{name}.tsv"
        comp = out_dir / f"{name}_vs_baseline.tsv"
        summ = out_dir / f"{name}_eval_summary.tsv"
        types = out_dir / f"{name}_types.tsv"
        sources = out_dir / f"{name}_sources.tsv"

        run([
            "python",
            "06_experiments/graph_neighbor_signal/scripts/create_final_abc_alignments.py",
            "--input", args.input,
            "--output", str(final),
            "--embedding-weight", str(ew),
            "--profile-weight", str(pw),
            "--neighbor-weight", str(nw),
            "--min-score", str(threshold),
        ])

        run([
            "python",
            "06_experiments/type_text_enrichment/scripts/compare_baseline_vs_enriched.py",
            "--baseline", args.baseline,
            "--enriched", str(final),
            "--out-summary", str(comp),
        ])

        run([
            "python",
            "05_entity_alignment/scripts/evaluate_final_alignments.py",
            "--final", str(final),
            "--proxy-gold", args.proxy_gold,
            "--out-summary", str(summ),
            "--out-type-dist", str(types),
            "--out-source-dist", str(sources),
        ])

        vals = {"variant": name, "embedding_weight": ew, "profile_weight": pw, "neighbor_weight": nw, "threshold": threshold}

        with open(summ, encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) == 2 and parts[0] in {
                    "final_alignments",
                    "final_pairs_in_proxy_gold",
                    "proxy_precision_like",
                    "proxy_recall_like",
                }:
                    vals[parts[0]] = parts[1]

        with open(comp, encoding="utf-8") as f:
            next(f)
            for line in f:
                metric, value = line.rstrip("\n").split("\t")
                vals[metric] = value

        rows.append(vals)

    summary = out_dir / "abc_sensitivity_summary.tsv"
    cols = [
        "variant",
        "embedding_weight",
        "profile_weight",
        "neighbor_weight",
        "threshold",
        "final_alignments",
        "final_pairs_in_proxy_gold",
        "proxy_precision_like",
        "proxy_recall_like",
        "shared_pairs",
        "baseline_only_pairs",
        "enriched_only_pairs",
    ]

    with open(summary, "w", encoding="utf-8") as out:
        out.write("\t".join(cols) + "\n")
        for r in rows:
            out.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")

    print(f"\nWrote sensitivity summary: {summary}")

if __name__ == "__main__":
    main()
