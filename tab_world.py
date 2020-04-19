import os
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_admin_components as dac
from covid_data import CovidDataProcessor, SCOPE_WORLD, CSSE_DAILY_COL_CONFIRMED, CSSE_DAILY_COL_HOVERTEXT
from tab_common import get_status_boxes
from plotutils import get_choropleth_mapbox
from tab_usa import get_choropleth_mapbox_usa


def get_choropleth_mapbox_world(dataproc: CovidDataProcessor, logger):
    mapbox_access_token = os.environ.get('MAPBOX_TOKEN')
    geojson = dataproc.get_geojson(scope=SCOPE_WORLD)
    df = dataproc.get_df_daily_report(scope=SCOPE_WORLD)
    locations = []
    cases = []
    text = []
    for feat in geojson['features']:
        country = feat['properties']['name']
        if country not in df.index:
            if logger is not None:
                logger.warning(f'{country} not found in dataset')
            continue
        row = df.loc[country]
        if row[CSSE_DAILY_COL_CONFIRMED] != 0:
            locations.append(country)
            cases.append(row[CSSE_DAILY_COL_CONFIRMED])
            text.append(row[CSSE_DAILY_COL_HOVERTEXT])

    featureid_key = 'properties.name'
    bvals = [1, 10, 100, 1000, 10000, 100000, 1000000, 10000000]

    fig = get_choropleth_mapbox(geojson=dataproc.get_geojson(scope=SCOPE_WORLD),
                                locations=locations,
                                z=cases,
                                color_boundaries = bvals,
                                color_min = '#add8e6',
                                color_max = '#000080',
                                hovertext=text,
                                mapbox_token=mapbox_access_token,
                                logarithmic=True,
                                featureid_key=featureid_key)
    return fig


def get_tab_content_world(data: CovidDataProcessor, logger=None):
    confirmed = data.get_total_confirmed(SCOPE_WORLD)
    deaths = data.get_total_deaths(SCOPE_WORLD)
    recovered = data.get_total_recovered(SCOPE_WORLD)
    active = data.get_total_active(SCOPE_WORLD)

    status_boxes = get_status_boxes(confirmed, deaths, recovered, active)

    return dac.TabItem(
        id='id-tab-content-world',
        children=html.Div(
            [
                html.Div(
                    [
                        status_boxes,
                        dac.SimpleBox(
                            style={'height': "600px"},
                            width=12,
                            title='World Outbreak Map',
                            children=[
                                dcc.Graph(
                                    id='id-mapbox-world',
                                    config=dict(displayModeBar=False),
                                    style={'width': '75vw'},
                                    figure=get_choropleth_mapbox_usa(dataproc=data, logger=logger),
                                )
                            ],
                        ),
                        dac.SimpleBox(
                            style={'height': "600px"},
                            width=12,
                            children=[
                                html.Div(
                                    [
                                        dbc.FormGroup(
                                            [
                                                dbc.Label("Select Location"),
                                                dcc.Dropdown(
                                                    id='id-dropdown-locations',
                                                    multi=True,
                                                    persistence=True,
                                                    persistence_type='local'
                                                ),
                                                dbc.Label("Stats"),
                                                dbc.RadioItems(
                                                    id='id-select-case-type',
                                                    options=[
                                                        {'label': 'Confirmed', 'value': 'Confirmed'},
                                                        {'label': 'Deaths', 'value': 'Deaths'},
                                                        {'label': 'Recovered', 'value': 'Recovered'},
                                                    ],
                                                    value='Confirmed',
                                                    inline=True
                                                ),
                                            ]
                                        )
                                    ],
                                ),
                                dcc.Graph(
                                    id='id-chart-world',
                                    config=dict(displayModeBar=False),
                                    style={'width': '75vw'}
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    )