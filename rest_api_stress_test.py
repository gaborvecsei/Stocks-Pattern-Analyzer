import concurrent.futures
import time

import numpy as np
import requests

BASE_URL = "http://localhost:8001"


def search_recent(symbol: str, window_size: int, future_size: int, top_k: int):
    s = time.time()
    url = f"{BASE_URL}/search/recent/?symbol={symbol.upper()}&window_size={window_size}&top_k={top_k}&future_size={future_size}"
    _ = requests.get(url)
    e = time.time()
    return e - s


def print_stats(request_execution_times: list, start_time, end_time, N: int):
    request_execution_times = np.array(request_execution_times)
    print("Statistics:")

    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.4f}")
    print(f"FPS: {1 / execution_time:.4f}")

    print(f"(single) Request execution time: {request_execution_times.mean()}+/-{request_execution_times.std()} ")


def test_most_recent_search(N: int):
    print(f"Recent search test with {N} requests")

    # # Sequential requests
    # print("Sequential requests")
    #
    # start_time = time.time()
    # request_execution_times = []
    # for i in range(N):
    #     exec_time = search_recent("AAPL", window_size=5, future_size=5, top_k=5)
    #     request_execution_times.append(exec_time)
    # end_time = time.time()
    #
    # print_stats(request_execution_times, start_time, end_time, N)
    # print("-" * 30)

    # Concurrent requests
    print("Concurrent requests")

    start_time = time.time()
    request_execution_times = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=None) as pool:
        futures = {}
        for i in range(N):
            # Previous manual tests showed there is no latency when using bigger sizes
            # (tested to the maximum allowed window length)
            f = pool.submit(search_recent, symbol="AAPL", window_size=5, future_size=5, top_k=5)
            futures[f] = i

        for future in concurrent.futures.as_completed(futures):
            try:
                exec_time = future.result()
                request_execution_times.append(exec_time)
            except Exception as e:
                print(e)

    end_time = time.time()

    print_stats(request_execution_times, start_time, end_time, N)
    print("-" * 30)


if __name__ == "__main__":
    test_most_recent_search(10)
