# CHS Model (ColabFold Quick Guide)

This guide lets you generate `targets/CHS.pdb` using ColabFold in Google Colab, then run docking here.

## 1) Open Google Colab
- Go to: https://colab.research.google.com/
- New Notebook → set Runtime to GPU (Runtime → Change runtime type → GPU)

## 2) Install ColabFold
```python
!pip -q install -U colabfold batchfold
!pip -q install -U openmm biopython
```

## 3) Paste the CHS sequence (from this repo)
- Open `targets/MP_B2XSE6.fasta` here and paste its contents into the cell below.

```python
sequence = """
>CHS_MONILIIO_B2XSE6
MANRPPLPSNASSSTVNDPYADPFADRPRQTHFTEPQHPYPSQASIPRPFESATSLPQEF
GARDQQFEEDDYVEKQPLTGGQAFAGGFYPPGPVDPEAYGDPYAGSRPASVVSSSTGGEK
SAWRRRQTIKRGVTRKVKLTKGNFITEYPVPTPILSATEAKYTATSTTEFSHMRYTAATC
DPDEFSEANGYSLRTKMYNRETELLIAVTSYNEDKTLYARTLHGVMLNIRDICKTKQSKY
WRRQAEEGNPGWQKITVALIVDGLEPMDKSVLDILATVGVYQDGVMKKQVDGKDTVAHIF
EYTTQLSVDATPQLVLPQANDPNNLVPVQIIFVLKAKNQKKINSHRWLFNAIGKILNPEV
CVLIDAGTKPGHKSIFYLWKAFYNDPHLGGCCGEIHAMIKGGKKLLNPLVAAQNFEYKMS
NILDKPLESSFGYVSVLPGAFSAYRYRAILGRPLEQYFHGDHSLADRLGPKRYYGNEHLH
QEHVLAEDRILCFELVAKKNDRWTLTYVKPSKAETDVPESAPELIGQRRRWLNGSFAASV
YALVNFFKLYQSGHGIFRMFFFHVQALYNIFSLVFSWFSLANIWLTFSIIIDLLPNLPGD
TAIIVFGTKAVTHWVNFGFKWIYLAFLALQFVLALGNRPKGERAAYTVTLWVYAILALYL
LVVYAILALYLLVCSFWLTIQAFQNIPKLVQANGGDAIKTLFQGPVGALIAAMFSTYGIY
IIASFLYRDPWHMFSSFFQYLLLAPSFTNVLNVYAFCNLHDVSWGTKGSDKAEALPSVSS
SKAKDADVAVVEDTAKVQEDVDAAFKETVTRAVTKIETKEEIEKPTMDDQNKTFRTRLVA
FWMLSNASLAVAISNLNGLPSSNPAQDEKDLADKQSTYFNIILYSTFGLAFVRFIGCLWY
FFKRNLFRCCRRN
"""
```

## 4) Predict structure with ColabFold (serverless)
```python
from colabfold.batch import run
import os, textwrap

jobname = "CHS_B2XSE6"
os.makedirs("out", exist_ok=True)
with open(f"out/{jobname}.fasta", "w") as f:
    f.write(sequence)

# Run minimal prediction (single model, relaxed structure)
run("out", f"out/{jobname}_results", msa_mode="mmseqs2_uniref_env")
```

This will create a directory like `out/CHS_B2XSE6_results/` containing PDB files.

## 5) Download the best PDB
- In Colab, open the files sidebar, navigate to `out/CHS_B2XSE6_results/` and download the top-ranked `*.pdb`.
- Save it into this repository at `targets/CHS.pdb`.

## 6) Back here: run docking vs CHS
```bash
make chs
```

This prepares `CHS.pdbqt`, builds a simple box (26 Å cube centered), docks 5 ligands (progress 20–100%), rebuilds summaries, computes ΔΔG with CHS as reference, and updates the ranking and plots.

## Notes
- CHS is likely multi-pass membrane protein; consider refining the binding box around the catalytic motifs once you inspect the model (e.g., with fpocket or manual selection), then rerun `make chs`.
- To increase search: `EXH=32 SEED=42 make chs`

