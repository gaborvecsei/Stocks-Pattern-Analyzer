import requests
from plotly import graph_objs
from sklearn.preprocessing import minmax_scale

from rest_api_models import (TopKSearchResponse, SearchWindowSizeResponse, DataRefreshResponse,
                             AvailableSymbolsResponse)

BASE_URL = "http://localhost:8001"


def get_search_window_sizes() -> list:
    res = requests.get(f"{BASE_URL}/search/sizes")
    res = SearchWindowSizeResponse.parse_obj(res.json())
    return res.sizes


def get_symbols() -> list:
    res = requests.get(f"{BASE_URL}/data/symbols")
    res = AvailableSymbolsResponse.parse_obj(res.json())
    return res.symbols


def search_most_recent(symbol: str, window_size: int, top_k: int, future_size: int) -> TopKSearchResponse:
    url = f"{BASE_URL}/search/recent/?symbol={symbol.upper()}&window_size={window_size}&top_k={top_k}&future_size={future_size}"
    res = requests.get(url)
    res = TopKSearchResponse.parse_obj(res.json())
    return res


def get_last_refresh_date() -> str:
    url = f"{BASE_URL}/refresh/when"
    res = requests.get(url)
    res = DataRefreshResponse.parse_obj(res)
    date_str = res.date.strftime("%Y/%m/%d, %H:%M:%S")
    return date_str


def visualize_graph(symbol: str, window_size: int, future_size: int, top_k: int):
    fig_bg_color = "#F9F9F9"
    anchor_color = "#FF372D"
    values_color = "#89D4F5"

    fig = graph_objs.Figure()
    try:
        ret = search_most_recent(symbol=symbol,
                                 window_size=window_size,
                                 top_k=top_k,
                                 future_size=future_size)
    except Exception:
        return fig

    for i, match in enumerate(ret.matches):
        x = list(range(1, len(match.values) + 1))
        original_values = match.values[::-1]
        minmax_values = minmax_scale(original_values)
        trace = graph_objs.Scatter(x=x,
                                   y=minmax_values,
                                   name=f"{i}) {match.symbol} ({match.start_date}-{match.end_date})",
                                   mode="lines",
                                   line=dict(color=values_color),
                                   opacity=1 / (i + 1),
                                   customdata=original_values,
                                   hovertemplate="<br>Norm. val.: %{y:.2f}<br>Value: %{customdata:.2f}$")
        fig.add_trace(trace)

    x = list(range(1, len(ret.anchor_values) + 1))
    anchor_original_values = ret.anchor_values[::-1]
    minmax_values = minmax_scale(anchor_original_values)
    trace = graph_objs.Scatter(x=x,
                               y=minmax_values,
                               name=f"Anchor ({ret.anchor_symbol})",
                               mode="lines+markers",
                               line=dict(color=anchor_color),
                               customdata=anchor_original_values,
                               hovertemplate="<br>Norm. val.: %{y:.2f}<br>Value: %{customdata:.2f}$")
    fig.add_trace(trace)

    fig.add_vline(x=window_size, line_dash="dash", line_color="black", annotation_text="Last market close")

    fig.update_xaxes(showspikes=True, spikecolor="black", spikesnap="cursor", spikemode="across")
    fig.update_yaxes(showspikes=True, spikecolor="black", spikethickness=1)

    x_axis_ticker_labels = list(range(-window_size, future_size + 1))
    fig.update_layout(title=f"Similar patters for {ret.anchor_symbol} based on historical market close data",
                      yaxis=dict(title="Value"),
                      xaxis=dict(title="Days",
                                 tickmode="array",
                                 tickvals=list(range(len(x_axis_ticker_labels))),
                                 ticktext=x_axis_ticker_labels),
                      hovermode="closest",
                      autosize=True,
                      plot_bgcolor=fig_bg_color,
                      paper_bgcolor=fig_bg_color,
                      legend=dict(font=dict(size=9), orientation="h"))

    return fig
