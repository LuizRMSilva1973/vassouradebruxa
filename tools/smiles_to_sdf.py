#!/usr/bin/env python3
"""
Convert one or more .smiles files to 3D SDFs using RDKit (ETKDG + UFF).

Input format (.smiles): a single line with SMILES (optionally followed by whitespace and a name).
Output: ligands/<name>.sdf (or inferred from filename), with 3D coordinates.

Usage examples:
  python3 tools/smiles_to_sdf.py pilot_assets/ligands/caspofungina.smiles \
                                  pilot_assets/ligands/ibrexafungerp.smiles \
    --outdir ligands

Requires: rdkit-pypi.
"""
import argparse
from pathlib import Path

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
except Exception:
    raise SystemExit("RDKit is required. Install with: pip install rdkit-pypi")


def smiles_to_3d_sdf(smiles: str, name: str, out_path: Path):
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        raise ValueError(f"Invalid SMILES for {name}")
    m = Chem.AddHs(m)
    params = AllChem.ETKDGv3()
    params.randomSeed = 0xC0FFEE
    if AllChem.EmbedMolecule(m, params=params) != 0:
        # fallback ETKDGv2
        if AllChem.EmbedMolecule(m, useExpTorsionAnglePrefs=True, useBasicKnowledge=True) != 0:
            raise RuntimeError(f"3D embedding failed for {name}")
    AllChem.UFFOptimizeMolecule(m, maxIters=500)

    w = Chem.SDWriter(str(out_path))
    m.SetProp("_Name", name)
    w.write(m)
    w.close()


def main():
    ap = argparse.ArgumentParser(description="Convert .smiles to 3D SDFs")
    ap.add_argument("inputs", nargs="+", help="Input .smiles files")
    ap.add_argument("--outdir", default="ligands", help="Output directory for SDFs")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for p in args.inputs:
        pth = Path(p)
        if not pth.exists():
            raise SystemExit(f"Input not found: {pth}")
        text = pth.read_text(encoding="utf-8").strip()
        if not text:
            raise SystemExit(f"Empty SMILES file: {pth}")
        parts = text.split()
        smiles = parts[0]
        name = parts[1] if len(parts) > 1 else pth.stem
        out = outdir / f"{name}.sdf"
        smiles_to_3d_sdf(smiles, name, out)
        print(f"[OK] {name}: {out}")


if __name__ == "__main__":
    main()

