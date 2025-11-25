#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-prep + docking para macropeptídeos (equinocandinas) com heurística/IA para reduzir torções.

Fluxo:
  SDF -> RDKit 3D (ETKDG+UFF) -> seleção de torções a congelar (heurística ou modelo ML opcional) ->
  PDBQT (Meeko; fallback prepare_ligand4.py) -> SMINA -> CSV/relatório.

Uso:
  python tools/auto_prepare_echinocandins.py \
    --ligands ligands/ \
    --targets targets/FKS.pdbqt \
    --box targets/FKS.box \
    --out docking_results_smina_auto/FKS \
    --exhaustiveness 8 --num-modes 9 --cpu 1 \
    --max-rotatable 12 \
    [--model models/torsion_freeze.pkl] \
    [--env-smina smina] [--prep-mgl /tmp/miniconda_smina/envs/smina/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_ligand4.py]

Observações:
- Se `meeko` estiver presente, geramos PDBQT direto no Python e marcamos as torções como FIXAS.
- Sem `meeko`, fazemos fallback para prepare_ligand4.py (precisa do PDB intermediário + MGLTools).
- O seletor de torções reduz até `--max-rotatable` ou congela o conjunto previsto pelo modelo.
"""

import os, sys, json, time, subprocess, shutil, glob, argparse
from pathlib import Path

import numpy as np
import pandas as pd

# RDKit
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolTransforms, rdmolops

# Opcional: modelo ML
try:
    from joblib import load as joblib_load
except Exception:
    joblib_load = None

# Opcional: Meeko para PDBQT direto
try:
    from meeko import MoleculePreparation, PDBQTWriterLegacy
except Exception:
    MoleculePreparation = None
    PDBQTWriterLegacy = None


def shell(cmd, check=True, env=None):
    print(f"[CMD] {cmd}")
    return subprocess.run(cmd, shell=True, check=check, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def rdkit_load_sdf_to_mol(sdf_path: Path):
    suppl = Chem.SDMolSupplier(str(sdf_path), removeHs=False, sanitize=True)
    mol = next((m for m in suppl if m is not None), None)
    if mol is None:
        raise RuntimeError(f"Falha ao ler SDF: {sdf_path}")
    # Adiciona Hs explícitos para melhor 3D
    mol = Chem.AddHs(mol)
    return mol


def rdkit_embed_minimize(mol, seed=42, max_iters=500):
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    params.useSmallRingTorsions = True
    params.useMacrocycleTorsions = True  # importante p/ macropeptídeos
    if AllChem.EmbedMolecule(mol, params) != 0:
        # fallback: Force random coords
        AllChem.EmbedMolecule(mol, useRandomCoords=True, randomSeed=seed)
    # Minimização UFF
    try:
        AllChem.UFFOptimizeMolecule(mol, maxIters=max_iters)
    except Exception:
        pass
    return mol


def list_rotatable_bonds(mol):
    # Padrão de ligação rotável (RDKit definition)
    rot_bond_smarts = Chem.MolFromSmarts("[!$(*#*)&!D1]-!@[!$(*#*)&!D1]")
    matches = mol.GetSubstructMatches(rot_bond_smarts)
    bonds = set()
    for u, v in matches:
        bond = mol.GetBondBetweenAtoms(u, v)
        if bond is not None and not bond.IsInRing():
            bonds.add((min(u, v), max(u, v)))
    # filtra amida (congelar por padrão)
    amide = Chem.MolFromSmarts("C(=O)-N")
    amide_matches = set()
    # GetSubstructMatches returns tuples for all atoms in the SMARTS; for C(=O)-N it's (C,O,N)
    for match in mol.GetSubstructMatches(amide):
        if len(match) >= 3:
            c_idx = match[0]
            n_idx = match[2]
            bond = mol.GetBondBetweenAtoms(c_idx, n_idx)
            if bond is not None:
                amide_matches.add((min(c_idx, n_idx), max(c_idx, n_idx)))
    return sorted(list(bonds)), amide_matches


def bond_features(mol, bond_uv):
    u, v = bond_uv
    bu = mol.GetAtomWithIdx(u)
    bv = mol.GetAtomWithIdx(v)
    b = mol.GetBondBetweenAtoms(u, v)
    feats = {
        "u_atomic_num": bu.GetAtomicNum(),
        "v_atomic_num": bv.GetAtomicNum(),
        "bond_order": int(b.GetBondTypeAsDouble()),
        "u_degree": bu.GetDegree(),
        "v_degree": bv.GetDegree(),
        "is_conjugated": int(b.GetIsConjugated()),
        "is_in_ring": int(b.IsInRing()),
        "u_is_aromatic": int(bu.GetIsAromatic()),
        "v_is_aromatic": int(bv.GetIsAromatic()),
    }
    return feats


def heuristic_freeze_selector(mol, rot_bonds, amide_bonds, max_rotatable=12):
    """
    Heurística: sempre congelar amidas; depois priorizar congelar
    - ligações imediatamente adjacentes a anéis grandes,
    - ligações altamente conjugadas,
    - até que o total de rotáveis <= max_rotatable.
    """
    to_freeze = set(amide_bonds)

    def bond_score(buv):
        feat = bond_features(mol, buv)
        score = 0.0
        # amida já foi adicionada; aqui valorizamos conjugação/anéis
        score += 1.5 * feat["is_conjugated"]
        score += 1.0 * (feat["u_is_aromatic"] or feat["v_is_aromatic"])
        score += 0.5 * (feat["u_degree"] >= 3) + 0.5 * (feat["v_degree"] >= 3)
        # favorecer congelar ligações com ordem > 1?
        score += 0.5 * (feat["bond_order"] > 1)
        return score

    # Rotáveis atuais (excluindo já congelados)
    remaining = [b for b in rot_bonds if b not in to_freeze]
    remaining_sorted = sorted(remaining, key=bond_score, reverse=True)

    # Estimativa: se número de rotáveis > max_rotatable, ir congelando pelos scores
    # (não tocamos em anéis)
    current_rot = len(rot_bonds)
    for b in remaining_sorted:
        if current_rot <= max_rotatable:
            break
        to_freeze.add(b)
        current_rot -= 1

    return to_freeze


def ml_freeze_selector(mol, rot_bonds, model_path, fallback_selector, max_rotatable):
    if not joblib_load or not os.path.isfile(model_path):
        return fallback_selector(mol, rot_bonds, set(), max_rotatable)
    model = joblib_load(model_path)
    X, feats_idx = [], []
    for b in rot_bonds:
        X.append(list(bond_features(mol, b).values()))
        feats_idx.append(b)
    X = np.array(X, dtype=float)
    # Modelo deve prever probabilidade de "congelar"
    proba = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else model.predict(X)
    # Ordena por probabilidade desc
    order = np.argsort(-proba)
    to_freeze = set()
    current_rot = len(rot_bonds)
    for i in order:
        if current_rot <= max_rotatable:
            break
        to_freeze.add(feats_idx[i])
        current_rot -= 1
    return to_freeze


def meeko_write_pdbqt(mol, pdbqt_path, frozen_bonds):
    # Define rotatable bonds mask para Meeko
    # Meeko usa percepções automáticas; passamos a lista de ligações a FIXAR.
    # Some Meeko builds don't accept keep_nonpolar_hydrogens; use default ctor
    prep = MoleculePreparation()
    # Marcar ligações a travar: Meeko aceita "set_rotatable_bond" (!= API pública estável),
    # então fazemos um truque: após prepare, acessamos graph e travamos "active_torsions".
    mprep = prep.prepare(mol)
    # Some Meeko versions return a list; take the first
    if isinstance(mprep, (list, tuple)) and len(mprep) > 0:
        mprep_obj = mprep[0]
    else:
        mprep_obj = mprep
    # travar torções se atributo existir
    locked = 0
    torsions = getattr(mprep_obj, 'torsions', [])
    for torsion in torsions:
        a1, a2 = torsion.atom_indices[1], torsion.atom_indices[2]
        uv = (min(a1, a2), max(a1, a2))
        if uv in frozen_bonds:
            setattr(torsion, 'active', False)
            locked += 1
    writer = PDBQTWriterLegacy()
    pdbqt_str = writer.write_string(mprep_obj)
    Path(pdbqt_path).write_text(pdbqt_str)
    return locked


def fallback_prepare_ligand4(pdb_path, pdbqt_out, prep_mgl, conda_env=None):
    if not prep_mgl or not os.path.isfile(prep_mgl):
        raise RuntimeError("prepare_ligand4.py não encontrado; instale MGLTools ou informe --prep-mgl")
    # Prefer 'pythonsh' if available (MGLTools wrapper), else use python
    pythonsh = shutil.which("pythonsh")
    # Run in the directory of the PDB to avoid issues with spaces in paths
    pdb_dir = os.path.dirname(os.path.abspath(pdb_path))
    pdb_base = os.path.basename(pdb_path)
    out_base = os.path.basename(pdbqt_out)
    if pythonsh:
        inner = f'"{pythonsh}" "{prep_mgl}" -l "{pdb_base}" -o "{out_base}" -U nphs_lps_waters_nonstdres'
        if conda_env:
            inner = f'conda run -n {conda_env} ' + inner
        cmd = f'cd "{pdb_dir}" && {inner}'
    else:
        inner = f'python "{prep_mgl}" -l "{pdb_base}" -o "{out_base}" -U nphs_lps_waters_nonstdres'
        if conda_env:
            inner = f'conda run -n {conda_env} ' + inner
        cmd = f'cd "{pdb_dir}" && {inner}'
    shell(cmd, check=True)


def write_pdb_from_rdkit(mol, out_pdb):
    # RDKit -> MOL -> OpenBabel para PDB robusto (opção A), ou RDKit Writer direto (opção B)
    # Opção B:
    Chem.MolToPDBFile(mol, str(out_pdb))


def run_smina(receptor_pdbqt, ligand_pdbqt, box_file, out_dir, ex=8, nm=9, cpu=1, seed=42, env_smina=None):
    box_txt = Path(box_file).read_text().strip().splitlines()
    kv = dict(line.split("=") for line in box_txt if "=" in line)
    cx, cy, cz = kv["center_x"], kv["center_y"], kv["center_z"]
    sx, sy, sz = kv["size_x"], kv["size_y"], kv["size_z"]

    lig_base = Path(ligand_pdbqt).stem
    out_pose = Path(out_dir) / f"{lig_base}_on_{Path(receptor_pdbqt).stem}.pdbqt"
    out_log  = Path(out_dir) / f"{lig_base}_on_{Path(receptor_pdbqt).stem}.log"
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    smina_cmd = f'smina --receptor "{receptor_pdbqt}" --ligand "{ligand_pdbqt}" ' \
                f'--center_x {cx} --center_y {cy} --center_z {cz} ' \
                f'--size_x {sx} --size_y {sy} --size_z {sz} ' \
                f'--exhaustiveness {ex} --num_modes {nm} --cpu {cpu} --seed {seed} ' \
                f'--out "{out_pose}" > "{out_log}" 2>&1'
    if env_smina:
        smina_cmd = f'conda run -n {env_smina} ' + smina_cmd
    res = shell(smina_cmd, check=False)
    return out_pose, out_log, res.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ligands", required=True, help="Pasta com SDFs ou caminho para um SDF único")
    ap.add_argument("--targets", required=True, help="receptor .pdbqt")
    ap.add_argument("--box", required=True, help=".box com center/size")
    ap.add_argument("--out", required=True, help="pasta de saída (logs/poses/CSVs)")
    ap.add_argument("--exhaustiveness", type=int, default=8)
    ap.add_argument("--num-modes", type=int, default=9)
    ap.add_argument("--cpu", type=int, default=1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-rotatable", type=int, default=12)
    ap.add_argument("--model", default=None, help="joblib pkl para predição de torções a congelar (opcional)")
    ap.add_argument("--env-smina", default=None, help="nome do env conda p/ rodar smina (ex.: smina)")
    ap.add_argument("--prep-mgl", default=None, help="caminho para prepare_ligand4.py p/ fallback")
    ap.add_argument("--force-mgl", action="store_true", help="força usar prepare_ligand4.py mesmo se Meeko estiver disponível")
    args = ap.parse_args()

    lig_paths = []
    L = Path(args.ligands)
    if L.is_dir():
        lig_paths = sorted(list(L.glob("*.sdf")))
    else:
        lig_paths = [L]

    out_root = Path(args.out); out_root.mkdir(parents=True, exist_ok=True)
    prep_dir  = out_root / "prepared"; prep_dir.mkdir(exist_ok=True)
    report_rows = []

    for sdf in lig_paths:
        name = sdf.stem.replace(" ", "_")
        try:
            mol = rdkit_load_sdf_to_mol(sdf)
            mol = rdkit_embed_minimize(mol, seed=args.seed)
            rot_bonds, amide_bonds = list_rotatable_bonds(mol)

            # Seleção de torções a congelar (ML opcional, senão heurística)
            if args.model:
                freeze_set = ml_freeze_selector(
                    mol, rot_bonds, args.model,
                    fallback_selector=lambda m, r, a, k: heuristic_freeze_selector(m, r, a, k),
                    max_rotatable=args.max_rotatable
                )
            else:
                freeze_set = heuristic_freeze_selector(mol, rot_bonds, amide_bonds, args.max_rotatable)

            # Geração de PDBQT
            pdbqt_out = prep_dir / f"{name}.pdbqt"
            locked = None
            use_meeko = (MoleculePreparation is not None and PDBQTWriterLegacy is not None and not args.force_mgl)
            if use_meeko:
                locked = meeko_write_pdbqt(mol, pdbqt_out, freeze_set)
            else:
                # Fallback: escreve PDB e chama prepare_ligand4.py
                pdb_tmp = prep_dir / f"{name}.pdb"
                write_pdb_from_rdkit(mol, pdb_tmp)
                fallback_prepare_ligand4(pdb_tmp, pdbqt_out, args.prep_mgl, args.env_smina)
                locked = len(freeze_set)  # indicativo apenas

            # Docking
            out_dir = out_root / f"{Path(args.targets).stem}" / name
            pose, logf, rc = run_smina(args.targets, str(pdbqt_out), args.box, out_dir,
                                       ex=args.exhaustiveness, nm=args.num_modes, cpu=args.cpu, seed=args.seed,
                                       env_smina=args.env_smina)

            # Extrair ΔG do log
            dg = None
            try:
                txt = Path(logf).read_text(errors="ignore").splitlines()
                for line in txt:
                    # smina output: "   1          -8.5  0.000  0.000"
                    if line.strip().startswith("1"):
                        parts = line.split()
                        if len(parts) >= 2:
                            dg = float(parts[1])
                            break
            except Exception:
                pass

            report_rows.append({
                "ligand": name,
                "sdf": str(sdf),
                "pdbqt": str(pdbqt_out),
                "rotatable_before": len(rot_bonds),
                "frozen": locked,
                "rotatable_after_est": max(0, len(rot_bonds) - (locked or 0)),
                "vina_dg_kcal_mol": dg,
                "smina_rc": rc,
                "log": str(logf),
                "pose": str(pose),
            })
            print(f"[OK] {name}: dg={dg}, frozen={locked}, rc={rc}")

        except Exception as e:
            print(f"[ERR] {name}: {e}")
            report_rows.append({
                "ligand": name, "error": str(e), "sdf": str(sdf)
            })

    df = pd.DataFrame(report_rows)
    df.to_csv(out_root / "summary_auto.csv", index=False)
    print(f"[DONE] summary: {out_root/'summary_auto.csv'}")


if __name__ == "__main__":
    main()
