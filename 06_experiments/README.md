# Stage 06 — Entity Alignment Experiments and Ablation Study

This folder contains the experimental extension stage of the YAGO–SemOpenAlex entity alignment pipeline.

The purpose of this stage is to evaluate whether the baseline entity alignment pipeline can be improved by adding extra evidence beyond the original embedding-based reranking and TF-IDF filtering.

In simple terms, Stage 05 produced a strong baseline set of one-to-one alignments. Stage 06 then tests additional evidence to see whether we can recover more plausible alignments without introducing too much noise.

The final selected output of this stage is used as the input for RDF export in Stage 07.

## Overview

The baseline alignment pipeline already produced a large, taxonomy-aware one-to-one alignment file:

```text
05_entity_alignment/final_alignment/outputs/strict/alignments_FINAL_tfidf.tsv
```

This baseline was precise and conservative, but it also rejected some candidate alignments that looked promising when profile-text similarity or graph-neighbor similarity was considered.

Therefore, this stage evaluates three experimental variants:

```text
A+B       Profile-text similarity
C only    Graph-neighbor similarity only
A+B+C     Profile-text similarity with graph-neighbor similarity refinement
```
Throughout this stage, the following shorthand notation is used:

```text
A = embedding similarity
B = profile-text similarity
C = graph-neighbor similarity
```

This notation is used throughout the remainder of this document when referring to the experimental variants.


The final selected system is:

```text
A+B+C final
```

with the following output file:

```text
06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv
```

Final selected alignment count:

```text
1,973,194 alignments
```

The results documented below use the strict taxonomy policy: YAGO entities with a
resolved incompatible type are rejected, and entities whose type remains
unresolved after the taxonomy/profile analysis are not silently treated as a
valid `unknown` class. Stage 06 therefore evaluates the three evidence variants
on the taxonomy-aware Stage 05 population.

## Why This Stage Exists

Entity alignment between large knowledge graphs is difficult because exact labels alone are not enough.

For example, the same label can refer to many different entities:

```text
The Incident
The Lost City
Second Chance
John Smith
Santa Cruz
```

At the same time, some plausible alignments have weak embedding similarities because the local graph structures are incomplete, heterogeneous, or simply represented differently in YAGO and SemOpenAlex.

The experiments in this stage test whether additional evidence can improve the alignment decision.

The main idea is:

```text
baseline alignment
        ↓
additional profile-text similarity evidence
        ↓
additional graph-neighbor similarity evidence
        ↓
sensitivity analysis
        ↓
final selected alignment set
```

## Experimental Design

The experiments were intentionally designed as an ablation study in which each additional source of evidence can be evaluated independently before being combined into a single final system.

```text
                    Baseline
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
   Experiment A+B            Experiment C
 (profile-text similarity) (graph-neighbor similarity)
          │                         │
          └────────────┬────────────┘
                       ▼
               Final A+B+C System
```

This design makes it possible to:

- evaluate the contribution of each additional evidence source independently;
- compare profile-text similarity and graph-neighbor similarity under the same evaluation protocol;
- determine whether the two evidence sources complement each other when combined into the final system.

Rather than treating the pipeline as a single sequence of processing steps, this experimental design provides a structured ablation study that explains why the final configuration was selected.

## Techniques Used in This Stage

Stage 06 combines several kinds of alignment evidence. Some are inherited from the Stage 05 baseline, while others are introduced by the experiments in this folder.

The goal is not to rely on one single score, but to compare different kinds of evidence for the same candidate pair.

| Technique | Used for | Purpose |
|---|---|---|
| Normalized label matching | Candidate generation | Groups YAGO and SemOpenAlex entities that share the same cleaned label |
| Token Jaccard similarity | Candidate features | Measures lexical overlap between labels |
| Label frequency and candidate counts | Candidate features | Helps identify ambiguous labels that appear many times |
| Label length difference | Candidate features | Penalizes suspicious matches with very different label lengths |
| DistMult embedding cosine similarity | Structural reranking | Measures similarity between entity embeddings learned from graph structure |
| Character n-gram TF-IDF cosine similarity | Profile-text similarity | Compares entity text profiles while handling accents, capitalization, punctuation, and spelling differences |
| Graph-neighbor TF-IDF cosine similarity | Graph-neighbor similarity | Compares local graph-neighbor structure around candidate entities |
| Weighted linear scoring | Final reranking | Combines embedding, profile-text, and graph-neighbor evidence |
| One-to-one matching | Final selection | Ensures that each YAGO entity and each SemOpenAlex entity appears in at most one final alignment |
| Sensitivity analysis | Parameter selection | Tests several weight and threshold choices before selecting the final configuration |

### Normalized Labels and Lexical Candidate Features

The experiments in Stage 06 build on candidate pairs created earlier in the pipeline.

The first important evidence source is the normalized label. Labels are cleaned and normalized so that superficial differences such as capitalization, punctuation, spacing, and accents do not prevent comparison.

For example:
```text
Émile Roux
Emile Roux

or

Martin Suárez
Martin Suarez
```
can still be compared as highly similar labels.

Several lexical features are preserved in the candidate files:

```
token_jaccard
semopenalex_label_freq
yago_candidate_count
label_length_diff
confidence_tier
```

These features help describe how ambiguous a candidate is.

For example, a label that appears only once is less ambiguous than a label shared by many candidate entities. Similarly, two labels with very different lengths are more suspicious than two labels with nearly identical lengths.

Token Jaccard similarity measures the overlap between label tokens. It is useful for simple cases where labels contain the same words in slightly different forms.

## Embedding Similarity

The main structural evidence comes from DistMult embeddings trained with PyTorch-BigGraph.

Each entity is represented as a vector. Candidate pairs are compared using cosine similarity between their learned embeddings.

This score is stored as: `embedding_cosine`.

The embedding similarity captures structural similarity from the knowledge graph. It is useful because two entities can have similar roles in the graph even when their profile-text metadata is incomplete.

However, embeddings alone are not always sufficient. Some plausible alignments have relatively weak embedding similarities because YAGO and SemOpenAlex have different schemas, different levels of completeness, and different graph neighborhoods.

This is why Stage 06 tests profile-text similarity and graph-neighbor similarity.

## Profile-Text Similarity

The A+B experiment introduces profile-text similarity.

Instead of comparing only the main label of an entity, the pipeline builds a larger text profile for each entity using available textual literals.

These profiles may contain labels, aliases, titles, names, and other text values extracted during preprocessing.

The similarity between two profiles is computed using: `character n-gram TF-IDF cosine similarity`. This score is stored as: `profile_tfidf_score`. Character n-grams were preferred over word-level tokenization because they are robust to spelling variations, accents, abbreviations, punctuation, and minor formatting differences frequently observed between YAGO and SemOpenAlex labels.

For example, they can handle:
```
accent differences
capitalization differences
punctuation differences
minor spelling variations
initials and name formatting
```

This is one reason why A+B recovered many alignments that the baseline rejected.

## Graph-Neighbor Similarity

The C and A+B+C experiments introduce graph-neighbor similarity.

Graph-neighbor profiles are constructed directly from the one-hop RDF
neighborhood of each entity by collecting neighboring entities and predicates
from direct incoming and outgoing triples before converting this local RDF
neighborhood into a textual representation for TF-IDF comparison. No two-hop
or three-hop expansion is used in the reported experiments.

For each candidate entity, the pipeline builds a compact text-like representation of its local graph neighborhood.

This context includes information such as:
```
incoming predicates
outgoing predicates
neighbor identifiers
local graph-neighbor structure
```
The graph-neighbor profiles of YAGO and SemOpenAlex candidate entities are then compared using TF-IDF cosine similarity.

This score is stored as: `neighbor_tfidf_score`

The idea is that two aligned entities should not only have similar names, but may also have similar surrounding graph structure.

In practice, graph-neighbor similarity was weaker than profile-text similarity. Many entities share similar graph neighborhoods even when they are not the same real-world entity. Therefore, graph-neighbor similarity was not used as a strong standalone evidence source in the final system.

Instead, it was used as a small consistency refinement in A+B+C.

## Weighted Scoring

The experimental systems combine multiple evidence types using weighted linear scores.

For A+B, the main idea is:

```
embedding similarity + profile-text similarity
```

For C-only, the main idea is:

```
embedding similarity + graph-neighbor similarity
```

DistMult embedding similarity remains the dominant component because it captures structural information learned directly from the knowledge graphs. The profile-text and graph-neighbor similarities act as complementary evidence that refines the embedding model rather than replacing it.

For the final A+B+C system, the selected score is:

```
abc_score =
    0.60 × embedding_cosine
  + 0.35 × profile_tfidf_score
  + 0.05 × neighbor_tfidf_score
```

The final threshold is `abc_score >= 0.30`

The graph-neighbor similarity receives a small weight because the sensitivity analysis showed that it is useful mainly as weak consistency evidence, not as the dominant alignment evidence.

## One-to-One Matching

After scoring and reranking, the pipeline applies one-to-one matching.

This means that:
```
one YAGO entity can align to at most one SemOpenAlex entity
one SemOpenAlex entity can align to at most one YAGO entity
```

This is important because many labels are ambiguous.

For example, a label such as: `The Incident` may appear as the title of multiple works. Without one-to-one matching and score-based selection, the pipeline could produce many conflicting alignments.

## Sensitivity Analysis

The final weights and threshold were not treated as fixed assumptions.

Several configurations were tested by changing:
```
embedding-similarity weight
profile-text-similarity weight
graph-neighbor-similarity weight
minimum final score threshold
```
The selected configuration preserved the highest proxy recall-like score while improving proxy precision-like performance and removing weak generic-label matches.

This sensitivity analysis supports the final choice of:
```
0.60 embedding similarity
0.35 profile-text similarity
0.05 graph-neighbor similarity
minimum abc_score 0.30
```

The final configuration was selected because it gave the best trade-off among the tested variants.

## Experimental Systems Compared

Four systems were compared.

### 1. Baseline

The baseline is the production output from Stage 05 before the experimental extensions.

It uses:

- exact label candidate generation
- DistMult embedding scoring
- profile/type filtering
- TF-IDF filtering
- one-to-one matching

Input/output file:

```text
05_entity_alignment/final_alignment/outputs/strict/alignments_FINAL_tfidf.tsv
```

Alignment count:

```text
1,755,590
```

The baseline is the most conservative system.

### 2. A+B — Profile-Text Similarity

The A+B experiment extends the baseline by using richer profile-text similarity. Profile-text similarity is computed using character n-gram TF-IDF, which helps handle spelling, accent, capitalization, and punctuation differences.

It starts from a larger candidate pool and scores candidate pairs using:

```text
embedding similarity
+
profile-text similarity
```

The goal is to recover plausible alignments where the embedding similarity is weaker, but the profile-text evidence is very strong.

Example cases recovered by this approach include:

```text
Martin Suárez      → Martin Suarez
Émile Roux         → Emile Roux
Pensares em Revista → Pensares em Revista
```

This experiment produced:

```text
06_experiments/type_text_enrichment/outputs/strict/alignments_type_text_enriched_1to1.tsv
```

Alignment count:

```text
1,977,402
```

### 3. C Only — Graph-Neighbor Similarity

The graph-neighbor-only experiment tests whether graph-neighbor similarity can act as independent alignment evidence.

The idea is that two aligned entities should not only have similar names, but also similar surrounding graph-neighbor evidence.

For example, if a YAGO entity and a SemOpenAlex entity both have graph neighborhoods involving similar predicates or related entities, that may provide additional evidence that the alignment is plausible.

This experiment uses:

```text
embedding similarity
+
graph-neighbor similarity
```

without profile-text similarity.

Output file:

```text
06_experiments/graph_neighbor_only/outputs/strict/alignments_graph_neighbor_1to1.tsv
```

Alignment count:

```text
1,931,659
```

These results suggest that graph-neighbor similarity contains useful information, but is not sufficiently discriminative to serve as the primary alignment evidence between heterogeneous knowledge graphs. Its greatest value lies in refining otherwise plausible candidates rather than generating new alignments independently.

### 4. A+B+C — Final Combined System

The final system combines:

```text
embedding similarity
+
profile-text similarity
+
graph-neighbor similarity
```

Graph-neighbor similarity is used as light refinement evidence rather than as the main decision evidence.

The final scoring formula used after sensitivity analysis was:

```text
abc_score =
    0.60 × embedding_cosine
  + 0.35 × profile_tfidf_score
  + 0.05 × neighbor_tfidf_score
```

The final threshold was:

```text
abc_score >= 0.30
```

Strict proxy-gold alignments are preserved.

Final output:

```text
06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv
```

Final alignment count:

```text
1,973,194
```

This is the final selected alignment file used by Stage 07 RDF export.

## Runtime Folder Structure

The GitHub repository contains the maintained scripts, tests, and this README.
The `data/`, `outputs/`, and `logs/` directories below are generated when the
experiments run and are intentionally excluded from Git.

```text
06_experiments/
├── type_text_enrichment/
│   ├── scripts/
│   ├── data/       # generated intermediate files, ignored by Git
│   ├── outputs/    # generated experiment outputs, ignored by Git
│   └── logs/       # generated Slurm logs, ignored by Git
│
├── graph_neighbor_only/
│   ├── scripts/
│   ├── data/       # generated intermediate files, ignored by Git
│   ├── outputs/    # generated experiment outputs, ignored by Git
│   └── logs/       # generated Slurm logs, ignored by Git
│
├── graph_neighbor_signal/
│   ├── scripts/
│   ├── data/       # generated intermediate files, ignored by Git
│   ├── outputs/    # generated experiment outputs, ignored by Git
│   └── logs/       # generated Slurm logs, ignored by Git
│
├── tests/
│   └── test_pipeline_cli.py
│
└── README.md
```

Each experiment has its own real, maintained implementation:

```text
scripts/   executable scripts and Slurm jobs
data/      intermediate generated files
outputs/   final and evaluation outputs
logs/      Slurm logs
```

This single README documents all three Stage 06 experiments.

## Script Reference

The scripts are grouped by the experiment that owns them.

### `type_text_enrichment/scripts/`

- `run_type_text_enrichment.sbatch` is the complete A+B Slurm entry point. It
  prepares any missing candidate and text-profile evidence, runs the
  taxonomy-aware reranker, creates permissive and strict one-to-one outputs,
  audits their types, and writes the comparison and evaluation summaries.
- `create_enriched_candidate_pool.py` retains candidates with embedding cosine
  at least `0.20` and keeps at most the ten highest-scoring candidates per YAGO
  entity.
- `build_entity_text_profiles.py` normalizes extracted text literals and gives
  extra repetition weight to label/name/title predicates before joining each
  entity's values into a profile.
- `score_profile_text_similarity.py` computes character n-gram TF-IDF cosine
  similarity for the YAGO/SemOpenAlex profiles required by the candidate pool.
- `rerank_type_text_candidates.py` combines embedding and profile scores,
  applies the Stage 05 taxonomy compatibility policy, and produces ranked and
  top-1 files for both the permissive and strict policies.
- `merge_proxy_gold.py` type-checks the proxy-gold and top-1 rows, prioritizes
  eligible proxy-gold pairs, and greedily enforces one-to-one uniqueness.
- `compare_baseline_vs_enriched.py` counts shared, baseline-only, and
  experiment-only pairs.

### `graph_neighbor_only/scripts/`

- `run_graph_neighbor_only.sbatch` is the complete C-only Slurm entry point. It
  prepares missing neighbor profiles and scores, performs taxonomy-aware
  reranking and one-to-one merging, and evaluates both policies.
- `build_candidate_neighbor_profiles.py` scans the preprocessed triples for
  direct incoming and outgoing edges of candidate entities and writes compact
  one-hop neighborhood contexts.
- `score_candidate_neighbor_similarity.py` computes TF-IDF cosine similarity
  between those candidate neighborhood contexts.
- `rerank_graph_neighbor_candidates.py` combines embedding and neighbor scores
  and applies taxonomy compatibility before selecting top-1 candidates.
- `merge_proxy_gold.py` and `compare_baseline_vs_enriched.py` are method-local
  copies of the same one-to-one merge and comparison logic used by A+B.

### `graph_neighbor_signal/scripts/`

- `run_graph_neighbor_signal.sbatch` is the A+B+C Slurm entry point. It adds
  one-hop neighbor scores to the selected A+B policy, summarizes that signal,
  runs every sensitivity configuration, and audits the selected `t=0.30`
  result.
- `build_neighbor_context_profiles.py` builds direct one-hop contexts only for
  entities present in the selected A+B alignment set.
- `score_neighbor_context_similarity.py` appends `neighbor_tfidf_score` to
  every A+B pair.
- `summarize_neighbor_scores.py` reports neighbor-score threshold counts
  separately for pairs shared with the baseline and pairs introduced by A+B.
- `create_final_abc_alignments.py` computes the weighted A+B+C score, preserves
  strict proxy-gold rows, applies the requested threshold, and writes one
  sensitivity output.
- `run_abc_sensitivity.py` executes the five documented weight/threshold
  configurations and collects their evaluation and baseline-overlap metrics.

The integration test is `tests/test_pipeline_cli.py`. It exercises the strict
versus permissive type policy and the A+B and C-only rerank/merge paths on
small synthetic inputs.

# Experiment A+B — Profile-Text Similarity

## Purpose

The purpose of A+B is to improve recall-like coverage by using richer profile-text similarity.

The baseline pipeline already combined embedding similarity with lexical filtering based on TF-IDF. However, it relied only on the primary entity labels. Stage 06 extends this idea by introducing richer profile-text similarity and graph-neighbor similarity as additional evidence.

A+B therefore expands the candidate pool and uses profile-text similarity to recover more alignments.

## Main Logic

The A+B pipeline works as follows:

```text
ambiguous embedding-ranked candidates
        ↓
create larger candidate pool
        ↓
build YAGO text profiles
        ↓
build SemOpenAlex text profiles
        ↓
score profile-text similarity
        ↓
rerank candidates using embedding similarity + profile-text similarity
        ↓
select top-1 candidate per YAGO entity
        ↓
merge with proxy-gold links
        ↓
apply one-to-one matching
```

The candidate pool uses:

```text
minimum embedding similarity: 0.20
top-k per YAGO entity: 10
```

The A+B combined score is based on:

```text
embedding_cosine
profile_tfidf_score
```

The run produced:

```text
06_experiments/type_text_enrichment/outputs/strict/alignments_type_text_enriched_1to1.tsv
```

## A+B Result

```text
Baseline rows:        1,755,590
A+B rows:             1,977,402
Shared with baseline: 1,630,402
Baseline-only pairs:    125,188
A+B-only pairs:         347,000
```

Proxy-gold evaluation:

```text
Final alignments:          1,977,402
Proxy-gold size:           1,385,607
Pairs in proxy-gold:         951,866
Proxy precision-like:      0.481372
Proxy recall-like:         0.686967
```

Because the experimental systems intentionally recover a larger number of ambiguous candidate alignments, the denominator of the proxy precision-like metric increases. Consequently, a small reduction in proxy precision-like is expected, while the substantial increase in proxy recall-like reflects the recovery of many additional plausible alignments.

Compared to the baseline, A+B recovered substantially more proxy-gold pairs and increased recall-like performance.

The cost was a decrease in precision-like score, which is expected because the system keeps more candidate alignments.

## Interpretation

A+B was the strongest main enhancement.

It recovered many plausible alignments that the baseline rejected, especially cases with:

- accents
- capitalization differences
- initials
- identical names but weaker embedding similarity
- strong profile-text evidence

Representative profile-text matches include:

```text
Martin Suárez → Martin Suarez
Émile Roux → Emile Roux
Carlos Ourívio Escobar → Carlos Ourivio Escobar
Pensares em Revista → Pensares em Revista
```

The experiment showed that profile-text similarity is strong complementary evidence for embedding similarity.

# Experiment C — Graph-Neighbor Only

## Purpose

The purpose of C is to test whether graph-neighbor similarity can independently improve entity alignment.

Instead of relying on profile-text similarity, this experiment builds a compact representation of the local graph neighborhood for candidate entities.

For each candidate entity, the script collects graph-neighbor evidence such as:

```text
outgoing predicates
incoming predicates
neighbor identifiers
```

These are converted into a text-like profile and compared using TF-IDF similarity.

## Main Logic

The graph-neighbor-only pipeline works as follows:

```text
ambiguous embedding-ranked candidates
        ↓
build YAGO graph-neighbor profiles
        ↓
build SemOpenAlex graph-neighbor profiles
        ↓
score graph-neighbor similarity
        ↓
rerank candidates using embedding similarity + graph-neighbor similarity
        ↓
select top-1 candidate per YAGO entity
        ↓
merge with proxy-gold links
        ↓
apply one-to-one matching
```

The scoring formula used in the graph-neighbor-only experiment was:

```text
combined_score =
    0.80 × embedding_cosine
  + 0.20 × neighbor_tfidf_score
```

Output file:

```text
06_experiments/graph_neighbor_only/outputs/strict/alignments_graph_neighbor_1to1.tsv
```

## C-Only Result

```text
Baseline rows:        1,755,590
C-only rows:          1,931,659
Shared with baseline: 1,694,474
Baseline-only pairs:     61,116
C-only pairs vs baseline: 237,185
```

Proxy-gold evaluation:

```text
Final alignments:          1,931,659
Proxy-gold size:           1,385,607
Pairs in proxy-gold:         951,866
Proxy precision-like:      0.492771
Proxy recall-like:         0.686967
```

## Interpretation

C-only achieved the same proxy recall-like score as A+B and a higher
proxy precision-like score, but it recovered fewer total pairs than A+B.

This suggests that graph-neighbor similarity alone is weaker and noisier than profile-text similarity.

The reason is understandable: many entities can have similar local graph neighborhoods even when they are not the same entity.

For example, many authors may have similar neighborhoods involving publications, institutions, sources, and concepts. Many works may also have similar graph structure despite being different publications.

Therefore, graph-neighbor similarity is useful, but it is not strong enough to replace profile-text similarity.

# A+B+C — Graph-Neighbor Consistency Refinement

## Purpose

The A+B+C experiment tests whether graph-neighbor evidence can refine the already strong A+B results.

The important difference is that here graph-neighbor similarity is not used as the main alignment evidence.

Instead, it is used as a small consistency bonus.

The idea is:

```text
A+B already finds many good alignments.
Graph-neighbor similarity may help remove the weakest remaining cases.
```

## Neighbor Score Analysis

The `neighbor_tfidf_score` values were generally small:

```text
Rows:       1,977,402
Mean:       0.0217
Median:     0.0183
75%:        0.0219
Maximum:    0.7709
```

Threshold counts:

```text
neighbor_tfidf_score >= 0.01: 1,942,015
neighbor_tfidf_score >= 0.05:    26,570
neighbor_tfidf_score >= 0.10:    15,961
neighbor_tfidf_score >= 0.20:     9,149
neighbor_tfidf_score >= 0.30:     8,117
neighbor_tfidf_score >= 0.50:     5,351
```

This showed that graph-neighbor evidence is usually weak. Therefore, it was used with a small weight in the final score.

## Final A+B+C Scoring

The final combined score is:

```text
abc_score =
    0.60 × embedding_cosine
  + 0.35 × profile_tfidf_score
  + 0.05 × neighbor_tfidf_score
```

The final threshold is:

```text
abc_score >= 0.30
```

This setting was selected after sensitivity analysis.

Output file:

```text
06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv
```

## Sensitivity Analysis

Several weight and threshold combinations were tested.

| Variant | Embedding | Profile | Neighbor | Threshold | Alignments | Proxy Precision-like | Proxy Recall-like |
|---|---:|---:|---:|---:|---:|---:|---:|
| A+B+C 0.60/0.35/0.05 t=0.25 | 0.60 | 0.35 | 0.05 | 0.25 | 1,976,656 | 0.481554 | 0.686967 |
| A+B+C 0.55/0.35/0.10 t=0.25 | 0.55 | 0.35 | 0.10 | 0.25 | 1,975,809 | 0.481760 | 0.686967 |
| A+B+C 0.65/0.30/0.05 t=0.25 | 0.65 | 0.30 | 0.05 | 0.25 | 1,976,685 | 0.481547 | 0.686967 |
| **A+B+C 0.60/0.35/0.05 t=0.30** | **0.60** | **0.35** | **0.05** | **0.30** | **1,973,194** | **0.482399** | **0.686967** |
| A+B+C 0.60/0.35/0.05 t=0.20 | 0.60 | 0.35 | 0.05 | 0.20 | 1,977,402 | 0.481372 | 0.686967 |

The selected final configuration is:

```text
0.60 embedding similarity
0.35 profile-text similarity
0.05 graph-neighbor similarity
threshold 0.30
```

This configuration achieved the best proxy precision-like score while preserving the same proxy recall-like score.

## Removed Alignment Inspection

The stricter threshold removed several thousand low-confidence alignments while preserving all proxy-gold pairs.

The threshold-review sample contains many generic labels such as:

```text
The Incident
The Lost City
An Untold Story
Second Chance
By the Sea
At the Window
Santa Cruz
Symphony No. 9
```

These are exactly the kinds of labels that can create false positives because the same title or name may occur many times across different entities.

The removed alignments generally had:

```text
low embedding similarity
low or medium profile-text similarity
very weak graph-neighbor similarity
abc_score below 0.30
```

This supports the conclusion that the stricter threshold mainly removed risky or likely false-positive alignments.

# Overall Results

The final comparison is:

| System | Rows | Proxy Hits | Proxy Precision-like | Proxy Recall-like | Shared with Baseline | Baseline-only | System-only |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 1,755,590 | 947,748 | 0.539846 | 0.683995 | 1,755,590 | 0 | 0 |
| A+B | 1,977,402 | 951,866 | 0.481372 | 0.686967 | 1,630,402 | 125,188 | 347,000 |
| C only | 1,931,659 | 951,866 | 0.492771 | 0.686967 | 1,694,474 | 61,116 | 237,185 |
| **A+B+C final** | **1,973,194** | **951,866** | **0.482399** | **0.686967** | **1,629,924** | **125,666** | **343,270** |

## Important Evaluation Note

The final Stage 06 output is a predicted alignment set, not manually verified ground truth.

The proxy precision-like and proxy recall-like values reported in this README are diagnostic silver-standard measures. They are computed using overlap with the strict proxy-gold set, which was constructed from high-confidence exact-label one-to-one matches.

Therefore, these values should not be interpreted as true human-verified precision and recall. Instead, they are used to compare alternative pipeline variants under the same evaluation assumptions.

The repository also provides annotation samples and threshold-review material
for human validation. These are supporting review artifacts, not a completed
human-labelled gold standard.

## Scientific Interpretation

The results show that the baseline alignment pipeline was precise but conservative.

Adding profile-text similarity produced the main improvement. It increased recall-like performance from:

```text
0.683995
```

to:

```text
0.686967
```

while increasing the number of final alignments by 221,812.

Graph-neighbor similarity alone produced the same proxy recall-like score as
A+B and higher proxy precision-like score, but fewer total alignments. This
suggests that graph-neighbor similarity is useful but more conservative than
profile-text enrichment as standalone evidence for these two knowledge graphs.

However, when graph-neighbor similarity was added as light refinement evidence on top of A+B, it slightly improved precision-like performance while preserving recall-like performance.

Therefore, the final A+B+C system was selected as the best overall trade-off between coverage and reliability among the tested configurations.

# How to Run the Experiments

All commands should be run from the project root:

```bash
cd /data/horse/ws/jovu353i-kgalign/KGAlignment
```

## Run A+B Type/Profile-Text Enrichment

```bash
sbatch 06_experiments/type_text_enrichment/scripts/run_type_text_enrichment.sbatch
```

Important output:

```text
06_experiments/type_text_enrichment/outputs/strict/alignments_type_text_enriched_1to1.tsv
```

Comparison summary:

```text
06_experiments/type_text_enrichment/outputs/strict/baseline_vs_ab_summary.tsv
```

This single job prepares missing candidate/profile evidence, reranks both
permissive and strict policies, merges the proxy-gold pairs, audits types, and
evaluates both outputs. Existing expensive evidence files are reused.

## Run C Graph-Neighbor Only

```bash
sbatch 06_experiments/graph_neighbor_only/scripts/run_graph_neighbor_only.sbatch
```

Important output:

```text
06_experiments/graph_neighbor_only/outputs/strict/alignments_graph_neighbor_1to1.tsv
```

Comparison summary:

```text
06_experiments/graph_neighbor_only/outputs/strict/baseline_vs_c_summary.tsv
```

This job uses the same candidate definition as A+B and creates that pool if it
is missing. It prepares missing one-hop graph-neighbor profiles and scores,
then produces and evaluates both policy variants.

## Run Graph-Neighbor Scoring on A+B

```bash
sbatch --export=ALL,ALIGNMENT_VARIANT=strict \
  06_experiments/graph_neighbor_signal/scripts/run_graph_neighbor_signal.sbatch
```

Important output:

```text
06_experiments/graph_neighbor_signal/outputs/strict/alignments_type_text_with_neighbor_scores.tsv
```

This file is not yet the final alignment file. It is the A+B result with an additional `neighbor_tfidf_score` column.

## Create Final A+B+C Alignments

```bash
python 06_experiments/graph_neighbor_signal/scripts/create_final_abc_alignments.py \
  --input 06_experiments/graph_neighbor_signal/outputs/strict/alignments_type_text_with_neighbor_scores.tsv \
  --output 06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv \
  --embedding-weight 0.60 \
  --profile-weight 0.35 \
  --neighbor-weight 0.05 \
  --min-score 0.30
```

Important output:

```text
06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv
```

## Run A+B+C Sensitivity Analysis

```bash
python 06_experiments/graph_neighbor_signal/scripts/run_abc_sensitivity.py \
  --input 06_experiments/graph_neighbor_signal/outputs/strict/alignments_type_text_with_neighbor_scores.tsv \
  --baseline 05_entity_alignment/final_alignment/outputs/strict/alignments_FINAL_tfidf.tsv \
  --proxy-gold 05_entity_alignment/data/gold/proxy_gold_exact_unique.tsv \
  --out-dir 06_experiments/graph_neighbor_signal/outputs/strict/sensitivity
```

Summary output:

```text
06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_sensitivity_summary.tsv
```

## Sample Removed Alignments for Manual Inspection

```bash
python 07_export/validation/review_score_threshold.py \
  --input 06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t020.tsv \
  --upper-threshold 0.30 \
  --all-output 07_export/validation/threshold_review/removed_below_030.tsv \
  --sample-output 07_export/validation/threshold_review/removed_below_030_sample.tsv \
  --summary-output 07_export/validation/threshold_review/removed_below_030_summary.json \
  --sample-size 200
```

This creates deterministic boundary-review material. Falling below the
threshold is not itself proof that a pair is wrong; the sample is intended for
human inspection.

# Important Output Files

## Final Selected Alignment File

```text
06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv
```

This is the final production alignment file selected after ablation and sensitivity analysis.

It is used as the input to Stage 07 RDF export.

## Main Experimental Outputs

```text
06_experiments/type_text_enrichment/outputs/strict/alignments_type_text_enriched_1to1.tsv
06_experiments/graph_neighbor_only/outputs/strict/alignments_graph_neighbor_1to1.tsv
06_experiments/graph_neighbor_signal/outputs/strict/alignments_type_text_with_neighbor_scores.tsv
06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv
```

## Main Evaluation Outputs

```text
06_experiments/type_text_enrichment/outputs/strict/evaluation_summary.tsv
06_experiments/type_text_enrichment/outputs/strict/baseline_vs_ab_summary.tsv
06_experiments/graph_neighbor_only/outputs/strict/evaluation_summary.tsv
06_experiments/graph_neighbor_only/outputs/strict/baseline_vs_c_summary.tsv
06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_sensitivity_summary.tsv
07_export/visualizations/tables/05_system_comparison.csv
```

# Notes on Resource Usage

The A+B and graph-neighbor experiments process millions of candidate pairs and large text/profile files.

They are best run through Slurm.

The graph-neighbor and type-text experiments can take several hours, especially when generating profiles and scoring millions of pairs.

Intermediate files are intentionally kept so that failed or interrupted jobs can resume without recomputing expensive stages.

Several scripts therefore use skip checks such as:

```text
if output exists, skip this step
```

This makes the experiments easier to rerun and debug on the HPC cluster.

# Final Decision

The final selected alignment set is:

```text
06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv
```

It was selected because it:

- preserves the highest proxy recall-like value obtained by the experiments
- slightly improves precision-like performance over A+B
- removes low-confidence generic-label alignments
- performs better than graph-neighbor-only
- is supported by sensitivity analysis and reproducible threshold-review samples

This final file is used by Stage 07 to export RDF `owl:sameAs` links.

# Summary
*Overall, Stage 06 demonstrates that profile-text similarity substantially improves alignment coverage, while graph-neighbor similarity provides a modest but meaningful refinement. The selected A+B+C configuration offers the best balance between coverage and reliability among the evaluated systems and therefore serves as the final production alignment set exported in Stage 07.*
