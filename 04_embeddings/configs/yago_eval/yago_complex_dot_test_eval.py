def get_torchbiggraph_config():
    return {
        "entity_path": "/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/input/yago",
        "edge_paths": ["/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/input_eval/yago_test"],
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
        "verbose": 1,
    }
