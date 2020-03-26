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
import json
from urllib.request import urlopen
import numpy as np

COL_FIPS='FIPS'
COL_PROVINCE_STATE='Province_State'
COL_COUNTRY_REGION='Country_Region'
COL_ADMIN2='Admin2'
COL_LATITUDE='Lat'
COL_LONGITUDE='Long_'
COL_CONFIRMED='Confirmed'
COL_DEATHS='Deaths'
COL_RECOVERED='Recovered'
COL_ACTIVE='Active'
COL_LOC_COMBINED='Combined_Key'
COL_HOVERTEXT='Hovertext'


url='https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/'+\
    'csse_covid_19_data/csse_covid_19_daily_reports/03-25-2020.csv'
s=requests.get(url).content
df=pd.read_csv(io.StringIO(s.decode('utf-8')))

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

def get_location(row):
    return row[COL_LOC_COMBINED]

def get_hovertext(row):
    return get_location(row) + '<br>' + \
           'Confirmed = ' + str(row[COL_CONFIRMED]) + '<br>' + \
           'Deaths = ' + str(row[COL_DEATHS]) + '<br>' + \
           'Recovered =' + str(row[COL_RECOVERED]) + '<br>' + \
           'Active =' + str(row[COL_ACTIVE])

df[COL_HOVERTEXT] = df.apply(lambda row: get_hovertext(row), axis=1)

df_usa = df[df[COL_COUNTRY_REGION]=='US']
df_usa = df[df[COL_FIPS].notna()] # drop rows with NaN in FIPS column
df_usa[COL_CONFIRMED] = df_usa[COL_CONFIRMED].replace(0, .000001)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
mapbox_access_token = os.environ.get('MAPBOX_TOKEN')
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

def get_location_suggestions():
    suggestions = df[COL_COUNTRY_REGION].unique().tolist()
    suggestions += df[COL_PROVINCE_STATE].fillna('').unique().tolist()
    suggestions += df[COL_ADMIN2].fillna('').unique().tolist()
    suggestions = sorted(suggestions)
    return suggestions

location_suggestions = get_location_suggestions()

DEFAULT_LATITUDE=38.92
DEFAULT_LONGITUDE=-77.07
DEFAULT_ZOOM=2


def get_latlong_and_zoom(location):
    if location is not None and location is not '':
        zoom = 4
        rows = df[df[COL_COUNTRY_REGION] == location]
        if rows.shape[0] == 0:
            rows = df[df[COL_PROVINCE_STATE] == location]
            zoom=5
        if rows.shape[0] == 0:
            rows = df[df[COL_ADMIN2] == location]
            zoom = 6
        if rows.shape[0] != 0:
            row = rows.iloc[0]
            return row[COL_LATITUDE], row[COL_LONGITUDE], zoom
    return DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_ZOOM

def get_choropleth_mapbox():
    fig = go.Figure(go.Choroplethmapbox(geojson=counties, locations=df_usa.FIPS,
                                        z=np.log10(df_usa.Confirmed),
                                        colorscale="Viridis",
                                        zmin=0, zmax=df_usa.Confirmed.max(), marker_line_width=0))
    fig.update_layout(mapbox_style="light", mapbox_accesstoken=mapbox_access_token,
                      mapbox_zoom=3, mapbox_center={"lat": 37.0902, "lon": -95.7129})
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig

def get_mapbox(center_latitude, center_longitude, zoom):
    datamap =  dict(
        type='scattermapbox',
        lat=df[COL_LATITUDE],
        lon=df[COL_LONGITUDE],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=df[COL_CONFIRMED],
            sizeref=2.*df[COL_CONFIRMED].values.max()/(100**2),
            sizemode='area',
            color='rgb(180,0,0)',
        ),
        text=df[COL_HOVERTEXT]
    )
    layout = dict(
        autosize=True,
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
                lat=center_latitude,
                lon=center_longitude
            ),
            pitch=0,
            zoom=zoom
        ),
        height=800,
    )

    fig = dict(
        data=[datamap],
        layout=layout
    )
    return fig


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
                    'display': 'block',
                    'text-align': 'center',
                    'left-margin': 'auto',
                    'right-margin': 'auto'
                }
            ),
            html.Datalist(
                id='id-list-suggested-inputs',
                children=[html.Option(value=word) for word in location_suggestions]
            ),

            dcc.Tabs([
                dcc.Tab(label='World', children=[
                    dcc.Input(id='id-input-loc',
                              type='text',
                              list='id-list-suggested-inputs',
                              value=''),
                    dcc.Graph(
                        id='id-mapbox-world',
                        figure={})
                ]),
                dcc.Tab(label='USA', children=[
                    dcc.Graph(
                        id='id-mapbox-usa',
                        figure=get_choropleth_mapbox())
                ]),
            ]),
        ]
    )


app.layout = serve_layout()

@app.callback(
    Output('id-mapbox-world', 'figure'),
    [Input('id-input-loc', 'value')]
)
def location_selected(location):
    lat, long, zoom = get_latlong_and_zoom(location)
    app.logger.warning(f'location={location}, lat={lat}, long={long}, zoom={zoom}')
    return get_mapbox(lat, long, zoom)

if __name__ == '__main__':
    app.run_server(debug=True)
