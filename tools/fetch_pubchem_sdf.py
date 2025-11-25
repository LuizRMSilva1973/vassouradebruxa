#!/usr/bin/env python3
"""
Download 3D SDFs from PubChem PUG REST based on a CSV with columns:
  ligante,pubchem_cid,smiles,sdf_3d_url

Example:
  python3 tools/fetch_pubchem_sdf.py \
    --input pilot_assets/data_ligantes_external.csv --outdir ligands

Network required.
"""
import argparse
import csv
from pathlib import Path
from urllib.request import urlopen


def fetch(url: str) -> bytes:
    with urlopen(url) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser(description="Fetch 3D SDFs from PubChem URLs in CSV")
    ap.add_argument("--input", required=True, help="CSV with columns: ligante,pubchem_cid,smiles,sdf_3d_url")
    ap.add_argument("--outdir", default="ligands", help="Directory to save SDFs")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with open(args.input, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            name = (row.get("ligante") or "").strip()
            url = (row.get("sdf_3d_url") or "").strip()
            if not name or not url:
                print(f"[SKIP] Missing name or URL: {row}")
                continue
            try:
                data = fetch(url)
            except Exception as e:
                print(f"[FAIL] {name}: {e}")
                continue
            outp = outdir / f"{name}.sdf"
            outp.write_bytes(data)
            print(f"[OK] {name}: {outp}")


if __name__ == "__main__":
    main()
