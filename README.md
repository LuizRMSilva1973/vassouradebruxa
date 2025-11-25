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

## Automação rápida (Makefile)
Com `vina` e `obabel` no `PATH`, use os alvos abaixo:
```
make test            # pytest -q (5 testes)
make prep_ligands    # gera SDF/3D e data/ligantes_props_obabel.csv a partir de config/ligantes_fks8wl6.txt
make dock_fks8wl6    # docking Vina sequencial para targets/FKS_8WL6.pdbqt (saída: docking_results/summary_affinities.csv)
make fks_pipeline    # dock_fks8wl6 + score + pareto + shortlist
```
Scripts utilizados:
- `tools/prep_ligands.sh`: converte ligantes (SDF/SMI/SMILES) para SDF 3D e recalcula propriedades.
- `tools/dock_fks8wl6.sh`: roda Vina ligante a ligante, com timeout adaptável (flag `BIG` no arquivo de ligantes) e extrai a melhor afinidade para o CSV.

Customize ligantes/flags em `config/ligantes_fks8wl6.txt` (segunda coluna opcional `BIG` para ligantes grandes). Caixas/receitores devem estar em `targets/FKS_8WL6.pdbqt` e `targets/FKS_8WL6.box`.

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

### Modelagem de Novos Alvos com ColabFold

Para gerar modelos 3D de alvos sem estrutura experimental, como a CHS, o ColabFold é utilizado.

1.  **Acesse o Notebook:** [ColabFold on Google Colab](https://colab.research.google.com/github/sokrypton/ColabFold/blob/main/beta/AlphaFold2.ipynb).
2.  **Ambiente:** Configure o ambiente de execução para **GPU**.
3.  **Sequência:** Cole a sequência FASTA do alvo (ex: de `targets/MP_B2XSE6.fasta`) no campo `query_sequence`.
4.  **Parâmetros:** Use as configurações recomendadas:
    *   `num_recycles`: `3` a `6`
    *   `model_type`: `AlphaFold2-ptm`
    *   `msa_mode`: `MMseqs2 (UniRef+Environmental)`
    *   `pair_mode`: `unpaired`
5.  **Execução:** Rode as células do notebook.
6.  **Download e Preparação:** Baixe o PDB com melhor ranking, renomeie para `targets/CHS.pdb` e siga as instruções em `notebooks/CHS_ColabFold.md` para preparar os arquivos `.pdbqt` e `.box`.

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

## Plano de Pesquisa e Análise
- Objetivo: identificar candidatos para controle da “vassoura‑de‑bruxa” (C. theobromae) visando alvos de parede celular (principalmente CHS e FKS), usando triagem in silico e critérios multiobjetivo com foco em eficácia e mobilidade xilemática.
- Alvos e priorização:
  - CHS (quitina‑sintase): prioridade pelas evidências de alvo clássico de UDP‑GlcNAc análogos (nikkomicina/polioxina) e boa perspectiva de seletividade.
  - FKS (β‑1,3‑glucano‑sintase): prioridade alta como alvo validado por echinocandinas/triterpenoides (ex.: ibrexafungerp), com atenção a propriedades para XyMove.
- Fluxo (alto nível):
  1) Curadoria de alvos e modelagem (AlphaFold/ColabFold quando necessário) + definição da caixa de docking no sítio ativo.
  2) Preparação dos ligantes (SDF/SMILES → PDBQT) e cálculo de propriedades (MW, logP/logD, TPSA, carga, HBD/HBA).
  3) Docking (AutoDock Vina) com parâmetros reprodutíveis e logs por par alvo×ligante.
  4) Pós‑processamento e seleção: ΔG, ΔΔG vs referência, Top‑N por alvo, e score multiobjetivo com `config/scoring.yaml`.
  5) Relato e decisão: aplicar `docs/CRITERIOS_GO_NO_GO.md` para classificar Go/Consider/No‑Go.
  6) Planejamento de validação experimental (MIC in vitro, depois tecido/estacas), usando quitosana/nanoquitosana como controle positivo.
- Score multiobjetivo: combina afinidade (ΔG), seletividade (ΔΔG), heurística de mobilidade xilemática (XyMove) e penalidades (PAINS/reatividade), com limiares configuráveis (ver `config/scoring.yaml`).
- Reprodutibilidade: scripts versionados; parâmetros e caixas registrados em `targets/*.box`; seeds e logs do Vina preservados.

Referências rápidas
- Plano detalhado CHS (modelagem + docking): `docs/CHS_DOCKING_PLAN.md`
- Workflow do piloto e prioridades de execução: `docs/WORKFLOW_PILOT.md`, `docs/PRIORIDADES.md`
- Critérios de decisão: `docs/CRITERIOS_GO_NO_GO.md`

Estado e Progresso
- Docking validado (FKS×nikkomicina Z): ΔG ≈ -4.81 kcal/mol (rodada rápida; recomenda‑se exaustividade maior para ranking definitivo).
- Próximo: modelar CHS via ColabFold (guia em `notebooks/CHS_ColabFold.md`), preparar `targets/CHS.pdbqt`/`targets/CHS.box` e rodar CHS×{nikkomicinaZ, polioxinaD}.
- Percentual de avanço atual:
  - Plano de Tarefas (docs/PLANO_TAREFAS.md): 55.6%
  - Checklist (docs/CHECKLIST_STATUS.md): 41.7%
  - Progresso geral (média simples): ~48.7%

## Reprodutibilidade e Dicas
- Logs por par em `docking_results/<ALVO>/<LIGANTE>/*.log` com seed reportada.
- `run_docking.sh` reusa PDBQT existentes e converte apenas o que falta; garante sanitização de receptores.
- Use `VINA_VERBOSE=1` para logs detalhados; para paralelizar, instale `parallel` e use `-t N`.

## Próximas Etapas
- Instalar `rdkit`.
- Usar `auto_prepare_echinocandins.py` para preparar os ligantes equinocandinas com um número reduzido de ligações rotacionáveis.
- Re-executar o docking com os novos ligantes.

- Assim que a rede liberar, rodar o fetch e escalar para 30–50 ligantes, entregando duas shortlists (exploratória/estrita) e o Pareto atualizado, com dossiês dos top-N.

## Créditos
- AutoDock Vina 1.2.x
- OpenBabel
- MGLTools (opcional)
