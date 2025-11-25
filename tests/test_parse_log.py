from pathlib import Path
from tools.rebuild_summary_from_logs import parse_log

SMINA = """\
# smina 1.2.3
mode |   affinity | dist from best mode
     | (kcal/mol) | rmsd l.b.| rmsd u.b.
-----+------------+----------+----------
   1        -7.4      0.000      0.000
   2        -6.2      2.0        3.1
"""

VINA = """\
# AutoDock Vina
mode |   affinity | dist from best mode
     | (kcal/mol) | rmsd l.b.| rmsd u.b.
-----+------------+----------+----------
   1        -6.1      0.000      0.000
"""


def _write(tmp_path: Path, target="FKS", ligand="rezafungin", body=VINA):
    log = tmp_path / "docking_results_smina" / target / ligand / f"{ligand}_on_{target}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(body)
    return log


def test_parse_vina(tmp_path):
    log = _write(tmp_path, body=VINA)
    r = parse_log(log)
    assert r["target"] == "FKS"
    assert r["ligand"] == "rezafungin"
    assert abs(float(r["best_affinity_kcal_per_mol"]) - (-6.1)) < 1e-6


def test_parse_smina(tmp_path):
    log = _write(tmp_path, body=SMINA)
    r = parse_log(log)
    assert abs(float(r["best_affinity_kcal_per_mol"]) - (-7.4)) < 1e-6

