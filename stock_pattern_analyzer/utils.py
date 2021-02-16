import pandas as pd


def date_to_str(date):
    return pd.to_datetime(date).strftime("%Y_%m_%d")
