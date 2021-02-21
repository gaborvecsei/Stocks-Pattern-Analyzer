import os

import requests

from rest_api_models import (TopKSearchResponse, SearchWindowSizeResponse, DataRefreshResponse,
                             AvailableSymbolsResponse)

BASE_URL = os.environ.get("REST_API_URL", default="http://localhost:8001")


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
