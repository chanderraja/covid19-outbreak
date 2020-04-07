import dash_html_components as html
import dash_core_components as dcc
import dash_admin_components as dac
import covid_data as data
from covid_data import CovidDataProcessor, SCOPE_USA
from tab_common import get_status_boxes

def get_tab_content_usa(data: CovidDataProcessor):
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
                            title='World Outbreak Map',
                            children=[
                                dcc.Graph(
                                    id='id-mapbox-usa',
                                    config=dict(displayModeBar=False),
                                    style={'width': '38vw'}
                                )
                            ]
                        ),
                        dac.SimpleBox(
                            style={'height': "600px"},
                            title="Box 2",
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
                                  style={'width': '38vw'}
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    )