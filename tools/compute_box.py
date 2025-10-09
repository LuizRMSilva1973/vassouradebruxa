#!/usr/bin/env python3
"""
Compute a Vina box (center/size) from a PDB structure given a selection:
- by HET ligand name (e.g., LIG), or
- by residue list (e.g., A:123,B:45), or
- fallback: all HETATMs (non-water) or the whole model.

Outputs lines in the format expected by targets/<ALVO>.box:
  center_x=...
  center_y=...
  center_z=...
  size_x=...
  size_y=...
  size_z=...

Example:
  python3 tools/compute_box.py --pdb targets/FKS.pdb --het LIG --margin 4.0 --out targets/FKS.box

Dependencies: Biopython (Bio.PDB). Optional: NumPy (not required).
"""
import argparse
from pathlib import Path
from typing import List, Tuple

from Bio.PDB import PDBParser


def parse_res_list(s: str) -> List[Tuple[str, int, str]]:
    """Parse a residue list like "A:123,B:45,.:10a" into tuples (chain, resseq, icode).
    Use "." to denote any chain; insertion code optional (e.g., 10A -> icode='A')."""
    out = []
    if not s:
        return out
    for tok in s.split(','):
        tok = tok.strip()
        if not tok:
            continue
        if ':' in tok:
            chain, rid = tok.split(':', 1)
        else:
            chain, rid = '.', tok
        chain = None if chain == '.' else chain
        icode = ' '
        # support like 10A -> resseq=10, icode='A'
        num = ''
        for ch in rid:
            if ch.isdigit():
                num += ch
            else:
                icode = ch
        if not num:
            raise ValueError(f"Residue id must contain a number: {tok}")
        out.append((chain, int(num), icode))
    return out


def collect_coords(structure, het: str = None, residues: List[Tuple[str, int, str]] = None):
    atoms = []
    if residues:
        resset = set(residues)
        for model in structure:
            for chain in model:
                for res in chain:
                    hetflag, resseq, icode = res.id
                    key = (chain.id, resseq, icode)
                    match = False
                    # allow wildcard chain if provided as (None,...)
                    for (c, r, i) in resset:
                        if (c is None or c == chain.id) and (r == resseq) and (i == icode):
                            match = True
                            break
                    if match:
                        for atom in res.get_atoms():
                            atoms.append(atom)
    elif het:
        het = het.strip().upper()
        for model in structure:
            for chain in model:
                for res in chain:
                    resname = res.get_resname().upper()
                    hetflag, _, _ = res.id
                    if hetflag.startswith('H') and resname == het and resname != 'HOH':
                        for atom in res.get_atoms():
                            atoms.append(atom)
    else:
        # all HETATMs except water; if none, all atoms
        for model in structure:
            for chain in model:
                for res in chain:
                    hetflag, _, _ = res.id
                    if hetflag.startswith('H') and res.get_resname().upper() != 'HOH':
                        for atom in res.get_atoms():
                            atoms.append(atom)
        if not atoms:
            for atom in structure.get_atoms():
                atoms.append(atom)

    coords = [atom.coord for atom in atoms]
    return coords


def calc_box(coords, margin: float = 4.0, cubic: bool = False):
    if not coords:
        raise ValueError("Empty selection: no atoms matched.")
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    zs = [c[2] for c in coords]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    minz, maxz = min(zs), max(zs)
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    cz = (minz + maxz) / 2.0
    sx = (maxx - minx) + 2 * margin
    sy = (maxy - miny) + 2 * margin
    sz = (maxz - minz) + 2 * margin
    if cubic:
        m = max(sx, sy, sz)
        sx = sy = sz = m
    return cx, cy, cz, sx, sy, sz


def main():
    ap = argparse.ArgumentParser(description="Compute Vina box from PDB selection")
    ap.add_argument("--pdb", required=True, help="Input PDB path")
    ap.add_argument("--het", default=None, help="HET ligand 3-letter code (e.g., LIG)")
    ap.add_argument("--res", default=None, help="Residues list, e.g., A:123,B:45 or .:10A")
    ap.add_argument("--margin", type=float, default=4.0, help="Padding (Å) added around selection")
    ap.add_argument("--cubic", action="store_true", help="Use a cubic box (max dimension)")
    ap.add_argument("--out", default=None, help="Write box to this path")
    args = ap.parse_args()

    pdb_path = Path(args.pdb)
    if not pdb_path.exists():
        raise SystemExit(f"PDB not found: {pdb_path}")

    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("STRUCT", str(pdb_path))

    residues = parse_res_list(args.res) if args.res else None
    coords = collect_coords(structure, het=args.het, residues=residues)
    cx, cy, cz, sx, sy, sz = calc_box(coords, margin=args.margin, cubic=args.cubic)

    lines = [
        f"center_x={cx:.3f}",
        f"center_y={cy:.3f}",
        f"center_z={cz:.3f}",
        f"size_x={sx:.3f}",
        f"size_y={sy:.3f}",
        f"size_z={sz:.3f}",
    ]

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[OK] Box written to: {args.out}")
    else:
        print("\n".join(lines))


if __name__ == "__main__":
    main()

