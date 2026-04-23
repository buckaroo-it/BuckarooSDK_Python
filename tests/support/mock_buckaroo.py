"""Queue-based fake :class:`HttpStrategy` for deterministic SDK tests.

Drop-in replacement for :class:`RequestsStrategy` / :class:`CurlStrategy`.
Queue expected requests in order; every outgoing call pops the next and
returns its canned response.

Usage::

    from tests.support.mock_buckaroo import MockBuckaroo
    from tests.support.mock_request import BuckarooMockRequest

    def test_it(mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/Transaction*",
                {"Key": "abc", "Status": {"Code": {"Code": 190}}},
            )
        )

        # inject mock_strategy as the http strategy for your client
        response = mock_strategy.request("POST", "https://x/json/Transaction")
        assert response.json()["Status"]["Code"]["Code"] == 190
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Dict, Iterable, Optional

from buckaroo.http.strategies.http_strategy import HttpResponse, HttpStrategy

from .mock_request import BuckarooMockRequest


class MockBuckaroo(HttpStrategy):
    """Order-based fake HTTP strategy. Queue requests, then call ``request``."""

    def __init__(self) -> None:
        self._queue: Deque[BuckarooMockRequest] = deque()

    def configure(self, **kwargs) -> None:
        return None

    def is_available(self) -> bool:
        return True

    def get_name(self) -> str:
        return "mock"

    def queue(self, req: BuckarooMockRequest) -> "MockBuckaroo":
        self._queue.append(req)
        return self

    def queue_many(self, reqs: Iterable[BuckarooMockRequest]) -> "MockBuckaroo":
        self._queue.extend(list(reqs))
        return self

    def reset(self) -> None:
        self._queue.clear()

    def assert_all_consumed(self) -> None:
        leftover = len(self._queue)
        if leftover > 0:
            raise AssertionError(f"{leftover} Buckaroo mock request(s) were not consumed")

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[str] = None,
        timeout: Optional[int] = None,
        verify_ssl: bool = True,
    ) -> HttpResponse:
        if not self._queue:
            raise AssertionError(
                f"Unexpected Buckaroo call with no mocks left: {method.upper()} {url}"
            )

        expected = self._queue[0]
        if not expected.matches(method, url):
            raise AssertionError(expected.mismatch_message(method, url))

        self._queue.popleft()

        if expected.exception is not None:
            raise expected.exception

        return expected.to_http_response()
