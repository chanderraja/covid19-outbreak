import os
from covid_data import CovidDataProcessor, SCOPE_WORLD, CSSE_DAILY_COL_CONFIRMED, CSSE_DAILY_COL_HOVERTEXT
from plotutils import get_choropleth_mapbox


def get_choropleth_mapbox_world(dataproc: CovidDataProcessor, logger):
    mapbox_access_token = os.environ.get('MAPBOX_TOKEN')
    geojson = dataproc.get_geojson(scope=SCOPE_WORLD)
    df = dataproc.get_df_daily_report(scope=SCOPE_WORLD)
    locations = []
    cases = []
    text = []
    for feat in geojson['features']:
        country = feat['properties']['name']
        if country not in df.index:
            if logger is not None:
                logger.info(f'{country} not found in dataset')
            continue
        row = df.loc[country]
        if row[CSSE_DAILY_COL_CONFIRMED] != 0:
            locations.append(country)
            cases.append(row[CSSE_DAILY_COL_CONFIRMED])
            text.append(row[CSSE_DAILY_COL_HOVERTEXT])

    featureid_key = 'properties.name'
    bvals = [1, 10, 100, 1000, 10000, 100000, 1000000, 10000000]

    fig = get_choropleth_mapbox(geojson=dataproc.get_geojson(scope=SCOPE_WORLD),
                                locations=locations,
                                z=cases,
                                color_boundaries = bvals,
                                color_min = '#ffffcc',
                                color_max = '#8b0000',
                                hovertext=text,
                                mapbox_token=mapbox_access_token,
                                logarithmic=True,
                                featureid_key=featureid_key)
    return fig

