$Env:CONDA_EXE = "/home/luiz/Área de trabalho/EMPRESAS/UNISAGRADO/PESQUISAS/VASSOURA DE BRUXA/miniforge_clean/bin/conda"
$Env:_CE_M = $null
$Env:_CE_CONDA = $null
$Env:_CONDA_ROOT = "/home/luiz/Área de trabalho/EMPRESAS/UNISAGRADO/PESQUISAS/VASSOURA DE BRUXA/miniforge_clean"
$Env:_CONDA_EXE = "/home/luiz/Área de trabalho/EMPRESAS/UNISAGRADO/PESQUISAS/VASSOURA DE BRUXA/miniforge_clean/bin/conda"
$CondaModuleArgs = @{ChangePs1 = $True}
Import-Module "$Env:_CONDA_ROOT\shell\condabin\Conda.psm1" -ArgumentList $CondaModuleArgs

Remove-Variable CondaModuleArgs