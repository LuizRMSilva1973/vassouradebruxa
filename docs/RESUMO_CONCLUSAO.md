## Resumo de Conclusão — Pipeline In Silico (Vassoura-de-Bruxa)

### O que já foi executado
- Docking (AutoDock Vina, e=16 n=9) concluído para CHS e FKS/FKS_8WL6; resumo em `docking_results/summary_affinities.csv`.
- Scoring multiobjetivo aplicado (`config/scoring.yaml` atual) com XyMove e ΔΔG (ref. FKS_8WL6); saídas em `docking_results/consensus_*`.
- Shortlist automática gerada (`docking_results/consensus_shortlist.csv`) e fronteira de Pareto (`docking_results/consensus_pareto_front.csv`).

### Achados principais (in silico)
- CHS (caixa 30 Å): melhor ΔG para nikkomicina Z (-9.20 kcal/mol), nikkomicina X (-8.67), poacic acid (-8.47), ibrexafungerp (-8.38). Indica sítio catalítico bem definido.
- FKS (modelo principal): afinidades moderadas (-6.65 a -5.39 kcal/mol). Papulacandin B, rezafungin, poacic acid e ibrexafungerp cruzaram filtros do score; micafungin ficou fora por XyMove baixo.
- FKS_8WL6 (PDB catalítico): ΔG = 0 para todos os ligantes → caixa/receptor precisam de revisão (provável PDBQT contaminado ou caixa fora do sítio).
- Shortlist atual (passando constraints): poacic acid, papulacandin B, rezafungin, ibrexafungerp (todos em FKS). Pareto sugere priorizar poacic acid (melhor XyMove) + papulacandin B/rezafungin (melhor ΔG).

### Lacunas críticas para concluir
- Estruturas de Moniliophthora perniciosa ainda não integradas (ver `docs/GAP_ANALISE_VASSOURA_BRUXA.md`): falta `targets/MP_FKS.pdb/.box` e `targets/MP_CHS.pdb/.box`.
- Revisar preparo/caixa do receptor FKS_8WL6: ΔG zero invalida ΔΔG de seletividade e distorce o score.
- Propriedades de ligantes incompletas (`data/moniliophthora/ligantes_mp.csv` e `data/templates/ligantes_template.csv` têm SMILES/props faltantes).
- Pesos/limiares do score estão brandos (`min_affinity_kcal_per_mol: -5.5`); carece recalibração após fix de FKS_8WL6.
- Não há reprodutibilidade de seeds/exaustividade registrada por alvo/ligante (logs existem, mas falta tabela de metadados).

### Próximas ações recomendadas
1) Corrigir FKS_8WL6: limpar PDB/PDBQT (remover tokens ROOT/BRANCH/TORSDOF), redefinir caixa no sítio catalítico e repetir docking dos 8 ligantes → recalcular ΔΔG e score.
2) Completar propriedades de ligantes: preencher SMILES/props faltantes nos CSV de templates/moniliophthora; rodar `tools/ligand_props.py` ou `tools/ligand_props_obabel.py` para atualizar `data/ligantes_props_obabel.csv`.
3) Integrar alvos de M. perniciosa: gerar/obter `targets/MP_FKS.pdb` e `targets/MP_CHS.pdb`, criar `*.box` (ver `docs/BOX_TUNING.md`) e executar lote piloto (≥5 ligantes priorizados).
4) Recalibrar score (`config/scoring.yaml` e `docs/CRITERIOS_GO_NO_GO.md`) com: limiar de afinidade ≤ -7.0, seletividade ≤ -1.0, XyMove ≥ 0.6; reprocessar `consensus_*`.
5) Gerar dossiê final: Top‑N por alvo (poses, ΔG/ΔΔG), gráfico de distribuição (usar `postprocess_docking.py` com `--plot-outdir`), e tabela Go/Consider/No-Go conforme os critérios revisados.
