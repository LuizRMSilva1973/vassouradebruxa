
import os
from colabfold.batch import run

inp_dir = r"/home/luiz/Área de trabalho/EMPRESAS/UNISAGRADO/PESQUISAS/VASSOURA DE BRUXA/in"
out_dir = r"/home/luiz/Área de trabalho/EMPRESAS/UNISAGRADO/PESQUISAS/VASSOURA DE BRUXA/out_FKS_demo"

print("Iniciando predição ColabFold ...")
print("Entrada:", inp_dir)
print("Saída:", out_dir)

run(
    inp_dir,
    out_dir,
    use_templates=False,
    use_gpu=False,
    msa_mode="single_sequence",
    model_type="auto",
    pair_mode="unpaired",
    num_models=1,
    is_complex=False,
    num_recycle=3,
    stop_at_score=100,
    random_seed=42,
)
print("Concluído. Arquivos salvos em:", out_dir)
