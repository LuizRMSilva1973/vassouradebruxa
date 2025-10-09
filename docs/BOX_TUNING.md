## Ajuste de Caixa (Docking Box)

Objetivo: definir `center_*` e `size_*` nos arquivos `targets/<ALVO>.box` com base em um PDB e um critério de seleção (ligante referência ou resíduos do sítio).

### Opção A — Baseada em ligante (HETATM)
Se o PDB tiver um ligante de referência (não água):
```
python3 tools/compute_box.py --pdb targets/FKS.pdb --het LIG --margin 4.0 --cubic --out targets/FKS.box
```
- `LIG` é o código de 3 letras do ligante.
- `--margin` adiciona acolchoamento em Å.
- `--cubic` usa box cúbica.

### Opção B — Baseada em resíduos do sítio
Se você souber os resíduos do sítio catalítico/alostérico:
```
python3 tools/compute_box.py --pdb targets/CHS.pdb \
  --res A:423,A:424,A:517 \
  --margin 4.0 --out targets/CHS.box
```
- Formato: `cadeia:resseq` (insertion code opcional, ex.: `10A`).

### Verificação Rápida
- Visualize o PDB e confirme se o cubo (size_*) cobre o sítio com folga (4–6 Å).
- Evite caixas muito grandes (>28–32 Å) para não diluir a busca do Vina.

