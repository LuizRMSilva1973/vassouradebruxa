#!/usr/bin/env bash
set -euo pipefail

# Dock 5 ligands against CHS and update summaries, ΔΔG (ref=CHS) and ranking.
# Prereqs: provide targets/CHS.pdb (from ColabFold or other) or targets/CHS.pdbqt.

WORKDIR=${WORKDIR:-$PWD}
TARGET=CHS
TGT_DIR="${WORKDIR}/targets"
REC_PDB="${TGT_DIR}/${TARGET}.pdb"
REC_PDBQT="${TGT_DIR}/${TARGET}.pdbqt"
BOX="${TGT_DIR}/${TARGET}.box"

LIG_PREP_DIR="${WORKDIR}/docking_results_smina_auto/FKS/prepared"
OUT_ROOT="${WORKDIR}/docking_results_smina/${TARGET}"

ligs=(anidulafungin caspofungin micafungin rezafungin papulacandin_B)

# Tuning (overridable via environment):
EXH=${EXH:-16}
NM=${NM:-9}
SEED=${SEED:-42}

command -v vina >/dev/null 2>&1 || { echo "[ERR] vina não encontrado"; exit 2; }
command -v obabel >/dev/null 2>&1 || { echo "[ERR] obabel não encontrado"; exit 2; }

# Prepare receptor PDBQT if needed
if [[ ! -s "$REC_PDBQT" ]]; then
  if [[ ! -s "$REC_PDB" ]]; then
    echo "[ERR] Receptor ausente. Forneça ${REC_PDB}." >&2
    exit 2
  fi
  echo "[INFO] Preparando receptor PDBQT via OpenBabel..."
  obabel -ipdb "$REC_PDB" -opdbqt -O "$REC_PDBQT" -xh --partialcharge gasteiger || \
  obabel -ipdb "$REC_PDB" -opdbqt -O "$REC_PDBQT" -xh
fi

# Prepare box if missing (fallback: auto box around all atoms, fixed size 26 Å)
if [[ ! -s "$BOX" ]]; then
  echo "[WARN] ${BOX} ausente. Gerando caixa simples (26 Å, centrada na estrutura)."
  python3 tools/compute_box_simple.py --pdb "$REC_PDB" --fixed-size 26.0 --out "$BOX" || \
  {
    echo "center_x=0.0" > "$BOX"; echo "center_y=0.0" >> "$BOX"; echo "center_z=0.0" >> "$BOX";
    echo "size_x=26.0" >> "$BOX"; echo "size_y=26.0" >> "$BOX"; echo "size_z=26.0" >> "$BOX";
  }
fi

cx=$(grep -E '^center_x=' "$BOX" | cut -d= -f2)
cy=$(grep -E '^center_y=' "$BOX" | cut -d= -f2)
cz=$(grep -E '^center_z=' "$BOX" | cut -d= -f2)
sx=$(grep -E '^size_x='   "$BOX" | cut -d= -f2)
sy=$(grep -E '^size_y='   "$BOX" | cut -d= -f2)
sz=$(grep -E '^size_z='   "$BOX" | cut -d= -f2)

TOTAL=${#ligs[@]}
DONE=0
for L in "${ligs[@]}"; do
  LIG_PDBQT="${LIG_PREP_DIR}/${L}.pdbqt"
  if [[ ! -s "$LIG_PDBQT" ]]; then
    alt=${L//_/ };
    test -s "${LIG_PREP_DIR}/${alt}.pdbqt" && LIG_PDBQT="${LIG_PREP_DIR}/${alt}.pdbqt"
  fi
  if [[ ! -s "$LIG_PDBQT" ]]; then
    echo "[SKIP] Ligante não encontrado em ${LIG_PREP_DIR}: ${L}"; ((DONE++)); continue
  fi
  OUTDIR="${OUT_ROOT}/${L}"; mkdir -p "$OUTDIR"
  echo "[RUN] ${TARGET}/${L} (exh=${EXH}, modes=${NM}, seed=${SEED})"
  vina --receptor "$REC_PDBQT" --ligand "$LIG_PDBQT" \
    --center_x "$cx" --center_y "$cy" --center_z "$cz" \
    --size_x "$sx" --size_y "$sy" --size_z "$sz" \
    --exhaustiveness "${EXH}" --num_modes "${NM}" --seed "${SEED}" \
    --out "${OUTDIR}/${L}_on_${TARGET}.pdbqt" \
    > "${OUTDIR}/${L}_on_${TARGET}.log" 2>&1 || true
  ((DONE++))
  echo "[PROGRESS] ${DONE}/${TOTAL} ($((DONE*100/TOTAL))%)"
done

# Rebuild and score with CHS as reference
python3 tools/rebuild_summary_from_logs.py --roots docking_results_smina docking_results_smina_auto --out docking_results/summary_affinities.csv
python3 postprocess_docking.py --input docking_results/summary_affinities.csv --ref-target CHS --out-ddg docking_results/summary_ddg.csv --out-ligand-summary docking_results/ligand_selectivity_summary.csv --out-sorted docking_results/summary_sorted.csv --plots box --plot-outdir docking_results/plots
python3 tools/score_multiobjective.py --summary docking_results/summary_affinities.csv --props data/ligantes_props_obabel.csv --config config/scoring.yaml --ref-target CHS --out-scored docking_results/scored.csv --out-ranking docking_results/ranking_overall.csv
echo "[OK] Docking CHS concluído e ranking atualizado (ref: CHS)."
