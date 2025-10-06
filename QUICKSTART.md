# Quickstart

1) Pré-requisitos
- AutoDock Vina (`vina`), OpenBabel (`obabel`), MGLTools (pythonsh + Utilities24).

2) Estrutura mínima
```
./
  targets/
    CHS.pdb
    CHS.box   # center_*, size_* (ver README)
  ligands/
    nikkomicinaZ.sdf
    polioxinaD.sdf
```

3) Rodar docking
```
chmod +x run_docking.sh
./run_docking.sh -e 16 -n 9
```
Saída: `docking_results/summary_affinities.csv` e subpastas por (alvo x ligante).

4) Top-N por alvo
```
python3 topn_by_target.py --input docking_results/summary_affinities.csv \
  --outdir docking_results/topN_by_target --top 10
```

5) Próximos passos
- Adicionar mais alvos e caixas (`targets/*.box`).
- Popular mais ligantes em `ligands/`.
- Refinar parâmetros (`--exhaustiveness`, `--num-modes`).

