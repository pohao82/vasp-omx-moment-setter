from .app_callbacks.view_callbacks import register_view_callbacks
from .app_callbacks.control_callbacks import register_control_callbacks
from .app_callbacks.file_io_callbacks import register_file_io_callbacks

def register_callbacks(app):
    """
    Registers all callbacks for the Dash app by calling
    the registration functions from specialized modules.
    """
    register_view_callbacks(app)
    register_control_callbacks(app)
    register_file_io_callbacks(app)
