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

graph = dcc.Graph(
            id='id-outbreak-graph',
            figure=get_time_series_scatter_chart(dataproc.get_df_confirmed_by_date_world(),
                                                 locations=['United States of America', 'China'])
)

def get_location_dropdown_options():
    df = dataproc.get_df_confirmed_by_date_world()
    options = [{'label': i, 'value': i} for i in df.index]
    return options

def get_chart(df):
    controls = dbc.Card(
        [
            dbc.FormGroup(
                [
                    dbc.Label('Select locations to compare'),
                    dcc.Dropdown(
                        id='id-loc-dropdown',
                        options=get_location_dropdown_options(),
                        value=['United States of America', 'Italy'],
                        multi=True
                    ),
                    graph
                ]
            ),
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
                                get_chart(dataproc.get_df_daily_report(scope=SCOPE_WORLD)),
                                lg=8,
                            ),
                        ],
                        align='center'
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
    chart = get_time_series_scatter_chart(dataproc.get_df_confirmed_by_date_world(),
                                                locations=locations)
    options = get_location_dropdown_options()
    if len(locations) == 5:
        options = [x for x in options if x['value'] in locations]
    return [chart, options]


# functionality is the same for both dropdowns, so we reuse filter_options
app.callback([Output('id-outbreak-graph', 'figure'),
              Output('id-loc-dropdown', 'options')],
             [Input('id-loc-dropdown', 'value')])(
    process_time_graph
)


if __name__ == '__main__':
    app.run_server(debug=False, port=8888)
