#!/usr/bin/env python3
"""
Compute Vina box (center/size) by parsing PDB text directly (no Biopython).
Supports selection by HET ligand name (e.g., --het NAG) or by residues list (--res A:123,B:45).

Usage:
  python3 tools/compute_box_simple.py --pdb targets/FKS.pdb --het NAG --margin 4.0 --cubic --out targets/FKS.box
"""
import argparse
from pathlib import Path
from typing import List, Tuple


def parse_res_list(s: str) -> List[Tuple[str, int, str]]:
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


def collect_coords(pdb_path: Path, het: str = None, residues: List[Tuple[str, int, str]] = None):
    coords = []
    het = het.strip().upper() if het else None
    resset = set(residues or [])
    with pdb_path.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if not (line.startswith('ATOM') or line.startswith('HETATM')):
                continue
            rec = line[:6].strip()
            resname = line[17:20].strip().upper()
            chain = line[21:22]
            resseq_str = line[22:26]
            icode = line[26:27]
            try:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
            except Exception:
                continue
            # Selection logic
            if residues:
                try:
                    resseq = int(resseq_str)
                except Exception:
                    continue
                match = False
                for (c, r, i) in resset:
                    if (c is None or c == chain) and (r == resseq) and (i == icode):
                        match = True
                        break
                if match:
                    coords.append((x, y, z))
            elif het:
                # Only HETATM lines with matching resname and not water
                if rec == 'HETATM' and resname == het and resname != 'HOH':
                    coords.append((x, y, z))
            else:
                # Default: all HETATMs except water; fallback to all atoms if none
                if rec == 'HETATM' and resname != 'HOH':
                    coords.append((x, y, z))
    # Fallback if het None and residues None but no HETATMs matched
    if not coords and not (het or residues):
        with pdb_path.open('r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    try:
                        x = float(line[30:38])
                        y = float(line[38:46])
                        z = float(line[46:54])
                        coords.append((x, y, z))
                    except Exception:
                        continue
    return coords


def calc_box(coords, margin: float = 4.0, cubic: bool = False):
    if not coords:
        raise ValueError('Empty selection: no atoms matched')
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
    ap = argparse.ArgumentParser(description='Compute Vina box without Biopython')
    ap.add_argument('--pdb', required=True)
    ap.add_argument('--het', default=None)
    ap.add_argument('--res', default=None)
    ap.add_argument('--margin', type=float, default=4.0)
    ap.add_argument('--cubic', action='store_true')
    ap.add_argument('--fixed-size', type=float, default=None, help='Force cubic box of given size (Å); center from selection')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    pdb = Path(args.pdb)
    residues = parse_res_list(args.res) if args.res else None
    coords = collect_coords(pdb, het=args.het, residues=residues)
    if args.fixed_size:
        # center from selection, fixed cubic size
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        zs = [c[2] for c in coords]
        cx = sum(xs)/len(xs)
        cy = sum(ys)/len(ys)
        cz = sum(zs)/len(zs)
        sx = sy = sz = float(args.fixed_size)
    else:
        cx, cy, cz, sx, sy, sz = calc_box(coords, margin=args.margin, cubic=args.cubic)
    lines = [
        f'center_x={cx:.3f}',
        f'center_y={cy:.3f}',
        f'center_z={cz:.3f}',
        f'size_x={sx:.3f}',
        f'size_y={sy:.3f}',
        f'size_z={sz:.3f}',
    ]
    if args.out:
        Path(args.out).write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print(f'[OK] Box written: {args.out}')
    else:
        print('\n'.join(lines))


if __name__ == '__main__':
    main()
