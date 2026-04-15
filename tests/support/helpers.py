"""Reusable test helpers for the Buckaroo SDK test suite.

Mirrors ``tests/Support/TestHelpers.php`` from the PHP SDK so fixtures stay
consistent across both implementations.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

STATUS_SUCCESS = 190
STATUS_FAILED = 490
SUBCODE_SUCCESS = "S001"
SUBCODE_FAILED = "F001"


class TestHelpers:
    """Fixture builders for Buckaroo-shaped responses."""

    @staticmethod
    def generate_transaction_key() -> str:
        """Return a 32-character uppercase hex transaction key."""
        return secrets.token_hex(16).upper()

    @staticmethod
    def success_response(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return a Buckaroo-shaped success response dict.

        ``overrides`` is shallow-merged over the top-level dict.
        """
        response: Dict[str, Any] = {
            "Key": TestHelpers.generate_transaction_key(),
            "Status": {
                "Code": {"Code": STATUS_SUCCESS, "Description": "Success"},
                "SubCode": {"Code": SUBCODE_SUCCESS, "Description": "Transaction successful"},
                "DateTime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            },
            "RequiredAction": None,
            "Services": [],
            "Invoice": f"INV-{uuid.uuid4().hex[:13]}",
            "ServiceCode": "creditcard",
            "IsTest": True,
            "Currency": "EUR",
            "AmountDebit": 10.00,
        }
        if overrides:
            response.update(overrides)
        return response

    @staticmethod
    def failed_response(
        error: str = "Transaction failed",
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return a Buckaroo-shaped failed response dict.

        Mutates only ``Status.Code`` and ``Status.SubCode`` on top of
        :meth:`success_response`, then shallow-merges ``overrides`` over the
        top-level dict.
        """
        response = TestHelpers.success_response()
        response["Status"]["Code"] = {"Code": STATUS_FAILED, "Description": "Failed"}
        response["Status"]["SubCode"] = {"Code": SUBCODE_FAILED, "Description": error}
        if overrides:
            response.update(overrides)
        return response
