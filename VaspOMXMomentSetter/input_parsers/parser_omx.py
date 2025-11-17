import sys
import os
import numpy as np # Used for spin vector calculations if needed

# --- Helper Functions ---
def remove_after_hash(text):
  index = text.find('#')
  if index != -1:
    return text[:index]
  return text

def parse_vector_line(line):
    """Parses a line containing 3 float values."""
    try:
        return [float(x) for x in line.split()[:3]]
    except (ValueError, IndexError):
        return None

def parse_atom_line_openmx(line, species_map):
    """
    Parses a line from the OpenMX Atoms.SpeciesAndNotations block.
    Format expected: AtomNumber Species X Y Z [Nup] [Ndn] [spin_theta] [spin_phi] ...
    Returns: species, position (list), initial_spin (list or None)
    """
    line=remove_after_hash(line)
    parts = line.split()
    if len(parts) < 5:
        return None, None, None

    atom_num = int(parts[0])
    species = parts[1]
    pos = [float(parts[2]), float(parts[3]), float(parts[4])]

    # col 
    # 5: Eup  6: Edn
    # noncol
    # 5: Eup 6: Edn  7 theta  8 phi

    # extract initial spin information
    n_up = float(parts[5])
    n_dn = float(parts[6])
    n_valence = n_up + n_dn
    spin_mag = n_up - n_dn

    initial_spin = None
    if len(parts) >= 12:
        try:
            spin_theta_deg = float(parts[7])
            spin_phi_deg = float(parts[8])

            # Convert spherical to Cartesian for VASP non-collinear MAGMOM
            spin_theta_rad = np.radians(spin_theta_deg)
            spin_phi_rad = np.radians(spin_phi_deg)

            sx = spin_mag * np.sin(spin_theta_rad) * np.cos(spin_phi_rad)
            sy = spin_mag * np.sin(spin_theta_rad) * np.sin(spin_phi_rad)
            sz = spin_mag * np.cos(spin_theta_rad)
            initial_spin = [sx, sy, sz]
        except ValueError:
            # If conversion fails, maybe it's just collinear spin magnitude
            try:
                collinear_spin_mag = spin_mag # Check typical position for collinear
                initial_spin = [collinear_spin_mag, 0.0, 0.0] # Store as z-component
            except (ValueError, IndexError):
                initial_spin = None # No spin info found or format mismatch
    elif len(parts) <=8 : # Potentially collinear spin magnitude only
         try:
            collinear_spin_mag = spin_mag
            initial_spin = [collinear_spin_mag, 0.0, 0.0] # Store as z-component
         except ValueError:
             initial_spin = None

    # Add species to map if new
    if species not in species_map:
        species_map[species] = {'count': 0, 'atoms': [], 'ldau': None} # Initialize LDAU info

    species_map[species]['count'] += 1
    species_map[species]['atoms'].append({'pos': pos, 
                                          'initial_spin': initial_spin, 
                                          'n_valence': n_valence})

    return species, pos, initial_spin, n_valence

def parse_ldau_openmx(u_line):
    """
    """
    ldau_definitions = {}

    u_parts = u_line.split()
    # Find nonzero U_value
    for k, element in enumerate(u_parts):
        # Try to convert the element to float
        try:
            value = float(element)
            # Check if the value is nonzero
            if value != 0.0:
                # Print the index, value, and previous element (which is typically the orbital)
                spec = u_parts[0]
                orb = u_parts[k-1]
                u_val = value
                print(f"Nonzero value found at index {k}: {element}")
                print(f"The corresponding orbital is: {u_parts[k-1]}")
                print(f"The pair is: {u_parts[k-1]} {element}")
                data['hubbard_values'][spec] = {'U': u_val,'orbital':orb}
        except ValueError:
            # If the element can't be converted to float, it's not a number
            continue

    return ldau_definitions # Needs implementation based on OpenMX U format


def map_xc_functional(openmx_xc):
    """Maps OpenMX XC functional name to VASP INCAR tags."""
    omx_xc = openmx_xc.lower()
    if 'pbe' in omx_xc:
        return {'GGA': 'PE'}
    elif 'lda' in omx_xc: # Might need more specific LDA checks (e.g., 'CA-PZ')
        return {'LDAU_LUA': '.FALSE.'} # Placeholder for LDA, VASP default is LDA if no GGA tag
    #elif 'scan' in omx_xc:
    #     return {'METAGGA': 'SCAN'}
    # Add more mappings as needed
    else:
        print(f"Warning: Unknown XC functional '{openmx_xc}'. Using PBE as default.")
        return {'GGA': 'PE'} # Default to PBE

def map_orbital_to_l(orbital_char):
    """Maps orbital character (s, p, d, f) to VASP LDAUL value."""
    mapping = {'s': 0, 'p': 1, 'd': 2, 'f': 3}
    return mapping.get(orbital_char.lower(), -1) # Return -1 for unknown/no U

# --- Main Parsing Logic ---
def parse_openmx_dat(file_content):
    """Parses the OpenMX .dat file and extracts relevant information."""
    data = {
        #'system_name': os.path.splitext(os.path.basename(filepath))[0],
        'system_name': 'system_name',
        'lattice_vectors': [],
        'species_map': {}, # { 'Species': {'count': N, 'atoms': [{'pos':[], 'initial_spin':[]}, ...], 'ldau': {'L':val,'U':val,'J':val or None} }, ... }
        'kgrid': None,
        'spin_pol': 'off', # 'off', 'on', 'nc'
        'energy_cutoff': None, # in eV
        'xc_type': 'GGA-PBE', # Default
        'scf_criterion': 1.0e-7, # Default
        'hubbard_u': 'off', # 'on' or 'off'
        'hubbard_values': {}, # Store parsed U values {'Species': {'orbital':{'U':val, 'J':val}}}
        'spin_constraints': [] # Store constraints if found
    }
    species_order_in_block = [] # Track the order species appear in Atoms.SpeciesAndNotations

    lines = file_content.split('\n')

    i = 0
    # iterate through lines
    while i < len(lines):
        line = remove_after_hash(lines[i]).strip()
        # skip comment and empty lines
        if not line or line.startswith('#') or line.startswith(';'):
            i += 1
            continue

        parts = line.split(None, 1) # Split only on the first whitespace
        keyword = parts[0].lower()

        # --- System Name (Optional, use filename if not found) ---
        if keyword == 'system.name':
            if len(parts) > 1:
                data['system_name'] = parts[1].strip()

        # --- Lattice Vectors ---
        elif keyword == 'atoms.unitvectors.unit':
            if len(parts) > 1 and parts[1].strip().lower() == 'ang': # VASP uses Angstrom
                 unit_conversion = 1.0
            else: # Assume Bohr if not Angstrom specified explicitly
                 unit_conversion = 0.529177210903 # Bohr to Angstrom
                 print("Warning: Assuming Bohr units for lattice vectors. Converting to Angstrom for POSCAR.")

            i += 1

            if i + 3 < len(lines):
                for j in range(1, 4):
                    vec = parse_vector_line(lines[i+j])
                    if vec:
                        data['lattice_vectors'].append([v * unit_conversion for v in vec])
                    else:
                        print(f"Warning: Could not parse lattice vector line: {lines[i+j].strip()}")
                i += 3 # Skip the vector lines
            else:
                 print("Warning: Found 'atoms.unitvectors' but not enough lines following for vectors.")

        # --- Species and Atoms ---
        elif keyword == '<atoms.speciesandcoordinates':
            i += 1
            while i < len(lines):
                atom_line = lines[i].strip()
                if atom_line.lower() == 'atoms.speciesandcoordinates>':
                    break
                species, pos, initial_spin, n_valence = parse_atom_line_openmx(atom_line, data['species_map'])
                if species and species not in species_order_in_block:
                    species_order_in_block.append(species)
                # Store atom data handled within parse_atom_line_openmx
                i += 1
        elif keyword == 'atoms.speciesandcoordinates.unit':
            # Correct loop increment is handled inside the while loop
            if len(parts) > 1:
                data['coord_type'] = parts[1].strip()
                print(f"read in coordinate type {data['coord_type']}")

        # --- K-point Grid ---
        elif keyword == 'scf.kgrid':
            if len(parts) > 1:
                kpts = parts[1].split()
                if len(kpts) >= 3:
                    try:
                        data['kgrid'] = [int(k) for k in kpts[:3]]
                    except ValueError:
                        print(f"Warning: Could not parse kgrid values: {parts[1]}")
                else:
                     print(f"Warning: Not enough values for kgrid: {parts[1]}")

        # --- Spin Polarization ---
        elif keyword == 'scf.spinpolarization':
            if len(parts) > 1:
                spin_setting = parts[1].lower()
                if spin_setting == 'on':
                    data['spin_pol'] = 'on'
                elif spin_setting == 'off':
                    data['spin_pol'] = 'off'
                elif spin_setting == 'nc':
                    data['spin_pol'] = 'nc'
                else:
                    print(f"Warning: Unknown scf.SpinPolarization setting: {parts[1]}. Assuming 'off'.")

        # --- Energy Cutoff ---
        elif keyword == 'scf.energycutoff': # Typically in Hartree in OpenMX
            if len(parts) > 1:
                try:
                    # Convert Hartree to eV for VASP ENCUT
                    data['energy_cutoff'] = float(parts[1]) #* 27.211386245988
                except ValueError:
                    print(f"Warning: Could not parse energy cutoff value: {parts[1]}")

        # --- XC Functional ---
        elif keyword == 'scf.xctype':
            if len(parts) > 1:
                data['xc_type'] = parts[1].strip()

        # --- Convergence Criterion ---
        elif keyword == 'scf.criterion': # Energy convergence
            if len(parts) > 1:
                try:
                    data['scf_criterion'] = float(parts[1])
                except ValueError:
                    print(f"Warning: Could not parse scf criterion value: {parts[1]}")

        # --- Hubbard U ---
        elif keyword == 'scf.hubbard.u':
            if len(parts) > 1 and parts[1].lower() == 'on':
                data['hubbard_u'] = 'on'

        # --- Hubbard U Values (Example parsing, adjust to your format) ---
        elif keyword == '<hubbard.u.values':
            i += 1
            u_lines = []
            while i < len(lines): #keep reading until the end
                u_line = lines[i].strip()
                if u_line.lower() == 'hubbard.u.values>':
                    break

                u_parts = u_line.split()
                u_lines.append(lines[i]) 
                # Find nonzero U_value
                for k, element in enumerate(u_parts):
                    # Try to convert the element to float
                    try:
                        value = float(element)
                        # Check if the value is nonzero
                        if value != 0.0:
                            spec = u_parts[0]
                            orb = u_parts[k-1]
                            u_val = value
                            print(f"Nonzero value found at index {k}: {element}")
                            print(f"The corresponding orbital is: {u_parts[k-1]}")
                            print(f"The pair is: {u_parts[k-1]} {element}")
                            # add J as a place holder to be filled in if exist
                            if spec not in data['hubbard_values']: 
                               data['hubbard_values'][spec] = {'U': u_val,'orbital':orb,'J':0}
                            else:
                               data['hubbard_values'][spec]['U'] = u_val

                    except ValueError:
                        # If the element can't be converted to float, it's not a number
                        continue

                #    except ValueError:
                #        print(f"Warning: Could not parse Hubbard U values line: {u_line}")
                #else:
                #    print(f"Warning: Skipping invalid Hubbard U values line: {u_line}")
                i += 1 

            # Correct loop increment handled inside
            nspecies = len(u_lines)

        elif keyword == '<hubbard.j.values':
            i += 1
            u_lines = []
            while i < len(lines): #keep reading until the end
                u_line = lines[i].strip()
                if u_line.lower() == 'hubbard.j.values>':
                    break

                u_parts = u_line.split()
                u_lines.append(lines[i]) 
                # Find nonzero U_value
                for k, element in enumerate(u_parts):
                    # Try to convert the element to float
                    try:
                        value = float(element)
                        # Check if the value is nonzero
                        if value != 0.0:
                            spec = u_parts[0]
                            orb = u_parts[k-1]
                            j_val = value
                            print(f"Nonzero value found at index {k}: {element}")
                            print(f"The corresponding orbital is: {u_parts[k-1]}")
                            print(f"The pair is: {u_parts[k-1]} {element}")
                            # assume U and J are the same shell
                            if spec not in data['hubbard_values']: 
                                data['hubbard_values'][spec] = {'U': 0,'orbital':orb,'J':j_val}
                            else: 
                                data['hubbard_values'][spec]['J'] = j_val

                    except ValueError:
                        # If the element can't be converted to float, it's not a number
                        continue

                i += 1 

            # Correct loop increment handled inside
            #print(u_lines)
            if data['hubbard_values']:
                print('hubbard_values')
                data['hubbard_values']

        i += 1 # this one leavs closing tag hubbard.u.values>


    # --- Post-processing: Assign LDAU values to species_map based on hubbard_values ---
    if data['hubbard_u'] == 'on' and data['hubbard_values']:
        for species_name, hubbard_data in data['hubbard_values'].items():
            if species_name in data['species_map']:
                first_orb = next(iter(hubbard_data)) # Get the first orbital key ('d', 'f', etc.)
                #print(hubbard_data)
                #print(first_orb)
                l_orb = hubbard_data['orbital'][1]
                #print(l_orb)
                l_val = map_orbital_to_l(l_orb)
                if l_val != -1:
                     data['species_map'][species_name]['ldau'] = {
                         'L': l_val,
                         'U': hubbard_data['U'],
                         'J': hubbard_data['J'] 
                     }
                else:
                     print(f"Warning: Could not map orbital '{first_orb}' for species {species_name} to VASP L value.")
            else:
                 print(f"Warning: Hubbard U defined for species '{species_name}' not found in atom list.")

    # Ensure species map uses the order from the atom block for consistency
    ordered_species_map = {spec: data['species_map'][spec] for spec in species_order_in_block if spec in data['species_map']}
    data['species_map'] = ordered_species_map

    return data


# Wrapper converter 
# call parse_openmx_dat to read in *.dat file and conver the output to standardized formmat
def simple_openmx_dat_parser(file_content):

    data = parse_openmx_dat(file_content)

    species_names = list(data['species_map'].keys())
    species_counts = [data['species_map'][s]['count'] for s in species_names]
    total_atoms = sum(species_counts)

    species = []
    for species_type in species_names:
        n_count = data['species_map'][species_type]['count']
        species = species + [species_type]*n_count

    # lattice_vectors
    lattice_matrix = np.array(data['lattice_vectors'])
    # coords 
    atom_count_check = 0
    coords_list = []
    spin_list = []
    valence_list = []
    for species_type in species_names:
        for atom_info in data['species_map'][species_type]['atoms']:
            pos = atom_info['pos']
            coords_list.append(pos)
            mom = atom_info['initial_spin']
            spin_list.append(mom)
            n_val = atom_info['n_valence']
            valence_list.append(n_val)
            atom_count_check += 1

    coords = np.array(coords_list)
    magmom = np.array(spin_list)
    valences = np.array(valence_list)

    coord_type = data['coord_type']
    is_cartesian = not coord_type.lower().startswith('f')

    return lattice_matrix, species, coords, is_cartesian, magmom, valences, data

