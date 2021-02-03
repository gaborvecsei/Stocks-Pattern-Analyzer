import numpy as np
import pandas as pd


def min_max_scale(x, axis=0):
    # If axis=0 then columns are normalized, if it is 1 then rows
    return (x - np.min(x, axis=axis)) / np.ptp(x, axis=axis)


def date_to_str(date):
    return pd.to_datetime(str(date)).strftime("%Y_%m_%d")
