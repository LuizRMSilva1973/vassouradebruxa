#!/usr/bin/env bash
set -euo pipefail

# Prepare echinocandin ligands with MGLTools (prepare_ligand4.py),
# reducing torsional issues for Vina/SMINA. Handles spaces by normalizing
# filenames (papulacandin_B) and uses a temporary workspace without spaces.
#
# Requirements:
# - obabel in PATH
# - conda env with MGLTools present (e.g., /tmp/miniconda_smina env "smina")
#
# Usage:
#   bash scripts/prepare_echinocandins_mgl.sh [--env smina] \
#     anidulafungin caspofungin micafungin rezafungin "papulacandin B"

ENV_NAME="smina"
LIGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)
      ENV_NAME="$2"; shift 2 ;;
    *)
      LIGS+=("$1"); shift ;;
  esac
done
if [[ ${#LIGS[@]} -eq 0 ]]; then
  LIGS=(anidulafungin caspofungin micafungin rezafungin "papulacandin B")
fi

ROOT_DIR="$(pwd)"
LIG_DIR="${ROOT_DIR}/ligands"
OUT_DIR="${ROOT_DIR}/ligands_mgl"
mkdir -p "${OUT_DIR}"

# Detect conda and prepare_ligand4.py inside the env
if [[ -f "/tmp/miniconda_smina/etc/profile.d/conda.sh" ]]; then
  # shellcheck disable=SC1091
  source "/tmp/miniconda_smina/etc/profile.d/conda.sh"
fi

PREP=""
if command -v conda >/dev/null 2>&1; then
  # search common install paths within env
  PREP_CANDS=(
    "/tmp/miniconda_smina/envs/${ENV_NAME}/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_ligand4.py"
    "/tmp/miniconda_smina/envs/${ENV_NAME}/share/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_ligand4.py"
  )
  for p in "${PREP_CANDS[@]}"; do
    if [[ -f "$p" ]]; then PREP="$p"; break; fi
  done
fi

if [[ -z "${PREP}" ]]; then
  echo "[ERROR] prepare_ligand4.py não encontrado no env '${ENV_NAME}'." >&2
  echo "        Instale via conda (bioconda/conda-forge) e tente novamente." >&2
  exit 2
fi

TMP="/tmp/mglprep_$$"
mkdir -p "${TMP}/in" "${TMP}/out"

echo ">>> Gerando PDB 3D e preparando com MGLTools (env=${ENV_NAME})"
for L in "${LIGS[@]}"; do
  in_sdf="${LIG_DIR}/${L}.sdf"
  base="${L// /_}"
  pdb_local="${TMP}/in/${base}.pdb"
  out_local="${TMP}/out/${base}.pdbqt"
  out_final="${OUT_DIR}/${base}.pdbqt"

  if [[ ! -f "${in_sdf}" ]]; then
    echo "[WARN] SDF ausente: ${in_sdf}; pulando" >&2
    continue
  fi

  echo "[OBABEL] ${L} -> PDB (3D)"
  if ! obabel "${in_sdf}" -O "${pdb_local}" --gen3d >/dev/null 2>&1; then
    echo "[WARN] OpenBabel falhou para ${L}; pulando" >&2
    continue
  fi

  echo "[MGL] ${L} -> PDBQT via prepare_ligand4.py"
  if ! conda run -n "${ENV_NAME}" python "${PREP}" -l "${pdb_local}" -o "${out_local}" -U nphs_lps_waters_nonstdres >/dev/null 2>&1; then
    echo "[WARN] prepare_ligand4.py falhou para ${L}; pulando" >&2
    continue
  fi

  cp -f "${out_local}" "${out_final}"
  echo "[OK] ${out_final}"
done

echo ">>> Concluído. Verifique saídas em: ${OUT_DIR}"

