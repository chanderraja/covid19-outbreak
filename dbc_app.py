import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from covid_data import CovidDataProcessor, SCOPE_WORLD, STAT_CONFIRMED, STAT_DEATHS, STAT_RECOVERED, STAT_ACTIVE
from tab_common import get_time_series_scatter_chart
from tab_world import get_choropleth_mapbox_world

supported_stats = [STAT_CONFIRMED, STAT_DEATHS, STAT_RECOVERED]

# =============================================================================
# Dash App and Flask Server
# =============================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

dataproc = CovidDataProcessor()

map = dcc.Graph(
    id='id-outbreak-map',
    figure=get_choropleth_mapbox_world(dataproc, logger=app.logger),
    responsive=True,
)

def get_location_options():
    df = dataproc.get_df_confirmed_by_date_world()
    options = [{'label': i, 'value': i} for i in df.index]
    return options

def get_location_selector():
    return dbc.FormGroup(
        [
            dbc.Label('Select up to 5 locations to compare'),
            dcc.Dropdown(
                id='id-loc-dropdown',
                options=get_location_options(),
                value=['Worldwide'],
                multi=True
            ),
        ]
    )


def get_outbreak_chart(id):
    return dcc.Graph(
        id=id,
        responsive=False)

stat_to_color_map = {
    STAT_CONFIRMED: 'warning',
    STAT_RECOVERED: 'success',
    STAT_DEATHS: 'danger',
    STAT_ACTIVE: 'info'
}

def get_stat_button_id(stat):
    return f'id-button-{stat.lower()}'

def get_stat_collapse_id(stat):
    return f'id-collapse-{stat.lower()}'

def get_stat_chart_id(stat):
    return f'id-chart-{stat.lower()}'

def get_stat_card(scope, stat):
    button_id = get_stat_button_id(stat)
    collapse_id = get_stat_collapse_id(stat)
    chart_id = get_stat_chart_id(stat)
    return dbc.Card(
        dbc.CardBody(
            [
                dbc.Button(
                    id=button_id,
                    children=[stat,
                              dbc.Badge(f'{dataproc.get_total_stat(scope, stat):,}',
                                        color='light',
                                        className="ml-1")],
                    size='lg',
                    color=stat_to_color_map.get(stat)
                ),
                dbc.Collapse(
                    get_outbreak_chart(chart_id),
                    id=collapse_id,
                ),
            ]
        )
    )


def serve_layout():
    layout = dbc.Container(
        [
            html.H1("My Dashboard"),
            html.Hr(),
            dbc.Row([dbc.Col(get_stat_card(SCOPE_WORLD, x), sm=12, md=4, lg=4) for x in supported_stats], justify='center'),
            dbc.Row(
                [
                    dbc.Col(
                        [get_location_selector()],
                        sm=9,
                        md=9,
                        lg=9,
                    ),
                ],
                align='center',
                justify='center'
            ),
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                        ]
                    ),
                ],
            ),
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Card([map]),
                                        lg=12
                                    ),
                                ],
                                align='center',
                                justify='center'
                            ),
                        ]
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
    chart_recovered = get_time_series_scatter_chart(dataproc.get_df_recovered_by_date_world(),
                                                locations=locations)
    options = get_location_options()
    if len(locations) == 5:
        options = [x for x in options if x['value'] in locations]
    return [chart_confirmed, chart_deaths, chart_recovered, options]

def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

def register_stat_collapse_callback(stat):
    collapse_id = get_stat_collapse_id(stat)
    button_id = get_stat_button_id(stat)
    output = Output(collapse_id, 'is_open')
    inputs = [Input(button_id, 'n_clicks')]
    states = [State(collapse_id, 'is_open')]
    app.callback(output, inputs, states)(toggle_collapse)

for s in supported_stats:
    register_stat_collapse_callback(s)

# functionality is the same for both dropdowns, so we reuse filter_options
app.callback(
    [Output('id-chart-confirmed', 'figure'),
    Output('id-chart-deaths', 'figure'),
    Output('id-chart-recovered', 'figure'),
    Output('id-loc-dropdown', 'options')],
    [Input('id-loc-dropdown', 'value')])(
    process_time_graph
)


if __name__ == '__main__':
    app.run_server(debug=False, port=8888)
