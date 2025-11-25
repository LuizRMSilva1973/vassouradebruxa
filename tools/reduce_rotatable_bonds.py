from rdkit import Chem
from rdkit.Chem import AllChem
import argparse

def reduce_rotatable_bonds(input_sdf, output_sdf, max_rotatable_bonds=6):
    suppl = Chem.SDMolSupplier(input_sdf)
    writer = Chem.SDWriter(output_sdf)

    for mol in suppl:
        if mol is None:
            continue

        # Get the number of rotatable bonds
        num_rotatable_bonds = AllChem.CalcNumRotatableBonds(mol)

        if num_rotatable_bonds > max_rotatable_bonds:
            # Attempt to reduce rotatable bonds by making some bonds rigid
            # This is a simplified approach and might not always work perfectly
            # For a more robust solution, one might need to identify specific bonds
            # to make rigid based on chemical knowledge or more advanced algorithms.
            # Here, we'll just try to set a conformation and hope it reduces flexibility.
            # A more direct way to reduce rotatable bonds is to modify the molecule itself,
            # e.g., by adding rings or making single bonds into double bonds, which is
            # beyond the scope of a simple script.
            # For docking, often the number of rotatable bonds is limited by the software
            # or by pre-processing steps that fix certain conformations.
            # For now, we'll just print a warning and proceed, as RDKit's primary
            # function is not to *reduce* rotatable bonds in the sense of chemical modification,
            # but to *count* them and generate conformations.
            print(f"Warning: Molecule has {num_rotatable_bonds} rotatable bonds, which is > {max_rotatable_bonds}. Proceeding without chemical modification to reduce them.")
        
        writer.write(mol)
    writer.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reduce rotatable bonds in a ligand (simplified approach).")
    parser.add_argument("--input", required=True, help="Input SDF file path.")
    parser.add_argument("--output", required=True, help="Output SDF file path.")
    parser.add_argument("--max_rotatable_bonds", type=int, default=6,
                        help="Maximum number of rotatable bonds allowed. (Note: This script does not chemically modify the molecule to reduce bonds, but can be extended).")
    args = parser.parse_args()

    reduce_rotatable_bonds(args.input, args.output, args.max_rotatable_bonds)
