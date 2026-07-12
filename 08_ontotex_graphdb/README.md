# Ontotext GraphDB setup

This folder contains the Docker Compose setup used to load the final
KGAlignment RDF output into Ontotext GraphDB for SPARQL validation, graph
inspection, and qualitative visualization.

GraphDB is used only as an RDF inspection and validation environment. The main
preprocessing, embedding, alignment, and RDF export stages are implemented in
the earlier pipeline folders.

The intended repository is:

```text
kgalign_merged
```

It contains three layers in one GraphDB repository:

- YAGO RDF data;
- SemOpenAlex RDF data;
- the final YAGO--SemOpenAlex alignment graph exported as `owl:sameAs` links
  with reified metadata.

Keeping all three layers in one repository makes the final alignments usable as
explicit bridges between the two knowledge graphs.

## Files in this folder

```text
08_ontotex_graphdb/
├── docker-compose.yml
├── kgalign_merged-config.ttl
├── SPARQL_EXAMPLES.md
├── .gitignore
└── README.md
```

Tracked files:

- `docker-compose.yml` defines the GraphDB runtime container and the one-time
  offline preload container.
- `kgalign_merged-config.ttl` is the GraphDB repository template used by
  `importrdf preload`.
- `SPARQL_EXAMPLES.md` contains the focused validation and inspection query
  bank used after the repository has loaded.

Local-only files:

- `graphdb-home/` stores the GraphDB license, logs, indexes, and repository
  data. It is intentionally ignored by Git.
- `*.license` and `*.log` files are local runtime artifacts and should not be
  committed.

## Expected input data

The preload service expects these pipeline outputs to exist relative to this
folder:

```text
../01_raw/semopenalex/
../01_raw/yago/
../07_export/rdf_alignments/final_alignments.trig
```

Only the following YAGO files are loaded:

```text
yago-beyond-wikipedia.ttl
yago-facts.ttl
yago-schema.ttl
yago-taxonomy.ttl
```

The alignment input is:

```text
../07_export/rdf_alignments/final_alignments.trig
```

The TriG export is used because it preserves the named alignment graph:

```text
https://kgalign.example.org/graph/final-alignments
```

## Requirements

- Docker with Docker Compose.
- Sufficient disk space for the loaded repository.
- An Ontotext GraphDB license suitable for the repository size.

This setup is intended for a Docker-capable workstation or server. It is not an
HPC/Slurm stage.

## License setup

Start GraphDB once:

```bash
docker compose up -d graphdb
```

Open the Workbench:

```text
http://localhost:7200/
```

Add the GraphDB license through the Workbench UI. The license is stored inside:

```text
graphdb-home/work/graphdb.license
```

Then stop GraphDB before the offline preload:

```bash
docker compose stop graphdb
```

Do not run the `graphdb` and `preload` services at the same time. They share the
same `graphdb-home/` directory.

## Offline preload

Run all commands from this folder:

```bash
cd 08_ontotex_graphdb
```

Create the repository with GraphDB's offline importer:

```bash
docker compose --profile preload run --rm preload
```

The preload command uses:

```text
--config-file /opt/graphdb/kgalign_merged-config.ttl
```

You do not need to create the repository manually in the Workbench.

The preload service creates a temporary RDF-only symlink tree inside the
container before calling GraphDB. This prevents non-RDF files from being picked
up recursively during import.

## Start GraphDB after preload

After preload finishes, start GraphDB:

```bash
docker compose up -d graphdb
```

Check repository state:

```bash
curl http://localhost:7200/rest/repositories
```

The repository is ready when `kgalign_merged` is shown as:

```text
"state":"RUNNING"
```

The Workbench UI can become reachable before the repository itself is ready.
For this dataset, wait for the repository state rather than assuming that an
open UI means SPARQL queries are usable.

Useful log command:

```bash
docker logs -f graphdb
```

The repository is ready after GraphDB reports that `kgalign_merged` has been
successfully initialized.

## SPARQL endpoint

Raw repository endpoint:

```text
http://localhost:7200/repositories/kgalign_merged
```

Workbench SPARQL page:

```text
http://localhost:7200/sparql
```

Use `SPARQL_EXAMPLES.md` for the maintained query set. It includes:

- import and RDF export sanity checks;
- one-to-one validation queries;
- source, confidence, and type summaries;
- type-crosswalk and manual inspection queries;
- compact GraphDB visualization queries for thesis screenshots;
- a limitations/error-analysis query.

## Repository scale

One completed merged repository reported:

```text
NumberOfStatements=25751585421
NumberOfExplicitStatements=25751585421
NumberOfEntities=4136826851
SuccessfulCommits=1
```

The loaded repository occupied approximately:

```text
2.3T graphdb-home/data/repositories/kgalign_merged
```

These values describe the complete merged GraphDB repository, not just the final
alignment graph. They are useful for sizing, but they are not model parameters.

## Important repository settings

`kgalign_merged-config.ttl` configures the repository with:

- repository id `kgalign_merged`;
- no reasoning ruleset;
- context and literal indexes enabled;
- large entity identifiers;
- `disable-sameAs=true`.

`disable-sameAs=true` does not remove the exported `owl:sameAs` triples. They
remain stored as explicit RDF statements. The setting prevents GraphDB from
performing sameAs expansion internally, which would be too expensive at this
graph size.

## Common checks

After startup, the first checks should be:

1. Count direct `owl:sameAs` links.
2. Count `kg:Alignment` metadata records.
3. Confirm unique YAGO and SemOpenAlex entity counts.
4. Check one-to-one violations on both sides.
5. Inspect the source/confidence and type distributions.
6. Render a compact GraphDB visual graph around one selected alignment.

The maintained queries for these checks are in `SPARQL_EXAMPLES.md`.

## Troubleshooting

### Repository is still STARTING

If the Workbench opens but SPARQL does not work, check:

```bash
curl http://localhost:7200/rest/repositories
```

If `kgalign_merged` is still `STARTING`, wait and monitor:

```bash
docker logs -f graphdb
```

### Repository does not exist after preload

Confirm that the preload command used:

```text
--config-file /opt/graphdb/kgalign_merged-config.ttl
```

The repository is created from the config file during offline preload.

### Autocomplete or namespace errors in Workbench

These usually happen while the repository is still opening. Wait until
`kgalign_merged` is `RUNNING`, then reload the Workbench page.

## Git hygiene

Commit the configuration and documentation in this folder:

```text
docker-compose.yml
kgalign_merged-config.ttl
SPARQL_EXAMPLES.md
README.md
.gitignore
```

Do not commit:

```text
graphdb-home/
*.license
*.log
```
