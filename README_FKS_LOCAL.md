**FKS via ColabFold (uso local, CPU)**

- Instala Miniforge localmente (`./.miniforge`)
- Cria env Conda `fksfold` (Python 3.10)
- Instala `colabfold==1.5.4`, `jax/jaxlib==0.4.26` (CPU), `openmm==8.1.1`, `numpy==1.26.4`, `pandas==1.5.3`, `biopython==1.85`
- Saneia seu FASTA e roda `colabfold.batch.run`

**Requisitos**
- Linux ou macOS (x86_64/arm64). Em Windows, use WSL2.
- Internet para instalação e, por padrão, para MSA (serviço MMseqs2 remoto). Para ambiente offline, use `--msa-mode single_sequence` (menor acurácia) ou prepare bancos locais do MMseqs2 (100+ GB).

**Como usar**
- Salve seu FASTA em um arquivo, ex.: `data/FKS.fasta` (a primeira linha deve começar com `>`)
- Execute:

```
python3 fksfold_local.py --fasta data/FKS.fasta --out out_FKS
```

- Isso irá:
  - Baixar/instalar Miniforge em `./.miniforge` (se necessário)
  - Criar o env `fksfold` e instalar pacotes
  - Validar e salvar o FASTA em `./in/FKS.fasta`
  - Rodar ColabFold (CPU) e salvar em `./out_FKS`

**Opções úteis**
- `--msa-mode`: `mmseqs2_uniref_env` (padrão, usa web) ou `single_sequence` (offline, menor acurácia)
- `--use-gpu`: tenta usar GPU (se disponível e drivers/CUDA corretos). Por padrão, roda em CPU.
- `--model-type`: `auto` (padrão) ou outro suportado pelo ColabFold
- `--num-recycle`: inteiro (padrão 3)
- `--py`: versão do Python para o ambiente (padrão 3.10)
- `--skip-install`: pula a etapa de instalação (se você já instalou antes)

**Exemplos**
- Totalmente offline (sem internet durante a predição), mas com acurácia menor:
```
python3 fksfold_local.py --fasta data/FKS.fasta --msa-mode single_sequence
```

- Tentando usar GPU (se configurada):
```
python3 fksfold_local.py --fasta data/FKS.fasta --use-gpu
```

**Saídas**
- `out_FKS/` conterá os arquivos `ranked_0.pdb`, `ranking_debug.json`, etc.

**Notas importantes**
- O modo padrão de MSA usa o serviço MMseqs2 remoto; se sua máquina não tiver acesso à internet, use `--msa-mode single_sequence` ou configure bancos locais grandes (100+ GB) e ajuste o ColabFold para usá-los.
- Caso já possua Conda/Mamba no sistema e prefira não instalar Miniforge local, você pode criar manualmente um env e usar `--skip-install`.

**Execução via Docker (recomendado)**
- Requer Docker instalado. Usa a imagem oficial `colabfold/colabfold:1.5.5` e evita conflitos de dependência.

Exemplos:

```
# Offline (sem MSA web):
./run_with_docker.sh --fasta data/FKS_example.fasta --msa-mode single_sequence --out out_FKS

# Com MSA via web (melhor acurácia, requer internet):
./run_with_docker.sh --fasta data/FKS_example.fasta --msa-mode mmseqs2_uniref_env --out out_FKS

# Tentando usar GPU (se drivers/nvidia-container-toolkit instalados):
./run_with_docker.sh --fasta data/FKS_example.fasta --use-gpu
```

Notas Docker:
- O script monta apenas o diretório do FASTA como `/in` e o diretório de saída como `/out` no container; o restante do workspace não é montado.
- Em GPU, é necessário o `nvidia-container-toolkit` e `--gpus all` (o script adiciona automaticamente com `--use-gpu`).
