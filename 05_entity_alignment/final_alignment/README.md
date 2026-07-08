# Stage 05 final alignment

This directory contains the authoritative taxonomy-aware Stage 05 alignment.
It classifies YAGO entities from explicit RDF class objects and transitive
`rdfs:subClassOf` ancestry in the local YAGO taxonomy.

## Type policies

Both policies start from the same Stage 05 candidate alignment:

- `permissive` rejects known incompatibilities but retains explicitly
  unresolved (`other_typed` or `untyped`) rows;
- `strict` retains only rows with positive compatible type evidence.

The thesis pipeline uses the strict result:

```text
05_entity_alignment/final_alignment/outputs/strict/alignments_FINAL_tfidf.tsv
```

It contains 1,755,590 one-to-one alignments. Its final audit reports only
resolved, type-compatible pairs.

Each policy directory also contains:

- `typefiltered.tsv` and `typefiltered_rejected.tsv`;
- `type_filter_summary.json`;
- recomputed `tfidf_input.tsv` and `tfidf_scores.tsv`;
- `evaluation_summary.tsv`;
- type and source distributions; and
- `final_type_audit.json`.

TF-IDF is recomputed after type filtering so every accepted ranked row receives
the correct profile score.

## Type evidence

The classifier follows transitive `rdfs:subClassOf` links from explicit YAGO
RDF classes to broad Schema.org roots. Multiple inheritance is preserved.
Every profile records one of:

- `taxonomy`;
- `predicate_fallback`;
- `typed_unmapped`; or
- `no_rdf_type`.

The alignment output never uses the ambiguous type value `unknown`. Lack of
positive type evidence remains explicit, and the strict policy excludes it.

The taxonomy inventory is:

```text
05_entity_alignment/final_alignment/outputs/yago_taxonomy_structure.json
```

## Run order

The Stage 05 profile job creates the shared ambiguous candidate pool if it is
missing, then builds the taxonomy profiles. From `KGAlignment/`:

```bash
jid05p=$(sbatch --parsable \
  05_entity_alignment/final_alignment/scripts/01_build_profiles.sbatch)

jid05=$(sbatch --parsable --dependency=afterok:$jid05p \
  05_entity_alignment/final_alignment/scripts/02_run_stage05.sbatch)
```

Profile construction is restart-safe: completed evidence and profile files are
reused when they are non-empty.

After completion, inspect:

```bash
cat 05_entity_alignment/final_alignment/outputs/profile_build_audit.json
cat 05_entity_alignment/final_alignment/outputs/profile_type_audit.json
cat 05_entity_alignment/final_alignment/outputs/strict/evaluation_summary.tsv
cat 05_entity_alignment/final_alignment/outputs/strict/final_type_audit.json
```

## Tests

Run in the project PBG environment:

```bash
python -m unittest discover \
  -s 05_entity_alignment/final_alignment/tests -v
```

The tests cover taxonomy ancestry, multiple inheritance, and explicit
unmapped/untyped states.
