"""Hosted Fields token service for Buckaroo credit card tokenization.

The Buckaroo Hosted Fields iframe tokenizes card data client-side, keeping
PAN/CVV out of the merchant server. The iframe needs a short-lived JWT,
minted via the OAuth2 ``client_credentials`` flow against
``auth.buckaroo.io`` using the merchant's Hosted Fields client_id /
client_secret pair (distinct from the Buckaroo store key / secret key
used for HMAC-signed API calls).

The PHP SDK does not include this service; OAuth is out of scope for the
core transaction API. This module exists only to consolidate the Hosted
Fields token exchange in one place.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from ..exceptions._buckaroo_error import BuckarooError
from ..http.strategies import HttpStrategy, HttpStrategyFactory


class HostedFieldsService:
    """Mint OAuth access tokens for the Buckaroo Hosted Fields iframe."""

    OAUTH_TOKEN_URL = "https://auth.buckaroo.io/oauth/token"
    GRANT_TYPE = "client_credentials"
    DEFAULT_SCOPE = "hostedfields:save"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        http_strategy: Optional[HttpStrategy] = None,
        timeout: int = 10,
    ) -> None:
        if client_id is None or not client_id.strip():
            raise ValueError("Client ID must be provided")
        if client_secret is None or not client_secret.strip():
            raise ValueError("Client secret must be provided")

        self._client_id = client_id.strip()
        self._client_secret = client_secret.strip()
        self._timeout = timeout
        self._injected_strategy = http_strategy
        self._strategy: Optional[HttpStrategy] = None

    def _get_strategy(self) -> HttpStrategy:
        if self._injected_strategy is not None:
            return self._injected_strategy
        if self._strategy is None:
            self._strategy = HttpStrategyFactory.create_strategy()
            self._strategy.configure()
        return self._strategy

    def get_token(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """Mint a Hosted Fields access token. Returns the decoded JSON body."""
        scope = scope or self.DEFAULT_SCOPE
        credentials = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode("utf-8")
        ).decode("ascii")
        body = urlencode({"scope": scope, "grant_type": self.GRANT_TYPE})

        try:
            response = self._get_strategy().request(
                method="POST",
                url=self.OAUTH_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=body,
                timeout=self._timeout,
            )
        except Exception as exc:
            if isinstance(exc, BuckarooError):
                raise
            raise BuckarooError(f"Hosted Fields token request failed: {exc}") from exc

        if not response.success:
            error = self._extract_error(response.text)
            raise BuckarooError(
                f"Hosted Fields token request failed (status {response.status_code}): {error}"
            )

        text = response.text or ""
        if not text.strip():
            raise BuckarooError("Hosted Fields token response was empty")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise BuckarooError(
                f"Failed to parse Hosted Fields token response JSON: {exc}"
            ) from exc

    @staticmethod
    def _extract_error(text: Optional[str]) -> str:
        """Pull RFC6749 error fields from the response without echoing the full body."""
        if not text:
            return "no body"
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return "non-JSON body"
        if not isinstance(data, dict):
            return "unexpected body shape"
        code = data.get("error") or "unknown_error"
        description = data.get("error_description")
        return f"{code}: {description}" if description else code
