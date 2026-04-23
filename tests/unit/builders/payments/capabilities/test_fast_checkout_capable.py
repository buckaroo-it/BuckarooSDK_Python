"""Tests for :class:`FastCheckoutCapable`.

Exercises the capability mixin through a real :class:`BuckarooHttpClient`
wired to a recording :class:`MockBuckaroo`. Assertions read the request
shape off the recorded HTTP call (``json.loads(call["data"])``), never
builder internals.
"""

from __future__ import annotations

from buckaroo.builders.payments.capabilities.fast_checkout_capable import (
    FastCheckoutCapable,
)
from buckaroo.models.payment_response import PaymentResponse
from tests.support.builders import make_test_builder, populate_required_fields
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import (
    recorded_action,
    recorded_request,
    wire_recording_http,
)


# ---------------------------------------------------------------------------
# Helpers


def _ready_builder(client, allowed=None):
    """Build a fully-populated test builder so ``build()`` passes required checks."""
    # Default: action known to validator with no allowed params (empty dict).
    # Keys must be dicts; validator iterates via ``.items()``.
    builder = make_test_builder(
        client,
        service_name="ideal",
        allowed_params=allowed if allowed is not None else {"payFastCheckout": {}},
        capabilities=(FastCheckoutCapable,),
    )
    populate_required_fields(builder)
    return builder


# ---------------------------------------------------------------------------
# payFastCheckout()


class TestPayFastCheckout:
    def test_posts_action_payFastCheckout(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.payFastCheckout()

        assert recorded_action(mock) == "payFastCheckout"

    def test_posts_to_transaction_endpoint(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.payFastCheckout()

        assert len(mock.calls) == 1
        call = mock.calls[0]
        assert call["method"] == "POST"
        assert call["url"] == "https://testcheckout.buckaroo.nl/json/transaction"

    def test_posts_expected_service_name(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.payFastCheckout()

        service = recorded_request(mock)["Services"]["ServiceList"][0]
        assert service["Name"] == "ideal"

    def test_returns_PaymentResponse_parsed_from_http_body(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                {"Key": "fastcheckout-xyz", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = _ready_builder(client)

        response = builder.payFastCheckout()

        assert isinstance(response, PaymentResponse)
        assert response.key == "fastcheckout-xyz"

    def test_validate_false_skips_parameter_validation(self):
        """With ``validate=False``, unknown parameters pass through to the request."""
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client, allowed={"payFastCheckout": {}})
        builder.add_parameter("someUnknownParam", "value")

        builder.payFastCheckout(validate=False)

        service = recorded_request(mock)["Services"]["ServiceList"][0]
        parameter_names = [p["Name"] for p in (service.get("Parameters") or [])]
        assert "Someunknownparam" in parameter_names
