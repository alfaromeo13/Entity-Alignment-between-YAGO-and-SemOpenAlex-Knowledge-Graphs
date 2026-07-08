# Research-question evidence map

This index maps the five questions in `Disposition of the Master.pdf` to the strongest generated evidence.

## Q1 — preprocessing and transformation

- Figures 01, 17–24, 36, 43–44 and 47–50: scale, raw RDF yield, observed predicates/types, formal ontology/schema, topology, distribution tails, namespaces and partitioning scale.
- Tables 01, 09, 11–12, 28–30 and 33–37: encoded graph, relation, observed-type, formal-schema, ontology-provenance, distribution and partition statistics.
- The methodological *how* belongs in prose; these figures establish the resulting scale and structure.

## Q2 — normalized labels as candidate generators

- Figures 06–08 and 25: candidate attrition, ambiguity tails, type-specific ambiguity and the largest label blocks.
- Figure 31: strict-label proxy versus ranked-ambiguous baseline composition.
- Labels are effective for narrowing the search space, but label equality must not be described as ground-truth identity.

## Q3 — embeddings for ambiguous candidates

- Figures 04–05, 39 and 51–53: final link-prediction comparison, model trade-offs, Hits@K/rank bands, plus YAGO and SemOpenAlex PBG training dynamics.
- Tables 02 and 38 preserve the final metrics and derived aggregate rank bands.
- Figures 09, 13–15, 26, 29, 32, 34 and 45: score selection, evidence distributions, type-specific confidence and decision-cohort interactions.
- The evidence supports candidate reranking utility, not unrestricted all-vs-all alignment.

## Q4 — type and predicate-profile filtering

- Figures 06 and 10: exact filter attrition and rejected type-pair heatmap.
- Figures 15, 28, 35 and 38: evidence/type behavior, accepted type matrix, external-ID agreement and aggregate bipartite flows.
- The very low institution/concept QID agreement identifies a limitation of the current proxy bypass and broad unknown-profile handling.

## Q5 — final scale, quality and limitations

- Figures 11–16, 26–28, 31–38 and 40: system comparison, overlap, sensitivity, score behavior, final composition, coverage, flow and concrete externally checked cases.
- Figures 41–42: alignment-aware neighborhood preservation and topology change after adding identity bridges, measured on the capped aligned-entity context graph.
- Figure 46: exact composition of the direct identity assertions, reification provenance and evidence metadata in the final RDF export.
- Tables 05–08, 13–14 and 16–38 provide the exact reportable values.
- External-QID subset: source 92.5%, publisher 94.4%, funder 80.9%, institution 3.6%, concept 0.0%.
- These rates are subset diagnostics, not overall precision. A manually annotated stratified sample is still required for a defensible absolute precision estimate.

## Remaining evidence gap

The reproducible study package in `07_export/validation/study/` contains a blinded, stratified 500-pair annotation sheet but no human verdicts yet. The remaining evaluation step is to record correct / incorrect / uncertain judgments and run the provided summary script for weighted precision, confidence intervals, score reliability and error categories.
