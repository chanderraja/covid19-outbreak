import plotly.graph_objects as go

RATE_NONE=0
RATE_DIFF=1
RATE_PERCENTAGE=2

def get_top_locations_bar_chart(df, stat, n=10, logger=None):
    if df is None:
        return dict(data=dict())
    data = []
    x_axis = df.index
    y_axis = df[stat]
    data.append(
        dict(name=df.index,
             x=x_axis,
             y=y_axis,
             type='bar',
             text=y_axis))
    figure = dict(
        data=data,
        layout=dict(
            title=f'top {n} trending',
            height=600,
            xaxis = dict(tickangle = 45),
            margin = dict(b = 100),
            autosize=True))
    return figure

def get_time_series_scatter_chart(df, locations=None, show_rate=RATE_NONE, title=None, logger=None):
    if df is None:
        return dict(data=dict())
    if show_rate == RATE_DIFF:
        df = df.diff()
    elif show_rate == RATE_PERCENTAGE:
        df = df.pct_change()
    x_list = [d.date() for d in df.index]
    data = []
    if locations is not None and isinstance(locations, list):
        for loc in locations:
            if loc not in df.columns:
                continue
            data.append(go.Scatter(x=x_list,
                               y=df[loc],
                               mode='lines',
                               name=loc))
    layout = go.Layout(
        title=title,
        height=600,
        plot_bgcolor='rgba(240,240,255,100)',
        legend=dict(
            x=0.05,
            y=0.95,
            traceorder='normal',
            font=dict(
                size=10,
            ),
        ),
    )

    fig = dict(data=data, layout=layout)
    return fig
