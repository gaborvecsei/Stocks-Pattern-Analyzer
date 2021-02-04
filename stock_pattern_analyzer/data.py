import pickle
from datetime import datetime

import numpy as np
import yfinance
from tqdm import tqdm

from . import utils


class DataHolder:
    def __init__(self, tickers: list, window_size: int, period_years: int = 5, interval: int = 1):
        self.tickers = tickers
        self.window_size = window_size
        self.period_years = period_years
        self.interval = interval

        # max values are calculated = years * interval days * 365
        self._max_values_per_stock = self.period_years * self.interval * 365

        # Max number of windows = number of years * days in a year * number of tickers
        self._max_nb_windows = (self._max_values_per_stock * len(self.tickers))

        # This holds the original values
        self.ticker_originals = np.zeros((len(self.tickers), self._max_values_per_stock), dtype=np.float32)

        # This holds the normalized values of the selected window from a stock
        self.ticker_windows_norm = np.zeros((self._max_nb_windows, self.window_size), dtype=np.float32)

        # This holds the start and end indices from a dataframe
        self.ticker_window_indices = np.zeros((self._max_nb_windows, 2), dtype=np.uint16)

        # Here we store the windows start and end dates
        self.ticker_window_dates = []

        # This holds which ticker the window belongs to (ticker is encoded with it's index in the list)
        self.window_labels = np.zeros(self._max_nb_windows, dtype=np.uint8)

        # As we are pre-allocating arrays, with this we can crop the unnecessary part which does not contain data
        self._useful_data_mask = np.zeros(self._max_nb_windows, dtype=bool)

        # This dict will hold the label to ticker mapping
        self.ticker_to_label = {}
        self.label_to_ticker = None

        # This gives back if the holder is filled with data or not
        self.is_data_downloaded = False

    def fill_data(self):
        row_index = 0

        for label, ticker in enumerate(tqdm(self.tickers)):
            # Df is reversed so the most recent values are at the top
            ticker_df = yfinance.Ticker(ticker).history(period=f"{self.period_years}y", interval=f"{self.interval}d")[
                        ::-1]
            close_values = ticker_df["Close"].values

            self.ticker_originals[label, :len(close_values)] = close_values
            self.ticker_to_label[ticker] = label

            for i in range(0, len(ticker_df) - self.window_size, 1):
                start_index = i
                end_index = i + self.window_size
                norm_values = utils.min_max_scale(close_values[start_index:end_index])
                start_date = ticker_df.index.values[start_index]
                end_date = ticker_df.index.values[end_index]

                self.ticker_window_indices[row_index, :] = [start_index, end_index]
                self.ticker_window_dates.append([start_date, end_date])
                self.ticker_windows_norm[row_index, :] = norm_values
                self.window_labels[row_index] = label
                self._useful_data_mask[row_index] = 1

                row_index += 1

        self.ticker_windows_norm = self.ticker_windows_norm[self._useful_data_mask]
        self.window_labels = self.window_labels[self._useful_data_mask]
        self.ticker_window_indices = self.ticker_window_indices[self._useful_data_mask]
        self.ticker_window_dates = np.array(self.ticker_window_dates)

        self.label_to_ticker = {v: k for k, v in self.ticker_to_label.items()}

        self.is_data_downloaded = True

    def get_date(self, index: int):
        start, end = self.ticker_window_dates[index]
        return start, end

    def get_ticker(self, index: int):
        return self.label_to_ticker[self.window_labels[index]]

    def get_norm_window(self, index: int):
        return self.ticker_windows_norm[index]

    def serialize(self, file_name: str = None):
        if not self.is_data_downloaded:
            raise ValueError("You need to fill the class with data first")

        if file_name is None:
            current_date = datetime.now().strftime("%Y_%m_%d")
            file_name = f"{self.period_years}y_{self.interval}d_{self.window_size}win_{current_date}"

        with open(file_name, "wb") as f:
            pickle.dump(self, f)

        return file_name

    @staticmethod
    def load(file_name: str) -> "DataHolder":
        with open(file_name, "rb") as f:
            obj = pickle.load(f)
        return obj
