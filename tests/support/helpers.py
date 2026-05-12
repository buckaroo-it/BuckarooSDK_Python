"""Reusable test helpers for the Buckaroo SDK test suite.

Named ``Helpers`` (not ``TestHelpers``) so pytest doesn't auto-collect the
class under its ``Test*`` discovery rule.
"""

from __future__ import annotations

import json
import secrets
from typing import Any, Dict, Optional

from tests.support.mock_request import BuckarooMockRequest

STATUS_SUCCESS = 190
STATUS_FAILED = 490
SUBCODE_SUCCESS = "S001"
SUBCODE_FAILED = "F001"
FIXED_DATETIME = "2026-01-01T00:00:00"
FIXED_INVOICE = "INV-FIXED"


class Helpers:
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
            "Key": Helpers.generate_transaction_key(),
            "Status": {
                "Code": {"Code": STATUS_SUCCESS, "Description": "Success"},
                "SubCode": {"Code": SUBCODE_SUCCESS, "Description": "Transaction successful"},
                "DateTime": FIXED_DATETIME,
            },
            "RequiredAction": None,
            "Services": [],
            "Invoice": FIXED_INVOICE,
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
        response = Helpers.success_response()
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
        tx_key = Helpers.generate_transaction_key()
        if redirect_url is None:
            redirect_url = f"https://checkout.buckaroo.nl/redirect/{tx_key}"
        response: Dict[str, Any] = {
            "Key": tx_key,
            "Status": {
                "Code": {"Code": 791, "Description": "Pending processing"},
                "SubCode": {"Code": "S001", "Description": "Transaction pending"},
                "DateTime": FIXED_DATETIME,
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
            "Invoice": FIXED_INVOICE,
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
        response = Helpers.success_response(
            {
                "Services": [{"Name": service_name, "Action": "Refund", "Parameters": []}],
                "ServiceCode": service_name,
                "AmountCredit": 10.00,
                "AmountDebit": None,
            }
        )
        if overrides:
            response.update(overrides)
        return response

    @staticmethod
    def assert_pay_returns_pending_with_redirect(
        buckaroo: Any,
        mock_strategy: Any,
        *,
        method: str,
        invoice: str,
        service_params: Optional[Dict[str, Any]] = None,
        payload_overrides: Optional[Dict[str, Any]] = None,
        response_overrides: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Queue a pending-redirect mock, run ``pay()``, assert the common trio.

        Returns the ``PaymentResponse`` so callers can tack on extra
        per-method assertions (currency, amount_debit, etc.).
        """
        response_body = Helpers.pending_redirect_response(method, overrides=response_overrides)
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        overrides = dict(payload_overrides or {})
        overrides.pop("invoice", None)
        payload = Helpers.standard_payload(invoice=invoice, **overrides)
        if service_params is not None:
            payload["service_parameters"] = service_params
        response = buckaroo.payments.create_payment(method, payload).pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
        _assert_recorded_action(mock_strategy, "Pay")
        return response

    @staticmethod
    def assert_refund_returns_success(
        buckaroo: Any,
        mock_strategy: Any,
        *,
        method: str,
        invoice: str,
        original_transaction_key: str = "ABC123",
        payload_overrides: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Queue a refund-shaped response, run ``refund()``, assert success."""
        response_body = Helpers.refund_response(method)
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        overrides = {
            "description": "Refund",
            "original_transaction_key": original_transaction_key,
            **(payload_overrides or {}),
        }
        overrides.pop("invoice", None)
        payload = Helpers.standard_payload(invoice=invoice, **overrides)
        response = buckaroo.payments.create_payment(method, payload).refund()
        assert response.status.code.code == STATUS_SUCCESS
        assert response.key == response_body["Key"]
        _assert_recorded_action(mock_strategy, "Refund")
        return response

    @staticmethod
    def assert_instant_refund_returns_success(
        buckaroo: Any,
        mock_strategy: Any,
        *,
        method: str,
        invoice: str,
        original_transaction_key: str = "ABC123",
        payload_overrides: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Queue an InstantRefund-shaped response, run ``instantRefund()``."""
        response_body = Helpers.success_response(
            {
                "Services": [{"Name": method, "Action": "InstantRefund", "Parameters": []}],
                "ServiceCode": method,
                "AmountCredit": 10.00,
                "AmountDebit": None,
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        overrides = {
            "description": "Instant refund",
            "original_transaction_key": original_transaction_key,
            **(payload_overrides or {}),
        }
        overrides.pop("invoice", None)
        payload = Helpers.standard_payload(invoice=invoice, **overrides)
        response = buckaroo.payments.create_payment(method, payload).instantRefund()
        assert response.status.code.code == STATUS_SUCCESS
        assert response.key == response_body["Key"]
        _assert_recorded_action(mock_strategy, "instantRefund")
        return response

    @staticmethod
    def assert_action_returns_pending_with_redirect(
        buckaroo: Any,
        mock_strategy: Any,
        *,
        method: str,
        invoice: str,
        action_name: str,
        call_method: str,
        payload_overrides: Optional[Dict[str, Any]] = None,
        extra_builder_setup: Optional[Any] = None,
    ) -> Any:
        """Queue a pending-redirect mock for ``action_name``, invoke ``call_method``.

        ``extra_builder_setup`` is a callable that receives the builder
        before the action fires, so tests can ``add_parameter(...)``.
        """
        response_body = Helpers.pending_redirect_response(method, action_name)
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        overrides = dict(payload_overrides or {})
        overrides.pop("invoice", None)
        payload = Helpers.standard_payload(invoice=invoice, **overrides)
        builder = buckaroo.payments.create_payment(method, payload)
        if extra_builder_setup is not None:
            extra_builder_setup(builder)
        response = getattr(builder, call_method)()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
        _assert_recorded_action(mock_strategy, action_name)
        return response

    @staticmethod
    def assert_fast_checkout_returns_pending_with_redirect(
        buckaroo: Any,
        mock_strategy: Any,
        *,
        method: str,
        invoice: str,
        payload_overrides: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Queue a PayFastCheckout redirect response, run ``payFastCheckout()``."""
        response_body = Helpers.pending_redirect_response(method, "PayFastCheckout")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        overrides = {
            "description": "Fast checkout",
            **(payload_overrides or {}),
        }
        overrides.pop("invoice", None)
        payload = Helpers.standard_payload(invoice=invoice, **overrides)
        response = buckaroo.payments.create_payment(method, payload).payFastCheckout()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
        _assert_recorded_action(mock_strategy, "payFastCheckout")
        return response


def _assert_recorded_action(mock_strategy: Any, expected: str) -> None:
    """Assert the last outgoing request carried ``Action=expected``.

    Requires a ``RecordingMock`` (root ``mock_strategy`` fixture). Raises
    ``AttributeError`` if the mock doesn't record calls, so swapping the
    fixture to a plain ``MockBuckaroo`` surfaces immediately.
    """
    actual = json.loads(mock_strategy.calls[-1]["data"])["Services"]["ServiceList"][0]["Action"]
    assert actual == expected, f"wire-level Action mismatch: expected {expected!r}, got {actual!r}"
