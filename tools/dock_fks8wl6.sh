#!/usr/bin/env bash
# Docking sequencial com Vina para um alvo (ex.: FKS_8WL6)

set -euo pipefail

if ! command -v vina >/dev/null 2>&1; then
  echo "[ERR] vina não encontrado no PATH (instale AutoDock Vina)" >&2
  exit 2
fi
if ! command -v obabel >/dev/null 2>&1; then
  echo "[ERR] obabel não encontrado no PATH (instale OpenBabel)" >&2
  exit 2
fi

LIG_LIST=${1:-config/ligantes_fks8wl6.txt}

TARGET=${TARGET:-FKS_8WL6}
EXH=${EXH:-16}
NM=${NM:-9}

OUTDIR="docking_results/${TARGET}"
mkdir -p "$OUTDIR"

RECEPTOR="targets/${TARGET}.pdbqt"

# Saída principal (usado pelo Makefile em score/pareto/shortlist)
OUTFILE=${OUTFILE:-docking_results/summary_affinities.csv}

# Parâmetros da caixa – estes valores são os que você ajustou para FKS_8WL6
center_x=${center_x:-131.460}
center_y=${center_y:-132.289}
center_z=${center_z:-134.163}
size_x=${size_x:-40.0}
size_y=${size_y:-40.0}
size_z=${size_z:-40.0}

# Tempo máximo por ligante (segundos)
T_SMALL=${T_SMALL:-90}
T_BIG=${T_BIG:-180}

echo "[INFO] Target: $TARGET"
echo "[INFO] Receptor PDBQT: $RECEPTOR"
echo "[INFO] Lista de ligantes: $LIG_LIST"
echo "[INFO] CSV de saída: $OUTFILE"

if [[ ! -s "$RECEPTOR" ]]; then
  echo "[ERR] Receptor não encontrado ou vazio: $RECEPTOR" >&2
  exit 1
fi

if [[ ! -f "$LIG_LIST" ]]; then
  echo "[ERR] Arquivo de lista de ligantes não encontrado: $LIG_LIST" >&2
  exit 1
fi

# Cabeçalho do CSV (sobrescreve arquivo anterior)
echo "target,ligand,best_affinity_kcal_per_mol,mode,exhaustiveness,num_modes,center_x,center_y,center_z,size_x,size_y,size_z" > "$OUTFILE"

while IFS= read -r raw; do
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

  lig_sdf="ligands/${name}.sdf"
  lig_pdbqt="ligands/${name}.pdbqt"

  if [[ ! -s "$lig_sdf" ]]; then
    echo "[WARN] $lig_sdf não existe ou está vazio – pulando $name"
    continue
  fi

  echo "[PREP] $name -> PDBQT"
  # -xp: tenta atribuir cargas/parâmetros extras
  if ! obabel "$lig_sdf" -O "$lig_pdbqt" -xp 2>/dev/null; then
    echo "[WARN] obabel -xp falhou para $name, tentando sem -xp"
    obabel "$lig_sdf" -O "$lig_pdbqt" 2>/dev/null || {
      echo "[FAIL] Não consegui gerar PDBQT para $name – pulando"
      continue
    }
  fi

  lig_out_dir="${OUTDIR}/${name}"
  mkdir -p "$lig_out_dir"
  lig_out="${lig_out_dir}/${name}_on_${TARGET}.pdbqt"
  log="${lig_out_dir}/${name}_on_${TARGET}.log"

  # timeout e exaustividade de acordo com o flag BIG
  if [[ "${flag:-}" == "BIG" ]]; then
    lig_exh=$EXH
    tlim=$T_BIG
  else
    lig_exh=$EXH
    tlim=$T_SMALL
  fi

  echo "[RUN] $name (exhaustiveness=$lig_exh, timeout=${tlim}s)"

  if timeout "${tlim}s" vina \
      --receptor "$RECEPTOR" \
      --ligand "$lig_pdbqt" \
      --center_x "$center_x" \
      --center_y "$center_y" \
      --center_z "$center_z" \
      --size_x "$size_x" \
      --size_y "$size_y" \
      --size_z "$size_z" \
      --exhaustiveness "$lig_exh" \
      --num_modes "$NM" \
      --out "$lig_out" >"$log" 2>&1; then

    # Extrair melhor afinidade do log
    best=$(awk '
      /^-----+/ {flag=1; next}
      flag && NF==3 {print $2; exit}
    ' "$log")

    mode=$(awk '
      /^-----+/ {flag=1; next}
      flag && NF==3 {print $1; exit}
    ' "$log")

    if [[ -n "${best:-}" ]]; then
      echo "[OK] $name -> melhor afinidade = $best kcal/mol (mode $mode)"
      echo "${TARGET},${name},${best},${mode},${lig_exh},${NM},${center_x},${center_y},${center_z},${size_x},${size_y},${size_z}" >> "$OUTFILE"
    else
      echo "[WARN] Não consegui extrair afinidade de $log para $name"
    fi
  else
    echo "[FAIL] $name (timeout ou erro do Vina; ver log: $log)"
  fi

done < "$LIG_LIST"

echo "[DONE] Docking concluído. Resultados em: $OUTFILE"
