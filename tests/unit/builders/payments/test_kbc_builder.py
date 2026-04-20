"""Unit coverage for :class:`KBCBuilder`.

Phase 7.19 — per-builder coverage. KBCBuilder is a minimal subclass of
:class:`PaymentBuilder` that only overrides :meth:`get_service_name` and
:meth:`get_allowed_service_parameters`; it mixes in no capability classes and
does not declare a ``_serviceName`` class attribute.
"""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.kbc_builder import KBCBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_request, wire_recording_http


# ---------------------------------------------------------------------------
# Construction


def test_construction_wired_to_mock_buckaroo_succeeds(client):
    builder = KBCBuilder(client)

    assert isinstance(builder, KBCBuilder)
    assert isinstance(builder, PaymentBuilder)
    assert builder._client is client


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_kbc_payment_button(client):
    builder = KBCBuilder(client)

    assert builder.get_service_name() == "KBCPaymentButton"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — snapshot every action


@pytest.mark.parametrize(
    "action",
    ["Pay", "Refund", "PayRemainder", "ExtraInfo", "UnknownAction"],
)
def test_get_allowed_service_parameters_returns_empty_dict_for_every_action(
    client, action
):
    builder = KBCBuilder(client)

    assert builder.get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_defaults_to_pay_and_returns_empty(client):
    """Covers the ``action: str = "Pay"`` default-argument branch."""
    builder = KBCBuilder(client)

    assert builder.get_allowed_service_parameters() == {}


# ---------------------------------------------------------------------------
# End-to-end pay via MockBuckaroo


def test_pay_posts_kbc_payment_button_service_to_transaction_endpoint():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "KBC-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    builder = populate_required_fields(KBCBuilder(client), amount=42.00)

    response = builder.pay(validate=False)

    assert "/json/transaction" in mock.calls[0]["url"].lower()
    sent = recorded_request(mock)
    service = sent["Services"]["ServiceList"][0]
    assert service["Name"] == "KBCPaymentButton"
    assert service["Action"] == "Pay"
    assert response.key == "KBC-1"
    mock.assert_all_consumed()
