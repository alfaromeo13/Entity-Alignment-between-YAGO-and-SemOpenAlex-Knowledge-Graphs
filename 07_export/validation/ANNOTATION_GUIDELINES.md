# Human annotation guidelines

## Question to answer

For each sampled pair, answer:

> Do the YAGO URI and SemOpenAlex URI denote the same real-world entity?

The labels being equal is candidate evidence, not proof. Ignore the model score
and selection source while judging; those fields are deliberately absent from
`annotation.tsv`.

## Verdicts

- `correct`: the available evidence identifies the same entity.
- `incorrect`: the evidence identifies different entities.
- `uncertain`: the available evidence cannot distinguish identity from a
  plausible namesake, or one side lacks enough information.

Prefer `uncertain` over guessing. Precision excludes uncertain rows and reports
their rate separately.

## Evidence standard

Use at least one identity-bearing fact beyond the shared name whenever
possible. Strong evidence includes an exact ORCID, DOI, ROR, ISSN, Wikidata QID
or another curated identifier. Otherwise compare several independent facts:

- author: affiliation, field, coauthors, works, dates or ORCID;
- work: title plus authors, year, venue and DOI;
- institution/funder/publisher/source: location, parent organization, website,
  acronym and external identifier;
- concept/topic/field: definition, broader/narrower concepts and disciplinary
  scope.

Record the strongest independent pages in `evidence_url_1` and
`evidence_url_2`. A YAGO page and a SemOpenAlex page are useful inspection
pages, but two pages repeating the same upstream identifier are not two
independent sources.

## Error categories

Assign exactly one primary category to each `incorrect` row:

- `name_ambiguity`: distinct entities share the same or a near-identical name.
- `incomplete_metadata`: the system selected the wrong entity because useful
  discriminating metadata was absent.
- `missing_neighbors`: graph context that would separate the entities was
  absent or too sparse.
- `ontology_mismatch`: the graphs conceptualize or scope the named thing
  differently (for example, a series versus a journal).
- `type_mismatch`: the pair clearly belongs to incompatible entity types.
- `noisy_source_data`: malformed, conflated or demonstrably wrong source
  records caused the alignment.
- `other`: none of the above; explain the cause in `notes`.

Choose the immediate primary failure, not every contributing condition.

## Review protocol

For a thesis-quality result:

1. freeze the generated sample and key before annotation;
2. have a second annotator independently judge at least 20% (ideally all);
3. discuss disagreements only after both independent sheets are saved;
4. report raw agreement and Cohen's kappa from the summary script;
5. preserve uncertain rows and evidence URLs in the archived study artifact;
6. never edit `sample_key.tsv` or replace difficult rows.

If disagreements are adjudicated, retain both original sheets and save the
adjudicated sheet as a third file with the adjudicator named.

