#!/usr/bin/env python3
"""
FKS via ColabFold (uso local, CPU por padrão)

Este script:
  1) Instala Miniforge (Conda) localmente na pasta .miniforge (se necessário)
  2) Cria env "fksfold" (Python 3.10)
  3) Instala versões compatíveis (CPU) de jax/jaxlib, colabfold, openmm, numpy/pandas, biopython
  4) Saneia um FASTA fornecido (caminho) e grava em ./in/FKS.fasta
  5) Executa colabfold.batch.run e salva em ./out_FKS

Observações:
- Modo padrão de MSA usa o serviço remoto do MMseqs2 ("mmseqs2_uniref_env") e requer internet.
- Para ambientes totalmente offline, use --msa-mode single_sequence (menor acurácia) OU
  prepare bancos locais do MMseqs2 (vários centenas de GB) e ajuste o ColabFold para usá-los.

Compatível com Linux/macOS (x86_64 e arm64). Para Windows, recomenda-se WSL2.
"""

import os
import sys
import stat
import json
import re
import textwrap
import shutil
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
import argparse
import platform


# ================= Caminhos/constantes =================
ROOT = Path(__file__).resolve().parent
# Instalação do Miniforge fora de caminhos com espaços
MAMBA_ROOT = Path.home() / ".fksfold" / "miniforge"
CONDA_BIN = MAMBA_ROOT / "bin" / "conda"
ENV_NAME = "fksfold"
IN_DIR = ROOT / "in"
OUT_DIR = ROOT / "out_FKS"
FASTA_PATH = IN_DIR / "FKS.fasta"
INSTALLER = Path.home() / ".fksfold" / "Miniforge3.sh"


def sh(cmd: str, check: bool = True, env=None):
    print(">>>", cmd)
    return subprocess.run(cmd, shell=True, check=check, env=env)


# ================= Util: detectar instalador correto =================
def _miniforge_installer_url() -> str:
    sysname = platform.system()
    machine = platform.machine().lower()

    if sysname == "Linux":
        if machine in ("x86_64", "amd64"):
            return "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
        elif machine in ("aarch64", "arm64"):
            return "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh"
    elif sysname == "Darwin":
        if machine in ("x86_64", "amd64"):
            return "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh"
        elif machine in ("arm64",):
            return "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh"

    raise RuntimeError(f"Sistema/arquitetura não suportados: {sysname} {machine}")


# ================= 1) Instalar Miniforge (Conda) =================
def download_miniforge_latest():
    url = _miniforge_installer_url()
    print("Baixando instalador:", url)
    INSTALLER.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r, open(INSTALLER, "wb") as f:
        f.write(r.read())
    os.chmod(INSTALLER, os.stat(INSTALLER).st_mode | stat.S_IEXEC)


def ensure_mambaforge():
    if not CONDA_BIN.exists():
        try:
            download_miniforge_latest()
        except Exception as e:
            raise RuntimeError(f"Falha ao baixar Miniforge: {e}")
        sh(f"bash \"{INSTALLER}\" -b -p \"{MAMBA_ROOT}\"")
    else:
        print("Miniforge já instalado.")
    os.environ["PATH"] = f"{MAMBA_ROOT}/bin:" + os.environ["PATH"]
    print("Conda no PATH:", shutil.which("conda"))


# ================= 2) Criar ambiente e instalar pacotes =================
def ensure_env(py="3.10"):
    env_dir = MAMBA_ROOT / "envs" / ENV_NAME
    if not env_dir.exists():
        sh(f"\"{CONDA_BIN}\" create -y -n {ENV_NAME} python={py}")
    else:
        print(f"Ambiente {ENV_NAME} já existe.")


def install_pkgs():
    base = f"\"{CONDA_BIN}\" run -n {ENV_NAME} python -m pip"
    # Versões estáveis e compatíveis (CPU)
    sh(f"{base} install --no-input --upgrade pip")
    sh(f"{base} install --no-input numpy==1.26.4 pandas==1.5.3 openmm==8.1.1 biopython==1.82")
    # ColabFold + Alphafold (versão mais recente disponível)
    sh(f"{base} install --no-input 'colabfold[alphafold]==1.5.5'")


# ================= 3) Saneamento e gravação do FASTA =================
def sanitize_and_write_fasta(fasta_in: Path):
    IN_DIR.mkdir(parents=True, exist_ok=True)
    ft_raw = fasta_in.read_text().strip()
    if not ft_raw.startswith(">"):
        raise ValueError("O FASTA deve começar com uma linha de cabeçalho iniciada por '>'.")

    header, *seq_lines = ft_raw.splitlines()
    seq = "".join(line.strip() for line in seq_lines)

    seq = seq.upper()
    seq = re.sub(r"[ \t\r0-9]", "", seq)
    seq = seq.replace("-", "")

    # 20 AA + extensões X, B, Z, U, O, J
    allowed = set("ACDEFGHIKLMNPQRSTVWYXBZUOJ")
    bad = sorted(set(seq) - allowed)
    if bad:
        raise ValueError(f"Caracteres inválidos na sequência: {''.join(bad)}")

    seq_wrapped = "\n".join(textwrap.wrap(seq, 60))
    fasta_final = f"{header}\n{seq_wrapped}\n"

    with open(FASTA_PATH, "w") as f:
        f.write(fasta_final)
    print("FASTA salvo em:", FASTA_PATH)
    print("Tamanho (aa):", len(seq))


# ================= 4) Rodar ColabFold.batch.run =================
def run_prediction(out_dir_path: Path, msa_mode: str, use_gpu: bool, model_type: str, num_recycle: int):
    out_dir_path.mkdir(parents=True, exist_ok=True)
    print("Iniciando predição ColabFold (CLI) ...")
    print("Entrada:", IN_DIR)
    print("Saída:", out_dir_path)
    # Construir comando do CLI
    cmd = (
        f'"{CONDA_BIN}" run -n {ENV_NAME} colabfold_batch '
        f'--msa-mode {msa_mode} --pair-mode unpaired '
        f'--model-type {model_type} --num-recycle {num_recycle} --num-models 1 '
        f'"{IN_DIR}" "{out_dir_path}"'
    )
    sh(cmd)


def main():
    p = argparse.ArgumentParser(description="FKS via ColabFold (local)")
    p.add_argument("--fasta", type=str, required=True, help="Caminho para o arquivo FASTA de entrada")
    p.add_argument("--out", type=str, default=str(OUT_DIR), help="Diretório de saída (default: ./out_FKS)")
    p.add_argument("--msa-mode", type=str, default="mmseqs2_uniref_env",
                   choices=["mmseqs2_uniref_env", "single_sequence"],
                   help="Modo de MSA. Para offline use 'single_sequence'.")
    p.add_argument("--model-type", type=str, default="auto", help="Tipo de modelo (auto, alphafold2_ptm, etc.)")
    p.add_argument("--num-recycle", type=int, default=3, help="Número de recycles (default: 3)")
    p.add_argument("--use-gpu", action="store_true", help="Tentar usar GPU (se disponível)")
    p.add_argument("--py", type=str, default="3.10", help="Versão do Python para o env (default: 3.10)")
    p.add_argument("--skip-install", action="store_true", help="Pular instalação do Miniforge/pacotes")

    args = p.parse_args()

    # Ajustar diretório de saída se fornecido
    out_dir = Path(args.out).resolve()

    fasta_path = Path(args.fasta).resolve()
    if not fasta_path.exists():
        print(f"ERRO: FASTA não encontrado: {fasta_path}", file=sys.stderr)
        sys.exit(2)

    if not args.skip_install:
        ensure_mambaforge()
        ensure_env(py=args.py)
        install_pkgs()
    else:
        # Ainda assim garantir que o conda está no PATH para executar
        if shutil.which("conda") is None and not CONDA_BIN.exists():
            print("ERRO: --skip-install usado mas conda não encontrado.", file=sys.stderr)
            sys.exit(2)
        if shutil.which("conda") is None:
            os.environ["PATH"] = f"{MAMBA_ROOT}/bin:" + os.environ.get("PATH", "")

    sanitize_and_write_fasta(fasta_path)
    run_prediction(out_dir_path=out_dir, msa_mode=args.msa_mode, use_gpu=args.use_gpu, model_type=args.model_type, num_recycle=args.num_recycle)


if __name__ == "__main__":
    main()
