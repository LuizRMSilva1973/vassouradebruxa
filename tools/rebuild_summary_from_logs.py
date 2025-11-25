#!/usr/bin/env python3
import csv
import re
from pathlib import Path
from typing import Optional


def parse_log(path: Path) -> Optional[dict]:
    try:
        target = path.parents[1].name
        ligand = path.parents[0].name
    except Exception:
        return None

    center = {"x": "", "y": "", "z": ""}
    size = {"x": "", "y": "", "z": ""}
    best_aff = None
    mode = None
    ex = None
    nm = None

    rx_center = re.compile(r"Grid center:\s*X\s+([\-0-9\.eE]+)\s+Y\s+([\-0-9\.eE]+)\s+Z\s+([\-0-9\.eE]+)")
    rx_size = re.compile(r"Grid size\s*:\s*X\s+([\-0-9\.eE]+)\s+Y\s+([\-0-9\.eE]+)\s+Z\s+([\-0-9\.eE]+)")
    rx_exh = re.compile(r"Exhaustiveness:\s*(\d+)")
    rx_nm = re.compile(r"num_modes\s*:?\s*(\d+)", re.IGNORECASE)
    rx_header = re.compile(r"^\s*mode\s*\|\s*affinity", re.IGNORECASE)
    rx_row = re.compile(r"^\s*(\d+)\s+([\-0-9\.eE]+)")

    table_started = False
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not table_started:
                m = rx_center.search(line)
                if m:
                    center["x"], center["y"], center["z"] = m.groups()
                m = rx_size.search(line)
                if m:
                    size["x"], size["y"], size["z"] = m.groups()
                m = rx_exh.search(line)
                if m:
                    ex = m.group(1)
                m = rx_nm.search(line)
                if m and nm is None:
                    nm = m.group(1)
            if rx_header.search(line):
                table_started = True
                continue
            if table_started:
                m = rx_row.match(line.replace('|', ' '))
                if m:
                    mode, best_aff = m.group(1), m.group(2)
                    break
    if best_aff is None:
        return None
    return {
        "target": target,
        "ligand": ligand,
        "best_affinity_kcal_per_mol": f"{float(best_aff):.3f}",
        "mode": mode or "1",
        "exhaustiveness": ex or "",
        "num_modes": nm or "",
        "center_x": center["x"],
        "center_y": center["y"],
        "center_z": center["z"],
        "size_x": size["x"],
        "size_y": size["y"],
        "size_z": size["z"],
    }


def main():
    """Scan one or more results roots for docking logs and build a unified summary.

    By default, scans these roots if present (in order):
      - docking_results
      - docking_results_smina
      - docking_results_smina_auto
    """
    import argparse

    ap = argparse.ArgumentParser(description="Rebuild summary_affinities.csv from Vina/Smina logs")
    ap.add_argument("--roots", nargs="*", default=[
        "docking_results",
        "docking_results_smina",
        "docking_results_smina_auto",
    ], help="One or more directories to scan for */*/*.log")
    ap.add_argument("--out", default="docking_results/summary_affinities.csv", help="Output CSV path")
    args = ap.parse_args()

    rows = []
    roots = [Path(r) for r in args.roots]
    for root in roots:
        if not root.exists():
            continue
        # allow varying depths like target/ligand/*.log or target/group/ligand/*.log
        logs = sorted(root.glob("**/*.log"))
        for log in logs:
            r = parse_log(log)
            if r:
                rows.append(r)

    # Deduplicate by (target, ligand) keeping best (most negative) affinity
    best_map = {}
    for r in rows:
        key = (r.get("target"), r.get("ligand"))
        if not key[0] or not key[1]:
            continue
        try:
            val = float(r.get("best_affinity_kcal_per_mol"))
        except Exception:
            continue
        if key not in best_map or val < float(best_map[key]["best_affinity_kcal_per_mol"]):
            best_map[key] = r
    rows = list(best_map.values())

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "target",
        "ligand",
        "best_affinity_kcal_per_mol",
        "mode",
        "exhaustiveness",
        "num_modes",
        "center_x",
        "center_y",
        "center_z",
        "size_x",
        "size_y",
        "size_z",
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"[OK] Wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
