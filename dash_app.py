import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash import Dash
from dash.dependencies import Input, Output

import stock_pattern_analyzer as spa
from dash_app_functions import get_search_window_sizes, get_symbols, search_most_recent

app = Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])
app.title = "Stock Patterns"
server = app.server

##### Header #####

header_div = html.Div([html.Div([html.H3("📈")], className="one-third column"),
                       html.Div([html.Div([html.H3("Stock Patterns", style={"margin-bottom": "0px"}),
                                           html.H5("Find historical patterns and use for forecasting",
                                                   style={"margin-top": "0px"})])],
                                className="one-half column", id="title"),
                       html.Div([html.A(html.Button("Gabor Vecsei"), href="https://www.gaborvecsei.com/")],
                                className="one-third column",
                                id="learn-more-button")],
                      id="header", className="row flex-display", style={"margin-bottom": "25px"})

##### Settings container #####

# symbol_input_box_id = "id-symbol-input-box"
# symbol_input_box = dcc.Input(id=symbol_input_box_id, value="AAPL", type="text", className="dcc_control")
symbol_dropdown_id = "id-symbol-dropdown"
available_symbols = get_symbols()
symbol_dropdown = dcc.Dropdown(id=symbol_dropdown_id,
                               options=[{"label": x, "value": x} for x in available_symbols],
                               multi=False,
                               value=available_symbols[0],
                               className="dcc_control")

window_size_dropdown_id = "id-window-size-dropdown"
window_sizes = get_search_window_sizes()
window_size_dropdown = dcc.Dropdown(id=window_size_dropdown_id,
                                    options=[{"label": f"{x} days", "value": x} for x in window_sizes],
                                    multi=False,
                                    value=window_sizes[0],
                                    className="dcc_control")

future_size_input_id = "id-future-size-input"
future_size_input = dcc.Input(id=future_size_input_id, type="number", min=0, max=25, value=5, className="dcc_control")

top_k_input_id = "id-top-k-input"
top_k_input = dcc.Input(id=top_k_input_id, type="number", min=0, max=25, value=5, className="dcc_control")

settings_div = html.Div([html.P("Symbol", className="control_label"),
                         symbol_dropdown,
                         html.P("Search window size", className="control_label"),
                         window_size_dropdown,
                         html.P("Future window size (max. 25)", className="control_label"),
                         future_size_input,
                         html.P("Patterns to match (max. 25)", className="control_label"),
                         top_k_input],
                        className="pretty_container three columns",
                        id="id-settings-div")

##### Stats & Graph #####

graph_id = "id-graph"
stats_and_graph_div = html.Div([html.Div(id="id-stats-container", className="row container-display"),
                                html.Div([dcc.Graph(id=graph_id)], id="id-graph-div", className="pretty_container")],
                               id="id-graph-container", className="nine columns")

##### Matched Stocks List #####

matched_table_id = "id-matched-list"
table_columns = ["Index", "Match distance", "Symbol", "Start date", "End Date", "Start Close Value ($)",
                 "End Close Value ($)"]
table = dash_table.DataTable(id=matched_table_id, columns=[{"id": c, "name": c} for c in table_columns], page_size=5)
matched_div = html.Div([html.Div([html.H6("Matched patterns"), table],
                                 className="pretty_container")],
                       id="id-matched-list-container",
                       className="eleven columns")

##### Reference Links #####

css_link = html.A("[1] Style of the page (css)",
                  href="https://github.com/plotly/dash-sample-apps/tree/master/apps/dash-oil-and-gas")
yahoo_data_link = html.A("[2] Yahoo data", href="https://finance.yahoo.com")
reference_links_div = html.Div([html.Div([html.H6("References"),
                                          css_link,
                                          html.Br(),
                                          yahoo_data_link],
                                         className="pretty_container")],
                               className="four columns")

##### Layout #####

app.layout = html.Div([header_div,
                       html.Div([settings_div,
                                 stats_and_graph_div],
                                className="row flex-display"),
                       html.Div([matched_div], className="row flex-display"),
                       reference_links_div],
                      id="mainContainer",
                      style={"display": "flex", "flex-direction": "column"})


##### Callbacks #####

@app.callback([Output(graph_id, "figure"),
               Output(matched_table_id, "data")],
              [Input(symbol_dropdown_id, "value"),
               Input(window_size_dropdown_id, "value"),
               Input(future_size_input_id, "value"),
               Input(top_k_input_id, "value")])
def update_plot_and_table(symbol_value, window_size_value, future_size_value, top_k_value):
    # RetAPI search
    ret = search_most_recent(symbol=symbol_value,
                             window_size=window_size_value,
                             top_k=top_k_value,
                             future_size=future_size_value)

    # Parse response and build the HTML table rows
    table_rows = []
    values = []
    symbols = []
    start_end_dates = []
    for i, match in enumerate(ret.matches):
        values.append(match.values)
        symbols.append(match.symbol)
        start_end_dates.append((match.start_date, match.end_date))
        row_values = [i + 1, match.distance, match.symbol, match.start_date, match.end_date, match.values[0],
                      match.values[-1]]
        row_dict = {c: v for c, v in zip(table_columns, row_values)}
        table_rows.append(row_dict)

    # Visualize the data on a graph
    fig = spa.visualize_graph(match_values_list=values,
                              match_symbols=symbols,
                              match_str_dates=start_end_dates,
                              window_size=window_size_value,
                              future_size=future_size_value,
                              anchor_symbol=ret.anchor_symbol,
                              anchor_values=ret.anchor_values,
                              show_legend=False)

    return fig, table_rows


if __name__ == "__main__":
    app.run_server(debug=True)
