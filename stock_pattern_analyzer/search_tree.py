from sklearn.neighbors import KDTree

from .data import RawStockDataHolder
import numpy as np

MINIMUM_WINDOW_SIZE = 5


class SearchTree:
    def __init__(self, data_holder: RawStockDataHolder, window_size: int):
        if window_size < MINIMUM_WINDOW_SIZE:
            raise ValueError(f"Window size is too small. Minimum is {MINIMUM_WINDOW_SIZE}")
        self.window_size = window_size
        self._data_holder = data_holder

        self.kdtree = None

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
        # TODO: normalize every window
        # norm_windows = normalize(windows)
        return windows

    def build_search_tree(self):
        X = self._create_windows()
        self.kdtree = KDTree(X)
        self.is_built = True

    def search(self, values: np.ndarray, k: int = 5) -> tuple:
        if not self.is_built:
            raise ValueError("You need to build teh search tree first")

        if len(values.shape) == 1:
            values = values.reshape(1, -1)

        top_k_distances, top_k_indices = self.kdtree.query(values, k=k)
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
