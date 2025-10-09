#!/usr/bin/env bash
set -euo pipefail

echo "[1/6] Checking prerequisites (vina, obabel)";
command -v vina >/dev/null 2>&1 || { echo "[ERROR] vina not found"; exit 2; }
command -v obabel >/dev/null 2>&1 || { echo "[ERROR] obabel not found"; exit 2; }

echo "[2/6] Ensuring targets and ligands exist"
[[ -s targets/FKS.pdb ]] || { echo "[ERROR] missing targets/FKS.pdb"; exit 2; }
[[ -s targets/FKS.box ]] || { echo "[ERROR] missing targets/FKS.box"; exit 2; }
count=$(ls ligands/*.sdf 2>/dev/null | wc -l || true)
if [[ "$count" -lt 1 ]]; then
  echo "[ERROR] No SDFs in ligands/. Place caspofungina.sdf and ibrexafungerp.sdf"; exit 2
fi

echo "[3/6] Running docking"
VINA_VERBOSE=${VINA_VERBOSE:-0} ./run_docking.sh -e ${EXHAUSTIVENESS:-12} -n ${NUM_MODES:-9}

echo "[4/6] Top-N by target"
python3 topn_by_target.py --input docking_results/summary_affinities.csv \
  --outdir docking_results/topN_by_target --top ${TOPN:-5}

echo "[5/6] Ligand properties (OpenBabel)"
python3 tools/ligand_props_obabel.py --indir ligands --output data/ligantes_props_obabel.csv

echo "[6/6] Multiobjective scoring"
REF_ARG=()
if [[ -s targets/CaLS.pdb && -s targets/CaLS.box ]]; then
  REF_ARG+=( --ref-target CaLS )
fi
python3 tools/score_multiobjective.py --summary docking_results/summary_affinities.csv \
  --props data/ligantes_props_obabel.csv --config config/scoring.yaml "${REF_ARG[@]}"

echo "[DONE] Outputs:"
echo " - docking_results/summary_affinities.csv"
echo " - docking_results/topN_by_target/"
echo " - docking_results/scored.csv"
echo " - docking_results/ranking_overall.csv"

