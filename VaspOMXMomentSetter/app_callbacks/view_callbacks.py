import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, no_update
from dash import dcc, html # Local import to keep layout dependencies minimal
from dash import dash_table # Local import to keep layout dependencies minimal
import time
#import pprint
from ..input_parsers.parser_wraper import SimpleStructure
from ..view.figure_components import structure_to_fig
from ..utils.string_utils import parse_selection_string


def register_view_callbacks(app):
    """Registers all callbacks for the Dash app."""

    # MAIN VIEW
    @app.callback(
        Output('structure-view', 'figure'),
        # inputs
        Input('structure-store', 'data'),
        Input('magnetism-type', 'value'),
        Input('species-checklist', 'value'),
        Input('moments-store', 'data'), # for displaying moments
        Input('selected-atoms-store', 'data'), # currently the yellow marker
        Input('view-options-checklist', 'value'),
        Input('radii-scale', 'value'), # scale atom radii
        Input('arrow-scale', 'value'), # scale vector size
        Input('center-vector-check', 'value'), # center the vector, or attached to the site
        Input('color-dropdown', 'value'), # vector color
        State('camera-store', 'data'), # to make sure update doesn't change camera,
        prevent_initial_call=True 
    )
    def update_structure_view(structure_dict, mag_type, visible_species, moments_data, selected_atoms, 
                         view_options, radii_scale, arrow_scale, center_vec_check, color_dropdown, camera_data):

        # update fig
        if not structure_dict:
            # Also return default values for columns and data
            return go.Figure(), [], []

        # Map color names to RGB [0-1] values
        color_map = {
            'red': [1, 0, 0],
            'green': [0, 1, 0],
            'blue': [0, 0, 1],
            'gray': [0.5, 0.5, 0.5],
            'black': [0, 0, 0]
        }

        vector_rgb = color_map[color_dropdown.lower()]

        structure = SimpleStructure.from_dict(structure_dict)
        moments_cart = moments_data['cartesian']

        center_arrow = 'center' in center_vec_check
        fig = structure_to_fig(structure, visible_species or [], radii_scale, 
                               arrow_scale, center_arrow, vector_rgb, 
                               selected_atoms, moments_cart, view_options)
        if camera_data:
            fig.update_layout(scene_camera=camera_data)

        fig.update_layout(uirevision="keep-camera")

        return fig


    @app.callback(
        Output('moment-table-container', 'children'),
        [Input('magnetism-type', 'value'), # col or noncol
         Input('show-table-check', 'value'), # check to show table
         Input('moments-store', 'data'), # for displaying moments
        ]
    )
    def show_moment_table(mag_type, show_table, moments_data):

        if not moments_data:
            return no_update

        if show_table:
            is_checked = True # show Div
        else:
            is_checked = False # hide Div

        table_style = {'display': 'block'} if is_checked else {'display': 'none'}

        moments_cart = moments_data['cartesian']
        moments_sph  = moments_data['spherical']

        if mag_type == 'collinear':
            col_names = ['atom', 'mx', 'my', 'mz']
            table_columns = [{"name": i, "id": i} for i in col_names]

            table_data = [
                {'atom': str(int(k)+1), 
                 'mx': f"{v[0]:.3f}", 
                 'my': f"{v[1]:.3f}", 
                 'mz': f"{v[2]:.3f}"}
                for k, v in sorted(moments_cart.items(), key=lambda item: int(item[0]))
            ]
        else: # 'noncollinear' case return spherical coordinates as well
            col_names = ['atom', 'mx', 'my', 'mz', 'mag', 'theta', 'phi']
            table_columns = [{"name": i, "id": i} for i in col_names]
            table_data = [
                {'atom': str(int(k)+1),
                 'mx': f"{v[0]:.3f}",
                 'my': f"{v[1]:.3f}",
                 'mz': f"{v[2]:.3f}",
                 'mag'  :f"{moments_sph[k][0]:.3f}",
                 'theta':f"{moments_sph[k][1]:.1f}",
                 'phi'  :f"{moments_sph[k][2]:.1f}"}
                for k, v in sorted(moments_cart.items(), key=lambda item: int(item[0]))
            ]

        return html.Div(style=table_style, children=[
            dash_table.DataTable(
                id='moments-table',
                columns=table_columns,
                data=table_data,
                style_cell={'textAlign': 'left'},
                style_table={
                    'maxHeight': '400px', # how many rows to show
                    'overflowY': 'auto'  # Adds a scrollbar
                }
            )
        ])


    # select atoms from click
    @app.callback(
        Output('selected-atoms-store', 'data'),
        Output('atom-selection-info', 'children'),
        Output('last-click-timestamp-store', 'data'),
        Input('structure-view', 'clickData'),
        State('selected-atoms-store', 'data'),
        State('last-click-timestamp-store', 'data'), 
        prevent_initial_call=True
    )
    def select_atom(clickData, selected_atoms, last_click_time):

        #Debouncing: Check if the click is too recent
        current_time = time.time()
        if (current_time - last_click_time) < 0.3: # 300ms threshold
            return no_update, no_update, no_update # Ignore this click

        # Check if clickData is valid AND if the clicked point has 'customdata'
        if clickData and 'customdata' in clickData['points'][0]:
            atom_index = clickData['points'][0]['customdata']

            # click to deselect
            if atom_index in selected_atoms:
                selected_atoms.remove(atom_index)
            # click to select
            else:
                selected_atoms.append(atom_index)
            selected_atoms.sort()

            if not selected_atoms:
                info_text = "Click on atoms to select/deselect them."
            else:
                atoms_display = [number+1 for number in selected_atoms] 
                info_text = f"Selected Atom Indices: {', '.join(map(str, atoms_display))}"

            # Update the list, info text, and the timestamp of this valid click
            return selected_atoms, info_text, current_time

        return no_update, no_update, no_update


    @app.callback(
        Output('selected-atoms-store', 'data', allow_duplicate=True),
        Output('atom-selection-info', 'children', allow_duplicate=True),
        Output('text-selection-input', 'value', allow_duplicate=True), # Output [] to clear the text box
        Input('deselect-all-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def deselect_all_atoms(n_clicks):
        """
        Clears the list of selected atoms and resets the info text.
        """
        # Return an empty list to clear the selection
        # and the default text for the info panel.
        return [], "Click on atoms to select/deselect them.", ''


    @app.callback(
        Output('camera-store', 'data', allow_duplicate=True),
        Output('structure-view', 'figure', allow_duplicate=True),
        Input('view-angle-radio', 'value'),
        State('structure-view', 'figure'), # Get the current figure
        State('camera-store', 'data'), # camera state
        prevent_initial_call=True
    )
    def set_view_angle(view_type, fig, camera_data):
        if not view_type or not fig:
            return no_update, no_update

        # 1. Get current camera state from the store
        if not camera_data:
            camera_data = {
                "eye": {"x": 1.5, "y": 1.5, "z": 1.5},
                "center": {"x": 0, "y": 0, "z": 0},
                "up": {"x": 0, "y": 0, "z": 1},
                #"projection": {"type": "orthographic"}
                "projection": {"type": "orthographic"}
            }

        # 2. Get current center, eye, and projection
        center = camera_data.get('center', dict(x=0, y=0, z=0))
        center_vec = np.array([center['x'], center['y'], center['z']])
        
        current_eye_dict = camera_data.get('eye', dict(x=1.5, y=1.5, z=1.5))
        current_eye_vec = np.array([current_eye_dict['x'], current_eye_dict['y'], current_eye_dict['z']])

        # 3. Calculate the current eye distance (magnitude), which controls zoom
        current_mag = np.linalg.norm(current_eye_vec - center_vec)
        if current_mag < 1e-6:
            current_mag = 3.0 # A reasonable default

        # 4. Define new view *directions* and 'up' vectors
        if view_type == 'default':
            eye_dir = np.array([1.0, 1.0, 1.0])
            up = dict(x=0, y=0, z=1)
        elif view_type == 'x':
            eye_dir = np.array([1.0, 0, 0])
            up = dict(x=0, y=0, z=1)
        elif view_type == 'y':
            eye_dir = np.array([0, 1.0, 0])
            up = dict(x=0, y=0, z=1)
        elif view_type == 'z':
            eye_dir = np.array([0, 0, 1.0])
            up = dict(x=0, y=1, z=0)  # 'Up' is now the Y direction
        else:
            return no_update, no_update

        # 5. Normalize the direction vector
        eye_dir_normalized = eye_dir / np.linalg.norm(eye_dir)

        # 6. Create new eye vector = center + (direction * saved_magnitude)
        new_eye_vec = center_vec + (eye_dir_normalized * current_mag)
        eye = dict(x=new_eye_vec[0], y=new_eye_vec[1], z=new_eye_vec[2])

        # 7. Construct the new camera object, PRESERVING the projection
        new_camera_data = {
            'eye': eye,
            'up': up,
            'center': center,
            'projection': camera_data.get('projection', {'type': 'orthographic'})
        }

        # 8. Assign the new camera object to the figure's layout
        fig['layout']['scene']['camera'] = new_camera_data

        return new_camera_data, fig


    @app.callback(
        Output("camera-store", "data"),
        Input("structure-view", "relayoutData"),
        State("camera-store", "data"),
        prevent_initial_call=True
    )
    def store_camera(relayout, current):
        if not relayout:
            return no_update

        # Initialize camera store if empty
        if not current:
            current = {
                "eye": {"x": 1.5, "y": 1.5, "z": 1.5},
                "center": {"x": 0, "y": 0, "z": 0},
                "up": {"x": 0, "y": 0, "z": 1},
                "projection": {"type": "perspective"} # orthographic
            }

        # Check for the full camera object, which is the most common update
        if "scene.camera" in relayout:
            cam_update = relayout["scene.camera"]

            # Update eye, center, up, and projection if they exist in the update
            if "eye" in cam_update and isinstance(cam_update["eye"], dict):
                current["eye"].update(cam_update["eye"])

            if "center" in cam_update and isinstance(cam_update["center"], dict):
                current["center"].update(cam_update["center"])

            if "up" in cam_update and isinstance(cam_update["up"], dict):
                current["up"].update(cam_update["up"])

            if "projection" in cam_update and isinstance(cam_update["projection"], dict):
                current["projection"].update(cam_update["projection"])

        # Handle partial updates (e.g., relayoutData = {"scene.camera.eye.x": 1.2})
        if "scene.camera.eye.x" in relayout:
            current["eye"]["x"] = relayout["scene.camera.eye.x"]
        if "scene.camera.eye.y" in relayout:
            current["eye"]["y"] = relayout["scene.camera.eye.y"]
        if "scene.camera.eye.z" in relayout:
            current["eye"]["z"] = relayout["scene.camera.eye.z"]

        return current
