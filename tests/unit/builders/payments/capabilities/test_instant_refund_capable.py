"""Tests for :class:`InstantRefundCapable`.

Exercises the capability mixin through a real :class:`BuckarooHttpClient`
wired to a recording :class:`MockBuckaroo`. Assertions read the request
shape off the recorded HTTP call (``json.loads(call["data"])``), never
builder internals.
"""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.capabilities.instant_refund_capable import (
    InstantRefundCapable,
)
from buckaroo.exceptions._parameter_validation_error import (
    RequiredParameterMissingError,
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
    builder = make_test_builder(
        client,
        service_name="ideal",
        allowed_params=allowed or {},
        capabilities=(InstantRefundCapable,),
    )
    populate_required_fields(builder)
    return builder


# ---------------------------------------------------------------------------
# instantRefund()


class TestInstantRefund:
    def test_posts_action_instantRefund(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.instantRefund(validate=False)

        assert recorded_action(mock) == "instantRefund"

    def test_posts_to_transaction_endpoint(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.instantRefund(validate=False)

        assert len(mock.calls) == 1
        call = mock.calls[0]
        assert call["method"] == "POST"
        assert call["url"] == "https://testcheckout.buckaroo.nl/json/transaction"

    def test_posts_expected_service_name(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.instantRefund(validate=False)

        service = recorded_request(mock)["Services"]["ServiceList"][0]
        assert service["Name"] == "ideal"

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

        response = builder.instantRefund(validate=False)

        assert isinstance(response, PaymentResponse)
        assert response.key == "refund-123"

    def test_forwards_validate_flag_true_triggers_validation(self):
        """``validate=True`` runs the real service-parameter validator against
        ``get_allowed_service_parameters("instantRefund")`` — so declaring a
        required parameter and omitting it must raise
        :class:`RequiredParameterMissingError`. Pins that the flag actually
        routes through ``build()``'s validation, not just a quirk crash."""
        _mock, client = wire_recording_http()
        builder = _ready_builder(
            client,
            allowed={
                "instantRefund": {
                    "refund_reason": {"type": str, "required": True},
                }
            },
        )

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.instantRefund(validate=True)

        assert exc.value.parameter_name == "refund_reason"
