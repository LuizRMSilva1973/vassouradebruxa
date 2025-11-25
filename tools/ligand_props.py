#!/usr/bin/env python3
"""
Compute basic ligand properties from SMILES and write a CSV with annotations.
Inputs: a CSV with at least columns: ligante,smiles
Outputs: CSV with computed columns: MW, MolLogP, TPSA, HBD, HBA, FormalCharge, QED

Example:
  python3 tools/ligand_props.py \
    --input data/templates/ligantes_template.csv \
    --output data/ligantes_props.csv

Requires: rdkit-pypi
"""
import argparse
import csv
from pathlib import Path

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors, QED
except Exception as e:
    raise SystemExit("RDKit is required. Install with: pip install rdkit-pypi")


def compute_props(smiles: str):
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return None
    mw = Descriptors.MolWt(m)
    logp = Crippen.MolLogP(m)
    tpsa = rdMolDescriptors.CalcTPSA(m)
    hbd = rdMolDescriptors.CalcNumHBD(m)
    hba = rdMolDescriptors.CalcNumHBA(m)
    fc = Chem.GetFormalCharge(m)
    qed = QED.qed(m)
    return {
        "MW": round(mw, 3),
        "logP": round(logp, 3),
        "TPSA": round(tpsa, 3),
        "HBD": int(hbd),
        "HBA": int(hba),
        "FormalCharge": int(fc),
        "QED": round(qed, 3),
    }


def main():
    ap = argparse.ArgumentParser(description="Compute ligand properties from SMILES")
    ap.add_argument("--input", required=True, help="Input CSV (must include 'ligante' and 'smiles')")
    ap.add_argument("--output", required=True, help="Output CSV path")
    args = ap.parse_args()

    inp = Path(args.input)
    rows = []
    with inp.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        if not {"ligante", "smiles"}.issubset(set(r.fieldnames or [])):
            raise SystemExit("Input must contain columns: ligante,smiles")
        for d in r:
            d = dict(d)
            smi = (d.get("smiles") or "").strip()
            if smi:
                props = compute_props(smi)
            else:
                props = None
            if props:
                for k, v in props.items():
                    d[k] = v
            else:
                for k in ["MW", "logP", "TPSA", "HBD", "HBA", "FormalCharge", "QED"]:
                    d.setdefault(k, "")
            rows.append(d)

    outp = Path(args.output)
    outp.parent.mkdir(parents=True, exist_ok=True)
    # Fieldnames: input fields + computed
    base = rows[0].keys() if rows else []
    computed = ["MW", "logP", "TPSA", "HBD", "HBA", "FormalCharge", "QED"]
    fieldnames = list(dict.fromkeys([*base, *computed]))
    with outp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for d in rows:
            w.writerow({k: d.get(k, "") for k in fieldnames})

    print(f"[OK] Properties written to: {outp}")


if __name__ == "__main__":
    main()

