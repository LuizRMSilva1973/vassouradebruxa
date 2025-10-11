#!/usr/bin/env python3
import argparse
import csv
from math import isnan
from pathlib import Path


def to_float(x):
    try:
        return float(x)
    except Exception:
        return None


def dominates(a, b, cols, maximize):
    """Return True if a dominates b (no worse in all, strictly better in at least one)."""
    better = False
    for i, c in enumerate(cols):
        va = a.get(c)
        vb = b.get(c)
        if va is None or vb is None:
            return False
        if maximize[i]:
            if va < vb:
                return False
            if va > vb:
                better = True
        else:
            if va > vb:
                return False
            if va < vb:
                better = True
    return better


def main():
    ap = argparse.ArgumentParser(description="Compute non-dominated Pareto front from scored.csv")
    ap.add_argument("--input", default="docking_results/scored.csv")
    ap.add_argument("--out", default="docking_results/pareto_front.csv")
    ap.add_argument("--columns", nargs="*", default=["score", "xymove", "best_affinity_kcal_per_mol"], help="Columns to consider")
    ap.add_argument("--maximize", nargs="*", default=["True", "True", "False"], help="Maximize flags aligned with columns")
    args = ap.parse_args()

    cols = args.columns
    maximize = [str(x).lower() in ("1", "true", "yes") for x in args.maximize]

    rows = []
    with open(args.input, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for d in r:
            dd = dict(d)
            # map selected columns to floats
            for c in cols:
                dd[c] = to_float(dd.get(c))
            rows.append(dd)

    # Compute front
    front = []
    for i, a in enumerate(rows):
        dom = False
        for j, b in enumerate(rows):
            if i == j:
                continue
            if dominates(b, a, cols, maximize):
                dom = True
                break
        if not dom:
            front.append(a)

    # Write output with main identifying columns
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "ligand",
        "target",
        "best_affinity_kcal_per_mol",
        "xymove",
        "ddg_kcal_per_mol",
        "score",
        "passes_constraints",
    ]
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in front:
            w.writerow({k: r.get(k, "") for k in fields})

    print(f"[OK] Pareto front size: {len(front)} -> {out}")


if __name__ == "__main__":
    main()

