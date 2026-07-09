# Integer Dataset Preparation

This stage converts the cleaned graph datasets produced in `02_preprocessed/` into a numerical representation suitable for large-scale knowledge graph embedding frameworks.

The preprocessed datasets store graph triples using RDF URIs:

```text
subject_uri<TAB>predicate_uri<TAB>object_uri
```

To enable efficient embedding training, each unique entity and relation is assigned a unique integer ID. The resulting graph representation becomes:

```text
head_id<TAB>relation_id<TAB>tail_id
```

This integer format is smaller, faster, and suitable for large-scale embedding pipelines. The generated datasets preserve mappings between RDF resources and integer identifiers, allowing embeddings to be mapped back to the original entities in later stages of the pipeline.

## Runtime Folder Structure

Only `scripts/` and this README are expected to be present in a fresh GitHub
clone. The encoded `yago/` and `semopenalex/` directories are generated outputs
and are intentionally excluded from Git.

```text
03_integer_encoding/
├── scripts/
│   ├── prepare_integer_dataset.py
│   └── soa_integer_prep.sbatch
├── yago/          # generated integer-encoded YAGO dataset, ignored by Git
├── semopenalex/   # generated integer-encoded SemOpenAlex dataset, ignored by Git
└── README.md
```

After this stage has run, the `yago/` and `semopenalex/` directories contain the
final integer-encoded datasets.

## Processing Workflow

```text
Preprocessed Graph Datasets
(02_preprocessed/)
            ↓
Entity and Relation Mapping
            ↓
Dictionary Construction
            ↓
Integer Triple Generation
            ↓
Embedding-Ready Datasets
```

## Main Script

**prepare_integer_dataset.py**

This script reads: `train.tsv`, `valid.tsv`, `test.tsv`

It produces: `entities.dict`, `relations.dict`, `train.tsv`, `valid.tsv`, `test.tsv`, `dataset_stats.json`

The script scans all graph triples, creates entity and relation mappings (unique integer identifiers), rewrites graph triples using integer identifiers, and generates dataset statistics.

The important implementation choice is that mappings are built from the graph splits and then reused consistently across `train.tsv`, `valid.tsv`, and `test.tsv`. This ensures that the same URI always receives the same integer ID within a dataset.

The dictionary format is:

```text
URI<TAB>ID
```

The integer triple format is:

```text
head_id<TAB>relation_id<TAB>tail_id
```

# Execution 

**1. Prepare YAGO integer dataset**

YAGO was small enough to be processed directly with the Python script on a standard compute node.

Command:

```bash
python3 03_integer_encoding/scripts/prepare_integer_dataset.py \
  --input-dir 02_preprocessed/yago \
  --output-dir 03_integer_encoding/yago \
  --dataset-name yago
```

Expected documented YAGO scale:

```text
num_entities: 99,313,458
num_relations: 68
train_triples: 176,220,725
valid_triples: 176,573
test_triples: 176,574
```
---
**2. Prepare SemOpenAlex integer dataset**

```bash
sbatch 03_integer_encoding/scripts/soa_integer_prep.sbatch
```

## Why This Stage Exists

The project intentionally separates preprocessing and integer encoding.

The datasets in `02_preprocessed/` remain human-readable and easy to inspect, while the datasets in `03_integer_encoding/` are optimized for efficient embedding training. This separation also makes it possible to reuse the same preprocessed datasets with <ins>different embedding frameworks</ins>.


## Summary

*This stage converts URI-based graph datasets into integer-encoded representations suitable for large-scale embedding training. Entity and relation dictionaries are generated, graph triples are rewritten using integer identifiers, and the resulting datasets are used as input for the PyTorch-BigGraph embedding stage.*
