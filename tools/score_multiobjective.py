#!/usr/bin/env python3
"""
Compute a composite multiobjective score for docking results using config/scoring.yaml.
Inputs:
 - docking_results/summary_affinities.csv (from run_docking.sh)
 - data/ligantes_props_obabel.csv (from ligand_props_obabel.py)
 - config/scoring.yaml (weights/constraints)

Outputs:
 - docking_results/scored.csv (per target x ligand with scores)
 - docking_results/ranking_overall.csv (best per ligand across targets)

Notes:
 - XyMove heuristic uses logP, TPSA, MW, FormalCharge to favor xylem mobility (0..1).
 - Selectivity (ΔΔG) requires a ref_target; if not provided, it is omitted from score.
"""
import argparse
import csv
import math
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


def load_yaml(path):
    """Load config/scoring.yaml; if PyYAML is unavailable, use a minimal parser.

    Minimal parser supports top-level maps and one-level nested maps of scalars:
    weights:, constraints:, penalties: with key: value (floats/ints/strings).
    Lines starting with '#' are ignored.
    """
    if yaml is not None:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    # Fallback minimal parse
    cfg = {}
    current = None
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if not line.startswith(" ") and line.endswith(":"):
                # New section
                key = line[:-1].strip()
                cfg[key] = {}
                current = key
                continue
            if current and line.startswith("  ") and ":" in line:
                k, v = line.strip().split(":", 1)
                k = k.strip()
                v = v.strip()
                # try numeric
                try:
                    if "." in v or "e" in v.lower():
                        val = float(v)
                    else:
                        val = int(v)
                except Exception:
                    val = v
                cfg[current][k] = val
    return cfg


def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for d in r:
            rows.append(dict(d))
    return rows, r.fieldnames


def to_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default


def xymove_heuristic(logp, tpsa, mw, charge):
    # Favor moderate logP (1..3), TPSA (60..120), MW (200..800), neutral/slightly positive charge
    def score_window(val, lo, hi):
        if val is None:
            return 0.0
        if val < lo:
            return max(0.0, 1.0 - (lo - val) / (lo if lo != 0 else 1))
        if val > hi:
            return max(0.0, 1.0 - (val - hi) / (hi if hi != 0 else 1))
        # inside window -> 1 dropping to 0.7 near edges
        center = (lo + hi) / 2.0
        span = (hi - lo) / 2.0
        return 0.7 + 0.3 * max(0.0, 1.0 - abs(val - center) / (span if span != 0 else 1))

    s_logp = score_window(logp, 1.0, 3.0)
    s_tpsa = score_window(tpsa, 60.0, 120.0)
    s_mw = score_window(mw, 200.0, 800.0)
    s_charge = 1.0 if (charge is not None and -1 <= charge <= 1) else 0.5
    # Weighted average
    total = 0.35 * s_logp + 0.30 * s_tpsa + 0.25 * s_mw + 0.10 * s_charge
    return max(0.0, min(1.0, total))


def normalize_affinity(dg):
    # Map ΔG (kcal/mol) to 0..1 where more negative -> closer to 1
    # Using a soft cap between -5 and -10
    if dg is None:
        return 0.0
    lo, hi = -5.0, -10.0
    if dg > lo:
        return 0.0
    if dg < hi:
        return 1.0
    return (lo - dg) / (lo - hi)


def normalize_ddg(ddg):
    # More negative ΔΔG (better than ref) -> closer to 1; cap at -2 .. 0
    if ddg is None:
        return 0.0
    lo, hi = -2.0, 0.0
    if ddg <= lo:
        return 1.0
    if ddg >= hi:
        return 0.0
    return (hi - ddg) / (hi - lo)


def main():
    ap = argparse.ArgumentParser(description="Score docking results with multiobjective config")
    ap.add_argument("--summary", default="docking_results/summary_affinities.csv")
    ap.add_argument("--props", default="data/ligantes_props_obabel.csv")
    ap.add_argument("--config", default="config/scoring.yaml")
    ap.add_argument("--ref-target", default=None, help="Reference target name for ΔΔG (off-target)")
    ap.add_argument("--out-scored", default="docking_results/scored.csv")
    ap.add_argument("--out-ranking", default="docking_results/ranking_overall.csv")
    args = ap.parse_args()

    cfg = load_yaml(args.config)
    weights = cfg.get("weights", {})
    constraints = cfg.get("constraints", {})

    rows, cols = load_csv(args.summary)
    props, _ = load_csv(args.props)
    # Build property map with simple normalization to mitigate name variants
    prop_map = {d["ligand"]: d for d in props if "ligand" in d}
    def find_props(lig_name: str):
        # try exact, then underscore/space variants and lowercase
        candidates = [
            lig_name,
            lig_name.replace("_", " "),
            lig_name.replace(" ", "_"),
        ]
        candidates += [c.lower() for c in list(candidates)]
        for c in candidates:
            if c in prop_map:
                return prop_map[c]
        return {}

    # Normalize ligand names (space/underscore) for grouping in ranking
    def norm_name(s: str) -> str:
        return (s or "").replace("_", " ").strip().lower()

    # If ref-target provided, compute best ΔG for ref per ligand (by normalized name)
    ref_best = {}
    if args.ref_target:
        for d in rows:
            if d.get("target") == args.ref_target:
                lig = d.get("ligand")
                ligk = norm_name(lig)
                dg = to_float(d.get("best_affinity_kcal_per_mol"))
                if dg is None:
                    continue
                if ligk not in ref_best or dg < ref_best[ligk]:
                    ref_best[ligk] = dg

    scored = []
    for d in rows:
        lig = d.get("ligand")
        ligk = norm_name(lig)
        dg = to_float(d.get("best_affinity_kcal_per_mol"))
        p = find_props(lig)
        logp = to_float(p.get("logP"))
        tpsa = to_float(p.get("TPSA"))
        mw = to_float(p.get("MW"))
        chg = to_float(p.get("FormalCharge"), 0.0)

        s_aff = normalize_affinity(dg)
        xy = xymove_heuristic(logp, tpsa, mw, chg)
        if args.ref_target and ligk in ref_best and dg is not None:
            ddg = dg - ref_best[ligk]
            s_ddg = normalize_ddg(ddg)
        else:
            ddg = None
            s_ddg = 0.0

        # Constraints check (soft filter)
        ok = True
        if constraints:
            if dg is not None and constraints.get("min_affinity_kcal_per_mol") is not None:
                ok = ok and (dg <= constraints["min_affinity_kcal_per_mol"])
            if ddg is not None and constraints.get("min_ddg_kcal_per_mol") is not None:
                ok = ok and (ddg <= constraints["min_ddg_kcal_per_mol"])
            if constraints.get("min_xymove") is not None:
                ok = ok and (xy >= constraints["min_xymove"])

        score = (
            weights.get("affinity", 0) * s_aff
            + weights.get("selectivity", 0) * s_ddg
            + weights.get("xymove", 0) * xy
        )
        out = dict(d)
        out.update({
            "aff_norm": f"{s_aff:.3f}",
            "ddg_kcal_per_mol": (f"{ddg:.3f}" if ddg is not None else "NA"),
            "ddg_norm": f"{s_ddg:.3f}",
            "xymove": f"{xy:.3f}",
            "score": f"{score:.3f}",
            "passes_constraints": "yes" if ok else "no",
        })
        scored.append(out)

    # Write per-target scored
    out_scored = Path(args.out_scored)
    out_scored.parent.mkdir(parents=True, exist_ok=True)
    base_fields = cols + ["aff_norm", "ddg_kcal_per_mol", "ddg_norm", "xymove", "score", "passes_constraints"]
    with out_scored.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=base_fields)
        w.writeheader()
        for r in scored:
            w.writerow({k: r.get(k, "") for k in base_fields})

    # Best per ligand across targets
    best_per_lig = {}
    for r in scored:
        lig = r.get("ligand")
        ligk = norm_name(lig)
        sc = to_float(r.get("score"))
        # Keep the best-scoring row per normalized ligand name
        if ligk not in best_per_lig or (sc is not None and sc > to_float(best_per_lig[ligk].get("score"))):
            best_per_lig[ligk] = r

    out_rank = Path(args.out_ranking)
    fields = ["ligand", "target", "best_affinity_kcal_per_mol", "xymove", "ddg_kcal_per_mol", "score", "passes_constraints"]
    with out_rank.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for ligk in sorted(best_per_lig.keys()):
            r = best_per_lig[ligk]
            w.writerow({k: r.get(k, "") for k in fields})

    print(f"[OK] Scored per-target -> {out_scored}")
    print(f"[OK] Ranking overall -> {out_rank}")


if __name__ == "__main__":
    main()
