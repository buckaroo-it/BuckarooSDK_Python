"""Tests for :class:`EncryptedPayCapable`.

Exercises the capability mixin through a real :class:`BuckarooHttpClient`
wired to a recording :class:`MockBuckaroo`. Assertions read the request
shape off the recorded HTTP call (``json.loads(call["data"])``), never
builder internals.

The mixin currently exposes one method: :meth:`payEncrypted`.
``payWithSecurityCode`` and ``payWithToken`` live on
:class:`CreditcardBuilder`.
"""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.capabilities.encrypted_pay_capable import (
    EncryptedPayCapable,
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
        service_name="creditcard",
        allowed_params=allowed or {},
        capabilities=(EncryptedPayCapable,),
    )
    populate_required_fields(builder)
    return builder


# ---------------------------------------------------------------------------
# payEncrypted()


class TestPayEncrypted:
    def test_posts_action_PayEncrypted(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.payEncrypted(validate=False)

        assert recorded_action(mock) == "PayEncrypted"

    def test_posts_to_transaction_endpoint(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.payEncrypted(validate=False)

        assert len(mock.calls) == 1
        call = mock.calls[0]
        assert call["method"] == "POST"
        assert call["url"] == "https://testcheckout.buckaroo.nl/json/transaction"

    def test_returns_PaymentResponse_parsed_from_http_body(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                {"Key": "txn-abc-123", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = _ready_builder(client)

        response = builder.payEncrypted(validate=False)

        assert isinstance(response, PaymentResponse)
        assert response.key == "txn-abc-123"

    def test_posts_service_named_from_builder(self):
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)

        builder.payEncrypted(validate=False)

        service = recorded_request(mock)["Services"]["ServiceList"][0]
        assert service["Name"] == "creditcard"
        assert service["Action"] == "PayEncrypted"

    def test_forwards_validate_flag_to_build(self):
        """The ``validate`` kwarg flows through to ``build()``.

        Invalid parameters survive when ``validate=False`` because the
        builder skips filtering. A validator run would have dropped them.
        """
        mock, client = wire_recording_http()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
        builder = _ready_builder(client)
        builder.add_parameter("not_allowed", "value")

        builder.payEncrypted(validate=False)

        params = recorded_request(mock)["Services"]["ServiceList"][0].get("Parameters") or []
        names = {p["Name"] for p in params}
        assert "Not_allowed" in names

    def test_forwards_validate_flag_true_triggers_validation(self):
        """``validate=True`` runs the real service-parameter validator against
        ``get_allowed_service_parameters("PayEncrypted")`` — so declaring a
        required parameter and omitting it must raise
        :class:`RequiredParameterMissingError`. Pins that the flag actually
        routes through ``build()``'s validation, not just a quirk crash."""
        _mock, client = wire_recording_http()
        builder = _ready_builder(
            client,
            allowed={
                "PayEncrypted": {
                    "encryptedPaymentData": {"type": str, "required": True},
                }
            },
        )

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.payEncrypted(validate=True)

        assert exc.value.parameter_name == "encryptedPaymentData"
