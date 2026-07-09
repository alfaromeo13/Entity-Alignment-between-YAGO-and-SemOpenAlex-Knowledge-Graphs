# 08 Ontotext GraphDB

This folder contains the Docker Compose setup for loading the final RDF output into Ontotext GraphDB. It is used for SPARQL inspection, graph-neighborhood exploration, repository statistics, and thesis screenshots.

This is not an HPC/Slurm stage. Run it on a local workstation or another Docker-capable machine. On TU Dresden/ZIH HPC systems, Singularity is the supported container workflow rather than Docker: <https://compendium.hpc.tu-dresden.de/software/containers/#singularity>

## License

GraphDB requires a license before use. For this project scale, use an Enterprise license.

- GraphDB licensing: <https://graphdb.ontotext.com/documentation/11.4/licensing.html>
- License setup: <https://graphdb.ontotext.com/documentation/11.4/set-up-your-license.html>
- Request a GraphDB license: <https://www.ontotext.com/products/graphdb/#:~:text=Request%20GraphDB%20License>

Place the license on the GraphDB host before preloading:

```text
/data/graphdb-home/work/graphdb.license
```

Do not commit the license file.

## Files

```text
08_ontotex_graphdb/
├── docker-compose.yml
└── README.md
```

## What gets loaded

The compose file creates one merged repository:

```text
kgalign_merged
```

This repository contains:

```text
YAGO triples
SemOpenAlex triples
final owl:sameAs alignments
```

The final alignments come from:

```text
KGAlignment/07_export/rdf_alignments/final_alignments.trig
```

Use the TriG export because it already contains the alignment named graph:

```text
https://kgalign.example.org/graph/final-alignments
```

Do not load the alignments into a separate third GraphDB repository if you want bridge visualization. The source graphs and the alignment graph must be in the same repository.

## Run order

First create the license directory and place the license file there:

```bash
mkdir -p /data/graphdb-home/work
```

Copy `graphdb.license` to:

```text
/data/graphdb-home/work/graphdb.license
```

Then preload the repository:

```bash
cd /data/horse/ws/jovu353i-kgalign/KGAlignment/08_ontotex_graphdb
docker compose run --rm preload
```

This creates the `kgalign_merged` repository offline. You do not need to start GraphDB first and you do not need to create the repository manually in the Workbench.

After preload finishes, start GraphDB:

```bash
docker compose up -d graphdb
```

Open:

```text
http://localhost:7200/
```

If you only have the license through the Workbench upload UI, start GraphDB once, upload the license, stop GraphDB, run the preload command, and start GraphDB again.

## Input paths

The compose file mounts project data directly:

```text
../01_raw/semopenalex
../01_raw/yago
../07_export/rdf_alignments
```

If you move the project to another server, keep the folder structure or update the volume paths in `docker-compose.yml`.

## Non-RDF files

GraphDB offline preload can fail if recursive import folders contain non-RDF files such as `.txt`, `.log`, or `.sh`. The preload service therefore creates a temporary RDF-only symlink tree inside the container before running `importrdf preload`.

For SemOpenAlex, RDF-like files are selected by extension:

```text
*.trig.gz, *.trig, *.ttl.gz, *.ttl, *.nt.gz, *.nt, *.nq.gz, *.nq, *.ntx
```

For YAGO, the preload uses:

```text
yago-beyond-wikipedia.ttl
yago-facts.ttl
yago-schema.ttl
yago-taxonomy.ttl
```

## Large-file import

The final alignment file is large:

```text
final_alignments.trig  about 1.5 GB
```

This setup uses GraphDB's offline `importrdf preload` feature because it is designed for very large initial RDF imports. Instead of sending data through the browser-based Workbench upload path, GraphDB reads the RDF files directly from directories mounted into the container and builds the repository on disk.

That is much better suited for this project than Workbench upload: the source KGs and the final alignment RDF are large, and GraphDB documents a default 1 GB limit for local/remote Workbench file import. Offline preload avoids that upload bottleneck and is the appropriate method for loading large graphs into a fresh repository.

The import is still bounded by the actual machine resources: disk space, memory, runtime, and GraphDB repository storage. But it is not constrained by the browser upload limit.

In the GraphDB loading table, this corresponds to `ImportRDF Preload`: the method intended for huge initial datasets. The other interfaces are useful only in different situations, for example adding data later to an already running repository. For this project setup, offline preload is the preferred method.

Here it is explained more: <https://graphdb.ontotext.com/documentation/11.4/loading-data.html>
