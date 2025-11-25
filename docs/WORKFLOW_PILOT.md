## Workflow do Piloto (com `pilot_assets/`)

### Entradas já fornecidas
- `pilot_assets/targets/FKS_links.txt`: referências (UniProt/AlphaFold/PDB) para obter/validar `targets/FKS.pdb`.
- `pilot_assets/ligands/*.smiles`: SMILES de caspofungina e ibrexafungerp.
- `pilot_assets/data_ligantes_external.csv`: CIDs e URLs 3D SDF (PubChem).
- `pilot_assets/docs/BOX_SUGESTOES.txt`: sugestões para definir a caixa.

### Caminhos de execução

Opção A — Gerar SDFs localmente (sem rede)
1) Converter SMILES → SDF 3D:
```
python3 tools/smiles_to_sdf.py pilot_assets/ligands/caspofungina.smiles \
                               pilot_assets/ligands/ibrexafungerp.smiles \
  --outdir ligands
```
2) Ajustar caixa do alvo (se já tiver `targets/FKS.pdb`):
```
python3 tools/compute_box.py --pdb targets/FKS.pdb --margin 4.0 --cubic --out targets/FKS.box
```
3) Rodar docking piloto (FKS × 2 ligantes):
```
./run_docking.sh -e 16 -n 9
```

Opção B — Baixar SDFs 3D do PubChem (requer rede)
```
python3 tools/fetch_pubchem_sdf.py --input pilot_assets/data_ligantes_external.csv --outdir ligands
```
Depois, seguir para ajuste de caixa e docking.

### Pós-processamento
```
python3 topn_by_target.py --input docking_results/summary_affinities.csv \
  --outdir docking_results/topN_by_target --top 5

python3 postprocess_docking.py --input docking_results/summary_affinities.csv \
  --ref-target CHS  # Use se houver resultados para CHS e FKS
```

### Observações
- Ajuste `targets/FKS.box` conforme `docs/BOX_TUNING.md` e `pilot_assets/docs/BOX_SUGESTOES.txt`.
- Se RDKit não estiver instalado, use o caminho B (PubChem) ou instale via `pip install rdkit-pypi`.

