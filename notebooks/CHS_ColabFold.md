## Guia ColabFold — Modelagem de CHS (Moniliophthora)

Este guia usa ColabFold (Google Colab) para gerar um modelo 3D de CHS a partir das FASTAs do repo.

### Passos
1) Abra no navegador: https://colab.research.google.com/github/sokrypton/ColabFold/blob/main/beta/AlphaFold2.ipynb
2) Em "Runtime" selecione GPU. Execute as células iniciais para instalar ColabFold.
3) Cole a sequência FASTA da CHS (arquivo sugerido):
   - `targets/MP_B2XSE6.fasta` (preferência)
   - Alternativa: `targets/MP_C0LT25.fasta` (fragmento)
4) Use `num_recycles=3–6`, `model_type=AlphaFold2-ptm`, `msa_mode=MMseqs2 (UniRef+Environmental)`, `pair_mode=unpaired`.
5) Baixe o modelo PDB gerado (melhor ranking pLDDT). Renomeie para `CHS_model.pdb`.
6) Copie o arquivo para este repo em `targets/CHS.pdb`.

### Observações
- CHS é multipasse de membrana; regiões transmembrana podem ter pLDDT maior que loops; foque o sítio catalítico (motivos `QRRRW` e `DXH`) para docking.
- Após salvar `targets/CHS.pdb`, rode:
```
obabel -ipdb targets/CHS.pdb -opdbqt -O targets/CHS.pdbqt -xh --partialcharge gasteiger
python3 tools/compute_box_simple.py --pdb targets/CHS.pdb --fixed-size 26.0 --out targets/CHS.box
```
- Se tiver PyMOL/ChimeraX, ajuste a caixa para cobrir o sítio catalítico (ver docs/CHS_DOCKING_PLAN.md).

