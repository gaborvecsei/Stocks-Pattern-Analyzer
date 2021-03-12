import os
import time
import json

import numpy as np
from tqdm import tqdm

import stock_pattern_analyzer as spa

NB_STOCKS = 100
NB_DAYS_PER_STOCK = 5 * 365
WINDOW_SIZES = [5, 10, 20, 50, 100]


def create_windows(X, window_size: int):
    window_indices = np.arange(X.shape[0] - window_size + 1)[:, None] + np.arange(window_size)
    return X[window_indices]


def over_estimate_memory_footprint(model):
    """
    A good over-approximation for the memory footprint is the file size of the pickled object
    Based on https://stackoverflow.com/a/565382/5108062
    """

    tmp_filename = "test.pk"
    model.serialize(tmp_filename)
    size_of_the_file = os.path.getsize(tmp_filename)
    os.remove(tmp_filename)
    return size_of_the_file


def measure_build_time(model_class, windowed_data):
    start_time = time.time()
    model = model_class()
    model.create(windowed_data)
    end_time = time.time()
    build_time = end_time - start_time
    return model, build_time


def estimate_query_speed(model, windowed_data, N: int):
    query = windowed_data[0]
    start_time = time.time()
    for i in range(N):
        _ = model.query(query, k=10)
    end_time = time.time()
    query_time = (end_time - start_time) / N
    return query_time


def perform_measurements():
    max_values = NB_STOCKS * NB_DAYS_PER_STOCK
    X = np.random.random(max_values)

    res_dict = {}

    for model_class in tqdm([spa.cKDTreeIndex, spa.FastIndex, spa.MemoryEfficientIndex]):
        res_dict[model_class.__name__] = {}
        for window_size in WINDOW_SIZES:
            res_dict[model_class.__name__][window_size] = {}
            data = create_windows(X, window_size)

            model, build_time = measure_build_time(model_class, data)
            res_dict[model_class.__name__][window_size]["build_time"] = build_time

            memory_footprint = over_estimate_memory_footprint(model)
            res_dict[model_class.__name__][window_size]["memory_footprint"] = memory_footprint

            query_speed = estimate_query_speed(model, data, 10)
            res_dict[model_class.__name__][window_size]["query_speed"] = query_speed

    with open("measurement_results.json", "w") as f:
        json.dump(res_dict, f)


if __name__ == "__main__":
    perform_measurements()
