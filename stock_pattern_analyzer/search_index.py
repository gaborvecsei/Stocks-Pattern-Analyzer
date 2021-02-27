import abc
import pickle

import faiss
import numpy as np
from scipy.spatial.ckdtree import cKDTree


class BaseIndex:

    def __init__(self):
        self.index = None

    @abc.abstractmethod
    def create(self, X: np.ndarray):
        raise NotImplementedError()

    @abc.abstractmethod
    def query(self, q: np.ndarray, k: int):
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def load(cls, file_path: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def serialize(self, file_path: str):
        raise NotImplementedError()


class FaissSimpleIndex(BaseIndex):

    def __init__(self):
        super().__init__()

    def create(self, X: np.ndarray):
        self.index = faiss.IndexFlatL2(X.shape[-1])
        self.index.add(X)

    def query(self, q: np.ndarray, k: int):
        distances, indices = self.index.search(q, k)
        return distances[0], indices[0]

    @classmethod
    def load(cls, file_path: str):
        faiss.read_index(str(file_path))

    def serialize(self, file_path: str):
        faiss.write_index(self.index, str(file_path))


class FaissQuantizedIndex(BaseIndex):

    def __init__(self):
        super().__init__()

    def create(self, X: np.ndarray):
        d = X.shape[-1]
        if d % 4 == 0:
            m = 4
        elif d % 5 == 0:
            m = 5
        elif d % 2 == 0:
            m = 2
        else:
            raise ValueError("This is not handled, can not find a good value for m")
        quantizer = faiss.IndexFlatL2(d)
        self.index = faiss.IndexIVFPQ(quantizer, d, 100, m, 8)
        self.index.train(X)
        self.index.add(X)

    def query(self, q: np.ndarray, k: int):
        distances, indices = self.index.search(q, k)
        return distances[0], indices[0]

    @classmethod
    def load(cls, file_path: str):
        obj = cls()
        obj.index = faiss.read_index(str(file_path))
        return obj

    def serialize(self, file_path: str):
        faiss.write_index(self.index, str(file_path))


class cKDTreeIndex(BaseIndex):

    def __init__(self):
        super().__init__()

    def create(self, X: np.ndarray):
        self.index = cKDTree(data=X)

    def query(self, q: np.ndarray, k: int):
        top_k_distances, top_k_indices = self.index.query(x=q, k=k)
        return top_k_distances, top_k_indices

    @classmethod
    def load(cls, file_path: str):
        obj = cls()
        with open(file_path, "rb") as f:
            obj.index = pickle.load(f)
        return obj

    def serialize(self, file_path: str):
        with open(file_path, "wb") as f:
            pickle.dump(self.index, f)
