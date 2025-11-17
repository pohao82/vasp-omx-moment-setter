from dash import dcc, html, dash_table
import importlib

def create_layout():
    """Creates the layout for the Dash app."""

    # check if library exist
    libp2o_exists = importlib.util.find_spec('poscar2openmx') is not None
    if libp2o_exists:
        print(f'Found library poscar2openmx activate option for create OpenMX input')
    show_p2o_option = {'visibility': 'visible','marginLeft':'10px'} if libp2o_exists == True else {'visibility': 'hidden'}

    return html.Div(style={'fontFamily': 'Arial, sans-serif'}, children=[
        # Data Stores
        dcc.Store(id='structure-store'),
        dcc.Store(id='moments-store', data={}),
        dcc.Store(id='moments-sph-store', data={}),
        dcc.Store(id='valence-store', data={}),
        dcc.Store(id='selected-atoms-store', data=[]),
        # camera
        dcc.Store(id='camera-store', data={}),
        dcc.Store(id="axis-range-store"),

        dcc.Store(id='last-click-timestamp-store', data=0),
        dcc.Store(id='natoms-store', data=0),
        dcc.Store(id='input-str', data=0),
        dcc.Store(id='is-omx', data=0),
        dcc.Store(id='poscar2omx-exists', data=0),

        # Header
        #html.Div(className='row', style={'display': 'flex'}, children=[
        #    html.H3("Interactive OpenMX input and Vasp MAGMOM generator", 
        #            style={'textAlign': 'center', 'marginBottom': '5px', 'marginTop': '5px' }),
        #]),
        html.H3("Interactive OpenMX input and Vasp MAGMOM generator", 
                style={'textAlign': 'center', 'marginBottom': '5px', 'marginTop': '5px' }),
        html.Hr(),
        # Main Content Area
        html.Div(className='row', style={'display': 'flex'}, children=[
            # Left Column: Structure Viewer
            html.Div(className='seven columns', style={'flex': '70%', 'padding': '10px', 'minWidth':0}, children=[
                # new grouped option
                html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '30px', 'marginBottom': '0px'}, children=[

                    # Item 1: Upload Box 
                    dcc.Upload(id='upload-input',
                        children=html.Div(['Drag & Drop or ', 'Select POSCAR']),
                        style={
                            'height': '50px', 'lineHeight': '50px', 'borderWidth': '1px',
                            'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center',
                            'padding': '0 10px',
                            'flex':'40%'
                        },
                        style_active={'borderColor': 'blue'},
                        style_reject={'borderColor': 'red'},
                        className='flex-item',
                    ),

                    # Item 2: Species Checklist
                    html.Div(children=[
                        html.Label("Species:", style={'fontWeight': 'bold'}),
                        dcc.Checklist(id='species-checklist', inline=True, labelStyle={'marginRight': '15px'})
                    ], className='flex-item', style={'flex': '30%'}),

                    # Item 3: Checklist for atom indices
                    html.Div(children=[
                        html.Label("View Options:", style={'fontWeight': 'bold'}),
                        dcc.Checklist(
                            id='view-options-checklist',
                            options=[{'label': 'Show Atom Indices', 'value': 'show_indices'}],
                            value=[],
                            inline=True
                        )
                    ], className='flex-item', style={'flex': '30%'}),
                ]),

                # --- Set view angles ---
                html.Div(style={'display': 'flex', 'marginBottom': '5px'}, children=[
                    html.Label("Set View Angle:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                    dcc.RadioItems(
                        id='view-angle-radio',
                        options=[
                            {'label': 'Default', 'value': 'default'},
                            {'label': 'From X', 'value': 'x'},
                            {'label': 'From Y', 'value': 'y'},
                            {'label': 'From Z', 'value': 'z'},
                        ],
                        value='default', # Start with the default view
                        inline=True,
                        labelStyle={'marginRight': '15px'}
                    )
                ]),
                # ---

            dcc.Graph(id='structure-view', style={'height': '85vh'}, config={'scrollZoom': True}), ]),

            # Right Column: Control Panel
            html.Div(style={'flex': '30%', 'padding': '0px'}, children=[
                #html.H3("Magnetic Moment Configuration"),
                html.Div(
                    style={'display': 'flex', 'alignItems': 'center', 'gap': '15px'}, # 'gap' adds spacing between items
                    children=[
                        html.B("Mode"), 
                        dcc.RadioItems(id='magnetism-type',
                            options=[{'label': 'Collinear', 'value': 'collinear'},
                                     {'label': 'Non-collinear', 'value': 'noncollinear'}],
                            value='collinear', labelStyle={'display': 'inline-block', 'marginRight': '20px'}),
                        html.Label("radii scale"), 
                        dcc.Input(id='radii-scale', type='number', value=4.0, style={'width': '30px'}),
                    ]),

                html.Div(style={'flex': '30%', 'padding': '0px'}, children=[
                        html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '5px'}, children=[
                            html.B("Vector:"),
                            html.Label("Scale"),
                            dcc.Input(id='arrow-scale', type='number', value=4.0, style={'width': '25px'}),
                            # <color 
                            html.Label("Color"),
                            dcc.Dropdown(
                                id='color-dropdown',
                                options=[
                                    {'label': '🔴 Red', 'value': 'red'},
                                    {'label': '🟢 Green', 'value': 'green'},
                                    {'label': '🔵 Blue', 'value': 'blue'},
                                    {'label': '⚫ Gray', 'value': 'gray'},
                                    {'label': '⚫ Black', 'value': 'black'}
                                ],
                                value='red',
                                clearable=False,
                                style={'width': '110px', 'fontSize': '14px'}  # Increases everything including balls
                            ),
                            # shift vectors 
                            dcc.Checklist(
                                id='center-vector-check',
                                options=[{'label': 'center', 'value': 'center'}],
                                value=['center'],
                                inline=True
                            ),
                        ])
                    ]),

                html.Hr(),
                html.Label("Update from MAGMOM String", style={'fontWeight': 'bold'}),
                # update moment using MAGMOM string
                dcc.Textarea(
                    id='magmom-input-textarea',
                    placeholder="Paste MAGMOM string here...\ne.g., 2*5.0 2*-5.0 or 0 0 5 0 0 -5 ...",
                    style={'width': '100%', 'height': 32}
                ),
                html.Button('Update from MAGMOM', id='update-from-magmom-button', n_clicks=0, style={'marginTop': '0px'}),
                html.Hr(),

                html.Div(
                    # Use flex display to align children horizontally
                    style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '5px'},
                    children=[
                        # 1. Atom Selection Info (Label/Text)
                        html.Div(
                            id='atom-selection-info', 
                            children="Click on atoms to select/deselect them.", 
                            style={'marginRight': '30px'} 
                        ),
                        # 2. Deselect All Button
                        html.Button(
                            'Deselect All', 
                            id='deselect-all-button', 
                            n_clicks=0, 
                        ),
                    ]
                ),

                # Alternative option, manually input atomic indices in input box
                html.Div([
                    html.Label("Or Select by numbers:", style={'marginTop': '10px'}),
                    dcc.Input(
                        # input numbers as a text string and the parse it
                        id='text-selection-input',
                        type='text',
                        placeholder='e.g., 0, 5:10, 12',
                        style={'width': '60%'}
                    )
                ]),
                # moment input
                html.Label("Input moment for the selected sites:",style={'fontWeight': 'bold'}), 
                html.Div(style={'maxHeight': '50px', 'overflowY': 'auto', 'padding': '5px'},id='moment-input-container'), 
                html.Div([
                    html.Button('Set Moments', id='update-moment-button', n_clicks=0),
                    html.Button('Reset All Moments', id='reset-moments-button', n_clicks=0, style={'marginLeft': '5px'})
                ], style={'marginTop': '0px'}),

                # Panel for Rotating moments
                html.Hr(),
                html.Div(
                    style={'display': 'flex', 'alignItems': 'center', 'width': '100%'}, # This is the parent container
                    children=[
                        # child 1
                        html.Div(
                            children=[
                            dcc.Checklist(
                                id='moment-rotate-check',
                                options=[{'label': 'Rotate moments', 'value': 'show'}],
                                value=[],
                                inline=True
                            )
                        ], style={'flex': '35%'}),
                        # child 2: the layout dependis on whether collinear oor noncollinear is selected
                        html.Div(id='moment-rot-input-container',style={'flex': '75%'} ), 
                    ]),

                html.Hr(),
                #--------------------------------------
                html.Div(style={'display': 'flex'}, children=[
                    html.B("Specified Moments Table", style={'marginTop': '2px'}),
                    html.Div( 
                        dcc.Checklist(
                            id='show-table-check',
                            options=[{'label': 'Display', 'value': 'show'}],
                            value=[],
                            inline=True
                        ), style={'display': 'flex', 'alignItems': 'center', 'width': '30%'}
                    ),
                ]),
                html.Div(id='moment-table-container', style={'flex': '65%'}),
                #--------------------------------------
                html.Hr(),
                html.Button('Generate VASP MAGMOM', id='generate-magmom-button', n_clicks=0, style={'marginTop': '10px'}),
                dcc.Textarea(id='magmom-output', readOnly=True,
                             placeholder="Your MAGMOM string will appear here...",
                             style={'width': '100%', 'height': 40, 'marginTop': '5px', 'fontFamily': 'monospace'}),
                #---------------------------------------------------------
                html.Div(
                    style={'display': 'flex', 'alignItems': 'center', 'width': '100%'},
                    children=[
                        html.B('Generate input:'),
                        # child 1
                        #html.Div(id='generate-omx-container',style={'flex': '75%'}),
                        html.Div(
                            style=show_p2o_option,
                            children=[
                                html.Div([
                                    html.Button('OpenMX (poscar2omx)', id='generate-openmx-button',
                                                n_clicks=0, style={'marginLeft': '0px'}),
                                    dcc.Download(id="download-openmx-input")
                                ], style={'marginTop': '10px'}),
                            ]),
                        # child 2: openmx *.dat file detected, decide whether to reuse the parameters or default
                        html.Div(id='keep-omx-parameter-container',style={'flex': '45%'}), 
                        #
                    ]),
            ])
        ])
    ])
