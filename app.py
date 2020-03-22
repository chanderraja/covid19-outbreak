import os
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import io
import requests

COL_PROVINCE_STATE='Province/State'
COL_STATE='State'
COL_COUNTRY_REGION='Country/Region'
COL_COUNTRY='Country'
COL_LATITUDE='Latitude'
COL_LONGITUDE='Longitude'


url='https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/03-21-2020.csv'
s=requests.get(url).content
df=pd.read_csv(io.StringIO(s.decode('utf-8')))
# clean up column names
df =  df.rename(columns={COL_PROVINCE_STATE: COL_STATE, COL_COUNTRY_REGION: COL_COUNTRY})


def get_location(row):
    state = row[COL_STATE]
    country = row[COL_COUNTRY]
    if pd.isna(state):
        return country
    return state + '<br>' + country

def get_hovertext(row):
    return get_location(row) + '<br>' + 'Confirmed = ' + str(row['Confirmed']) + \
           '<br>' + 'Deaths = ' + str(row['Deaths']) + '<br>' + 'Recovered =' + str(row['Recovered'])

df['hovertext'] = df.apply(lambda row: get_hovertext(row), axis=1)



external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
mapbox_access_token = os.environ.get('MAPBOX_TOKEN')
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

def get_location_suggestions():
    suggestions = df[COL_COUNTRY].unique().tolist()
    suggestions += df[COL_STATE].fillna('').unique().tolist()
    suggestions = sorted(suggestions)
    return suggestions



DEFAULT_LATITUDE=38.92
DEFAULT_LONGITUDE=-77.07
DEFAULT_ZOOM=2


def get_latlong_and_zoom(location):
    if location is not None and location is not '':
        rows = df[df.Country == location]
        if rows.shape[0] == 0:
            rows = df[df.State == location]

        if rows.shape[0] != 0:
            row = rows.iloc[0]
            return row[COL_LATITUDE], row[COL_LONGITUDE], 4
    return DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_ZOOM


def get_mapbox(center_latitude, center_longitude, zoom):
    datamap =  dict(
        type='scattermapbox',
        lat=df['Latitude'],
        lon=df['Longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=df['Confirmed'],
            sizeref=2.*df['Confirmed'].values.max()/(100**2),
            sizemode='area',
            color='rgb(180,0,0)',
        ),
        text=df['hovertext']
    )
    layout = dict(
        autosize=True,
        hovermode='closest',
        geo = dict(
            projection = dict(
                type = 'equirectangular'
            ),
        ),
        mapbox=dict(
            style='light',
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=center_latitude,
                lon=center_longitude
            ),
            pitch=0,
            zoom=zoom
        ),
    )

    fig = dict(
        data=[datamap],
        layout=layout
    )
    return fig


def serve_layout():
    return html.Div(
        [
            html.H4(
                'COVID-19 Outbreak Dashboard',
                style={
                    'color': 'blue',
                    'font-style': 'italic',
                    'font-weight': 'bold',
                    'height': '50px',
                    'display': 'block',
                    'text-align': 'center',
                    'left-margin': 'auto',
                    'right-margin': 'auto'
                }
            ),
            html.Datalist(
                id='id-list-suggested-inputs',
                children=[html.Option(value=word) for word in get_location_suggestions()]
            ),
            dcc.Input(id='id-input-loc',
                      type='text',
                      list='id-list-suggested-inputs',
                      value=''
                      ),
            dcc.Loading(
                id='id-loading',
                children=[
                    html.Div(
                        dcc.Graph(
                            id='id-mapbox',
                            figure={}
                        ),
                        id='id-map-container'
                    ),
                ],
                type='circle'
            ),
        ]
    )


app.layout = serve_layout()

@app.callback(
    Output('id-mapbox', 'figure'),
    [Input('id-input-loc', 'value')]
)
def location_selected(location):
    lat, long, zoom = get_latlong_and_zoom(location)
    app.logger.warning(f'location={location}, lat={lat}, long={long}, zoom={zoom}')
    return get_mapbox(lat, long, zoom)

if __name__ == '__main__':
    app.run_server(debug=True)
