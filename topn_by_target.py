#!/usr/bin/env python3
import argparse
import csv
import os
import sys
from collections import defaultdict


def parse_args():
    p = argparse.ArgumentParser(
        description="Gera Top-N por alvo a partir do summary_affinities.csv"
    )
    p.add_argument("--input", required=True, help="Caminho do summary_affinities.csv")
    p.add_argument("--outdir", required=True, help="Diretório de saída para Top-N")
    p.add_argument("--top", type=int, default=10, help="N do Top-N (padrão: 10)")
    return p.parse_args()


def safe_float(s):
    try:
        return float(s)
    except Exception:
        return None


def load_summary(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {
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
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            sys.exit(
                f"[ERRO] Cabeçalhos ausentes em {path}: {', '.join(sorted(missing))}"
            )
        for r in reader:
            r = dict(r)
            r["affinity"] = safe_float(r.get("best_affinity_kcal_per_mol", ""))
            rows.append(r)
    return rows


def group_by_target(rows):
    g = defaultdict(list)
    for r in rows:
        g[r["target"]].append(r)
    return g


def sort_and_topn(records, n):
    # Menor afinidade (mais negativa) é melhor. NA vai para o fim.
    def key(r):
        aff = r.get("affinity")
        return (aff if aff is not None else float("inf"), r.get("ligand", ""))

    recs = sorted(records, key=key)
    return recs[: max(0, n)]


def write_csv(path, fieldnames, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def main():
    args = parse_args()
    rows = load_summary(args.input)
    if not rows:
        sys.exit("[ERRO] Arquivo de resumo sem registros.")

    # Campos de saída (adiciona 'rank' na frente)
    base_fields = [
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
    out_fields = ["rank"] + base_fields

    grouped = group_by_target(rows)

    combined_out = []
    for target, recs in sorted(grouped.items()):
        top = sort_and_topn(recs, args.top)
        target_rows = []
        for i, r in enumerate(top, start=1):
            out = {k: r.get(k, "") for k in base_fields}
            out["rank"] = i
            target_rows.append(out)
            combined_out.append(out)

        out_path = os.path.join(args.outdir, f"{target}_top{args.top}.csv")
        write_csv(out_path, out_fields, target_rows)

    # combinado
    combined_path = os.path.join(args.outdir, f"combined_top{args.top}.csv")
    write_csv(combined_path, out_fields, combined_out)

    print(f"[OK] Top-{args.top} por alvo salvo em: {args.outdir}")
    print(f"[OK] Resumo combinado: {combined_path}")


if __name__ == "__main__":
    main()

