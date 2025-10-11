#!/usr/bin/env python3
"""
Run SMINA in batch over all target×ligand combinations using existing .box definitions.
Outputs a summary CSV compatible with Vina's summary for downstream processing.

Requirements: `smina` binary in PATH.
"""
import argparse
import csv
import os
from pathlib import Path
import subprocess


def read_box(path: Path):
    vals = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                vals[k.strip()] = float(v.strip())
    need = ["center_x", "center_y", "center_z", "size_x", "size_y", "size_z"]
    if not all(k in vals for k in need):
        raise ValueError(f"Invalid box file: {path}")
    return vals


def main():
    ap = argparse.ArgumentParser(description="Run SMINA batch with boxes and summarize")
    ap.add_argument("--targets", default="targets")
    ap.add_argument("--ligands", default="ligands")
    ap.add_argument("--outdir", default="docking_results_smina")
    ap.add_argument("--exhaustiveness", type=int, default=16)
    ap.add_argument("--num-modes", type=int, default=9)
    args = ap.parse_args()

    targets = sorted(Path(args.targets).glob("*.pdbqt"))
    ligands = sorted(Path(args.ligands).glob("*.pdbqt"))
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    summary = outdir / "summary_affinities.csv"

    with summary.open("w", encoding="utf-8", newline="") as fsum:
        w = csv.writer(fsum)
        w.writerow([
            "target","ligand","best_affinity_kcal_per_mol","mode","exhaustiveness","num_modes",
            "center_x","center_y","center_z","size_x","size_y","size_z"
        ])

        for t in targets:
            base = t.stem
            box = Path(args.targets) / f"{base}.box"
            if not box.exists():
                print(f"[WARN] Missing box for {base}; skipping")
                continue
            vals = read_box(box)
            for lig in ligands:
                lbase = lig.stem
                pair_out = outdir / base / lbase
                pair_out.mkdir(parents=True, exist_ok=True)
                outp = pair_out / f"{lbase}_on_{base}.pdbqt"
                logf = pair_out / f"{lbase}_on_{base}.log"
                cmd = [
                    "smina",
                    "--receptor", str(t),
                    "--ligand", str(lig),
                    "--center_x", str(vals["center_x"]),
                    "--center_y", str(vals["center_y"]),
                    "--center_z", str(vals["center_z"]),
                    "--size_x", str(vals["size_x"]),
                    "--size_y", str(vals["size_y"]),
                    "--size_z", str(vals["size_z"]),
                    "--exhaustiveness", str(args.exhaustiveness),
                    "--num_modes", str(args.num_modes),
                    "--out", str(outp),
                ]
                try:
                    with logf.open("w", encoding="utf-8") as flog:
                        subprocess.run(cmd, check=True, stdout=flog, stderr=subprocess.STDOUT)
                except Exception as e:
                    print(f"[WARN] smina failed for {lbase} on {base}: {e}")
                    continue
                # parse best affinity from log
                best = None
                mode = None
                try:
                    with logf.open("r", encoding="utf-8") as flog:
                        lines = flog.readlines()
                    flag = False
                    for ln in lines:
                        if ln.strip().startswith("-----"):
                            flag = True
                            continue
                        if flag and ln.strip():
                            parts = ln.split()
                            mode = parts[0]
                            best = float(parts[1])
                            break
                except Exception:
                    pass
                if best is not None:
                    w.writerow([
                        base, lbase, best, mode or 1, args.exhaustiveness, args.num_modes,
                        vals["center_x"], vals["center_y"], vals["center_z"],
                        vals["size_x"], vals["size_y"], vals["size_z"],
                    ])
    print(f"[OK] SMINA summary -> {summary}")


if __name__ == "__main__":
    main()

