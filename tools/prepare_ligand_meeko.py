from rdkit import Chem
from rdkit.Chem import AllChem, rdMolTransforms
from meeko import MoleculePreparation, PDBQTWriterLegacy
import sys
import os
from rdkit.Chem.MolStandardize import rdMolStandardize # Importar rdMolStandardize

# uso: python tools/prepare_ligand_meeko.py input.smi output.pdbqt
# input.smi: linha única com SMILES e opcionalmente " lig_name"
smi_path, out_pdbqt = sys.argv[1], sys.argv[2]
with open(smi_path) as f:
    line = f.read().strip()
smiles = line.split()[0]

# 1) ler e sanitizar
mol = Chem.MolFromSmiles(smiles)
if mol is None:
    raise RuntimeError(f"ERRO: Não foi possível ler o SMILES: {smiles}")

# Padronização da molécula (limpeza, tautômeros/protômeros)
# Usar os defaults do CleanupParameters já ajuda
cleaner = rdMolStandardize.CleanupParameters()
mol = rdMolStandardize.Cleanup(mol) # Aplica limpeza básica
# Para gerar tautômeros/protômeros, precisaríamos de um TautomerEnumerator
# ou um WarheadEnumerator, que retornam múltiplas moléculas.
# Por simplicidade, vamos focar na limpeza padrão e na protonação padrão com AddHs.
# Se o objetivo é gerar *variantes* de tautômeros/protômeros,
# o script precisaria ser mais complexo para lidar com múltiplas saídas.

mol = Chem.AddHs(mol)  # hidrogênios explícitos (protonação padrão em pH neutro)

# 2) conformer 3D (ETKDGv3) + minimização MMFF
try:
    AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
    AllChem.MMFFOptimizeMolecule(mol, maxIters=500)
except Exception as e:
    print(f"ERRO na geração 3D ou minimização MMFF: {e}", file=sys.stderr)
    print("- Verifique SMILES (sais/contra-íons/tautômeros).", file=sys.stderr)
    print("- Tente remover Hs e regenerar 3D.", file=sys.stderr)
    print("- Use ETKDGv3 com useMacrocycleTorsions=True se houver macrociclo.", file=sys.stderr)
    raise

# 3) preparar p/ Vina/Smina: charges de Gasteiger e árvore de torções
prep = MoleculePreparation()  # Meeko decide torções de forma segura
prepped_mols = prep.prepare(mol) # Pode retornar uma lista de PreparedMolecule

# 4) escrever PDBQT
writer = PDBQTWriterLegacy()
with open(out_pdbqt, "w", encoding="utf-8") as g:
    # se quiser só o primeiro modelo:
    prepped_iter = prepped_mols if isinstance(prepped_mols, (list, tuple)) else [prepped_mols]
    prepped_first = next(iter(prepped_iter))
    result = writer.write_string(prepped_first)

    pdbqt_string = None
    extra = {}
    if isinstance(result, tuple):
        pdbqt_string = result[0]
        # se houver campos extras, guarde para log
        if len(result) > 1:
            extra["status"] = result[1]
        if len(result) > 2:
            extra["messages"] = result[2]
    else:
        pdbqt_string = result

    if not pdbqt_string or not pdbqt_string.strip():
        raise RuntimeError("Meeko retornou PDBQT vazio para este ligante.")

    # (opcional) logar status/mensagens
    if extra:
        print(f"MEeko extra: {extra}", file=sys.stderr)

    if not pdbqt_string.endswith("\n"):
        pdbqt_string += "\n"
    g.write(pdbqt_string)

print("OK:", os.path.basename(out_pdbqt))