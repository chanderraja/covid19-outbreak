import os
import dash_html_components as html
import dash_core_components as dcc
import dash_admin_components as dac
import covid_data as data
from covid_data import CovidDataProcessor, SCOPE_USA, SCOPE_US_COUNTIES
from covid_data import CSSE_DAILY_COL_CONFIRMED, CSSE_DAILY_COL_FIPS, CSSE_DAILY_COL_HOVERTEXT
from tab_common import get_status_boxes
from plotutils import get_choropleth_mapbox


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
                                color_max = '#654321',
                                hovertext=df_positive[CSSE_DAILY_COL_HOVERTEXT],
                                mapbox_token=mapbox_access_token,
                                logarithmic = True)
    return fig
