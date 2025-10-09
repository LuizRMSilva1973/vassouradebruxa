## Prioridades de Piloto

Piloto focado em um alvo e poucos ligantes para validar o pipeline ponta‑a‑ponta. Depois, expandir.

### Alvo Prioritário
- FKS — β‑1,3‑glucano‑sintase
  - Justificativa: há inibidores consagrados (echinocandinas) e um triterpenoide (ibrexafungerp) com mecanismos conhecidos; facilita interpretar resultados iniciais.
  - Próximo na fila: CHS — quitina‑sintase (nikkomicina Z, polioxina D).

### Conjunto Piloto de Ligantes (FKS)
- caspofungina.sdf
- ibrexafungerp.sdf

Opcional (rodada seguinte, CHS):
- nikkomicinaZ.sdf
- polioxinaD.sdf

### Entradas Necessárias (a providenciar)
- `targets/FKS.pdb` (modelo do alvo) e `targets/FKS.box` (centro/tamanho do grid)
- `ligands/caspofungina.sdf`, `ligands/ibrexafungerp.sdf`

### Execução do Piloto
1) Verifique MGLTools, Vina e OpenBabel instalados (veja README/instalação).
2) Coloque os arquivos listados acima nos diretórios correspondentes.
3) Rode: `./run_docking.sh -e 16 -n 9`
4) Gere Top‑N: `python3 topn_by_target.py --input docking_results/summary_affinities.csv --outdir docking_results/topN_by_target --top 5`
5) Pós‑proc.: `python3 postprocess_docking.py --input docking_results/summary_affinities.csv --ref-target CHS` (apenas se houver dois alvos para ΔΔG).

### Saídas Esperadas
- `docking_results/summary_affinities.csv`
- `docking_results/topN_by_target/`
- `docking_results/plots/` (se usar `postprocess_docking.py`)

