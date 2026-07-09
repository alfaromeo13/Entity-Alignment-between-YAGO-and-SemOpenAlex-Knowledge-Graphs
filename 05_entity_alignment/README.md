# YAGO–SemOpenAlex Entity Alignment

This folder contains the core entity alignment pipeline between YAGO and SemOpenAlex.

The goal of this stage is to create a large, high-confidence baseline set of one-to-one predicted alignments between entities in the two knowledge graphs. The Stage 05 output is then refined and compared in `06_experiments/`, where the final export candidate is selected.

This stage is precision-oriented. It does not try to force every YAGO entity to match something in SemOpenAlex. That would not be realistic, because YAGO and SemOpenAlex have very different scopes. YAGO is a broad general-purpose knowledge graph, while SemOpenAlex is a scholarly knowledge graph focused on authors, works, institutions, sources, publishers, funders, concepts, and related research entities.

Instead of doing expensive all-versus-all comparison, the pipeline uses a staged approach:

```text
Labels
  ↓
Normalized exact-label candidates
  ↓
Strict proxy-gold + ambiguous candidates
  ↓
Embedding-based reranking
  ↓
Threshold filtering
  ↓
One-to-one matching
  ↓
YAGO predicate-profile validation
  ↓
SemOpenAlex type/profile filtering
  ↓
TF-IDF lexical refinement
  ↓
Stage 05 TF-IDF baseline alignments
  ↓
Stage 06 experimental refinement and final selection
```

The main Stage 05 baseline file is:

```text
05_entity_alignment/final_alignment/outputs/strict/alignments_FINAL_tfidf.tsv
```

It contains:

```text
1,755,591 lines including header
1,755,590 final alignments
```

Stage 05 baseline SemOpenAlex type distribution:

```text
author         1,546,286
work             172,389
institution       26,490
source             7,291
publisher          1,322
funder               925
concept              724
keyword              160
subfield               2
topic                  1
```

The final alignment set used by the export stage is selected in Stage 06:

```text
06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv
```

That file contains 1,973,194 one-to-one alignments after profile-text enrichment, graph-neighbor scoring, ABC score combination, and threshold sensitivity analysis.

## Runtime Folder Structure

The GitHub repository contains the maintained scripts, tests, and documentation.
The `data/`, `outputs/`, and `logs/` directories below are created by the
alignment jobs and are intentionally excluded from Git because they contain
large generated artifacts.

```text
05_entity_alignment/
├── data/              # generated intermediate alignment data, ignored by Git
│   ├── candidates/
│   ├── gold/
│   └── labels/
│
├── outputs/           # generated alignment outputs and summaries, ignored by Git
│   ├── evaluation/
│   ├── final/
│   └── rankings/
│
├── scripts/
├── logs/              # generated Slurm logs, ignored by Git
└── README.md
```

### `data/`

This folder contains intermediate data produced during the alignment process.

```text
data/labels/
```

Stores extracted and normalized labels for YAGO and SemOpenAlex.

```text
data/candidates/
```

Stores exact-label candidate pairs, filtered candidates, ambiguous candidates, and candidates enriched with integer embedding IDs.

```text
data/gold/
```

Stores the strict proxy-gold alignment set created from high-confidence one-to-one exact-label matches.

### `outputs/`

This folder contains alignment outputs, ranking outputs, final alignments, and evaluation summaries.

```text
outputs/rankings/
```

Stores ranked ambiguous candidates after embedding-based scoring.

```text
outputs/final/
```

Stores the final alignment files and important intermediate final-stage outputs.

```text
outputs/evaluation/
```

Stores evaluation summaries, type distributions, source distributions, profile filtering summaries, and manual inspection samples.

### `scripts/`

This folder contains the Python scripts and Slurm wrappers used to run the full alignment pipeline.

## Key Script Logic

Several scripts in this stage contain alignment decisions rather than only file conversion or job orchestration.

`prepare_entity_labels.py` selects one representative label per entity from the raw text literals. It filters out mostly non-Latin text and prefers shorter clean labels, which usually work better for names, titles, and exact-label blocking.

`normalize_labels.py` defines the canonical label normalization used for blocking. It applies Unicode normalization, ASCII folding, lowercasing, punctuation removal, and whitespace cleanup before exact-label matching.

`filter_exact_label_candidates.py` removes noisy exact-label matches before scoring. It filters very frequent labels, labels that are too short, labels with too few tokens, numeric-only labels, and a curated set of generic labels such as `unknown`, `journal`, `city`, or `university`.

`score_and_split_exact_candidates.py` assigns candidate confidence tiers. Strict one-to-one exact-label matches become `strict_proxy_gold`, while ambiguous labels are kept for embedding-based reranking.

`score_candidates_with_pbg_embeddings.py` loads partitioned PyTorch-BigGraph entity embeddings and computes cosine similarity for ambiguous YAGO-SemOpenAlex candidate pairs. It also writes the top-ranked SemOpenAlex candidate for each YAGO entity.

`threshold_sweep_alignments.py` evaluates candidate counts across embedding thresholds and applies an early compatibility heuristic based on SemOpenAlex URI type and whether the YAGO label looks person-like.

`filter_and_merge_alignments.py` combines strict proxy-gold alignments with accepted embedding top-1 predictions. It applies the selected embedding threshold and an early type-safety check before producing the first merged alignment file.

`profile_final_alignments_predicates.py` enriches alignments with coarse YAGO profile categories by scanning YAGO predicate patterns. These profiles distinguish person-like, creative-work-like, organization-like, place-like, and event-like entities.

`filter_by_yago_profile_type.py` applies schema-aware filtering after predicate profiling. It rejects profile/type pairs that were found to be risky, such as place-like YAGO entities matched to SemOpenAlex authors.

`merge_tfidf.py` applies the Stage 05 TF-IDF baseline keep rule. A row is retained if it has strong embedding support, or if it has medium embedding support plus high TF-IDF lexical similarity. Later experiments in `06_experiments/` build on this baseline and compare it against profile-text and graph-neighbor refinements.

## Inputs from Previous Stages

This stage depends on outputs from earlier parts of the project.

### Textual input from preprocessing

```text
02_preprocessed/yago/entity_text_raw.tsv
02_preprocessed/semopenalex_clean/entity_text_raw.tsv
```

These files contain textual literals extracted during RDF preprocessing, such as labels, names, titles, descriptions, comments, and alternative names.

### Integer dictionaries from integer encoding

```text
03_integer_encoding/yago/entities.dict
03_integer_encoding/semopenalex/entities.dict
```

These dictionaries map RDF entity URIs to integer IDs. They are needed because PyTorch-BigGraph embeddings are indexed by integer entity IDs, not by URI strings.

### Trained graph embeddings

```text
04_embeddings/output/yago/
04_embeddings/output/semopenalex/
```

The entity alignment pipeline uses the trained graph embeddings as a structural signal for reranking ambiguous candidates. In the final pipeline, DistMult-based embedding scores were used for candidate reranking.

## Execution Order

### 1. Prepare Entity Labels

```bash
cd /data/horse/ws/jovu353i-kgalign/KGAlignment

sbatch 05_entity_alignment/scripts/prepare_labels.sbatch
```

This step reads the raw text literal files from preprocessing and creates one representative label per entity.

Input:

```text
02_preprocessed/yago/entity_text_raw.tsv
02_preprocessed/semopenalex_clean/entity_text_raw.tsv
```

Outputs:

```text
05_entity_alignment/data/labels/yago_labels.tsv
05_entity_alignment/data/labels/semopenalex_labels.tsv
```

The purpose of this step is to transform raw textual literals into a simpler label table that can be used for candidate generation.

### 2. Normalize Labels

```bash
sbatch 05_entity_alignment/scripts/normalize_labels.sbatch
```

This step normalizes labels so that small surface-form differences do not prevent matching.

Typical normalization includes:

```text
lowercasing
punctuation cleanup
whitespace normalization
basic text cleanup
```

Example:

```text
"University of Oxford"
→
"university of oxford"
```

Outputs:

```text
05_entity_alignment/data/labels/yago_labels_norm.tsv
05_entity_alignment/data/labels/semopenalex_labels_norm.tsv
```

Normalized labels are the basis for exact-label candidate generation.

### 3. Generate Exact-Label Candidates

```bash
sbatch 05_entity_alignment/scripts/generate_exact_candidates.sbatch
```

This step joins YAGO and SemOpenAlex entities by identical normalized labels.

Example:

```text
YAGO label:        albert einstein
SemOpenAlex label: albert einstein
```

This creates a candidate pair.

Output:

```text
05_entity_alignment/data/candidates/exact_label_candidates.tsv
```

This is a blocking step. Its purpose is to reduce the search space from impossible all-versus-all matching to a much smaller set of plausible candidate pairs.

### 4. Filter Exact-Label Candidates

```bash
sbatch 05_entity_alignment/scripts/filter_exact_candidates.sbatch
```

Some normalized labels are too generic or too frequent. They create too many candidate pairs and are not useful for high-confidence alignment.

Examples of problematic labels:

```text
introduction
editorial
john smith
unknown
```

This step removes or limits overly ambiguous label groups.

Outputs:

```text
05_entity_alignment/data/candidates/exact_label_candidates_filtered.tsv
05_entity_alignment/data/candidates/exact_label_candidates_filtered_summary.tsv
05_entity_alignment/data/candidates/exact_label_candidates_filtered_yago_distribution.tsv
```

This improves scalability and reduces noisy candidate explosions.

### 5. Summarize Exact Candidates

```bash
sbatch 05_entity_alignment/scripts/summarize_exact_candidates.sbatch
```

This step produces statistics about the candidate set.

Output:

```text
05_entity_alignment/data/candidates/exact_label_candidate_stats.tsv
```

The summary helps inspect candidate counts, ambiguity levels, and the effect of candidate filtering.

### 6. Split Candidates into Proxy-Gold and Ambiguous Sets

```bash
sbatch 05_entity_alignment/scripts/score_and_split_exact_candidates.sbatch
```

This step separates exact-label candidates into two groups.

*Strict proxy-gold* - If a normalized label maps to exactly one YAGO entity and exactly one SemOpenAlex entity, the pair is treated as a high-confidence exact match.

Output:

```text
05_entity_alignment/data/gold/proxy_gold_exact_unique.tsv
```

This is called proxy-gold because it is not manually verified ground truth. It is a strict silver-standard alignment set derived from exact normalized labels under strong one-to-one constraints.

*Ambiguous candidates* - If a label maps to multiple possible entities, it is not accepted directly. Instead, it is kept for embedding-based reranking.

Output:

```text
05_entity_alignment/data/candidates/exact_label_candidates_ambiguous.tsv
```

This distinction is important because exact-label matching alone is not enough. Many entities share the same name, especially people, works, and generic scholarly terms.

### 7. Attach Integer IDs to Ambiguous Candidates

```bash
sbatch 05_entity_alignment/scripts/add_ids_to_candidates.sbatch
```

PyTorch-BigGraph embeddings are stored by integer entity ID. This step maps YAGO and SemOpenAlex entity URIs in the ambiguous candidate file to their corresponding integer IDs.

Inputs:

```text
05_entity_alignment/data/candidates/exact_label_candidates_ambiguous.tsv
03_integer_encoding/yago/entities.dict
03_integer_encoding/semopenalex/entities.dict
```

Output:

```text
05_entity_alignment/data/candidates/exact_label_candidates_ambiguous_with_ids.tsv
```

This file can now be used for embedding-based scoring.

### 8. Score Ambiguous Candidates with PBG Embeddings

```bash
sbatch 05_entity_alignment/scripts/score_candidates_with_pbg_embeddings.sbatch
```

This step scores ambiguous candidate pairs using graph embeddings trained in the previous stage.

For each candidate pair:

```text
YAGO entity ↔ SemOpenAlex entity
```

the script loads the corresponding embedding vectors and computes an embedding similarity score.

Output:

```text
05_entity_alignment/outputs/scores/ambiguous_distmult_embedding_scored.tsv
```

This gives a structural ranking signal for candidates that have the same or similar textual label but may refer to different entities.

### 9. Rank Ambiguous Candidates

The embedding-scored candidates are reduced to the best candidate per YAGO entity. This top-1 ranking is produced by the previous `score_candidates_with_pbg_embeddings.sbatch` step.

```bash
sbatch 05_entity_alignment/scripts/score_candidates_with_pbg_embeddings.sbatch
```

The same job writes both the full scored candidate table and the top-1 ranked candidate table.

Output:

```text
05_entity_alignment/outputs/rankings/ambiguous_distmult_top1.tsv
```

This file stores the top-ranked SemOpenAlex candidate for each ambiguous YAGO entity.

The goal is not to use embeddings for unrestricted all-versus-all matching. Instead, embeddings are used only after textual blocking has already produced a controlled candidate set.

### 10. Threshold Sweep

```bash
sbatch 05_entity_alignment/scripts/threshold_sweep_alignments.sbatch
```

This step tests different embedding similarity thresholds.

Output:

```text
05_entity_alignment/outputs/final/threshold_sweep_summary.tsv
```

The selected threshold was:

```text
embedding_cosine >= 0.30
```

This threshold was used as the first acceptance boundary for embedding-based candidates before later filtering stages.

The threshold is intentionally not the only quality control step. It is followed by one-to-one matching, SemOpenAlex type extraction, YAGO predicate-profile validation, profile/type filtering, and TF-IDF refinement.

### 11. Filter and Merge Alignments

```bash
sbatch 05_entity_alignment/scripts/filter_and_merge_alignments.sbatch
```

This step merges two alignment sources:

```text
strict proxy-gold exact matches
embedding-based top-1 predictions
```

It also applies an early SemOpenAlex type check.

Output:

```text
05_entity_alignment/outputs/final/alignments_threshold030_typefiltered.tsv
```

This file contains the first combined alignment set after thresholding and early type filtering.

### 12. Enforce One-to-One Matching

```bash
sbatch 05_entity_alignment/scripts/one_to_one_matching.sbatch
```

This step enforces a global one-to-one constraint.

After this step:

```text
each YAGO entity appears at most once
each SemOpenAlex entity appears at most once
```

Output:

```text
05_entity_alignment/outputs/final/alignments_threshold030_typefiltered_1to1.tsv
```

One-to-one matching is important because the final alignment file is intended to represent direct entity correspondences, not many-to-many candidate links.

### 13. YAGO Predicate-Profile Enrichment

```bash
sbatch 05_entity_alignment/scripts/profile_final_alignments_predicates.sbatch
```
This script scans YAGO predicates for aligned YAGO entities and assigns coarse profile categories based on observed predicate patterns.

Examples:

```text
person_like:
birthDate, deathDate, gender, birthPlace, deathPlace

creative_work_like:
author, datePublished, inLanguage, about

organization_like:
founder, foundingDate, member, parentOrganization, worksFor, affiliation

place_like:
geo, latitude, longitude, location, address, containedInPlace

event_like:
startDate, endDate, organizer
```

Output:

```text
05_entity_alignment/outputs/final/alignments_threshold030_1to1_predicate_profile.tsv
```

This step made the validation more robust because it used actual YAGO predicate patterns instead of relying on a single explicit type field.

### 14. SemOpenAlex Type Correction and Profile-Based Filtering

```bash
sbatch 05_entity_alignment/scripts/filter_by_yago_profile_type.sbatch
```

This step targets schema-incompatible alignments, especially cases where place-like or work-like YAGO entities are matched to SemOpenAlex authors.

Examples of suspicious pairs:

```text
place_like → author
person_like → work
creative_work_like → author
organization_like → author
organization_like → work
event_like → author
```
The SemOpenAlex type extractor recognizes the URI classes needed for this schema-aware filtering.

Final recognized SemOpenAlex types include:

```text
author
work
institution
source
publisher
funder
concept
keyword
topic
field
subfield
domain
venue
```

Output:

```text
05_entity_alignment/outputs/final/alignments_threshold030_1to1_profilefiltered.tsv
```

Rejected alignments are stored separately:

```text
05_entity_alignment/outputs/final/alignments_threshold030_1to1_profilefiltered_rejected.tsv
```

This step made the final alignment set more schema-aware.

### 15. Prepare TF-IDF Input

```bash
python 05_entity_alignment/scripts/prepare_tfidf_input.py \
  --input 05_entity_alignment/outputs/final/alignments_threshold030_1to1_profilefiltered.tsv \
  --output 05_entity_alignment/outputs/final/tfidf_input.tsv
```

This step prepares the input for TF-IDF refinement from the profile-filtered alignment file.

The TF-IDF stage is not applied to the full graph and not to all possible YAGO–SemOpenAlex pairs. It is applied only to selected paired labels from the already filtered candidate set.

### 16. TF-IDF Reranking / Lexical Refinement

```bash
sbatch 05_entity_alignment/scripts/tfidf_rerank_safe.sbatch
```

This step computes lexical TF-IDF similarity between paired YAGO and SemOpenAlex labels.
The implementation uses row-wise cosine similarity:

```text
YAGO label 1 ↔ SemOpenAlex label 1
YAGO label 2 ↔ SemOpenAlex label 2
YAGO label 3 ↔ SemOpenAlex label 3
...
```

The TF-IDF normalization includes:

```text
Unicode normalization
accent stripping
lowercasing
punctuation removal
whitespace cleanup
```

Examples:

```text
Höll      → holl
O’Neill   → oneill
Zha-Jun   → zha jun
Tōru      → toru
Čelig     → celig
```

Output:

```text
05_entity_alignment/outputs/final/tfidf_scores.tsv
```

If this intermediate file is not present, it can be regenerated from `tfidf_input.tsv` using the Slurm wrapper above.

### 17. Merge TF-IDF Scores and Produce Final File

```bash
sbatch 05_entity_alignment/scripts/merge_tfidf.sbatch
```

This step merges TF-IDF scores back into the profile-filtered alignment file and applies the Stage 05 baseline production rule.

Final keep rule:

```text
keep if embedding_cosine >= 0.40
```

or:

```text
keep if tfidf_score >= 0.85 and embedding_cosine >= 0.30
```

This means that a candidate can be retained in two ways:

1. it has strong graph embedding support
2. it has medium graph embedding support and very strong lexical support

Stage 05 baseline output:

```text
05_entity_alignment/final_alignment/outputs/strict/alignments_FINAL_tfidf.tsv
```

This file is the baseline alignment set for later experimental refinement. It is no longer the file exported directly; the export stage uses the Stage 06 selected candidate.

In the final Stage 05 output, the TF-IDF keep rule does not remove additional rows because all embedding-based rows that reach this stage have `tfidf_score >= 0.85` after the previous filtering stages. Therefore, the Stage 05 baseline file has the same row count as `alignments_threshold030_1to1_profilefiltered.tsv`.

### 18. Evaluate Final Alignments

```bash
sbatch 05_entity_alignment/scripts/evaluate_final_alignments.sbatch
```

This step produces final evaluation and inspection summaries.

Outputs include:

```text
05_entity_alignment/outputs/evaluation/final_alignment_summary.tsv
05_entity_alignment/outputs/evaluation/final_alignment_source_distribution.tsv
05_entity_alignment/outputs/evaluation/final_alignment_type_distribution.tsv
05_entity_alignment/outputs/evaluation/final_alignment_yago_semopenalex_type_pairs.tsv
05_entity_alignment/outputs/evaluation/profile_type_filter_summary.tsv
05_entity_alignment/outputs/evaluation/yago_profile_semopenalex_type_summary.tsv
05_entity_alignment/outputs/evaluation/yago_predicate_semopenalex_type_summary.tsv
05_entity_alignment/outputs/evaluation/yago_type_map_for_final_alignments.tsv
```


Manual inspection samples can be regenerated from the Stage 05 baseline file using `sample_final_alignments_for_manual_check.py`.

```bash
python 05_entity_alignment/scripts/sample_final_alignments_for_manual_check.py \
  --input 05_entity_alignment/final_alignment/outputs/strict/alignments_FINAL_tfidf.tsv \
  --out-dir 05_entity_alignment/outputs/evaluation/manual_checks_final
```

The generated files are intended for qualitative inspection of random alignments, embedding-derived alignments, low-score embedding cases, and type-specific samples.
These files help inspect both high-confidence and potentially risky alignments.

### Important Stage 05 Outputs

The most important Stage 05 baseline file is:

```text
05_entity_alignment/final_alignment/outputs/strict/alignments_FINAL_tfidf.tsv
```

Important final-stage outputs:

```text
05_entity_alignment/outputs/final/alignments_threshold030_1to1_profilefiltered.tsv
05_entity_alignment/outputs/final/alignments_threshold030_1to1_profilefiltered_rejected.tsv
05_entity_alignment/outputs/final/alignments_threshold030_1to1_predicate_profile.tsv
05_entity_alignment/outputs/final/threshold_sweep_summary.tsv
```

These are useful for debugging, explaining, and reproducing the final alignment decision.

The Stage 05 baseline alignment file contains:

```text
1,755,590 final alignments
```

Stage 05 baseline SemOpenAlex type distribution:

```text
author         1,546,286
work             172,389
institution       26,490
source             7,291
publisher          1,322
funder               925
concept              724
keyword              160
subfield               2
topic                  1
```

## Interpretation of the Result

The Stage 05 result is a high-confidence predicted baseline alignment set, not manually verified ground truth. It should be interpreted together with the Stage 06 experiments, which add text-profile and graph-neighbor signals before selecting the final export candidate.

The largest aligned category is `author`, which is expected because both YAGO and SemOpenAlex contain many person entities, and names are often the strongest cross-graph signal.

The second-largest category is `work`, followed by institutions and sources.
Publishers, funders, concepts, and keywords form smaller aligned groups.

The Stage 05 alignment count is realistic because YAGO and SemOpenAlex do not have complete overlap. YAGO is broad and general-purpose, while SemOpenAlex is scholarly. Therefore, the real overlap is concentrated mainly in people, publications, institutions, sources, publishers, funders, keywords, and concepts.

The Stage 05 file should be interpreted as:

```text
high-confidence predicted alignments
```

not as:

```text
perfect complete ground truth
```

Some false positives may still exist, especially for common names, same-name authors, weak type information, and entities with very similar surface forms. However, the pipeline includes several safeguards:

```text
exact-label blocking
ambiguity filtering
strict proxy-gold construction
embedding-based reranking
threshold selection
one-to-one matching
SemOpenAlex URI type extraction
YAGO predicate-profile validation
profile/type filtering
TF-IDF lexical refinement
profile-text enrichment in Stage 06
graph-neighbor refinement in Stage 06
ABC weighted score selection in Stage 06
```

## Why This Pipeline Is Scalable

The pipeline avoids full all-versus-all matching.

A naive approach would compare every YAGO entity with every SemOpenAlex entity, which is infeasible at this scale.

Instead, the pipeline uses blocking and staged refinement:

```text
1. generate candidates only from normalized label overlap
2. accept only strict one-to-one exact matches directly
3. rerank ambiguous candidates with embeddings
4. apply threshold and type checks
5. enforce one-to-one matching
6. validate with YAGO predicate profiles
7. refine borderline cases with TF-IDF
```

This makes the approach scalable while still using multiple signals.

## Role in the Full Project

This stage is the main entity alignment stage of the thesis.

Previous stages produced:

```text
01_raw/              raw RDF dumps
02_preprocessed/     cleaned structural triples and text literals
03_integer_encoding/ integer ID datasets
04_embeddings/       graph embeddings
```

This stage uses those outputs to produce the Stage 05 baseline:

```text
05_entity_alignment/final_alignment/outputs/strict/alignments_FINAL_tfidf.tsv
```

Stage 06 then uses that baseline and the candidate-level outputs from this stage to produce the final selected alignment file:

```text
06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv
```

## Summary

*This stage produces the Stage 05 YAGO–SemOpenAlex baseline alignment set. The pipeline starts from normalized textual labels, constructs exact-label candidates, separates strict proxy-gold matches from ambiguous cases, reranks ambiguous candidates with graph embeddings, applies thresholding and one-to-one matching, validates explicit YAGO taxonomy classes against SemOpenAlex URI types, and finally applies TF-IDF lexical refinement. The strict Stage 05 baseline contains 1,755,590 one-to-one alignments and is refined further in `06_experiments/`.*
