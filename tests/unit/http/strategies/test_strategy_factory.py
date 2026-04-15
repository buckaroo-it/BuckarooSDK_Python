"""Unit tests for buckaroo.http.strategies.strategy_factory."""

import pytest

from buckaroo.http.strategies.strategy_factory import HttpStrategyFactory
from buckaroo.http.strategies.requests_strategy import RequestsStrategy
from buckaroo.http.strategies.curl_strategy import CurlStrategy


# ---------------------------------------------------------------------------
# Auto-detect (no preferred strategy)
# ---------------------------------------------------------------------------


def test_create_strategy_auto_returns_requests_when_available(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: True)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: True)

    strategy = HttpStrategyFactory.create_strategy()

    assert isinstance(strategy, RequestsStrategy)


def test_create_strategy_auto_falls_back_to_curl_when_requests_unavailable(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: False)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: True)

    strategy = HttpStrategyFactory.create_strategy()

    assert isinstance(strategy, CurlStrategy)


def test_create_strategy_auto_raises_when_nothing_available(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: False)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: False)

    with pytest.raises(RuntimeError) as exc_info:
        HttpStrategyFactory.create_strategy()

    message = str(exc_info.value)
    assert "requests" in message
    assert "curl" in message


# ---------------------------------------------------------------------------
# Explicit selection
# ---------------------------------------------------------------------------


def test_create_strategy_explicit_requests_when_available(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: True)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: True)

    strategy = HttpStrategyFactory.create_strategy("requests")

    assert isinstance(strategy, RequestsStrategy)


def test_create_strategy_explicit_curl_when_available(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: True)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: True)

    strategy = HttpStrategyFactory.create_strategy("curl")

    assert isinstance(strategy, CurlStrategy)


def test_create_strategy_explicit_requests_unavailable_raises_with_available(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: False)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: True)

    with pytest.raises(RuntimeError) as exc_info:
        HttpStrategyFactory.create_strategy("requests")

    message = str(exc_info.value)
    assert "requests" in message
    assert "curl" in message


def test_create_strategy_bogus_name_raises(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: True)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: True)

    with pytest.raises(RuntimeError) as exc_info:
        HttpStrategyFactory.create_strategy("bogus")

    assert "bogus" in str(exc_info.value)


def test_create_strategy_case_insensitive(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: True)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: True)

    strategy = HttpStrategyFactory.create_strategy("REQUESTS")

    assert isinstance(strategy, RequestsStrategy)


# ---------------------------------------------------------------------------
# Availability introspection
# ---------------------------------------------------------------------------


def test_get_available_strategies_both_available(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: True)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: True)

    assert HttpStrategyFactory.get_available_strategies() == ["requests", "curl"]


def test_get_available_strategies_only_curl(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: False)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: True)

    assert HttpStrategyFactory.get_available_strategies() == ["curl"]


def test_get_available_strategies_none(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: False)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: False)

    assert HttpStrategyFactory.get_available_strategies() == []


def test_is_strategy_available_requests(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: True)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: False)

    assert HttpStrategyFactory.is_strategy_available("requests") is True


def test_is_strategy_available_curl_false(monkeypatch):
    monkeypatch.setattr(RequestsStrategy, "is_available", lambda self: True)
    monkeypatch.setattr(CurlStrategy, "is_available", lambda self: False)

    assert HttpStrategyFactory.is_strategy_available("curl") is False


def test_is_strategy_available_bogus(monkeypatch):
    assert HttpStrategyFactory.is_strategy_available("bogus") is False
