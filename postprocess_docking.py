#!/usr/bin/env python3
import argparse
import csv
from collections import defaultdict
from pathlib import Path

# Backend não interativo para salvar figuras (opcional)
HAVE_MPL = True
try:
    import matplotlib  # type: ignore
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # type: ignore
except Exception:
    HAVE_MPL = False


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
    # Simple SVG fallback for boxplots when matplotlib is unavailable
    def save_boxplot_svg(targets, series, out_path):
        """Write a simple boxplot as SVG using only stdlib.

        targets: list of target names
        series: list of lists of floats (same order as targets)
        """
        # Compute quartiles and whiskers
        import math
        def quantile(vals, q):
            if not vals:
                return None
            xs = sorted(vals)
            pos = (len(xs) - 1) * q
            lo = math.floor(pos)
            hi = math.ceil(pos)
            if lo == hi:
                return xs[int(pos)]
            return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)

        stats = []
        all_vals = []
        for vals in series:
            if vals:
                all_vals.extend(vals)
                q1 = quantile(vals, 0.25)
                med = quantile(vals, 0.50)
                q3 = quantile(vals, 0.75)
                vmin = min(vals)
                vmax = max(vals)
            else:
                q1 = med = q3 = vmin = vmax = None
            stats.append((q1, med, q3, vmin, vmax))
        if not all_vals:
            return False
        vmin_all = min(all_vals)
        vmax_all = max(all_vals)
        if vmin_all == vmax_all:
            vmax_all = vmin_all + 1.0

        # SVG canvas
        W, H = 900, 500
        margin_l, margin_r, margin_t, margin_b = 80, 20, 30, 60
        plot_w = W - margin_l - margin_r
        plot_h = H - margin_t - margin_b

        def ypix(val):
            # Map value -> y pixel (top smaller, bottom larger)
            return margin_t + (vmax_all - val) * plot_h / (vmax_all - vmin_all)

        n = len(targets)
        if n == 0:
            return False
        step = plot_w / max(1, n)
        box_w = step * 0.35

        # Build SVG elements
        parts = []
        parts.append(f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}'>")
        parts.append("<style> .axis{stroke:#333;stroke-width:1} .grid{stroke:#ddd;stroke-width:1} .txt{font:12px sans-serif;fill:#333} .legend{font:14px sans-serif;fill:#333} </style>")
        # Title
        parts.append(f"<text class='legend' x='{W/2:.1f}' y='20' text-anchor='middle'>Distribuição de afinidades por alvo (Boxplot)</text>")
        # Axes
        # y-axis with ticks
        yticks = 6
        for i in range(yticks+1):
            frac = i/yticks
            val = vmin_all + (vmax_all - vmin_all)*frac
            y = ypix(val)
            parts.append(f"<line class='grid' x1='{margin_l}' y1='{y:.1f}' x2='{W-margin_r}' y2='{y:.1f}'/>")
            parts.append(f"<text class='txt' x='{margin_l-6}' y='{y+4:.1f}' text-anchor='end'>{val:.2f}</text>")
        # x-axis
        parts.append(f"<line class='axis' x1='{margin_l}' y1='{H-margin_b}' x2='{W-margin_r}' y2='{H-margin_b}'/>")

        # Boxes per target
        for idx, (t, st) in enumerate(zip(targets, stats)):
            q1, med, q3, vmin, vmax = st
            cx = margin_l + step*(idx+0.5)
            # Label
            parts.append(f"<text class='txt' x='{cx:.1f}' y='{H-margin_b+18}' text-anchor='middle' transform='rotate(0 {cx:.1f},{H-margin_b+18})'>{t}</text>")
            if None in (q1, med, q3, vmin, vmax):
                continue
            # Box
            yq1 = ypix(q1); yq3 = ypix(q3)
            x0 = cx - box_w/2; x1 = cx + box_w/2
            parts.append(f"<rect x='{x0:.1f}' y='{min(yq1,yq3):.1f}' width='{box_w:.1f}' height='{abs(yq3-yq1):.1f}' fill='#7aa6e3' stroke='#225c9c' stroke-width='1' fill-opacity='0.5' />")
            # Median
            ymed = ypix(med)
            parts.append(f"<line x1='{x0:.1f}' y1='{ymed:.1f}' x2='{x1:.1f}' y2='{ymed:.1f}' stroke='#1b3f6b' stroke-width='2' />")
            # Whiskers
            yvmin = ypix(vmin); yvmax = ypix(vmax)
            parts.append(f"<line x1='{cx:.1f}' y1='{yvmin:.1f}' x2='{cx:.1f}' y2='{yq1:.1f}' stroke='#225c9c' stroke-width='1' />")
            parts.append(f"<line x1='{cx:.1f}' y1='{yq3:.1f}' x2='{cx:.1f}' y2='{yvmax:.1f}' stroke='#225c9c' stroke-width='1' />")
            parts.append(f"<line x1='{(cx-box_w*0.3):.1f}' y1='{yvmin:.1f}' x2='{(cx+box_w*0.3):.1f}' y2='{yvmin:.1f}' stroke='#225c9c' stroke-width='1' />")
            parts.append(f"<line x1='{(cx-box_w*0.3):.1f}' y1='{yvmax:.1f}' x2='{(cx+box_w*0.3):.1f}' y2='{yvmax:.1f}' stroke='#225c9c' stroke-width='1' />")

        # Y label
        parts.append(f"<text class='txt' x='20' y='{H/2:.1f}' transform='rotate(-90 20,{H/2:.1f})' text-anchor='middle'>Afinidade (kcal/mol) — mais negativo é melhor</text>")
        parts.append("</svg>")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(parts), encoding="utf-8")
        return True

    if plot_kinds and not HAVE_MPL:
        # Fallback: only boxplot as SVG
        plot_kinds = {'box'} if 'box' in plot_kinds or 'violin' in plot_kinds else set()
        if not plot_kinds:
            print("[WARN] matplotlib não disponível; pulando geração de gráficos.")
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
            if HAVE_MPL and 'violin' in plot_kinds:
                plt.figure(figsize=(10, 5))
                _ = plt.violinplot(data, showmeans=True, showmedians=True)
                plt.xticks(range(1, len(targets)+1), targets, rotation=45, ha='right')
                plt.ylabel('Afinidade (kcal/mol) — valores mais negativos são melhores')
                plt.title('Distribuição de afinidades por alvo (Violin)')
                plt.tight_layout()
                plt.savefig(outdir / 'affinity_by_target_violin.png', dpi=150)
                plt.close()
            if 'box' in plot_kinds:
                if HAVE_MPL:
                    plt.figure(figsize=(10, 5))
                    plt.boxplot(data, showmeans=True)
                    plt.xticks(range(1, len(targets)+1), targets, rotation=45, ha='right')
                    plt.ylabel('Afinidade (kcal/mol) — valores mais negativos são melhores')
                    plt.title('Distribuição de afinidades por alvo (Boxplot)')
                    plt.tight_layout()
                    plt.savefig(outdir / 'affinity_by_target_box.png', dpi=150)
                    plt.close()
                else:
                    save_boxplot_svg(targets, data, outdir / 'affinity_by_target_box.svg')

    print("Feito:")
    print(f" - CSV ordenado: {args.out_sorted}")
    if args.ref_target:
        print(f" - CSV ΔΔG: {args.out_ddg}")
        print(f" - Resumo por ligante: {args.out_ligand_summary}")
    if plot_kinds:
        print(f" - Gráficos em: {args.plot_outdir}")


if __name__ == "__main__":
    main()
