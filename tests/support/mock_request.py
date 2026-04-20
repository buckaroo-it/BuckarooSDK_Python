"""Expected request + canned response used by :class:`MockBuckaroo`."""

from __future__ import annotations

import json as _json
import re
from fnmatch import translate
from typing import Any, Dict, Optional

from buckaroo.http.strategies.http_strategy import HttpResponse


class BuckarooMockRequest:
    """One expected HTTP request paired with a canned response or exception.

    URL patterns support three modes:

    - exact match: the pattern must equal the URL byte-for-byte.
    - ``*`` wildcard glob: any pattern containing ``*`` is matched with
      :func:`fnmatch.translate` + :func:`re.fullmatch`.
    - ``/regex/`` delimited regex: patterns wrapped in forward slashes are
      matched with :func:`re.search` (inner text is the regex).
    """

    def __init__(self, method: str, url_pattern: str) -> None:
        self._method = method.upper()
        self._url_pattern = url_pattern
        self._url_matcher = self._compile_url_matcher(url_pattern)
        self._status = 200
        self._headers: Dict[str, str] = {}
        self._body: Any = None
        self._raw_text: Optional[str] = None
        self._content_type: str = "application/json"
        self._exception: Optional[BaseException] = None

    @staticmethod
    def _compile_url_matcher(pattern: str):
        if len(pattern) >= 2 and pattern.startswith("/") and pattern.endswith("/"):
            compiled = re.compile(pattern[1:-1])
            return lambda url: compiled.search(url) is not None
        if "*" in pattern:
            compiled = re.compile(translate(pattern))
            return lambda url: compiled.fullmatch(url) is not None
        return lambda url: url == pattern

    @classmethod
    def json(
        cls,
        method: str,
        url_pattern: str,
        body: Any,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> "BuckarooMockRequest":
        req = cls(method, url_pattern)
        req._status = status
        req._body = body
        req._headers = dict(headers) if headers else {}
        return req

    @classmethod
    def text(
        cls,
        method: str,
        url_pattern: str,
        body: str,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        content_type: str = "text/html",
    ) -> "BuckarooMockRequest":
        """Canned raw-text (non-JSON) response. Body is emitted verbatim."""
        req = cls(method, url_pattern)
        req._status = status
        req._raw_text = body
        req._content_type = content_type
        req._headers = dict(headers) if headers else {}
        return req

    def with_exception(self, exc: BaseException) -> "BuckarooMockRequest":
        self._exception = exc
        return self

    @property
    def exception(self) -> Optional[BaseException]:
        return self._exception

    def matches(self, method: str, url: str) -> bool:
        if method.upper() != self._method:
            return False
        return self._url_matcher(url)

    def mismatch_message(self, method: str, url: str) -> str:
        return (
            "Buckaroo request mismatch\n"
            f"expected: {self._method} {self._url_pattern}\n"
            f"actual:   {method.upper()} {url}"
        )

    def to_http_response(self) -> HttpResponse:
        headers = {"Content-Type": self._content_type, **self._headers}
        text = self._raw_text if self._raw_text is not None else _json.dumps(self._body)
        return HttpResponse(
            status_code=self._status,
            headers=headers,
            text=text,
            success=200 <= self._status < 300,
        )

