import dash
import dash_core_components as dcc
import dash_html_components as html
import requests
from datetime import datetime
import rest_api
from plotly import graph_objs, subplots
from sklearn.preprocessing import minmax_scale

BASE_URL = "http://localhost:8001"


def get_search_window_sizes() -> list:
    res = requests.get(f"{BASE_URL}/search/sizes")
    res = rest_api.SearchWindowSizeResponse.parse_obj(res.json())
    return res.sizes


def search_most_recent(symbol: str, window_size: int, top_k: int, future_size: int) -> rest_api.TopKSearchResponse:
    url = f"{BASE_URL}/search/recent/?symbol={symbol.upper()}&window_size={window_size}&top_k={top_k}&future_size={future_size}"
    res = requests.get(url)
    res = rest_api.TopKSearchResponse.parse_obj(res.json())
    return res


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=[external_stylesheets])

page_title = html.H1(children="Stock Patterns")
page_subtitle = html.Div(children="Find the best matches from historic data")

window_size_dropdown_title = html.Label("Search window size (days)")
window_size_dropdown_id = "id-window-size-dropdown"
window_sizes = get_search_window_sizes()
window_size_dropdown = dcc.Dropdown(id=window_size_dropdown_id,
                                    options=[{"label": f"{x} days", "value": x} for x in window_sizes],
                                    value=window_sizes[0],
                                    style={"width": "50%"})
window_size_div = html.Div(children=[window_size_dropdown_title, window_size_dropdown])

future_size_title = html.Label("Future size (days)")
future_size_input_id = "id-future-size-input"
future_size_input = dcc.Input(id=future_size_input_id, type="number", min=0, max=28, value=5)
future_size_div = html.Div(children=[future_size_title, future_size_input])

top_k_title = html.Label("Visualize Top-K matches")
top_k_input_id = "id-top-k-input"
top_k_input = dcc.Input(id=top_k_input_id, type="number", min=0, max=25, value=5)
top_k_div = html.Div(children=[top_k_title, top_k_input])

symbol_input_title = html.Label("Ticker symbol")
symbol_input_box_id = "id-symbol-input-box"
symbol_input_box = dcc.Input(id=symbol_input_box_id, value="", type="text", placeholder="GME")
symbol_input_div = html.Div(children=[symbol_input_title, symbol_input_box])

submit_button_id = "id-submit-button"
submit_button = html.Button("Match", id=submit_button_id, n_clicks=0)

graph_id = "id-graph"
graph = dcc.Graph(id=graph_id)

app.layout = html.Div(
    children=[page_title,
              page_subtitle,
              window_size_div,
              symbol_input_div,
              future_size_div,
              top_k_div,
              submit_button,
              graph])


@app.callback(dash.dependencies.Output(graph_id, "figure"),
              [dash.dependencies.Input(symbol_input_box_id, "value"),
               dash.dependencies.Input(window_size_dropdown_id, "value"),
               dash.dependencies.Input(future_size_input_id, "value"),
               dash.dependencies.Input(top_k_input_id, "value")])
def submit_button_pressed(symbol_value, window_size_value, future_size, top_k):
    fig = graph_objs.Figure()
    try:
        ret = search_most_recent(symbol=symbol_value,
                                 window_size=window_size_value,
                                 top_k=top_k,
                                 future_size=future_size)
    except Exception:
        return fig

    for i, match in enumerate(ret.matches):
        x = list(range(1, len(match.values) + 1))
        minmax_values = minmax_scale(match.values)[::-1]
        trace = graph_objs.Scatter(x=x, y=minmax_values,
                                   name=f"{i}) {match.symbol} ({match.start_date}-{match.end_date})",
                                   mode="lines", line=dict(color="red"))
        fig.add_trace(trace)

    x = list(range(1, len(ret.anchor_values) + 1))
    minmax_values = minmax_scale(ret.anchor_values)[::-1]
    trace = graph_objs.Scatter(x=x, y=minmax_values,
                               name=f"Anchor ({ret.anchor_symbol})",
                               mode="lines+markers", line=dict(color="blue"))
    fig.add_trace(trace)

    fig.update_layout(title="Top-K matches",
                      yaxis=dict(title="Value"),
                      xaxis=dict(title="days"),
                      hovermode="x")
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
