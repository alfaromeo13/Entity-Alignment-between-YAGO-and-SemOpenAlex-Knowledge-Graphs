# SPARQL examples for `kgalign_merged`

These queries are the maintained GraphDB query bank for the merged KGAlignment
repository. They assume that the repository contains:

- YAGO RDF;
- SemOpenAlex RDF;
- the final alignment graph from
  `07_export/rdf_alignments/final_alignments.trig`.

The final alignment graph is:

```text
https://kgalign.example.org/graph/final-alignments
```

The exported direct identity links have this direction:

```text
YAGO entity  owl:sameAs  SemOpenAlex entity
```

Each direct `owl:sameAs` link also has a reified `kg:Alignment` metadata
resource with source, confidence tier, scores, and SemOpenAlex type.

Performance note: the merged repository is very large. Avoid `ORDER BY RAND()`
and graph-wide negative checks during interactive work unless they are really
needed. Prefer the bounded queries below.

## Query index

| No. | Purpose |
|---:|---|
| 1 | Import sanity counts |
| 2 | URI direction sample |
| 3 | One-to-one violation check |
| 4 | Source/confidence summary |
| 5 | SemOpenAlex type distribution |
| 6 | SemOpenAlex--YAGO type crosswalk |
| 7 | Manual inspection sample |
| 8 | Metadata for one selected alignment |
| 9 | Compact thesis-safe institution graph |
| 10 | Verified two-bridge thesis graph |
| 11 | External Wikidata/QID agreement examples |
| 12 | Borderline or suspicious alignments |

## 1. Import sanity counts

Expected result for the final export:

- direct `owl:sameAs` links: `1,973,194`;
- `kg:Alignment` metadata records: `1,973,194`;
- unique YAGO entities: `1,973,194`;
- unique SemOpenAlex entities: `1,973,194`.

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX kg:  <https://kgalign.example.org/schema/>

SELECT ?sameAsLinks ?metadataRecords ?uniqueYagoEntities ?uniqueSemOpenAlexEntities
WHERE {
  {
    SELECT (COUNT(*) AS ?sameAsLinks)
    WHERE {
      GRAPH <https://kgalign.example.org/graph/final-alignments> {
        ?yago owl:sameAs ?semopenalex .
      }
    }
  }

  {
    SELECT (COUNT(*) AS ?metadataRecords)
    WHERE {
      GRAPH <https://kgalign.example.org/graph/final-alignments> {
        ?alignment a kg:Alignment .
      }
    }
  }

  {
    SELECT
      (COUNT(DISTINCT ?yago) AS ?uniqueYagoEntities)
      (COUNT(DISTINCT ?semopenalex) AS ?uniqueSemOpenAlexEntities)
    WHERE {
      GRAPH <https://kgalign.example.org/graph/final-alignments> {
        ?yago owl:sameAs ?semopenalex .
      }
    }
  }
}
```

## 2. URI direction sample

This is a fast visual sanity check. Subjects should be YAGO resources and
objects should be SemOpenAlex resources.

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?yago ?semopenalex
WHERE {
  GRAPH <https://kgalign.example.org/graph/final-alignments> {
    ?yago owl:sameAs ?semopenalex .
  }
}
LIMIT 20
```

## 3. One-to-one violation check

Expected result: no rows.

This checks both directions of the final one-to-one constraint.

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?side ?entity ?matches
WHERE {
  {
    SELECT ("YAGO side" AS ?side) (?yago AS ?entity)
           (COUNT(DISTINCT ?semopenalex) AS ?matches)
    WHERE {
      GRAPH <https://kgalign.example.org/graph/final-alignments> {
        ?yago owl:sameAs ?semopenalex .
      }
    }
    GROUP BY ?yago
    HAVING (COUNT(DISTINCT ?semopenalex) > 1)
  }
  UNION
  {
    SELECT ("SemOpenAlex side" AS ?side) (?semopenalex AS ?entity)
           (COUNT(DISTINCT ?yago) AS ?matches)
    WHERE {
      GRAPH <https://kgalign.example.org/graph/final-alignments> {
        ?yago owl:sameAs ?semopenalex .
      }
    }
    GROUP BY ?semopenalex
    HAVING (COUNT(DISTINCT ?yago) > 1)
  }
}
ORDER BY DESC(?matches)
LIMIT 100
```

## 4. Source/confidence summary

Use this for the thesis table describing where final links came from and how
they were classified.

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX kg:  <https://kgalign.example.org/schema/>

SELECT ?source ?confidence
       (COUNT(*) AS ?alignments)
       (AVG(?abcScore) AS ?meanABC)
       (MIN(?abcScore) AS ?minABC)
       (MAX(?abcScore) AS ?maxABC)
WHERE {
  GRAPH <https://kgalign.example.org/graph/final-alignments> {
    ?alignment a kg:Alignment ;
               kg:source ?source ;
               kg:confidence ?confidence ;
               kg:abcScore ?abcScore .
  }
}
GROUP BY ?source ?confidence
ORDER BY ?source ?confidence
```

## 5. SemOpenAlex type distribution

Use this for the final alignment composition by SemOpenAlex entity type.

```sparql
PREFIX kg: <https://kgalign.example.org/schema/>

SELECT ?semopenalexType (COUNT(*) AS ?alignments)
WHERE {
  GRAPH <https://kgalign.example.org/graph/final-alignments> {
    ?alignment a kg:Alignment ;
               kg:semopenalexType ?semopenalexType .
  }
}
GROUP BY ?semopenalexType
ORDER BY DESC(?alignments)
```

## 6. SemOpenAlex--YAGO type crosswalk

This summarizes which YAGO RDF classes appear most often for each SemOpenAlex
type. It is useful for discussing schema heterogeneity.

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX kg:  <https://kgalign.example.org/schema/>

SELECT ?semopenalexType ?yagoType (COUNT(DISTINCT ?yago) AS ?alignedEntities)
WHERE {
  GRAPH <https://kgalign.example.org/graph/final-alignments> {
    ?alignment a kg:Alignment ;
               rdf:subject ?yago ;
               kg:semopenalexType ?semopenalexType .
  }

  {
    ?yago rdf:type ?yagoType .
  }
  UNION {
    GRAPH ?g {
      ?yago rdf:type ?yagoType .
    }
  }
}
GROUP BY ?semopenalexType ?yagoType
ORDER BY ?semopenalexType DESC(?alignedEntities)
LIMIT 100
```

## 7. Manual inspection sample

Use this to inspect high-confidence examples with labels and scores. Change the
`VALUES ?semopenalexType` block to inspect another entity type.

```sparql
PREFIX owl:     <http://www.w3.org/2002/07/owl#>
PREFIX rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos:    <http://www.w3.org/2004/02/skos/core#>
PREFIX schema:  <http://schema.org/>
PREFIX schemas: <https://schema.org/>
PREFIX foaf:    <http://xmlns.com/foaf/0.1/>
PREFIX kg:      <https://kgalign.example.org/schema/>

SELECT ?semopenalexType ?yago ?yagoLabel ?semopenalex ?semopenalexLabel
       ?abcScore ?embeddingScore ?profileScore ?neighborScore
       ?source ?confidence
WHERE {
  {
    SELECT ?semopenalexType ?yago ?semopenalex
           ?abcScore ?embeddingScore ?profileScore ?neighborScore
           ?source ?confidence
    WHERE {
      VALUES ?semopenalexType {
        "institution"
      }

      GRAPH <https://kgalign.example.org/graph/final-alignments> {
        ?alignment a kg:Alignment ;
                   rdf:subject ?yago ;
                   rdf:predicate owl:sameAs ;
                   rdf:object ?semopenalex ;
                   kg:semopenalexType ?semopenalexType ;
                   kg:abcScore ?abcScore ;
                   kg:embeddingScore ?embeddingScore ;
                   kg:profileTfidfScore ?profileScore ;
                   kg:neighborTfidfScore ?neighborScore ;
                   kg:source ?source ;
                   kg:confidence ?confidence .

        FILTER(?confidence = "high_confidence" || ?confidence = "strict_proxy_gold")
      }
    }
    LIMIT 100
  }

  OPTIONAL {
    { ?yago ?yp ?rawYagoLabel . }
    UNION { GRAPH ?yg { ?yago ?yp ?rawYagoLabel . } }
    VALUES ?yp { rdfs:label skos:prefLabel schema:name schemas:name foaf:name }
    FILTER(LANG(?rawYagoLabel) = "" || LANGMATCHES(LANG(?rawYagoLabel), "en"))
  }

  OPTIONAL {
    { ?semopenalex ?sp ?rawSemopenalexLabel . }
    UNION { GRAPH ?sg { ?semopenalex ?sp ?rawSemopenalexLabel . } }
    VALUES ?sp { rdfs:label skos:prefLabel schema:name schemas:name foaf:name }
    FILTER(LANG(?rawSemopenalexLabel) = "" || LANGMATCHES(LANG(?rawSemopenalexLabel), "en"))
  }

  BIND(COALESCE(?rawYagoLabel, STRAFTER(STR(?yago), "/resource/")) AS ?yagoLabel)
  BIND(COALESCE(?rawSemopenalexLabel, STRAFTER(STR(?semopenalex), "https://semopenalex.org/")) AS ?semopenalexLabel)
}
LIMIT 100
```

## 8. Metadata for one selected alignment

This query inspects the exported metadata for one known alignment. Replace the
two IRIs to inspect another pair.

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX kg:  <https://kgalign.example.org/schema/>

SELECT ?predicate ?value
WHERE {
  GRAPH <https://kgalign.example.org/graph/final-alignments> {
    ?alignment a kg:Alignment ;
               rdf:subject <http://yago-knowledge.org/resource/Harvard_Stem_Cell_Institute_Q40771227> ;
               rdf:predicate owl:sameAs ;
               rdf:object <https://semopenalex.org/institution/I4210157861> ;
               ?predicate ?value .
  }
}
ORDER BY ?predicate ?value
```

## 9. Compact thesis-safe institution graph

This is the safest GraphDB visualization query. It avoids author identity links
and shows one institution bridge plus YAGO type/location context and one
SemOpenAlex work/authorship/author chain.

```sparql
PREFIX owl:     <http://www.w3.org/2002/07/owl#>
PREFIX rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dct:     <http://purl.org/dc/terms/>
PREFIX schema:  <http://schema.org/>
PREFIX schemas: <https://schema.org/>
PREFIX foaf:    <http://xmlns.com/foaf/0.1/>
PREFIX soa:     <https://semopenalex.org/ontology/>
PREFIX kg:      <https://kgalign.example.org/schema/>

CONSTRUCT {
  ?yagoInstNode owl:sameAs ?soaInstNode .
  ?yagoInstNode rdf:type ?instTypeNode .
  ?yagoInstNode schema:location ?instLocationNode .

  ?workNode soa:hasAuthorship ?authorshipNode .
  ?authorshipNode soa:hasOrganization ?soaInstNode .
  ?authorshipNode soa:hasAuthor ?authorNode .

  ?yagoInstNode rdfs:label ?yagoInstLabel .
  ?soaInstNode rdfs:label ?soaInstLabel .
  ?instTypeNode rdfs:label ?instTypeLabel .
  ?instLocationNode rdfs:label ?instLocationLabel .
  ?workNode rdfs:label ?workLabel .
  ?authorshipNode rdfs:label ?authorshipLabel .
  ?authorNode rdfs:label ?authorLabel .
}
WHERE {
  VALUES (?realYagoInst ?realSoaInst) {
    (
      <http://yago-knowledge.org/resource/Harvard_Stem_Cell_Institute_Q40771227>
      <https://semopenalex.org/institution/I4210157861>
    )
  }

  GRAPH <https://kgalign.example.org/graph/final-alignments> {
    ?alignment a kg:Alignment ;
               rdf:subject ?realYagoInst ;
               rdf:object ?realSoaInst ;
               kg:semopenalexType "institution" .
    ?realYagoInst owl:sameAs ?realSoaInst .
  }

  {
    SELECT DISTINCT ?realWork ?realAuthorship ?realSoaAuthor
    WHERE {
      VALUES ?realSoaInst {
        <https://semopenalex.org/institution/I4210157861>
      }

      ?realAuthorship soa:hasOrganization ?realSoaInst ;
                      soa:hasAuthor ?realSoaAuthor .
      ?realWork soa:hasAuthorship ?realAuthorship .
    }
    ORDER BY ?realWork ?realSoaAuthor
    LIMIT 1
  }

  OPTIONAL {
    {
      SELECT ?realYagoInst (SAMPLE(?candidateInstType) AS ?realInstType)
      WHERE {
        VALUES ?realYagoInst {
          <http://yago-knowledge.org/resource/Harvard_Stem_Cell_Institute_Q40771227>
        }

        ?realYagoInst rdf:type ?candidateInstType .
        FILTER(
          !CONTAINS(LCASE(STR(?candidateInstType)), "wikicat")
          && (
            CONTAINS(LCASE(STR(?candidateInstType)), "research")
            || CONTAINS(LCASE(STR(?candidateInstType)), "institute")
            || CONTAINS(LCASE(STR(?candidateInstType)), "organization")
          )
        )
      }
      GROUP BY ?realYagoInst
    }
  }

  OPTIONAL {
    {
      SELECT ?realYagoInst (SAMPLE(?candidateInstLocation) AS ?realInstLocation)
      WHERE {
        VALUES ?realYagoInst {
          <http://yago-knowledge.org/resource/Harvard_Stem_Cell_Institute_Q40771227>
        }

        ?realYagoInst ?instLocationPredicate ?candidateInstLocation .
        VALUES ?instLocationPredicate { schema:location schemas:location }
        FILTER(isIRI(?candidateInstLocation))
      }
      GROUP BY ?realYagoInst
    }
  }

  OPTIONAL {
    ?realYagoInst ?yagoInstLabelPredicate ?rawYagoInstLabel .
    VALUES ?yagoInstLabelPredicate { rdfs:label schema:name schemas:name foaf:name }
    FILTER(LANG(?rawYagoInstLabel) = "" || LANGMATCHES(LANG(?rawYagoInstLabel), "en"))
  }

  OPTIONAL {
    ?realSoaInst ?soaInstLabelPredicate ?rawSoaInstLabel .
    VALUES ?soaInstLabelPredicate { rdfs:label schema:name schemas:name foaf:name }
    FILTER(LANG(?rawSoaInstLabel) = "" || LANGMATCHES(LANG(?rawSoaInstLabel), "en"))
  }

  OPTIONAL {
    ?realWork dct:title ?rawWorkLabel .
    FILTER(LANG(?rawWorkLabel) = "" || LANGMATCHES(LANG(?rawWorkLabel), "en"))
  }

  OPTIONAL {
    ?realSoaAuthor foaf:name ?rawAuthorLabel .
    FILTER(LANG(?rawAuthorLabel) = "" || LANGMATCHES(LANG(?rawAuthorLabel), "en"))
  }

  BIND(REPLACE(REPLACE(STRAFTER(STR(?realYagoInst), "/resource/"), "_Q[0-9]+$", ""), "_", " ") AS ?fallbackInstName)
  BIND(IF(BOUND(?rawYagoInstLabel), STR(?rawYagoInstLabel), ?fallbackInstName) AS ?yagoName)
  BIND(IF(BOUND(?rawSoaInstLabel), STR(?rawSoaInstLabel), ?fallbackInstName) AS ?soaName)

  BIND(IF(BOUND(?rawWorkLabel), STR(?rawWorkLabel), STRAFTER(STR(?realWork), "https://semopenalex.org/work/")) AS ?rawWorkName)
  BIND(IF(STRLEN(?rawWorkName) > 55, CONCAT(SUBSTR(?rawWorkName, 1, 55), "..."), ?rawWorkName) AS ?shortWorkName)
  BIND(IF(BOUND(?rawAuthorLabel), STR(?rawAuthorLabel), STRAFTER(STR(?realSoaAuthor), "https://semopenalex.org/author/")) AS ?rawAuthorName)

  BIND(REPLACE(REPLACE(?yagoName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?instSlug)
  BIND(REPLACE(REPLACE(?shortWorkName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?workSlug)
  BIND(REPLACE(REPLACE(?rawAuthorName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?authorSlug)
  BIND(STRAFTER(STR(?realSoaInst), "https://semopenalex.org/institution/") AS ?soaInstId)
  BIND(STRAFTER(STR(?realAuthorship), "https://semopenalex.org/") AS ?authorshipId)

  BIND(IRI(CONCAT("http://yago-knowledge.org/visual/YAGO_", ?instSlug)) AS ?yagoInstNode)
  BIND(IRI(CONCAT("https://semopenalex.org/visual/SOA_", ?instSlug, "_", ?soaInstId)) AS ?soaInstNode)
  BIND(IRI(CONCAT("https://semopenalex.org/visual/SOA_work_", ?workSlug)) AS ?workNode)
  BIND(IRI(CONCAT("https://semopenalex.org/visual/SOA_authorship_", ENCODE_FOR_URI(?authorshipId))) AS ?authorshipNode)
  BIND(IRI(CONCAT("https://semopenalex.org/visual/SOA_author_", ?authorSlug)) AS ?authorNode)

  OPTIONAL {
    FILTER(BOUND(?realInstType))
    BIND(REPLACE(REPLACE(STRAFTER(STR(?realInstType), "/resource/"), "_Q[0-9]+$", ""), "_", " ") AS ?instTypeName)
    BIND(REPLACE(REPLACE(?instTypeName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?instTypeSlug)
    BIND(IRI(CONCAT("http://yago-knowledge.org/visual/YAGO_type_", ?instTypeSlug)) AS ?instTypeNode)
    BIND(STRLANG(CONCAT("YAGO type: ", ?instTypeName), "en") AS ?instTypeLabel)
  }

  OPTIONAL {
    FILTER(BOUND(?realInstLocation))
    BIND(REPLACE(REPLACE(STRAFTER(STR(?realInstLocation), "/resource/"), "_Q[0-9]+$", ""), "_", " ") AS ?instLocationName)
    BIND(REPLACE(REPLACE(?instLocationName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?locationSlug)
    BIND(IRI(CONCAT("http://yago-knowledge.org/visual/YAGO_loc_", ?locationSlug)) AS ?instLocationNode)
    BIND(STRLANG(CONCAT("YAGO location: ", ?instLocationName), "en") AS ?instLocationLabel)
  }

  BIND(STRLANG(CONCAT("YAGO institution: ", ?yagoName), "en") AS ?yagoInstLabel)
  BIND(STRLANG(CONCAT("SemOpenAlex institution: ", ?soaName), "en") AS ?soaInstLabel)
  BIND(STRLANG(CONCAT("SemOpenAlex work: ", ?shortWorkName), "en") AS ?workLabel)
  BIND(STRLANG("SemOpenAlex authorship", "en") AS ?authorshipLabel)
  BIND(STRLANG(CONCAT("SemOpenAlex author: ", ?rawAuthorName), "en") AS ?authorLabel)
}
LIMIT 50
```

## 10. Verified two-bridge thesis graph

This is the richer optional thesis visualization. It contains two accepted
`owl:sameAs` bridges:

- Harvard Stem Cell Institute:
  `Q40771227` / `I4210157861`;
- Rui Kuai:
  `Q61131091` / `A5020101838`, checked externally through ORCID
  `0000-0003-2324-1272`.

Use this graph only as a qualitative inspection example.

```sparql
PREFIX owl:     <http://www.w3.org/2002/07/owl#>
PREFIX rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dct:     <http://purl.org/dc/terms/>
PREFIX schema:  <http://schema.org/>
PREFIX schemas: <https://schema.org/>
PREFIX foaf:    <http://xmlns.com/foaf/0.1/>
PREFIX soa:     <https://semopenalex.org/ontology/>
PREFIX kg:      <https://kgalign.example.org/schema/>

CONSTRUCT {
  ?yagoInstNode owl:sameAs ?soaInstNode .
  ?yagoInstNode rdf:type ?instTypeNode .
  ?yagoInstNode schema:location ?instLocationNode .

  ?workNode soa:hasAuthorship ?authorshipNode .
  ?authorshipNode soa:hasOrganization ?soaInstNode .
  ?authorshipNode soa:hasAuthor ?soaAuthorNode .

  ?yagoAuthorNode owl:sameAs ?soaAuthorNode .
  ?yagoAuthorNode rdf:type ?authorTypeNode .
  ?yagoAuthorNode ?authorContextPredicate ?authorContextNode .

  ?yagoInstNode rdfs:label ?yagoInstLabel .
  ?soaInstNode rdfs:label ?soaInstLabel .
  ?instTypeNode rdfs:label ?instTypeLabel .
  ?instLocationNode rdfs:label ?instLocationLabel .
  ?workNode rdfs:label ?workLabel .
  ?authorshipNode rdfs:label ?authorshipLabel .
  ?soaAuthorNode rdfs:label ?soaAuthorLabel .
  ?yagoAuthorNode rdfs:label ?yagoAuthorLabel .
  ?authorTypeNode rdfs:label ?authorTypeLabel .
  ?authorContextNode rdfs:label ?authorContextLabel .
}
WHERE {
  VALUES (?realYagoInst ?realSoaInst) {
    (
      <http://yago-knowledge.org/resource/Harvard_Stem_Cell_Institute_Q40771227>
      <https://semopenalex.org/institution/I4210157861>
    )
  }

  GRAPH <https://kgalign.example.org/graph/final-alignments> {
    ?instAlignment a kg:Alignment ;
                   rdf:subject ?realYagoInst ;
                   rdf:object ?realSoaInst ;
                   kg:semopenalexType "institution" .
    ?realYagoInst owl:sameAs ?realSoaInst .
  }

  {
    SELECT DISTINCT ?realWork ?realAuthorship ?realSoaAuthor ?realYagoAuthor
    WHERE {
      VALUES ?realSoaInst {
        <https://semopenalex.org/institution/I4210157861>
      }

      ?realAuthorship soa:hasOrganization ?realSoaInst ;
                      soa:hasAuthor ?realSoaAuthor .
      ?realWork soa:hasAuthorship ?realAuthorship .
      ?realSoaAuthor foaf:name ?candidateAuthorName .
      FILTER(LCASE(STR(?candidateAuthorName)) = "rui kuai")

      GRAPH <https://kgalign.example.org/graph/final-alignments> {
        ?authorAlignment a kg:Alignment ;
                         rdf:subject ?realYagoAuthor ;
                         rdf:object ?realSoaAuthor ;
                         kg:semopenalexType "author" ;
                         kg:confidence "strict_proxy_gold" .
        ?realYagoAuthor owl:sameAs ?realSoaAuthor .
      }
    }
    ORDER BY ?realWork
    LIMIT 1
  }

  OPTIONAL {
    {
      SELECT ?realYagoInst (SAMPLE(?candidateInstType) AS ?realInstType)
      WHERE {
        VALUES ?realYagoInst {
          <http://yago-knowledge.org/resource/Harvard_Stem_Cell_Institute_Q40771227>
        }

        ?realYagoInst rdf:type ?candidateInstType .
        FILTER(
          !CONTAINS(LCASE(STR(?candidateInstType)), "wikicat")
          && (
            CONTAINS(LCASE(STR(?candidateInstType)), "research")
            || CONTAINS(LCASE(STR(?candidateInstType)), "institute")
            || CONTAINS(LCASE(STR(?candidateInstType)), "organization")
          )
        )
      }
      GROUP BY ?realYagoInst
    }
  }

  OPTIONAL {
    {
      SELECT ?realYagoInst (SAMPLE(?candidateInstLocation) AS ?realInstLocation)
      WHERE {
        VALUES ?realYagoInst {
          <http://yago-knowledge.org/resource/Harvard_Stem_Cell_Institute_Q40771227>
        }

        ?realYagoInst ?instLocationPredicate ?candidateInstLocation .
        VALUES ?instLocationPredicate { schema:location schemas:location }
        FILTER(isIRI(?candidateInstLocation))
      }
      GROUP BY ?realYagoInst
    }
  }

  OPTIONAL {
    ?realYagoAuthor rdf:type ?realAuthorType .
    FILTER(!CONTAINS(LCASE(STR(?realAuthorType)), "wikicat"))
  }

  OPTIONAL {
    ?realYagoAuthor ?authorContextPredicate ?realAuthorContext .
    VALUES ?authorContextPredicate {
      schema:affiliation schemas:affiliation
      schema:worksFor schemas:worksFor
      schema:alumniOf schemas:alumniOf
      schema:nationality schemas:nationality
      schema:birthPlace schemas:birthPlace
      schema:memberOf schemas:memberOf
    }
    FILTER(isIRI(?realAuthorContext))
  }

  OPTIONAL {
    ?realYagoInst ?yagoInstLabelPredicate ?rawYagoInstLabel .
    VALUES ?yagoInstLabelPredicate { rdfs:label schema:name schemas:name foaf:name }
    FILTER(LANG(?rawYagoInstLabel) = "" || LANGMATCHES(LANG(?rawYagoInstLabel), "en"))
  }

  OPTIONAL {
    ?realSoaInst ?soaInstLabelPredicate ?rawSoaInstLabel .
    VALUES ?soaInstLabelPredicate { rdfs:label schema:name schemas:name foaf:name }
    FILTER(LANG(?rawSoaInstLabel) = "" || LANGMATCHES(LANG(?rawSoaInstLabel), "en"))
  }

  OPTIONAL {
    ?realWork dct:title ?rawWorkLabel .
    FILTER(LANG(?rawWorkLabel) = "" || LANGMATCHES(LANG(?rawWorkLabel), "en"))
  }

  OPTIONAL {
    ?realSoaAuthor foaf:name ?rawSoaAuthorLabel .
    FILTER(LANG(?rawSoaAuthorLabel) = "" || LANGMATCHES(LANG(?rawSoaAuthorLabel), "en"))
  }

  OPTIONAL {
    ?realYagoAuthor ?yagoAuthorLabelPredicate ?rawYagoAuthorLabel .
    VALUES ?yagoAuthorLabelPredicate { rdfs:label schema:name schemas:name foaf:name }
    FILTER(LANG(?rawYagoAuthorLabel) = "" || LANGMATCHES(LANG(?rawYagoAuthorLabel), "en"))
  }

  BIND(REPLACE(REPLACE(STRAFTER(STR(?realYagoInst), "/resource/"), "_Q[0-9]+$", ""), "_", " ") AS ?fallbackInstName)
  BIND(IF(BOUND(?rawYagoInstLabel), STR(?rawYagoInstLabel), ?fallbackInstName) AS ?yagoInstName)
  BIND(IF(BOUND(?rawSoaInstLabel), STR(?rawSoaInstLabel), ?fallbackInstName) AS ?soaInstName)

  BIND(IF(BOUND(?rawWorkLabel), STR(?rawWorkLabel), STRAFTER(STR(?realWork), "https://semopenalex.org/work/")) AS ?realWorkName)
  BIND(IF(STRLEN(?realWorkName) > 55, CONCAT(SUBSTR(?realWorkName, 1, 55), "..."), ?realWorkName) AS ?shortWorkName)
  BIND(IF(BOUND(?rawSoaAuthorLabel), STR(?rawSoaAuthorLabel), STRAFTER(STR(?realSoaAuthor), "https://semopenalex.org/author/")) AS ?soaAuthorName)

  BIND(REPLACE(REPLACE(STRAFTER(STR(?realYagoAuthor), "/resource/"), "_Q[0-9]+$", ""), "_", " ") AS ?fallbackYagoAuthorName)
  BIND(IF(BOUND(?rawYagoAuthorLabel), STR(?rawYagoAuthorLabel), ?fallbackYagoAuthorName) AS ?yagoAuthorName)

  BIND(REPLACE(REPLACE(?yagoInstName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?instSlug)
  BIND(REPLACE(REPLACE(?shortWorkName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?workSlug)
  BIND(REPLACE(REPLACE(?soaAuthorName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?soaAuthorSlug)
  BIND(REPLACE(REPLACE(?yagoAuthorName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?yagoAuthorSlug)
  BIND(STRAFTER(STR(?realSoaInst), "https://semopenalex.org/institution/") AS ?soaInstId)
  BIND(STRAFTER(STR(?realAuthorship), "https://semopenalex.org/") AS ?authorshipId)

  BIND(IRI(CONCAT("http://yago-knowledge.org/visual/YAGO_", ?instSlug)) AS ?yagoInstNode)
  BIND(IRI(CONCAT("https://semopenalex.org/visual/SOA_", ?instSlug, "_", ?soaInstId)) AS ?soaInstNode)
  BIND(IRI(CONCAT("https://semopenalex.org/visual/SOA_work_", ?workSlug)) AS ?workNode)
  BIND(IRI(CONCAT("https://semopenalex.org/visual/SOA_authorship_", ENCODE_FOR_URI(?authorshipId))) AS ?authorshipNode)
  BIND(IRI(CONCAT("https://semopenalex.org/visual/SOA_author_", ?soaAuthorSlug)) AS ?soaAuthorNode)
  BIND(IRI(CONCAT("http://yago-knowledge.org/visual/YAGO_author_", ?yagoAuthorSlug)) AS ?yagoAuthorNode)

  OPTIONAL {
    FILTER(BOUND(?realInstType))
    BIND(REPLACE(REPLACE(STRAFTER(STR(?realInstType), "/resource/"), "_Q[0-9]+$", ""), "_", " ") AS ?instTypeName)
    BIND(REPLACE(REPLACE(?instTypeName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?instTypeSlug)
    BIND(IRI(CONCAT("http://yago-knowledge.org/visual/YAGO_type_", ?instTypeSlug)) AS ?instTypeNode)
    BIND(STRLANG(CONCAT("YAGO type: ", ?instTypeName), "en") AS ?instTypeLabel)
  }

  OPTIONAL {
    FILTER(BOUND(?realInstLocation))
    BIND(REPLACE(REPLACE(STRAFTER(STR(?realInstLocation), "/resource/"), "_Q[0-9]+$", ""), "_", " ") AS ?instLocationName)
    BIND(REPLACE(REPLACE(?instLocationName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?locationSlug)
    BIND(IRI(CONCAT("http://yago-knowledge.org/visual/YAGO_loc_", ?locationSlug)) AS ?instLocationNode)
    BIND(STRLANG(CONCAT("YAGO location: ", ?instLocationName), "en") AS ?instLocationLabel)
  }

  OPTIONAL {
    FILTER(BOUND(?realAuthorType))
    BIND(REPLACE(REPLACE(STRAFTER(STR(?realAuthorType), "/resource/"), "_Q[0-9]+$", ""), "_", " ") AS ?authorTypeName)
    BIND(REPLACE(REPLACE(?authorTypeName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?authorTypeSlug)
    BIND(IRI(CONCAT("http://yago-knowledge.org/visual/YAGO_author_type_", ?authorTypeSlug)) AS ?authorTypeNode)
    BIND(STRLANG(CONCAT("YAGO author type: ", ?authorTypeName), "en") AS ?authorTypeLabel)
  }

  OPTIONAL {
    FILTER(BOUND(?realAuthorContext))
    BIND(REPLACE(REPLACE(STRAFTER(STR(?realAuthorContext), "/resource/"), "_Q[0-9]+$", ""), "_", " ") AS ?authorContextName)
    BIND(REPLACE(REPLACE(?authorContextName, "[^A-Za-z0-9]+", "_"), "(^_+|_+$)", "") AS ?authorContextSlug)
    BIND(IRI(CONCAT("http://yago-knowledge.org/visual/YAGO_author_fact_", ?authorContextSlug)) AS ?authorContextNode)
    BIND(STRLANG(CONCAT("YAGO author fact: ", ?authorContextName), "en") AS ?authorContextLabel)
  }

  BIND(STRLANG(CONCAT("YAGO institution: ", ?yagoInstName), "en") AS ?yagoInstLabel)
  BIND(STRLANG(CONCAT("SemOpenAlex institution: ", ?soaInstName), "en") AS ?soaInstLabel)
  BIND(STRLANG(CONCAT("SemOpenAlex work: ", ?shortWorkName), "en") AS ?workLabel)
  BIND(STRLANG("SemOpenAlex authorship", "en") AS ?authorshipLabel)
  BIND(STRLANG(CONCAT("SemOpenAlex author: ", ?soaAuthorName), "en") AS ?soaAuthorLabel)
  BIND(STRLANG(CONCAT("YAGO author: ", ?yagoAuthorName), "en") AS ?yagoAuthorLabel)
}
LIMIT 100
```

## 11. External Wikidata/QID agreement examples

Some YAGO IRIs retain Wikidata QIDs and some SemOpenAlex entities expose
external identifiers. This query finds examples where both sides expose the
same QID. Coverage is incomplete, so this is a partial validation query.

```sparql
PREFIX owl:     <http://www.w3.org/2002/07/owl#>
PREFIX rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX schema:  <http://schema.org/>
PREFIX schemas: <https://schema.org/>
PREFIX kg:      <https://kgalign.example.org/schema/>

SELECT ?semopenalexType ?yago ?semopenalex ?qid ?semopenalexExternalId
WHERE {
  GRAPH <https://kgalign.example.org/graph/final-alignments> {
    ?alignment a kg:Alignment ;
               rdf:subject ?yago ;
               rdf:object ?semopenalex ;
               kg:semopenalexType ?semopenalexType .
  }

  BIND(REPLACE(STR(?yago), "^.*_(Q[0-9]+)$", "$1") AS ?qid)
  FILTER(REGEX(?qid, "^Q[0-9]+$"))

  {
    ?semopenalex ?externalPredicate ?semopenalexExternalId .
  }
  UNION {
    GRAPH ?g {
      ?semopenalex ?externalPredicate ?semopenalexExternalId .
    }
  }

  VALUES ?externalPredicate {
    owl:sameAs schema:sameAs schemas:sameAs schema:identifier schemas:identifier
  }

  FILTER(CONTAINS(STR(?semopenalexExternalId), ?qid))
}
LIMIT 100
```

## 12. Borderline or suspicious alignments

Use this for limitations/error-analysis discussion. It searches for final links
with ambiguous confidence or weak evidence signals.

```sparql
PREFIX owl:     <http://www.w3.org/2002/07/owl#>
PREFIX rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos:    <http://www.w3.org/2004/02/skos/core#>
PREFIX schema:  <http://schema.org/>
PREFIX schemas: <https://schema.org/>
PREFIX foaf:    <http://xmlns.com/foaf/0.1/>
PREFIX kg:      <https://kgalign.example.org/schema/>

SELECT ?semopenalexType ?yago ?yagoLabel ?semopenalex ?semopenalexLabel
       ?abcScore ?embeddingScore ?profileScore ?neighborScore ?source ?confidence
WHERE {
  GRAPH <https://kgalign.example.org/graph/final-alignments> {
    ?alignment a kg:Alignment ;
               rdf:subject ?yago ;
               rdf:predicate owl:sameAs ;
               rdf:object ?semopenalex ;
               kg:semopenalexType ?semopenalexType ;
               kg:abcScore ?abcScore ;
               kg:embeddingScore ?embeddingScore ;
               kg:profileTfidfScore ?profileScore ;
               kg:neighborTfidfScore ?neighborScore ;
               kg:source ?source ;
               kg:confidence ?confidence .
  }

  OPTIONAL {
    { ?yago ?yp ?rawYagoLabel . }
    UNION { GRAPH ?yg { ?yago ?yp ?rawYagoLabel . } }
    VALUES ?yp { rdfs:label skos:prefLabel schema:name schemas:name foaf:name }
    FILTER(LANG(?rawYagoLabel) = "" || LANGMATCHES(LANG(?rawYagoLabel), "en"))
  }

  OPTIONAL {
    { ?semopenalex ?sp ?rawSemopenalexLabel . }
    UNION { GRAPH ?sg { ?semopenalex ?sp ?rawSemopenalexLabel . } }
    VALUES ?sp { rdfs:label skos:prefLabel schema:name schemas:name foaf:name }
    FILTER(LANG(?rawSemopenalexLabel) = "" || LANGMATCHES(LANG(?rawSemopenalexLabel), "en"))
  }

  BIND(COALESCE(?rawYagoLabel, STRAFTER(STR(?yago), "/resource/")) AS ?yagoLabel)
  BIND(COALESCE(?rawSemopenalexLabel, STRAFTER(STR(?semopenalex), "https://semopenalex.org/")) AS ?semopenalexLabel)

  FILTER(
    ?confidence = "ambiguous"
    || ?abcScore < 0.45
    || ?profileScore < 0.15
    || ?neighborScore < 0.05
  )
}
ORDER BY ?confidence ?abcScore ?semopenalexType
LIMIT 100
```
