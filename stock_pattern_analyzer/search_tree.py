from sklearn.neighbors import KDTree

from .data import DataHolder


class SearchTree:
    def __init__(self, data_holder: DataHolder):
        self.tree = KDTree(data_holder.ticker_windows_norm)
        self._data_holder = data_holder

    def search_most_recent(self, ticker: str, k: int = 5):
        anchor_ticker_mask = self._data_holder.window_labels == self._data_holder.ticker_to_label[ticker]
        anchor_windows = self._data_holder.ticker_windows_norm[anchor_ticker_mask]
        anchor_values_norm = anchor_windows[0, :]

        top_k_distances, top_k_indices = self.tree.query(anchor_values_norm.reshape(1, -1), k=k)
        top_k_distances = top_k_distances.ravel()[1:]
        top_k_indices = top_k_indices.ravel()[1:]

        return top_k_indices, top_k_distances
