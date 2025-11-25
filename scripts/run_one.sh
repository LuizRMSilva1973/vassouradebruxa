#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 2 ]]; then
  echo "Usage: $(basename "$0") <TARGET_BASE> <LIGAND_BASE>"; exit 2; fi
T="$1"; L="$2"
export VINA_VERBOSE=1
WORKDIR=${WORKDIR:-$PWD}
TARGETS_DIR="${WORKDIR}/targets"
LIGANDS_DIR="${WORKDIR}/ligands"

echo "[INFO] Target: $T, Ligand: $L"

if [[ ! -f "${TARGETS_DIR}/${T}.pdbqt" ]]; then
  if [[ -n "${PREP_REC_CMD:-}" ]]; then
    echo "[INFO] Preparing receptor PDBQT via MGLTools..."
    eval "${PREP_REC_CMD} -r \"${TARGETS_DIR}/${T}.pdb\" -o \"${TARGETS_DIR}/${T}.pdbqt\"" >/dev/null 2>&1
  else
    echo "[INFO] Preparing receptor PDBQT via OpenBabel..."
    obabel -ipdb "${TARGETS_DIR}/${T}.pdb" -opdbqt -O "${TARGETS_DIR}/${T}.pdbqt" -xh -p 7.4 --partialcharge gasteiger || \
obabel -ipdb "${TARGETS_DIR}/${T}.pdb" -opdbqt -O "${TARGETS_DIR}/${T}.pdbqt" -xh
    # Sanitize receptor PDBQT if contains ligand tokens
    if grep -qE '^(ROOT|BRANCH|TORSDOF|ENDROOT|ENDBRANCH)' "${TARGETS_DIR}/${T}.pdbqt" 2>/dev/null; then
      echo "[INFO] Sanitizing receptor PDBQT (removing ligand tokens)..."
      awk 'BEGIN{print "REMARK  Receptor PDBQT sanitized from OpenBabel output"} \
           /^ATOM/ || /^HETATM/ || /^TER/ || /^END$/ || /^REMARK/ {print} \
           {next}' "${TARGETS_DIR}/${T}.pdbqt" > "${TARGETS_DIR}/${T}.pdbqt.sanitized" && \
      mv "${TARGETS_DIR}/${T}.pdbqt.sanitized" "${TARGETS_DIR}/${T}.pdbqt"
    fi
  fi
fi
if [[ ! -f "${LIGANDS_DIR}/${L}.pdbqt" ]]; then
  if [[ -n "${PREP_LIG_CMD:-}" ]]; then
    echo "[INFO] Preparing ligand PDBQT via MGLTools..."
    # First generate PDB 3D via OpenBabel
    obabel "${LIGANDS_DIR}/${L}.sdf" -O "${LIGANDS_DIR}/${L}.pdb" --gen3d >/dev/null 2>&1 || true
    eval "${PREP_LIG_CMD} -l \"${LIGANDS_DIR}/${L}.pdb\" -o \"${LIGANDS_DIR}/${L}.pdbqt\"" >/dev/null 2>&1
  else
    echo "[INFO] Preparing ligand PDBQT via OpenBabel..."
    obabel "${LIGANDS_DIR}/${L}.sdf" -O "${LIGANDS_DIR}/${L}.pdbqt" --gen3d --partialcharge gasteiger || \
obabel "${LIGANDS_DIR}/${L}.sdf" -O "${LIGANDS_DIR}/${L}.pdbqt" --gen3d || \
obabel "${LIGANDS_DIR}/${L}.sdf" -O "${LIGANDS_DIR}/${L}.pdbqt"
  fi
fi # <--- Adicionado 'fi' aqui

if [[ ! -f "${TARGETS_DIR}/${T}.box" ]]; then
  echo "[ERROR] Missing ${TARGETS_DIR}/${T}.box"; exit 2
fi
cx=$(grep '^center_x=' "${TARGETS_DIR}/${T}.box" | cut -d= -f2)
cy=$(grep '^center_y=' "${TARGETS_DIR}/${T}.box" | cut -d= -f2)
cz=$(grep '^center_z=' "${TARGETS_DIR}/${T}.box" | cut -d= -f2)
sx=$(grep '^size_x=' "${TARGETS_DIR}/${T}.box" | cut -d= -f2)
sy=$(grep '^size_y=' "${TARGETS_DIR}/${T}.box" | cut -d= -f2)
sz=$(grep '^size_z=' "${TARGETS_DIR}/${T}.box" | cut -d= -f2)

OUTDIR="${WORKDIR}/docking_results/${T}/${L}"
mkdir -p "$OUTDIR"

vina_cmd=(vina)
vina_cmd+=(--receptor "${TARGETS_DIR}/${T}.pdbqt")
vina_cmd+=(--ligand "${LIGANDS_DIR}/${L}.pdbqt")
vina_cmd+=(--center_x "$cx" --center_y "$cy" --center_z "$cz")
vina_cmd+=(--size_x "$sx" --size_y "$sy" --size_z "$sz")
vina_cmd+=(--exhaustiveness "${EXHAUSTIVENESS:-12}" --num_modes "${NUM_MODES:-9}")

if [[ -n "${VINA_SEED:-}" ]]; then
  vina_cmd+=(--seed "${VINA_SEED}")
fi

"${vina_cmd[@]}" --out "${OUTDIR}/${L}_on_${T}.pdbqt" 2>&1 | tee "${OUTDIR}/${L}_on_${T}.log"
echo "[DONE] See log: ${OUTDIR}/${L}_on_${T}.log"