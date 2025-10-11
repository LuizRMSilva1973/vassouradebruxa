## Checklist — Status Atual vs. Pendências

Este documento resume o que já existe no repositório e o que falta produzir para a modelagem multiobjetivo in silico de alvos de parede celular em Ceratobasidium theobromae.

### Já Existe (no repo)
- Estrutura de docking com AutoDock Vina: `run_docking.sh`, `topn_by_target.py`, `postprocess_docking.py`.
- Documentação operacional: `README.md`, `QUICKSTART.md`, `CONTRIBUTING.md`.
- Template de caixas (grid) de docking: `targets/EXAMPLE.box`.
- Listas iniciais em CSV:
  - `Alvos_C_theobromae.csv` (CHS, FKS, AGS, GEL/GAS, CDA — em alto nível)
  - `Ligantes_C_theobromae.csv` (exemplos: nikkomicina, polioxina, echinocandinas, ibrexafungerp, quitosana)
- Configuração de lint Python: `ruff.toml`.

### Falta Produzir (alto nível)
- Curadoria detalhada dos alvos: IDs/isoformas em C. theobromae, domínios, topologia TM, motivos catalíticos, evidências de essencialidade/expressão.
- Modelagem/refino estrutural (membrana), sítios de ligação e cavidades relevantes para CHS/FKS/AGS.
- Triagem expandida de ligantes com propriedades calculadas (SMILES, MW, logP/logD, TPSA, pKa, carga, SA score, alertas PAINS).
- Definição formal do esquema multiobjetivo: pesos, restrições e penalidades (afinidade, seletividade ΔΔG, mobilidade xilemática XyMove, sintetizabilidade, filtros de segurança).
- QSAR/ML: protocolo de features, validação (k-fold/externa), domínio de aplicabilidade.
- Pareto fronts e seleção de 10–20 candidatos com dossiê (poses, ΔG/ΔΔG, XyMove, SA, alertas).
- Reprodutibilidade: versões, seeds, caderno de execução e scripts encadeados.

### Próximos Passos (neste repo)
1) Preencher templates de alvos e ligantes em `data/templates/`.
2) Ajustar `config/scoring.yaml` (pesos/limiares) e `docs/CRITERIOS_GO_NO_GO.md`.
3) Popular `targets/` (PDB/PDBQT) e `ligands/` com entradas reais; criar `*.box` por alvo.
4) Rodar docking inicial (1–2 alvos x 3–5 ligantes) para validar pipeline e gerar `summary_affinities.csv`.
5) Usar `postprocess_docking.py` para ΔΔG e gráficos de distribuição por alvo.

