#!/usr/bin/env python3
"""
Fetch Isomeric SMILES from PubChem by compound name and emit a CSV suitable for build_library_from_smiles.

Inputs:
  --names data/library_names.txt  (one name per line)
Outputs:
  data/library_smiles.csv (append or overwrite)

Note: Network required.
"""
import argparse
import csv
import sys
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen


def fetch_smiles(name: str) -> str | None:
    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
        + quote(name)
        + "/property/IsomericSMILES/CSV"
    )
    with urlopen(url, timeout=20) as r:
        text = r.read().decode("utf-8", errors="ignore")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Header like: "Name,IsomericSMILES" then values
    if len(lines) < 2:
        return None
    parts = lines[1].split(",", 1)
    if len(parts) != 2:
        return None
    smiles = parts[1].strip()
    if smiles and smiles.lower() != "na":
        return smiles
    return None


def main():
    ap = argparse.ArgumentParser(description="Fetch PubChem Isomeric SMILES by names")
    ap.add_argument("--names", default="data/library_names.txt")
    ap.add_argument("--out", default="data/library_smiles.csv")
    ap.add_argument("--append", action="store_true", help="Append to existing CSV")
    args = ap.parse_args()

    names_path = Path(args.names)
    out_path = Path(args.out)
    names = [ln.strip() for ln in names_path.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("#")]

    mode = "a" if (args.append and out_path.exists()) else "w"
    with out_path.open(mode, newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if mode == "w":
            w.writerow(["ligand", "smiles", "source", "notes"])
        for name in names:
            try:
                smi = fetch_smiles(name)
            except Exception as e:
                print(f"[FAIL] {name}: {e}", file=sys.stderr)
                continue
            if not smi:
                print(f"[MISS] {name}: no SMILES", file=sys.stderr)
                continue
            w.writerow([name, smi, "PubChem", "auto-fetched by name"])
            print(f"[OK] {name}")


if __name__ == "__main__":
    main()

