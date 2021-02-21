from typing import List, Tuple

import numpy as np
from plotly import graph_objs
from sklearn.preprocessing import minmax_scale

FIG_BG_COLOR = "#F9F9F9"
ANCHOR_COLOR = "#FF372D"
VALUES_COLOR = "#89D4F5"


def visualize_graph(match_values_list: List[np.ndarray],
                    match_symbols: List[str],
                    match_str_dates: List[Tuple[str, str]],
                    window_size: int,
                    future_size: int,
                    anchor_symbol: str,
                    anchor_values: np.ndarray,
                    show_legend: bool = True) -> graph_objs.Figure:
    fig = graph_objs.Figure()

    assert len(match_values_list) == len(match_symbols), "Something is fishy"

    for i in range(len(match_symbols)):
        match_values = match_values_list[i]
        match_symbol = match_symbols[i]
        match_start_date, match_end_date = match_str_dates[i]

        x = list(range(1, len(match_values) + 1))
        original_values = match_values[::-1]
        minmax_values = minmax_scale(original_values)
        trace = graph_objs.Scatter(x=x,
                                   y=minmax_values,
                                   name=f"{i}) {match_symbol} ({match_start_date} - {match_end_date})",
                                   mode="lines",
                                   line=dict(color=VALUES_COLOR),
                                   opacity=1 / (i + 1),
                                   customdata=original_values,
                                   hovertemplate="<br>Norm. val.: %{y:.2f}<br>Value: %{customdata:.2f}$")
        fig.add_trace(trace)

    x = list(range(1, len(anchor_values) + 1))
    anchor_original_values = anchor_values[::-1]
    minmax_values = minmax_scale(anchor_original_values)
    trace = graph_objs.Scatter(x=x,
                               y=minmax_values,
                               name=f"Anchor ({anchor_symbol})",
                               mode="lines+markers",
                               line=dict(color=ANCHOR_COLOR),
                               customdata=anchor_original_values,
                               hovertemplate="<br>Norm. val.: %{y:.2f}<br>Value: %{customdata:.2f}$")
    fig.add_trace(trace)

    fig.add_vline(x=window_size, line_dash="dash", line_color="black", annotation_text="Last market close")

    # fig.update_xaxes(showspikes=True, spikecolor="black", spikesnap="cursor", spikemode="across")
    # fig.update_yaxes(showspikes=True, spikecolor="black", spikethickness=1)

    x_axis_ticker_labels = list(range(-window_size, future_size + 1))
    fig.update_layout(title=f"Similar patters for {anchor_symbol} based on historical market close data",
                      yaxis=dict(title="Value"),
                      xaxis=dict(title="Days",
                                 tickmode="array",
                                 tickvals=list(range(len(x_axis_ticker_labels))),
                                 ticktext=x_axis_ticker_labels),
                      hovermode="closest",
                      autosize=True,
                      plot_bgcolor=FIG_BG_COLOR,
                      paper_bgcolor=FIG_BG_COLOR,
                      legend=dict(font=dict(size=9), orientation="h", yanchor="bottom", y=-0.5),
                      showlegend=show_legend)

    return fig
