#!/usr/bin/env bash
set -euo pipefail

# Wrapper para rodar ColabFold via Docker oficial
# Requisitos: Docker instalado e acesso à internet (se usar MSA via web)

# Imagem oficial hospedada no GHCR
# Preferir GHCR (confiável/publicado pelo projeto) na versão 1.5.4
IMAGE="ghcr.io/sokrypton/colabfold:1.5.4"
FASTA=""
OUT_DIR="out_FKS"
MSA_MODE="single_sequence"      # offline por padrão
MODEL_TYPE="auto"
NUM_RECYCLE="3"
NUM_MODELS="1"
USE_GPU="0"

usage() {
  cat <<EOF
Uso: $0 --fasta caminho.fasta [opções]

Opções:
  --fasta PATH              Caminho para o arquivo FASTA (obrigatório)
  --out DIR                 Diretório de saída (default: out_FKS)
  --msa-mode MODE           mmseqs2_uniref_env | mmseqs2_uniref | single_sequence (default: single_sequence)
  --model-type TYPE         auto | alphafold2 | alphafold2_ptm | ... (default: auto)
  --num-recycle N           Número de recycles (default: 3)
  --num-models N            Número de modelos (1..5) (default: 1)
  --use-gpu                 Usa GPU (requer drivers + nvidia-container-toolkit)
  -h, --help                Mostra esta ajuda

Exemplos:
  $0 --fasta data/FKS_example.fasta --msa-mode single_sequence
  $0 --fasta data/FKS_example.fasta --msa-mode mmseqs2_uniref_env --out out_FKS
  $0 --fasta data/FKS_example.fasta --use-gpu --num-recycle 3 --num-models 1
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fasta) FASTA="$2"; shift 2;;
    --out) OUT_DIR="$2"; shift 2;;
    --msa-mode) MSA_MODE="$2"; shift 2;;
    --model-type) MODEL_TYPE="$2"; shift 2;;
    --num-recycle) NUM_RECYCLE="$2"; shift 2;;
    --num-models) NUM_MODELS="$2"; shift 2;;
    --use-gpu) USE_GPU="1"; shift 1;;
    -h|--help) usage; exit 0;;
    *) echo "Opção desconhecida: $1"; usage; exit 2;;
  esac
done

if [[ -z "$FASTA" ]]; then
  echo "ERRO: --fasta é obrigatório" >&2
  usage
  exit 2
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERRO: Docker não encontrado. Instale o Docker antes." >&2
  exit 2
fi

# Normalizar caminhos absolutos preservando espaços
abs_path() {
  python3 - "$1" <<'PY'
import os, sys
p = sys.argv[1]
print(os.path.abspath(p))
PY
}

FASTA_ABS="$(abs_path "$FASTA")"
OUT_ABS="$(abs_path "$OUT_DIR")"
FASTA_DIR="$(dirname "$FASTA_ABS")"
FASTA_BASENAME="$(basename "$FASTA_ABS")"

mkdir -p "$OUT_ABS"

DOCKER_ARGS=(run --rm -it -u "$(id -u):$(id -g)" \
  -v "$FASTA_DIR":/in \
  -v "$OUT_ABS":/out)

# Montar cache de pesos para evitar re-downloads
HOST_CACHE_DIR="$HOME/.cache/colabfold"
mkdir -p "$HOST_CACHE_DIR"
DOCKER_ARGS+=( -v "$HOST_CACHE_DIR":/root/.cache/colabfold )

if [[ "$USE_GPU" == "1" ]]; then
  # Requer nvidia-container-toolkit instalado/configurado
  DOCKER_ARGS+=(--gpus all)
fi

CMD=("$IMAGE" colabfold_batch \
  --msa-mode "$MSA_MODE" \
  --pair-mode unpaired \
  --model-type "$MODEL_TYPE" \
  --num-recycle "$NUM_RECYCLE" \
  --num-models "$NUM_MODELS" \
  "/in/$FASTA_BASENAME" \
  /out)

echo "[Docker] Executando ColabFold..."
echo "Imagem: $IMAGE"
echo "Entrada: $FASTA_ABS"
echo "Saída:   $OUT_ABS"

set -x
# Tenta imagem primária; se falhar, tenta alternativa no Docker Hub
if ! docker "${DOCKER_ARGS[@]}" "${CMD[@]}"; then
  set +x
  echo "Falha com $IMAGE; tentando Docker Hub..."
  IMAGE="colabfold/colabfold:1.5.4"
  set -x
  docker "${DOCKER_ARGS[@]}" "$IMAGE" colabfold_batch \
    --msa-mode "$MSA_MODE" --pair-mode unpaired --model-type "$MODEL_TYPE" \
    --num-recycle "$NUM_RECYCLE" --num-models "$NUM_MODELS" \
    "/in/$FASTA_BASENAME" /out
fi
