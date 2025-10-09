#!/usr/bin/env
# C. theobromae — Pipeline In Silico (Docking + Pós-processamento + Score)

Este repositório contém um fluxo de trabalho reproduzível para triagem computacional de ligantes em alvos de parede celular (ex.: FKS/CHS/AGS) de Ceratobasidium theobromae usando AutoDock Vina, com pós‑processamento (Top‑N por alvo, ΔΔG de seletividade), gráficos e um score multiobjetivo simples. Inclui scripts utilitários para preparar dados, calcular propriedades e consolidar resultados.

## Estrutura do Repositório
- `targets/`: estruturas PDB dos alvos e caixas de docking `*.box` (centro/tamanho da grade). Ex.: `FKS.pdb`, `FKS.box`.
- `ligands/`: estruturas de ligantes (`.sdf/.mol/.mol2/.pdb`). Exemplos incluídos.
- `docking_results/`: saídas do Vina por `(alvo × ligante)`, resumo `summary_affinities.csv` e derivados (Top‑N, ΔΔG, gráficos, ranking).
- `tools/`: utilitários (cálculo de caixa, propriedades, score multiobjetivo, conversões).
- `scripts/`: helpers de execução (`run_one.sh`, detecção do MGLTools, piloto, etc.).
- `docs/`: planos, critérios e checklist do projeto.
- `config/scoring.yaml`: pesos/limiares para score multiobjetivo.
- `data/`: templates e propriedades calculadas de ligantes.
- `run_docking.sh`: orquestra preparo (alvos/ligantes) e docking em lote (robusto a receptores PDBQT “contaminados”).
- `topn_by_target.py`: gera Top‑N por alvo a partir do resumo.
- `postprocess_docking.py`: ordenações, ΔΔG e gráficos; inclui fallback de gráfico (SVG) mesmo sem matplotlib.

## Pré‑requisitos
- AutoDock Vina (`vina`) 1.2.x no `PATH`.
- OpenBabel (`obabel`, `obprop`) no `PATH`.
- (Opcional) MGLTools 1.5.7 (`pythonsh` + `Utilities24`) para preparação PDBQT com AT‑Tools; quando ausente, o pipeline usa OpenBabel como fallback.
- (Opcional) `matplotlib` para gráficos PNG; sem ele, o script gera boxplot em SVG.

Instalação opcional (Linux):
```
chmod +x install_in_silico.sh
./install_in_silico.sh
```

## Preparação dos Dados
1) Alvos: adicione `targets/<ALVO>.pdb`.
2) Caixa por alvo: crie `targets/<ALVO>.box` (mesmo nome do `.pdb`). Formato:
```
center_x=10.0
center_y=15.0
center_z=20.0
size_x=20.0
size_y=20.0
size_z=20.0
```
- `size_*` em Å; cubra o sítio ativo.
3) Ligantes: coloque em `ligands/` (`.sdf/.mol/.mol2/.pdb`).

Dica (sanitização de receptor): caso `targets/<ALVO>.pdbqt` já exista e contenha tokens de ligante (`ROOT/BRANCH/TORSDOF`), o `run_docking.sh` detecta e sanitiza automaticamente. Isso evita o erro do Vina “Unknown or inappropriate tag found in rigid receptor”.

## Execução do Docking (Lote)
```
chmod +x run_docking.sh
./run_docking.sh -e 16 -n 9 --cpu 1
```
Parâmetros úteis:
- `-e/--exhaustiveness N`: exaustividade (padrão 16).
- `-n/--num-modes N`: nº de poses (padrão 9).
- `-t/--threads N`: paralelização com GNU parallel (se disponível).
- `--cpu N`: encadeado para o Vina por job.
- `--no-topn`: desativa geração automática de Top‑N ao final.

Saídas principais:
- `docking_results/summary_affinities.csv` (resumo por par alvo×ligante).
- Subpastas com logs/poses: `docking_results/<ALVO>/<LIGANTE>/`.

Execução de 1 par (debug rápido):
```
EXHAUSTIVENESS=12 NUM_MODES=9 VINA_CPU=1 \
  scripts/run_one.sh FKS ibrexafungerp
```

## Pós‑processamento
1) Top‑N por alvo (CSV):
```
python3 topn_by_target.py \
  --input docking_results/summary_affinities.csv \
  --outdir docking_results/topN_by_target --top 10
```
Gera `docking_results/topN_by_target/<ALVO>_top10.csv` e `combined_top10.csv`.

2) Ordenação + ΔΔG + gráficos:
```
python3 postprocess_docking.py \
  --input docking_results/summary_affinities.csv \
  --ref-target FKS_8WL6 \
  --out-sorted docking_results/summary_sorted.csv \
  --out-ddg docking_results/summary_ddg.csv \
  --out-ligand-summary docking_results/ligand_selectivity_summary.csv \
  --plot-outdir docking_results/plots --plots violin,box
```
- Sem `matplotlib`, o script emite aviso e gera boxplot SVG: `docking_results/plots/affinity_by_target_box.svg`.

## Propriedades dos Ligantes
- Via OpenBabel (`obprop`) para `.sdf` em `ligands/`:
```
python3 tools/ligand_props_obabel.py \
  --indir ligands --output data/ligantes_props_obabel.csv
```
- Via RDKit a partir de SMILES (requer `rdkit-pypi`):
```
python3 tools/ligand_props.py \
  --input data/templates/ligantes_template.csv \
  --output data/ligantes_props.csv
```

## Score Multiobjetivo
Configuração: `config/scoring.yaml` (pesos/limiares). Execução:
```
python3 tools/score_multiobjective.py \
  --summary docking_results/summary_affinities.csv \
  --props data/ligantes_props_obabel.csv \
  --config config/scoring.yaml \
  --ref-target FKS_8WL6 \
  --out-scored docking_results/scored.csv \
  --out-ranking docking_results/ranking_overall.csv
```
Saídas:
- `docking_results/scored.csv` (alvo×ligante, com normalizações e `passes_constraints`).
- `docking_results/ranking_overall.csv` (melhor alvo por ligante, com `score`).

Notas de modelagem:
- Afinidade (ΔG): mapeada para [0..1] privilegiando valores ≤ -10 como 1.0 e penalizando > -5.
- Seletividade (ΔΔG): requer `--ref-target` e é favorecida quando ΔG(alvo) ≪ ΔG(referência).
- XyMove (0..1): heurística baseada em logP/TPSA/MW/carga para mobilidade xilemática.

## Resultados (estado atual — exemplo)
- Rodadas rápidas indicaram para `FKS`:
  - ibrexafungerp: ΔG ≈ -4.80 kcal/mol.
  - nikkomicinaZ: ΔG ≈ -4.83 kcal/mol.
- Em `FKS_8WL6`, ambos os ligantes ~0.0 (sem atração no box usado).
- ΔΔG (ref. `FKS_8WL6`) favorece `FKS` (≈ -4.8 kcal/mol) para ambos, no estado atual.
- Limiar default (`min_affinity_kcal_per_mol: -7.0`) não atendido em corrida rápida ⇒ recomenda‑se rodadas mais exaustivas.

## Problemas conhecidos e contornos
- Vina “internal error … tree.h(101)” com caspofungina (macropeptídeo). Opções:
  - Usar Smina ou outro build do Vina (1.2.2/1.2.3);
  - Reduzir graus de liberdade (torsões) do ligante ou usar docking parcialmente rígido;
  - Revisar o box (aumentar `size_*`) e repetir.

## Próximos Passos Sugeridos
- Rodada robusta: `--exhaustiveness 16` e `--num-modes 9` para todos os pares disponíveis.
- Investigar caspofungina: tentar Smina ou Vina alternativo; se indisponível, preparar ligante com torsões limitadas e repetir.
- Expandir alvos: adicionar `CHS.pdb` (e `.box`) e outros alvos (AGS/GEL/CDA) conforme `docs/PLANO_TAREFAS.md`.
- Gráficos completos: instalar `matplotlib` para também gerar violin/PNG.
- Calibrar `config/scoring.yaml` após o lote robusto; revisar `docs/CRITERIOS_GO_NO_GO.md`.
- Preencher templates em `data/templates/` com IDs, SMILES e metadados.

## Reprodutibilidade e Dicas
- Logs por par em `docking_results/<ALVO>/<LIGANTE>/*.log` com seed reportada.
- `run_docking.sh` reusa PDBQT existentes e converte apenas o que falta; garante sanitização de receptores.
- Use `VINA_VERBOSE=1` para logs detalhados; para paralelizar, instale `parallel` e use `-t N`.

## Créditos
- AutoDock Vina 1.2.x
- OpenBabel
- MGLTools (opcional)

