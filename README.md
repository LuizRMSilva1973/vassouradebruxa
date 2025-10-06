#!/usr/bin/env
# C. theobromae — Docking in silico

Pipeline para preparar alvos/ligantes e rodar AutoDock Vina em lote, gerando um resumo de afinidades e Top-N por alvo.

## Estrutura
- `targets/`: PDBs dos alvos e caixas `*.box` (grid).
- `ligands/`: estruturas dos ligantes (`.sdf/.mol/.mol2/.pdb`).
- `docking_results/`: saídas do Vina (por alvo x ligante) + `summary_affinities.csv`.
- `md_results/`: reservado para dinâmica molecular (não usado aqui).
- `run_docking.sh`: orquestra preparo e docking.
- `topn_by_target.py`: pós-processamento do `summary_affinities.csv`.
- `install_in_silico.sh`: instalador de dependências no Linux.

## Instalação (opcional)
```
chmod +x install_in_silico.sh
./install_in_silico.sh
```
Inclui: AutoDock Vina, OpenBabel, MGLTools, GROMACS, PyMOL. Também cria `~/Ctheobromae_in_silico` (não obrigatório usar).

## Preparação dos dados
1) Coloque os alvos como `targets/<ALVO>.pdb`.
2) Para cada alvo, crie uma caixa `targets/<ALVO>.box` (veja `targets/EXAMPLE.box`). Formato:
```
center_x=10.0
center_y=15.0
center_z=20.0
size_x=20.0
size_y=20.0
size_z=20.0
```
- O nome do `.box` deve corresponder ao PDB do alvo.
- `size_*` em Å; cubra o sítio ativo.
3) Coloque ligantes em `ligands/` (`.sdf/.mol/.mol2/.pdb`).

## Execução do docking
```
chmod +x run_docking.sh
./run_docking.sh -e 16 -n 9
```
Parâmetros úteis:
- `-e/--exhaustiveness N`: exaustividade do Vina (padrão 16).
- `-n/--num-modes N`: número de poses (padrão 9).
- `-t/--threads N`: paralelização com GNU parallel (se instalado).
- `--cpu N`: passado ao Vina por job.

Saída principal: `docking_results/summary_affinities.csv`.

## Top-N por alvo
Após o docking, gere Top-N:
```
python3 topn_by_target.py --input docking_results/summary_affinities.csv \
  --outdir docking_results/topN_by_target --top 10
```
Gera um CSV por alvo (`<ALVO>_top10.csv`) e um combinado (`combined_top10.csv`).

## Dicas
- MGLTools deve estar instalado; o `run_docking.sh` tenta localizar `pythonsh` e `Utilities24` automaticamente.
- OpenBabel (`obabel`) é usado para gerar coordenadas 3D e converter ligantes.
- Para um teste rápido, use 1 alvo + 2 ligantes e ajuste `size_*` da caixa para um cubo de ~20–24 Å.
