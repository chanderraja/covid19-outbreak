import dash
from dash.dependencies import Input, Output

import dash_html_components as html
import dash_core_components as dcc
import dash_admin_components as dac

from dash.exceptions import PreventUpdate

# =============================================================================
# Dash App and Flask Server
# =============================================================================
app = dash.Dash(__name__)
server = app.server