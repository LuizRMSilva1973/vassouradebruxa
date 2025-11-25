# Construção da Biblioteca de Ligantes

Objetivo: criar 30–50 ligantes prioritários para triagem (CHS/FKS), com SMILES rastreáveis e geração automática de SDF/PDBQT.

Fluxo com SMILES (sem rede):
- Preencha `data/library_smiles.csv` com colunas `ligand,smiles,source,notes`.
- Gere estruturas: `python3 tools/build_library_from_smiles.py --csv data/library_smiles.csv --outdir ligands`

Fluxo com PubChem (requer rede):
- Monte um CSV com `ligante,pubchem_cid,smiles,sdf_3d_url` (ex.: em `pilot_assets/candidate_pubchem.csv`).
- Baixe SDF 3D: `python3 tools/fetch_pubchem_sdf.py --input pilot_assets/candidate_pubchem.csv --outdir ligands`
- Converta para PDBQT (o `run_docking.sh` faz isso automaticamente se faltar).

Boas práticas:
- Priorize séries químicas: análogos de nikkomicina/polioxina (CHS) e triterpenos análogos (FKS).
- Evite duplicatas; registre fontes e observações (alertas/PAINS, carga, massa).
- Para peptídeos (echinocandinas), use Smina se Vina falhar.

