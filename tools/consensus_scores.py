#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


def to_float(x):
    try:
        return float(x)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description="Build consensus affinities (Vina+Smina) by averaging ΔG per target×ligand")
    ap.add_argument("--vina", required=True)
    ap.add_argument("--smina", required=True)
    ap.add_argument("--out", default="docking_results/consensus_affinities.csv")
    args = ap.parse_args()

    def load(path):
        rows = []
        with open(path, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for d in r:
                rows.append(d)
        return rows

    vina = load(args.vina)
    smina = load(args.smina)

    # Index by (target, ligand)
    def index(rows):
        m = {}
        for d in rows:
            key = (d.get("target"), d.get("ligand"))
            m.setdefault(key, []).append(d)
        return m

    iv = index(vina)
    ismi = index(smina)

    out = []
    for key in sorted(set(list(iv.keys()) + list(ismi.keys()))):
        tv = iv.get(key, [])
        ts = ismi.get(key, [])
        vals = []
        for src in (tv + ts):
            dg = to_float(src.get("best_affinity_kcal_per_mol"))
            if dg is not None:
                vals.append(dg)
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        # Use vina row as template if exists, else smina
        base = (tv[0] if tv else ts[0]).copy()
        base["best_affinity_kcal_per_mol"] = f"{avg:.3f}"
        out.append(base)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    if out:
        with open(args.out, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=out[0].keys())
            w.writeheader()
            for r in out:
                w.writerow(r)
    print(f"[OK] Consensus rows: {len(out)} -> {args.out}")


if __name__ == "__main__":
    main()

