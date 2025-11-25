#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera targets/CHS.pdb localmente usando ESMFold (esm).
Uso:
  python scripts/build_chs_pdb.py --fasta targets/MP_B2XSE6.fasta --out targets/CHS.pdb [--device cuda|cpu]
"""

import argparse
import sys
from pathlib import Path

import torch


def load_sequence_from_fasta(fp: Path) -> str:
    seq = []
    with fp.open("r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            if ln.startswith(">"):
                continue
            seq.append(ln.strip())
    s = "".join(seq).replace(" ", "").replace("\t", "")
    if len(s) < 100:
        sys.exit(f"[ERRO] Sequência curta/ausente em {fp} (len={len(s)})")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fasta", required=True, help="Arquivo FASTA da CHS (ex.: targets/MP_B2XSE6.fasta)")
    ap.add_argument("--out", required=True, help="Saída PDB (ex.: targets/CHS.pdb)")
    ap.add_argument(
        "--device",
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="cuda ou cpu (padrão: cuda se disponível)",
    )
    args = ap.parse_args()

    fasta = Path(args.fasta)
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    seq = load_sequence_from_fasta(fasta)

    # Carrega ESMFold
    try:
        from esm import pretrained
    except Exception as e:
        sys.exit(
            "[ERRO] Pacote 'esm' não encontrado. Instale-o primeiro (vide instruções de ambiente).\n"
            f"Detalhes: {e}"
        )

    print(f"[INFO] Carregando ESMFold em device={args.device}…")
    model = pretrained.esmfold_v1()
    model = model.eval()
    if args.device != "cpu":
        model = model.to(args.device)

    # Inference
    with torch.no_grad():
        if args.device != "cpu":
            # FP16 acelera em GPU moderna
            with torch.cuda.amp.autocast():
                pdb = model.infer_pdb(seq)
        else:
            pdb = model.infer_pdb(seq)

    outp.write_text(pdb, encoding="utf-8")
    # Validação rápida
    n_atoms = sum(1 for ln in pdb.splitlines() if ln.startswith(("ATOM", "HETATM")))
    print(f"[OK] Gravado {outp} (ATOM/HETATM linhas: {n_atoms})")
    if n_atoms < 500:
        print("[WARN] PDB tem poucas coordenadas; verifique se a sequência está correta.")


if __name__ == "__main__":
    main()

