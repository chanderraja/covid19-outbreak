import dash_html_components as html
import dash_admin_components as dac
import dash_core_components as dcc
from plotutils import get_choropleth_mapbox

def get_status_boxes(confirmed, deaths, recovered, active):
    return html.Div([
        dac.InfoBox(
            value=f'{confirmed:,}',
            title='Confirmed',
            color='info',
            icon='thermometer',
            width=3
        ),
        dac.InfoBox(
            elevation=4,
            value=f'{deaths:,}',
            title='Deaths',
            color='danger',
            icon='ribbon',
            width=3
        ),
        dac.InfoBox(
            value=f'{recovered:,}',
            title='Recovered',
            color='success',
            icon='running',
            width=3
        ),
        dac.InfoBox(
            value=f'{active:,}',
            title='Active',
            color='warning',
            icon='ambulance',
            width=3
        ),
    ], className='row')

def get_mapbox(id, title, scope):
    return dac.SimpleBox(
        style={'height': "600px"},
        width=12,
        title=title,
        children=[
            dcc.Graph(
                id=id,
                config=dict(displayModeBar=False),
                style={'width': '90vw'},
                figure=get_choropleth_mapbox()
            )
        ],
    ),

