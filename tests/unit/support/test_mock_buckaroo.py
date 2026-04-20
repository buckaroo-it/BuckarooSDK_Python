"""Tests for tests.support.mock_buckaroo."""

import pytest

from buckaroo.http.strategies.http_strategy import HttpStrategy
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


def test_mock_buckaroo_is_http_strategy_subclass():
    assert issubclass(MockBuckaroo, HttpStrategy)
    assert isinstance(MockBuckaroo(), HttpStrategy)


def test_is_available_and_get_name():
    mock = MockBuckaroo()
    assert mock.is_available() is True
    assert mock.get_name() == "mock"


def test_configure_accepts_any_kwargs():
    mock = MockBuckaroo()
    mock.configure(timeout=5, retry_attempts=1)  # must not raise


def test_queue_and_queue_many_return_self():
    mock = MockBuckaroo()
    req = BuckarooMockRequest.json("POST", "https://x/a", {})
    assert mock.queue(req) is mock
    assert mock.queue_many([BuckarooMockRequest.json("POST", "https://x/b", {})]) is mock


def test_request_consumes_queued_response():
    mock = MockBuckaroo()
    mock.queue(BuckarooMockRequest.json("POST", "https://x/a", {"ok": True}))
    response = mock.request("POST", "https://x/a", data="payload")
    assert response.status_code == 200
    assert response.success is True
    assert response.json() == {"ok": True}


def test_request_empty_queue_raises_assertion_error():
    mock = MockBuckaroo()
    with pytest.raises(AssertionError) as ei:
        mock.request("POST", "https://x/a")
    msg = str(ei.value)
    assert "POST" in msg
    assert "https://x/a" in msg


def test_request_method_mismatch_raises_with_expected_and_actual():
    mock = MockBuckaroo()
    mock.queue(BuckarooMockRequest.json("POST", "https://x/a", {}))
    with pytest.raises(AssertionError) as ei:
        mock.request("GET", "https://x/a")
    msg = str(ei.value)
    assert "expected" in msg.lower()
    assert "POST https://x/a" in msg
    assert "GET https://x/a" in msg


def test_request_url_mismatch_raises_with_expected_and_actual():
    mock = MockBuckaroo()
    mock.queue(BuckarooMockRequest.json("POST", "https://x/a", {}))
    with pytest.raises(AssertionError) as ei:
        mock.request("POST", "https://x/other")
    msg = str(ei.value)
    assert "https://x/a" in msg
    assert "https://x/other" in msg


def test_request_with_exception_raises_that_exception():
    mock = MockBuckaroo()
    err = RuntimeError("boom")
    mock.queue(
        BuckarooMockRequest.json("POST", "https://x/a", {}).with_exception(err)
    )
    with pytest.raises(RuntimeError) as ei:
        mock.request("POST", "https://x/a")
    assert ei.value is err


def test_assert_all_consumed_passes_on_empty():
    mock = MockBuckaroo()
    mock.assert_all_consumed()  # no raise


def test_assert_all_consumed_raises_with_leftover_count():
    mock = MockBuckaroo()
    mock.queue_many([
        BuckarooMockRequest.json("POST", "https://x/a", {}),
        BuckarooMockRequest.json("POST", "https://x/b", {}),
    ])
    with pytest.raises(AssertionError) as ei:
        mock.assert_all_consumed()
    assert "2" in str(ei.value)


def test_reset_clears_queue():
    mock = MockBuckaroo()
    mock.queue(BuckarooMockRequest.json("POST", "https://x/a", {}))
    mock.reset()
    mock.assert_all_consumed()  # no raise


def test_requests_consume_in_order():
    mock = MockBuckaroo()
    mock.queue_many([
        BuckarooMockRequest.json("POST", "https://x/a", {"n": 1}),
        BuckarooMockRequest.json("POST", "https://x/b", {"n": 2}),
    ])
    r1 = mock.request("POST", "https://x/a")
    r2 = mock.request("POST", "https://x/b")
    assert r1.json() == {"n": 1}
    assert r2.json() == {"n": 2}
    mock.assert_all_consumed()


def test_mock_strategy_fixture_yields_fresh_instance(mock_strategy):
    assert isinstance(mock_strategy, MockBuckaroo)
