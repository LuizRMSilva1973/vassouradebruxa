## Workflow — Moniliophthora perniciosa (Piloto)

Objetivo: rodar um piloto de docking para MP_FKS/MP_CHS com um painel inicial de ligantes.

### Entradas
- Alvos (modelos): `targets/MP_FKS.pdb`, `targets/MP_CHS.pdb` (a providenciar) e caixas `targets/MP_FKS.box`, `targets/MP_CHS.box`.
- Ligantes: `data/moniliophthora/ligantes_mp.csv` (com SMILES para caspofungina/ibrexafungerp; demais a preencher).

### Preparar ligantes (sem rede)
Opção RDKit (recomendado):
```
pip install rdkit-pypi  # se permitido
python3 tools/smiles_to_sdf.py \
  pilot_assets/ligands/caspofungina.smiles \
  pilot_assets/ligands/ibrexafungerp.smiles \
  --outdir ligands
```
Se RDKit indisponível, usar `ligands/*.sdf` pré-gerados (copiar para a pasta).

### Definir caixas
Assim que `targets/MP_*.pdb` estiverem prontos, gerar `.box` com:
```
python3 tools/compute_box.py --pdb targets/MP_FKS.pdb --margin 4.0 --cubic --out targets/MP_FKS.box
python3 tools/compute_box.py --pdb targets/MP_CHS.pdb --margin 4.0 --cubic --out targets/MP_CHS.box
```
Depois, ajuste fino conforme `docs/BOX_TUNING.md`.

### Rodar docking (piloto)
```
chmod +x run_docking.sh
EXHAUSTIVENESS=16 NUM_MODES=9 VINA_CPU=1 ./run_docking.sh
```
Pré-requisitos no PATH: `vina`, `obabel` (+ opcional MGLTools para preparação). Saídas em `docking_results/`.

### Pós-processamento
```
python3 topn_by_target.py --input docking_results/summary_affinities.csv \
  --outdir docking_results/topN_by_target --top 5

python3 postprocess_docking.py --input docking_results/summary_affinities.csv \
  --ref-target MP_CHS --out-ddg docking_results/summary_ddg.csv
```

### Notas
- Preencher `data/moniliophthora/alvos_mp.csv` com IDs e evidências assim que disponíveis.
- Recalibrar `config/scoring.yaml` após a primeira rodada e atualizar `docs/CRITERIOS_GO_NO_GO.md`.

