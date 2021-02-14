from datetime import datetime
from pathlib import Path

import numpy  as np
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Response

import stock_pattern_analyzer as spa
from rest_api_models import (SuccessResponse, DataRefreshResponse, TopKSearchResponse, AvailableSymbolsResponse,
                             SearchWindowSizeResponse, MatchResponse)

app = FastAPI()
app.data_holder = None
app.search_tree_dict = {}
app.scheduler = AsyncIOScheduler()
app.last_refreshed = None

AVAILABLE_SEARCH_WINDOW_SIZES = [5, 10, 15, 20]
TICKER_LIST = ["AAPL", "GME", "AMC", "TSLA"]
PERIOD_YEARS = 2


def find_and_remove_files(folder_path: str, file_pattern: str) -> list:
    paths = Path(folder_path).glob(file_pattern)
    for p in paths:
        p.unlink()
    return list(paths)


@app.get("/")
def root():
    return Response(content="Welcome to the stock pattern matcher RestAPI")


@app.get("/data/prepare", response_model=SuccessResponse)
def prepare_data(force_update: bool = False):
    app.data_holder = spa.initialize_data_holder(tickers=TICKER_LIST, period_years=PERIOD_YEARS,
                                                 force_update=force_update)
    return SuccessResponse()


@app.get("/search/prepare/{window_size}", response_model=SuccessResponse)
def prepare_search_tree(window_size: int, force_update: bool = False):
    app.search_tree_dict[window_size] = spa.initialize_search_tree(data_holder=app.data_holder, window_size=window_size,
                                                                   force_update=force_update)
    return SuccessResponse()


@app.get("/search/prepare", response_model=SuccessResponse)
def prepare_all_search_trees(force_update: bool = False):
    for w in AVAILABLE_SEARCH_WINDOW_SIZES:
        prepare_search_tree(window_size=w, force_update=force_update)
    return SuccessResponse()


@app.get("/data/refresh", response_model=SuccessResponse)
def refresh_data():
    # TODO: hardcoded file prefix and folder
    find_and_remove_files(".", "data_holder_*.pk")
    prepare_data()
    return SuccessResponse(message=f"Existing data holder files removed, and a new one is created")


@app.get("/search/refresh", response_model=SuccessResponse)
def refresh_search():
    # TODO: hardcoded file prefix and folder
    find_and_remove_files(".", "search_tree_*.pk")
    prepare_all_search_trees()
    return SuccessResponse()


@app.get("/refresh", response_model=SuccessResponse)
def refresh_everything():
    refresh_data()
    refresh_search()
    app.last_refreshed = datetime.now()
    return SuccessResponse()


@app.get("/refresh/when", response_model=DataRefreshResponse)
def when_was_data_refreshed():
    return DataRefreshResponse(date=app.last_refreshed)


@app.get("/search/sizes", response_model=SearchWindowSizeResponse)
def get_available_search_window_sizes():
    return SearchWindowSizeResponse(sizes=AVAILABLE_SEARCH_WINDOW_SIZES)


@app.get("/data/symbols", response_model=AvailableSymbolsResponse)
def get_available_symbols():
    return AvailableSymbolsResponse(symbols=TICKER_LIST)


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

    top_k_indices, top_k_distances = search_tree.search(values=most_recent_values, k=top_k + 1)
    # We need to discard the first item, as that is our search sequence
    top_k_indices = top_k_indices[1:]
    top_k_distances = top_k_distances[1:]

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


@app.on_event("startup")
def startup_event():
    # Download and prepare new data when app starts
    refresh_everything()

    # Refresh data after every market close
    # TODO: set the timezones and add multiple refresh jobs for the multiple market closes
    app.scheduler.add_job(func=refresh_everything, trigger="cron", day="*", hour=8, minute=35)
    app.scheduler.add_job(func=refresh_everything, trigger="cron", day="*", hour=15, minute=35)
    app.scheduler.start()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
