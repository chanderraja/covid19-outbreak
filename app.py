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
from tab_usa import get_tab_content_usa
from tab_world import get_tab_content_world
import covid_data

SCOPE_WORLD='world'
SCOPE_USA='usa'

SCOPE_WORLD_LABEL='Worldwide'
SCOPE_USA_LABEL='United States'

STAT_CONFIRMED='Confirmed'
STAT_DEATHS='Deaths'
STAT_RECOVERED='Recovered'
STAT_ACTIVE='Active'


dataproc = covid_data.CovidDataProcessor()

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

df_countries = df.drop(columns=[COL_FIPS, COL_PROVINCE_STATE, COL_ADMIN2, COL_LATITUDE, COL_LONGITUDE, COL_LOC_COMBINED])
df_countries = df_countries.groupby(df[COL_COUNTRY_REGION]).aggregate(aggregation_functions)
df_countries.rename(
    index={
        'US': 'United States of America',
        'Congo (Brazzaville)': 'Republic of the Congo',
        'Congo (Kinshasa)': 'Democratic Republic of the Congo'
    }, inplace=True)

df_world_totals = df_countries.aggregate(aggregation_functions)

with open('./data/us_counties_2010.json') as f:
    us_counties = json.load(f)
    for feat in us_counties['features']:
        state_fips = feat['properties']['STATE']
        county_fips = feat['properties']['COUNTY']
        feat['id'] = state_fips + county_fips


with open('./data/countries.geo.json') as f:
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

def get_time_series_scatter_chart(df, locations=None):
    aggregate_sum = df.aggregate('sum')
    x_list = [pd.to_datetime(d).date() for d in aggregate_sum.index]
    data = []
    data.append(go.Scatter(x=x_list,
                           y=aggregate_sum,
                           mode='lines'))
    if locations is not None and isinstance(locations, list):
        for loc in locations:
            if loc not in df.index:
                app.logger.warning(f'Invalid location {loc} passed, skipping....')
                continue
            data.append(go.Scatter(x=x_list,
                               y=df.loc[loc,:],
                               mode='lines',
                               name=loc))
    layout = go.Layout(
        plot_bgcolor='rgba(240,240,255,100)',
        legend=dict(
            x=0.1,
            y=0.7,
            traceorder='normal',
            font=dict(
                size=12, ),
        ),
    )

    fig = go.Figure(data=data, layout=layout)
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
    ]) #, className='row')


def serve_layout():
    return dac.TabItem(
        id='content_value_boxes',
        children=[
            dac.Body(
                [
                    get_status_boxes(),
                    dac.SimpleBox(
                        #style={'height': '600px', 'width': '1200px'},
                        children=[
                                dcc.Graph(
                                    id='id-mapbox-world',
                                    figure=get_choropleth_mapbox_world(),
                                ),
                        ], width=10
                    ),
                    dac.SimpleBox(
                        #style={'height': '600px', 'width': '1200px'},
                        title='Confirmed cases over time',
                        children=[
                            dcc.Dropdown(
                                id='id-dropdown-locations',
                                multi=True,
                                persistence=True,
                                persistence_type='local'
                            ),
                            html.Br(),
                            dcc.RadioItems(
                                id='id-select-case-type',
                                options=[
                                    {'label': STAT_CONFIRMED, 'value': STAT_CONFIRMED},
                                    {'label': STAT_DEATHS, 'value': STAT_DEATHS},
                                ],
                                value='Confirmed',
                                labelStyle={'display': 'inline-block'},
                                persistence=True,
                                persistence_type='local'
                            ),
                            html.Br(),
                            dcc.Graph(
                                id='id-chart-cases-by-date'
                            ),
                        ], width=10
                    ),
                    dac.SimpleBox(
                        #style={'height': '600px', 'width': '1200px'},
                        title='Deaths over time',
                        children=[
                            dcc.Graph(
                                id='id-chart-deaths-by-date',
                            ),
                        ], width=10
                    ),
                ],
            ),
        ]
    )

body = dac.Body(
    dac.TabItems([
        get_tab_content_world(dataproc),
        get_tab_content_usa(dataproc)
    ])
)
sidebar = dac.Sidebar(
    [
        dac.SidebarMenu(
            [
                dac.SidebarHeader(children='Select Outbreak Scope'),
                dac.SidebarMenuItem(id='id-tab-world', label='Worldwide', icon=''),
                dac.SidebarMenuItem(id='id-tab-usa', label='United States', icon=''),
            ]
        ),
    ],
    title='Dashboard',
    skin='light',
    color='primary',
    brand_color='primary',
    src='./assets/virus.png',
    elevation=5,
    opacity=0.8
)

app.layout = dac.Page([sidebar, body])


# =============================================================================
# Callbacks
# =============================================================================
def activate(input_id, n_tab_world, n_tab_usa):
    # Depending on tab which triggered a callback, show/hide contents of app
    if input_id == 'id-tab-world' and n_tab_world:
        return True, False
    elif input_id == 'id-tab-usa' and n_tab_usa:
        return False, True
    else:
        return True, False


@app.callback([Output('id-tab-content-world', 'active'),
               Output('id-tab-content-usa', 'active')],
              [Input('id-tab-world', 'n_clicks'),
               Input('id-tab-usa', 'n_clicks')]
              )
def display_tab(n_tab_world, n_tab_usa):
    ctx = dash.callback_context  # Callback context to recognize which input has been triggered

    # Get id of input which triggered callback
    if not ctx.triggered:
        raise PreventUpdate
    else:
        input_id = ctx.triggered[0]['prop_id'].split('.')[0]

    return activate(input_id, n_tab_world, n_tab_usa)

'''
@app.callback(
    [Output('id-mapbox-world', 'figure'),
     Output('id-dropdown-locations', 'options'),
     Output('id-dropdown-locations', 'value'),
     Output('id-chart-cases-by-date', 'figure')],
    [Input('id-select-scope', 'value')]
)
'''
def update_output_div(scope):
    if scope == SCOPE_WORLD:
        df = dataproc.get_df_confirmed_by_date_world()
        options = [{'label': x, 'value': x} for x in df.index]
        value = df.index[0]
        map = get_choropleth_mapbox_world()
        chart = get_time_series_scatter_chart(df)
    else:
        df = dataproc.get_df_confirmed_by_date_usa()
        options = [{'label': x, 'value': x} for x in df.index]
        value = df.index[0]
        map = get_choropleth_mapbox_us_counties()
        chart = get_time_series_scatter_chart(df)
    return [map, options, value, chart]


if __name__ == '__main__':
    app.run_server(debug=True)
