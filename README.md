**Vassoura de Bruxa — Docking Pipeline**

- Pipeline de docking em lote para avaliar múltiplos ligantes contra múltiplos alvos de Ceratobasidium theobromae.
- Usa AutoDock Vina, Open Babel e MGLTools para preparar entradas, executar o docking e resumir resultados.

**Objetivo**
- Priorizar compostos por afinidade teórica e orientar análises de seletividade entre alvos fúngicos (ex.: CHS — chitin synthase; FKS — 1,3-β-glucan synthase).
- Padronizar a preparação de estruturas (ligantes e alvos) e a definição de caixas de docking por alvo.

**Estrutura**
- `targets/` PDBs dos alvos e arquivos `.box` por alvo (caixa de docking).
- `ligands/` Arquivos de ligantes (`.sdf`, `.mol`, `.mol2`, `.pdb`).
- `docking_results/` Saídas do Vina organizadas por alvo/ligante e um CSV de resumo.
- `run_docking.sh` Script principal de execução.
- `install_in_silico.sh` (opcional) Script de instalação de dependências.

**Pré‑requisitos**
- `autodock-vina` (Vina ≥ 1.1.2/1.2.x)
- `openbabel` (obabel ≥ 3)
- `MGLTools` 1.5.7 (pythonsh + Utilities24: `prepare_ligand4.py` e `prepare_receptor4.py`)
- `GNU parallel` (opcional, paraleliza jobs)
- `PyMOL` (opcional, visualização)
- Dica: use `install_in_silico.sh` caso incluído neste repositório. Caso contrário, instale via gerenciador de pacotes da sua distribuição.

**Preparação dos Dados**
- Alvos (`targets/`):
  - Adicione os arquivos `ALVO.pdb` (resolvidos/previstos). O script gera `ALVO.pdbqt` com AutoDockTools (parâmetros padrão do `prepare_receptor4.py`).
  - Crie a caixa de docking por alvo: arquivo `targets/ALVO.box` contendo centro e tamanho em Å:
    - Exemplo (`targets/CHS.box`):
      - `center_x=10.0`
      - `center_y=15.0`
      - `center_z=20.0`
      - `size_x=24.0`
      - `size_y=24.0`
      - `size_z=24.0`
  - Como definir a caixa: no AutoDockTools (ADT), aponte para o sítio de interesse (ex.: canal do motivo QRRRW para CHS) e anote o centro e as dimensões mínimas que cobrem o pocket (20–30 Å costuma ser um bom ponto de partida; caixas muito grandes aumentam o custo e diluem a precisão).
- Ligantes (`ligands/`):
  - Coloque arquivos em formatos suportados (`.sdf`, `.mol`, `.mol2`, `.pdb`). O script converte para `.pdbqt` via Open Babel (gera 3D) + `prepare_ligand4.py` (cargas/torções padrão).
  - Boas práticas: revisar protonação/tautômeros no pH alvo, estereoisomeria e limpeza de sais/contra-íons antes do docking.

**Execução**
- Estrutura mínima no diretório atual:
  - `targets/` com `ALVO.pdb` e `ALVO.box`
  - `ligands/` com ligantes
- Comandos:
  - `chmod +x run_docking.sh`
  - `./run_docking.sh [opções]`
- Opções principais:
  - `-e, --exhaustiveness N` ajusta `--exhaustiveness` do Vina (padrão: 16)
  - `-n, --num-modes N` ajusta `--num_modes` do Vina (padrão: 9)
  - `-t, --threads N` número de jobs paralelos (GNU parallel)
  - `--cpu N` define `--cpu` do Vina para cada job
  - `-h, --help` ajuda
- Variáveis de ambiente (alternativas às flags):
  - `WORKDIR`, `EXHAUSTIVENESS`, `NUM_MODES`, `THREADS`, `VINA_CPU`
- Exemplos:
  - Sequencial: `./run_docking.sh -e 24 -n 12 --cpu 8`
  - Paralelo (4 jobs × 2 CPUs por job): `./run_docking.sh -e 24 -n 12 -t 4 --cpu 2`
- Observações:
  - O script é incremental: se `.pdbqt` já existe, reaproveita, acelerando re‑execuções.
  - Requer um arquivo `.box` válido por alvo; sem ele, o alvo é rejeitado.

**Saídas**
- Árvores de resultados:
  - `docking_results/<ALVO>/<LIGANTE>/<LIGANTE>_on_<ALVO>.pdbqt` pose(s) do Vina
  - `docking_results/<ALVO>/<LIGANTE>/<LIGANTE>_on_<ALVO>.log` log do Vina
  - `docking_results/summary_affinities.csv` resumo global
- Colunas do CSV:
  - `target` alvo (base do PDBQT)
  - `ligand` ligante (base do PDBQT)
  - `best_affinity_kcal_per_mol` afinidade mais favorável do log (kcal/mol)
  - `mode` modo correspondente (índice do Vina)
  - `exhaustiveness` valor usado
  - `num_modes` valor usado
  - `center_x,center_y,center_z` centro da caixa (Å)
  - `size_x,size_y,size_z` dimensões da caixa (Å)

**Validação e Visualização**
- Inspeção visual no PyMOL:
  - Carregue o receptor `ALVO.pdb` ou `ALVO.pdbqt` e a pose `LIGANTE_on_ALVO.pdbqt`.
  - Alternativa: converter a pose para PDB com Open Babel: `obabel pose.pdbqt -O pose.pdb`.
- Boas práticas de QC:
  - Verificar colisões/penetrações, geometria irreal e interações chave no pocket.
  - Conferir se o centro/caixa cobrem o sítio catalítico/funcional desejado.
  - Avaliar consistência de poses (clustering) e plausibilidade química.

**Resolução de Problemas**
- MGLTools não encontrado:
  - O script tenta localizar `pythonsh` e `Utilities24` em caminhos comuns. Reinstale o MGLTools 1.5.7 ou ajuste sua instalação para um dos caminhos detectados.
- Falha no `obabel --gen3d`:
  - Verifique integridade do arquivo do ligante; se preciso, limpe sais e gere 3D previamente (`obabel in.sdf -O out.pdb --gen3d --addh`).
- Vina muito lento:
  - Reduza a caixa (`size_*`), diminua `--exhaustiveness` ou aumente jobs/CPUs se houver recursos disponíveis.
- CSV vazio ou parcial:
  - Confirme existência dos `.box` por alvo e dos `.pdbqt` gerados; cheque logs individuais em `docking_results/<ALVO>/<LIGANTE>/*.log`.

**Boas Práticas de Reprodutibilidade**
- Registre exatamente `exhaustiveness`, `num_modes`, `--cpu`, versão do Vina e os parâmetros de caixa.
- Mantenha snapshots dos PDBs de entrada (targets) e dos arquivos de ligantes originais.
- Para estudos comparativos, não altere a caixa entre rodadas; altere apenas os ligantes.

**Próximos Passos (Opcional)**
- Pós‑processamento em Python para:
  - Ordenar o `summary_affinities.csv` por ΔG (afinidade mais baixa).
  - Calcular ΔΔG seletividade contra um alvo de referência.
  - Preparar planilha para priorização (ex.: MCDA_template.xlsx).

**Pós‑processamento (script incluso)**
- Arquivo: `postprocess_docking.py`
- Funções:
  - Ordena o CSV de resumo por afinidade (mais negativa primeiro).
  - Calcula ΔΔG de seletividade por par (alvo × ligante) usando um alvo de referência.
  - Gera um resumo por ligante com o melhor alvo e ΔΔG vs referência.
- Uso típico:
  - `./postprocess_docking.py` (gera `docking_results/summary_sorted.csv`)
  - `./postprocess_docking.py --ref-target CHS` (adiciona `summary_ddg.csv` e `ligand_selectivity_summary.csv`)
- Opções:
  - `--input` CSV de entrada (padrão: `docking_results/summary_affinities.csv`)
  - `--out-sorted` CSV ordenado (padrão: `docking_results/summary_sorted.csv`)
  - `--ref-target` nome do alvo de referência (não‑alvo)
  - `--out-ddg` CSV de ΔΔG (padrão: `docking_results/summary_ddg.csv`)
  - `--out-ligand-summary` resumo por ligante (padrão: `docking_results/ligand_selectivity_summary.csv`)
  - Observação: ΔΔG = ΔG(target, ligand) − ΔG(ref_target, ligand); valores negativos indicam maior seletividade para o alvo em relação ao de referência.

**Como Citar (Sugestão)**
- AutoDock Vina: Trott, O.; Olson, A. J. J. Comput. Chem. 2010.
- Open Babel: O’Boyle, N. M. et al. J. Cheminform. 2011.
- MGLTools/ADT: Sanner, M. F. J. Mol. Graph. Model. 1999; Morris, G. M. et al. J. Comput. Chem. 2009.
