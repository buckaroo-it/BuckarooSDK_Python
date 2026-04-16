"""Extended test helpers with per-method response factories.

Builds on :class:`helpers.TestHelpers` with response shapes for specific
Buckaroo actions (pending redirect, refund, etc.).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .helpers import TestHelpers as _Base


class TestHelpers(_Base):
    """Response factories for feature tests."""

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
