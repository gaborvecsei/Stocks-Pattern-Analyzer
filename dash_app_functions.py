import requests

import stock_pattern_analyzer as spa
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
    try:
        ret = search_most_recent(symbol=symbol,
                                 window_size=window_size,
                                 top_k=top_k,
                                 future_size=future_size)
        values = []
        symbols = []
        dates = []
        for m in ret.matches:
            values.append(m.values)
            symbols.append(m.symbol)
            dates.append((m.start_date, m.end_date))

        fig = spa.visualize_graph(match_values_list=values,
                                  match_symbols=symbols,
                                  match_str_dates=dates,
                                  window_size=window_size,
                                  future_size=future_size,
                                  anchor_symbol=ret.anchor_symbol,
                                  anchor_values=ret.anchor_values)
        return fig
    except Exception:
        return None
