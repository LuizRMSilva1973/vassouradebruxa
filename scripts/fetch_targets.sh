#!/usr/bin/env bash
set -euo pipefail

# Fetch AlphaFold PDBs for a list of UniProt IDs and prepare boxes with a fixed cubic size.
# Usage examples:
#   ./scripts/fetch_targets.sh CHS Q00764 Q12470 Q07843
#   ./scripts/fetch_targets.sh CaLS Q9FGD1 Q9FGR0 Q9FGE4 Q8L7R3

if [[ $# -lt 2 ]]; then
  echo "Usage: $(basename "$0") <BASE_NAME> <UNIPROT1> [UNIPROT2 ...]"; exit 2
fi

BASE="$1"; shift
mkdir -p targets
got=""
for acc in "$@"; do
  url="https://alphafold.ebi.ac.uk/files/AF-${acc}-F1-model_v4.pdb"
  out="targets/${BASE}_${acc}.pdb"
  echo "[DL] $url -> $out"
  if curl -L -fS "$url" -o "$out"; then
    got="$out"
    break
  else
    rm -f "$out" || true
  fi
done

if [[ -n "$got" ]]; then
  cp -f "$got" "targets/${BASE}.pdb"
  python3 tools/compute_box_simple.py --pdb "targets/${BASE}.pdb" --fixed-size 26.0 --out "targets/${BASE}.box" || true
  echo "[OK] Prepared: targets/${BASE}.pdb and targets/${BASE}.box"
else
  echo "[WARN] No AlphaFold PDB fetched for ${BASE}." >&2
  exit 1
fi

