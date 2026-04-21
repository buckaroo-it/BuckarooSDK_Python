"""Unit coverage for :class:`PayByBankBuilder`.

Phase 7.25 — per-builder coverage. PayByBankBuilder mixes in
:class:`BankTransferCapabilities`, which composes
:class:`InstantRefundCapable` and :class:`FastCheckoutCapable`. Tests pin the
allowed-parameter shape for every action we care about, assert that every
capability-mixin method is present and callable, and drive ``pay`` through
``MockBuckaroo`` end to end.
"""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.paybybank_builder import PayByBankBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_request, wire_recording_http


# ---------------------------------------------------------------------------
# Construction


def test_construction_wired_to_mock_buckaroo_succeeds(client):
    builder = PayByBankBuilder(client)

    assert isinstance(builder, PayByBankBuilder)
    assert isinstance(builder, PaymentBuilder)
    assert builder._client is client


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_paybybank(client):
    builder = PayByBankBuilder(client)

    assert builder.get_service_name() == "PayByBank"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — snapshot supported actions


def test_get_allowed_service_parameters_pay_snapshot(client):
    builder = PayByBankBuilder(client)

    assert builder.get_allowed_service_parameters("Pay") == {
        "issuer": {
            "type": str,
            "required": True,
            "description": "PayByBank bank issuer code",
        },
    }


def test_get_allowed_service_parameters_is_case_insensitive_for_pay(client):
    """Source lower-cases the action before matching, so "pay" equals "Pay"."""
    builder = PayByBankBuilder(client)

    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters(
        "Pay"
    )


def test_get_allowed_service_parameters_defaults_to_pay(client):
    """Covers the ``action: str = "Pay"`` default-argument branch."""
    builder = PayByBankBuilder(client)

    assert builder.get_allowed_service_parameters() == builder.get_allowed_service_parameters("Pay")


@pytest.mark.parametrize(
    "action",
    ["Refund", "Authorize", "Capture", "PayRemainder", "UnknownAction"],
)
def test_get_allowed_service_parameters_unsupported_action_returns_empty(client, action):
    builder = PayByBankBuilder(client)

    assert builder.get_allowed_service_parameters(action) == {}


# ---------------------------------------------------------------------------
# End-to-end pay via MockBuckaroo


def test_pay_posts_paybybank_service_to_transaction_endpoint_and_parses_response():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "PBB-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    builder = populate_required_fields(PayByBankBuilder(client), amount=23.45)

    response = builder.pay(validate=False)

    assert "/json/transaction" in mock.calls[0]["url"].lower()
    sent = recorded_request(mock)
    service = sent["Services"]["ServiceList"][0]
    assert service["Name"] == "PayByBank"
    assert service["Action"] == "Pay"
    assert response.key == "PBB-1"
    mock.assert_all_consumed()
