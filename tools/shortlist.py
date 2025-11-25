#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
from collections import defaultdict


def to_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default


def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        fields = r.fieldnames or []
        for d in r:
            rows.append(dict(d))
    return rows, fields


def write_csv(path, fields, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def main():
    ap = argparse.ArgumentParser(description="Generate a shortlist of promising candidates from scored docking results")
    ap.add_argument("--scored", default="docking_results/scored.csv")
    ap.add_argument("--ranking", default="docking_results/ranking_overall.csv")
    ap.add_argument("--out", default="docking_results/shortlist.csv")
    ap.add_argument("--min-score", type=float, default=0.45)
    ap.add_argument("--min-xymove", type=float, default=0.35)
    ap.add_argument("--per-target-top", type=int, default=5, help="Take up to N best per target passing thresholds")
    ap.add_argument("--top-k", type=int, default=25, help="Final cap for shortlist size")
    args = ap.parse_args()

    scored, s_fields = load_csv(args.scored)
    # quick index per target
    per_target = defaultdict(list)
    for r in scored:
        r_score = to_float(r.get("score"))
        r_xy = to_float(r.get("xymove"))
        if r.get("passes_constraints") != "yes":
            continue
        if r_score is None or r_xy is None:
            continue
        if r_score < args.min_score or r_xy < args.min_xymove:
            continue
        per_target[r.get("target")].append(r)

    # sort per target by score desc, then by affinity asc (more negative better)
    def key_sc(r):
        sc = to_float(r.get("score"), -1.0)
        dg = to_float(r.get("best_affinity_kcal_per_mol"), 1e9)
        return (-sc, dg, r.get("ligand", ""))

    selected = []
    for t, lst in per_target.items():
        lst_sorted = sorted(lst, key=key_sc)
        selected.extend(lst_sorted[: max(0, args.per_target_top)])

    # dedupe by ligand preferring higher score
    best_by_lig = {}
    for r in selected:
        lig = r.get("ligand")
        sc = to_float(r.get("score"), -1.0)
        if lig not in best_by_lig or sc > to_float(best_by_lig[lig].get("score"), -1.0):
            best_by_lig[lig] = r

    final = sorted(best_by_lig.values(), key=lambda r: (-to_float(r.get("score"), -1.0), to_float(r.get("best_affinity_kcal_per_mol"), 1e9)))
    if args.top_k and len(final) > args.top_k:
        final = final[: args.top_k]

    fields = [
        "ligand",
        "target",
        "best_affinity_kcal_per_mol",
        "xymove",
        "ddg_kcal_per_mol",
        "score",
        "passes_constraints",
    ]
    write_csv(args.out, fields, final)
    print(f"[OK] Shortlist -> {args.out} ({len(final)} entries)")


if __name__ == "__main__":
    main()

