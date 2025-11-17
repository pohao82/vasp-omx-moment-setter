import numpy as np

def unitcell_edges(lattice):
    o = np.array([0, 0, 0])
    a, b, c = lattice[0], lattice[1], lattice[2]

    # Define the 8 corners of the unit cell
    corners = [
        o, a, b, c,
        a + b, a + c, b + c,
        a + b + c
    ]

    # Define the 12 edges by connecting corner indices
    edges = [
        (0, 1), (0, 2), (0, 3), # Edges from origin
        (1, 4), (1, 5),         # Edges from corner 'a'
        (2, 4), (2, 6),         # Edges from corner 'b'
        (3, 5), (3, 6),         # Edges from corner 'c'
        (4, 7), (5, 7), (6, 7)  # Edges to corner 'a+b+c'
    ]

    # Create lists of coordinates for the lines, separated by None
    cell_x, cell_y, cell_z = [], [], []
    for start_idx, end_idx in edges:
        p1 = corners[start_idx]
        p2 = corners[end_idx]
        cell_x.extend([p1[0], p2[0], None])
        cell_y.extend([p1[1], p2[1], None])
        cell_z.extend([p1[2], p2[2], None])

    return (cell_x, cell_y, cell_z)
