import os
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import io
import requests
import json
from urllib.request import urlopen
import numpy as np
from plotutils import get_choropleth_mapbox, discrete_colorscale, interpolated_colors

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


#url='https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/'+\
#    'csse_covid_19_data/csse_covid_19_daily_reports/03-29-2020.csv'

url = './covid-19-data/csse_covid_19_data/csse_covid_19_daily_reports/04-01-2020.csv'
df=pd.read_csv(url, dtype={COL_FIPS: str})

df_countries = df.drop(columns=[COL_FIPS, COL_PROVINCE_STATE, COL_ADMIN2, COL_LATITUDE, COL_LONGITUDE, COL_LOC_COMBINED])
aggregation_functions = {COL_CONFIRMED: 'sum', COL_DEATHS: 'sum', COL_RECOVERED: 'sum', COL_ACTIVE: 'sum'}
df_countries = df_countries.groupby(df[COL_COUNTRY_REGION]).aggregate(aggregation_functions)
df_countries.rename(index={'US': 'United States of America'},inplace=True)



#with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
#    counties = json.load(response)

with open('us_counties_2010.json') as f:
    us_counties = json.load(f)
    for feat in us_counties['features']:
        state_fips = feat['properties']['STATE']
        county_fips = feat['properties']['COUNTY']
        feat['id'] = state_fips + county_fips


with open('countries.geo.json') as f:
    countries = json.load(f)


def get_location(row):
    if COL_LOC_COMBINED in row.index:
        return row[COL_LOC_COMBINED]
    if COL_PROVINCE_STATE in row.index:
        if COL_COUNTRY_REGION in row.index:
            return row[COL_PROVINCE_STATE] + ', ' + row[COL_COUNTRY_REGION]
        else:
            return row[COL_PROVINCE_STATE]
    return row.name


def get_hovertext(row):
    return get_location(row) + '<br>' + \
           'Confirmed = ' + str(row[COL_CONFIRMED]) + '<br>' + \
           'Deaths = ' + str(row[COL_DEATHS]) + '<br>' + \
           'Recovered =' + str(row[COL_RECOVERED]) + '<br>' + \
           'Active =' + str(row[COL_ACTIVE])

df[COL_HOVERTEXT] = df.apply(lambda row: get_hovertext(row), axis=1)

df_countries[COL_HOVERTEXT] = df_countries.apply(lambda row: get_hovertext(row), axis=1)

df_usa = df[df[COL_COUNTRY_REGION]=='US']
df_usa = df[df[COL_FIPS].notna()] # drop rows with NaN in FIPS column

external_stylesheets = [dbc.themes.SIMPLEX]
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

def get_choropleth_mapbox_world():
    locations = []
    cases = []
    text = []
    for feat in countries['features']:
        country = feat['properties']['name']
        if country in df_countries.index:
            row = df_countries.loc[country]
            if row[COL_CONFIRMED] != 0:
                locations.append(country)
                cases.append(row[COL_CONFIRMED])
                text.append(row[COL_HOVERTEXT])

    featureid_key = 'properties.name'
    bvals = [1, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000, 10000000]

    fig = get_choropleth_mapbox(geojson=countries,
                                locations=locations,
                                z=cases,
                                color_boundaries = bvals,
                                color_min = '#ffff3F',
                                color_max = '#ff0000',
                                hovertext=text,
                                mapbox_token=mapbox_access_token,
                                logarithmic=True,
                                featureid_key=featureid_key)
    return fig


def get_choropleth_mapbox_us_counties():
    bvals = [1, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000]
    df_positive = df_usa[df_usa[COL_CONFIRMED] != 0]
    fig = get_choropleth_mapbox(geojson=us_counties,
                                locations=df_positive[COL_FIPS],
                                z=df_positive[COL_CONFIRMED],
                                color_boundaries = bvals,
                                color_min = '#ffff00',
                                color_max = '#ff0000',
                                hovertext=df_positive[COL_HOVERTEXT],
                                mapbox_token=mapbox_access_token,
                                logarithmic = True)
    return fig



def serve_layout():

    return html.Div(
        [
            html.H4(
                'Dashboard',
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
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                dcc.Graph(
                                    id='id-mapbox-world',
                                    figure=get_choropleth_mapbox_world()
                                ),
                            ]
                        ),  width={"size": 6, "offset": 3},
                    ),
                ]
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                dcc.Graph(
                                    id='id-mapbox-usa',
                                    figure=get_choropleth_mapbox_us_counties()
                                ),
                            ]
                        ), width={"size": 6, "offset": 3},
                    ),
                ]
            ),
        ]
    )



app.layout = serve_layout()

'''
@app.callback(
    Output('id-mapbox-world', 'figure'),
    [Input('id-input-loc', 'value')]
)
def location_selected(location):
    lat, long, zoom = get_latlong_and_zoom(location)
    app.logger.warning(f'location={location}, lat={lat}, long={long}, zoom={zoom}')
    return get_mapbox(lat, long, zoom)
'''
if __name__ == '__main__':
    app.run_server(debug=True)
