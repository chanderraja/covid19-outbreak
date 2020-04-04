import os
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_admin_components as dac
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
aggregation_functions = {COL_CONFIRMED: 'sum', COL_DEATHS: 'sum', COL_RECOVERED: 'sum', COL_ACTIVE: 'sum'}

url_daily = './covid-19-data/csse_covid_19_data/csse_covid_19_daily_reports/04-03-2020.csv'
df = pd.read_csv(url_daily, dtype={COL_FIPS: str})

url_time_series_confirmed = './covid-19-data/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
df_time_series_confirmed = pd.read_csv(url_time_series_confirmed)
df_countries_time_series_confirmed = df_time_series_confirmed.drop(columns=['Province/State', COL_LATITUDE, 'Long'])
df_countries_time_series_confirmed = df_countries_time_series_confirmed.groupby(df_countries_time_series_confirmed['Country/Region']).aggregate('sum')
df_countries_time_series_confirmed.rename(
    index={
        'US': 'United States of America',
        'Congo (Brazzaville)': 'Republic of the Congo',
        'Congo (Kinshasa)': 'Democratic Republic of the Congo'
    }, inplace=True)

df_countries = df.drop(columns=[COL_FIPS, COL_PROVINCE_STATE, COL_ADMIN2, COL_LATITUDE, COL_LONGITUDE, COL_LOC_COMBINED])
df_countries = df_countries.groupby(df[COL_COUNTRY_REGION]).aggregate(aggregation_functions)
df_countries.rename(
    index={
        'US': 'United States of America',
        'Congo (Brazzaville)': 'Republic of the Congo',
        'Congo (Kinshasa)': 'Democratic Republic of the Congo'
    }, inplace=True)

df_world_totals = df_countries.aggregate(aggregation_functions)

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

external_stylesheets = [dbc.themes.DARKLY]
mapbox_access_token = os.environ.get('MAPBOX_TOKEN')
app = dash.Dash(__name__)
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

def get_time_series_scatter_chart_world():
    df_world_time_series_confirmed = df_countries_time_series_confirmed.aggregate('sum')
    x_list = [pd.to_datetime(d).date() for d in df_world_time_series_confirmed.index]
    data = []
    data.append(go.Scatter(x=x_list,
                     y=df_world_time_series_confirmed,
                     mode='lines'))
    fig = go.Figure(data=data, layout=dict(title='World Confirmed Outbreaks'))
    return fig


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
    bvals = [1, 10, 100, 1000, 10000, 100000, 1000000, 10000000]

    fig = get_choropleth_mapbox(geojson=countries,
                                locations=locations,
                                z=cases,
                                color_boundaries = bvals,
                                color_min = '#ffff3F',
                                color_max = '#8b0000',
                                hovertext=text,
                                mapbox_token=mapbox_access_token,
                                logarithmic=True,
                                featureid_key=featureid_key)
    return fig


def get_choropleth_mapbox_us_counties():
    bvals = [1, 10, 100, 1000, 10000, 100000]
    df_positive = df_usa[df_usa[COL_CONFIRMED] != 0]
    fig = get_choropleth_mapbox(geojson=us_counties,
                                locations=df_positive[COL_FIPS],
                                z=df_positive[COL_CONFIRMED],
                                color_boundaries = bvals,
                                color_min = '#ffff00',
                                color_max = '#8b0000',
                                hovertext=df_positive[COL_HOVERTEXT],
                                mapbox_token=mapbox_access_token,
                                logarithmic = True)
    return fig


def get_status_boxes():
    return html.Div([
        dac.InfoBox(
            value=f'{df_world_totals[COL_CONFIRMED]:,}',
            title='Confirmed',
            color='info',
            icon='hospital',
            width=3
        ),
        dac.InfoBox(
            elevation=4,
            value=f'{df_world_totals[COL_DEATHS]:,}',
            title='Deaths',
            color='danger',
            icon='ribbon',
            width=3
        ),
        dac.InfoBox(
            value=f'{df_world_totals[COL_RECOVERED]:,}',
            title='Recovered',
            color='success',
            icon='running',
            width=3
        ),
        dac.InfoBox(
            value=f'{df_world_totals[COL_ACTIVE]:,}',
            title='Active',
            color='warning',
            icon='ambulance',
            width=3
        ),
    ], className='row')


def serve_layout():
    return dac.TabItem(
        id='content_value_boxes',
        children=[
            dac.Body(
                [
                    get_status_boxes(),
                    dac.SimpleBox(
                        style={'height': '600px', 'width': '800px'},
                        title='World',
                        children=[
                            dcc.Graph(
                                id='id-mapbox-world',
                                figure=get_choropleth_mapbox_world(),
                            ),
                        ], width=12
                    ),
                    dac.SimpleBox(
                        style={'height': '600px', 'width': '800px'},
                        title='World Confirmed',
                        children=[
                            dcc.Graph(
                                id='id-time-series-world',
                                figure=get_time_series_scatter_chart_world(),
                            ),
                        ], width=12
                    ),
                    dac.SimpleBox(
                        style={'height': '600px', 'width': '800px'},
                        title='United States',
                        children=[
                            dcc.Graph(
                                id='id-mapbox-usa',
                                figure=get_choropleth_mapbox_us_counties(),
                            ),
                        ], width=12
                    )
                ],
            ),
        ]
    )


sidebar = dac.Sidebar(
    [
        dac.SidebarMenu(
            [
                dac.SidebarHeader(children='Select Outbreak Map'),
                dcc.Dropdown(
                    id='id-select-map',
                    options=[{'label': i, 'value': i} for i in ['World', 'USA']],
                    value='World'
                ),
                dac.SidebarMenuItem(id='tab_cards', label='Basic cards', icon='fa-map'),
                dac.SidebarMenuItem(id='tab_social_cards', label='Social cards', icon='id-card'),
                dac.SidebarMenuItem(id='tab_tab_cards', label='Tab cards', icon='image'),
                dac.SidebarHeader(children="Boxes"),
                dac.SidebarMenuItem(id='tab_basic_boxes', label='Basic boxes', icon='desktop'),
                dac.SidebarMenuItem(id='tab_value_boxes', label='Value/Info boxes', icon='suitcase'),
            ]
        ),
    ],
    title='Dashboard',
    skin="dark",
    color="primary",
    brand_color="primary",
    #url="https://quantee.ai",
    src='./virus.png',
    elevation=5,
    opacity=0.8
)

app.layout = dac.Page([sidebar, serve_layout()])

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
