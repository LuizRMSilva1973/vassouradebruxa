#!/usr/bin/env bash
set -euo pipefail

# Detect MGLTools (pythonsh + Utilities24) and print useful info or export lines.
# Usage:
#   bash scripts/detect_mgltools.sh            # human-readable output
#   bash scripts/detect_mgltools.sh --print-exports  # prints export lines to eval

PRINT_EXPORTS=0
if [[ "${1:-}" == "--print-exports" ]]; then PRINT_EXPORTS=1; fi

cands=(
  "$HOME/MGLTools-1.5.7/bin"
  "$HOME/mgltools_x86_64Linux2_1.5.7/bin"
  "/usr/local/MGLTools-1.5.7/bin"
  "/opt/mgltools/bin"
)

# Also scan common roots shallowly
roots=("$HOME" "/usr/local" "/opt" "/usr")
for r in "${roots[@]}"; do
  while IFS= read -r -d '' p; do
    cands+=("$(dirname "$p")")
  done < <(find "$r" -maxdepth 6 -type f -name pythonsh -print0 2>/dev/null || true)
done

found_bin=""
found_rec=""
found_lig=""
for b in "${cands[@]}"; do
  [[ -x "$b/pythonsh" ]] || continue
  base="$b/../MGLToolsPckgs/AutoDockTools/Utilities24"
  if [[ -f "$base/prepare_receptor4.py" && -f "$base/prepare_ligand4.py" ]]; then
    found_bin="$b"
    found_rec="$b/pythonsh $base/prepare_receptor4.py"
    found_lig="$b/pythonsh $base/prepare_ligand4.py"
    break
  fi
done

if [[ -z "$found_bin" ]]; then
  echo "[ERROR] MGLTools (pythonsh + Utilities24) não encontrado nos caminhos comuns." >&2
  echo "Instale o MGLTools 1.5.7 ou a ADFR Suite, ou informe manualmente os caminhos." >&2
  exit 1
fi

if [[ "$PRINT_EXPORTS" -eq 1 ]]; then
  echo "export PREP_REC_CMD=\"$found_rec\""
  echo "export PREP_LIG_CMD=\"$found_lig\""
else
  echo "[OK] Detectado MGLTools: $found_bin"
  echo "PREP_REC_CMD: $found_rec"
  echo "PREP_LIG_CMD: $found_lig"
  echo
  echo "Para exportar automaticamente, rode:"
  echo "  eval \"\$(bash scripts/detect_mgltools.sh --print-exports)\""
fi

