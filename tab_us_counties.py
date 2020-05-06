import os
from covid_data import CovidDataProcessor, SCOPE_USA, SCOPE_US_COUNTIES
from covid_data import CSSE_DAILY_COL_CONFIRMED, CSSE_DAILY_COL_FIPS, CSSE_DAILY_COL_HOVERTEXT
from plotutils import get_choropleth_mapbox
import plotly.express as px


def get_choropleth_mapbox_us_counties(dataproc: CovidDataProcessor, logger):
    mapbox_access_token = os.environ.get('MAPBOX_TOKEN')
    geojson = dataproc.get_geojson(scope=SCOPE_US_COUNTIES)
    df = dataproc.get_df_daily_report(scope=SCOPE_US_COUNTIES)
    bvals = [1, 10, 100, 1000, 10000, 100000]
    df_positive = df[df[CSSE_DAILY_COL_CONFIRMED] != 0]
    fig = get_choropleth_mapbox(geojson=geojson,
                                locations=df_positive.index,
                                z=df_positive[CSSE_DAILY_COL_CONFIRMED],
                                color_boundaries = bvals,
                                color_min = '#ffffcc',
                                color_max = '#8b0000',
                                hovertext=df_positive[CSSE_DAILY_COL_HOVERTEXT],
                                mapbox_token=mapbox_access_token,
                                logarithmic = True,
                                logger=logger)

    '''
    fig = px.choropleth_mapbox(df, geojson=geojson, locations=df_positive.index, color=df_positive[CSSE_DAILY_COL_CONFIRMED],
                               color_continuous_scale="Viridis",
                               #range_color=(0, 12),
                               mapbox_style="carto-positron",
                               zoom=3, center={"lat": 37.0902, "lon": -95.7129},
                               opacity=0.5,
                               #labels={'unemp': 'unemployment rate'}
                               )
    '''
    return fig
