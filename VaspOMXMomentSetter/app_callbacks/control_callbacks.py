from dash import Input, Output, State, no_update
from dash import dcc, html
#import pprint
from ..utils.string_utils import parse_selection_string
from ..utils.coordinate_transform import cartesian_to_spherical, rotate_vector, spherical_to_cartesian


def register_control_callbacks(app):

    # Interactive panel section
    @app.callback(
        Output('moment-input-container', 'children'),
        Input('magnetism-type', 'value'),
    )
    def update_input_panel(mag_type):
        # Determine the style for non-collinear inputs
        non_collinear_style = {'visibility': 'visible','marginLeft':'10px'} if mag_type == 'noncollinear' else {'visibility': 'hidden'}
        moment_disp = "|M|:" if mag_type == 'noncollinear' else [html.B('M'),html.Label(' :')]

        return html.Div(
            style={'display': 'flex', 'alignItems': 'center', 'width': '100%'}, # This is the parent container
            children=[
                html.Div([
                    html.Label(moment_disp),
                    dcc.Input(id='moment-mag-in', type='number', value=0.0, style={'width': '50px'})
                ]),
                html.Div(style=non_collinear_style, children=[
                    html.Label("θ:"),
                    dcc.Input(id='moment-theta-in', type='number', value=0.0, style={'width': '45px'}),
                    html.Label(" φ:"),
                    dcc.Input(id='moment-phi-in', type='number', value=0.0, style={'width': '35px'}),
                ]),
        ])


    @app.callback(
        Output('moment-rot-input-container', 'children'),
        Input('magnetism-type', 'value'),
        Input('moment-rotate-check', 'value'),
    )
    def update_input_panel_rot(mag_type, mag_rot_check):
        if mag_rot_check: 
            is_checked = True # show the Div
        else:
            is_checked = False # hide the Div

        # Whether to show input area for moment rotation
        non_collinear_style = {'display': 'block'} if mag_type == 'noncollinear' and is_checked==True else {'display': 'none'}

        return html.Div([
            html.Div(style=non_collinear_style, children=[
                html.Label("θ:"),
                dcc.Input(id='rotation-theta-input', type='number', value=0.0, style={'width': '40px'}),
                html.Label("φ:", style={'marginLeft': '10px'}),
                dcc.Input(id='rotation-phi-input', type='number', value=0.0, style={'width': '40px'}),
                html.Button('Apply Rotation', id='rotate-moments-button', n_clicks=0 ),
            ]),
        ])


    @app.callback(
        Output('moments-store', 'data', allow_duplicate=True),
        Output('selected-atoms-store', 'data', allow_duplicate=True),
        Output('text-selection-input', 'value'), # Output [] to clear the text box
        Input('update-moment-button', 'n_clicks'),
        State('magnetism-type', 'value'),
        State('selected-atoms-store', 'data'), # From clicking
        State('text-selection-input', 'value'),  # From text input
        State('moment-mag-in', 'value'),
        State('moment-theta-in', 'value'),
        State('moment-phi-in', 'value'),
        State('moments-store', 'data'),
        State('natoms-store', 'data'), # Total number of atoms
        prevent_initial_call=True
    )
    def set_or_update_moment(n_clicks, mag_type, clicked_atoms, text_selection,
                             mag, theta, phi, current_moments, natoms):
        if mag is None or natoms is None:
            return no_update, no_update, no_update

        atoms_to_modify = []
        # Prioritize text input for selection
        if text_selection:
            try:
                atoms_to_modify = parse_selection_string(text_selection, natoms)
                atoms_to_modify = [atom-1 for atom in atoms_to_modify]

            except (ValueError, TypeError) as e:
                print(f"Error parsing selection string: {e}")
                return no_update, no_update, no_update # Stop if parsing fails

        # Fallback to click selection if text box is empty
        elif clicked_atoms:
            atoms_to_modify = clicked_atoms

        if not atoms_to_modify:
            return no_update, no_update, no_update # do nothing

        # apply specified moments to the selected sites
        if mag_type == 'collinear':
            moment_vec = [mag, 0.0, 0.0]
            ang = 180 if mag<0 else 0
            moment_sph = [abs(mag),ang,0.0]
        else: # noncollinear
            if theta is None or phi is None: return no_update, no_update, no_update
            moment_sph = [mag, theta, phi]
            moment_vec = spherical_to_cartesian(mag, theta, phi)

        for atom_idx in atoms_to_modify:
            current_moments['cartesian'][str(atom_idx)] = moment_vec
            current_moments['spherical'][str(atom_idx)] = moment_sph

        # Return updated moments, and clear both click and text selections
        return current_moments, [], ''


    # rotate moments, similar to set moments
    @app.callback(
        Output('moments-store', 'data', allow_duplicate=True),
        Input('rotate-moments-button', 'n_clicks'),
        State('moments-store', 'data'),
        State('selected-atoms-store', 'data'),
        State('text-selection-input', 'value'),
        State('natoms-store', 'data'),
        State('rotation-theta-input', 'value'),
        State('rotation-phi-input', 'value'),
        prevent_initial_call=True
    )
    def rotate_selected_moments(n_clicks, current_moments, clicked_atoms, 
                                text_selection, natoms, theta, phi):
        if not current_moments or (theta is None or phi is None):
            return no_update

        # Determine which atoms are selected (priority to text input)
        atoms_to_modify = []
        if text_selection:
            try:
                atoms_to_modify = parse_selection_string(text_selection, natoms)
                atoms_to_modify = [atom-1 for atom in atoms_to_modify]
            except (ValueError, TypeError):
                return no_update
        elif clicked_atoms:
            atoms_to_modify = clicked_atoms

        if not atoms_to_modify:
            return no_update # No atoms selected to rotate

        # Loop through selected atoms and apply rotation
        for atom_idx in atoms_to_modify:
            idx_str = str(atom_idx)
            # Get the current moment, default to [0,0,0] if not set
            current_vec = current_moments['cartesian'].get(idx_str, [0.0, 0.0, 0.0])
            # Rotated moment
            new_vec = rotate_vector(current_vec, theta, phi)
            # Update the dictionary
            current_moments['cartesian'][idx_str] = new_vec
            current_moments['spherical'][idx_str] = cartesian_to_spherical(new_vec)

        return current_moments


    @app.callback(
        Output('moments-store', 'data', allow_duplicate=True),
        Input('reset-moments-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def reset_all_moments(n_clicks):
        """ Clears all stored magnetic moments. """
        return {'cartesian':{},'spherical':{}} # Return an empty dictionary
