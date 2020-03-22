import os
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import io
import requests


url='https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/03-21-2020.csv'
s=requests.get(url).content
df=pd.read_csv(io.StringIO(s.decode('utf-8')))

def get_location(row):
    state = row['Province/State']
    country = row['Country/Region']
    if pd.isna(state):
        return country
    return state + '<br>' + country

def get_hovertext(row):
    return get_location(row) + '<br>' + 'Confirmed = ' + str(row['Confirmed']) + \
           '<br>' + 'Deaths = ' + str(row['Deaths']) + '<br>' + 'Recovered =' + str(row['Recovered'])

df['hovertext'] = df.apply(lambda row: get_hovertext(row), axis=1)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
mapbox_access_token = os.environ.get('MAPBOX_TOKEN')
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

def get_mapbox():
    datamap =  [dict(
        type='scattermapbox',
        lat=df['Latitude'],
        lon=df['Longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=df['Confirmed'],
            sizeref=2.*df['Confirmed'].values.max()/(100**2),
            sizemode='area',
            color='rgb(180,0,0)',
        ),
        text=df['hovertext']
    )]
    layout = dict(
        autosize=True,
        height=600,
        hovermode='closest',
        geo = dict(
            projection = dict(
                type = 'equirectangular'
            ),
        ),
        mapbox=dict(
            style='dark',
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=38.92,
                lon=-77.07
            ),
            pitch=0,
            zoom=2
        ),
    )

    fig = dict(
        data=datamap,
        layout=layout
    )

    return dcc.Graph(
        id='id-mapbox',
        figure=fig
    )


def serve_layout():
    return html.Div(
        [
            html.H4(
                'COVID-19 Outbreak Dashboard',
                style={
                    'color': 'blue',
                    'font-style': 'italic',
                    'font-weight': 'bold',
                    'height': '50px',
                    'display': 'inline-block'
                }
            ),
            dcc.Loading(
                id='id-loading',
                children=[
                    html.Div(
                        [
                            get_mapbox()
                        ],
                        id='id-map-container'
                    ),
                ],
                type='circle'
            ),
        ]
    )


app.layout = serve_layout()

if __name__ == '__main__':
    app.run_server(debug=True)
