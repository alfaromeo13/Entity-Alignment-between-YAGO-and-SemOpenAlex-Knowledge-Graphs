# RDF Preprocessing and Dataset Construction

This stage converts the raw RDF dumps from YAGO and SemOpenAlex into a common TSV representation suitable for large-scale graph embedding training and entity alignment.

The original datasets (dumps) are not directly suitable for graph embedding training or entity alignment. They contain a mixture of structural graph edges, textual literals, schema information, ontology definitions, helper resources, and dataset-specific metadata.

The objective of this stage is therefore to:
1. Parse and normalize RDF data into a uniform line-based representation.
2. Separate structural graph information from textual literals.
3. Remove ontology definitions, schema resources, and helper entities.
4. Extract textual attributes relevant for later entity alignment.
5. Create deterministic train/validation/test graph splits.
6. Produce cleaned datasets suitable for scalable graph embedding training and entity alignment.

## Folder Structure
```
02_preprocessed/
├── scripts/             # preprocessing scripts, Slurm jobs, and utilities
├── logs/                # Slurm logs for preprocessing jobs
├── manifests/           # SemOpenAlex shard manifests generated during preprocessing
├── yago/                # final cleaned YAGO dataset
├── semopenalex_clean/   # final cleaned SemOpenAlex dataset
└── README.md
```
The `yago/` and `semopenalex_clean/` directories contain the final datasets used by all downstream stages of the pipeline.

Temporary SemOpenAlex folders such as `semopenalex_shards/`, `semopenalex_retry_shards/`, `semopenalex_pass3_shards/`, and `semopenalex_combined_shards/` are created during preprocessing. After `semopenalex_clean/` is produced and verified, these temporary folders are no longer needed.

## Processing Workflow
```
Raw RDF Dumps
(Turtle / TriG)
        ↓
Apache Jena riot
(RDF parsing and normalization)
        ↓
N-Triples / N-Quads
        ↓
Filtering and Cleaning
        ↓
Structural / Textual Separation
        ↓
Train / Valid / Test Generation
        ↓
Final Preprocessed Datasets
```
Apache Jena riot is used as the RDF parsing layer of the pipeline. It validates RDF syntax and converts YAGO Turtle files into N-Triples and SemOpenAlex TriG files into N-Quads. These normalized line-oriented formats simplify large-scale stream processing and allow the subsequent Python preprocessing scripts to operate without implementing a full RDF parser.

The preprocessing scripts then filter unwanted resources, separate structural triples from textual information, and generate the datasets used later for embedding training and entity alignment.

The final output consists of two datasets for each knowledge graph:

**Structural triples** 
```text
subject<TAB>predicate<TAB>object
```
These are entity-to-entity graph edges used later for embedding training.

Only triples whose subject and object are both RDF resources (IRIs) are retained as structural graph edges. These triples are written to: `train.tsv`, `valid.tsv`, `test.tsv`

**Textual Data**
```text
entity<TAB>predicate<TAB>text
```
Only selected text-bearing predicates are retained, including labels, names, titles, descriptions, comments, and alternative names. These records are written to `entity_text_raw.tsv`. This file is later used for label extraction, normalization, candidate generation, and entity alignment.

## Scripts

**`run_yago_preprocess.sh`** - YAGO preprocessing wrapper.

The script scans all YAGO Turtle files, converts them to N-Triples using Apache Jena riot, and streams the normalized RDF statements directly into preprocess_structural_stream.py.

Because processing is performed as a stream, intermediate RDF files do not need to be materialized on disk.

---
**`run_semopenalex_one_file.sh`** - SemOpenAlex shard-processing wrapper. Each SemOpenAlex shard is processed independently. Workflow:

1. Decompress .trig.gz shard.
2. Sanitize malformed TriG content.
3. Parse TriG into N-Quads using Apache Jena riot.
4. Run preprocess_structural_stream.py.
5. Store shard-local outputs.
6. Mark the shard as SUCCESS or FAILED.

This shard-based design was introduced because the complete SemOpenAlex RDF dataset was too large to process reliably as a single job and some shards contained malformed RDF statements. Processing shards independently enabled fault isolation and efficient recovery through targeted retry passes.

---
**`preprocess_structural_stream.py`** - Core preprocessing script used by both YAGO and SemOpenAlex.

The script reads normalized RDF statements (N-Triples or N-Quads) from standard input and converts them into graph and text datasets. Main responsibilities:

1. Parse normalized RDF statements.
2. Filter schema resources and dataset-specific helper entities.
3. Separate structural triples from textual literals.
4. Retain only selected text-bearing predicates.
5. Create deterministic train/validation/test splits.
6. Generate preprocessing statistics.

Outputs: `train.tsv`, `valid.tsv`, `test.tsv`, `entity_text_raw.tsv`, `stats.json`

The important logic in this script is the separation between structural entity-to-entity triples and text-bearing literal triples. It also applies deterministic train/validation/test splitting, so repeated runs over the same normalized RDF input produce reproducible downstream datasets.

---
**`sanitize_trig_stream.py`** - First-pass sanitizer. Removes known malformed RDF fragments and problematic Unicode patterns that prevent Apache Jena riot from parsing certain SemOpenAlex shards.

---
**`sanitize_trig_stream_pass2.py`** - Second-pass sanitizer. Introduces block-aware handling of hasKeyword statements and performs additional structural repairs when problematic lines are removed. This pass was used to recover shards that failed after the first preprocessing attempt.

---
**`sanitize_trig_stream_pass3.py`** - Final third-pass recovery sanitizer. Applies the most conservative filtering strategy and was used only for the small number of shards that remained problematic after the previous recovery passes.

The sanitizer scripts are part of the data-recovery logic rather than generic cleanup. They make the SemOpenAlex TriG shards parseable while keeping the rest of the preprocessing stream unchanged.

---
**`build_semopenalex_manifest.sh`** - Creates the full manifest of all SemOpenAlex `.trig.gz` shards to process. Output: 02_preprocessed/manifests/semopenalex_full_manifest.txt

---
**`build_failed_manifest.sh`** - Creates a manifest containing only shards that failed in the previous pass. Output: 02_preprocessed/manifests/semopenalex_failed_manifest.txt

---

**`build_pass3_manifest.sh`** - Creates the final retry manifest from shards that still failed after the second pass. Output: 02_preprocessed/manifests/semopenalex_pass3_manifest.txt

---

**`merge_semopenalex_shards.py`** - Merges successful SemOpenAlex shard outputs into the final clean dataset:

```text
02_preprocessed/semopenalex_clean/
```

It concatenates:

- `train.tsv`
- `valid.tsv`
- `test.tsv`
- `entity_text_raw.tsv`

and produces:

- `merge_summary.json`
- `successful_shards.txt`
- `failed_shards.txt`

# Execution Order:

<mark>Note that all large preprocessing jobs should be submitted through Slurm, not run directly on the login node! </mark>

**1. Preprocess YAGO**

```bash
sbatch /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/scripts/preprocess_yago_barnard.sbatch
```
Expected  output:
```text
/data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/yago/
```
---

**2. Build SemOpenAlex manifest** 

```bash
cd /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed 
bash scripts/build_semopenalex_manifest.sh
```

This creates the list of raw SemOpenAlex `.trig.gz` shards.

---

**3. Run first SemOpenAlex preprocessing pass**

This processes all shards using a Slurm array.

```bash
sbatch /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/scripts/preprocess_semopenalex_array_full.sbatch
```
Temporary output:
```text
02_preprocessed/semopenalex_shards/
```
---

**4. Build failed-shard manifest**

*This identifies shards that failed in the first pass.*

```bash
cd /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed 
bash scripts/build_failed_manifest.sh
```
---

**5. Run retry pass**

```bash
sbatch /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/scripts/preprocess_semopenalex_array_retry.sbatch
```
Temporary output:
```text
02_preprocessed/semopenalex_retry_shards/
```
---
**6. Build pass-3 manifest**

*This identifies the remaining failed shards after retry.*
```bash
cd /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed 
bash scripts/build_pass3_manifest.sh
```
---

**7. Run pass 3**

```bash
sbatch /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/scripts/preprocess_semopenalex_array_pass3.sbatch
```
Temporary output:
```text
02_preprocessed/semopenalex_pass3_shards/
```
---

**8. Build combined SemOpenAlex shard directory**

```bash
cd /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed

rm -rf semopenalex_combined_shards
mkdir -p semopenalex_combined_shards

rsync -a semopenalex_shards/ semopenalex_combined_shards/

find semopenalex_retry_shards -name SUCCESS | while read -r f; do
  d="$(dirname "$f")"
  b="$(basename "$d")"
  rsync -a --delete "$d"/ semopenalex_combined_shards/"$b"/
done

find semopenalex_pass3_shards -name SUCCESS | while read -r f; do
  d="$(dirname "$f")"
  b="$(basename "$d")"
  rsync -a --delete "$d"/ semopenalex_combined_shards/"$b"/
done
```
---

**9. Verify combined shards**

```bash
find semopenalex_combined_shards -name SUCCESS | wc -l
find semopenalex_combined_shards -name FAILED | wc -l
```

Expected final result:

```text
SUCCESS: 1242
FAILED: 0
```

---

**10. Merge SemOpenAlex shards**
```bash
python3 scripts/merge_semopenalex_shards.py \
  --shards-dir /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/semopenalex_combined_shards \
  --output-dir /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/semopenalex_clean
```

Expected final output:

```text
02_preprocessed/semopenalex_clean/train.tsv
02_preprocessed/semopenalex_clean/valid.tsv
02_preprocessed/semopenalex_clean/test.tsv
02_preprocessed/semopenalex_clean/entity_text_raw.tsv
02_preprocessed/semopenalex_clean/merge_summary.json
02_preprocessed/semopenalex_clean/successful_shards.txt
02_preprocessed/semopenalex_clean/failed_shards.txt
```
---
**11. Inspect final SemOpenAlex output**

```bash
cat /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/semopenalex_clean/merge_summary.json
wc -l /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/semopenalex_clean/failed_shards.txt
ls -lh /data/horse/ws/jovu353i-kgalign/KGAlignment/02_preprocessed/semopenalex_clean
```

## Final Outputs

After successful preprocessing, the important final folders are:
```
02_preprocessed/yago/
02_preprocessed/semopenalex_clean/
```
These directories contain the final cleaned datasets (structural graph triples and textual data) which are used by downstream stages.

## Summary
*This stage produced the cleaned graph and text datasets used by the rest of the pipeline. The preprocessing workflow transformed raw YAGO and SemOpenAlex RDF dumps into structural and textual datasets suitable for large-scale graph embedding training and entity alignment. This included RDF parsing and normalization, filtering of schema and helper resources, extraction of selected textual attributes, and construction of train/validation/test graph splits. YAGO was processed directly from Turtle files, while SemOpenAlex required a robust shard-based workflow due to its scale and malformed RDF content. The final SemOpenAlex dataset was created through multiple recovery passes and a final merge of all successful shard outputs.*
