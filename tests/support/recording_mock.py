"""Recording variant of :class:`MockBuckaroo` plus a stub client wiring helper.

Phase-4 tests wire a real :class:`BuckarooHttpClient` to a recording HTTP
strategy so they can assert the exact request shape that reached the wire
(via ``json.loads(call["data"])``). The pattern was copy-pasted across 7
test files before being consolidated here.

Usage::

    from tests.support.recording_mock import (
        recorded_action,
        recorded_request,
        wire_recording_http,
    )

    def test_something():
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))

        # ...drive the SUT via client.http_client...

        assert recorded_action(mock) == "Pay"
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from buckaroo.config.buckaroo_config import BuckarooConfig
from buckaroo.http.client import BuckarooHttpClient

from .mock_buckaroo import MockBuckaroo


class RecordingMock(MockBuckaroo):
    """:class:`MockBuckaroo` variant that records every outgoing request."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: List[Dict[str, Any]] = []

    def request(self, method, url, headers=None, data=None, timeout=None, verify_ssl=True):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers) if headers else {},
                "data": data,
                "timeout": timeout,
                "verify_ssl": verify_ssl,
            }
        )
        return super().request(method, url, headers, data, timeout, verify_ssl)


class StubClient:
    """Thin stand-in for :class:`BuckarooClient` that exposes ``http_client``."""

    def __init__(self, mock: RecordingMock, *, config: Optional[BuckarooConfig] = None) -> None:
        self.http_client = BuckarooHttpClient(
            store_key="test_store_key",
            secret_key="test_secret_key",
            config=config or BuckarooConfig(),
        )
        self.http_client.http_strategy = mock


def wire_recording_http(
    *, config: Optional[BuckarooConfig] = None
) -> Tuple[RecordingMock, StubClient]:
    """Return a fresh ``(mock, stub_client)`` pair wired together.

    The returned stub client has a real :class:`BuckarooHttpClient` whose
    ``http_strategy`` is the recording mock, so every call made through the
    client is appended to ``mock.calls``.
    """
    mock = RecordingMock()
    client = StubClient(mock, config=config)
    return mock, client


def recorded_request(mock: RecordingMock) -> Dict[str, Any]:
    """Return the single recorded call's parsed JSON body.

    Fails the test if zero or more than one call was recorded.
    """
    assert len(mock.calls) == 1, f"expected 1 call, got {len(mock.calls)}"
    return json.loads(mock.calls[0]["data"])


def recorded_action(mock: RecordingMock) -> str:
    """Return the ``Action`` from the single recorded call's first service."""
    return recorded_request(mock)["Services"]["ServiceList"][0]["Action"]
