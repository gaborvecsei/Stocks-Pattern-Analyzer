import concurrent.futures
import pickle
from datetime import datetime
from pathlib import Path
from typing import Tuple

import numpy as np
import yfinance
from tqdm import tqdm


class RawStockDataHolder:
    def __init__(self, ticker_symbols: list, period_years: int = 5, interval: int = 1):
        self.ticker_symbols = ticker_symbols
        self.period_years = period_years
        self.interval = interval

        max_values_per_stock = self.period_years * self.interval * 365
        nb_ticker_symbols = len(self.ticker_symbols)

        self.dates = np.zeros((nb_ticker_symbols, max_values_per_stock))
        self.values = np.zeros((nb_ticker_symbols, max_values_per_stock), dtype=np.float16)
        self.nb_of_valid_values = np.zeros(nb_ticker_symbols, dtype=np.int32)

        self.symbol_to_label = {symbol: label for label, symbol in enumerate(ticker_symbols)}
        self.label_to_symbol = {label: symbol for symbol, label in self.symbol_to_label.items()}

        self.is_filled = False

    def _get_stock_data_for_symbol(self, symbol: str) -> Tuple[np.ndarray, np.ndarray, int]:
        ticker = yfinance.Ticker(symbol)
        period_str = f"{self.period_years}y"
        interval_str = f"{self.interval}d"
        ticker_df = ticker.history(period=period_str, interval=interval_str, rounding=True)[::-1]

        if ticker_df.empty or len(ticker_df) == 0:
            raise ValueError(f"{symbol} does not have enough data")

        close_values = ticker_df["Close"].values
        dates = ticker_df.index.values
        label = self.symbol_to_label[symbol]

        return close_values, dates, label

    def fill(self):
        pbar = tqdm(desc="Symbol data download", total=len(self.ticker_symbols))

        with concurrent.futures.ThreadPoolExecutor() as pool:
            future_to_symbol = {}
            for symbol in self.ticker_symbols:
                future = pool.submit(self._get_stock_data_for_symbol, symbol=symbol)
                future_to_symbol[future] = symbol

            for future in concurrent.futures.as_completed(future_to_symbol):
                completed_symbol = future_to_symbol[future]
                try:
                    close_values, dates, label = future.result()
                    self.values[label, :len(close_values)] = close_values
                    self.dates[label, :len(dates)] = dates
                    self.nb_of_valid_values[label] = len(dates)
                except ValueError as e:
                    print(f"ERROR with {completed_symbol}: {e}")
                    continue

                pbar.update(1)
        self.is_filled = True
        pbar.close()

    def create_filename_for_today(self) -> str:
        current_date = datetime.now().strftime("%Y_%m_%d")
        file_name = f"data_holder_{self.period_years}y_{self.interval}d_{current_date}.pk"
        return file_name

    def serialize(self) -> str:
        if not self.is_filled:
            raise ValueError("You need to fill the class with data first")

        file_name = self.create_filename_for_today()
        with open(file_name, "wb") as f:
            pickle.dump(self, f)

        return file_name

    @staticmethod
    def load(file_name: str) -> "RawStockDataHolder":
        with open(file_name, "rb") as f:
            obj = pickle.load(f)
        return obj


def initialize_data_holder(tickers: list, period_years: int, force_update: bool = False):
    data_holder = RawStockDataHolder(ticker_symbols=tickers,
                                     period_years=period_years,
                                     interval=1)

    file_path = Path(data_holder.create_filename_for_today())

    if (not file_path.exists()) or force_update:
        data_holder.fill()
        data_holder.serialize()
    else:
        data_holder = RawStockDataHolder.load(str(file_path))
    return data_holder
