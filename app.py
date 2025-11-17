import dash
from VaspOMXMomentSetter.view.layout import create_layout
from VaspOMXMomentSetter.callbacks import register_callbacks

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "MAGMOM Generator"
server = app.server

app.layout = create_layout()
register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)
