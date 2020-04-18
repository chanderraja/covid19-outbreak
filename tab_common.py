import pandas as pd
import plotly.graph_objects as go
import dash_html_components as html
import dash_admin_components as dac
import dash_core_components as dcc
from plotutils import get_choropleth_mapbox
from covid_data import CSSE_DAILY_COL_CONFIRMED

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

def get_time_series_scatter_chart(df, locations=None, title=None, logger=None):
    if df is None:
        return dict(data=dict())
    x_list = [pd.to_datetime(d).date() for d in df.columns]
    data = []
    if locations is not None and isinstance(locations, list):
        for loc in locations:
            if loc not in df.index:
                continue
            data.append(go.Scatter(x=x_list,
                               y=df.loc[loc,:],
                               mode='lines',
                               name=loc))
    layout = go.Layout(
        title=title,
        plot_bgcolor='rgba(240,240,255,100)',
        legend=dict(
            x=0.05,
            y=0.95,
            traceorder='normal',
            font=dict(
                size=10,
            ),
        ),
    )

    fig = dict(data=data, layout=layout)
    return fig
