"""Form-encoded push verifier (SHA-1 over ``brq_signature``).

Mirrors PHP ``Handlers/Reply/HttpPost.php``. Buckaroo signs form-style push
notifications with a SHA-1 digest over the sorted ``brq_*`` / ``add_*`` /
``cust_*`` parameters concatenated with the merchant secret key, delivered
in the ``brq_signature`` field of the form body.
"""

from __future__ import annotations

import hmac
from hashlib import sha1
from typing import Mapping
from urllib.parse import unquote_plus


class HttpPost:
    """Verify SHA-1 signatures on form-style Buckaroo pushes."""

    SIGNATURE_FIELD = "brq_signature"
    INCLUDE_PREFIXES = ("add_", "brq_", "cust_")

    def __init__(self, secret_key: str) -> None:
        if secret_key is None or not secret_key.strip():
            raise ValueError("Secret key must be provided")
        self.secret_key = secret_key.strip()

    def validate(self, params: Mapping[str, object]) -> bool:
        """Return True if ``params['brq_signature']`` matches the computed signature."""
        provided = next(
            (v for k, v in params.items() if k.lower() == self.SIGNATURE_FIELD),
            None,
        )
        if not provided or not isinstance(provided, str):
            return False
        expected = self.compute_signature(params)
        return hmac.compare_digest(provided, expected)

    def compute_signature(self, params: Mapping[str, object]) -> str:
        """Compute the expected SHA-1 signature for a form-style push."""
        decoded = [
            (k, unquote_plus(v) if isinstance(v, str) else v)
            for k, v in params.items()
            if k.lower() != self.SIGNATURE_FIELD
        ]
        filtered = [
            (k, v)
            for k, v in decoded
            if any(k.lower().startswith(p) for p in self.INCLUDE_PREFIXES)
        ]
        sorted_items = sorted(filtered, key=lambda pair: pair[0].lower())
        sign_string = "".join(f"{k}={v if v is not None else ''}" for k, v in sorted_items)
        sign_string += self.secret_key
        return sha1(sign_string.encode("utf-8")).hexdigest()
