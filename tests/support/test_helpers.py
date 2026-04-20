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
    """Fixture builders for Buckaroo-shaped payloads and responses."""

    @staticmethod
    def generate_transaction_key() -> str:
        """Return a 32-character uppercase hex transaction key."""
        return secrets.token_hex(16).upper()

    @staticmethod
    def standard_payload(invoice: str = "INV-1", **overrides: Any) -> Dict[str, Any]:
        """Return the standard create_payment payload every feature test uses.

        ``overrides`` are shallow-merged over the defaults, so callers can
        adjust or add fields (e.g. ``service_parameters``) per-test.
        """
        payload: Dict[str, Any] = {
            "currency": "EUR",
            "amount": 10.00,
            "description": "Test",
            "invoice": invoice,
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }
        payload.update(overrides)
        return payload

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

    @staticmethod
    def pending_redirect_response(
        service_name: str,
        action: str = "Pay",
        redirect_url: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Buckaroo-shaped pending response with redirect action."""
        tx_key = TestHelpers.generate_transaction_key()
        if redirect_url is None:
            redirect_url = f"https://checkout.buckaroo.nl/redirect/{tx_key}"
        response: Dict[str, Any] = {
            "Key": tx_key,
            "Status": {
                "Code": {"Code": 791, "Description": "Pending processing"},
                "SubCode": {"Code": "S001", "Description": "Transaction pending"},
                "DateTime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            },
            "RequiredAction": {
                "Name": "Redirect",
                "RedirectURL": redirect_url,
            },
            "Services": [
                {
                    "Name": service_name,
                    "Action": action,
                    "Parameters": [],
                }
            ],
            "Invoice": f"INV-{uuid.uuid4().hex[:13]}",
            "ServiceCode": service_name,
            "IsTest": True,
            "Currency": "EUR",
            "AmountDebit": 10.00,
        }
        if overrides:
            response.update(overrides)
        return response

    @staticmethod
    def refund_response(
        service_name: str,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Buckaroo-shaped successful refund response."""
        response = TestHelpers.success_response({
            "Services": [{"Name": service_name, "Action": "Refund", "Parameters": []}],
            "ServiceCode": service_name,
            "AmountCredit": 10.00,
            "AmountDebit": None,
        })
        if overrides:
            response.update(overrides)
        return response
