import numpy as np
import math
import plotly.graph_objects as go


def __shorten(n):
    if n < 1000:
        return f'{n}'
    if n < 1E6:
        return f'{n/1E3:g}k'
    if n < 1E9:
        return f'{n/1E6:g}m'
    return f'{n/1E9:g}B'


def rgb_str_to_tuple(rgb_str):
    """
    convert color string in #rrggbb format into separate R,G and B values
    :param rgb_str: rgb_str in '#rrggbb' hex format
    :return: tuple containing R, G and B values as ints
    """
    s = rgb_str.lstrip('#')
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))


def rgb_tuple_to_str(rgb):
    """
    convert color string in #rrggbb format into separate R,G and B values
    :param rgb: tuple containing r, g and b values
    :return: string in '#rrggbb' hex format
    """
    rgb_str = '#'
    for i in range(0,3):
        rgb_str += f'{rgb[i]:02x}'
    return rgb_str

def interpolated_colors(color1, color2, n):
    """
    return an interpolated sequence of colors
    :param color1: starting color in plotly hex format '#RRGGBB'
    :param color2: ending color in plotly hex format '#RRGGBB'
    :param n: number of colors to return
    :return: list of linearly interpolated Plotly color sequence starting with color1 and ending with color2 inclusive
    """
    rgb1 = rgb_str_to_tuple(color1)
    rgb2 = rgb_str_to_tuple(color2)
    colors = []
    r_list = np.linspace(rgb1[0], rgb2[0], num=n, endpoint=True, dtype=int)
    g_list = np.linspace(rgb1[1], rgb2[1], num=n, endpoint=True, dtype=int)
    b_list = np.linspace(rgb1[2], rgb2[2], num=n, endpoint=True, dtype=int)
    for i in range(0, n):
        rgb = (r_list[i], g_list[i], b_list[i])
        colors.append(rgb_tuple_to_str(rgb))
    return colors


def discrete_colorscale(bvals, colors, logarithmic=False, shorten_ticktext=True):
    """
    bvals - list of values bounding intervals/ranges of interest
    colors - list of rgb or hex colorcodes for values in [bvals[k], bvals[k+1]],0<=k < len(bvals)-1
    ticktext_exp - if True, ticktext must be expressd as 10^bvals[x]
    ceil - if True, tick text will contain ceiling values of tick values
    returns the plotly discrete colorscale
    """
    if len(bvals) != len(colors) + 1:
        raise ValueError('len(boundary values) should be equal to  len(colors)+1')
    bvals = sorted(bvals)
    bvals_orig = bvals # save the original values
    bvals = np.log10(bvals) if logarithmic is True else bvals
    nvals = [(v - bvals[0]) / (bvals[-1] - bvals[0]) for v in bvals]  # normalized values
    dcolorscale = []  # discrete colorscale
    for k in range(len(colors)):
        dcolorscale.extend([[nvals[k], colors[k]], [nvals[k + 1], colors[k]]])
    bvals = np.array(bvals)
    tickvals = [np.mean(bvals[k:k + 2]) for k in
                range(len(bvals) - 1)]  # position with respect to bvals where ticktext is displayed

    if shorten_ticktext is True:
        cscale_text = [__shorten(x) for x in bvals_orig]
    else:
        cscale_text = [f'{x:,g}' for x in bvals_orig]
    ticktext = [f'<{cscale_text[1]}'] + [f'{cscale_text[k]}-{cscale_text[k + 1]}'
                                          for k in range(1, len(cscale_text) - 2)] + [f'>{cscale_text[-2]}']
    zmin = bvals[0]
    zmax = bvals[-1]
    return dcolorscale, tickvals, ticktext, zmin, zmax


def get_choropleth_mapbox(geojson, locations, z, hovertext,  mapbox_token,
                          color_boundaries, color_min, color_max,
                          name=None, logarithmic=False, featureid_key=None, logger=None):
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
    if logger is not None:
        logger.warning('start map construction')
    color_boundaries = sorted(color_boundaries)
    colors = interpolated_colors(color_min, color_max, len(color_boundaries)-1)
    colorscale, tickvals, ticktext, zmin, zmax = discrete_colorscale(color_boundaries, colors, logarithmic)
    data = []
    data.append(
        go.Choroplethmapbox(
            geojson=geojson,
            locations=locations,
            featureidkey=featureid_key,
            colorscale=colorscale,
            colorbar=dict(
                thickness=25,
                tickvals=tickvals,
                ticktext=ticktext),
            z=z if not logarithmic else np.log10(z),
            zmin=zmin,
            zmax=zmax,
            marker_line_width=0,
            marker_line_color='white',
            marker_opacity=0.8,
            text=hovertext,
            hoverinfo='text'))

    fig = go.Figure(data=data)

    fig.update_layout(
        title=name,
        mapbox=dict(
            style='outdoors',
            accesstoken=mapbox_token,
            zoom=3,
            center={"lat": 37.0902, "lon": -95.7129}
        )
    )
    fig.update_layout(margin={"r": 10, "t": 10, "l": 10, "b": 10})
    if logger is not None:
        logger.warning('end map construction')
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
            style='open-street-map',
            #accesstoken=mapbox_token,
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

