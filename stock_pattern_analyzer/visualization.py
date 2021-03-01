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
                    show_legend: bool = True,
                    offset_traces: bool = False) -> graph_objs.Figure:
    nb_matches = len(match_symbols)
    opacity_values = np.linspace(0.2, 1.0, nb_matches)[::-1]

    anchor_original_values = anchor_values[::-1]
    minmax_anchor_values = minmax_scale(anchor_original_values)

    fig = graph_objs.Figure()

    assert len(match_values_list) == len(match_symbols), "Something is fishy"

    # Draw all matches
    for i in range(nb_matches):
        match_values = match_values_list[i]
        match_symbol = match_symbols[i]
        match_start_date, match_end_date = match_str_dates[i]

        x = list(range(1, len(match_values) + 1))
        original_values = match_values[::-1]
        minmax_matched_values = minmax_scale(original_values)
        if offset_traces:
            diff = minmax_anchor_values[window_size - 1] - minmax_matched_values[window_size - 1]
            minmax_matched_values = minmax_matched_values + diff
        trace_name = f"{i}) {match_symbol} ({match_start_date} - {match_end_date})"
        trace = graph_objs.Scatter(x=x,
                                   y=minmax_matched_values,
                                   name=trace_name,
                                   meta=trace_name,
                                   mode="lines",
                                   line=dict(color=VALUES_COLOR),
                                   opacity=opacity_values[i],
                                   customdata=original_values,
                                   hovertemplate="<b>%{meta}</b><br>Norm. val.: %{y:.2f}<br>Value: %{customdata:.2f}$<extra></extra>")
        fig.add_trace(trace)

    # Draw the anchor series
    x = list(range(1, len(anchor_values) + 1))
    trace_name = f"Anchor ({anchor_symbol})"
    trace = graph_objs.Scatter(x=x,
                               y=minmax_anchor_values,
                               name=trace_name,
                               meta=trace_name,
                               mode="lines+markers",
                               line=dict(color=ANCHOR_COLOR),
                               customdata=anchor_original_values,
                               hovertemplate="<b>%{meta}</b><br>Norm. val.: %{y:.2f}<br>Value: %{customdata:.2f}$<extra></extra>")
    fig.add_trace(trace)

    # Add "last market close" line
    fig.add_vline(x=window_size, line_dash="dash", line_color="black",
                  annotation_text="Last market close (for selected symbol)")

    # Style the figure
    fig.update_xaxes(showspikes=True, spikecolor="black", spikesnap="cursor", spikemode="across")
    # fig.update_yaxes(showspikes=True, spikecolor="black", spikethickness=1)

    x_axis_ticker_labels = list(range(-window_size, future_size + 1))
    fig.update_layout(title=f"Similar patters for {anchor_symbol} based on historical market close data",
                      yaxis=dict(title="Normalized Value"),
                      xaxis=dict(title="Days",
                                 tickmode="array",
                                 tickvals=list(range(len(x_axis_ticker_labels))),
                                 ticktext=x_axis_ticker_labels),
                      autosize=True,
                      plot_bgcolor=FIG_BG_COLOR,
                      paper_bgcolor=FIG_BG_COLOR,
                      legend=dict(font=dict(size=9), orientation="h", yanchor="bottom", y=-0.5),
                      showlegend=show_legend,
                      spikedistance=1000,
                      hoverdistance=100)

    return fig
