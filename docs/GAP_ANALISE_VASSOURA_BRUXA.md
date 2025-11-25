## Análise de Lacunas — "Vassoura‑de‑Bruxa" (Moniliophthora perniciosa)

Objetivo: alinhar o pipeline in silico existente (focado em C. theobromae) para geração de candidatos com potencial fungicida contra M. perniciosa, apontando faltas e próximos passos práticos.

### 1) Alinhamento de Espécie (Falta)
- O repositório está orientado a C. theobromae; a doença‑alvo aqui é a vassoura‑de‑bruxa (M. perniciosa).
- Ações:
  - Adicionar `data/moniliophthora/` com proteoma/anotações de M. perniciosa (cepa relevante à região/variedade de cacau).
  - Mapear ortólogos para alvos de parede (FKS/CHS/AGS/GEL/CDA) e priorizar isoformas essenciais/expressas em fase biotrófica/necrotrofa.
  - Atualizar `data/templates/alvos_template.csv` com IDs de M. perniciosa e evidências (domínios, TM, motivos catalíticos).

### 2) Modelos Estruturais de Alvos (Falta)
- Ausência de PDB/PDBQT específicos de M. perniciosa.
- Ações:
  - Gerar modelos por predição/homologia para FKS e CHS de M. perniciosa; validar confiança/cobertura de sítio.
  - Orientar em membrana e limpar PDBs para docking; salvar em `targets/MP_*.(pdb|pdbqt)`.
  - Definir caixas `targets/MP_*.box` com base em cavidade catalítica/alostérica (ver `docs/BOX_TUNING.md`).

### 3) Conjunto de Ligantes e Propriedades (Parcial)
- Existem exemplos (caspofungina/ibrexafungerp, nikkomicina/polioxina), mas faltam listas completas e propriedades padronizadas.
- Ações:
  - Curar um painel: referências (echinocandinas/triterpenoides, análogos UDP‑GlcNAc), bibliotecas focadas e compostos desenvolvíveis.
  - Popular `ligands/` com SDF/SMILES e calcular propriedades: MW, logP/logD pH 5–6, TPSA, pKa/carga, SA, alertas PAINS.
  - Considerar propriedades de mobilidade xilemática/floemática (índice XyMove já rascunhado) visando penetração sistêmica na planta.

### 4) Seleção Multiobjetivo e Seletividade (Parcial)
- `config/scoring.yaml` é rascunho e não há alvo de referência para ΔΔG específico de M. perniciosa.
- Ações:
  - Definir alvo(s) de referência para seletividade (ex.: homólogo da planta/cacau para evitar fitotoxicidade, ou proteína fúngica não desejada).
  - Recalibrar pesos/limiares após primeira rodada robusta de docking; documentar racional em `docs/CRITERIOS_GO_NO_GO.md`.

### 5) Validação e Robustez In Silico (Falta)
- Faltam testes de sensibilidade e variação de parâmetros de docking.
- Ações:
  - Rodadas com `--exhaustiveness` e `--num-modes` variados; replicar seeds; checar estabilidade de ranking.
  - Checar alternativas ao Vina (ex.: Smina) para macro‑cíclicos/grandes (caspofungina).
  - Gerar Pareto fronts e relatório de robustez.

### 6) Ponte para o Mundo Real (Falta)
- Não há plano de validação experimental e critérios de progressão para fungicida em cacau.
- Ações sugeridas (fora do escopo de código, mas necessárias ao objetivo final):
  - Ensaios in vitro de crescimento micelial (MIC, MFC) de M. perniciosa com top‑candidatos.
  - Ensaios em tecidos de cacau (galhos/mudas) para eficácia e fitotoxicidade.
  - Considerar formulação e compatibilidade agronômica; avaliar risco de resistência (hotspots em FKS/CHS) e combinações de alvos.

### 7) Organização e Reprodutibilidade (Parcial)
- Há scripts e docs sólidos; faltam preenchimentos e automações específicas.
- Ações:
  - Preencher `data/templates/*` (alvos/ligantes) com foco em M. perniciosa.
  - Registrar metadados de execução (versões, seeds) e dossiê por candidato (pose, ΔG/ΔΔG, XyMove, SA, alertas).

### Entregas Minimais para “Próximo Passo”
1) `targets/MP_FKS.pdb` + `targets/MP_FKS.box` e 1 alvo adicional (CHS).
2) 8–15 ligantes prioritários preparados em `ligands/` com propriedades em `data/ligantes_props_*.csv`.
3) `docking_results/summary_affinities.csv` + `postprocess_docking.py` com ΔΔG e gráficos.
4) `config/scoring.yaml` recalibrado + `docs/CRITERIOS_GO_NO_GO.md` preenchido.

