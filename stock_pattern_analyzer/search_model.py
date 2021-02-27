import pickle
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.preprocessing import minmax_scale

from .data import RawStockDataHolder
from .search_index import FaissQuantizedIndex, cKDTreeIndex

MINIMUM_WINDOW_SIZE = 5


class SearchModel:
    def __init__(self, data_holder: RawStockDataHolder, window_size: int):
        if window_size < MINIMUM_WINDOW_SIZE:
            raise ValueError(f"Window size is too small. Minimum is {MINIMUM_WINDOW_SIZE}")
        self.window_size = window_size
        self._data_holder = data_holder

        self.index = None

        # TODO: solve this more efficiently without wasting memory
        # This stores the start and end indices in the original array of the windows
        self.start_end_indices_in_original_array = None
        # This stores the ticket symbol label associated with every window
        self.labels = None

        self.is_built = False

    def _create_windows(self):
        if not self._data_holder.is_filled:
            raise ValueError("Data holder needs to be filled first")

        windows = []
        self.start_end_indices_in_original_array = []
        self.labels = []

        # TODO: this for-loop should be vectorized
        for symbol in self._data_holder.ticker_symbols:
            label = self._data_holder.symbol_to_label[symbol]
            nb_valid_values = self._data_holder.nb_of_valid_values[label]

            symbol_values = self._data_holder.values[label][:nb_valid_values]
            # Vectorized sliding window creation
            window_indices = np.arange(symbol_values.shape[0] - self.window_size + 1)[:, None] + np.arange(
                self.window_size)
            windows.extend(symbol_values[window_indices])
            self.start_end_indices_in_original_array.extend(window_indices[:, (0, -1)])
            self.labels.extend([label] * len(window_indices))

        self.start_end_indices_in_original_array = np.array(self.start_end_indices_in_original_array)
        self.labels = np.array(self.labels)
        windows = np.array(windows)
        windows = minmax_scale(windows, feature_range=(0, 1), axis=1)

        windows = np.nan_to_num(windows)
        return windows

    def build_search_tree(self):
        X = self._create_windows()
        self.index = FaissQuantizedIndex()
        # self.index = cKDTreeSearch()
        self.index.create(X.astype(np.float32))
        self.is_built = True

    def search(self, values: np.ndarray, k: int = 5) -> tuple:
        if not self.is_built:
            raise ValueError("You need to build teh search tree first")

        values = minmax_scale(values, feature_range=(0, 1))
        if len(values.shape) == 1:
            values = values.reshape(1, -1)
        values = values.astype(np.float32)

        top_k_distances, top_k_indices = self.index.query(q=values, k=k)
        top_k_distances = top_k_distances.ravel()
        top_k_indices = top_k_indices.ravel()

        return top_k_indices, top_k_distances

    def get_window_symbol_label(self, index: int):
        return self.labels[index]

    def get_window_symbol(self, index: int) -> str:
        label = self.get_window_symbol_label(index)
        return self._data_holder.label_to_symbol[label]

    def _get_label_and_start_end_indices(self, index: int, future_length: int):
        start_index, end_index = self.start_end_indices_in_original_array[index]
        label = self.get_window_symbol_label(index)

        if future_length > 0:
            start_index -= future_length
            if start_index < 0:
                start_index = 0
        return label, start_index, end_index

    def get_window_dates(self, index: int, future_length: int = 0) -> np.ndarray:
        label, start_index, end_index = self._get_label_and_start_end_indices(index, future_length)
        dates = self._data_holder.dates[label][start_index:end_index + 1]
        return dates

    def get_window_values(self, index: int, future_length: int = 0):
        label, start_index, end_index = self._get_label_and_start_end_indices(index, future_length)
        values = self._data_holder.values[label][start_index:end_index + 1]
        return values

    def get_start_end_date(self, index: int, future_length: int = 0) -> tuple:
        dates = self.get_window_dates(index, future_length)
        return dates[0], dates[-1]

    def create_filename_for_today(self) -> str:
        current_date = datetime.now().strftime("%Y_%m_%d")
        file_name = f"search_tree_{self.window_size}win_{current_date}.pk"
        return file_name

    def serialize(self) -> str:
        if not self.is_built:
            raise ValueError("You need to build the tree first")

        file_name = self.create_filename_for_today()
        with open(file_name, "wb") as f:
            pickle.dump(self, f)

        return file_name

    @staticmethod
    def load(file_name: str) -> "SearchModel":
        with open(file_name, "rb") as f:
            obj = pickle.load(f)
        return obj


def initialize_search_tree(data_holder: RawStockDataHolder, window_size: int, force_update: bool = False):
    search_tree = SearchModel(data_holder=data_holder, window_size=window_size)

    file_path = Path(search_tree.create_filename_for_today())

    if (not file_path.exists()) or force_update:
        search_tree.build_search_tree()
        # TODO: implement serialization
        # search_tree.serialize()
    else:
        search_tree = SearchModel.load(str(file_path))
    return search_tree
