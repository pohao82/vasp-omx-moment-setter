import base64
import numpy as np
from VaspOMXMomentSetter.input_parsers.parser_omx import simple_openmx_dat_parser
from VaspOMXMomentSetter.input_parsers.parser_vasp import simple_poscar_parser
#from VaspOMXMomentSetter.input_parsers.parser_class import SimpleStructure

def input_parser(contents):
    """Parses POSCAR content string into a pymatgen Structure object."""
    _content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        #structure = Structure.from_str(decoded.decode('utf-8'), fmt="poscar")
        #return structure
        file_content = decoded.decode('utf-8')
        # find if the coordinates section exists
        if '<Atoms.SpeciesAndCoordinates' in file_content:
            print('Read from OpenMX *.dat input')
            # data stores all omx settings
            lattice_matrix, species, coords, is_cartesian, magmom, n_valence, data = simple_openmx_dat_parser(file_content)
            print(f'spin polarization : {data['spin_pol']}')
            input_type ='omx'
        else:
            print('Read in POSCAR (vasp)')
            lattice_matrix, species, coords, is_cartesian = simple_poscar_parser(file_content)
            magmom = None 
            n_valence = None 
            data = None
            input_type ='poscar'

        # group data
        crystal_data ={
                'structure': SimpleStructure(lattice_matrix, species, coords, coords_are_cartesian=is_cartesian),
                'moments': magmom,
                'valence': n_valence,
                'parameter_data': data,
                'file_str': file_content, # for creating output
                'input_type': input_type
                }
        #return SimpleStructure(lattice_matrix, species, coords, coords_are_cartesian=is_cartesian), magmom, n_valence, data, file_content
        return crystal_data
    except Exception as e:
        print(f"Error parsing input file: {e}")
        return None

class SimpleLattice:
    """A minimal lattice object."""
    def __init__(self, matrix):
        self.matrix = np.array(matrix)

class SimpleSite:
    """A minimal site object with just a species string."""
    def __init__(self, species_string):
        self.species_string = species_string

class SimpleStructure:
    """A pymatgen-free object that mimics the necessary Structure attributes."""
    def __init__(self, lattice_matrix, species, coords, coords_are_cartesian=True):
        self.lattice = SimpleLattice(lattice_matrix)
        self.species = list(species)
        self.sites = [SimpleSite(s) for s in self.species]

        if coords_are_cartesian:
            self.cart_coords = np.array(coords)
            self.frac_coords = np.array(coords) @ np.linalg.inv(self.lattice.matrix)
        else: # Convert from direct to cartesian
            self.cart_coords = np.array(coords) @ self.lattice.matrix
            self.frac_coords = np.array(coords)

        self.symbol_set = sorted(list(set(self.species)))

    def __len__(self):
        return len(self.species)

    def as_dict(self):
        """Serializes the object for dcc.Store."""
        return {
            'lattice_matrix': self.lattice.matrix.tolist(),
            'species': self.species,
            'cart_coords': self.cart_coords.tolist(),
            'frac_coords': self.frac_coords.tolist()
        }

    @classmethod
    def from_dict(cls, d):
        """Deserializes the object from a dictionary."""
        return cls(d['lattice_matrix'], d['species'], d['cart_coords'], d['frac_coords'])

