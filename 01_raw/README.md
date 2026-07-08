# Raw Input Data

This folder contains the original raw knowledge graph dumps used in the project. These files are treated as immutable source data and should not be edited manually. All later stages of the pipeline start from these raw RDF dumps and write their outputs into separate downstream folders.

The two input knowledge graphs are stored as:

```text
01_raw/ 
├── yago/ 
└── semopenalex/
```

YAGO is stored as Turtle files (.ttl), while SemOpenAlex is stored as compressed TriG shards (.trig.gz).

The raw dumps are the starting point of the full pipeline. The raw RDF files are not directly used for embedding training or entity alignment. They first pass through RDF parsing, filtering, and preprocessing.

# Data Acquisition

**SemOpenAlex** raw data was obtained as compressed TriG files (`.trig.gz`).
These files contain RDF data with named graphs and are processed in compressed form during preprocessing. You can run a download script from this folder as following:

```bash
cd /data/horse/ws/jovu353i-kgalign/KGAlignment/01_raw/semopenalex

bash download_semopenalex.sh
```
During preprocessing, these files are decompressed on the fly using `pigz -dc` and parsed with Apache Jena riot

**YAGO 4.5** raw data was obtained as Turtle files (`.ttl`) and downloaded from their official website: https://yago-knowledge.org/downloads/yago-4-5


# Verification Commands

Check raw YAGO files

```bash
ls -lh /data/horse/ws/jovu353i-kgalign/KGAlignment/01_raw/yago

find /data/horse/ws/jovu353i-kgalign/KGAlignment/01_raw/yago -name "*.ttl" | wc -l
```

Check raw SemOpenAlex files

```bash
ls -lh /data/horse/ws/jovu353i-kgalign/KGAlignment/01_raw/semopenalex | head

find /data/horse/ws/jovu353i-kgalign/KGAlignment/01_raw/semopenalex -name "*.trig.gz" | wc -l
```

## Notes

*This folder should remain unchanged after download. If a new version of YAGO or SemOpenAlex is downloaded, it should either be <ins>clearly separated into a new subfolder or documented carefully, so that experiments remain reproducible</ins>.*