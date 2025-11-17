import numpy as np
from dash import Input, Output, State, no_update
from dash import dcc, html
from ..input_parsers.parser_wraper import input_parser
from ..utils.coordinate_transform import cartesian_to_spherical, spherical_to_cartesian
from ..utils.format_magmom_vasp import parse_magmom_string, generate_magmom_string
from ..input_creators.omx_parameter_setup import omx_default_input_str


def register_file_io_callbacks(app):
    """Registers all callbacks for the Dash app."""

    @app.callback(
        Output('structure-store', 'data'),
        Output('species-checklist', 'options'),
        Output('species-checklist', 'value'),
        Output('moments-store', 'data', allow_duplicate=True),
        Output('selected-atoms-store', 'data', allow_duplicate=True),
        Output('natoms-store','data'),
        Output('magnetism-type','value'),
        Output('input-str','data'), # input poscar or *.dat as a string object
        Output('is-omx','data'),
        Input('upload-input', 'contents'),
        prevent_initial_call=True
    )
    def upload_and_store_structure(contents):

        if contents:
            crystal_data = input_parser(contents)

            structure    = crystal_data['structure']
            magmom       = crystal_data['moments']
            n_valence    = crystal_data['valence']
            data         = crystal_data['parameter_data']
            file_content = crystal_data['file_str']

            if '<Atoms.SpeciesAndCoordinates' in file_content:
                print("It's an OpenMX input add option to keep parameters")
                is_omx = True
            else:
                is_omx = False

            moments_data = {'cartesian':{},'spherical':{}}
            # populate the moment dict with existing magmom
            if magmom is not None:
                moments_data['cartesian'] = {str(i): spin for i, spin in enumerate(magmom)}
                moments_data['spherical'] = {str(i): cartesian_to_spherical(spin) for i, spin in enumerate(magmom)}

            if structure:
                species = sorted(list(structure.symbol_set))
                options = [{'label': s, 'value': s} for s in species]
                natoms = len(structure)
                mag_type = 'noncollinear' if data and data.get('spin_pol', '').lower() == 'nc' else 'collinear'

                return structure.as_dict(), options, species, moments_data, [], natoms, mag_type, file_content, is_omx

        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update


    # If omx format detected, display the option for keeping original parameters
    @app.callback(
        Output('keep-omx-parameter-container', 'children'),
        Input('is-omx', 'data'),
    )
    def check_keep_omx(is_omx):
        keep_omx_option = {'display': 'block','marginLeft':'10px'} if is_omx == True else {'display': 'none'}
        return html.Div(
            style=keep_omx_option,
            children=[
                html.Div([
                    html.Button('OpenMX (Only Modify input moments)', 
                                id='generate-openmx-button2', n_clicks=0, 
                                style={'marginLeft': '10px'}),
                    dcc.Download(id="download-openmx-input2")
                ], style={'marginTop': '10px'}),
            ])


    @app.callback(
        Output('magmom-output', 'value'),
        Input('generate-magmom-button', 'n_clicks'),
        State('natoms-store', 'data'),
        State('moments-store', 'data'), 
        State('magnetism-type', 'value'),
        prevent_initial_call=True
    )
    def generate_and_display_magmom(n_clicks, natoms, moments_data, mag_type):
        is_collinear = mag_type == 'collinear'
        return generate_magmom_string(natoms, moments_data['cartesian'], is_collinear)


    # Reading magmom strings
    @app.callback(
        Output('moments-store', 'data', allow_duplicate=True),
        Output('magnetism-type', 'value', allow_duplicate=True),
        Input('update-from-magmom-button', 'n_clicks'),
        State('magmom-input-textarea', 'value'),
        State('natoms-store', 'data'),
        prevent_initial_call=True
    )
    def update_moments_from_string(n_clicks, magmom_str, natoms):
        if not magmom_str or natoms == 0:
            return no_update
        try:
            # Parse the string and update the moments-store
            new_moments = {'cartesian':{}, 'spherical':{}}
            moments_in, mag_type = parse_magmom_string(magmom_str, natoms)
            print(f'MAGMOM string is {mag_type}')

            new_moments['cartesian'] = moments_in
            new_moments['spherical'] = {str(i): cartesian_to_spherical(moments_in[i]) for i in moments_in}
            return new_moments, mag_type
        except ValueError as e:
            # If parsing fails, print an error to the console and do nothing
            print(f"Error parsing MAGMOM string: {e}")
            return no_update, no_update


    # --- OpneMX Input file Generation ---
    # Option 1 generate omx input using poscar2openmx library
    @app.callback(
        Output("download-openmx-input", "data"),
        Input('generate-openmx-button', 'n_clicks'),
        State('structure-store','data'),
        State('magnetism-type', 'value'),
        State('moments-store', 'data'),
        prevent_initial_call=True
    )
    def generate_openmx_input(n_clicks, structure, moment_type, moments):

        if n_clicks is None or n_clicks == 0:
            return dash.no_update

        # omx_default_input_str calls poscar2openmx if the lib is detected
        omx_input_str = omx_default_input_str(structure, moment_type, moments)
        filename = f"input_omx_str.dat"

        # Use dcc.send_string to serve the content directly to the browser
        return dcc.send_string(
           omx_input_str,
           filename=filename,
           type="text/plain" # Explicitly define the MIME type for text files
        )


    #Option 2 Generate input by modifying original omx *.dat file
    @app.callback(
        Output("download-openmx-input2", "data"),
        Input('generate-openmx-button2', 'n_clicks'),
        State('structure-store','data'),
        State('magnetism-type', 'value'),
        State('moments-store', 'data'),
        State('input-str', 'data'),
        prevent_initial_call=True
    )
    def modify_omx_input_moments(n_clicks, structure, moment_type, moments, openmx_input_content):
        from ..input_creators.modify_openmx_moments import modify_openmx_spins
        import re

        if n_clicks is None or n_clicks == 0:
            return dash.no_update

        # initiatalize a full natoms-by-3 moment array as a place holder
        natoms = len(structure['frac_coords'])
        moment_array = np.zeros((natoms,3))

        # populate moment array with assigned spin moments
        new_moment_dict = moments['cartesian']
        for k in new_moment_dict.keys():
            moment_array[int(k),:] = new_moment_dict[k]

        # Identify whether frac or cart coordinates
        pattern = r"^(?!#)\s*Atoms\.SpeciesAndCoordinates\.Unit\s+(\S+)"
        match = re.search(pattern, openmx_input_content, re.MULTILINE)
        if match:
            result = match.group(1)
            print(f"The extracted unit is: **{result}**")
            if result.lower()=='frac':
                print('input is in frac')
                coords = structure['frac_coords']
            elif result.lower()=='ang':
                print('in put is in ang')
                coords = structure['cart_coords']
            else:
                raise CustomError("Atoms.SpeciesAndCoordinates.Unit should be either frac or Ang")
        else:
            print("can't find coordinate system type: choose frac or cart")

        is_noncollinear = True if moment_type.lower() =='noncollinear' else False
        # modity the moments in the original *.dat input
        modified_content = modify_openmx_spins(openmx_input_content,
                                               moment_array, 
                                               is_noncollinear, coords)
        filename = f"input_omx_str.dat"

        # Use dcc.send_string to serve the content directly to the browser
        return dcc.send_string(
           modified_content,
           filename=filename,
           type="text/plain" # Explicitly define the MIME type for text files
        )
