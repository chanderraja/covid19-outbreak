import dash_html_components as html
import dash_core_components as dcc
import dash_admin_components as dac
import covid_data as data
from covid_data import CovidDataProcessor, SCOPE_WORLD
from tab_common import get_status_boxes
from plotutils import get_choropleth_mapbox

def get_choropleth_mapbox_world(data: CovidDataProcessor, geo_json):
    locations = []
    cases = []
    text = []

    df = data.df_daily_countries()
    for feat in geo_json['features']:
        country = feat['properties']['name']
        if country in df.index:
            row = df.loc[country]
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


def get_tab_content_world(data: CovidDataProcessor):
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
                                    style={'width': '38vw'}
                                )
                            ],
                        ),
                        dac.SimpleBox(
                            style={'height': "600px"},
                            width=12,
                            title="Box 2",
                            children=[
                                html.Div(
                                    [
                                        dcc.Dropdown(
                                           id='id-dropdown-locations',
                                           multi=True,
                                           persistence=True,
                                           persistence_type='local'
                                        ),
                                        dcc.RadioItems(
                                           id='id-select-case-type',
                                           options=[
                                               {'label': 'Confirmed', 'value': 'Confirmed'},
                                               {'label': 'Deaths', 'value': 'Deaths'},
                                               {'label': 'Recovered', 'value': 'Recovered'},
                                           ],
                                           value='Confirmed',
                                           labelStyle={'display': 'inline-block'},
                                           persistence=True,
                                           persistence_type='local'
                                        ),
                                    ], className='row'
                                ),
                                dcc.Graph(
                                    id='id-chart-world',
                                    config=dict(displayModeBar=False),
                                  style={'width': '38vw'}
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    )