import numpy as np

# Fromat vasp magmom string: combine zeros etc..
def format_magmom_vasp(values, lnoncollinear=False, tolerance=1e-3):

    formatted_parts = []
    zero_count = 0
    if lnoncollinear:

        mag_vals = np.array(values)
        nvalues = len(values)
        n_sites = nvalues//3
        mag_vals = np.reshape(mag_vals,(n_sites,3))

        for i in range(n_sites):
            row = mag_vals[i,:]
            #print(row)
            if np.all(abs(row) < tolerance):
                zero_count += 3
            else:
                # Process any pending zeros before handling the non-zero value
                if zero_count > 0:
                    formatted_parts.append(f"{zero_count}*0")
                    zero_count = 0 # Reset counter

                row = np.round(row, 6)
                str_arr = ' '.join('0' if abs(x) < 1e-6 else f"{x:.15g}"for x in row)

                formatted_parts.append(str_arr+' ')

        # Handle any trailing zeros after the loop finishes
        if zero_count > 0:
            formatted_parts.append(f"{zero_count}*0")

    # collinear
    else:
        for value in values:
            # Check if the value is effectively zero
            if abs(value) < tolerance:
                zero_count += 1
            else:
                # Process any pending zeros before handling the non-zero value
                if zero_count > 0:
                    if zero_count == 1:
                        formatted_parts.append("0")
                    else:
                        formatted_parts.append(f"{zero_count}*0")
                    zero_count = 0 # Reset counter

                # Format and add the non-zero value
                if abs(value-int(round(value)))<1e-2:
                    formatted_parts.append(f"{value:.0f}")
                else:
                    formatted_parts.append(f"{value:.6f}")

        # Handle any trailing zeros after the loop finishes
        if zero_count > 0:
            if zero_count == 1:
                formatted_parts.append("0")
            else:
                formatted_parts.append(f"{zero_count}*0")

    return " ".join(formatted_parts)

#mag_vals = np.array([1.0, 2.0, 3.0, 0.0, 0.0, 0.0, -1.572891, 0, 0, 0, 0, 0 ,0,0,0, 0, 1, 0, 3, 0, 0, 0,0,0])
#print(f"{mag_vals} -> '{format_magmom_vasp(mag_vals)}'")

def parse_magmom_string(magmom_str, natoms):
    """
    Parses a VASP MAGMOM string into the app's moment dictionary format.
    Handles both collinear (e.g., '2*5.0 2*-5.0') and non-collinear formats.
    """
    # Clean the input string
    s = magmom_str.lower().replace('magmom', '').replace('=', '').strip()
    
    # Expand run-length encoding (e.g., "2*5.0")
    parts = s.split()
    expanded_values = []
    for part in parts:
        if '*' in part:
            count, value = part.split('*')
            expanded_values.extend([float(value)] * int(count))
        else:
            expanded_values.append(float(part))

    # Check if collinear or non-collinear based on the number of values
    if len(expanded_values) == natoms:
        mag_type = 'collinear'
        # Collinear: [m1, m2, ...] -> { '0': [m1,0,0], '1': [m2,0,0], ... }
        moments_dict = {str(i): [val, 0.0, 0.0] for i, val in enumerate(expanded_values)}
    elif len(expanded_values) == 3 * natoms:
        mag_type = 'noncollinear'
        # Non-collinear: [m1x, m1y, m1z, m2x, ...] -> { '0': [m1x,m1y,m1z], ... }
        moments_array = np.array(expanded_values).reshape((natoms, 3))
        moments_dict = {str(i): vec.tolist() for i, vec in enumerate(moments_array)}
    else:
        raise ValueError(f"Invalid number of moments. Expected {natoms} (collinear) "
                         f"or {3*natoms} (non-collinear), but got {len(expanded_values)}.")

    return moments_dict, mag_type


def generate_magmom_string(num_atoms, moments_data, collinear):
    """Generates the VASP MAGMOM string. Convert from moments_data"""

    if collinear:
        lnoncollinear = False
        moments = [0.0] * num_atoms
        for idx_str, moment_vec in moments_data.items():
            moments[int(idx_str)] = moment_vec[0]
        moment_list = moments

    else: # Non-collinear
        lnoncollinear = True
        moments = [[0.0, 0.0, 0.0] for _ in range(num_atoms)]
        for idx_str, moment_vec in moments_data.items():
            moments[int(idx_str)] = moment_vec
        # unroll list
        moment_list = []
        for mom in moments:
            moment_list.extend(mom)

    mom_str = format_magmom_vasp(moment_list, lnoncollinear, tolerance=1e-3)

    return "MAGMOM = " + mom_str
