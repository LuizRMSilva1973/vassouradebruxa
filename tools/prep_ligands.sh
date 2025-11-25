#!/usr/bin/env bash
# Prepara ligantes: gera .sdf (com 3D) e recalcula ligantes_props_obabel.csv

set -euo pipefail

if ! command -v obabel >/dev/null 2>&1; then
  echo "[ERR] obabel não encontrado no PATH (instale OpenBabel)" >&2
  exit 2
fi
if ! command -v obprop >/dev/null 2>&1; then
  echo "[ERR] obprop não encontrado no PATH (faz parte do OpenBabel)" >&2
  exit 2
fi

LIG_LIST=${1:-config/ligantes_fks8wl6.txt}
LIG_DIR=ligands
PROPS_OUT=data/ligantes_props_obabel.csv

echo "[INFO] Lista de ligantes: $LIG_LIST"
echo "[INFO] Diretório de ligantes: $LIG_DIR"

if [[ ! -f "$LIG_LIST" ]]; then
  echo "[ERR] Arquivo de lista de ligantes não encontrado: $LIG_LIST" >&2
  exit 1
fi

mkdir -p "$LIG_DIR"

while IFS= read -r raw; do
  # remove comentários inline e espaços nas pontas
  raw="${raw%%#*}"
  raw="$(printf '%s' "$raw" | sed 's/^ *//;s/ *$//')"
  [[ -z "${raw:-}" ]] && continue

  flag=""
  if [[ "$raw" =~ [[:space:]]+BIG$ ]]; then
    flag="BIG"
    raw="${raw%[[:space:]]BIG}"
    raw="$(printf '%s' "$raw" | sed 's/ *$//')"
  fi
  name="$raw"

  sdf="${LIG_DIR}/${name}.sdf"
  smi="${LIG_DIR}/${name}.smi"
  smiles="${LIG_DIR}/${name}.smiles"

  if [[ -s "$sdf" ]]; then
    echo "[OK] $sdf já existe (não vou regenerar)"
  elif [[ -s "$smi" ]]; then
    echo "[GEN] $name: $smi -> $sdf (--gen3d)"
    obabel "$smi" -O "$sdf" --gen3d
  elif [[ -s "$smiles" ]]; then
    echo "[GEN] $name: $smiles -> $sdf (--gen3d)"
    obabel "$smiles" -O "$sdf" --gen3d
  else
    echo "[WARN] Não encontrei $name.{sdf,smi,smiles} em $LIG_DIR – pulando"
    continue
  fi

  if [[ ! -s "$sdf" ]]; then
    echo "[ERR] $sdf ficou vazio para $name – verifique o arquivo de origem" >&2
  fi

done < "$LIG_LIST"

echo "[INFO] Recalculando propriedades com ligand_props_obabel.py"
python3 tools/ligand_props_obabel.py \
  --indir "$LIG_DIR" \
  --output "$PROPS_OUT"

echo "[OK] Propriedades atualizadas em $PROPS_OUT"
