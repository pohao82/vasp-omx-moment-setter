import plotly.graph_objects as go

def plotly_add_arrows(figure, start_pos, arrow_vector, center_arrow=True, 
                      vector_color = [1,0,0],
                      label='', # label to disply
                      legend_name='vector', # use to group vectors
                      showlegend=True,
                      arrow_tip_ratio=0.5,
                      arrow_starting_ratio = 0.95
                      ):

    end_pos = start_pos + arrow_vector

    shift = (end_pos-start_pos)*0.5 if center_arrow else [0,0,0]

    color_str = f'rgb({int(vector_color[0]*255)}, {int(vector_color[1]*255)}, {int(vector_color[2]*255)})'

    figure.add_trace(go.Scatter3d(
        x=[start_pos[0]-shift[0], end_pos[0]-shift[0]], 
        y=[start_pos[1]-shift[1], end_pos[1]-shift[1]], 
        z=[start_pos[2]-shift[2], end_pos[2]-shift[2]],
        mode='lines', 
        #line=dict(width=8, color='red'), 
        line=dict(width=8, color=color_str), 
        #name=f'Moment @{site_index}',
        name=label,
        legendgroup = legend_name,
        showlegend=showlegend,
        hoverinfo='skip'
    ))

    # add arrow head (cones)
    figure.add_trace(go.Cone(
        x=[start_pos[0] + arrow_starting_ratio*(end_pos[0]-start_pos[0])-shift[0]],
        y=[start_pos[1] + arrow_starting_ratio*(end_pos[1]-start_pos[1])-shift[1]],
        z=[start_pos[2] + arrow_starting_ratio*(end_pos[2]-start_pos[2])-shift[2]],
        u=[arrow_tip_ratio*(end_pos[0]-start_pos[0])],
        v=[arrow_tip_ratio*(end_pos[1]-start_pos[1])],
        w=[arrow_tip_ratio*(end_pos[2]-start_pos[2])],
        sizeref=1.2,   # Larger value = smaller cone
        showlegend=False,
        showscale=False,
        legendgroup=legend_name,
        #colorscale=[[0, 'rgb(255,0,0)'], [1, 'rgb(255,0,0)']]
        colorscale=[[0, color_str], [1, color_str]]
        ))

    return figure

# for 3d balls plotting 
# https://stackoverflow.com/questions/70977042/how-to-plot-spheres-in-3d-with-plotly-or-another-library

