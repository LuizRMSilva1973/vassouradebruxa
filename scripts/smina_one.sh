#!/usr/bin/env bash
set -euo pipefail

# Robust SMINA runner for a single target×ligand using targets/<T>.box
# - Reads grid center/size from box file
# - Uses conda env 'smina' if available, otherwise 'smina' in PATH
# - Writes logs/poses to docking_results_smina/<T>/<L>/
#
# Usage:
#   bash scripts/smina_one.sh <TARGET_BASE> <LIGAND_PDBQT> [--exhaustiveness 8] [--num-modes 9] [--cpu 1]
#
# Environment variables:
#   SMINA_SEED: Seed for Smina (optional)

if [[ $# -lt 2 ]]; then
  echo "Usage: $(basename "$0") <TARGET_BASE> <LIGAND_PDBQT> [--exhaustiveness N] [--num-modes N] [--cpu N]" >&2
  exit 2
fi

T="$1"; shift
LIG_PDBQT="$1"; shift

EXH=8
NM=9
CPU=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --exhaustiveness) EXH="$2"; shift 2 ;;
    --num_modes)      NM="$2";  shift 2 ;;
    --cpu)            CPU="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

ROOT_DIR="$(pwd)"
TGT_DIR="${ROOT_DIR}/targets"
BOX="${TGT_DIR}/${T}.box"
REC="${TGT_DIR}/${T}.pdbqt"

[[ -f "${REC}" ]] || { echo "[ERROR] receptor não encontrado: ${REC}" >&2; exit 2; }
[[ -f "${LIG_PDBQT}" ]] || { echo "[ERROR] ligante não encontrado: ${LIG_PDBQT}" >&2; exit 2; }
[[ -f "${BOX}" ]] || { echo "[ERROR] caixa não encontrada: ${BOX}" >&2; exit 2; }

cx=$(grep -E '^center_x=' "${BOX}" | cut -d= -f2)
cy=$(grep -E '^center_y=' "${BOX}" | cut -d= -f2)
cz=$(grep -E '^center_z=' "${BOX}" | cut -d= -f2)
sx=$(grep -E '^size_x='   "${BOX}" | cut -d= -f2)
sy=$(grep -E '^size_y='   "${BOX}" | cut -d= -f2)
sz=$(grep -E '^size_z='   "${BOX}" | cut -d= -f2)

OUT_DIR="${ROOT_DIR}/docking_results_smina/${T}/$(basename "${LIG_PDBQT}" .pdbqt)"
mkdir -p "${OUT_DIR}"
OUTP="${OUT_DIR}/$(basename "${LIG_PDBQT}" .pdbqt)_on_${T}.pdbqt"
LOGF="${OUT_DIR}/$(basename "${LIG_PDBQT}" .pdbqt)_on_${T}.log"

# Resolve smina cmd
SMINA="smina"
if [[ -f "/tmp/miniconda_smina/etc/profile.d/conda.sh" ]]; then
  # shellcheck disable=SC1091
  source "/tmp/miniconda_smina/etc/profile.d/conda.sh"
  if command -v conda >/dev/null 2>&1; then
    SMINA="conda run -n smina smina"
  fi
fi

smina_cmd=("$SMINA")
smina_cmd+=(--receptor "${REC}")
smina_cmd+=(--ligand "${LIG_PDBQT}")
smina_cmd+=(--center_x "$cx" --center_y "$cy" --center_z "$cz")
smina_cmd+=(--size_x "$sx" --size_y "$sy" --size_z "$sz")
smina_cmd+=(--exhaustiveness "$EXH" --num_modes "$NM" --cpu "$CPU")

if [[ -n "${SMINA_SEED:-}" ]]; then
  smina_cmd+=(--seed "${SMINA_SEED}")
fi

set -x
"${smina_cmd[@]}" \
  --out "${OUTP}" \
  > "${LOGF}" 2>&1 || true
set +x

echo "[DONE] Log: ${LOGF}"
echo "[DONE] Out: ${OUTP}"
