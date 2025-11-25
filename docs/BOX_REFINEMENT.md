# Refinamento da Caixa de Docking (CHS e outros alvos)

Este guia reúne opções práticas para definir/ajustar a `*.box` (centro/tamanho) do Vina/Smina visando maior acurácia no sítio ativo.

## Opção A — fpocket (cavidades)
1. Rode o fpocket no PDB do alvo (fora do repo, requer instalação):
   ```bash
   fpocket -f targets/CHS.pdb -o chs_fpocket_out
   ```
2. Localize a cavidade de interesse, por exemplo `chs_fpocket_out/*/pockets/pocket1_atm.pdb`.
3. Gere a caixa centrada na cavidade com margem (e caixa cúbica):
   ```bash
   python3 tools/compute_box_simple.py \
     --pdb chs_fpocket_out/CHS_out/pockets/pocket1_atm.pdb \
     --margin 4.0 --cubic --out targets/CHS.box
   ```

## Opção B — Ligante (autobox via pose)
Se você já tem uma pose (PDBQT) para um ligante guia (ex.: resultado de docking rápido):
```bash
python3 tools/compute_box_simple.py \
  --pdb docking_results_smina/CHS/<ligante>/<ligante>_on_CHS.pdbqt \
  --margin 6.0 --cubic --out targets/CHS.box
```
Isto cria uma caixa cúbica ao redor das coordenadas do ligante com 6 Å de folga.

## Opção C — Motivos catalíticos / resíduos
Use seleção por resíduos/motivos (ver `tools/compute_box.py`). Exemplos:
```bash
# caixa em torno de resíduos A:123,A:124,A:125 (mais 4 Å de margem)
python3 tools/compute_box.py --pdb targets/CHS.pdb \
  --res A:123,A:124,A:125 --margin 4.0 --out targets/CHS.box

# caixa baseada em HET (se houver co-fator 3-letras, ex.: UDP)
python3 tools/compute_box.py --pdb targets/CHS.pdb --het UDP --margin 4.0 --out targets/CHS.box
```

## Dicas
- Após atualizar `targets/CHS.box`, rode `make chs` para refazer o docking de validação.
- Para explorar caixas maiores/menores, ajuste `--margin` (ligante/pocket) ou `--fixed-size` (cubo de aresta fixa).
- Para robustez, aumente a busca: `EXH=32 SEED=42 make chs`.

