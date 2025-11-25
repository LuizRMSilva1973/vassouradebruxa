import os
import yaml

configfile: "config/pipeline.yaml"

# Default targets
USE_CONSENSUS = config.get("consensus", {}).get("enabled", False)
ENABLE_PARETO = config.get("pareto", {}).get("enabled", True)

SUMMARY_DIR = "docking_results"
SUMMARY_CSV = f"{SUMMARY_DIR}/summary_affinities.csv"
SUMMARY_SMINA = f"{SUMMARY_DIR}_smina/summary_affinities.csv"
SUMMARY_CONS = f"{SUMMARY_DIR}/consensus_affinities.csv"
SCORED_CSV = f"{SUMMARY_DIR}/scored.csv"
RANKING_CSV = f"{SUMMARY_DIR}/ranking_overall.csv"
PARETO_CSV = f"{SUMMARY_DIR}/pareto_front.csv"
SHORTLIST_CSV = f"{SUMMARY_DIR}/shortlist.csv"
DB_FILE = config.get("duckdb", {}).get("path", "data/results.duckdb")
LIB_SMILES = "data/library_smiles.csv"
LIB_STAMP = "data/.library_built"

def score_input():
    if USE_CONSENSUS:
        return SUMMARY_CONS
    return SUMMARY_CSV

rule all:
    input:
        SCORED_CSV,
        RANKING_CSV,
        SHORTLIST_CSV,
        DB_FILE,
        PARETO_CSV if ENABLE_PARETO else []
        ,LIB_STAMP if os.path.exists(LIB_SMILES) else []

rule build_library:
    input:
        LIB_SMILES
    output:
        LIB_STAMP
    shell:
        (
            "python3 tools/build_library_from_smiles.py --csv {input} --outdir ligands && "
            "echo built > {output}"
        )

rule props_obabel:
    input:
        expand("ligands/{{name}}.sdf", name=lambda: [p[:-4] for p in os.listdir("ligands") if p.endswith(".sdf")])
    output:
        "data/ligantes_props_obabel.csv"
    shell:
        "python3 tools/ligand_props_obabel.py --indir ligands --output {output}"

rule docking_vina:
    output:
        SUMMARY_CSV
    params:
        e=lambda w: config.get("vina", {}).get("exhaustiveness", 16),
        n=lambda w: config.get("vina", {}).get("num_modes", 9),
        t=lambda w: config.get("vina", {}).get("threads", ""),
        cpu=lambda w: config.get("vina", {}).get("cpu", "")
    shell:
        (
            "EXHAUSTIVENESS={params.e} NUM_MODES={params.n} VINA_CPU={params.cpu} "
            "./run_docking.sh "
            "{('-t ' + str(params.t)) if str(params.t) else ''}"
        )

rule docking_smina:
    output:
        SUMMARY_SMINA
    params:
        e=lambda w: config.get("smina", {}).get("exhaustiveness", 16),
        n=lambda w: config.get("smina", {}).get("num_modes", 9)
    shell:
        (
            "python3 tools/run_smina_batch.py --targets targets --ligands ligands "
            "--outdir docking_results_smina --exhaustiveness {params.e} --num-modes {params.n}"
        )

rule consensus_affinities:
    input:
        vina=SUMMARY_CSV,
        smina=SUMMARY_SMINA
    output:
        SUMMARY_CONS
    shell:
        "python3 tools/consensus_scores.py --vina {input.vina} --smina {input.smina} --out {output}"

rule postprocess:
    input:
        summary=SUMMARY_CSV
    output:
        sorted=f"{SUMMARY_DIR}/summary_sorted.csv",
        ddg=f"{SUMMARY_DIR}/summary_ddg.csv",
        ligsum=f"{SUMMARY_DIR}/ligand_selectivity_summary.csv"
    params:
        ref=lambda w: config.get("postprocess", {}).get("ref_target", "FKS_8WL6")
    shell:
        (
            "python3 postprocess_docking.py --input {input.summary} --ref-target {params.ref} "
            "--out-sorted {output.sorted} --out-ddg {output.ddg} --out-ligand-summary {output.ligsum}"
        )

rule score_multiobjective:
    input:
        summary=lambda w: score_input(),
        props="data/ligantes_props_obabel.csv",
        cfg="config/scoring.yaml"
    output:
        scored=SCORED_CSV,
        ranking=RANKING_CSV
    params:
        ref=lambda w: config.get("score", {}).get("ref_target", "FKS_8WL6")
    shell:
        (
            "python3 tools/score_multiobjective.py --summary {input.summary} --props {input.props} "
            "--config {input.cfg} --ref-target {params.ref} --out-scored {output.scored} --out-ranking {output.ranking}"
        )

rule pareto:
    input:
        SCORED_CSV
    output:
        PARETO_CSV
    params:
        cols=lambda w: config.get("pareto", {}).get("columns", ["score","xymove","best_affinity_kcal_per_mol"]) ,
        maximize=lambda w: config.get("pareto", {}).get("maximize", [True, True, False])
    shell:
        "python3 tools/pareto.py --input {input} --out {output} --columns {params.cols} --maximize {params.maximize}"

rule shortlist:
    input:
        scored=SCORED_CSV,
        ranking=RANKING_CSV
    output:
        SHORTLIST_CSV
    params:
        min_score=lambda w: config.get("shortlist", {}).get("min_score", 0.45),
        min_xymove=lambda w: config.get("shortlist", {}).get("min_xymove", 0.35),
        top_k=lambda w: config.get("shortlist", {}).get("top_k", 25),
        per_target_top=lambda w: config.get("shortlist", {}).get("per_target_top", 5)
    shell:
        (
            "python3 tools/shortlist.py --scored {input.scored} --ranking {input.ranking} "
            "--out {output} --min-score {params.min_score} --min-xymove {params.min_xymove} "
            "--top-k {params.top_k} --per-target-top {params.per_target_top}"
        )

rule load_duckdb:
    input:
        scored=SCORED_CSV,
        ranking=RANKING_CSV,
        summary=SUMMARY_CSV
    output:
        DB_FILE
    shell:
        "python3 tools/load_to_duckdb.py --db {output} --schema schema.sql"
