import dash_core_components as dcc
import dash_html_components as html
from dash import Dash
from dash.dependencies import Input, Output

from dash_app_functions import get_search_window_sizes, visualize_graph, get_symbols

app = Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])
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
future_size_input = dcc.Input(id=future_size_input_id, type="number", min=0, max=28, value=5, className="dcc_control")

top_k_input_id = "id-top-k-input"
top_k_input = dcc.Input(id=top_k_input_id, type="number", min=0, max=25, value=5, className="dcc_control")

settings_div = html.Div([html.P("Symbol", className="control_label"),
                         symbol_dropdown,
                         html.P("Search window size", className="control_label"),
                         window_size_dropdown,
                         html.P("Future window size", className="control_label"),
                         future_size_input,
                         html.P("Top-K (max number of patterns to match)", className="control_label"),
                         top_k_input],
                        className="pretty_container three columns",
                        id="id-settings-div")

##### Stats & Graph #####

graph_id = "id-graph"

stats_and_graph_div = html.Div([html.Div(id="id-stats-container", className="row container-display"),
                                html.Div([dcc.Graph(id=graph_id)], id="id-graph-div", className="pretty_container")],
                               id="id-graph-container", className="nine columns")

##### Layout #####

app.layout = html.Div([header_div,
                       html.Div([settings_div,
                                 stats_and_graph_div],
                                className="row flex-display")],
                      id="mainContainer",
                      style={"display": "flex", "flex-direction": "column"})


##### Callbacks #####

@app.callback(Output(graph_id, "figure"),
              [Input(symbol_dropdown_id, "value"),
               Input(window_size_dropdown_id, "value"),
               Input(future_size_input_id, "value"),
               Input(top_k_input_id, "value")])
def update_plot(symbol_value, window_size_value, future_size_value, top_k_value):
    fig = visualize_graph(symbol=symbol_value,
                          window_size=window_size_value,
                          future_size=future_size_value,
                          top_k=top_k_value)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
