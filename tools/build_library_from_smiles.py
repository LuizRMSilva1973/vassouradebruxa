#!/usr/bin/env python3
"""
Build ligand 3D SDF and PDBQT from a CSV manifest of SMILES using OpenBabel.

Input CSV (default: data/library_smiles.csv) with columns:
  ligand,smiles,source,notes

Requires: obabel in PATH.
"""
import argparse
import csv
import subprocess
from pathlib import Path


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Command failed ({r.returncode}): {' '.join(cmd)}\nSTDERR:\n{r.stderr}")
    return r.stdout


def ensure_sdf_and_pdbqt(name: str, smiles: str, lig_dir: Path):
    lig_dir.mkdir(parents=True, exist_ok=True)
    sdf = lig_dir / f"{name}.sdf"
    pdbqt = lig_dir / f"{name}.pdbqt"
    if (not sdf.exists()) or sdf.stat().st_size == 0:
        run(["obabel", "-:" + smiles, "-osdf", "-O", str(sdf), "--gen3d"])
    if (not pdbqt.exists()) or pdbqt.stat().st_size == 0:
        # direct SMILES -> PDBQT (fallback) if needed
        run(["obabel", "-:" + smiles, "-opdbqt", "-O", str(pdbqt), "--gen3d", "--partialcharge", "gasteiger"])
    return sdf, pdbqt


def main():
    ap = argparse.ArgumentParser(description="Build library from SMILES CSV using OpenBabel")
    ap.add_argument("--csv", default="data/library_smiles.csv")
    ap.add_argument("--outdir", default="ligands")
    args = ap.parse_args()

    lig_dir = Path(args.outdir)
    lig_dir.mkdir(parents=True, exist_ok=True)

    with open(args.csv, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        missing = {"ligand", "smiles"} - set(r.fieldnames or [])
        if missing:
            raise SystemExit(f"CSV missing columns: {', '.join(sorted(missing))}")
        built = 0
        for row in r:
            name = (row.get("ligand") or "").strip()
            smiles = (row.get("smiles") or "").strip()
            if not name or not smiles:
                continue
            ensure_sdf_and_pdbqt(name, smiles, lig_dir)
            built += 1
            print(f"[OK] {name}")
    print(f"[DONE] Built/verified {built} ligands in {lig_dir}")


if __name__ == "__main__":
    main()
