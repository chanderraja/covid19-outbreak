import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from covid_data import CovidDataProcessor, SCOPE_WORLD
from tab_common import get_time_series_scatter_chart
from tab_world import get_choropleth_mapbox_world

# =============================================================================
# Dash App and Flask Server
# =============================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

dataproc = CovidDataProcessor()

def get_location_options():
    df = dataproc.get_df_confirmed_by_date_world()
    options = [{'label': i, 'value': i} for i in df.index]
    return options

def get_chart(df):
    controls = dbc.Card(
        [
            dbc.FormGroup(
                [
                    dbc.Label('Select statistic to plot'),
                    dbc.RadioItems(
                        id='id-radiobuttons-stat',
                        options=[
                            {'label': 'Confirmed', 'value': 'confirmed'},
                            {'label': 'Deaths', 'value': 'deaths'},
                            {'label': 'Recovered', 'value': 'recovered'},
                            {'label': 'Active', 'value': 'active'},
                        ],
                        value='confirmed',
                    ),
                ]
            ),
        ],
        body=True,
        className='row'
    )
    return controls


map = dcc.Graph(
    id='id-outbreak-map',
    figure=get_choropleth_mapbox_world(dataproc, logger=app.logger),
    responsive=True,
)

def get_location_selector():
    return dbc.Card(
        dbc.FormGroup(
            [
                dbc.Label('Select up to 5 locations to compare'),
                dcc.Dropdown(
                    id='id-loc-dropdown',
                    options=get_location_options(),
                    value=['Worldwide'],
                    multi=True
                ),
            ]
        ),
    )

def get_outbreak_chart(title, id):
    return dbc.Card(
        [
            html.H4(title),
            dcc.Graph(id=id, responsive=False)
        ]
    )



def serve_layout():
    layout = dbc.Container(
        [
            html.H1("My Dashboard"),
            html.Hr(),
            dbc.FormGroup(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [get_location_selector()],
                                sm=12,
                                md=8,
                                lg=6,
                            ),
                        ],
                        align='center'
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [get_outbreak_chart('Confirmed', 'id-timechart-confirmed')],
                                sm=12,
                                md=6,
                                lg=6,
                            ),
                            dbc.Col(
                                [get_outbreak_chart('Deaths', 'id-timechart-deaths')],
                                sm=12,
                                md=6,
                                lg=6,
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card([map]),
                                lg=8
                            ),
                        ],
                        align='center'
                    ),
                ],
            )
        ],
        fluid=True,
    )
    return layout


app.layout = serve_layout

def process_time_graph(locations):
    chart_confirmed = get_time_series_scatter_chart(dataproc.get_df_confirmed_by_date_world(),
                                                locations=locations)
    chart_deaths = get_time_series_scatter_chart(dataproc.get_df_deaths_by_date_world(),
                                                locations=locations)
    options = get_location_options()
    if len(locations) == 5:
        options = [x for x in options if x['value'] in locations]
    return [chart_confirmed, chart_deaths, options]


# functionality is the same for both dropdowns, so we reuse filter_options
app.callback([Output('id-timechart-confirmed', 'figure'),
              Output('id-timechart-deaths', 'figure'),
              Output('id-loc-dropdown', 'options')],
             [Input('id-loc-dropdown', 'value')])(
    process_time_graph
)


if __name__ == '__main__':
    app.run_server(debug=False, port=8888)
