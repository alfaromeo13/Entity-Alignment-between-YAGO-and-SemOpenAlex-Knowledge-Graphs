def get_torchbiggraph_config():
    return {
        "entity_path": "/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/input/yago",
        "edge_paths": ["/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/input/yago"],
        "checkpoint_path": "/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/output/yago/complex_dot",

        "entities": {
            "entity": {"num_partitions": 32}
        },

        "relations": [
            {
                "name": f"r{i}",
                "lhs": "entity",
                "rhs": "entity",
                "operator": "complex_diagonal",
            }
            for i in range(68)
        ],

        "dynamic_relations": False,

        "dimension": 200,
        "global_emb": False,
        "comparator": "dot",
        "bias": True,
        "init_scale": 0.1,

        "num_epochs": 5,
        "workers": 28,
        "batch_size": 100000,
        "num_batch_negs": 1000,
        "num_uniform_negs": 1000,
        "loss_fn": "logistic",
        "lr": 0.1,

        "max_edges_per_chunk": 50000000,
        "bucket_order": "inside_out",

        "eval_fraction": 0.01,
        "eval_num_batch_negs": 1000,
        "eval_num_uniform_negs": 1000,

        "verbose": 1,
    }
