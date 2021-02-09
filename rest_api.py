from enum import Enum
from typing import List, Optional
import uvicorn
import numpy  as np
from pydantic import BaseModel

import stock_pattern_analyzer as spa

from fastapi import FastAPI, HTTPException, Response

app = FastAPI()
app.data_holder = None
app.search_tree_dict = {}

AVAILABLE_SEARCH_WINDOW_SIZES = [5, 10, 15, 20]
TICKER_LIST = ["AAPL", "GME", "AMC", "TSLA"]
PERIOD_YEARS = 5


class SuccessResponse(BaseModel):
    message: str = "Successful"


@app.get("/")
def root():
    return Response(content="Welcome to the stock pattern matcher RestAPI")


@app.get("/data/prepare")
def prepare_data(force_update: bool = False):
    app.data_holder = spa.initialize_data_holder(tickers=TICKER_LIST, period_years=PERIOD_YEARS,
                                                 force_update=force_update)
    return SuccessResponse()


@app.get("/search/prepare/{window_size}")
def prepare_search_tree(window_size: int, force_update: bool = False):
    app.search_tree_dict[window_size] = spa.initialize_search_tree(data_holder=app.data_holder, window_size=window_size,
                                                                   force_update=force_update)
    return SuccessResponse()


class SearchWindowSizeResponse(BaseModel):
    sizes: List[int]


@app.get("/search/sizes", response_model=SearchWindowSizeResponse)
def get_available_search_window_sizes():
    return SearchWindowSizeResponse(sizes=AVAILABLE_SEARCH_WINDOW_SIZES)


class AvailableSymbolsResponse(BaseModel):
    symbols: List[str]


@app.get("/data/symbols", response_model=AvailableSymbolsResponse)
def get_available_symbols():
    return AvailableSymbolsResponse(symbols=TICKER_LIST)


@app.get("/data/symbols")
class MatchResponse(BaseModel):
    symbol: str
    distance: float
    start_date: str
    end_date: str
    todays_value: Optional[float]
    future_value: Optional[float]
    change: Optional[float]
    values: Optional[List[float]]


class TopKSearchResponse(BaseModel):
    matches: List[MatchResponse] = []
    forecast_type: str
    forecast_confidence: float
    anchor_symbol: str
    anchor_values: Optional[List[float]]
    window_size: int
    top_k: int
    future_size: int


@app.get("/search/recent/", response_model=TopKSearchResponse)
async def search_most_recent(symbol: str, window_size: int = 5, top_k: int = 5, future_size: int = 5):
    symbol = symbol.upper()
    try:
        label = app.data_holder.symbol_to_label[symbol]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Ticker symbol {symbol} is not supported")
    most_recent_values = app.data_holder.values[label][:window_size]

    try:
        search_tree = app.search_tree_dict[window_size]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"No prepared {window_size} day search window")

    top_k_indices, top_k_distances = search_tree.search(values=most_recent_values, k=top_k)

    forecast_values = []
    matches = []

    for index, distance in zip(top_k_indices, top_k_distances):
        ticker = search_tree.get_window_symbol(index)
        start_date, end_date = search_tree.get_start_end_date(index)

        start_date_str = spa.date_to_str(start_date)
        end_date_str = spa.date_to_str(end_date)

        window_with_future_values = search_tree.get_window_values(index=index,
                                                                  future_length=future_size)
        todays_value = window_with_future_values[-window_size]
        future_value = window_with_future_values[0]
        diff_from_today = todays_value - future_value

        match = MatchResponse(symbol=ticker,
                              distance=distance,
                              start_date=start_date_str,
                              end_date=end_date_str,
                              todays_value=todays_value,
                              future_value=future_value,
                              change=diff_from_today,
                              values=window_with_future_values.tolist())

        matches.append(match)

        forecast_values.append(diff_from_today)

    tmp = np.where(np.array(forecast_values) < 0, 0, 1)
    forecast_confidence = np.sum(tmp) / len(tmp)
    forecast_type = "gain"
    if forecast_confidence <= 0.5:
        forecast_type = "loss"
        forecast_confidence = 1 - forecast_confidence

    top_k_match = TopKSearchResponse(matches=matches,
                                     forecast_type=forecast_type,
                                     forecast_confidence=forecast_confidence,
                                     anchor_symbol=symbol,
                                     window_size=window_size,
                                     top_k=top_k,
                                     future_size=future_size,
                                     anchor_values=most_recent_values.tolist())

    return top_k_match


if __name__ == "__main__":
    prepare_data()
    for win_size in AVAILABLE_SEARCH_WINDOW_SIZES:
        prepare_search_tree(win_size)

    uvicorn.run(app, host="0.0.0.0", port=8001)
