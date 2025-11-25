import subprocess, sys
from pathlib import Path

PDB_OK = """\
ATOM      1  C   ALA A   1      10.000  10.000  10.000  1.00 20.00           C
ATOM      2  C   ALA A   2      20.000  30.000  40.000  1.00 20.00           C
"""


def test_box_from_valid_pdb(tmp_path):
    pdb = tmp_path / "rec.pdb"
    pdb.write_text(PDB_OK)
    out = tmp_path / "box.box"
    cmd = [sys.executable, "tools/compute_box_simple.py", "--pdb", str(pdb),
           "--fixed-size", "26.0", "--out", str(out)]
    subprocess.run(cmd, check=True)
    txt = out.read_text()
    assert "center_x=" in txt and "size_x=26.0" in txt


def test_box_from_invalid_pdb_fails(tmp_path):
    pdb = tmp_path / "bad.pdb"
    pdb.write_text("<html>error</html>")
    out = tmp_path / "box.box"
    cmd = [sys.executable, "tools/compute_box_simple.py", "--pdb", str(pdb),
           "--fixed-size", "26.0", "--out", str(out)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    assert p.returncode != 0
    msg = (p.stdout + p.stderr).lower()
    assert "no atom/hetatm" in msg or "receptor file not found" in msg or "the file may be invalid" in msg

