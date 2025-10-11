## CHS — Modelagem e Docking (Passo a Passo)

Objetivo: modelar CHS de Moniliophthora (FASTA já no repo) e rodar docking com nikkomicina Z e polioxina D.

### 1) Modelar a CHS (ColabFold)
- FASTA disponíveis:
  - `targets/MP_B2XSE6.fasta` (preferencial; sequência longa com motivos catalíticos QRRRW/DXH)
  - `targets/MP_C0LT25.fasta` (fragmento)
- Use o guia em `notebooks/CHS_ColabFold.md` para gerar `CHS_model.pdb` no Colab.
- Ao finalizar, salve o arquivo como `targets/CHS.pdb` neste repositório.

### 2) Preparar caixa (box) no sítio ativo
- O sítio catalítico da CHS inclui o motivo `QRRRW` e `DXH` (região citosólica). Gere uma caixa cúbica inicial:
```
python3 tools/compute_box.py --pdb targets/CHS.pdb \
  --chain auto --around-motif QRRRW --size 24 24 24 \
  --out targets/CHS.box
```
- Se o motivo não for encontrado (numeração/resíduos), use caixa fixa e ajuste por visualização (PyMOL/ChimeraX):
```
python3 tools/compute_box_simple.py --pdb targets/CHS.pdb \
  --fixed-size 26.0 --out targets/CHS.box
```

### 3) Preparar ligantes
- Nikkomicina Z já está em `ligands/nikkomicinaZ.sdf` (e `.pdbqt`).
- Polioxina D: buscar no PubChem (CID) e baixar SDF 3D; depois converter:
```
python3 tools/fetch_pubchem_sdf.py --cid <CID_POLIOXINA_D> --out ligands/polioxinaD.sdf
obabel ligands/polioxinaD.sdf -O ligands/polioxinaD.pdbqt --gen3d --partialcharge gasteiger
```

### 4) Docking rápido (validação)
```
cx=$(grep -E '^center_x=' targets/CHS.box | cut -d'=' -f2)
cy=$(grep -E '^center_y=' targets/CHS.box | cut -d'=' -f2)
cz=$(grep -E '^center_z=' targets/CHS.box | cut -d'=' -f2)
sx=$(grep -E '^size_x=' targets/CHS.box | cut -d'=' -f2)
sy=$(grep -E '^size_y=' targets/CHS.box | cut -d'=' -f2)
sz=$(grep -E '^size_z=' targets/CHS.box | cut -d'=' -f2)
mkdir -p docking_results/quicktest_chs
vina --receptor targets/CHS.pdbqt --ligand ligands/nikkomicinaZ.pdbqt \
  --center_x "$cx" --center_y "$cy" --center_z "$cz" \
  --size_x "$sx" --size_y "$sy" --size_z "$sz" \
  --exhaustiveness 8 --num_modes 9 --cpu 2 \
  --out docking_results/quicktest_chs/nikkomicinaZ_on_CHS.pdbqt \
  > docking_results/quicktest_chs/nikkomicinaZ_on_CHS.log 2>&1

vina --receptor targets/CHS.pdbqt --ligand ligands/polioxinaD.pdbqt \
  --center_x "$cx" --center_y "$cy" --center_z "$cz" \
  --size_x "$sx" --size_y "$sy" --size_z "$sz" \
  --exhaustiveness 8 --num_modes 9 --cpu 2 \
  --out docking_results/quicktest_chs/polioxinaD_on_CHS.pdbqt \
  > docking_results/quicktest_chs/polioxinaD_on_CHS.log 2>&1
```

### 5) Docking em lote (pipeline do repo)
- Após validar, rode o lote completo:
```
./run_docking.sh -e 16 -n 9 -t 4
```

### 6) Pontuação multiobjetivo e seleção
```
python3 tools/score_multiobjective.py \
  --summary docking_results/summary_affinities.csv \
  --props data/ligantes_props_obabel.csv \
  --config config/scoring.yaml \
  --ref-target FKS_8WL6
```
- Go: ΔG ≤ -7.0; ΔΔG ≤ -1.0; XyMove ≥ 0.6; score ≥ 0.70.
- Consider: ΔG ≤ -6.0; score 0.55–0.70.

### 7) Próximos passos
- Revisar poses/contatos (PyMOL), ajustar a caixa se necessário, repetir docking com `--exhaustiveness 32`.
- Montar dossiê Top‑N e preparar ensaio MIC in vitro (nikkomicinaZ/polioxinaD como candidatos CHS; ibrexafungerp como referência FKS; quitosana como controle positivo).

