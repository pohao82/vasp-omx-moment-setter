import numpy as np
from numpy import linalg as la
import plotly.graph_objects as go
#from pymatgen.core import Structure
import pprint
from ..load_vesta_setup import load_vesta_colors
from ..utils.unitcell_utils import unitcell_edges
from ..utils.plotly_obj import plotly_add_arrows

# VESTA Color Parser
atom_colors, atom_radii = load_vesta_colors()

# Fallback for common elements if element.ini is not found or is empty
if not atom_colors:
    print("WARNING: 'element.ini' not found or is empty. Using fallback colors.")
    atom_colors = {
        "V": "yellow", "O": "red", "Mn": "purple", "Se": "green",
        "C": "gray", "H": "white", "Fe": "orange", "N": "blue",
        "S": "lightsalmon", "Si": "steelblue"
    }

# plot structures
def structure_to_fig(structure, visible_species, radii_scale,
                     arrow_scale, center_arrow, vector_rgb,
                     highlighted_atoms=None, moments_data=None, view_options=None):
    if highlighted_atoms is None: highlighted_atoms = []
    if view_options is None: view_options = [] # Default to empty list
    fig = go.Figure()

    # plot Unitcell boundaries
    lattice = structure.lattice.matrix
    # get cell edges
    cell_x, cell_y, cell_z = unitcell_edges(lattice) 
    fig.add_trace(go.Scatter3d(
        x=cell_x, y=cell_y, z=cell_z,
        mode='lines',
        line=dict(color='black', width=2),
        name='Unit Cell',
        hoverinfo='none'
    ))

    # --------------------------------------
    # Add atoms as scatter points
    # loop over species
    for species in structure.symbol_set:
        #print(structure.sites)
        if species in visible_species:
            # group all the sites of this element/species
            indices = [i for i, site in enumerate(structure.sites) if site.species_string == species]
            #[print(f"{site._label}") for i, site in enumerate(structure.sites) if site.species_string == species]
            positions = structure.cart_coords[indices] # simple np.ndarray
            colors = [atom_colors.get(species, 'blue')] * len(indices) # Default to blue if not in dict
            radii = float(atom_radii.get(species, 1.5))

            # --- DETERMINE THE MODE BASED ON THE CHECKBOX ---
            show_indices = 'show_indices' in view_options
            mode = 'markers+text' if show_indices else 'markers'

            fig.add_trace(go.Scatter3d(
                x=positions[:, 0], y=positions[:, 1], z=positions[:, 2],
                mode=mode, # Use the mode determined above
                text=[f"#{i+1}" for i in indices], # Always provide the text
                textposition='top center', # Position the text above the marker
                textfont=dict(size=18, color='grey'),
                marker=dict(size=2*radii*radii_scale, color=colors),
                name=species,
                customdata=indices,
                hovertext=[], # [f"{species} #{i}" for i in indices],
                hoverinfo='text' # Re-enable the default hover for extra info
            ))

    # Highlight selected atoms
    if highlighted_atoms:
        pos = structure.cart_coords[highlighted_atoms]
        species_names = [structure.sites[i].species_string for i in highlighted_atoms]
        fig.add_trace(go.Scatter3d(
            x=pos[:, 0], y=pos[:, 1], z=pos[:, 2],
            mode='markers',
            marker=dict(size=10, color='yellow', symbol='circle', line=dict(color='black', width=2)),
            name='Selected', 
            hoverinfo='text',
            hovertext=[f"{s} #{i}" for s, i in zip(species_names, highlighted_atoms)],
            customdata=highlighted_atoms
        ))

    # Add magnetic moment arrows
    if moments_data:
        first_moment = True  # Flag to track the first trace
        for site_index, moment in moments_data.items():
            if sum(abs(m) for m in moment) > 1e-6:
                #mom_vec = np.sqrt(0.8*np.array(moment))
                mom_vec = 0.8*np.array(moment)
                # scale moments
                mom_vec = mom_vec/np.sqrt(la.norm(mom_vec))

                # maybe write a class object for this to interact with plotly?
                start_pos = structure.cart_coords[int(site_index)]
                fig = plotly_add_arrows(fig, start_pos, (1+0.1*arrow_scale)*mom_vec,
                                        center_arrow=center_arrow,
                                        vector_color=vector_rgb,
                                        label=f"moment",
                                        legend_name="moment_group",
                                        showlegend=first_moment)
                first_moment = False # switch off, 

    # Update layout and scene
    ax_style = dict(showbackground = False,
                backgroundcolor="rgb(240, 240, 240)",
                showgrid=False,
                zeroline=False)

    fig.update_layout(
        scene=dict(xaxis_title='X (Å)',
                   yaxis_title='Y (Å)',
                   zaxis_title='Z (Å)',
                   xaxis = ax_style,
                   yaxis = ax_style,
                   zaxis = ax_style,
                   aspectmode='data',
                   ),
        #margin=dict(l=10, r=10, t=10, b=10), 
        showlegend=True
    )
    #fig.update_layout(uirevision="structure-view")

    return fig
