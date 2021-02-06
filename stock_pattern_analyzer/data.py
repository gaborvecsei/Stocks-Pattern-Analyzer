import pickle
from datetime import datetime

import numpy as np
import yfinance
from tqdm import tqdm

from . import utils


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

    def fill(self) -> None:
        for symbol in tqdm(self.ticker_symbols):
            ticker = yfinance.Ticker(symbol)
            ticker_df = ticker.history(period=f"{self.period_years}y", interval=f"{self.interval}d")[::-1]

            close_values = ticker_df["Close"].values
            dates = ticker_df.index.values

            label = self.symbol_to_label[symbol]
            self.values[label, :len(close_values)] = close_values
            self.dates[label, :len(dates)] = dates
            self.nb_of_valid_values[label] = len(dates)

        self.is_filled = True

    def create_filename_for_today(self) -> str:
        current_date = datetime.now().strftime("%Y_%m_%d")
        file_name = f"{self.period_years}y_{self.interval}d_{current_date}.pk"
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
