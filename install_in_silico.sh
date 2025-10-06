#!/bin/bash
# Script de instalação para ambiente in silico no Linux Mint
# Autor: MantovaniTech IA
# Data: 2025

echo ">>> Atualizando pacotes..."
sudo apt update && sudo apt upgrade -y

echo ">>> Instalando dependências básicas..."
sudo apt install -y build-essential git wget curl unzip cmake software-properties-common

echo ">>> Instalando Python e pacotes úteis..."
sudo apt install -y python3 python3-pip python3-venv
pip3 install --upgrade pip
pip3 install numpy pandas rdkit-pypi matplotlib biopython

echo ">>> Instalando AutoDock Vina..."
sudo apt install -y autodock-vina

echo ">>> Instalando OpenBabel..."
sudo apt install -y openbabel

echo ">>> Instalando GROMACS..."
sudo apt install -y gromacs

echo ">>> Instalando PyMOL (visualização opcional)..."
sudo apt install -y pymol

echo ">>> Baixando e instalando MGLTools (AutoDockTools)..."
wget -c http://mgltools.scripps.edu/downloads/tars/releases/REL1.5.7/mgltools_x86_64Linux2_1.5.7.tar.gz
tar -xvzf mgltools_x86_64Linux2_1.5.7.tar.gz
cd mgltools_x86_64Linux2_1.5.7
./install.sh
cd ..

echo ">>> Criando estrutura de diretórios de trabalho..."
mkdir -p ~/Ctheobromae_in_silico/{targets,ligands,docking_results,md_results}

echo ">>> Instalação concluída!"
echo "Pastas criadas em: ~/Ctheobromae_in_silico"
echo "Ferramentas instaladas: AutoDock Vina, OpenBabel, GROMACS, MGLTools, PyMOL"
echo "Pronto para preparar alvos e ligantes."
