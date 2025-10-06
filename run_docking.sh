#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# run_docking.sh - AutoDock Vina em lote (alvos x ligantes)
# Estrutura esperada no diretório ATUAL onde você rodar:
#   ./
#     ├─ targets/           # PDBs dos alvos + .box (centro/tamanho)
#     ├─ ligands/           # SDF/MOL/PDB dos ligantes
#     ├─ docking_results/   # saídas serão criadas aqui
#     └─ md_results/        # (não usado aqui)
# ------------------------------------------------------------

# Usa o diretório atual por padrão; permite override com WORKDIR
WORKDIR="${WORKDIR:-$PWD}"
TARGETS_DIR="${WORKDIR}/targets"
LIGANDS_DIR="${WORKDIR}/ligands"
OUTDIR="${WORKDIR}/docking_results"
SUMMARY="${OUTDIR}/summary_affinities.csv"

# Parâmetros ajustáveis via flags
EXHAUSTIVENESS=${EXHAUSTIVENESS:-16}
THREADS=${THREADS:-}
VINA_CPU=${VINA_CPU:-}
NUM_MODES=${NUM_MODES:-9}
TOPN_N=${TOPN_N:-10}
GENERATE_TOPN=${GENERATE_TOPN:-1}

usage() {
  cat <<EOF
Uso: $(basename "$0") [opções]

Opções:
  -e, --exhaustiveness N   Define exhaustiveness do Vina (padrão: ${EXHAUSTIVENESS})
  -t, --threads N          Número de jobs paralelos (GNU parallel). Se ausente, auto.
  --cpu N              Passa --cpu N para o Vina (por job).
  -n, --num-modes N        Define --num_modes do Vina (padrão: ${NUM_MODES})
  -N, --topn N             Gera Top-N por alvo após o docking (padrão: ${TOPN_N})
      --no-topn            Desativa a geração automática de Top-N
  -h, --help               Mostra esta ajuda e sai.

Ambiente:
  WORKDIR           Raiz do projeto (padrão: diretório atual)
  EXHAUSTIVENESS    Igual a --exhaustiveness
  THREADS           Igual a --threads
  VINA_CPU          Igual a --cpu
  NUM_MODES         Igual a --num-modes
  TOPN_N            Igual a --topn
  GENERATE_TOPN     1 para habilitar (padrão), 0 para desabilitar

Estrutura esperada:
  ${WORKDIR}/targets   (PDBs + .box)
  ${WORKDIR}/ligands   (SDF/MOL/MOL2/PDB)
  ${WORKDIR}/docking_results (saídas)
EOF
}

# Parse de argumentos
while [[ $# -gt 0 ]]; do
  case "$1" in
    -e|--exhaustiveness)
      [[ $# -ge 2 ]] || { echo "Faltou valor para $1"; exit 2; }
      EXHAUSTIVENESS="$2"; shift 2 ;;
    -t|--threads)
      [[ $# -ge 2 ]] || { echo "Faltou valor para $1"; exit 2; }
      THREADS="$2"; shift 2 ;;
    --cpu)
      [[ $# -ge 2 ]] || { echo "Faltou valor para $1"; exit 2; }
      VINA_CPU="$2"; shift 2 ;;
    -n|--num-modes)
      [[ $# -ge 2 ]] || { echo "Faltou valor para $1"; exit 2; }
      NUM_MODES="$2"; shift 2 ;;
    -N|--topn)
      [[ $# -ge 2 ]] || { echo "Faltou valor para $1"; exit 2; }
      TOPN_N="$2"; GENERATE_TOPN=1; shift 2 ;;
    --no-topn)
      GENERATE_TOPN=0; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Opção desconhecida: $1"; usage; exit 2 ;;
  esac
done

# 1) Localizar scripts do MGLTools (prepare_ligand4.py / prepare_receptor4.py)
find_mgltool() {
  local cand
  for cand in \
    "${HOME}/MGLTools-1.5.7/bin" \
    "/usr/local/MGLTools-1.5.7/bin" \
    "/usr/bin" \
    "/opt/mgltools/bin" \
    "${HOME}/mgltools_x86_64Linux2_1.5.7/bin"
  do
    if [[ -x "${cand}/pythonsh" ]] && [[ -f "${cand}/../MGLToolsPckgs/AutoDockTools/Utilities24/prepare_ligand4.py" ]]; then
      echo "${cand}"
      return 0
    fi
  done
  return 1
}

MGLBIN="$(find_mgltool || true)"
if [[ -z "${MGLBIN}" ]]; then
  echo "ERRO: Não encontrei o MGLTools (pythonsh + Utilities24). Verifique a instalação."
  echo "Dica: rode novamente o instalador e confirme o caminho do MGLTools."
  exit 1
fi

PREP_LIG="${MGLBIN}/pythonsh ${MGLBIN}/../MGLToolsPckgs/AutoDockTools/Utilities24/prepare_ligand4.py"
PREP_REC="${MGLBIN}/pythonsh ${MGLBIN}/../MGLToolsPckgs/AutoDockTools/Utilities24/prepare_receptor4.py"

# 2) checagens
command -v vina >/dev/null 2>&1 || { echo "ERRO: 'vina' não encontrado."; exit 1; }
command -v obabel >/dev/null 2>&1 || { echo "ERRO: 'openbabel (obabel)' não encontrado."; exit 1; }

mkdir -p "${OUTDIR}"

# 3) header do CSV resumo
echo "target,ligand,best_affinity_kcal_per_mol,mode,exhaustiveness,num_modes,center_x,center_y,center_z,size_x,size_y,size_z" > "${SUMMARY}"

# 4) função: preparar alvo (PDB -> PDBQT) usando MGLTools
prep_target() {
  local pdb="$1"
  local base="$(basename "${pdb}" .pdb)"
  local outpdbqt="${TARGETS_DIR}/${base}.pdbqt"
  if [[ -f "${outpdbqt}" ]]; then
    echo "[TARGET] ${base}.pdbqt já existe."
  else
    echo "[TARGET] Preparando ${base}.pdbqt ..."
    ${PREP_REC} -r "${pdb}" -o "${outpdbqt}" >/dev/null 2>&1
  fi
}

# 5) função: preparar ligante (qualquer formato comum -> PDBQT)
prep_ligand() {
  local file="$1"
  local stem="$(basename "${file}")"
  local name="${stem%.*}"
  local tmp_pdb="${LIGANDS_DIR}/${name}.pdb"
  local outpdbqt="${LIGANDS_DIR}/${name}.pdbqt"

  if [[ -f "${outpdbqt}" ]]; then
    echo "[LIG] ${name}.pdbqt já existe."
    return
  fi

  echo "[LIG] Gerando 3D e convertendo ${stem} -> ${name}.pdb ..."
  obabel "${file}" -O "${tmp_pdb}" --gen3d >/dev/null 2>&1

  echo "[LIG] Preparando ${name}.pdbqt ..."
  ${PREP_LIG} -l "${tmp_pdb}" -o "${outpdbqt}" >/dev/null 2>&1
}

# 6) função: ler caixa (grid) do arquivo targets/<ALVO>.box
# Formato esperado (linhas, qualquer ordem; números em ponto):
# center_x=10.0
# center_y=15.0
# center_z=20.0
# size_x=20.0
# size_y=20.0
# size_z=20.0
read_box() {
  local base="$1"
  local file="${TARGETS_DIR}/${base}.box"
  if [[ ! -f "${file}" ]]; then
    echo "ERRO: Caixa ausente para ${base}. Crie ${file} com center_* e size_*."
    return 1
  fi
  # shellcheck disable=SC1090
  center_x=$(grep -E '^center_x=' "${file}" | cut -d'=' -f2)
  center_y=$(grep -E '^center_y=' "${file}" | cut -d'=' -f2)
  center_z=$(grep -E '^center_z=' "${file}" | cut -d'=' -f2)
  size_x=$(grep -E '^size_x='   "${file}" | cut -d'=' -f2)
  size_y=$(grep -E '^size_y='   "${file}" | cut -d'=' -f2)
  size_z=$(grep -E '^size_z='   "${file}" | cut -d'=' -f2)
  if [[ -z "${center_x}" || -z "${center_y}" || -z "${center_z}" || -z "${size_x}" || -z "${size_y}" || -z "${size_z}" ]]; then
    echo "ERRO: Formato inválido em ${file}. Preencha todas as 6 chaves."
    return 1
  fi
  echo "${center_x}|${center_y}|${center_z}|${size_x}|${size_y}|${size_z}"
}

# 7) função: docking de 1 alvo x 1 ligante
dock_pair() {
  local target_pdbqt="$1"
  local ligand_pdbqt="$2"

  local tbase="$(basename "${target_pdbqt}" .pdbqt)"
  local lbase="$(basename "${ligand_pdbqt}" .pdbqt)"

  # caixa
  IFS='|' read -r cx cy cz sx sy sz < <( read_box "${tbase}" )

  local pair_out="${OUTDIR}/${tbase}/${lbase}"
  mkdir -p "${pair_out}"

  local outp="${pair_out}/${lbase}_on_${tbase}.pdbqt"
  local logf="${pair_out}/${lbase}_on_${tbase}.log"

  echo "[DOCK] ${lbase} x ${tbase} (cx,cy,cz= ${cx},${cy},${cz} | sx,sy,sz= ${sx},${sy},${sz})"

  # Monta args do Vina dinamicamente
  local vina_args=(
    --receptor "${target_pdbqt}"
    --ligand   "${ligand_pdbqt}"
    --center_x "${cx}" --center_y "${cy}" --center_z "${cz}"
    --size_x   "${sx}" --size_y   "${sy}" --size_z   "${sz}"
    --exhaustiveness "${EXHAUSTIVENESS}"
    --num_modes "${NUM_MODES}"
    --out "${outp}" --log "${logf}"
  )
  if [[ -n "${VINA_CPU}" ]]; then
    vina_args+=( --cpu "${VINA_CPU}" )
  fi
  vina "${vina_args[@]}" >/dev/null 2>&1

  # extrair melhor afinidade do log
  local best_aff mode
  best_aff="$(awk '/^-----+/{f=1;next} f && NF>0{print $2; exit}' "${logf}" 2>/dev/null || echo "NA")"
  mode="$(awk '/^-----+/{f=1;next} f && NF>0{print $1; exit}' "${logf}" 2>/dev/null || echo "NA")"

  echo "${tbase},${lbase},${best_aff},${mode},${EXHAUSTIVENESS},${NUM_MODES},${cx},${cy},${cz},${sx},${sy},${sz}" >> "${SUMMARY}"
}

# 8) preparar todos os alvos e ligantes
echo ">>> Preparando ALVOS (PDB -> PDBQT)..."
shopt -s nullglob
for t in "${TARGETS_DIR}"/*.pdb; do
  prep_target "${t}"
done

echo ">>> Preparando LIGANTES (-> PDBQT)..."
for L in "${LIGANDS_DIR}"/*.{sdf,mol,mol2,pdb}; do
  [[ -e "$L" ]] || continue
  prep_ligand "${L}"
done

# 9) montar listas finais
mapfile -t TARGETS_PDBQT < <(ls "${TARGETS_DIR}"/*.pdbqt 2>/dev/null || true)
mapfile -t LIGANDS_PDBQT < <(ls "${LIGANDS_DIR}"/*.pdbqt  2>/dev/null || true)

if [[ ${#TARGETS_PDBQT[@]} -eq 0 || ${#LIGANDS_PDBQT[@]} -eq 0 ]]; then
  echo "ERRO: faltam alvos (.pdbqt) ou ligantes (.pdbqt)."
  exit 1
fi

# 10) docking em lote (com parallel, se existir)
echo ">>> Iniciando docking em lote... (exhaustiveness=${EXHAUSTIVENESS}, num_modes=${NUM_MODES}${THREADS:+, threads=${THREADS}}${VINA_CPU:+, vina_cpu=${VINA_CPU}})"
if command -v parallel >/dev/null 2>&1; then
  export -f dock_pair read_box
  export OUTDIR SUMMARY EXHAUSTIVENESS VINA_CPU
  if [[ -n "${THREADS}" ]]; then
    parallel -j "${THREADS}" --will-cite dock_pair {1} {2} ::: "${TARGETS_PDBQT[@]}" ::: "${LIGANDS_PDBQT[@]}"
  else
    parallel --will-cite dock_pair {1} {2} ::: "${TARGETS_PDBQT[@]}" ::: "${LIGANDS_PDBQT[@]}"
  fi
else
  for t in "${TARGETS_PDBQT[@]}"; do
    for l in "${LIGANDS_PDBQT[@]}"; do
      dock_pair "${t}" "${l}"
    done
  done
fi

echo ">>> Concluído. Resumo em: ${SUMMARY}"

# 11) Pós-processamento opcional: Top-N por alvo
if [[ "${GENERATE_TOPN}" == "1" ]]; then
  echo ">>> Gerando Top-${TOPN_N} por alvo (se script disponível)..."
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  candidates=(
    "${script_dir}/topn_by_target.py"
    "${WORKDIR}/topn_by_target.py"
  )
  ran=0
  for s in "${candidates[@]}"; do
    if [[ -f "${s}" ]]; then
      if command -v python3 >/dev/null 2>&1; then
        python3 "${s}" --input "${SUMMARY}" --outdir "${OUTDIR}/topN_by_target" --top "${TOPN_N}" || echo "[WARN] Falha ao gerar Top-N com ${s}"
        ran=1
        break
      else
        echo "[WARN] python3 não encontrado; pulando Top-N."
        ran=1
        break
      fi
    fi
  done
  if [[ "${ran}" -eq 0 ]]; then
    echo "[INFO] Script topn_by_target.py não encontrado; pulando Top-N."
  fi
fi
