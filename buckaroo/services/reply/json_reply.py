"""JSON push verifier (HMAC-SHA256 over the ``Authorization`` header).

Mirrors PHP ``Handlers/Reply/Json.php`` (which delegates to
``Handlers/HMAC/Validator.php``). Buckaroo signs JSON push notifications
with an HMAC-SHA256 hash carried in the
``Authorization: hmac key:hash:nonce:time`` header. Verification recomputes
the hash from the URL, method, body, and merchant credentials, then
compares constant-time.

Module file is ``json_reply.py`` (not ``json.py``) to avoid shadowing the
stdlib :mod:`json`. Class name is :class:`Json` for parity with the PHP SDK.
"""

from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
from typing import Optional, Union
from urllib.parse import quote


class Json:
    """Verify HMAC-SHA256 signatures on JSON-style Buckaroo pushes."""

    def __init__(self, store_key: str, secret_key: str) -> None:
        if store_key is None or not store_key.strip():
            raise ValueError("Store key must be provided")
        if secret_key is None or not secret_key.strip():
            raise ValueError("Secret key must be provided")
        self.store_key = store_key.strip()
        self.secret_key = secret_key.strip()

    def validate(
        self,
        authorization: Optional[str],
        uri: str,
        method: str,
        body: Union[str, bytes, None] = "",
    ) -> bool:
        """Return True if ``authorization`` is a valid HMAC for the request."""
        if not authorization:
            return False

        parts = authorization.split(":")
        if len(parts) != 4:
            return False
        provided_hash = parts[1]
        nonce = parts[2]
        timestamp = parts[3]

        content_b64 = self._md5_b64(body)
        encoded_url = self._encode_url(uri)
        signing_string = (
            f"{self.store_key}{method}{encoded_url}{timestamp}{nonce}{content_b64}"
        )
        expected = base64.b64encode(
            _hmac.new(
                self.secret_key.encode("utf-8"),
                signing_string.encode("utf-8"),
                hashlib.sha256,
            ).digest()
        ).decode("ascii")

        return _hmac.compare_digest(provided_hash, expected)

    @staticmethod
    def _md5_b64(body: Union[str, bytes, None]) -> str:
        if not body:
            return ""
        if isinstance(body, str):
            body = body.encode("utf-8")
        return base64.b64encode(hashlib.md5(body).digest()).decode("ascii")

    @staticmethod
    def _encode_url(url: str) -> str:
        if url.startswith("https://"):
            url = url[8:]
        elif url.startswith("http://"):
            url = url[7:]
        return quote(url, safe="").lower()
