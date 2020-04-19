import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from covid_data import CovidDataProcessor, SCOPE_WORLD, SCOPE_USA, SCOPE_US_COUNTIES
from covid_data import STAT_CONFIRMED, STAT_DEATHS, STAT_RECOVERED, STAT_ACTIVE
from covid_data import LOC_WORLD_OVERALL, LOC_USA_OVERALL
from tab_common import get_time_series_scatter_chart, get_top_locations_bar_chart, stat_to_color_map
from tab_world import get_choropleth_mapbox_world
from tab_usa import get_choropleth_mapbox_usa
from tab_us_counties import get_choropleth_mapbox_us_counties

supported_stats = [STAT_CONFIRMED, STAT_DEATHS, STAT_RECOVERED]

# =============================================================================
# Dash App and Flask Server
# =============================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# widget IDS
MAX_COMPARE_LOCS=5
ID_DROPDOWN_LOC='id-dropdown-loc'
ID_COLLAPSE_LOC='id-collapse-loc'
ID_BUTTON_SELECT_TOP_CONFIRMED= 'id-button-select-top-confirmed'
ID_BUTTON_SELECT_TOP_DEATHS= 'id-button-select-top-deaths'
ID_DIV_SCOPE='id-div-scope'

dataproc = CovidDataProcessor()

def get_map(scope):
    if scope == SCOPE_WORLD:
        map = get_choropleth_mapbox_world(dataproc, logger=app.logger)
    elif scope == SCOPE_USA:
        map = get_choropleth_mapbox_usa(dataproc, logger=app.logger)
    elif scope== SCOPE_US_COUNTIES:
        map = get_choropleth_mapbox_us_counties(dataproc, logger=app.logger)
    else:
        return None
    graph = dcc.Graph(
        id='id-outbreak-map',
        figure=map,
        responsive=True,
    )
    return graph

def get_location_options(scope):
    df = dataproc.get_stat_by_date_df(scope, STAT_CONFIRMED)
    options = [{'label': i, 'value': i} for i in df.index]
    return options

def get_location_overall(scope):
    if scope == SCOPE_WORLD:
        return LOC_WORLD_OVERALL
    elif scope == SCOPE_USA:
        return LOC_USA_OVERALL
    elif scope == SCOPE_US_COUNTIES:
        return LOC_USA_OVERALL
    return 'Not implemented'

def get_location_selector(scope):
    return dbc.Collapse(
        [
            dbc.FormGroup(
                [
                    dbc.Label(f'Select up to {MAX_COMPARE_LOCS} locations to compare'),
                    dcc.Dropdown(
                        id=ID_DROPDOWN_LOC,
                        options=get_location_options(scope),
                        value=[get_location_overall(scope)],
                        multi=True,
                        persistence=True
                    ),
                    html.Br(),
                    dbc.FormGroup([
                        dbc.Button(
                            f'Click to select the top {MAX_COMPARE_LOCS} locations in confirmed cases',
                            id=ID_BUTTON_SELECT_TOP_CONFIRMED
                        ),
                        dbc.Button(
                            f'Click to compare the top {MAX_COMPARE_LOCS} locations in deaths',
                            id=ID_BUTTON_SELECT_TOP_DEATHS
                        ),
                    ], className='row')
                ]
            )
        ],
        id=ID_COLLAPSE_LOC
    )


def get_stat_button_id(stat):
    return f'id-button-{stat}'

def get_stat_collapse_id(stat):
    return f'id-collapse-{stat}'

def get_stat_from_collapse_id(id):
    return id.lstrip('id-collapse-')

def get_stat_over_time_chart_id(stat):
    return f'id-stat-over-time-chart-{stat}'

def get_top_n_chart_id(stat):
    return f'id-stat-top-n-chart-{stat}'

def get_stat_card(scope, stat):
    button_id = get_stat_button_id(stat)
    collapse_id = get_stat_collapse_id(stat)
    time_chart_obj = dcc.Graph(id=get_stat_over_time_chart_id(stat))
    top_n_chart_obj = dcc.Graph(
        id=get_top_n_chart_id(stat),
        figure=get_top_locations_bar_chart(dataproc.get_top_locations(scope, stat, 10), stat)
    )
    chart = dcc.Loading(dbc.Row([dbc.Col(time_chart_obj), dbc.Col(top_n_chart_obj)]))
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

def get_stat_charts_ui(scope):
    ui =    \
    [
        dbc.Row([dbc.Col(get_location_selector(scope))],
            align='center',
            justify='left'
        )
    ]

    cols = lambda scope, stat: dbc.Col(get_stat_card(scope, stat))

    ui += \
    [
        dbc.Row(cols(scope, x), justify='left') for x in supported_stats
    ]
    return ui

def serve_layout():
    scope = SCOPE_WORLD
    layout = dbc.Container(
        [
            html.H1("My Dashboard"),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(get_stat_charts_ui(scope), lg=12),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dbc.Card([get_map(scope)]), lg=12),
                ],
                align='center',
                justify='center'
            ),
            html.Div(id=ID_DIV_SCOPE, children=scope, style={'display': 'none'}),
        ], fluid=True,
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
    outputs = Output(ID_COLLAPSE_LOC, 'is_open')
    inputs = [Input(get_stat_collapse_id(s), 'is_open') for s in supported_stats]
    app.callback(outputs, inputs)(toggle_collapse_controls_callabck)

register_collapse_controls_callback()

def process_location_dropdown_options(locations, scope):
    options = get_location_options(scope)
    if len(locations) == MAX_COMPARE_LOCS:
        options = [x for x in options if x['value'] in locations]
    return [options]

def register_location_dropdown_options_callback():
    outputs = [Output(ID_DROPDOWN_LOC, 'options')]
    inputs = [Input(ID_DROPDOWN_LOC, 'value'),
              Input(ID_DIV_SCOPE, 'children')]
    app.callback(outputs, inputs)(process_location_dropdown_options)

register_location_dropdown_options_callback()

@app.callback(
    Output(ID_DROPDOWN_LOC, 'value'),
    [Input(ID_BUTTON_SELECT_TOP_CONFIRMED, 'n_clicks'),
     Input(ID_BUTTON_SELECT_TOP_DEATHS, 'n_clicks'),
     Input(ID_DIV_SCOPE, 'children')]
)
def select_top_locations_button_callback(sel_top_confirmed, sel_top_deaths, scope):
    if not sel_top_confirmed and not sel_top_deaths:
        raise PreventUpdate
    ctx = dash.callback_context
    input = ctx.triggered[0]['prop_id'].split('.')[0]
    stat = STAT_CONFIRMED if input == ID_BUTTON_SELECT_TOP_CONFIRMED else STAT_DEATHS
    df = dataproc.get_top_locations(scope, stat, n=MAX_COMPARE_LOCS)
    locs = list(df.index)
    return locs


def process_by_date_charts(locations, is_open, scope):
    ctx = dash.callback_context
    inputs = list(ctx.inputs)
    collapse_id = inputs[1].split('.')[0]
    stat = get_stat_from_collapse_id(collapse_id)
    if is_open:
        return [get_time_series_scatter_chart(dataproc.get_stat_by_date_df(scope, stat), locations)]
    else:
        raise PreventUpdate

def register_by_date_charts_callback(stat):
    outputs = [Output(get_stat_over_time_chart_id(stat), 'figure')]
    inputs = [Input(ID_DROPDOWN_LOC, 'value')]
    inputs += [Input(get_stat_collapse_id(stat), 'is_open')]
    inputs += [Input(ID_DIV_SCOPE, 'children')]
    app.callback(outputs, inputs)(process_by_date_charts)

for s in supported_stats:
    register_by_date_charts_callback(s)


if __name__ == '__main__':
    app.run_server(debug=False, port=8888)
