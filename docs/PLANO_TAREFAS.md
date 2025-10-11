## Plano de Tarefas — Modelagem Multiobjetivo (In Silico)

Escopo: alvos de parede celular (CHS, FKS, AGS, GEL/GAS, CDA) em C. theobromae, com triagem computacional e critérios Go/No-Go.

### Fase 1 — Organização e Dados (Semana 1)
- [x] Inventário inicial do repo e estrutura mínima (feito neste commit)
- [x] Tabela de alvos (IDs, domínios, TM, motivos catalíticos) — `data/templates/alvos_template.csv`
- [x] Tabela de ligantes (SMILES, propriedades, flags) — `data/templates/ligantes_template.csv`
- [x] Definir `config/scoring.yaml` (pesos e limiares iniciais) e `docs/CRITERIOS_GO_NO_GO.md`

### Fase 2 — Docking Piloto (Semana 2)
- [x] Preparar 1–2 alvos com PDB/PDBQT e `*.box` validadas
- [x] Preparar 3–5 ligantes representativos (PDBQT)
- [x] Rodar `./run_docking.sh -e 16 -n 9` e verificar `docking_results/summary_affinities.csv`
- [x] Gerar Top‑N por alvo com `topn_by_target.py` e gráficos com `postprocess_docking.py`

### Fase 3 — Multiobjetivo e Seleção (Semana 3)
- [ ] Calibrar pesos (afinidade, ΔΔG seletividade, XyMove, SA, filtros)
- [ ] Gerar Pareto fronts e lista Top‑N global
- [ ] Consolidar 10–20 candidatos com dossiê técnico

### Fase 4 — QSAR e Robustez (Semana 4)
- [ ] Definir features e conjuntos de treino/validação (externa)
- [ ] Avaliar R²/Q²/RMSE/AUC e domínio de aplicabilidade
- [ ] Relatório de sensibilidade e limitações

### Entregáveis
- [x] `docs/CHECKLIST_STATUS.md` (status) — pronto
- [ ] `docs/CRITERIOS_GO_NO_GO.md` (decisão) — rascunho a preencher
- [x] Templates em `data/templates/` — prontos para preenchimento
- [ ] `config/scoring.yaml` — rascunho a ajustar

Responsáveis/Prazos: preencha colunas “Owner” e “Due” nos templates ou edite este plano conforme a sua equipe.
