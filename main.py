import argparse
from pathlib import Path

import stock_pattern_analyzer

DEFAULT_TICKERS = ["AAPL", "MSFT", "AMZN", "BABA", "ROKU", "TDOC", "CRSP", "SQ", "NVTA", "Z", "BIDU", "SPOT", "PRLB",
                   "TSLA", "GME", "BB", "AMC", "LI", "NIO"]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--ticker", required=True, type=str, help="Anchor ticker (e.g.: GME)")
    parser.add_argument("-w", "--window-size", required=True, type=int, help="Pattern size")
    parser.add_argument("-p", "--period-years", default=1, type=int, help="Maximum historical data length")
    parser.add_argument("-k", "--top-k", default=5, type=int, help="Return the top-K search results")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()

    file_path = Path("E:\\Projects\Stocks-Pattern-Analyzer\\stock_pattern_analyzer\\5y_1d_7win_2021_02_04")
    if not file_path.exists():
        data_holder = stock_pattern_analyzer.DataHolder(tickers=DEFAULT_TICKERS, window_size=args.window_size,
                                                        period_years=args.period_years,
                                                        interval=1)
        data_holder.fill_data()
        data_holder.serialize()
    else:
        data_holder = stock_pattern_analyzer.DataHolder.load(str(file_path))

    search_tree = stock_pattern_analyzer.SearchTree(data_holder)
    top_k_indices, top_k_distances = search_tree.search_most_recent(ticker=args.ticker, k=args.top_k)

    for index, distance in zip(top_k_indices, top_k_distances):
        ticker = data_holder.get_ticker(index)
        window_norm_values = data_holder.get_norm_window(index)
        start_date, end_date = data_holder.get_date(index)
        start_date = stock_pattern_analyzer.date_to_str(start_date)
        end_date = stock_pattern_analyzer.date_to_str(end_date)

        bull_or_bear = "bull"
        if window_norm_values[0] < window_norm_values[-1]:
            bull_or_bear = "bear"

        print(f"Match with {ticker} (distance: {distance:.2f}), from {end_date} to {start_date} --> {bull_or_bear}")
