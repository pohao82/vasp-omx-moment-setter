import math
import numpy as np
from ..utils.string_utils import find_start_by_char_transition
from ..utils.coordinate_transform import cartesian_to_spherical


def modify_openmx_spins(input_file_content, new_spin_moments, is_noncollinear, coord_orig=None):
    """
    Modifies the Spin moment initialization fields in the OpenMX input file content.

    Args:
        input_file_content (str): The entire content of the OpenMX input file.
        new_spin_moments (list of lists or np.ndarray): An N-by-3 array of (Mx, My, Mz) 
                                                       for N atoms.

    Returns:
        str: The modified content of the input file.
    """
    lines = input_file_content.splitlines('\n')
    modified_lines = []
    in_coords_block = False
    atom_count = 0
    start_tag = '<Atoms.SpeciesAndCoordinates'
    end_tag = 'Atoms.SpeciesAndCoordinates>'

    # Ensure the spin array has the correct number of atoms
    lines_check = input_file_content.splitlines()
    try:
        # This line attempts to find the Atoms.Number entry and extract the count
        atom_number_line = next(line for line in lines_check if line.strip().startswith('Atoms.Number'))
        N_atoms_in_file = int(atom_number_line.split()[-1].replace('-', ''))
    except (StopIteration, ValueError, IndexError):
        print(f"Warning: Could not reliably parse 'Atoms.Number'. Assuming N={N_atoms_in_file}.")

    if N_atoms_in_file != len(new_spin_moments):
        raise ValueError(f"Number of spin moments provided ({len(new_spin_moments)}) must match "
                         f"Atoms.Number in file ({N_atoms_in_file}).")

    print(f"Applying new {N_atoms_in_file} spin moments to {len(new_spin_moments)} atoms...")

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith(start_tag):
            in_coords_block = True
            modified_lines.append(line)
            continue

        if stripped_line.startswith(end_tag):
            in_coords_block = False
            modified_lines.append(line)
            continue

        if in_coords_block and stripped_line:
            line = line.rstrip('\n').split('#')[0] # remove comments
            parts = line.split()
            nparts = len(parts)

            # parts[5] and parts[6] are spin up and down elect
            n_valence = float(parts[5])+float(parts[6])

            # reorder the moments
            if coord_orig is not None:
                coord_new = [float(part) for part in parts[2:5]]
                # This uses broadcasting to subtract the target from every row
                differences = np.array(coord_orig) - np.array(coord_new)
                # Square the differences and sum them along each row (axis=1)
                dist2 = np.sum(differences**2, axis=1)
                # Find the index of the smallest distance
                closest_index = np.argmin(dist2)
                Mx, My, Mz = new_spin_moments[closest_index]
            else:
                # 1. Get the new Cartesian moments for the current atom
                Mx, My, Mz = new_spin_moments[atom_count]

            # 2. Convert to spherical coordinates
            if is_noncollinear:
                [mag, Theta, Phi] = cartesian_to_spherical([Mx,My,Mz])
            else:
                mag = Mx 

            s_up = 0.5*(n_valence + mag)
            s_dn = 0.5*(n_valence + mag) - mag

            # Find where coord_z ends or where s_up begins
            start_index = find_start_by_char_transition(line, 6) 
            #start_index=52
            prefix = line[:start_index]

            if is_noncollinear:
                # constrain and orbital moment enhancing flag
                start_flag = find_start_by_char_transition(line, 12) 
                if nparts >10: # keep the original flag
                    additiona_flag = line[start_flag:].rstrip('\n')
                else: # collinear add flag
                    additiona_flag = '1 on'

                new_spin_block_aligned = (
                    f"  {s_up:5.2f}  {s_dn:5.2f}" # 
                    f" {Theta:7.2f} {Phi:7.2f}" # Spin angles
                    f" {Theta:7.2f} {Phi:7.2f}" # Orbital angles (initial guess same as spin)
                    f"  {additiona_flag}"
                )
            else: # collinear 
                new_spin_block_aligned = (
                    f"  {s_up:5.2f} {s_dn:5.2f}" # 
                )

            # Reconstruct the full line
            new_line = prefix + new_spin_block_aligned + '\n'
            atom_count += 1
            modified_lines.append(new_line)

        else: # everything other than coorindates
            # Append lines outside the block
            if 'scf.SpinPolarization' in line:
                if is_noncollinear:
                    line = 'scf.SpinPolarization       nc  # On|Off|NC\n'
                else:
                    line = 'scf.SpinPolarization       on  # On|Off|NC\n'

            modified_lines.append(line)

    return "".join(modified_lines)


#@ 1. New Spin Moments Array (N-by-3 array, N=20 in this example)
#new_moments = np.array([
#    [1.0, 1.0, 1.0],  # V 1: +X direction
#    [0.0, 1.0, 0.0],  # V 2: +Y direction
#    [-1.0, 0.0, 0.0], # V 3: -X direction
#    [0.0, -1.0, 0.0], # V 4: -Y direction
#    [0.0, 0.0, 1.0],  # V 5: +Z direction
#    [0.0, 0.0, -1.0], # V 6: -Z direction
#    [0.5, 0.5, 0.0],  # V 7: XY plane
#    [0.0, 0.0, 0.0],  # V 8: Zero moment
#    [0.0, 0.0, 0.0],  # O 9: Zero moment
#    [0.0, 0.0, 0.0],   # O 10: Zero moment
#    [1.0, 0.0, 0.0],  # V 1: +X direction
#    [0.0, 1.0, 0.0],  # V 2: +Y direction
#    [-1.0, 0.0, 0.0], # V 3: -X direction
#    [0.0, -1.0, 0.0], # V 4: -Y direction
#    [0.0, 0.0, 1.0],  # V 5: +Z direction
#    [0.0, 0.0, -1.0], # V 6: -Z direction
#    [0.5, 0.5, 0.0],  # V 7: XY plane
#    [0.0, 0.0, 0.0],  # V 8: Zero moment
#    [0.0, 0.0, 0.0],  # O 9: Zero moment
#    [0.0, 0.0, 0.0]   # O 10: Zero moment
#])
#
#input_omx = 'input_omx.dat'
#with open(input_omx, 'r') as f:
#    openmx_input_content = f.readlines()
#
## 3. Modify the file content
#modified_content = modify_openmx_spins(openmx_input_content, new_moments, is_noncollinear=False)
#
## 4. Save the modified content to a new file (optional, but useful for testing)
#output_filepath = "openmx_input_nc.dat"
#try:
#    with open(output_filepath, "w") as f:
#        f.write(modified_content)
#    print(f"\nSuccessfully generated and saved modified file to '{output_filepath}'.")
#except Exception as e:
#    print(f"\nCould not write file: {e}")
#
#print("\n--- Modified OpenMX Content ---")
##print(modified_content)
#
