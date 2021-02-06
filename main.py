import argparse
from pathlib import Path

import numpy as np

import stock_pattern_analyzer

# DEFAULT_TICKERS = ["AAPL", "MSFT", "AMZN", "BABA", "ROKU", "TDOC", "CRSP", "SQ", "NVTA", "Z", "BIDU", "SPOT", "PRLB",
#                    "TSLA", "GME", "BB", "AMC", "LI", "NIO"]
DEFAULT_TICKERS = ["AAPL", "MSFT"]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--ticker", required=True, type=str, help="Anchor ticker (e.g.: GME)")
    parser.add_argument("-w", "--window-size", required=True, type=int, help="Pattern size")
    parser.add_argument("-p", "--period-years", default=1, type=int, help="Maximum historical data length")
    parser.add_argument("-k", "--top-k", default=5, type=int, help="Return the top-K search results")
    parser.add_argument("-f", "--future-window-size", default=5, type=int, help="Future of matching stocks")
    args = parser.parse_args()
    return args


def initialize_data_holder(tickers: list, period_years: int):
    data_holder = stock_pattern_analyzer.RawStockDataHolder(ticker_symbols=tickers,
                                                            period_years=period_years,
                                                            interval=1)

    file_path = Path(data_holder.create_filename_for_today())

    if not file_path.exists():
        data_holder.fill()
        data_holder.serialize()
    else:
        data_holder = stock_pattern_analyzer.RawStockDataHolder.load(str(file_path))
    return data_holder


def initialize_search_tree(data_holder: stock_pattern_analyzer.RawStockDataHolder, window_size: int):
    search_tree = stock_pattern_analyzer.SearchTree(data_holder=data_holder, window_size=window_size)

    file_path = Path(search_tree.create_filename_for_today())

    if not file_path.exists():
        search_tree.build_search_tree()
        search_tree.serialize()
    else:
        search_tree = stock_pattern_analyzer.SearchTree.load(str(file_path))
    return search_tree


if __name__ == "__main__":
    args = parse_args()

    data_holder = initialize_data_holder(tickers=DEFAULT_TICKERS, period_years=args.period_years)
    search_tree = initialize_search_tree(data_holder=data_holder, window_size=args.window_size)

    label = data_holder.symbol_to_label[args.ticker]
    most_recent_values = data_holder.values[label][:search_tree.window_size]
    top_k_indices, top_k_distances = search_tree.search(values=most_recent_values, k=args.top_k)

    predictions = []

    print(f"Forecast with a future length of {search_tree.window_size}")
    print("-" * 30)

    for index, distance in zip(top_k_indices, top_k_distances):
        ticker = search_tree.get_window_symbol(index)
        start_date, end_date = search_tree.get_start_end_date(index)

        start_date_str = stock_pattern_analyzer.date_to_str(start_date)
        end_date_str = stock_pattern_analyzer.date_to_str(end_date)
        print(f"Match with {ticker} (distance: {distance:.2f}), from {end_date_str} to {start_date_str}")

        window_with_future_values = search_tree.get_window_values(index=index,
                                                                  future_length=args.future_window_size)
        todays_value = window_with_future_values[-args.window_size]
        future_value = window_with_future_values[0]
        diff_from_today = todays_value - future_value
        print(f"from ${todays_value:.2f} to ${future_value:.2f} change was: ${diff_from_today:.2f}")
        print("-" * 30)

        predictions.append(diff_from_today)

    asd = np.where(np.array(predictions) < 0, 0, 1)
    pred = np.sum(asd) / len(asd)

    if pred > 0.5:
        print(f"\nBullish with {pred * 100:.0f}% chance")
    else:
        print(f"\nBearish with {(1 - pred) * 100:.0f}% chance")
