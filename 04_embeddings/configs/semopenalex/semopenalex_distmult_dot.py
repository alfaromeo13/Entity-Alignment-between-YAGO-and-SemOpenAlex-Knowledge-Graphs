def get_torchbiggraph_config():
    return {
        "entity_path": "/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/input/semopenalex",
        "edge_paths": ["/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/input/semopenalex"],
        "checkpoint_path": "/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/output/semopenalex/distmult_dot",

        "entities": {
            "entity": {"num_partitions": 128}
        },

        "relations": [
            {
                "name": f"r{i}",
                "lhs": "entity",
                "rhs": "entity",
                "operator": "diagonal",
            }
            for i in range(31)
        ],

        "dynamic_relations": False,

        "dimension": 200,
        "global_emb": False,
        "comparator": "dot",
        "bias": True,
        "init_scale": 0.1,

        "num_epochs": 3,
        "workers": 28,
        "batch_size": 200000,
        "num_batch_negs": 1000,
        "num_uniform_negs": 1000,
        "loss_fn": "logistic",
        "lr": 0.1,

        "max_edges_per_chunk": 100000000,
        "bucket_order": "inside_out",

        "eval_fraction": 0.0,

        "verbose": 1,
    }
