from itertools import groupby
import importlib

def omx_default_input_str(structure, moment_type, moments):

    struct_dict = {}
    # interface different structure dicts for compatibility
    struct_dict['lattice'] = structure['lattice_matrix']
    species = structure['species']
    struct_dict['element'] = species
    struct_dict['comment'] = 'Awesome converter'
    struct_dict['direct'] = False # always false because cart_coord
    struct_dict['atom_counts']=[len(list(group)) for key, group in groupby(species)]

    positions = []
    for element, pos in zip(structure['species'],structure['cart_coords']):
        positions.append((element, pos))
    struct_dict['positions'] = positions

    # allocate a full list for moments
    print(f'moment type:{moment_type}')
    if moment_type == 'noncollinear':
        moments_assigned = moments['spherical']
    else:
        moments_assigned = moments['cartesian'] # collinear, only the first column will be used

    # create a place holder for moments
    moment_list = [[0,0,0] for i in range(len(positions))]
    # populated the assigned sites
    for atom_idx in moments_assigned.keys():
        moment_list[int(atom_idx)] = moments_assigned[atom_idx]

    # ******************************************************
    #     parameters (will take input somewhere else)
    # ******************************************************
    param = {}
    param['pol'] = 'nc' if moment_type == 'noncollinear' else 'on'
    param['basis_ver'] = '19'
    param['output'] = 'input_omx.dat'
    param['magmom'] = moment_list # default: None. For nc: (|mag|, theta, phi)

    # Default values: need to be assigned
    param['xc'] = 'GGA-PBE'
    param['band'] = 'off'
    param['element_order'] = None 
    param['basis_prec'] = 'Standard'
    param['coord_system'] = 'F'
    param['basis'] = None 

    libp2o_exists = importlib.util.find_spec('poscar2openmx') is not None
    if libp2o_exists:
        from poscar2openmx.io.write_openmx_str import write_openmx_str
        omx_input_str = write_openmx_str(struct_dict, param)

    return omx_input_str
