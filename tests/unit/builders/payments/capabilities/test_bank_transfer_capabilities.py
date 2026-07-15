"""Tests for :class:`BankTransferCapabilities`.

``BankTransferCapabilities`` composes :class:`InstantRefundCapable` and
:class:`FastCheckoutCapable` — no new methods of its own. These tests
exercise the composition through a real :class:`BuckarooHttpClient`
wired to a recording :class:`MockBuckaroo`. Assertions read the request
shape off the recorded HTTP call (``json.loads(call["data"])``), never
builder internals.
"""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.capabilities.bank_transfer_capabilities import (
    BankTransferCapabilities,
)
from buckaroo.builders.payments.capabilities.fast_checkout_capable import (
    FastCheckoutCapable,
)
from buckaroo.builders.payments.capabilities.instant_refund_capable import (
    InstantRefundCapable,
)
from buckaroo.models.payment_response import PaymentResponse
from tests.support.builders import make_test_builder, populate_required_fields
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action, recorded_request, wire_recording_http


# ---------------------------------------------------------------------------
# Helpers


def _ready_builder(client, allowed=None):
    """Build a fully-populated test builder mixing in BankTransferCapabilities."""
    builder = make_test_builder(
        client,
        service_name="sofort",
        allowed_params=allowed or {},
        capabilities=(BankTransferCapabilities,),
    )
    populate_required_fields(builder)
    return builder


# ---------------------------------------------------------------------------
# Composition


class TestComposition:
    def test_mixes_in_instant_refund_capable(self):
        _mock, client = wire_recording_http()
        builder = _ready_builder(client)

        assert isinstance(builder, InstantRefundCapable)

    def test_mixes_in_fast_checkout_capable(self):
        _mock, client = wire_recording_http()
        builder = _ready_builder(client)

        assert isinstance(builder, FastCheckoutCapable)


# ---------------------------------------------------------------------------
# instantRefund()


class TestInstantRefund:
    def test_posts_action_instantRefund(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.instantRefund("ABC123", validate=False)

        assert recorded_action(mock) == "instantRefund"

    def test_posts_to_transaction_endpoint(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.instantRefund("ABC123", validate=False)

        assert len(mock.calls) == 1
        call = mock.calls[0]
        assert call["method"] == "POST"
        assert call["url"] == "https://testcheckout.buckaroo.nl/json/transaction"

    def test_returns_payment_response(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                {"Key": "refund-123", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = _ready_builder(client)

        response = builder.instantRefund("ABC123", validate=False)

        assert isinstance(response, PaymentResponse)
        assert response.key == "refund-123"

    def test_sends_original_transaction_key_and_amount_credit_on_the_wire(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.instantRefund("ABC123", validate=False)

        request = recorded_request(mock)
        assert request["OriginalTransactionKey"] == "ABC123"
        assert request["AmountCredit"] == 10.0
        assert "AmountDebit" not in request

    def test_raises_value_error_without_original_transaction_key(self):
        _mock, client = wire_recording_http()
        builder = _ready_builder(client)

        with pytest.raises(ValueError, match="Original transaction key is required"):
            builder.instantRefund(validate=False)


# ---------------------------------------------------------------------------
# payFastCheckout()


class TestPayFastCheckout:
    def test_posts_action_payFastCheckout(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.payFastCheckout(validate=False)

        assert recorded_action(mock) == "payFastCheckout"

    def test_posts_to_transaction_endpoint(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.payFastCheckout(validate=False)

        assert len(mock.calls) == 1
        call = mock.calls[0]
        assert call["method"] == "POST"
        assert call["url"] == "https://testcheckout.buckaroo.nl/json/transaction"

    def test_returns_payment_response(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                {"Key": "checkout-789", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = _ready_builder(client)

        response = builder.payFastCheckout(validate=False)

        assert isinstance(response, PaymentResponse)
        assert response.key == "checkout-789"
