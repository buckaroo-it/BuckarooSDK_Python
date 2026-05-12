"""
HTTP Client Strategies for Buckaroo SDK.

This package provides different HTTP client implementations using the strategy pattern.
"""

from .http_strategy import HttpStrategy, HttpResponse
from .requests_strategy import RequestsStrategy
from .curl_strategy import CurlStrategy
from .strategy_factory import HttpStrategyFactory

__all__ = [
    "HttpStrategy",
    "HttpResponse",
    "RequestsStrategy",
    "CurlStrategy",
    "HttpStrategyFactory",
]
