import dash_table
import dash_table.FormatTemplate as FormatTemplate
from dash_table.Format import Format, Scheme, Sign, Symbol, Group
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from covid_data import CovidDataProcessor
from covid_data import VALUE_TYPE_ONE_PER_N, VALUE_TYPE_PER_CAPITA, VALUE_TYPE_DAILY_DIFF
from covid_data import VALUE_TYPE_CUMULATIVE, VALUE_TYPE_DAILY_PERCENT_CHANGE
import pandas as pd


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
        style_cell={
            'height': 'auto',
            'width': '60px',
            'minWidth': '60px',
            'maxWidth': '60px',
            'whiteSpace': 'normal',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
        },
        sort_action='native',
        row_selectable='multi',
        filter_action='native',
        selected_rows=[0],
        page_action='native',
        page_current=0,
        page_size = 20,
        persistence_type='local',
        persistence=True
    )
    return table


def stat_table_select_callback(virt_indices, virt_row_ids, virt_selected_rows, row_ids, selected_row_ids, selected_rows, active_cell):
    print(f'virt_data={virt_indices}')
    print(f'virt_rows_ids={virt_row_ids}')
    print(f'virt_selected_rows={virt_selected_rows}')
    print(f'rows_ids={row_ids}')
    print(f'selected_row_ids={selected_row_ids}')
    print(f'selected_rows={selected_rows}')
    print(f'active_cell={active_cell}')
    raise PreventUpdate
    if virt_selected_rows is None or len(virt_selected_rows) == 0:
        raise PreventUpdate
    style = [
        {
            'if': { 'row_index':  selected_rows[0]},
            'backgroundColor': 'blue',
            'color': 'white'
        }
    ]
    return style



def register_stat_table_select_callback(app, table_id):
    outputs = Output(table_id, 'style_data_conditional')
    inputs = [
        Input(table_id, 'derived_virtual_indices '),
        Input(table_id, 'derived_virtual_row_ids'),
        Input(table_id, 'derived_virtual_selected_rows'),
        Input(table_id, 'row_ids'),
        Input(table_id, 'selected_row_ids'),
        Input(table_id, 'selected_rows'),
        Input(table_id, 'active_cell')]
    app.callback(outputs, inputs)(stat_table_select_callback)

def get_stat_table_selected_location_input(table_id):
    return Input(table_id, 'selected_row_ids')