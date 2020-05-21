import dash_table
import dash_table.FormatTemplate as FormatTemplate
from dash_table.Format import Format, Scheme, Sign, Symbol, Group
from covid_data import CovidDataProcessor
from covid_data import VALUE_TYPE_ONE_PER_N, VALUE_TYPE_PER_CAPITA, VALUE_TYPE_DAILY_DIFF
from covid_data import VALUE_TYPE_CUMULATIVE, VALUE_TYPE_DAILY_PERCENT_CHANGE


def get_stat_table(dataproc: CovidDataProcessor, scope, stat, table_id):
    # get stats for all locations under scope for latest date
    df = dataproc.get_all_loc_stats(scope=scope, stat=stat)
    style_cell_conditional = [
        {
            'if': {'column_id': 'location'},
            'textAlign': 'left'
        } for c in df.columns
    ]

    table = dash_table.DataTable(
        id=table_id,
        #columns=[
        #   dict(name=i, id=i, deletable=False) for i in df.columns
        #],
        columns=[{
            'id': 'index',
            'name': 'Location',
            'type': 'text'
        }, {
            'id': VALUE_TYPE_CUMULATIVE,
            'name': 'Total',
            'type': 'numeric',
            'format': Format(
                        precision=0,
                        group=Group.yes,
                        scheme=Scheme.fixed)
        }, {
            'id': VALUE_TYPE_DAILY_DIFF,
            'name': 'Change',
            'type': 'numeric',
            'format': Format(precision=0,
                        group=Group.yes,
                        scheme=Scheme.fixed).sign(Sign.positive)
        }, { 'id': VALUE_TYPE_DAILY_PERCENT_CHANGE,
            'name': 'Change (%)',
            'type': 'numeric',
            'format': Format(scheme=Scheme.fixed, precision=2).sign(Sign.positive)
        }, {
            'id': VALUE_TYPE_PER_CAPITA,
            'name': 'Per Capita',
            'type': 'numeric',
            'format': Format(precision=2,
                        group=Group.yes,
                        scheme=Scheme.fixed)
        }, {
            'id': VALUE_TYPE_ONE_PER_N,
            'name': '1 Per N',
            'type': 'numeric',
            'format': Format(precision=0,
                        group=Group.yes,
                        scheme=Scheme.fixed)
        }],
        data=df.to_dict('records'),
        editable=False,
        #filter_action='native',
        sort_action='native',
        #page_action='native',
        #page_size=10,
        #page_action='none',
        #persistence=True,
        virtualization=True,
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_cell_conditional=style_cell_conditional,
        style_cell={
            'height': 'auto',
            'width': '80px',
            'minWidth': '80px',
            'maxWidth': '80px',
            'whiteSpace': 'normal',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
        },
        style_table={
            'overflowY': 'auto'
        },
        fixed_rows={'headers': True, 'data': 0}
    )
    return table