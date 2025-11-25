#!/usr/bin/env bash
set -euo pipefail

# Full CHS pipeline: (1) ensure model (ESMFold), (2) prepare PDBQT and BOX, (3) docking + scoring.
# Usage:
#   bash scripts/run_full_chs_pipeline.sh [--device cuda|cpu] [--exh 16] [--seed 42]

DEVICE="auto"
EXH=16
SEED=42

while [[ $# -gt 0 ]]; do
  case "$1" in
    --device) DEVICE="$2"; shift 2;;
    --exh) EXH="$2"; shift 2;;
    --seed) SEED="$2"; shift 2;;
    *) echo "[WARN] Unknown arg: $1"; shift;;
  esac
done

progress() { echo "[PROGRESS] $1% - $2"; }

progress 0 "Start full CHS pipeline"

# 1) Ensure CHS.pdb exists; if not, try to build with ESMFold
if [[ ! -s targets/CHS.pdb ]]; then
  echo "[STEP] CHS model not found. Building with ESMFold..."
  devarg=()
  if [[ "$DEVICE" == "cpu" ]]; then devarg=(--device cpu); fi
  if [[ "$DEVICE" == "cuda" ]]; then devarg=(--device cuda); fi
  python3 scripts/build_chs_pdb.py --fasta targets/MP_B2XSE6.fasta --out targets/CHS.pdb "${devarg[@]}"
fi
progress 20 "CHS.pdb ready"

# 2) Prepare PDBQT
if [[ ! -s targets/CHS.pdbqt ]]; then
  echo "[STEP] Preparing CHS.pdbqt via OpenBabel"
  obabel -ipdb targets/CHS.pdb -opdbqt -O targets/CHS.pdbqt -xh --partialcharge gasteiger || \
  obabel -ipdb targets/CHS.pdb -opdbqt -O targets/CHS.pdbqt -xh
fi
progress 35 "CHS.pdbqt ready"

# 3) Build BOX (fallback 26 Å cube)
if [[ ! -s targets/CHS.box ]]; then
  echo "[STEP] Creating initial 26 Å cubic CHS.box"
  python3 tools/compute_box_simple.py --pdb targets/CHS.pdb --fixed-size 26.0 --out targets/CHS.box
fi
progress 45 "CHS.box ready"

# 4) Optional: refine via fpocket if available
if command -v fpocket >/dev/null 2>&1; then
  echo "[STEP] fpocket available. Running cavity detection..."
  fpocket -f targets/CHS.pdb -o chs_fpocket_out >/dev/null 2>&1 || true
  POCKET=$(ls -1 chs_fpocket_out/*/pockets/pocket1_atm.pdb 2>/dev/null | head -n1 || true)
  if [[ -n "${POCKET}" ]]; then
    echo "[STEP] Updating CHS.box from pocket1_atm.pdb"
    python3 tools/compute_box_simple.py --pdb "$POCKET" --margin 4.0 --cubic --out targets/CHS.box
  fi
fi
progress 55 "BOX refined (if fpocket present)"

# 5) Docking vs CHS (uses scripts/run_chs_set.sh)
echo "[STEP] Docking vs CHS (EXH=$EXH, SEED=$SEED)"
EXH=$EXH SEED=$SEED bash scripts/run_chs_set.sh
progress 90 "Docking done"

# 6) Pareto and shortlist
python3 tools/pareto.py --input docking_results/scored.csv --out docking_results/pareto_front.csv
python3 tools/shortlist.py --scored docking_results/scored.csv --out docking_results/shortlist.csv
progress 100 "Pareto & shortlist ready"

echo "[OK] Full CHS pipeline completed. See docking_results/*.csv"

