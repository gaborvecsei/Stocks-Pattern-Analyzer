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

##### Explanation #####

explanation_div = html.Div([dcc.Markdown("""Select a stock symbol and a time-frame. This tools finds similar patterns in
historical data.

The most similar patters are visualized with an extended *time-frame/'future data'*, which can be an
indication of future price movement for the selected (anchor) stock.""")])

##### Settings container #####

symbol_dropdown_id = "id-symbol-dropdown"
available_symbols = get_symbols()
default_symbol = "AAPL" if "AAPL" in available_symbols else available_symbols[0]
symbol_dropdown = dcc.Dropdown(id=symbol_dropdown_id,
                               options=[{"label": x, "value": x} for x in available_symbols],
                               multi=False,
                               value=default_symbol,
                               className="dcc_control")

window_size_dropdown_id = "id-window-size-dropdown"
window_sizes = get_search_window_sizes()
window_size_dropdown = dcc.Dropdown(id=window_size_dropdown_id,
                                    options=[{"label": f"{x} days", "value": x} for x in window_sizes],
                                    multi=False,
                                    value=window_sizes[2],
                                    className="dcc_control")

future_size_input_id = "id-future-size-input"
MAX_FUTURE_WINDOW_SIZE = 10
future_size_input = dcc.Input(id=future_size_input_id, type="number", min=0, max=MAX_FUTURE_WINDOW_SIZE, value=5,
                              className="dcc_control")

top_k_input_id = "id-top-k-input"
MAX_TOP_K_VALUE = 10
top_k_input = dcc.Input(id=top_k_input_id, type="number", min=0, max=MAX_TOP_K_VALUE, value=5, className="dcc_control")

offset_checkbox_id = "id-offset-checkbox"
offset_checkbox = dcc.Checklist(id=offset_checkbox_id, options=[{"label": "Use Offset", "value": "offset"}],
                                value=["offset"], className="dcc_control")

settings_div = html.Div([html.P("Symbol (anchor)", className="control_label"),
                         symbol_dropdown,
                         html.P("Search window size", className="control_label"),
                         window_size_dropdown,
                         html.P(f"Future window size (max. {MAX_FUTURE_WINDOW_SIZE})", className="control_label"),
                         future_size_input,
                         html.P(f"Patterns to match (max. {MAX_TOP_K_VALUE})", className="control_label"),
                         top_k_input,
                         html.P("Offset the matched patterns for easy comparison (to the anchors last market close)",
                                className="control_label"),
                         offset_checkbox],
                        className="pretty_container three columns",
                        id="id-settings-div")

##### Stats & Graph #####

graph_id = "id-graph"
stats_and_graph_div = html.Div([html.Div(id="id-stats-container", className="row container-display"),
                                html.Div([dcc.Graph(id=graph_id)], id="id-graph-div", className="pretty_container")],
                               id="id-graph-container", className="nine columns")

##### Matched Stocks List #####

matched_table_id = "id-matched-list"
table_columns = ["Index",
                 "Match distance",
                 "Symbol",
                 "Pattern Start Date",
                 "Pattern End Date",
                 "Pattern Start Close Value ($)",
                 "Pattern End Close Value ($)",
                 "Pattern Future Close Value ($)"]
table = dash_table.DataTable(id=matched_table_id, columns=[{"id": c, "name": c} for c in table_columns], page_size=5)
matched_div = html.Div([html.Div([html.H6("Matched (most similar) patterns"), table],
                                 className="pretty_container")],
                       id="id-matched-list-container",
                       className="eleven columns")

##### Reference Links #####

css_link = html.A("[1] Style of the page (css)",
                  href="https://github.com/plotly/dash-sample-apps/tree/master/apps/dash-oil-and-gas")
yahoo_data_link = html.A("[2] Yahoo data", href="https://finance.yahoo.com")
gabor_github_link = html.A("[3] Gabor Vecsei GitHub", href="https://github.com/gaborvecsei")
reference_links_div = html.Div([html.Div([html.H6("References"),
                                          css_link,
                                          html.Br(),
                                          yahoo_data_link,
                                          html.Br(),
                                          gabor_github_link],
                                         className="pretty_container")],
                               className="four columns")

##### Layout #####

app.layout = html.Div([header_div,
                       explanation_div,
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
               Input(top_k_input_id, "value"),
               Input(offset_checkbox_id, "value")])
def update_plot_and_table(symbol_value, window_size_value, future_size_value, top_k_value, checkbox_value):
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
        row_values = [i + 1,
                      match.distance,
                      match.symbol,
                      match.end_date,
                      match.start_date,
                      match.values[-1],
                      match.values[window_size_value - 1],
                      match.values[0]]
        row_dict = {c: v for c, v in zip(table_columns, row_values)}
        table_rows.append(row_dict)

    offset_traces = False if len(checkbox_value) == 0 else True

    # Visualize the data on a graph
    fig = spa.visualize_graph(match_values_list=values,
                              match_symbols=symbols,
                              match_str_dates=start_end_dates,
                              window_size=window_size_value,
                              future_size=future_size_value,
                              anchor_symbol=ret.anchor_symbol,
                              anchor_values=ret.anchor_values,
                              show_legend=False,
                              offset_traces=offset_traces)

    return fig, table_rows


if __name__ == "__main__":
    app.run_server(debug=False)
