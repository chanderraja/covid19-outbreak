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

# widget IDS
MAX_COMPARE_LOCS=5
ID_DROPDOWN_LOC='id-dropdown-loc'

LOC_WORLDWIDE='Worldwide'

dataproc = CovidDataProcessor()

map = dcc.Graph(
    id='id-outbreak-map',
    figure=get_choropleth_mapbox_world(dataproc, logger=app.logger),
    responsive=True,
)

def get_location_options():
    df = dataproc.get_stat_by_date_df(SCOPE_WORLD, STAT_CONFIRMED)
    options = [{'label': i, 'value': i} for i in df.index]
    return options

def get_location_selector():
    return dbc.Collapse(
        [
            dbc.FormGroup(
                [
                    dbc.Label(f'Select up to {MAX_COMPARE_LOCS} locations to compare'),
                    dcc.Dropdown(
                        id=ID_DROPDOWN_LOC,
                        options=get_location_options(),
                        value=[LOC_WORLDWIDE],
                        multi=True,
                        persistence=True
                    ),
                ]
            )
        ],
        id='id-collapse-loc'
    )


def get_outbreak_chart(id):
    return dcc.Graph(
        id=id,
        responsive=True)

stat_to_color_map = {
    STAT_CONFIRMED: 'warning',
    STAT_RECOVERED: 'success',
    STAT_DEATHS: 'danger',
    STAT_ACTIVE: 'info'
}

def get_stat_button_id(stat):
    return f'id-button-{stat}'

def get_stat_collapse_id(stat):
    return f'id-collapse-{stat}'

def get_stat_from_collapse_id(id):
    return id.lstrip('id-collapse-')

def get_stat_chart_id(stat):
    return f'id-chart-{stat}'

def get_stat_card(scope, stat):
    button_id = get_stat_button_id(stat)
    collapse_id = get_stat_collapse_id(stat)
    chart_id = get_stat_chart_id(stat)
    chart_obj = dcc.Graph(id=chart_id)
    chart = dcc.Loading(dbc.Row([dbc.Col(chart_obj)]))
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        id=button_id,
                        children=[
                            stat,
                            dbc.Badge(f'{dataproc.get_total_stat(scope, stat):,}', color='light', className="ml-1")
                        ], size='lg', color=stat_to_color_map.get(stat)
                    )
                ], width=2)
            ])
        ]),
        dbc.Collapse(dbc.CardBody([chart]), id=collapse_id, is_open=False)
    ])

def get_stat_charts_ui():
    ui =    \
    [
        dbc.Row([dbc.Col(get_location_selector(), md=8)],
            align='center',
            justify='left'
        )
    ]

    ui += \
    [
        dbc.Row(dbc.Col(get_stat_card(SCOPE_WORLD, x), md=8), justify='left') for x in supported_stats
    ]
    return ui

def serve_layout():
    layout = dbc.Container(
        [
            html.H1("My Dashboard"),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(get_stat_charts_ui(), md=6),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H2('Header')),
                                dbc.CardBody(),
                                dbc.CardFooter('Footer'),
                            ]
                        ),
                        md=6
                    )
                ]
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
        fluid=False,
    )
    return layout


app.layout = serve_layout()

def toggle_collapse_callback(n, is_open):
    if n:
        return not is_open
    return is_open


def register_stat_collapse_callback(stat):
    output = Output(get_stat_collapse_id(stat), 'is_open')
    inputs = [Input(get_stat_button_id(stat), 'n_clicks')]
    states = [State(get_stat_collapse_id(stat), 'is_open')]
    app.callback(output, inputs, states)(toggle_collapse_callback)

for s in supported_stats:
    register_stat_collapse_callback(s)

def toggle_collapse_controls_callabck(*args):
    return True if any(args) else False

def register_collapse_controls_callback():
    outputs = Output('id-collapse-loc', 'is_open')
    inputs = [Input(get_stat_collapse_id(s), 'is_open') for s in supported_stats]
    app.callback(outputs, inputs)(toggle_collapse_controls_callabck)

register_collapse_controls_callback()

def process_location_dropdown_options(locations):
    options = get_location_options()
    if len(locations) == MAX_COMPARE_LOCS:
        options = [x for x in options if x['value'] in locations]
    return [options]

def register_location_dropdown_options_callback():
    outputs = [Output(ID_DROPDOWN_LOC, 'options')]
    inputs = [Input(ID_DROPDOWN_LOC, 'value')]
    app.callback(outputs, inputs)(process_location_dropdown_options)

register_location_dropdown_options_callback()

def process_by_date_charts(locations, is_open):
    ctx = dash.callback_context
    inputs = list(ctx.inputs)
    collapse_id = inputs[1].split('.')[0]
    stat = get_stat_from_collapse_id(collapse_id)
    if is_open:
        return [get_time_series_scatter_chart(dataproc.get_stat_by_date_df(SCOPE_WORLD, stat), locations)]
    else:
        raise PreventUpdate

def register_by_date_charts_callback(stat):
    outputs = [Output(get_stat_chart_id(stat), 'figure')]
    inputs = [Input(ID_DROPDOWN_LOC, 'value')]
    inputs += [Input(get_stat_collapse_id(stat), 'is_open')]
    app.callback(outputs, inputs)(process_by_date_charts)

for s in supported_stats:
    register_by_date_charts_callback(s)


if __name__ == '__main__':
    app.run_server(debug=False, port=8888)
