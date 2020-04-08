import os
import dash_html_components as html
import dash_core_components as dcc
import dash_admin_components as dac
import covid_data as data
from covid_data import CovidDataProcessor, SCOPE_USA, SCOPE_US_COUNTIES
from covid_data import CSSE_DAILY_COL_CONFIRMED, CSSE_DAILY_COL_FIPS, CSSE_DAILY_COL_HOVERTEXT
from tab_common import get_status_boxes
from plotutils import get_choropleth_mapbox


def get_choropleth_mapbox_usa(dataproc: CovidDataProcessor, logger):
    mapbox_access_token = os.environ.get('MAPBOX_TOKEN')
    geojson = dataproc.get_geojson_us_counties()
    df = dataproc.get_df_daily_report(scope=SCOPE_US_COUNTIES)
    bvals = [1, 10, 100, 1000, 10000, 100000, 1000000]
    df_positive = df[df[CSSE_DAILY_COL_CONFIRMED] != 0]
    fig = get_choropleth_mapbox(geojson=geojson,
                                locations=df_positive[CSSE_DAILY_COL_FIPS],
                                z=df_positive[CSSE_DAILY_COL_CONFIRMED],
                                color_boundaries = bvals,
                                color_min = '#ffff00',
                                color_max = '#8b0000',
                                hovertext=df_positive[CSSE_DAILY_COL_HOVERTEXT],
                                mapbox_token=mapbox_access_token,
                                logarithmic = True)
    return fig


def get_tab_content_usa(data: CovidDataProcessor, logger):
    confirmed = data.get_total_confirmed(SCOPE_USA)
    deaths = data.get_total_deaths(SCOPE_USA)
    recovered = data.get_total_recovered(SCOPE_USA)
    active = data.get_total_active(SCOPE_USA)

    status_boxes = get_status_boxes(confirmed, deaths, recovered, active)

    return dac.TabItem(
        id='id-tab-content-usa',
        children=html.Div(
            [
                html.Div(
                    [
                        status_boxes,
                        dac.SimpleBox(
                            style={'height': "600px"},
                            title='U.S. Outbreak Map',
                            width=12,
                            children=[
                                dcc.Graph(
                                    id='id-mapbox-usa',
                                    config=dict(displayModeBar=False),
                                    style={'width': '75vw'},
                                    figure=get_choropleth_mapbox_usa(data, logger)
                                )
                            ]
                        ),
                        dac.SimpleBox(
                            style={'height': "600px"},
                            title="Box 2",
                            width=12,
                            children=[
                                html.Div(
                                    [
                                        dcc.Dropdown(
                                           id='id-dropdown-locations-usa',
                                           multi=True,
                                           persistence=True,
                                           persistence_type='local'
                                        ),
                                        dcc.RadioItems(
                                           id='id-select-case-type-usa',
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
                                    id='id-chart-usa',
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