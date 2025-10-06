#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
from collections import defaultdict


def parse_float(s):
    try:
        return float(s)
    except Exception:
        return None


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = []
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
    ap = argparse.ArgumentParser(description="Exporta Top-N ligantes por alvo a partir do summary_affinities.csv")
    ap.add_argument("--input", default="docking_results/summary_affinities.csv", help="CSV de entrada")
    ap.add_argument("--outdir", default="docking_results/topN_by_target", help="Diretório de saída por alvo")
    ap.add_argument("--top", type=int, default=10, help="Quantidade Top-N por alvo (padrão: 10)")
    ap.add_argument("--targets", default=None, help="Lista de alvos a incluir (separados por vírgula)")
    ap.add_argument("--targets-file", default=None, help="Arquivo com um alvo por linha a incluir")
    ap.add_argument("--include-na", action="store_true", help="Incluir entradas sem afinidade numérica (NA) no final")
    args = ap.parse_args()

    rows, cols = read_rows(args.input)

    # filtro de alvos
    allow = None
    if args.targets or args.targets_file:
        allow = set()
        if args.targets:
            allow.update([t.strip() for t in args.targets.split(',') if t.strip()])
        if args.targets_file:
            p = Path(args.targets_file)
            if p.exists():
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line:
                        allow.add(line)
        if allow:
            rows = [d for d in rows if d.get("target") in allow]

    # agrupar por alvo
    by_t = defaultdict(list)
    for d in rows:
        by_t[d.get("target")].append(d)

    index_rows = []
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # campos de saída: manter os existentes e acrescentar rank
    out_fields = list(cols)
    if "rank" not in out_fields:
        out_fields.append("rank")

    for target in sorted(by_t.keys()):
        lst = by_t[target]
        # separar válidos e NAs
        valid = [d for d in lst if d.get("best_affinity_kcal_per_mol_num") is not None]
        na = [d for d in lst if d.get("best_affinity_kcal_per_mol_num") is None]
        valid_sorted = sorted(valid, key=lambda d: d.get("best_affinity_kcal_per_mol_num"))
        top = valid_sorted[: max(0, args.top)]
        # atribuir rank iniciando em 1
        for i, d in enumerate(top, start=1):
            d["rank"] = i
        # opção de incluir NAs no final, sem rank
        out_rows = list(top)
        if args.include-na and na:
            for d in na:
                d["rank"] = "NA"
            out_rows.extend(na)

        out_path = outdir / f"top{args.top}_{target}.csv"
        write_csv(out_path, out_fields, out_rows)
        index_rows.append({"target": target, "file": str(out_path)})

    # índice geral
    idx_fields = ["target", "file"]
    write_csv(outdir / "index.csv", idx_fields, index_rows)

    print(f"Gerado Top-{args.top} por alvo em: {outdir}")
    print(f"Alvos processados: {len(index_rows)}")


if __name__ == "__main__":
    main()

