from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SuccessResponse(BaseModel):
    message: str = "Successful"


class SearchWindowSizeResponse(BaseModel):
    sizes: List[int]


class AvailableSymbolsResponse(BaseModel):
    symbols: List[str]


class MatchResponse(BaseModel):
    symbol: str
    distance: float
    start_date: str
    end_date: str
    todays_value: Optional[float]
    future_value: Optional[float]
    change: Optional[float]
    values: Optional[List[float]]


class TopKSearchResponse(BaseModel):
    matches: List[MatchResponse] = []
    forecast_type: str
    forecast_confidence: float
    anchor_symbol: str
    anchor_values: Optional[List[float]]
    window_size: int
    top_k: int
    future_size: int


class DataRefreshResponse(BaseModel):
    message: str = "Last (most recent) refresh"
    date: datetime


class IsReadyResponse(BaseModel):
    is_ready: bool
