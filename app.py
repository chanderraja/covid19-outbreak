import dash
import logging
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from covid_data import CovidDataProcessor, SCOPE_WORLD, SCOPE_USA, SCOPE_US_COUNTIES
from covid_data import get_scope_types, get_location_overall
from covid_data import STAT_CONFIRMED, STAT_DEATHS, STAT_RECOVERED, STAT_ACTIVE
from stat_table import get_stat_table

supported_stats = [STAT_CONFIRMED, STAT_DEATHS]

# =============================================================================
# Dash App and Flask Server
# =============================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to logger
app.logger.addHandler(ch)

# widget IDS
ID_DROPDOWN_SCOPE='id-dropdown-scope'
ID_STAT_TABLE_DIV='id-stat-table-div'
ID_STAT_TABLE='id-stat-table'
ID_STAT_CHARTS_DIV='id-stat-charts-div'
ID_RADIOITEMS_STAT='id-radioitems-stat'

dataproc = CovidDataProcessor()

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
                value=get_scope_types()[0],
                clearable=False,
                persistence=True,
            ), width=4
        ),
    ],
    color='light',
    light=True,
)

def get_stat_table_ui():
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    dbc.FormGroup([
                        dbc.Label('Statistic'),
                        dcc.RadioItems(
                            id=ID_RADIOITEMS_STAT,
                            options=[dict(label=x, value=x) for x in supported_stats],
                            value=STAT_CONFIRMED,
                            labelStyle={'display': 'block'},
                            inputStyle={'margin-right': '5px'},
                            persistence=True
                        )
                    ])
                ]
            ),
            dbc.CardBody(id=ID_STAT_TABLE_DIV)
        ],
    )

def get_stat_charts_ui():
    return dbc.Card(
        [
            dbc.CardBody(id=ID_STAT_CHARTS_DIV)
        ],
    )



def serve_layout():
    layout = dbc.Container(
        [
            dashboard,
            html.Hr(),
            dbc.Row([
                dbc.Col(get_stat_table_ui(), lg=6),
                dbc.Col(get_stat_charts_ui(), lg=6)

            ]),
       ], fluid=True,
    )
    return layout


app.layout = serve_layout()


from stat_table import register_stat_table_select_callback, get_stat_table_selected_location_input
from tab_common import get_time_series_scatter_chart
from covid_data import get_value_types

@app.callback(
    Output(ID_STAT_TABLE_DIV, 'children'),
    [Input(ID_DROPDOWN_SCOPE, 'value'),
     Input(ID_RADIOITEMS_STAT, 'value')]
)
def stat_table_callback(scope, stat):
    return get_stat_table(dataproc, scope, stat, table_id=ID_STAT_TABLE)

#register_stat_table_select_callback(app, ID_STAT_TABLE)

@app.callback(
    Output(ID_STAT_CHARTS_DIV, 'children'),
    [Input(ID_DROPDOWN_SCOPE, 'value'),
     Input(ID_RADIOITEMS_STAT, 'value'),
     get_stat_table_selected_location_input(table_id=ID_STAT_TABLE)]
)
def stat_charts_callback(scope, stat, locations):
    figures = [get_time_series_scatter_chart(dataproc.get_stat_by_date_df(scope, stat, value_type=v),
                                             locations, title=v, height=500, width=600)
                for v in get_value_types()]
    charts = [dcc.Graph(figure=f) for f in figures]
    return charts

if __name__ == '__main__':
    app.run_server(debug=False, port=8765)
