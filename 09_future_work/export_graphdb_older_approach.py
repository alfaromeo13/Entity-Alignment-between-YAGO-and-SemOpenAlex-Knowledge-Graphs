import os
import time
import gzip
import requests

GRAPHDB = "http://localhost:7200"
REPO = "yago"  # todo: change to "yago" for YAGO repo and then "semopenalex" for SemOpenAlex repo
OUT_DIR = "./exports"
BATCH_GB = 20                 # rotate every ~20GB compressed (tune)
USE_GZIP = True               # strongly recommended

os.makedirs(OUT_DIR, exist_ok=True)

url = f"{GRAPHDB}/repositories/{REPO}/statements"

headers = {
    "Accept": "application/n-triples"
}

def open_out(i: int):
    fn = os.path.join(OUT_DIR, f"{REPO}_statements_part{i:04d}.nt" + (".gz" if USE_GZIP else ""))
    f = gzip.open(fn, "wb") if USE_GZIP else open(fn, "wb")
    return fn, f

part = 0
written = 0
limit_bytes = int(BATCH_GB * (1024**3))

out_name, out_f = open_out(part)
print(f"[+] Writing to {out_name}")

with requests.get(url, headers=headers, stream=True, timeout=600) as r:
    r.raise_for_status()
    for chunk in r.iter_content(chunk_size=64 * 1024 * 1024):  # 64MB chunks
        if not chunk:
            continue
        out_f.write(chunk)
        written += len(chunk)

        if written >= limit_bytes:
            out_f.close()
            part += 1
            written = 0
            out_name, out_f = open_out(part)
            print(f"[+] Rotated. Writing to {out_name}")

out_f.close()
print("Export finished!")