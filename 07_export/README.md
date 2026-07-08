# RDF Export, Analysis, and Validation

This stage converts the final YAGO–SemOpenAlex entity alignments into RDF so they can be imported into GraphDB, inspected using Semantic Web tools, and queried with SPARQL. In simple terms, this stage turns the final TSV table of matched entities into RDF files that GraphDB can load and query.

The exported RDF represents identity links between entities in the two knowledge graphs using the standard OWL predicate:

```text
owl:sameAs
```

The exported files are intended for inspection, visualization, and downstream
knowledge graph integration. This stage also contains the maintained reporting
figures, native result tables, structural analyses, and validation tools.

## Directory map

```text
07_export/
├── README.md                  
├── rdf_alignments/           # production Turtle and TriG alignment exports
├── scripts/                  # export, analysis, figure, and orchestration code
├── logs/                     # Slurm output from maintained Stage 07 jobs
├── validation/               # audit, sampling, annotation, and SPARQL workflow
└── visualizations/
    ├── figures/              # 52 generated publication SVG figures
    ├── tables/               # 38 machine-readable CSV result tables
    ├── THESIS_TABLES.md      # compact preview of every CSV table
    └── RESEARCH_QUESTION_EVIDENCE.md
```

The `rdf_alignments/` and `visualizations/` directories are generated outputs.
The `scripts/` and `validation/` directories are the maintained implementation.
The official SemOpenAlex ontology is a raw source input and therefore lives in
`01_raw/semopenalex/semopenalex-ontology.ttl`.

## Quick start

From the `KGAlignment/` directory, regenerate the RDF export with:

```bash
python 07_export/scripts/export_sameas.py \
  --input 06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv \
  --out-ttl 07_export/rdf_alignments/final_alignments.ttl \
  --out-trig 07_export/rdf_alignments/final_alignments.trig \
  --graph https://kgalign.example.org/graph/final-alignments
```

Regenerate the maintained figures, tables, and evidence map with:

```bash
python 07_export/scripts/generate_all_visualizations.py
```

## Validation

Stage 07 contains two validation tracks that answer different questions.
`validation/audit_alignments.py` checks every final row for
machine-testable defects. The `sampling` and `summarization` scripts support a
human study that can estimate semantic correctness. An integrity audit cannot
prove that two URIs denote the same real-world entity, so it must not be
reported as an accuracy or precision measurement.

Two alignment-aware structural analyses are also exported:

- `41_neighbor_preservation.svg` maps recoverable neighbors from both graphs
  through the final alignments and measures their Jaccard overlap;
- `42_bridge_topology_change.svg` measures connected components before and
  after adding all identity bridges in the selected strict catalog.

Both analyses are exact over the stored Stage 06 neighborhood contexts. Those
contexts contain only immediate, one-hop incoming and outgoing triples: the
pipeline did not recursively traverse to two-hop or three-hop neighbors. The
complete train/validation/test graphs were scanned, but each final A+B+C
profile was capped at 40 tokens—at most 20 predicate/neighbor pairs. The
results are therefore not described as complete topology measurements of the
original 10-billion-edge graphs.

For the exhaustive machine audit, run:

```bash
python 07_export/validation/audit_alignments.py \
  --input 06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv \
  --output-dir 07_export/validation/results/audit
```

For semantic validation, at least 385 independent judgments give an
approximately ±5 percentage-point 95% margin under simple random sampling.
The maintained default is 500. The sampler intentionally oversamples small
entity-type, source, and score strata and records inclusion probabilities and
survey weights, allowing the summarizer to estimate whole-catalog precision
without pretending the sample is proportional:

```bash
python 07_export/validation/sample_for_annotation.py \
  --input 06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv \
  --output-dir 07_export/validation/study \
  --sample-size 500 \
  --seed 20260629
```

This creates `annotation.tsv`, the annotator-facing sheet;
`sample_key.tsv`, the untouched key with scores and weights; and
`sampling_manifest.json`, which records population counts, allocations, and
the seed. For each annotation, record `correct`, `incorrect`, or `uncertain`.
Incorrect rows may be categorized as name ambiguity, incomplete metadata,
missing neighbors, ontology mismatch, type mismatch, noisy source data, or
other. Supporting URLs and notes should explain the evidence; uncertainty
must not be forced into an error. The detailed decision rubric remains in
`validation/ANNOTATION_GUIDELINES.md`.

After genuine annotation, summarize the study with:

```bash
python 07_export/validation/summarize_annotations.py \
  --key 07_export/validation/study/sample_key.tsv \
  --annotations 07_export/validation/study/annotation.tsv \
  --output-dir 07_export/validation/results/human
```

The summarizer refuses incomplete sheets by default because selective
completion can bias the estimate. `--allow-incomplete` is only for a clearly
labelled interim report. Multiple independently completed sheets may be
supplied after `--annotations`; pairwise Cohen's kappa is reported where
judgments overlap. Report the weighted precision estimate and interval, type,
source, and score-band summaries, and the weighted error taxonomy. The ABC
score is not a probability, so its score-band reliability output must not be
called calibrated probability unless a separate held-out calibration model is
fitted.

The final ABC threshold is an optional confidence filter, not a structural
requirement of one-to-one alignment. `validation/review_score_threshold.py`
extracts rows below a proposed cutoff without treating them as errors. The
current `0.20` versus `0.30` review is stored under
`validation/threshold_review/` as all 4,208 affected rows, a deterministic
200-row sample, and a JSON evidence summary. This review must precede any claim
that the higher threshold improves semantic precision.

## Input

The export stage uses the final production alignment set selected after the experimental evaluation performed in Stage 06.

Final input:

```text
06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv
```

This file represents the final one-to-one entity alignments after:

- embedding-based candidate ranking
- profile text refinement
- graph-neighbor consistency refinement
- sensitivity analysis and threshold selection

The final alignment count is read directly from this strict output. The
ablation figures use the same strict taxonomy policy for Baseline, A+B,
C-only, and A+B+C.

The input TSV contains columns including:

```text
yago_entity
semopenalex_entity
embedding_cosine
profile_tfidf_score
neighbor_tfidf_score
abc_score
source
confidence_tier
semopenalex_uri_type
```

Only the entity URIs are required to construct the RDF identity links.

The remaining columns are exported as alignment metadata.

## RDF export script

```text
07_export/scripts/export_sameas.py
```

The script performs the following steps:

1. reads the final alignment TSV
2. extracts YAGO and SemOpenAlex entity URIs
3. removes surrounding angle brackets if present
4. creates an `owl:sameAs` statement for each alignment
5. creates a stable reified resource for the assertion and attaches evidence
   metadata to that resource
6. writes both Turtle and TriG serializations

## RDF Representation

Each predicted alignment is exported as an RDF identity statement.

Example:

```turtle
<http://yago-knowledge.org/resource/Albert_Einstein>
    owl:sameAs
<https://semopenalex.org/author/A123456789> .
```

The export additionally describes each identity assertion using standard RDF
reification. Scores belong to the alignment assertion—not to the YAGO entity:

```turtle
<http://yago-knowledge.org/resource/Albert_Einstein>
    owl:sameAs <https://semopenalex.org/author/A123456789> .

<https://kgalign.example.org/alignment/EXAMPLE_HASH>
    a rdf:Statement, kg:Alignment ;
    rdf:subject <http://yago-knowledge.org/resource/Albert_Einstein> ;
    rdf:predicate owl:sameAs ;
    rdf:object <https://semopenalex.org/author/A123456789> ;
    kg:embeddingScore "0.9143"^^xsd:float ;
    kg:profileTfidfScore "0.9832"^^xsd:float ;
    kg:neighborTfidfScore "0.1245"^^xsd:float ;
    kg:abcScore "0.8674"^^xsd:float ;
    kg:semopenalexType "author" ;
    kg:source "embedding_type_text_top1" ;
    kg:confidence "high_confidence" .
```

The project-specific namespace used for metadata is:

```text
https://kgalign.example.org/schema/
```

## Exported Metadata

The exported metadata describes why a particular alignment was selected.

| Property | Description |
|----------|-------------|
| rdf:subject | YAGO entity in the asserted identity link |
| rdf:predicate | `owl:sameAs` identity predicate |
| rdf:object | SemOpenAlex entity in the asserted identity link |
| embeddingScore | Embedding similarity produced by the DistMult model |
| profileTfidfScore | Similarity between entity textual profiles |
| neighborTfidfScore | Similarity computed from graph-neighbor textual context |
| abcScore | Final weighted score after combining embedding, profile, and neighbor signals |
| semopenalexType | Semantic type of the matched SemOpenAlex entity |
| source | Origin of the alignment within the pipeline |
| confidence | Confidence category assigned during candidate generation |

## Turtle Output

The Turtle serialization is written to:

```text
07_export/rdf_alignments/final_alignments.ttl
```

Typical uses include:

- GraphDB import
- Protégé inspection
- RDF validation
- SPARQL querying
- Semantic Web applications

## TriG Output

The TriG serialization is written to:

```text
07_export/rdf_alignments/final_alignments.trig
```

TriG stores exactly the same triples as Turtle while placing them inside a named graph.

Example:

```trig
<https://kgalign.example.org/graph/final-alignments> {

    <http://yago-knowledge.org/resource/Albert_Einstein>
        owl:sameAs <https://semopenalex.org/author/A123456789> .

    <https://kgalign.example.org/alignment/EXAMPLE_HASH>
        a rdf:Statement, kg:Alignment ;
        rdf:subject <http://yago-knowledge.org/resource/Albert_Einstein> ;
        rdf:predicate owl:sameAs ;
        rdf:object <https://semopenalex.org/author/A123456789> ;
        kg:embeddingScore "0.9143"^^xsd:float ;
        kg:profileTfidfScore "0.9832"^^xsd:float ;
        kg:neighborTfidfScore "0.1245"^^xsd:float ;
        kg:abcScore "0.8674"^^xsd:float ;
        kg:semopenalexType "author" ;
        kg:source "embedding_type_text_top1" ;
        kg:confidence "high_confidence" .

}
```

Using a named graph keeps the generated alignments separate from the original YAGO and SemOpenAlex datasets.

---

## Execution

Run from the project root:

```bash
cd /data/horse/ws/jovu353i-kgalign/KGAlignment

python 07_export/scripts/export_sameas.py \
    --input 06_experiments/graph_neighbor_signal/outputs/strict/sensitivity/abc_w060_035_005_t030.tsv \
    --out-ttl 07_export/rdf_alignments/final_alignments.ttl \
    --out-trig 07_export/rdf_alignments/final_alignments.trig \
    --graph https://kgalign.example.org/graph/final-alignments
```

The script reports the alignment and triple counts when it finishes.

## GraphDB Usage

The generated RDF files can be imported together with YAGO and SemOpenAlex into GraphDB.

Simple alignment query:

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?yago ?semopenalex
WHERE {
    ?yago owl:sameAs ?semopenalex .
}
LIMIT 100
```

Query including alignment metadata:

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX kg: <https://kgalign.example.org/schema/>

SELECT
    ?yago
    ?semopenalex
    ?embedding
    ?profile
    ?neighbor
    ?abc
    ?type
    ?source
    ?confidence
WHERE {
    ?alignment a kg:Alignment ;
               rdf:subject ?yago ;
               rdf:predicate owl:sameAs ;
               rdf:object ?semopenalex ;
               kg:embeddingScore ?embedding ;
               kg:profileTfidfScore ?profile ;
               kg:neighborTfidfScore ?neighbor ;
               kg:abcScore ?abc ;
               kg:semopenalexType ?type ;
               kg:source ?source ;
               kg:confidence ?confidence .
}
LIMIT 100
```

`owl:sameAs` has stronger semantics than a generic similarity link. When
loading this export only for inspection, use a GraphDB repository without an
equality-expanding ruleset unless identity inference is explicitly desired;
otherwise inference across two million links can be expensive.

Query within the named graph:

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?yago ?semopenalex
WHERE {

    GRAPH <https://kgalign.example.org/graph/final-alignments> {

        ?yago owl:sameAs ?semopenalex .

    }

}
LIMIT 100
```

### Maintained GraphDB/SPARQL queries

The reusable queries are stored under `07_export/validation/queries/`:

| Query | What does it do? | Why is it useful? | Expected observation |
|---|---|---|---|
| `check_one_to_one.rq` | Finds YAGO or SemOpenAlex entities linked to more than one counterpart. | Rechecks the one-to-one export constraint inside the triple store. | A correct import returns no rows. |
| `score_and_type_counts.rq` | Aggregates alignment counts and ABC scores by type, source, and confidence tier. | Confirms that GraphDB contains the same catalog composition as the TSV/RDF export. | Counts should reconcile with the Stage 07 tables and strict TSV total. |
| `inspect_alignment.rq` | Returns selected labels, types, identifiers, IRI neighbors, and reified evidence for one pair. | Supports manual identity validation with both graph context and model evidence. | The YAGO and SemOpenAlex descriptions should refer to the same entity when the prediction is correct. |
| `construct_alignment_neighborhood.rq` | Constructs a small RDF subgraph around one predicted pair and its alignment resource. | Produces an actual graph result that GraphDB can visualize, rather than a decorative schematic. | The result should show two source neighborhoods connected by `owl:sameAs`, plus the assertion metadata. |

Both HTTP and HTTPS schema.org namespaces are handled because YAGO uses
`http://schema.org/`, while other imported data may use
`https://schema.org/`. Replace the placeholder IRIs in the two inspection
queries before execution.

### What remains to do in GraphDB

GraphDB screenshots cannot be generated reproducibly until the actual
repository is loaded. The remaining manual workflow is:

1. create a repository without equality-expanding inference for initial
   inspection;
2. import **one** alignment serialization—Turtle for the default graph or TriG
   for the named graph, not both;
3. import YAGO and SemOpenAlex, or smaller source subgraphs, when complete
   neighborhoods are required;
4. run `check_one_to_one.rq` and `score_and_type_counts.rq` as import smoke
   tests;
5. select one externally confirmed and one questionable alignment, replace
   the IRIs in `construct_alignment_neighborhood.rq`, and visualize the
   constructed result;
6. capture the repository statistics and the two local-neighborhood views only
   after recording the repository ruleset, imported files, and query.

The most useful thesis screenshots would therefore be:

- one confirmed YAGO–`owl:sameAs`–SemOpenAlex neighborhood;
- one contradicted or ambiguous neighborhood illustrating an error mode;
- one GraphDB repository-statistics view reporting statements, resources,
  classes, and predicates.

These screenshots are presentation evidence, not replacements for Tables
01–38 or the human validation study. Arbitrary SPARQL-result screenshots,
interface chrome, and a second import of the same alignment triples would add
clutter rather than evidence.

### Why some YAGO dump URIs have no public webpage

A missing YAGO webpage does not automatically mean that an alignment URI is
invalid. The project uses the downloaded YAGO 4.5 RDF snapshot, including
approximately 23 GB of `yago-facts.ttl` and 128 GB of
`yago-beyond-wikipedia.ttl`. YAGO officially distributes ordinary facts and
“facts beyond Wikipedia” as separate parts of the release:

```text
https://yago-knowledge.org/downloads/yago-4-5
```

The public YAGO browser and SPARQL endpoint are separate live services. They
may run a different snapshot, omit a dump-only or beyond-Wikipedia entity from
their browser index, or require the exact case-sensitive and escaped resource
identifier. The YAGO homepage also currently announces a forthcoming new
release and website overhaul, which makes temporary snapshot differences
particularly plausible:

```text
https://yago-knowledge.org/
```

An RDF IRI identifies a graph resource; it is not a guarantee that an HTML
description page will remain dereferenceable. For this project, the immutable
local dump is therefore the provenance authority. If the URI occurs in that
dump, preprocessing did not invent it merely because the current website
cannot display it.

To distinguish a browser problem from a public-endpoint snapshot difference,
run the following query at `https://yago-knowledge.org/sparql` after replacing
the example IRI:

```sparql
ASK {
  {
    <http://yago-knowledge.org/resource/REPLACE_ME> ?predicate ?object
  }
  UNION
  {
    ?subject ?predicate <http://yago-knowledge.org/resource/REPLACE_ME>
  }
}
```

A `true` result with no browser page indicates a browser/rendering problem. A
`false` result for an IRI that is present locally indicates that the live
endpoint and downloaded dump do not contain exactly the same snapshot. Only an
IRI missing from both the local raw dump and the relevant public data would
indicate a pipeline-provenance problem.

## Validation scope

There is no reliable automatic procedure that can prove every identity claim
correct. The project therefore combines three complementary levels:

1. the exhaustive integrity audit checks every row for one-to-one assignment,
   URI, type, score, duplicate, and missing-value defects;
2. external Wikidata QIDs validate the subset for which independent
   identifiers exist, while retaining the strong type-selection caveat;
3. the stratified 500-pair human study estimates whole-catalog precision,
   confidence intervals, score reliability, and error categories.

The current strict catalog passes the first level with zero reported integrity
issues. The external-ID analysis is partial, and the human study remains
incomplete until verdicts are entered in the annotation sheet.

## Script guide

The code is intentionally split into statistical backends and renderers.
Backends scan large source files once and cache compact Python objects;
renderers convert those statistics into SVG and CSV. This separation makes
rerendering fast and keeps plotting code from silently redefining the
measurements. Static figures use Matplotlib and Seaborn; the ontology parser
also uses RDFLib. `scripts/requirements-visualization.txt` pins the Python
packages expected by the stage-local virtual environment.

### Production and orchestration

`scripts/export_sameas.py` streams the final TSV, writes direct `owl:sameAs`
assertions, creates stable SHA-256-based alignment IRIs, attaches standard RDF
reification and evidence metadata, and emits equivalent Turtle and named-graph
TriG files. It normalizes and validates absolute IRIs, escapes RDF literals,
validates numeric lexical forms, and fails rather than writing malformed RDF.
Its inputs and destinations are explicit command-line arguments, allowing the
same exporter to be tested on a small file or used on the two-million-row
production catalog.

`scripts/generate_all_visualizations.py` is the maintained reporting entry
point. It invokes every figure family in dependency order, ensures Tables
26–27 exist before rebuilding the combined table preview. A child failure
stops the workflow. Pass
`--refresh` when source data changed and statistical caches must be rebuilt;
omit it when only presentation code changed.

### Statistical backends

`scripts/thesis_statistics.py` computes and caches the core dataset, training,
candidate, threshold, ablation, score, and system-overlap statistics used by
Figures 01–16. It deliberately distinguishes proxy diagnostics from human
precision and recall. It reads the four maintained systems, PBG evaluation and
training summaries, candidate-stage counts, threshold/sensitivity results,
and deterministic samples used for inspection cohorts, then writes
`visualizations/cache/thesis_statistics.pkl`.

`scripts/additional_statistics.py` computes the extended observed-type,
held-out topology, ambiguity, final alignment matrix, label-length,
neighbor-score, and predicate-co-occurrence statistics used by Figures 17–30.
It scans held-out string triples and the final catalog, uses deterministic
sampling where a full cross-product would be impractical, and writes
`visualizations/cache/additional_statistics.pkl`.

`scripts/external_identifier_validation.py` builds the partial independent
Wikidata-QID validation for concepts, institutions, funders, publishers, and
sources by scanning the corresponding compressed SemOpenAlex RDF shards and
comparing those QIDs with QIDs encoded in YAGO resource URIs. It caches the
mapping in `visualizations/cache/external_identifier_validation.pkl`. Its rates apply only to
entities with identifiers on both sides and therefore are not global
precision.

### Static figure generators

`scripts/make_thesis_figures.py` produces Figures 01–16: scale, relation
imbalance, embedding evaluation, training behavior, candidate attrition,
ambiguity, thresholding, ablation, score evidence, and inspection cohorts. It
also writes the core CSV tables that preserve the exact plotted values.

`scripts/make_additional_figures.py` produces Figures 17–30 and rebuilds
`THESIS_TABLES.md`. It covers observed ontology use, predicate vocabularies,
evaluation-graph topology, label properties, confidence descriptions, neighbor
agreement, and predicate co-occurrence. It is the final table-index builder, so
the orchestrator runs prerequisite table producers first.

`scripts/make_reporting_additions.py` produces Figures 31–35 and the
research-question evidence map: baseline provenance, selection mechanisms,
type evolution, decision-cohort correlations, and external-ID agreement. It
collects the reporting additions used in the final thesis figures and writes
`RESEARCH_QUESTION_EVIDENCE.md`.

`scripts/make_visual_story_figures.py` produces Figures 36–40: RDF processing
yield, target coverage, aggregate bipartite alignment flow, SemOpenAlex PBG
training, and externally checked alignment cases. The bipartite figure is an
aggregate type-to-type flow rather than an unreadable two-million-edge graph;
the case figure only uses alignments with real external evidence.

`scripts/make_structural_validation_figures.py` produces Figures 41–42 and
Tables 26–27 by reconstructing aligned-neighbor edges from the capped Stage 06
contexts. It maps recoverable aligned neighbors to compute preservation
Jaccard values, then uses an efficient disjoint-set representation to compare
components before and after all identity bridges. Its cache and claims are
explicitly limited to stored, capped contexts.

`scripts/make_ontology_schema_figures.py` produces Figures 43–44 and Tables
28–30. It parses the YAGO schema/taxonomy and pinned official SemOpenAlex
OWL/SHACL ontology, inventories their formal models, and extracts complete
domain–predicate–range signatures. It also hashes every parsed schema source,
making the ontology comparison auditable.

`scripts/make_supported_extension_figures.py` produces Figures 45–46 and
Tables 31–32: confidence distributions by entity type and exact RDF-export
triple composition. It excludes strict-proxy rows from the type-specific score
distribution because their synthetic high scores would obscure ranked
candidate behavior.

`scripts/make_link_prediction_extensions.py` produces Figures 51–53 and Table
38 from the final PBG evaluation metrics: model trade-offs, measured Hits@K
curves, and rank-band composition derived from reported Hits@1/10/50. It never
reconstructs per-triple ranks or relation-level scores that the raw PBG logs do
not contain.

For interpretation, Table 02 and Figures 04 and 51–53 are the scientific
model-comparison results. They use the final held-out evaluation: 176,574 YAGO
triples and the documented 50,000-triple SemOpenAlex evaluation sample.
Figures 05 and 39 are optimization diagnostics showing whether training
behaved sensibly; training curves alone do not establish that one model
generalizes better than another.

`scripts/make_distribution_extensions.py` produces Figures 47–50 and Tables
33–37. It adds the full predicate rank-frequency curve, entity-degree CCDF,
predicate namespace/entropy analysis, and a YAGO-versus-SemOpenAlex PBG
partition-scale comparison. Partition averages are arithmetic consequences of
the saved PBG configurations and dataset totals, not invented measurements of
individual bucket load.

### Validation tools

`validation/audit_alignments.py` checks every final row for machine-testable
integrity problems and writes a JSON report plus bounded issue examples.
`validation/sample_for_annotation.py` creates the reproducible, blinded,
stratified annotation sheet, hidden score/weight key, and sampling manifest.
`validation/summarize_annotations.py` joins completed sheets to that key,
validates verdicts, computes survey-weighted precision and Wilson intervals,
summarizes error types and score reliability, and measures pairwise Cohen's
kappa for overlapping annotators. `validation/queries/` contains the four
maintained GraphDB queries: one-to-one checking, score/type reconciliation,
pair inspection, and a CONSTRUCT query for neighborhood visualization.

## Non-figure output guide

The two files in `rdf_alignments/` are the production deliverable. Use the Turtle file
for a default-graph import and the TriG file when the alignments should remain
inside the named graph
`https://kgalign.example.org/graph/final-alignments`. They contain equivalent
data, so a GraphDB repository normally needs only one of them.

Running `validation/sample_for_annotation.py` creates a study directory whose
`sample_key.tsv` contains hidden identities and sampling weights,
`annotation.tsv` is the annotator-facing worksheet, and
`sampling_manifest.json` records the seed and allocation.

Running `validation/audit_alignments.py` creates `audit_report.json` and
`audit_issue_examples.tsv` in the requested output directory.

`visualizations/THESIS_TABLES.md` is a convenient preview, while the 38 CSV
files in `visualizations/tables/` are the authoritative machine-readable
results. `RESEARCH_QUESTION_EVIDENCE.md` maps research claims to figures and
tables.

`01_raw/semopenalex/semopenalex-ontology.ttl` is the pinned official
SemOpenAlex ontology required for reproducible schema analysis. It was
retrieved on 2026-06-30 from
`https://raw.githubusercontent.com/metaphacts/semopenalex/main/ontologies/semopenalex-ontology.ttl`;
the corresponding Git blob is
`88c3f9d4e02710e39f726467f32ac30d1eda0726`, and the file SHA-256 is
`9557078a1fdb75a5aeafd94d1192f752dc5af2cd6912fd58ab5b7434f4c85e29`.
`01_raw/semopenalex/download_semopenalex.sh` now downloads this ontology from
GitHub together with the SemOpenAlex S3 data. YAGO and SemOpenAlex schema
inputs therefore both live in Stage 01.

## Analyses intentionally left pending

Several attractive plots would imply stronger evidence than the repository
currently contains. A manual-validation accuracy summary and empirical score
calibration require completed human judgments, so no correctness percentages
are fabricated. The existing proxy-gold and external-identifier analyses are
clearly labelled as partial diagnostics.

A monotonic “refinement waterfall” is also not generated because the actual
pipeline contains alternative and expanding systems—especially the A+B
profile enrichment—rather than one sequence of filters. Figure 33 and Table 19
show the real per-system type evolution without inventing intermediate stages.

A predicate-frequency chart is not relabelled as “predicate importance.”
Frequency, co-occurrence, and formal domain/range connectivity are available
in Figures 18, 30, and 44, but causal importance would require an attributable
predicate-level alignment model that this pipeline does not use.

A before/after UMAP is not generated from the independently trained YAGO and
SemOpenAlex embedding spaces. Their coordinates are not directly comparable
without an explicit cross-space transformation. Likewise, GraphDB screenshots
are presentation artifacts rather than reproducible analyses; the maintained
SPARQL queries and HTML explorer preserve the underlying evidence more
reliably.

Embedding-norm, nearest-neighbor, hubness, and intra/inter-type similarity
analyses would require a dedicated distributed scan of the multi-terabyte,
partitioned PBG checkpoints. They are not inferred from checkpoint file sizes.
Figure 50 therefore reports only exact configuration scale and explicitly
labelled arithmetic averages.

Literal length by predicate and complete URI/literal/blank-node composition
would require a new predicate-aware census of the raw RDF or the approximately
275 GB of preprocessed entity-text rows. The existing summaries do not retain
all of those categories at the required granularity, so no partial scan is
presented as a whole-dataset result.

The `torchbiggraph_eval` logs contain global metrics and partition-bucket
aggregates, but not individual triple ranks or relation identifiers. Figures
51–53 therefore use the reported final metrics directly. Figure 53 derives
aggregate rank bands algebraically from nested Hits@K values; it is not an
individual-rank histogram. Relation-wise MRR and a true rank distribution
cannot be reconstructed from these logs.

Pie charts are deliberately not added. The relevant compositions contain
several unequal categories or require comparison between two graphs; aligned
bars, stacked bars, and curves preserve labels and support more accurate
comparisons. Figures 31, 46, and 49 cover the plausible pie-chart subjects in
more readable forms.

## Figure catalog

All figures are SVG files in `07_export/visualizations/figures/`. They are
generated from project data rather than manually edited artwork.

### What, why, and what to observe

The SVGs keep captions short so the plots remain readable. This table supplies
the interpretation that should accompany each figure in the thesis,
presentation, or repository. “Observe” identifies the intended reading of the
result; it is not an additional claim beyond the plotted data.

| Figure | What is this? | Why does it matter? | What should I observe? |
|---|---|---|---|
| 01 — Dataset scale | Four comparisons of encoded entities, relations, structural triples, and text rows. | Establishes the computational scale that motivated streaming preprocessing, HPC execution, and partitioned embeddings. | SemOpenAlex is much larger in entities and triples, while YAGO uses more relation types and produced more text rows. |
| 02 — Relation Pareto | Top held-out predicates with individual and cumulative triple shares. | Shows whether a small relation subset can dominate embedding optimization and evaluation. | `rdf:type` and `owl:sameAs` dominate YAGO, while SemOpenAlex volume is concentrated in a small scholarly-predicate core. |
| 03 — Relation Lorenz | Lorenz curves and Gini coefficients for predicate frequencies. | Quantifies relation imbalance without relying on hand-picked top predicates. | Both graphs are unequal, but YAGO is more concentrated than SemOpenAlex. |
| 04 — Embedding benchmark | Final MRR, Hits@1/10/50, and AUC for TransE, DistMult, and ComplEx. | This is the principal scientific comparison used to choose the candidate-ranking model. | DistMult leads the central MRR and early-Hits metrics; TransE remains stronger on some YAGO broad-rank metrics. |
| 05 — Training dynamics | YAGO loss, MRR, Hits@10, and AUC across epochs. | Confirms convergence and guards against reporting a single accidental checkpoint. | Loss stabilizes and ranking metrics plateau; the curves are diagnostics, not substitutes for final evaluation. |
| 06 — Candidate attrition | Counts from 328.8 million blocked exact-label pairs through filtering and final systems. | Makes every major reduction and expansion in candidate volume visible. | Blocking removes most Cartesian comparisons, type filters reduce implausible pairs, and profile enrichment expands final coverage. |
| 07 — Candidate ambiguity CCDF | Complementary cumulative distribution of candidates per YAGO entity. | Demonstrates why normalized-label equality cannot by itself establish identity. | A substantial tail retains many alternatives, including entities with 10, 20, or more candidates. |
| 08 — Ambiguity by type | Candidate-count bands separated by SemOpenAlex entity type. | Identifies which semantic categories require the strongest disambiguation. | Works and authors have pronounced high-ambiguity tails; smaller types exhibit different ambiguity regimes. |
| 09 — Threshold trade-off | Candidate retention, type filtering, and rejection across embedding thresholds. | Documents the operating-point choice instead of presenting threshold 0.30 as arbitrary. | Higher thresholds sharply reduce coverage while changing the mix of accepted and semantically rejected candidates. |
| 10 — Semantic rejection matrix | Counts of rejected YAGO-profile and SemOpenAlex-type combinations. | Shows the concrete contribution of type compatibility beyond numerical similarity. | A few implausible flows, especially broad organization/place/work combinations, account for most rejections. |
| 11 — Ablation comparison | Final sizes and proxy diagnostics for Baseline, A+B, C-only, and A+B+C. | Separates the contribution of profile text from graph-neighbor evidence. | Profile enrichment drives most coverage growth; neighbor-only evidence is weaker and the selected strict combined system retains about 1.97 million links. |
| 12 — System UpSet | Exact intersections among the four alignment systems. | Distinguishes robustly repeated links from method-specific additions. | A large shared core exists, alongside sizeable profile-enriched and smaller method-specific subsets. |
| 13 — Evidence rainclouds | Embedding, profile, and neighbor score distributions by accepted, new, proxy, and rejected cohorts. | Reveals distribution overlap that means and tables conceal. | Proxy rows form a synthetic high-score mass, profile evidence is strong for enriched links, and neighbor scores remain comparatively small. |
| 14 — Score interactions | Accepted and threshold-rejected density plots for pairs of evidence scores. | Shows the multivariate decision landscape rather than treating scores independently. | Embedding and profile evidence separate decisions most clearly; neighbor evidence adds a weaker, complementary signal. |
| 15 — Evidence by type | Mean weighted ABC contributions for each entity type. | Tests whether one evidence balance works uniformly across semantic categories. | Embedding and profile components dominate, while their relative contribution varies by type and the 5% neighbor term stays small. |
| 16 — Validation-sample cohorts | Score, type, and label-length comparisons within the current 500-pair stratified sample. | Directs manual review toward different score regimes without pretending that unlabeled samples are errors. | Strict-proxy pairs form a distinct high-score group, while ranked pairs span three progressively higher ABC-score bands. |
| 18 — Top predicates | Thirty most frequent held-out predicates in each graph. | Makes the semantic focus of general-purpose YAGO and scholarly SemOpenAlex directly comparable. | YAGO mixes identity, type, location, and general relations; SemOpenAlex emphasizes scholarly authorship, citation, and publication structure. |
| 19 — Type profiles | Most frequent observed `rdf:type` classes in held-out data. | Complements the formal schema with evidence about classes actually used by instances. | YAGO has a broad heterogeneous class profile; SemOpenAlex is concentrated in its scholarly entity classes. |
| 20 — Predicate overlap | Counts of predicate URIs unique to YAGO, shared, and unique to SemOpenAlex. | Quantifies direct vocabulary compatibility between the graphs. | Only two predicate URIs are shared, so entity alignment cannot rely on a common relation vocabulary. |
| 21 — Evaluation-graph topology | Nodes, edges, degree summaries, hubs, and components for tractable evaluation graphs. | Provides defensible topology evidence without claiming to summarize the complete terabyte-scale training graph. | Both evaluation graphs are sparse and fragmented, with mean behavior far below their largest hubs. |
| 22 — Degree distribution | Log–log degree-frequency curves for the evaluation graphs. | Shows whether connectivity is homogeneous or dominated by a long tail. | Most nodes have very low degree and a small hub population extends the tail by several orders of magnitude. |
| 23 — Component sizes | Ranked connected-component sizes for both evaluation graphs. | Describes fragmentation more clearly than a component count alone. | Many components are small, while a limited number of much larger components dominate connected mass. |
| 24 — Aligned label lengths | Final YAGO and SemOpenAlex label lengths plus within-pair length differences. | Detects broad normalization or formatting asymmetries in accepted links. | The two distributions are similar overall, but only a minority of pairs have exactly equal character length. |
| 25 — Ambiguous labels | Normalized labels with the largest SemOpenAlex candidate blocks. | Provides intuitive examples of why label blocking still requires ranking. | Generic publication, institution, and personal names can refer to tens or hundreds of target entities. |
| 26 — Confidence distribution | Accepted and threshold-rejected ABC-score distributions around the selected cutoff. | Documents numerical separation without calling the score a calibrated probability. | Rejected candidates lie below 0.30, ambiguous accepted candidates occupy a broad higher range, and proxy rows create a separate high-score mass. |
| 27 — Proxy recovery by type | Proxy totals, recovered links, and recall-like rates by entity type. | Tests type-specific recovery against the strict label-derived silver standard. | Recovery is high for several types but uneven; these rates are proxy diagnostics, not human recall. |
| 28 — Alignment type matrix | Final ambiguous YAGO-profile to SemOpenAlex-type counts. | Reveals dominant and unusual semantic flows hidden by global totals. | Person-like profiles overwhelmingly map to authors and creative-work-like profiles to works, with smaller cross-type flows. |
| 29 — Neighbor agreement | Hexbin relationships between neighbor score and embedding, profile, and ABC scores. | Tests whether graph-neighbor evidence duplicates or complements the stronger channels. | Correlations are weak, confirming that neighbor evidence is mostly complementary rather than a replacement for profile or embedding evidence. |
| 30 — Predicate co-occurrence | Jaccard co-occurrence matrices for predicates incident to the same entities. | Summarizes local relation families and schema usage beyond frequency counts. | Co-occurrence is structured but sparse, and the characteristic predicate groupings differ between the two graphs. |
| 31 — Baseline composition | Strict-proxy versus embedding-ranked baseline shares and baseline type counts. | Prevents the baseline from being interpreted as one homogeneous selection mechanism. | The baseline is a mixture of two large sources and is strongly author-dominated. |
| 32 — Final-score mixture | ABC-score distributions separated by strict proxy and ranked ambiguous selection. | Explains why one global histogram would be statistically misleading. | Strict proxies use fixed 1.0 embedding/profile markers and therefore cluster at 0.95–0.99; ranked ambiguous links form a broad measured distribution. |
| 33 — Type evolution | Entity-type counts across Baseline, A+B, C-only, and A+B+C. | Identifies which semantic categories account for system growth or contraction; it does not measure correctness. | Profile enrichment expands several types substantially, while the final combination largely preserves that coverage. |
| 34 — Decision correlations | Score-correlation matrices calculated separately for accepted and rejected ambiguous pairs. | Avoids the proxy mass obscuring relationships around the actual threshold decision. | ABC is strongly tied to embedding among accepted links, while rejected links show a markedly different embedding/profile relationship. |
| 35 — External identifier agreement | Wikidata-QID agreement for checkable final links by type and source. | Supplies independent partial validation where both graphs expose identifiers. | Sources and publishers agree strongly, while institution and concept subsets reveal serious type-dependent weaknesses. |
| 36 — RDF processing yield | Structural, literal/non-structural, filtered, helper, and malformed processing outcomes. | Connects raw RDF volume to the graph and text artifacts used downstream. | Structural retention dominates, but text extraction and filtering account for meaningful graph-specific shares. |
| 37 — Target coverage | Final aligned counts as a fraction of available SemOpenAlex catalog sizes by type. | Separates a two-million-link headline from actual type-specific catalog coverage. | Coverage is highly uneven: institutions reach about 24.7%, publishers 12.8%, and keywords 10.1%, while several taxonomy levels remain very low. |
| 38 — Bipartite flow | Aggregate ribbons from heuristic YAGO predicate-profile categories to known SemOpenAlex URI types. | Provides the requested bipartite view without drawing millions of unreadable entity-level edges. | Person-to-author and creative-work-to-work dominate. “Unclassified by predicates” means the heuristic abstained; it does not mean either URI or the SemOpenAlex type is missing. |
| 39 — SemOpenAlex PBG training | Weighted epoch losses and final-epoch partition-loss distributions for three models. | Shows convergence and partition heterogeneity on the 9.62-billion-triple graph. | Loss decreases across epochs, while model-specific partition spreads show that optimization difficulty is not uniform. |
| 40 — Alignment cases | One externally confirmed and one contradicted final alignment with scores and QIDs. | Demonstrates concretely why high similarity does not guarantee real-world identity. | Similar-looking, high-scoring links can either agree or disagree when checked against independent identifiers. |
| 41 — Neighbor preservation | Jaccard overlap after mapping recoverable neighbors through final alignments. | Directly tests whether identity links preserve local graph context. | Most evaluable pairs have little or no shared mapped neighborhood; the small positive tail varies strongly by type. |
| 42 — Bridge topology | Components and component sizes before and after adding all identity bridges. | Quantifies the structural effect of alignment instead of merely illustrating a bridge. | Identity links greatly reduce component count and enlarge connected structures in the capped aligned-context graph. |
| 43 — Formal schema comparison | OWL/SHACL classes, property declarations, constraints, namespaces, and hierarchy metrics. | Separates formal ontology design from instance-level predicate frequency. | YAGO has a vastly deeper taxonomy and SHACL-oriented property semantics; SemOpenAlex explicitly declares more OWL properties. |
| 44 — Predicate connectivity | Selected formal domain-to-object-property-to-range signatures for both schemas. | Makes each graph’s semantic schema readable as connectivity rather than a flat predicate list. | YAGO connects broad general-purpose classes, whereas SemOpenAlex centers authors, works, institutions, sources, publishers, and concepts. |
| 45 — Confidence by type | ABC-score distributions for ranked ambiguous links, separated by entity type. | Tests whether one global score distribution hides type-specific difficulty. | Authors and sources generally score higher than works, concepts, and institutions; proxy rows are excluded to expose this variation. |
| 46 — RDF export composition | Triple counts for direct identity links, reification, numerical evidence, and categorical metadata. | Explains why two million alignments produce 26.31 million RDF triples. | Standard reification is the largest component, followed by numerical and categorical evidence; direct `owl:sameAs` links are retained explicitly. |
| 47 — Relation rank–frequency | Full held-out predicate frequencies ordered by rank on log–log axes. | Extends the top-predicate view to the complete vocabulary tail. | Both curves are heavy-tailed but have different shapes; no formal Zipf fit is claimed. |
| 48 — Degree CCDF | Probability that entity degree is at least a given threshold. | Gives the graph-mining-standard tail view complementary to Figure 22’s point frequencies. | Degree-one entities dominate and only a very small fraction persist into the high-degree tail. |
| 49 — Namespace and entropy | Predicate occurrence shares by namespace plus normalized Shannon entropy. | Links vocabulary provenance with a quantitative measure of frequency diversity. | YAGO is more concentrated and has lower normalized entropy; SemOpenAlex spreads volume across its ontology and reused scholarly namespaces. |
| 50 — PBG partition scale | Entity partitions, possible partition pairs, and arithmetic average partition loads. | Explains why SemOpenAlex required a substantially heavier distributed configuration. | SemOpenAlex uses 128 versus 32 entity partitions, creating 16,384 versus 1,024 possible partition pairs and much larger checkpoint partitions. |
| 51 — Model trade-off | MRR versus Hits@10 with AUC encoded by bubble area. | Makes multi-metric model selection visible in one compact final-evaluation view. | DistMult occupies the strongest MRR/Hits@10 region, while TransE’s YAGO AUC advantage remains visible. |
| 52 — Hits@K curves | Reported Hits@1, Hits@10, and Hits@50 connected for each model. | Shows how quickly correct entities become reachable as the allowed rank expands. | SemOpenAlex models start much higher at rank 1; all models approach very high recovery by rank 50. |
| 53 — Rank-band composition | Shares in rank 1, ranks 2–10, ranks 11–50, and above 50 derived from Hits@K. | Converts cumulative metrics into an intuitive difficulty composition without inventing individual ranks. | About 80% of SemOpenAlex cases rank first for DistMult/ComplEx, compared with roughly 40% on YAGO. |

### Detailed methodological notes

The following paragraphs record scope, caveats, and links between figures and
tables. Use the interpretation table above for a quick reading and these notes
when writing the methods or results chapters.

**01 — Dataset scale.** Compares entity, relation, structural-triple, and text
volume across YAGO and SemOpenAlex. It establishes the computational scale and
explains why streaming, HPC resources, and partitioned embeddings were needed.

**02 — Relation Pareto.** Ranks predicates by held-out frequency and shows how
quickly a small predicate subset accounts for most edges. It identifies
relation imbalance that can dominate embedding training.

**03 — Relation Lorenz.** Summarizes predicate-frequency inequality with
Lorenz curves. It supports the claim that both graphs have highly uneven
relation distributions without relying on a few selected predicates.

**04 — Embedding benchmark.** Compares TransE, DistMult, and ComplEx using
link-prediction metrics on both graphs. It documents the empirical basis for
selecting DistMult for downstream candidate ranking.

**05 — Training dynamics.** Shows loss and ranking metrics over training
epochs. It helps distinguish genuine convergence from a result reported only
at one favorable checkpoint.

**06 — Candidate attrition.** Follows candidate counts from raw exact-label
pairs through filtering and final selection. It makes the scale reduction and
the role of each filtering stage explicit.

**07 — Candidate ambiguity CCDF.** Shows the long tail of entities sharing the
same normalized label. It demonstrates why label equality is a candidate
generator rather than sufficient identity evidence.

**08 — Ambiguity by type.** Separates label ambiguity by SemOpenAlex entity
type. It reveals which domains, especially authors and works, require stronger
disambiguation evidence.

**09 — Threshold trade-off.** Compares retained candidates and semantic-filter
outcomes across embedding thresholds. It documents why the selected threshold
balances coverage against progressively weaker candidates.

**10 — Semantic rejection heatmap.** Counts incompatible YAGO-profile and
SemOpenAlex-type combinations removed by semantic filtering. It shows what the
type constraint contributes beyond numerical similarity.

**11 — Ablation comparison.** Compares the baseline, profile-text enrichment,
graph-neighbor-only method, and final combined system. It identifies profile
text as the main expansion signal and neighbor evidence as a smaller
refinement.

**12 — System UpSet.** Displays exact intersections among the four alignment
systems. It distinguishes alignments consistently recovered by multiple
methods from method-specific additions.

**13 — Evidence rainclouds.** Compares embedding, profile, neighbor, and final
score distributions for important decision groups. It exposes overlap and
separation that averages alone would conceal.

**14 — Score interactions.** Plots pairwise score relationships for accepted
and rejected candidates. It shows whether the evidence channels reinforce one
another or capture different properties.

**15 — Evidence by type.** Decomposes the weighted final score by entity type.
It shows that the usefulness of embedding, profile, and neighbor evidence is
not uniform across semantic categories.

**16 — Validation-sample cohorts.** Compares the strict-proxy cohort with
three ranked ABC-score bands in the current 500-pair stratified sample. It
guides manual review without treating unannotated pairs as errors.

**18 — Top predicates.** Displays the 30 most frequent held-out predicates in
each graph. It makes the different scholarly and general-knowledge graph
semantics visible.

**19 — Ontology/type profiles.** Compares the most frequent `rdf:type` classes
in the held-out graphs. It illustrates the broad YAGO ontology and the more
specialized SemOpenAlex schema.

**20 — Predicate overlap.** Counts predicate URIs unique to each graph and
shared by both. It quantifies the limited direct schema overlap that motivates
alignment above the predicate level.

**21 — Evaluation-graph topology.** Reports nodes, edges, degree, density, and
components for the tractable evaluation graphs. It provides topology evidence
without pretending the SemOpenAlex sample is its terabyte-scale training graph.

**22 — Degree distribution.** Shows log–log degree-frequency curves for the
evaluation graphs. It supports heavy-tail language and highlights hubs without
claiming a fitted power law.

**23 — Component-size ranks.** Ranks connected components by size in both
evaluation graphs. It shows fragmentation and the relative dominance of the
largest components.

**24 — Aligned-label lengths.** Compares label lengths and within-pair length
differences across every final alignment. It detects broad formatting and
normalization asymmetries in the accepted population.

**25 — Most ambiguous labels.** Ranks normalized labels producing the largest
SemOpenAlex candidate blocks. It provides concrete examples of why names such
as generic publication terms are difficult.

**26 — Confidence distribution.** Contrasts accepted and threshold-rejected
score distributions. It describes numerical separation, but must not be called
calibration until human correctness labels are available.

**27 — Proxy-gold by type.** Shows strict exact-label proxy composition and
type-specific recovery in the final catalog. It diagnoses coverage against the
silver standard without presenting proxy labels as true ground truth.

**28 — Alignment type matrix.** Counts ambiguous final alignments by YAGO
profile type and SemOpenAlex URI type. It reveals dominant flows, including
accepted pairs whose YAGO type cannot be resolved from predicate evidence alone.

**29 — Neighbor-score agreement.** Relates the TF–IDF neighbor score to
embedding, profile, and final scores on a deterministic sample. It shows that
neighbor evidence is generally weak and complementary rather than redundant.

**30 — Predicate co-occurrence.** Measures Jaccard overlap among incident
predicate entity sets. It summarizes which relation families tend to occur in
the same local neighborhoods.

**31 — Baseline composition.** Separates strict proxy and embedding-ranked
alignments in the Stage 05 baseline. It prevents the two selection mechanisms
from being interpreted as one homogeneous population.

**32 — Final-score mixture.** Compares final-score distributions by selection
mechanism. Strict proxies were assigned embedding and profile markers of 1.0,
so their ABC scores are mechanically concentrated between approximately 0.95
and 0.99; those values are not calibrated probabilities. The ranked ambiguous
component is the broader measured score distribution.

**33 — Entity-type evolution.** Tracks entity-type counts across the baseline,
A+B, graph-neighbor-only, and A+B+C systems. It shows which types account for
coverage gains or losses.

**34 — Evidence correlations by decision.** Reports score correlations
separately for accepted and rejected ambiguous cohorts. This avoids the strict
proxy mass hiding relationships relevant to actual ranking decisions.

**35 — External identifier agreement.** Compares YAGO URI Wikidata QIDs with
SemOpenAlex Wikidata links where both exist. It provides independent partial
validation and exposes severe type dependence, so it is not an overall
precision estimate.

**36 — RDF processing yield.** Separates structural, textual, and discarded or
non-structural processing outcomes. It documents how raw RDF volume becomes
the graph and profile inputs used by the pipeline.

**37 — Target catalog coverage.** Compares final alignments with SemOpenAlex
catalog sizes by entity type. It answers how much of each target category is
actually linked.

**38 — Bipartite alignment flow.** Draws aggregate flows from YAGO profile
categories to SemOpenAlex entity types. `unclassified by predicates` means the
YAGO entity had no decisive predicate signature among the heuristic
person/work/organization/place/event hints. It contains 207,249 links—about
20.6% of the non-proxy flows shown.
SemOpenAlex types remain known from their URIs. These links passed other
ranking evidence, but the heuristic supplied no positive YAGO type evidence;
the category is therefore a validation priority, not proof of an invalid link.

**39 — SemOpenAlex PBG training.** Shows weighted epoch loss and partition
variation across all 16,384 PBG partitions. It documents large-scale training
behavior rather than relying on an unrepresentative partition.

**40 — Alignment case studies.** Contrasts one externally confirmed and one
externally contradicted final link, including scores and QIDs. It demonstrates
why high aggregate scores still require independent identity evidence.

**41 — Neighbor preservation.** Maps recoverable neighbors through the final
alignment into shared pair IDs and computes Jaccard overlap. It directly
measures aligned-neighborhood preservation within the stored contexts.

**42 — Bridge topology change.** Compares components, largest component, and
mean component size before and after adding every identity bridge. It
quantifies how alignment changes connectivity in the aligned-entity context
graph.

**43 — Formal schema comparison.** Compares OWL/SHACL node shapes, declared
classes, declared object/datatype/annotation properties, SHACL range
semantics, constraints, hierarchy size, and depth. Unlike Figures 18–20, it
parses formal schema artifacts rather than only instance-level predicate
usage. In particular, it makes visible that YAGO expresses its property
semantics through SHACL constraints rather than OWL property declarations.

**44 — Predicate connectivity.** Shows selected formal
domain-class → object-property → range-class signatures from both schemas.
Table 29 retains every extracted object and datatype signature.

**45 — Confidence by entity type.** Compares ABC-score distributions for
ranked ambiguous alignments while excluding synthetic high-score proxy rows.
It reveals materially different score regimes across entity types.

**46 — RDF export composition.** Decomposes each serialization into direct
identity assertions, reification structure, numerical evidence, and
categorical metadata, explaining all 26,311,805 exported triples.

**47 — Relation rank–frequency.** Plots every predicate observed in each
complete held-out graph by frequency rank on log–log axes. It exposes the full
long tail beyond the top-predicate view without claiming that a Zipf model was
statistically fitted.

**48 — Degree CCDF.** Shows the probability that an evaluation-graph entity
has degree at least a given threshold. This tail-oriented view complements the
degree-frequency plot in Figure 22 and uses exactly the same documented graph
scope.

**49 — Predicate namespaces and entropy.** Decomposes held-out predicate
occurrences by RDF namespace and reports normalized Shannon entropy. It shows
both vocabulary provenance and frequency diversity, complementing the
Lorenz/Gini analysis.

**50 — PBG partitioning scale.** Compares the exact entity partitions,
possible partition-pair buckets, and arithmetic average entities/triples per
partition unit for YAGO and SemOpenAlex. These averages explain configuration
scale but are not presented as measured per-bucket load distributions.

**51 — Link-prediction trade-off.** Places each model by final MRR and Hits@10,
with AUC encoded by bubble area and printed explicitly. Separate YAGO and
SemOpenAlex panels make the empirical DistMult selection immediately visible.

**52 — Hits@K curves.** Connects the three K values actually reported by
`torchbiggraph_eval`: Hits@1, Hits@10, and Hits@50. It shows how quickly each
model recovers the correct entity as the allowed rank expands.

**53 — Rank-band composition.** Decomposes each evaluation into rank 1, ranks
2–10, ranks 11–50, and ranks above 50 using the reported cumulative Hits@K
rates. These are aggregate bands, not reconstructed per-triple ranks.

## Table catalog

The 38 CSV files in `07_export/visualizations/tables/` contain the exact values
behind the figures and are preferable to extracting numbers from SVGs.
`THESIS_TABLES.md` provides a combined human-readable preview.

**01 — Dataset statistics.** Exact entities, relations, structural triples,
and text-row counts for both datasets; this is the authoritative scale table.

**02 — Link prediction.** Model-level loss, rank, MRR, Hits@k, AUC, and test
counts; this supports the embedding-model selection.

**03 — Candidate attrition.** Counts at each candidate-generation and
filtering stage; this supports the pipeline reduction narrative.

**04 — Threshold sweep.** Candidate and type-filter outcomes for every tested
threshold; this records the operating-point trade-off.

**05 — System comparison.** Final sizes, proxy diagnostics, overlaps, types,
and weak-score counts across systems; this is the principal ablation table.

**06 — Sensitivity.** Results for alternative ABC weights and thresholds; this
shows whether the selected configuration is stable.

**07 — Evidence descriptives.** Count, mean, deviation, median, minimum, and
maximum for every evidence score by decision group; this provides exact
distribution summaries.

**08 — Final type distribution.** Final counts and fractions by SemOpenAlex
type; this records catalog composition.

**09 — Relation distribution.** Predicate counts, shares, and cumulative
shares by graph; this is the numerical basis for Figures 02–03 and 18.

**10 — Semantic rejections.** Rejected YAGO-profile/SemOpenAlex-type
combinations; this is the numerical basis for the rejection heatmap.

**11 — Sample graph statistics.** Nodes, edges, degree, density, and component
counts for the documented evaluation graphs; its scope must remain attached to
any quoted value.

**12 — Type profiles.** Observed `rdf:type` classes and counts by dataset; this
supports ontology-profile comparisons.

**13 — Proxy gold by type.** Proxy totals, recovered pairs, and recall-like
rates by type; these are silver-standard diagnostics, not human recall.

**14 — Final alignment matrix.** Exact YAGO-profile to SemOpenAlex-type counts;
this supports the type matrix and aggregate flow.

**15 — Top ambiguous labels.** Normalized labels and their target frequencies;
this identifies the largest ambiguity blocks.

**16 — Baseline source composition.** Counts and shares for strict proxy versus
embedding-ranked baseline links; this separates baseline provenance.

**17 — Baseline type composition.** Baseline alignment counts by type; this
documents its author-heavy composition.

**18 — Final score histogram.** ABC-score bins by source group; this exposes
the mixture of proxy and ranked-ambiguous scores.

**19 — Entity-type evolution.** Type counts for every evaluated system; this
quantifies the changes visualized in Figure 33.

**20 — Evidence correlations.** Pairwise Pearson correlations and cohort
sample sizes; this provides the exact values behind Figure 34.

**21 — External identifier validation.** Checkable counts, QID agreements, and
agreement rates by type and source; selection bias prevents interpreting it as
global precision.

**22 — RDF processing outcomes.** Processed statement counts and shares by
outcome and graph; this documents transformation yield.

**23 — Target catalog coverage.** Catalog sizes, aligned counts, and coverage
rates by type; this provides exact target-side coverage.

**24 — Bipartite alignment flows.** Exact YAGO-profile/SemOpenAlex-type flow
counts used by Figure 38.

**25 — SemOpenAlex PBG training.** Weighted loss, percentile band, epoch,
model, and partition count; this records the complete training summary.

**26 — Neighbor preservation.** Evaluable counts, Jaccard summaries, and
shared-neighbor rates by type and source; this is the numerical basis for
Figure 41.

**27 — Bridge topology.** Before/after nodes, edges, identity bridges,
components, and component sizes; this is the numerical basis for Figure 42.

**28 — Formal schema inventory.** Exact core-schema, property, namespace, and
class-hierarchy metrics for both graphs; this supports Figure 43.

**29 — Semantic predicate signatures.** Complete SHACL-derived domain,
predicate, range, property-kind, URI, and namespace records behind Figure 44.

**30 — Ontology source provenance.** Paths and SHA-256 hashes for all parsed
schema sources, making the comparison auditable.

**31 — Confidence by entity type.** Ranked-ambiguous counts, means, quantiles,
and extrema by type; this supplies the exact values behind Figure 45.

**32 — RDF export composition.** Triples per alignment, total triples, shares,
and contents for each semantic export group; this supports Figure 46.

**33 — Relation rank–frequency.** Complete frequency rank, URI, occurrence,
share, and cumulative-share records behind Figure 47.

**34 — Degree CCDF.** Degree thresholds, point counts, tail counts, and tail
probabilities behind Figure 48.

**35 — Predicate namespace composition.** Held-out occurrences and shares by
predicate namespace behind the left panel of Figure 49.

**36 — Predicate entropy.** Shannon entropy, normalized entropy, effective
predicate count, observed predicate count, and Gini coefficient by graph.

**37 — PBG partitioning scale.** Exact configurations, dataset totals,
arithmetic partition averages, and checkpoint partition-file sizes behind
Figure 50.

**38 — Link-prediction rank bands.** Dataset, model, reported-rate-derived
rank-band share, and evaluation-set size behind Figure 53. Figures 51–52 use
the authoritative final metrics already preserved in Table 02.

## Why `owl:sameAs`

The purpose of the alignment pipeline is to identify entities in YAGO and SemOpenAlex that refer to the same real-world object.

For this reason the exported links use the standard Semantic Web identity relation:

```text
owl:sameAs
```

During earlier stages of the pipeline several intermediate relations and scoring mechanisms were used for candidate generation, embedding ranking, profile refinement, and graph-neighbor consistency analysis.

Only the final selected alignments are exported as RDF identity links.

## Summary

*This stage converts the final experimentally selected YAGO–SemOpenAlex
alignments into RDF, preserves each direct `owl:sameAs` assertion, and records
its evidence on a stable reified alignment resource. It also provides the
reproducible analysis, native tables, interactive inspection, and validation
artifacts needed to interpret those links without confusing automatic
integrity checks or proxy labels with human-verified correctness.*
