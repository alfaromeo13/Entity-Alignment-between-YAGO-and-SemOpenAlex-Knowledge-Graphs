# PyTorch-BigGraph Embedding Training and Evaluation

This stage trains and evaluates knowledge graph embeddings for YAGO and SemOpenAlex using PyTorch-BigGraph.

The integer-encoded datasets produced in `03_integer_encoding/` are converted into the partitioned HDF5 format required by PyTorch-BigGraph. After conversion, TransE, DistMult, and ComplEx models are trained and evaluated using link prediction.

The trained embeddings are later used in the entity alignment pipeline as a structural signal for scoring and reranking ambiguous candidate alignments.

## Purpose

The goal of this stage is to learn vector representations of entities and relations in both knowledge graphs.

These embeddings are not used to generate all possible cross-graph entity pairs directly. Instead, they are used later in the entity alignment stage to help resolve ambiguous candidate matches that were first generated using textual labels.

In the full pipeline, this stage has the following role:

```text
Integer-encoded graph triples
        ↓
PyTorch-BigGraph data conversion
        ↓
Embedding training
        ↓
Link prediction evaluation
        ↓
Best model selection
        ↓
Entity alignment
```

## Input Data

The input data comes from:

```text
03_integer_encoding/yago/
03_integer_encoding/semopenalex/
```

Each dataset contains:

```text
entities.dict
relations.dict
train.tsv
valid.tsv
test.tsv
dataset_stats.json
```

The graph triples are already integer-encoded:

```text
head_id<TAB>relation_id<TAB>tail_id
```

The `train.tsv`, `valid.tsv`, and `test.tsv` files were created earlier during preprocessing.

- `train.tsv` is used for embedding training.
- `test.tsv` is held out and used for link prediction evaluation.
- `valid.tsv` can be used for validation or tuning.

## Folder Structure

```text
04_embeddings/
├── analysis/
│   ├── semopenalex/
│   └── yago/
│
├── configs/
│   ├── yago/
│   ├── yago_eval/
│   ├── semopenalex/
│   └── semopenalex_eval/
│
├── logs/
├── input/
├── input_eval/
├── output/
│   ├── yago/
│   └── semopenalex/
│
├── scripts/
│   ├── convert_to_pbg.py
│   ├── patch_pbg_ids.py
│   ├── sample_pbg_eval_dataset.py
│   ├── convert_yago.sbatch
│   ├── convert_semopenalex.sbatch
│   ├── patch_yago.sbatch
│   ├── patch_semopenalex.sbatch
│   ├── train_semopenalex_pbg_generic.sbatch
│   ├── train_pbg_generic.sbatch
│   └── eval_pbg_generic.sbatch
│
└── README.md
```

The repository uses generic Slurm wrappers for embedding training and evaluation. 
`train_pbg_generic.sbatch` is used for YAGO, while `train_semopenalex_pbg_generic.sbatch` is used for SemOpenAlex because the two datasets require different default resource allocations and configuration layouts.

Individual experiments are selected through the `PBG_CONFIG` and `PBG_EVAL_CONFIG` environment variables, while descriptive Slurm job names (e.g., `soa_distmult_dot`, `yago_eval_transe`) are assigned when submitting jobs. This avoids maintaining separate wrapper scripts for each embedding model while preserving clear experiment tracking in Slurm and PIKA.

## Why PyTorch-BigGraph Was Used

PyTorch-BigGraph is designed for large-scale knowledge graph embedding training. It supports graph partitioning, negative sampling, and distributed processing, making it suitable for graphs containing hundreds of millions or even billions of entities and edges.

PyTorch-BigGraph was selected because earlier embedding experiments did not scale well to the size of the final YAGO and SemOpenAlex datasets. Its partitioned training architecture enabled scalable embedding generation while keeping memory requirements manageable.

In this project, PyTorch-BigGraph was used to train three knowledge graph embedding models:

```text
TransE
DistMult
ComplEx
```

These models were selected because they are standard knowledge graph embedding models and can be expressed using PyTorch-BigGraph operators and comparators.

## Model Configurations

The embedding configurations are stored in:

```text
04_embeddings/configs/yago/
04_embeddings/configs/semopenalex/
```

Evaluation configurations are stored in:

```text
04_embeddings/configs/yago_eval/
04_embeddings/configs/semopenalex_eval/
```

The main trained models were:

```text
TransE      translation operator + cosine comparator
DistMult    diagonal operator + dot comparator
ComplEx     complex diagonal operator + dot comparator
```

The general configuration choices were:

```text
Embedding dimension: 200
YAGO partitions: 32
SemOpenAlex partitions: 128
YAGO epochs: 5
SemOpenAlex epochs: 3
```

SemOpenAlex used more partitions because it is much larger than YAGO.

## Scripts

### `convert_to_pbg.py`

Converts integer-encoded graph triples into the partitioned HDF5 bucket format required by PyTorch-BigGraph.

Input:

```text
head_id<TAB>relation_id<TAB>tail_id
```

Output:

```text
edges_<left_partition>_<right_partition>.h5
entity_count_entity_<partition>.txt
```

The script partitions graph edges according to entity IDs and prepares the dataset for scalable PyTorch-BigGraph training.

The partitioning logic uses the integer entity ID modulo the number of partitions. This convention is also used later when loading embeddings for candidate scoring.

### `patch_pbg_ids.py`

Fixes entity identifiers inside the generated PyTorch-BigGraph partitions.

During conversion, edges are written using global entity IDs. However, PyTorch-BigGraph expects entity IDs inside each partition to be local to that partition. This script remaps global entity IDs into partition-local IDs and updates the HDF5 buckets.

This patching step is required before training can begin.

This script is not only a file-format cleanup step: it converts global entity IDs into partition-local offsets, matching the indexing convention expected by PyTorch-BigGraph checkpoint files.

### `sample_pbg_eval_dataset.py`

Creates sampled evaluation datasets from a full PyTorch-BigGraph test set.

This was primarily used for SemOpenAlex because the full test set contains millions of edges, making complete evaluation computationally expensive. A sampled test set gives a practical estimate of link prediction performance while keeping evaluation time manageable.

The sampling preserves the full partition grid and allocates the 50k sample proportionally across non-empty buckets, so the evaluation subset remains compatible with the PyTorch-BigGraph evaluator.

## Execution Order

All large jobs should be submitted through Slurm.

### 1. Convert YAGO to PyTorch-BigGraph format

```bash
sbatch 04_embeddings/scripts/convert_yago.sbatch
```

### 2. Patch YAGO partition-local IDs

```bash
sbatch 04_embeddings/scripts/patch_yago.sbatch
```

This converts global entity IDs inside the generated HDF5 buckets into partition-local IDs expected by PyTorch-BigGraph.

### 3. Train YAGO embeddings

The generic training wrapper is reused for all YAGO embedding models. The specific configuration is selected using the `PBG_CONFIG` environment variable, while the submitted Slurm job name identifies the experiment.

TransE

```bash
PBG_CONFIG=04_embeddings/configs/yago/yago_transe_cos.py \
sbatch --job-name=yago_transe_cos \
04_embeddings/scripts/train_pbg_generic.sbatch
```

DistMult

```bash
PBG_CONFIG=04_embeddings/configs/yago/yago_distmult_dot.py \
sbatch --job-name=yago_distmult_dot \
04_embeddings/scripts/train_pbg_generic.sbatch
```

ComplEx

```bash
PBG_CONFIG=04_embeddings/configs/yago/yago_complex_dot.py \
sbatch --job-name=yago_complex_dot \
04_embeddings/scripts/train_pbg_generic.sbatch
```

### 4. Convert SemOpenAlex to PyTorch-BigGraph format

```bash
sbatch 04_embeddings/scripts/convert_semopenalex.sbatch
```

### 5. Patch SemOpenAlex partition-local IDs

```bash
sbatch 04_embeddings/scripts/patch_semopenalex.sbatch
```

This step is required before training because PyTorch-BigGraph expects local entity IDs inside each partition.

### 6. Train SemOpenAlex embeddings

The SemOpenAlex training wrapper is reused for all SemOpenAlex embedding models, with the specific model determined by `PBG_CONFIG`.

TransE

```bash
PBG_CONFIG=04_embeddings/configs/semopenalex/semopenalex_transe_cos.py \
sbatch --job-name=soa_transe_cos \
04_embeddings/scripts/train_semopenalex_pbg_generic.sbatch
```

DistMult

```bash
PBG_CONFIG=04_embeddings/configs/semopenalex/semopenalex_distmult_dot.py \
sbatch --job-name=soa_distmult_dot \
04_embeddings/scripts/train_semopenalex_pbg_generic.sbatch
```

ComplEx

```bash
PBG_CONFIG=04_embeddings/configs/semopenalex/semopenalex_complex_dot.py \
sbatch --job-name=soa_complex_dot \
04_embeddings/scripts/train_semopenalex_pbg_generic.sbatch
```

### 7. Convert the held-out test splits into the partitioned HDF5 bucket format required by PyTorch-BigGraph evaluation.

Convert the held-out test splits into PyTorch-BigGraph bucket format.

**YAGO:**

```bash
python 04_embeddings/scripts/convert_to_pbg.py \
  --input 03_integer_encoding/yago/test.tsv \
  --out 04_embeddings/input_eval/yago_test \
  --entities "$(wc -l < 03_integer_encoding/yago/entities.dict)" \
  --partitions 32

python 04_embeddings/scripts/patch_pbg_ids.py \
  --edge-dir 04_embeddings/input_eval/yago_test \
  --num-partitions 32
```

**SemOpenAlex:**

```bash
python 04_embeddings/scripts/convert_to_pbg.py \
  --input 03_integer_encoding/semopenalex/test.tsv \
  --out 04_embeddings/input_eval/semopenalex_test \
  --entities 1936550634 \
  --partitions 128

python 04_embeddings/scripts/patch_pbg_ids.py \
  --edge-dir 04_embeddings/input_eval/semopenalex_test \
  --num-partitions 128
```

### 8. Prepare SemOpenAlex sampled evaluation data

Because the complete SemOpenAlex test split contains millions of triples, a stratified 50,000-edge sampled evaluation dataset was generated for link prediction. This substantially reduced evaluation time while preserving a representative estimate of embedding quality.

```bash
python 04_embeddings/scripts/sample_pbg_eval_dataset.py \
  --input-dir 04_embeddings/input_eval/semopenalex_test \
  --output-dir 04_embeddings/input_eval/semopenalex_test_sampled_50k \
  --num-partitions 128 \
  --target-total 50000
```

### 9. Run link prediction evaluation

**YAGO:**

TransE

```bash
PBG_EVAL_CONFIG=04_embeddings/configs/yago_eval/yago_transe_cos_test_eval.py \
PBG_EVAL_TXT=04_embeddings/analysis/yago/yago_transe_official_eval.txt \
sbatch --job-name=yago_eval_transe \
04_embeddings/scripts/eval_pbg_generic.sbatch
```

DistMult

```bash
PBG_EVAL_CONFIG=04_embeddings/configs/yago_eval/yago_distmult_dot_test_eval.py \
PBG_EVAL_TXT=04_embeddings/analysis/yago/yago_distmult_official_eval.txt \
sbatch --job-name=yago_eval_distmult \
04_embeddings/scripts/eval_pbg_generic.sbatch
```

ComplEx

```bash
PBG_EVAL_CONFIG=04_embeddings/configs/yago_eval/yago_complex_dot_test_eval.py \
PBG_EVAL_TXT=04_embeddings/analysis/yago/yago_complex_official_eval.txt \
sbatch --job-name=yago_eval_complex \
04_embeddings/scripts/eval_pbg_generic.sbatch
```

**SemOpenAlex:**

TransE

```bash
PBG_EVAL_CONFIG=04_embeddings/configs/semopenalex_eval/semopenalex_transe_cos_test_eval.py \
PBG_EVAL_TXT=04_embeddings/analysis/semopenalex/semopenalex_transe_official_eval_50k.txt \
sbatch --job-name=soa_eval_transe_50k \
04_embeddings/scripts/eval_pbg_generic.sbatch
```

DistMult

```bash
PBG_EVAL_CONFIG=04_embeddings/configs/semopenalex_eval/semopenalex_distmult_dot_test_eval.py \
PBG_EVAL_TXT=04_embeddings/analysis/semopenalex/semopenalex_distmult_official_eval_50k.txt \
sbatch --job-name=soa_eval_distmult_50k \
04_embeddings/scripts/eval_pbg_generic.sbatch
```

ComplEx

```bash
PBG_EVAL_CONFIG=04_embeddings/configs/semopenalex_eval/semopenalex_complex_dot_test_eval.py \
PBG_EVAL_TXT=04_embeddings/analysis/semopenalex/semopenalex_complex_official_eval_50k.txt \
sbatch --job-name=soa_eval_complex_50k \
04_embeddings/scripts/eval_pbg_generic.sbatch
```

### 10. Generate analysis tables and figures

```bash
python 04_embeddings/analysis/yago/plot_yago_visualizations.py
```
These plots are useful because YAGO had evaluation enabled during training.

## Training Time

The time required to train the embedding models depends primarily on the size of the knowledge graph.

For **YAGO**, training typically takes **10–15 hours**, so the entire process can usually be completed within a single Slurm job.

Training embeddings for **SemOpenAlex** is more computationally demanding and typically takes **10–20 days**, depending on the selected embedding model and the available HPC resources. Since jobs on the TU Dresden HPC system are limited to a maximum wall time of **7 days**, long-running experiments had to be resumed multiple times. In practice, training most SemOpenAlex models required **two or three consecutive job submissions**.

To avoid maintaining separate Slurm scripts for every experiment, the repository uses generic training and evaluation wrappers (`train_pbg_generic.sbatch` and `eval_pbg_generic.sbatch`). The embedding model and configuration are selected through environment variables, while the submitted Slurm job name is used to distinguish individual experiments.

## Evaluation Strategy

Link prediction was used as an intrinsic evaluation of embedding quality.

The purpose of link prediction evaluation was to check whether the trained embeddings captured useful structural patterns in each graph before using them in the entity alignment pipeline.

The main metrics were:

```text
MRR
Hits@1
Hits@10
Hits@50
AUC
Positive rank
```

YAGO was evaluated on its full test split.

SemOpenAlex was evaluated on a sampled 50k held-out test set. A 50k sample was considered sufficiently large to provide stable link prediction estimates while keeping evaluation computationally feasible.

Training-time evaluation was disabled for SemOpenAlex to make training feasible at scale. Therefore, SemOpenAlex results are reported as final sampled link prediction tables rather than epoch-wise MRR, Hits@k, or AUC curves.

## Link Prediction Results

YAGO was evaluated on the full test split of 176,574 triples.

| Model | MRR | Hits@1 | Hits@10 | Hits@50 | AUC | PosRank |
|---|---:|---:|---:|---:|---:|---:|
| TransE | 0.4366 | 0.3349 | 0.6172 | 0.9856 | 0.7676 | 12.83 |
| DistMult | 0.4976 | 0.4181 | 0.6199 | 0.9703 | 0.7438 | 14.05 |
| ComplEx | 0.4791 | 0.4007 | 0.6008 | 0.9615 | 0.7293 | 14.80 |

DistMult achieved the strongest YAGO MRR and Hits@1, while TransE achieved the strongest AUC and Hits@50.

SemOpenAlex was evaluated on a sampled 50k held-out test set.

| Model | MRR | Hits@1 | Hits@10 | Hits@50 | AUC | PosRank |
|---|---:|---:|---:|---:|---:|---:|
| TransE | 0.7869 | 0.7242 | 0.9002 | 0.9963 | 0.9315 | 4.49 |
| DistMult | 0.8373 | 0.7998 | 0.9067 | 0.9995 | 0.9476 | 3.73 |
| ComplEx | 0.8361 | 0.7994 | 0.9041 | 0.9997 | 0.9456 | 3.80 |


DistMult achieved the strongest overall performance on both YAGO and SemOpenAlex and was therefore selected as the embedding model used in the final entity alignment pipeline.

SemOpenAlex final results were obtained from the official 50k sampled link prediction evaluation files:

```text
analysis/semopenalex/semopenalex_transe_official_eval_50k.txt
analysis/semopenalex/semopenalex_distmult_official_eval_50k.txt
analysis/semopenalex/semopenalex_complex_official_eval_50k.txt
```

## Important Outputs

The most important outputs of this stage are the trained embedding models stored in:

```text
04_embeddings/output/yago/
04_embeddings/output/semopenalex/
```

These outputs are consumed directly by the entity alignment stage (05_entity_alignment) for embedding-based candidate scoring and reranking.

These folders contain the trained embedding checkpoints and would be expensive to recreate.

Each model directory contains the PyTorch-BigGraph checkpoint files for one trained embedding model. These files store the learned entity and relation embeddings and are required by later stages that use embeddings for candidate scoring and reranking.

The final entity alignment pipeline primarily uses the DistMult model outputs:

```text
04_embeddings/output/yago/distmult_dot/
04_embeddings/output/semopenalex/distmult_dot/
```

The analysis/ folder contains the official link prediction evaluation outputs used to compare TransE, DistMult, and ComplEx.


## Role in the Full Pipeline

This stage produced graph embeddings for both YAGO and SemOpenAlex.

The final entity alignment pipeline uses the trained DistMult embeddings as a structural reranking signal. The embeddings are applied after textual candidate generation, not as an unrestricted all-vs-all matching method.

```text
Textual candidate generation
        ↓
Ambiguous candidates
        ↓
Embedding-based scoring / reranking
        ↓
Filtered one-to-one alignments
```

This design keeps the alignment process scalable while still using graph structure to improve candidate ranking.

## Summary

*This stage converted integer-encoded graph triples into PyTorch-BigGraph input format, trained TransE, DistMult, and ComplEx embeddings for YAGO and SemOpenAlex, evaluated the models using link prediction, and selected the strongest embeddings for downstream entity alignment.*

*YAGO was evaluated on the full test split, while SemOpenAlex was evaluated on a sampled 50k held-out test set due to scale. DistMult was selected as the main embedding model for the final entity alignment pipeline because it achieved strong and stable link prediction performance and provided a practical structural signal for reranking ambiguous candidate alignments.*
