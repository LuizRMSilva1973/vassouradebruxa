#!/usr/bin/env python3
import argparse
import csv
from collections import defaultdict
from pathlib import Path

# Backend não interativo para salvar figuras
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


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
    ap = argparse.ArgumentParser(description="Pós-processamento do resumo do Vina: ordenação, filtros e ΔΔG de seletividade, com gráficos.")
    ap.add_argument("--input", default="docking_results/summary_affinities.csv", help="CSV de entrada (resumo do docking)")
    ap.add_argument("--out-sorted", default="docking_results/summary_sorted.csv", help="CSV ordenado por melhor afinidade (ascendente)")
    ap.add_argument("--ref-target", default=None, help="Nome do alvo de referência para ΔΔG (não-alvo)")
    ap.add_argument("--out-ddg", default="docking_results/summary_ddg.csv", help="CSV com colunas de ΔΔG vs alvo de referência")
    ap.add_argument("--out-ligand-summary", default="docking_results/ligand_selectivity_summary.csv", help="Resumo por ligante (melhor alvo, ΔΔG vs referência)")

    # Filtros
    ap.add_argument("--targets", default=None, help="Lista de alvos a incluir (separados por vírgula). Ex.: CHS,FKS")
    ap.add_argument("--targets-file", default=None, help="Arquivo com um alvo por linha para incluir")

    # Gráficos
    ap.add_argument("--plot-outdir", default="docking_results/plots", help="Diretório para salvar figuras")
    ap.add_argument("--plots", default="violin,box", help="Tipos de gráficos: violin,box (separar por vírgula)")
    args = ap.parse_args()

    rows, cols = read_summary(args.input)

    # Aplicar filtros de alvos, se fornecidos
    allowed_targets = None
    if args.targets or args.targets_file:
        allowed_targets = set()
        if args.targets:
            allowed_targets.update([t.strip() for t in args.targets.split(',') if t.strip()])
        if args.targets_file:
            p = Path(args.targets_file)
            if p.exists():
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line:
                        allowed_targets.add(line)
        if allowed_targets:
            rows = [d for d in rows if d.get("target") in allowed_targets]

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

    # Gráficos: afinidade por alvo (violin/box)
    plot_kinds = {k.strip().lower() for k in args.plots.split(',') if k.strip()}
    if plot_kinds:
        # Agrupar por alvo
        by_target = defaultdict(list)
        for d in rows:
            val = d.get("best_affinity_kcal_per_mol_num")
            if val is not None:
                by_target[d.get("target")].append(val)

        # Ordenar alvos por mediana (opcional) ou alfabeticamente para estabilidade
        targets = sorted(by_target.keys())
        data = [by_target[t] for t in targets]
        outdir = Path(args.plot_outdir)
        outdir.mkdir(parents=True, exist_ok=True)

        if data and any(len(lst) for lst in data):
            if 'violin' in plot_kinds:
                plt.figure(figsize=(10, 5))
                parts = plt.violinplot(data, showmeans=True, showmedians=True)
                plt.xticks(range(1, len(targets)+1), targets, rotation=45, ha='right')
                plt.ylabel('Afinidade (kcal/mol) — valores mais negativos são melhores')
                plt.title('Distribuição de afinidades por alvo (Violin)')
                plt.tight_layout()
                plt.savefig(outdir / 'affinity_by_target_violin.png', dpi=150)
                plt.close()
            if 'box' in plot_kinds:
                plt.figure(figsize=(10, 5))
                plt.boxplot(data, showmeans=True)
                plt.xticks(range(1, len(targets)+1), targets, rotation=45, ha='right')
                plt.ylabel('Afinidade (kcal/mol) — valores mais negativos são melhores')
                plt.title('Distribuição de afinidades por alvo (Boxplot)')
                plt.tight_layout()
                plt.savefig(outdir / 'affinity_by_target_box.png', dpi=150)
                plt.close()

    print("Feito:")
    print(f" - CSV ordenado: {args.out_sorted}")
    if args.ref_target:
        print(f" - CSV ΔΔG: {args.out_ddg}")
        print(f" - Resumo por ligante: {args.out_ligand_summary}")
    if plot_kinds:
        print(f" - Gráficos em: {args.plot_outdir}")


if __name__ == "__main__":
    main()
