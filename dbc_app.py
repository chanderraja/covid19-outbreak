import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from covid_data import CovidDataProcessor, SCOPE_WORLD, SCOPE_USA, SCOPE_US_COUNTIES
from covid_data import get_scope_types, get_location_overall
from covid_data import STAT_CONFIRMED, STAT_DEATHS, STAT_RECOVERED, STAT_ACTIVE
from covid_data import GRANULARITY_ABSOLUTE, GRANULARITY_PER_CAPITA
from tab_common import get_time_series_scatter_chart, get_top_locations_bar_chart
from tab_common import VALUE_TYPE_CUMULATIVE, VALUE_TYPE_DAILY_DIFF, VALUE_TYPE_DAILY_PERCENT_CHANGE

from tab_world import get_choropleth_mapbox_world
from tab_usa import get_choropleth_mapbox_usa
from tab_us_counties import get_choropleth_mapbox_us_counties

supported_stats = [STAT_CONFIRMED, STAT_DEATHS]

# =============================================================================
# Dash App and Flask Server
# =============================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server

# widget IDS
MAX_COMPARE_LOCS=5
NUM_LOCATIONS_TRENDING=10
ID_DROPDOWN_SCOPE='id-dropdown-scope'
ID_DROPDOWN_LOC= 'id-dropdown-loc'
ID_DROPDOWN_LOC_DIV= ID_DROPDOWN_LOC + '-div'
ID_COLLAPSE_LOC='id-collapse-loc'
ID_BUTTON_SELECT_TOP_CONFIRMED= 'id-button-select-top-confirmed'
ID_BUTTON_SELECT_TOP_DEATHS= 'id-button-select-top-deaths'
ID_RADIOITEMS_TIMECHART_SETTINGS='id-radioitems-timechart-settings'
ID_STAT_HEADER_COL_CONFIRMED= 'id-stat-col-confirmed'
ID_STAT_HEADER_COL_DEATHS= 'id-stat-col-deaths'
ID_STAT_HEADER_COL_RECOVERED= 'id-stat-col-recovered'
ID_MAPBOX='id-mapbox'

stat_header_col_id_to_stat_map = {
    ID_STAT_HEADER_COL_CONFIRMED: STAT_CONFIRMED,
    ID_STAT_HEADER_COL_DEATHS: STAT_DEATHS,
    ID_STAT_HEADER_COL_RECOVERED: STAT_RECOVERED
}
def make_reverse_lookup(fwd_lookup):
    rev_lookup = {}
    for key in fwd_lookup:
        val = fwd_lookup[key]
        rev_lookup[val] = key
    return rev_lookup

# make reverse lookups
stat_to_stat_header_col_id_map = make_reverse_lookup(stat_header_col_id_to_stat_map)

dataproc = CovidDataProcessor()

stat_to_color_map = {
    STAT_CONFIRMED: 'warning',
    STAT_RECOVERED: 'success',
    STAT_DEATHS: 'danger',
    STAT_ACTIVE: 'info'
}

def get_map(scope):
    if scope == SCOPE_WORLD:
        map = get_choropleth_mapbox_world(dataproc, logger=app.logger)
    elif scope == SCOPE_USA:
        map = get_choropleth_mapbox_usa(dataproc, logger=app.logger)
    elif scope== SCOPE_US_COUNTIES:
        map = get_choropleth_mapbox_us_counties(dataproc, logger=app.logger)
    else:
        return None
    return map


def get_location_options(scope):
    granularity = GRANULARITY_PER_CAPITA if scope == SCOPE_WORLD else GRANULARITY_ABSOLUTE
    df = dataproc.get_stat_by_date_df(scope, stat=STAT_CONFIRMED, granularity=granularity)
    options = [{'label': i, 'value': i} for i in df.columns]
    return options

def get_chart_controls(scope):
    return dbc.Collapse(
        [
            dbc.Card(
                dbc.CardHeader(
                [
                    dbc.Label(f'Select up to {MAX_COMPARE_LOCS} locations to compare'),
                    html.Div(dcc.Dropdown(id=ID_DROPDOWN_LOC), id=ID_DROPDOWN_LOC_DIV),
                    html.Br(),
                    dbc.FormGroup([
                        dbc.Label('Time Chart Settings'),
                        dcc.RadioItems(
                            id=ID_RADIOITEMS_TIMECHART_SETTINGS,
                            options=[
                                dict(label='Cumulative', value=VALUE_TYPE_CUMULATIVE),
                                dict(label='Daily change (absolute)', value=VALUE_TYPE_DAILY_DIFF),
                                dict(label='Daily change (percentage)', value=VALUE_TYPE_DAILY_PERCENT_CHANGE)
                            ],
                            value = VALUE_TYPE_CUMULATIVE,
                            labelStyle={'display': 'block'},
                            inputStyle={'margin-right': '5px'},
                            persistence=True
                        )
                    ])
                ])
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


def get_stat_header_col_text(scope, stat, value_type=VALUE_TYPE_CUMULATIVE):
    # get overall stats
    value, diff, pct_change = dataproc.get_latest_stat(stat, scope)
    diff_arrow = lambda diff: f'\u21e7' if diff > 0 else f'\u21e9'
    arrow = diff_arrow(diff)
    formatted_value = f'{value:,} {stat}'
    formatted_diff = f'{diff:+,.0f} ({pct_change:+.2f}%) {arrow} past 24h'
    col1 = dbc.Col([
        html.H2(f'{formatted_value}', className='alert-heading'),
        html.H4(f'{formatted_diff}'),
    ], width=4)
    # add 2 rows per col, max 2 cols
    rows_per_col = 1
    max_cols = 6
    n = rows_per_col * max_cols
    df = dataproc.get_top_locations(scope, stat, value_type=value_type, n=n)
    locs = list(df.index)

    textlist = []
    num_cols = 0
    num_rows = 0
    col2_subcols = []
    for loc in locs:
        value, diff, pct_change = dataproc.get_latest_stat(stat, scope, loc=loc)
        arrow = diff_arrow(diff)
        formatted_loc = f'{loc}'
        formatted_value = f'{value:,}'
        formatted_diff = f'{diff:+,.0f} ({pct_change:+.2f}%) {arrow}'
        textlist.append(html.H6(formatted_loc))
        textlist.append(html.H6(formatted_value))
        textlist.append(html.P(formatted_diff))
        num_rows += 1
        if num_rows == rows_per_col:
            col2_subcols.append(dbc.Col([x for x  in textlist]))
            textlist.clear()
            num_rows = 0
            num_cols += 1
            if num_cols == max_cols:
                break

    col2 = dbc.Col(dbc.Row(col2_subcols))
    return dbc.Row([col1, col2])

def get_stat_card(scope, stat, value_type=VALUE_TYPE_CUMULATIVE):
    button_id = get_stat_button_id(stat)
    collapse_id = get_stat_collapse_id(stat)
    time_chart_obj = dcc.Graph(id=get_stat_over_time_chart_id(stat))
    top_n_chart_obj = dcc.Graph(id=get_top_n_chart_id(stat))
    chart = dcc.Loading(dbc.Row([dbc.Col(time_chart_obj, sm=12, lg=6), dbc.Col(top_n_chart_obj, sm=12, lg=6)]))

    return dbc.Card([
        dbc.CardHeader(
            dbc.Alert(
                dbc.Row([
                    dbc.Col(id=stat_to_stat_header_col_id_map[stat], width=11),
                    dbc.Col([
                        dbc.Button('Expand', id=button_id)
                    ], align='end')
                ]),  color=stat_to_color_map.get(stat)
            ),
        ),
        dbc.Collapse(dbc.CardBody([chart]), id=collapse_id, is_open=False)
    ])


def get_stat_charts_ui(scope, value_type=VALUE_TYPE_CUMULATIVE):
    ui =    \
    [
        dbc.Row([
            dbc.Col(get_chart_controls(scope))],
            align='center',
            justify='left'
        )
    ]

    cols = lambda scope, stat, value_type: dbc.Col(get_stat_card(scope, stat, value_type))

    ui += \
    [
        dbc.Row(cols(scope, x, value_type), justify='left') for x in supported_stats
    ]
    return ui


dbc.Label(f'Select Scope'),

dashboard = dbc.Navbar(
    [
        dbc.Col(dbc.NavbarBrand("Dashboard", href="#"), sm=3, md=4),
        dbc.Col(
            dbc.Nav(dbc.NavItem(dbc.NavLink('Select Scope')), navbar=True),
            width='auto',
        ),
        dbc.Col(
            dcc.Dropdown(
                id=ID_DROPDOWN_SCOPE,
                options=[{'label': i, 'value': i} for i in get_scope_types()],
                value=SCOPE_WORLD,
                clearable=False,
                persistence=True,
            ), width=4
        ),
    ],
    color='light',
    light=True,
)


def serve_layout():
    scope = SCOPE_WORLD
    layout = dbc.Container(
        [
            dashboard,
            html.Hr(),
            dbc.Row([
                dbc.Col(get_stat_charts_ui(scope), lg=12)
            ]),
            dbc.Row([
                dbc.Col(dbc.Card([dcc.Loading(dcc.Graph(id=ID_MAPBOX))]), lg=8),
            ], align='center', justify='center'),
        ], fluid=True,
    )
    return layout


app.layout = serve_layout()

search_bar = dbc.Row(
    [
        dbc.Col(dbc.Input(type="search", placeholder="Search")),
        dbc.Col(
            dbc.Button("Search", color="primary", className="ml-2"),
            width="auto",
        ),
    ],
    no_gutters=True,
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)


def stat_header_callback(scope):
    ctx = dash.callback_context
    output_id = ctx.outputs_list['id']
    stat = stat_header_col_id_to_stat_map[output_id]
    return get_stat_header_col_text(scope, stat)

def register_stat_header_col_update_callback(stat):
    output = Output(stat_to_stat_header_col_id_map[stat], 'children')
    inputs = [Input(ID_DROPDOWN_SCOPE, 'value')]
    app.callback(output, inputs)(stat_header_callback)

for stat in supported_stats:
    register_stat_header_col_update_callback(stat)

def toggle_collapse_callback(n, is_open):
    button_text = lambda open: 'collapse' if open else 'expand'
    if n:
        return [not is_open, button_text(not is_open)]
    return [is_open, button_text(is_open)]

def register_stat_collapse_callback(stat):
    output = [Output(get_stat_collapse_id(stat), 'is_open'), Output(get_stat_button_id(stat), 'children')]
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

@app.callback(
    Output(ID_DROPDOWN_LOC_DIV, 'children'),
    [Input(ID_DROPDOWN_SCOPE, 'value')],
    [State(ID_RADIOITEMS_TIMECHART_SETTINGS, 'value')]
)
def show_dropdown(scope, value_type):
    locs = dataproc.get_all_locations(scope)
    options = [{'label': v, 'value': v} for v in locs]
    df = dataproc.get_top_locations(scope, stat, value_type=value_type, n=MAX_COMPARE_LOCS)
    selected_locs = list(df.index)
    return dcc.Dropdown(
        id=ID_DROPDOWN_LOC,
        options=options,
        value=selected_locs,
        multi=True,
        persistence_type='local',
        persistence=scope
    )

'''
def process_location_dropdown_options(locations, scope):
    options = get_location_options(scope)
    if locations is not None and len(locations) == MAX_COMPARE_LOCS:
        options = [x for x in options if x['value'] in locations]
    return [options]

def register_location_dropdown_options_callback():
    outputs = [Output(ID_DROPDOWN_LOC, 'options')]
    inputs = [Input(ID_DROPDOWN_LOC, 'value'),
              Input(ID_DROPDOWN_SCOPE, 'value')]
    app.callback(outputs, inputs)(process_location_dropdown_options)

register_location_dropdown_options_callback()


def select_top_locations_button_callback(sel_top_confirmed, sel_top_deaths, scope, value_type):
    if not sel_top_confirmed and not sel_top_deaths:
        raise PreventUpdate
    ctx = dash.callback_context
    triggered_input = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_input != ID_BUTTON_SELECT_TOP_CONFIRMED and triggered_input != ID_BUTTON_SELECT_TOP_DEATHS:
        raise PreventUpdate
    stat = STAT_CONFIRMED
    if triggered_input == ID_BUTTON_SELECT_TOP_DEATHS:
        stat = STAT_DEATHS
    df = dataproc.get_top_locations(scope, stat, value_type=value_type, n=MAX_COMPARE_LOCS)
    locs = list(df.index)
    return locs

def register_select_top_locations_callback():
    outputs = Output(ID_DROPDOWN_LOC, 'value')
    inputs =  [
        Input(ID_BUTTON_SELECT_TOP_CONFIRMED, 'n_clicks'),
        Input(ID_BUTTON_SELECT_TOP_DEATHS, 'n_clicks')]
    states = [
        State(ID_DROPDOWN_SCOPE, 'value'),
        State(ID_RADIOITEMS_TIMECHART_SETTINGS, 'value')]
    app.callback(outputs, inputs, states)(select_top_locations_button_callback)

register_select_top_locations_callback()
'''
def process_by_date_charts(locations, value_type, is_open, scope):
    ctx = dash.callback_context
    inputs = list(ctx.inputs)
    collapse_id = inputs[2].split('.')[0]
    stat = get_stat_from_collapse_id(collapse_id)
    return [get_time_series_scatter_chart(dataproc.get_stat_by_date_df(scope, stat, value_type=value_type), locations),
            get_top_locations_bar_chart(dataproc.get_top_locations(scope, stat, value_type=value_type, n=NUM_LOCATIONS_TRENDING), stat)]

def register_by_date_charts_callback(stat):
    outputs = [Output(get_stat_over_time_chart_id(stat), 'figure'),
               Output(get_top_n_chart_id(stat), 'figure')]
    inputs = [Input(ID_DROPDOWN_LOC, 'value')]
    inputs += [Input(ID_RADIOITEMS_TIMECHART_SETTINGS, 'value')]
    inputs += [Input(get_stat_collapse_id(stat), 'is_open')]
    inputs += [Input(ID_DROPDOWN_SCOPE, 'value')]
    app.callback(outputs, inputs)(process_by_date_charts)

for stat in supported_stats:
    register_by_date_charts_callback(stat)


@app.callback(
    Output(ID_MAPBOX, 'figure'),
    [Input(ID_DROPDOWN_SCOPE, 'value')]
)
def map_callback(scope):
    return get_map(scope)


if __name__ == '__main__':
    app.run_server(debug=False, port=8888)


'''
                    
                    dbc.Button(
                        f'Click to compare the top {MAX_COMPARE_LOCS} locations for Covid-19 confirmed cases',
                        id=ID_BUTTON_SELECT_TOP_CONFIRMED,
                        size='lg',
                        color='primary',
                        block=True
                    ),
                    dbc.Button(
                        f'Click to compare the top {MAX_COMPARE_LOCS} locations for Covid-19 deaths',
                        id=ID_BUTTON_SELECT_TOP_DEATHS,
                        size='lg',
                        color='primary',
                        block=True
                    ),
                    html.Br(),

'''