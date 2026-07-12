# Ontotext GraphDB Setup

This folder contains the Docker Compose setup used to load the final KGAlignment RDF output into Ontotext GraphDB.

GraphDB is used here as an RDF inspection and validation environment. It is mainly used for SPARQL validation, graph inspection, qualitative examples, repository statistics, and thesis screenshots. The main preprocessing, embedding, alignment, and RDF export stages are implemented in the earlier pipeline folders.

The intended GraphDB repository is:

    kgalign_merged

This repository contains three layers loaded together:

- YAGO RDF data;
- SemOpenAlex RDF data;
- the final YAGO--SemOpenAlex alignment graph exported as explicit `owl:sameAs` links with reified metadata.

Keeping all three layers in one repository makes the final alignments usable as bridges between the two knowledge graphs. This allows SPARQL queries and GraphDB visualizations to move from SemOpenAlex scholarly entities to their corresponding YAGO entities and surrounding context.

## Files in this folder

    08_ontotex_graphdb/
    ├── docker-compose.yml
    ├── kgalign_merged-config.ttl
    ├── SPARQL_EXAMPLES.md
    ├── .gitignore
    └── README.md

Tracked files:

- `docker-compose.yml` defines the GraphDB runtime container and the one-time offline preload container.
- `kgalign_merged-config.ttl` is the GraphDB repository template used by `importrdf preload`.
- `SPARQL_EXAMPLES.md` contains the validation, inspection, and visualization queries used after the repository has loaded.
- `.gitignore` keeps local GraphDB data, logs, and license files out of Git.

Local-only files:

- `graphdb-home/` stores the GraphDB license, logs, indexes, and repository data.
- `*.license` and `*.log` files are local runtime artifacts and should not be committed.

## Expected input data

The preload service expects the following pipeline outputs to exist relative to this folder:

    ../01_raw/semopenalex/
    ../01_raw/yago/
    ../07_export/rdf_alignments/final_alignments.trig

Only the following YAGO files are loaded:

    yago-beyond-wikipedia.ttl
    yago-facts.ttl
    yago-schema.ttl
    yago-taxonomy.ttl

The final alignment input is:

    ../07_export/rdf_alignments/final_alignments.trig

The TriG export is used because it preserves the named alignment graph:

    https://kgalign.example.org/graph/final-alignments

Do not load the alignments into a separate GraphDB repository if you want bridge visualization. YAGO, SemOpenAlex, and the final alignment graph must be loaded into the same repository.

## Requirements

This setup is intended for a Docker-capable workstation or server. It is not an HPC/Slurm stage.

Required software and resources:

- Docker with Docker Compose;
- sufficient disk space for a multi-terabyte repository;
- enough memory for GraphDB preload and runtime;
- an Ontotext GraphDB license suitable for the repository size.

On TU Dresden/ZIH HPC systems, Singularity is the supported container workflow rather than Docker:

    https://compendium.hpc.tu-dresden.de/software/containers/#singularity

Practical requirements for this exact merged repository:

| Resource | Recommendation |
|---|---|
| RAM | 128 GiB minimum |
| Swap | at least 64 GiB; 128 GiB safer |
| GraphDB runtime heap | keep close to `-Xmx112g` |
| Preload memory | 120g container limit worked, with little margin |
| Disk capacity | at least 3 TiB free; 4 TiB+ safer |
| Disk type | SSD/NVMe strongly recommended |
| CPU | 16 cores usable; 24+ cores better for preload |
| Input RDF size | about 362 GB |
| Final repository size | about 2.3T |
| Startup time after preload/restart | about 50--75 minutes before SPARQL is usable |

These values are based on the completed `kgalign_merged` import and should be treated as practical guidance, not as fixed requirements for every machine.

## GraphDB license

GraphDB requires a license before this repository can be loaded and used. For this project scale, the experiments were performed with a GraphDB Enterprise license.

Useful links:

- GraphDB licensing: <https://graphdb.ontotext.com/documentation/11.4/licensing.html>
- GraphDB license setup: <https://graphdb.ontotext.com/documentation/11.4/set-up-your-license.html>
- Request a GraphDB license: <https://www.ontotext.com/products/graphdb/>

The license file is stored locally inside:

    graphdb-home/work/graphdb.license

This file is local to the machine and must not be committed to Git.

## Run order

The normal workflow is:

    1. Start GraphDB once.
    2. Add the GraphDB license.
    3. Stop GraphDB.
    4. Run the offline preload.
    5. Start GraphDB again.
    6. Wait until kgalign_merged becomes RUNNING.
    7. Use SPARQL and the GraphDB visual graph tools.

Run all commands from this folder:

    cd 08_ontotex_graphdb

## License setup

Start GraphDB:

    docker compose up -d graphdb

Open the Workbench:

    http://localhost:7200/

Add the GraphDB license through the Workbench UI. After the license is added, stop GraphDB before running the offline preload:

    docker compose stop graphdb

Do not run `graphdb` and `preload` at the same time. They share the same `graphdb-home/` directory.

If you already have a valid `graphdb.license` file, you can copy it directly to:

    graphdb-home/work/graphdb.license

## Offline preload

Create the repository with GraphDB's offline importer:

    docker compose --profile preload run --rm preload

For long runs, save the preload log:

    docker compose --profile preload run --rm preload 2>&1 | tee preload-$(date +%Y%m%d-%H%M%S).log

The preload command creates `kgalign_merged` using:

    --config-file /opt/graphdb/kgalign_merged-config.ttl

You do not need to create the repository manually in the Workbench.

The preload service creates a temporary RDF-only symlink tree inside the container before calling GraphDB. This prevents non-RDF files such as logs, text files, or scripts from being picked up during recursive import.

The preload can take many hours. Do not stop Docker or reboot the server while preload is running.

## Start GraphDB after preload

After preload finishes, start GraphDB:

    docker compose up -d graphdb

Check the repository state:

    curl http://localhost:7200/rest/repositories

The repository is ready when `kgalign_merged` is shown as:

    "state":"RUNNING"

The Workbench UI can become reachable before the repository itself is ready. For this dataset, wait for the repository state instead of assuming that an open UI means SPARQL queries are usable.

Useful log command:

    docker logs -f graphdb

Wait until GraphDB reports that `kgalign_merged` has been successfully initialized.

## SPARQL endpoint

Raw repository endpoint:

    http://localhost:7200/repositories/kgalign_merged

Workbench SPARQL page:

    http://localhost:7200/sparql

The maintained query set is stored in:

    SPARQL_EXAMPLES.md

It includes:

- RDF export consistency checks;
- one-to-one validation queries;
- source, confidence, and type summaries;
- SemOpenAlex type to YAGO type crosswalk queries;
- representative alignment examples;
- compact GraphDB visualization queries for thesis screenshots;
- limitations/error-analysis queries.

## Repository scale

One completed merged preload reported:

    NumberOfStatements=25751585421
    NumberOfExplicitStatements=25751585421
    NumberOfEntities=4136826851
    SuccessfulCommits=1

The loaded repository occupied approximately:

    2.3T graphdb-home/data/repositories/kgalign_merged

These values describe the complete merged GraphDB repository, not only the final alignment graph. They are useful for sizing and reproducibility, but they are not model parameters.

## Important repository settings

`kgalign_merged-config.ttl` configures the repository with:

- repository id `kgalign_merged`;
- no reasoning ruleset;
- context and literal indexes enabled;
- large entity identifiers;
- `disable-sameAs=true`.

`disable-sameAs=true` does **not** remove the exported `owl:sameAs` triples. They remain stored as explicit RDF statements. The setting only prevents GraphDB from expanding `owl:sameAs` links internally through reasoning, which would be too expensive at this graph size.

## Useful monitoring commands

Check running containers:

    docker ps

Follow GraphDB logs:

    docker logs -f graphdb

Watch memory and CPU usage:

    docker stats graphdb

Check repository state:

    curl http://localhost:7200/rest/repositories

Check repository counters on disk:

    grep -E '^(NumberOfStatements|NumberOfExplicitStatements|NumberOfEntities|SuccessfulCommits)=' \
      graphdb-home/data/repositories/kgalign_merged/storage/owlim.properties

## Common checks after loading

After the repository becomes `RUNNING`, the most useful checks are:

1. Count direct `owl:sameAs` links.
2. Count `kg:Alignment` metadata records.
3. Confirm that the direct links and metadata records match.
4. Check one-to-one violations on both sides.
5. Inspect the distribution by SemOpenAlex entity type.
6. Inspect source/confidence summaries.
7. Inspect the SemOpenAlex type to YAGO type crosswalk.
8. Render one compact GraphDB visual graph around a selected alignment.

The maintained queries for these checks are in:

    SPARQL_EXAMPLES.md

## Thesis evidence

For the thesis, the full query bank does not need to be shown. The most useful GraphDB evidence is a small set of selected tables and one compact visual example.

Recommended thesis artifacts:

- RDF export consistency table;
- one-to-one validation table;
- distribution by SemOpenAlex entity type;
- SemOpenAlex type to YAGO type crosswalk;
- representative alignment examples;
- one GraphDB visual graph showing an `owl:sameAs` bridge.

The completed repository was checked with SPARQL after import. The two core export-consistency checks returned the same value:

    direct owl:sameAs links:        1,973,194
    kg:Alignment metadata records:  1,973,194

This confirms that the named alignment graph contains both direct `owl:sameAs` bridge triples and corresponding reified alignment metadata records.

The full SPARQL query set remains in `SPARQL_EXAMPLES.md`.

## Troubleshooting

### Repository is still STARTING

If the Workbench opens but SPARQL queries do not work, check:

    curl http://localhost:7200/rest/repositories

If `kgalign_merged` is still `STARTING`, wait and monitor:

    docker logs -f graphdb

For this dataset size, startup can take a long time.

### Repository does not exist after preload

Confirm that the preload command used:

    --config-file /opt/graphdb/kgalign_merged-config.ttl

The repository is created from the config file during offline preload.

### Workbench autocomplete or namespace errors

These can appear while `kgalign_merged` is still `STARTING`. Wait until the repository becomes `RUNNING`, then reload the Workbench page.

### Memory or entity-pool issues

Keep the high runtime heap settings in `docker-compose.yml`. If memory settings were changed, recreate the container:

    docker compose up -d --force-recreate graphdb