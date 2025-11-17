import numpy as np

def simple_poscar_parser(file_content):
    """A lightweight POSCAR parser that returns a SimpleStructure object."""
    lines = file_content.split('\n')

    scaling_factor = float(lines[1])

    lattice_matrix = np.array([list(map(float, line.split())) for line in lines[2:5]])
    lattice_matrix *= scaling_factor

    elements = lines[5].split()
    counts = list(map(int, lines[6].split()))

    species = []
    for el, count in zip(elements, counts):
        species.extend([el] * count)

    num_atoms = sum(counts)
    coord_type = lines[7].strip().lower()

    coords = np.array([list(map(float, line.split())) for line in lines[8:8+num_atoms]])

    is_cartesian = coord_type.startswith('c') or coord_type.startswith('k')

    return lattice_matrix, species, coords, is_cartesian
