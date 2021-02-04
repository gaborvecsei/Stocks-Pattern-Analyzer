import argparse
from pathlib import Path

import numpy as np

import stock_pattern_analyzer

DEFAULT_TICKERS = ["AAPL", "MSFT", "AMZN", "BABA", "ROKU", "TDOC", "CRSP", "SQ", "NVTA", "Z", "BIDU", "SPOT", "PRLB",
                   "TSLA", "GME", "BB", "AMC", "LI", "NIO"]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--ticker", required=True, type=str, help="Anchor ticker (e.g.: GME)")
    parser.add_argument("-w", "--window-size", required=True, type=int, help="Pattern size")
    parser.add_argument("-p", "--period-years", default=1, type=int, help="Maximum historical data length")
    parser.add_argument("-k", "--top-k", default=5, type=int, help="Return the top-K search results")
    parser.add_argument("-f", "--future-window-size", default=5, type=int, help="Future of matching stocks")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()

    data_holder = stock_pattern_analyzer.DataHolder(tickers=DEFAULT_TICKERS,
                                                    window_size=args.window_size,
                                                    period_years=args.period_years,
                                                    interval=1)

    file_path = Path(data_holder.create_filename_for_today())

    if not file_path.exists():
        data_holder.fill_data()
        data_holder.serialize()
    else:
        data_holder = stock_pattern_analyzer.DataHolder.load(str(file_path))

    search_tree = stock_pattern_analyzer.SearchTree(data_holder)
    top_k_indices, top_k_distances = search_tree.search_most_recent(ticker=args.ticker, k=args.top_k)

    predictions = []

    for index, distance in zip(top_k_indices, top_k_distances):
        ticker = data_holder.get_ticker_symbol(index)
        window_norm_values = data_holder.get_window(index)
        start_date, end_date = data_holder.get_date(index)
        start_date = stock_pattern_analyzer.date_to_str(start_date)
        end_date = stock_pattern_analyzer.date_to_str(end_date)

        print(f"Match with {ticker} (distance: {distance:.2f}), from {end_date} to {start_date}")

        window_with_future_values, window_with_future_dates = data_holder.get_window_with_future(index=index,
                                                                                                 future_size=args.future_window_size,
                                                                                                 normalize=False)
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
        print(f"\nBearish with {(1 - pred) * 100:.0f}% change")
