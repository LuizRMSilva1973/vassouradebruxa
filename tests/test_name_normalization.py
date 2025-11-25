import csv, sys, subprocess
from pathlib import Path

SCORING_YAML = """\
weights:
  affinity: 1.0
  selectivity: 0.0
  xymove: 0.0
constraints:
  min_xymove: 0.0
"""


def write_csv(p, rows, header):
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def test_synonym_merge(tmp_path):
    # Summary com dois sinônimos do mesmo ligante
    summary = tmp_path / "summary.csv"
    rows = [
        {"target": "FKS", "ligand": "papulacandin B", "best_affinity_kcal_per_mol": "-6.1"},
        {"target": "FKS", "ligand": "papulacandin_B", "best_affinity_kcal_per_mol": "-5.8"},
    ]
    write_csv(summary, rows, ["target", "ligand", "best_affinity_kcal_per_mol"])

    props = tmp_path / "props.csv"
    write_csv(props, [{"ligand": "papulacandin B", "logP": "3.1"}], ["ligand", "logP"])

    cfg = tmp_path / "scoring.yaml"
    cfg.write_text(SCORING_YAML)

    scored = tmp_path / "scored.csv"
    ranking = tmp_path / "ranking.csv"

    cmd = [sys.executable, "tools/score_multiobjective.py", "--summary", str(summary),
           "--props", str(props), "--config", str(cfg),
           "--out-scored", str(scored), "--out-ranking", str(ranking)]
    subprocess.run(cmd, check=True)

    txt = ranking.read_text().lower()
    # Deve haver apenas 1 entrada (a melhor, -6.1)
    assert txt.count("papulacandin") == 1
    assert "-6.1" in (scored.read_text() + txt)

