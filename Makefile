PY ?= python3
PIP ?= pip
DEVICE ?= cpu
EXH ?= 16
NM ?= 9
SEED ?= 42
REF ?= FKS_8WL6

# Lista de ligantes e alvo padrão para FKS
LIG_LIST ?= config/ligantes_fks8wl6.txt
FKS_TARGET ?= FKS_8WL6

.PHONY: test score pareto shortlist chs chs_env chs_build full_chs \
        prep_ligands dock_fks8wl6 fks_pipeline chs_box_fpocket \
        chs_box_ligand consensus

test:
	pytest -q

score:
	$(PY) tools/score_multiobjective.py \
		--summary docking_results/summary_affinities.csv \
		--props data/ligantes_props_obabel.csv \
		--config config/scoring.yaml \
		--ref-target FKS_8WL6

pareto:
	$(PY) tools/pareto.py \
		--input docking_results/scored.csv \
		--out docking_results/pareto_front.csv

shortlist:
	$(PY) tools/shortlist.py \
		--scored docking_results/scored.csv \
		--out docking_results/shortlist.csv

chs:
	bash scripts/run_chs_set.sh

# --------------------------------------------------------------------
# NOVO: preparação de ligantes e docking para FKS_8WL6
# --------------------------------------------------------------------

# Gera SDF/3D para todos os ligantes e recalcula ligantes_props_obabel.csv
prep_ligands:
	./tools/prep_ligands.sh $(LIG_LIST)

# Docking só para FKS_8WL6 (usa Vina sequencial + timeout)
dock_fks8wl6: prep_ligands
	OUTFILE=docking_results/summary_affinities.csv \
	TARGET=$(FKS_TARGET) \
	EXH=$(EXH) NM=$(NM) \
	./tools/dock_fks8wl6.sh $(LIG_LIST)

# Pipeline completo para FKS_8WL6: docking + score + pareto + shortlist
fks_pipeline: dock_fks8wl6 score pareto shortlist
	@echo "[DONE] Pipeline FKS_8WL6 concluído. Veja docking_results/*.csv"

# --------------------------------------------------------------------
# Ambiente virtual e pipeline CHS
# --------------------------------------------------------------------

.ONESHELL:
chs_env:
	python3 -m venv .venv
	. .venv/bin/activate; \
	$(PIP) install -U pip; \
	$(PIP) install -r requirements-chs.txt
	@echo "[OK] Ambiente pronto. Ative com: source .venv/bin/activate"

# Full automation for CHS: build model (ESMFold), prepare, dock, and summarize
full_chs: chs_env
	bash scripts/run_full_chs_pipeline.sh \
		--device $(if $(DEVICE),$(DEVICE),auto) \
		--exh $(if $(EXH),$(EXH),16) \
		--seed $(if $(SEED),$(SEED),42)

.ONESHELL:
chs_build:
	. .venv/bin/activate; \
	if [ ! -s targets/CHS.pdb ]; then \
	  echo "[BUILD] Gerando CHS.pdb via ESMFold ($(DEVICE))"; \
	  $(PY) scripts/build_chs_pdb.py \
	    --fasta $(if $(FASTA),$(FASTA),targets/MP_B2XSE6.fasta) \
	    --out $(if $(OUT),$(OUT),targets/CHS.pdb) \
	    --device $(DEVICE); \
	fi; \
	if [ ! -s targets/CHS.pdbqt ]; then \
	  echo "[PREP] Preparando CHS.pdbqt via OpenBabel"; \
	  obabel -ipdb targets/CHS.pdb -opdbqt -O targets/CHS.pdbqt -xh --partialcharge gasteiger || \
	  obabel -ipdb targets/CHS.pdb -opdbqt -O targets/CHS.pdbqt -xh; \
	fi; \
	if [ ! -s targets/CHS.box ]; then \
	  echo "[BOX] Gerando CHS.box (cubo 26 Å centrado)"; \
	  $(PY) tools/compute_box_simple.py --pdb targets/CHS.pdb --fixed-size 26.0 --out targets/CHS.box; \
	fi; \
	echo "[DOCK] CHS (EXH=$(EXH), NM=$(NM), SEED=$(SEED))"; \
	EXH=$(EXH) NM=$(NM) SEED=$(SEED) bash scripts/run_chs_set.sh; \
	echo "[OK] CHS completo. Ranking/ΔΔG atualizados."

# Refinar caixa com fpocket (usar caminho do pocket PDB):
# uso: make chs_box_fpocket POCKET=chs_fpocket_out/CHS_out/pockets/pocket1_atm.pdb
chs_box_fpocket:
	@if [ -z "$(POCKET)" ]; then echo "Usage: make chs_box_fpocket POCKET=<path_to_pocket_pdb>"; exit 2; fi
	$(PY) tools/compute_box_simple.py --pdb "$(POCKET)" --margin 4.0 --cubic --out targets/CHS.box
	@echo "[OK] Atualizado: targets/CHS.box"

# Refinar caixa a partir de uma pose de ligante:
# uso: make chs_box_ligand LIG=caspofungin [MARGIN=6.0]
chs_box_ligand:
	@if [ -z "$(LIG)" ]; then echo "Usage: make chs_box_ligand LIG=<ligand_base> [MARGIN=6.0]"; exit 2; fi
	$(PY) tools/compute_box_simple.py --pdb docking_results_smina/CHS/$(LIG)/$(LIG)_on_CHS.pdbqt --margin $(if $(MARGIN),$(MARGIN),6.0) --cubic --out targets/CHS.box
	@echo "[OK] Atualizado: targets/CHS.box"

# --------------------------------------------------------------------
# Consensus (Vina + Smina) e multiobjetivo
# --------------------------------------------------------------------
.ONESHELL:
consensus:
	$(PY) tools/rebuild_summary_from_logs.py \
		--roots docking_results_smina \
		--out docking_results/summary_affinities_vina.csv
	$(PY) tools/rebuild_summary_from_logs.py \
		--roots docking_results_smina_auto \
		--out docking_results/summary_affinities_smina.csv
	$(PY) tools/consensus_scores.py \
		--vina docking_results/summary_affinities_vina.csv \
		--smina docking_results/summary_affinities_smina.csv \
		--out docking_results/consensus_affinities.csv
	$(PY) tools/score_multiobjective.py \
		--summary docking_results/consensus_affinities.csv \
		--props data/ligantes_props_obabel.csv \
		--config config/scoring.yaml \
		--ref-target $(REF) \
		--out-scored docking_results/consensus_scored.csv \
		--out-ranking docking_results/consensus_ranking.csv
	$(PY) tools/pareto.py \
		--input docking_results/consensus_scored.csv \
		--out docking_results/consensus_pareto_front.csv
	$(PY) tools/shortlist.py \
		--scored docking_results/consensus_scored.csv \
		--out docking_results/consensus_shortlist.csv
	@echo "[OK] Consensus computed. See docking_results/consensus_*.csv"
