#!/usr/bin/env python3
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edges", required=True)
    ap.add_argument("--out-config", required=True)
    ap.add_argument("--checkpoint-path", required=True)
    ap.add_argument("--operator", required=True, choices=["distmult", "complex_diagonal", "transe"])
    ap.add_argument("--num-partitions", type=int, default=8)
    ap.add_argument("--dimension", type=int, default=200)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--workers", type=int, default=64)
    args = ap.parse_args()

    rels = set()
    with open(args.edges, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                rels.add(p[1])
            if i % 100_000_000 == 0:
                print(f"scanned={i:,} relations={len(rels):,}", flush=True)

    rels = sorted(rels)

    with open(args.out_config, "w", encoding="utf-8") as out:
        out.write("def get_torchbiggraph_config():\n")
        out.write("    return dict(\n")
        out.write('        entity_path="/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/data/imported_p8",\n')
        out.write('        edge_paths=["/data/horse/ws/jovu353i-kgalign/KGAlignment/08_joint_embeddings/data/imported_p8"],\n')
        out.write(f'        checkpoint_path="{args.checkpoint_path}",\n')
        out.write(f'        entities={{"entity": {{"num_partitions": {args.num_partitions}}}}},\n')
        out.write("        relations=[\n")
        for r in rels:
            out.write(f'            {{"name": {r!r}, "lhs": "entity", "rhs": "entity", "operator": {args.operator!r}, "weight": 1.0}},\n')
        out.write("        ],\n")
        out.write(f"        dimension={args.dimension},\n")
        out.write("        global_emb=False,\n")
        out.write("        comparator='dot',\n")
        out.write(f"        num_epochs={args.epochs},\n")
        out.write("        num_uniform_negs=100,\n")
        out.write("        loss_fn='softmax',\n")
        out.write("        lr=0.1,\n")
        out.write("        eval_fraction=0.001,\n")
        out.write("        eval_num_batch_negs=100,\n")
        out.write(f"        workers={args.workers},\n")
        out.write("    )\n")

    print(f"Relations: {len(rels):,}")
    print(f"Wrote: {args.out_config}")

if __name__ == "__main__":
    main()
