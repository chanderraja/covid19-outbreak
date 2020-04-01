import numpy as np
import plotly.graph_objects as go

def discrete_colorscale(bvals, colors, ticktext_exp=False):
    """
    bvals - list of values bounding intervals/ranges of interest
    colors - list of rgb or hex colorcodes for values in [bvals[k], bvals[k+1]],0<=k < len(bvals)-1
    ticktext_exp - if True, ticktext must be expressd as 10^bvals[x]
    returns the plotly discrete colorscale
    """
    if len(bvals) != len(colors) + 1:
        raise ValueError('len(boundary values) should be equal to  len(colors)+1')
    bvals = sorted(bvals)
    nvals = [(v - bvals[0]) / (bvals[-1] - bvals[0]) for v in bvals]  # normalized values
    dcolorscale = []  # discrete colorscale
    for k in range(len(colors)):
        dcolorscale.extend([[nvals[k], colors[k]], [nvals[k + 1], colors[k]]])
    bvals = np.array(bvals)
    tickvals = [np.mean(bvals[k:k + 2]) for k in
                range(len(bvals) - 1)]  # position with respect to bvals where ticktext is displayed
    bvals_text = bvals if ticktext_exp == False else [np.power(10,x) for x in bvals]
    bvals_text = np.array(bvals_text)
    ticktext = [f'<{bvals_text[1]:,}'] + [f'{bvals_text[k]:,}-{bvals_text[k + 1]:,}'
                                          for k in range(1, len(bvals_text) - 2)] + [f'>{bvals_text[-2]:,}']
    return dcolorscale, tickvals, ticktext


def get_choropleth_mapbox(geojson, locations, z, hovertext, colorscale,
                          tickvals, ticktext, mapbox_token, featureid_key=None):
    """
    geojson - geojson in dict format
    locations - list of locations matching those in the geoJSON for which data values needs to be plotted
    z - list data values corresponding to the locations
    hovertext - list of hover text to display corresponding each location
    colorscale - color scale
    tickvals - tickvals for the colorscale
    ticktext - tick text to diosplay on the colorscale
    mapbox_token - mapbox API token
    featureid_key - geoJSON key to map to location names instead of the default id
    returns a choropleth mapbox with the specified parameters
    """
    data = []
    data.append(go.Choroplethmapbox(
                        geojson=geojson,
                        locations=locations,
                        featureidkey=featureid_key,
                        colorscale=colorscale,
                        colorbar=dict(thickness=10,
                            tickvals=tickvals,
                            ticktext=ticktext),
                        z=z,
                        marker_line_width=0,
                        text=hovertext,
                        hoverinfo='text'))

    fig = go.Figure(data=data)

    fig.update_layout(mapbox_style="dark", mapbox_accesstoken=mapbox_token,
                      mapbox_zoom=2, mapbox_center={"lat": 37.0902, "lon": 0.0}
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


def get_scattermapbox(latitudes, longitudes, hovertext, marker_sizes, marker_sizeref, center_lat, center_long, zoom, mapbox_token):
    datamap =  dict(
        type='scattermapbox',
        lat=latitudes,
        lon=longitudes,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=marker_sizes,
            sizeref=marker_sizeref,
            sizemode='area',
            color='rgb(180,0,0)',
        ),
        text=hovertext
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
            style='dark',
            accesstoken=mapbox_token,
            bearing=0,
            center=dict(
                lat=center_lat,
                lon=center_long
            ),
            pitch=0,
            zoom=zoom
        ),
        height=800,
    )

    fig = dict(
        data=[datamap],
        layout=layout
    )
    return {}

