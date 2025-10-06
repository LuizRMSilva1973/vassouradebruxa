#!/usr/bin/env python3
import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_float(val):
    try:
        return float(val)
    except Exception:
        return None


def read_summary(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for d in r:
            d = dict(d)
            d["best_affinity_kcal_per_mol_num"] = parse_float(d.get("best_affinity_kcal_per_mol"))
            rows.append(d)
    return rows, r.fieldnames


def write_csv(path, fieldnames, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for d in rows:
            w.writerow({k: d.get(k, "") for k in fieldnames})


def main():
    ap = argparse.ArgumentParser(description="Pós-processamento do resumo do Vina: ordenação e ΔΔG de seletividade.")
    ap.add_argument("--input", default="docking_results/summary_affinities.csv", help="CSV de entrada (resumo do docking)")
    ap.add_argument("--out-sorted", default="docking_results/summary_sorted.csv", help="CSV ordenado por melhor afinidade (ascendente)")
    ap.add_argument("--ref-target", default=None, help="Nome do alvo de referência para ΔΔG (não-alvo)")
    ap.add_argument("--out-ddg", default="docking_results/summary_ddg.csv", help="CSV com colunas de ΔΔG vs alvo de referência")
    ap.add_argument("--out-ligand-summary", default="docking_results/ligand_selectivity_summary.csv", help="Resumo por ligante (melhor alvo, ΔΔG vs referência)")
    args = ap.parse_args()

    rows, cols = read_summary(args.input)

    # Ordenar por afinidade (mais negativa primeiro). Colocar NAs no final.
    rows_sorted = sorted(
        rows,
        key=lambda d: (d["best_affinity_kcal_per_mol_num"] is None, d.get("best_affinity_kcal_per_mol_num", 0.0)),
    )
    write_csv(args.out_sorted, cols, rows_sorted)

    if args.ref_target:
        # Mapear afinidade do ligante no alvo de referência
        ref_aff = {}
        # pode haver múltiplas entradas; escolher a melhor (mais negativa)
        tmp = defaultdict(list)
        for d in rows:
            if d.get("target") == args.ref_target:
                val = d.get("best_affinity_kcal_per_mol_num")
                if val is not None:
                    tmp[d.get("ligand")].append(val)
        for lig, vals in tmp.items():
            ref_aff[lig] = min(vals) if vals else None

        # Criar CSV com ΔΔG: ΔΔG = ΔG(target,ligand) - ΔG(ref_target,ligand)
        ddg_fields = list(cols) + [
            "ref_target",
            "ref_affinity_kcal_per_mol",
            "ddg_kcal_per_mol",
        ]
        ddg_rows = []
        for d in rows_sorted:
            lig = d.get("ligand")
            dg = d.get("best_affinity_kcal_per_mol_num")
            ref_dg = ref_aff.get(lig)
            ddg = (dg - ref_dg) if (dg is not None and ref_dg is not None) else None
            ddg_rows.append({
                **{k: d.get(k) for k in cols},
                "ref_target": args.ref_target,
                "ref_affinity_kcal_per_mol": ("{:.3f}".format(ref_dg) if ref_dg is not None else "NA"),
                "ddg_kcal_per_mol": ("{:.3f}".format(ddg) if ddg is not None else "NA"),
            })
        write_csv(args.out_ddg, ddg_fields, ddg_rows)

        # Resumo por ligante: melhor alvo (menor ΔG), ΔG_ref, ΔΔG_best
        lig_best = {}
        by_lig = defaultdict(list)
        for d in rows:
            dg = d.get("best_affinity_kcal_per_mol_num")
            if dg is not None:
                by_lig[d.get("ligand")].append((dg, d.get("target")))
        for lig, lst in by_lig.items():
            if not lst:
                continue
            best_dg, best_target = min(lst, key=lambda x: x[0])
            ref_dg = ref_aff.get(lig)
            ddg_best = (best_dg - ref_dg) if (best_dg is not None and ref_dg is not None) else None
            lig_best[lig] = {
                "ligand": lig,
                "best_target": best_target,
                "best_affinity_kcal_per_mol": best_dg,
                "ref_target": args.ref_target,
                "ref_affinity_kcal_per_mol": ref_dg,
                "ddg_best_kcal_per_mol": ddg_best,
            }

        lig_fields = [
            "ligand",
            "best_target",
            "best_affinity_kcal_per_mol",
            "ref_target",
            "ref_affinity_kcal_per_mol",
            "ddg_best_kcal_per_mol",
        ]
        lig_rows = []
        for lig in sorted(lig_best.keys()):
            x = lig_best[lig]
            lig_rows.append({
                "ligand": x["ligand"],
                "best_target": x["best_target"],
                "best_affinity_kcal_per_mol": ("{:.3f}".format(x["best_affinity_kcal_per_mol"]) if x["best_affinity_kcal_per_mol"] is not None else "NA"),
                "ref_target": x["ref_target"],
                "ref_affinity_kcal_per_mol": ("{:.3f}".format(x["ref_affinity_kcal_per_mol"]) if x["ref_affinity_kcal_per_mol"] is not None else "NA"),
                "ddg_best_kcal_per_mol": ("{:.3f}".format(x["ddg_best_kcal_per_mol"]) if x["ddg_best_kcal_per_mol"] is not None else "NA"),
            })
        write_csv(args.out_ligand_summary, lig_fields, lig_rows)

    print("Feito:")
    print(f" - CSV ordenado: {args.out_sorted}")
    if args.ref_target:
        print(f" - CSV ΔΔG: {args.out_ddg}")
        print(f" - Resumo por ligante: {args.out_ligand_summary}")


if __name__ == "__main__":
    main()

