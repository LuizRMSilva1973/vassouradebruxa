#!/usr/bin/env python3
"""
Compute ligand properties using OpenBabel's obprop for SDF files in a directory.
Outputs a CSV: ligand,MW,logP,TPSA,HBD,HBA,FormalCharge

Usage:
  python3 tools/ligand_props_obabel.py --indir ligands --output data/ligantes_props_obabel.csv

Requires: OpenBabel (obprop)
"""
import argparse
import csv
import subprocess
from pathlib import Path


def run_obprop(path: Path) -> dict:
    try:
        out = subprocess.check_output(["obprop", str(path)], text=True)
    except Exception as e:
        return {}
    props = {}
    for line in out.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
        else:
            parts = line.split()
            if not parts:
                continue
            k = parts[0].strip()
            v = " ".join(parts[1:]).strip() if len(parts) > 1 else ""
        props[k] = v
    # Map to canonical keys if available
    m = {}
    # Normalize keys case-insensitively; common obprop keys:
    # mol_weight (or MolWt) -> MW; logP -> logP; PSA -> TPSA; (HBD/HBA/FormalCharge may be absent)
    lower = {k.lower(): v for k, v in props.items()}
    def grab_float(keys):
        for k in keys:
            if k in lower and lower[k] not in (None, ""):
                try:
                    return float(lower[k])
                except Exception:
                    return lower[k]
        return None

    m["MW"] = grab_float(["mol_weight", "molwt", "molecularweight", "mw"])
    m["logP"] = grab_float(["logp"])  # already numeric
    # Map PSA to TPSA
    tpsa = grab_float(["tpsa", "psa"])
    if tpsa is not None:
        m["TPSA"] = tpsa
    # Optional fields
    for dst, keys in (
        ("HBD", ["hbd", "hbond donors", "hbond_donors"]),
        ("HBA", ["hba", "hbond acceptors", "hbond_acceptors"]),
        ("FormalCharge", ["formalcharge", "charge"]),
    ):
        val = grab_float(keys)
        if val is not None:
            m[dst] = val
    return m


def main():
    ap = argparse.ArgumentParser(description="Compute ligand properties via obprop")
    ap.add_argument("--indir", default="ligands", help="Directory with .sdf files")
    ap.add_argument("--output", default="data/ligantes_props_obabel.csv", help="Output CSV path")
    args = ap.parse_args()

    indir = Path(args.indir)
    sdf_files = sorted(indir.glob("*.sdf"))
    rows = []
    for p in sdf_files:
        name = p.stem
        props = run_obprop(p)
        props["ligand"] = name
        rows.append(props)

    outp = Path(args.output)
    outp.parent.mkdir(parents=True, exist_ok=True)
    fields = ["ligand", "MW", "logP", "TPSA", "HBD", "HBA", "FormalCharge"]
    with outp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    print(f"[OK] Wrote properties for {len(rows)} ligands -> {outp}")


if __name__ == "__main__":
    main()
