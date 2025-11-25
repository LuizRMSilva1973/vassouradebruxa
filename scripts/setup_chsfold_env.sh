#!/usr/bin/env bash
set -euo pipefail
# Uso:
#   scripts/setup_chsfold_env.sh --conda-env chsfold [--cpu|--cuda cu121]
# Ex.: scripts/setup_chsfold_env.sh --conda-env chsfold --cpu
#      scripts/setup_chsfold_env.sh --conda-env chsfold --cuda cu121

ENVNAME="chsfold"
MODE="cpu"
CUDA_TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --conda-env) ENVNAME="$2"; shift 2 ;;
    --cpu) MODE="cpu"; shift ;;
    --cuda) MODE="cuda"; CUDA_TAG="$2"; shift 2 ;;
    *) echo "arg desconhecido: $1"; exit 2 ;;
  esac
done

echo "[INFO] criando env ${ENVNAME} (python 3.10)"
conda create -y -n "${ENVNAME}" python=3.10
eval "$(conda shell.bash hook)"
conda activate "${ENVNAME}"

if [[ "$MODE" == "cpu" ]]; then
  echo "[INFO] Torch CPU"
  pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
else
  if [[ -z "$CUDA_TAG" ]]; then
    echo "[ERRO] use --cuda <cu121|cu118|...>"
    exit 2
  fi
  echo "[INFO] Torch CUDA (${CUDA_TAG})"
  pip install --index-url "https://download.pytorch.org/whl/${CUDA_TAG}" torch torchvision torchaudio
fi

echo "[INFO] ESM + deps"
pip install "git+https://github.com/facebookresearch/esm.git" einops biopython

echo "[INFO] OpenFold"
pip install "git+https://github.com/aqlaboratory/openfold.git@main"

python - <<'PY'
import torch, importlib
import esm
print("torch ok, cuda:", torch.cuda.is_available())
print("esm ok:", hasattr(esm, "pretrained"))
print("openfold import:", importlib.util.find_spec("openfold") is not None)
PY

echo "[OK] ambiente pronto: conda activate ${ENVNAME}"
