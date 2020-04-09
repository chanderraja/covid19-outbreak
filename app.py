import os
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_admin_components as dac
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
from plotutils import get_choropleth_mapbox, discrete_colorscale, interpolated_colors
from tab_usa import get_tab_content_usa
from tab_world import get_tab_content_world
import covid_data
from covid_data import SCOPE_WORLD, SCOPE_USA, SCOPE_US_COUNTIES
from covid_data import CSSE_DAILY_COL_CONFIRMED, CSSE_DAILY_COL_DEATHS, CSSE_DAILY_COL_RECOVERED, CSSE_DAILY_COL_ACTIVE
from covid_data import CSSE_DAILY_COL_HOVERTEXT

STAT_CONFIRMED='Confirmed'
STAT_DEATHS='Deaths'
STAT_RECOVERED='Recovered'
STAT_ACTIVE='Active'

dataproc = covid_data.CovidDataProcessor()

external_stylesheets = [dbc.themes.BOOTSTRAP]
mapbox_access_token = os.environ.get('MAPBOX_TOKEN')
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

'''
def get_location_suggestions():
    suggestions = df[COL_COUNTRY_REGION].unique().tolist()
    suggestions += df[COL_PROVINCE_STATE].fillna('').unique().tolist()
    suggestions += df[COL_ADMIN2].fillna('').unique().tolist()
    suggestions = sorted(suggestions)
    return suggestions

location_suggestions = get_location_suggestions()

DEFAULT_LATITUDE=38.92
DEFAULT_LONGITUDE=-77.07
DEFAULT_ZOOM=2


def get_latlong_and_zoom(location):
    if location is not None and location is not '':
        zoom = 4
        rows = df[df[COL_COUNTRY_REGION] == location]
        if rows.shape[0] == 0:
            rows = df[df[COL_PROVINCE_STATE] == location]
            zoom=5
        if rows.shape[0] == 0:
            rows = df[df[COL_ADMIN2] == location]
            zoom = 6
        if rows.shape[0] != 0:
            row = rows.iloc[0]
            return row[COL_LATITUDE], row[COL_LONGITUDE], zoom
    return DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_ZOOM
'''

def get_time_series_scatter_chart(df, locations=None):
    aggregate_sum = df.aggregate('sum')
    x_list = [pd.to_datetime(d).date() for d in aggregate_sum.index]
    data = []
    data.append(go.Scatter(x=x_list,
                           y=aggregate_sum,
                           mode='lines'))
    if locations is not None and isinstance(locations, list):
        for loc in locations:
            if loc not in df.index:
                app.logger.warning(f'Invalid location {loc} passed, skipping....')
                continue
            data.append(go.Scatter(x=x_list,
                               y=df.loc[loc,:],
                               mode='lines',
                               name=loc))
    layout = go.Layout(
        plot_bgcolor='rgba(240,240,255,100)',
        legend=dict(
            x=0.1,
            y=0.7,
            traceorder='normal',
            font=dict(
                size=12, ),
        ),
    )

    fig = go.Figure(data=data, layout=layout)
    return fig

body = dac.Body(
    dac.TabItems([
        get_tab_content_world(dataproc, logger=app.logger),
        get_tab_content_usa(dataproc, logger=app.logger)
    ])
)
sidebar = dac.Sidebar(
    [
        dac.SidebarMenu(
            [
                dac.SidebarHeader(children='Select Outbreak Scope'),
                dac.SidebarMenuItem(id='id-tab-world', label='Worldwide', icon=''),
                dac.SidebarMenuItem(id='id-tab-usa', label='United States', icon=''),
            ]
        ),
    ],
    title='Dashboard',
    skin='light',
    color='primary',
    brand_color='primary',
    src='./assets/virus.png',
    elevation=5,
    opacity=0.8
)

app.layout = dac.Page([sidebar, body])


# =============================================================================
# Callbacks
# =============================================================================
def activate(input_id, n_tab_world, n_tab_usa):
    # Depending on tab which triggered a callback, show/hide contents of app
    if input_id == 'id-tab-world' and n_tab_world:
        return True, False
    elif input_id == 'id-tab-usa' and n_tab_usa:
        return False, True
    else:
        return True, False


@app.callback([Output('id-tab-content-world', 'active'),
               Output('id-tab-content-usa', 'active')],
              [Input('id-tab-world', 'n_clicks'),
               Input('id-tab-usa', 'n_clicks')]
              )
def display_tab(n_tab_world, n_tab_usa):
    ctx = dash.callback_context  # Callback context to recognize which input has been triggered

    # Get id of input which triggered callback
    if not ctx.triggered:
        raise PreventUpdate
    else:
        input_id = ctx.triggered[0]['prop_id'].split('.')[0]

    return activate(input_id, n_tab_world, n_tab_usa)

'''
@app.callback(
    [Output('id-mapbox-world', 'figure'),
     Output('id-dropdown-locations', 'options'),
     Output('id-dropdown-locations', 'value'),
     Output('id-chart-cases-by-date', 'figure')],
    [Input('id-select-scope', 'value')]
)

def update_output_div(scope):
    if scope == SCOPE_WORLD:
        df = dataproc.get_df_confirmed_by_date_world()
        options = [{'label': x, 'value': x} for x in df.index]
        value = df.index[0]
        map = get_choropleth_mapbox_world()
        chart = get_time_series_scatter_chart(df)
    else:
        df = dataproc.get_df_confirmed_by_date_usa()
        options = [{'label': x, 'value': x} for x in df.index]
        value = df.index[0]
        map = get_choropleth_mapbox_us_counties()
        chart = get_time_series_scatter_chart(df)
    return [map, options, value, chart]
'''

if __name__ == '__main__':
    app.run_server(debug=True)
