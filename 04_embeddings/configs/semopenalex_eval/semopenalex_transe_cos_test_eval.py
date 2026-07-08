def get_torchbiggraph_config():
    return {
        "entity_path": "/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/input/semopenalex",
        "edge_paths": ["/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/input_eval/semopenalex_test_sampled_50k"],
        "checkpoint_path": "/data/horse/ws/jovu353i-kgalign/KGAlignment/04_embeddings/output/semopenalex/transe_cos",

        "entities": {
            "entity": {"num_partitions": 128}
        },

        "relations": [
            {
                "name": f"r{i}",
                "lhs": "entity",
                "rhs": "entity",
                "operator": "translation",
            }
            for i in range(31)
        ],

        "dynamic_relations": False,
        "dimension": 200,
        "global_emb": False,
        "comparator": "cos",
        "bias": False,
        "init_scale": 0.001,
        "verbose": 1,
    }
