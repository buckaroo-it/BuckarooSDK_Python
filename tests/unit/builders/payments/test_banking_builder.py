"""Unit coverage for :class:`BankingBuilder`.

Banking is a payout (PaymentOrder action): Buckaroo sends money OUT to a
bank account given an IBAN and account holder name. Unlike the base Pay
flow it has no redirect, so it overrides ``required_fields`` to drop the
``return_url*`` requirements, and it swaps ``AmountDebit`` for
``AmountCredit`` on the wire (same precedent as ``refund()`` and
``cancelAuthorize()``).
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.banking_builder import BankingBuilder
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_request, wire_recording_http


@pytest.fixture
def builder(client: BuckarooClient) -> BankingBuilder:
    return BankingBuilder(client)


# ---------------------------------------------------------------------------
# Construction


def test_instantiates_as_payment_builder(builder: BankingBuilder) -> None:
    assert isinstance(builder, BankingBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_construction_binds_client(builder: BankingBuilder, client: BuckarooClient) -> None:
    assert builder._client is client


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_banking(builder: BankingBuilder) -> None:
    assert builder.get_service_name() == "Banking"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — PaymentOrder action snapshot


def test_get_allowed_service_parameters_paymentorder_snapshot(
    builder: BankingBuilder,
) -> None:
    assert builder.get_allowed_service_parameters("PaymentOrder") == {
        "accountholdername": {
            "type": str,
            "required": True,
            "description": "Account holder name",
        },
        "iban": {
            "type": str,
            "required": True,
            "description": "IBAN",
        },
    }


def test_get_allowed_service_parameters_paymentorder_case_insensitive(
    builder: BankingBuilder,
) -> None:
    assert builder.get_allowed_service_parameters(
        "paymentorder"
    ) == builder.get_allowed_service_parameters("PaymentOrder")


@pytest.mark.parametrize("action", ["Pay", "Refund", "Authorize", "Capture", "Unknown"])
def test_get_allowed_service_parameters_non_paymentorder_actions_return_empty(
    builder: BankingBuilder, action: str
) -> None:
    assert builder.get_allowed_service_parameters(action) == {}


# ---------------------------------------------------------------------------
# required_fields — no return URLs required


def test_required_fields_currency_amount_and_invoice(builder: BankingBuilder) -> None:
    assert builder.required_fields("PaymentOrder") == {
        "currency": None,
        "amount_debit": None,
        "invoice": None,
    }


def test_build_succeeds_without_return_urls(builder: BankingBuilder) -> None:
    builder.currency("EUR").amount(150.0).invoice("Banking_Test_1")
    # Should not raise even though no return_url* fields were set.
    payment_request = builder.build("PaymentOrder", validate=False)
    assert payment_request.currency == "EUR"


# ---------------------------------------------------------------------------
# End-to-end payment_order via MockBuckaroo


def test_payment_order_posts_banking_service_with_amount_credit():
    mock, stub_client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "BNK-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    builder = BankingBuilder(stub_client)
    builder.currency("EUR").amount(150.0).invoice("Banking_Test_1").description("Test")
    builder.add_parameter("AccountHolderName", "Arensman")
    builder.add_parameter("IBAN", "NL44RABO0123456789")

    response = builder.payment_order(validate=False)

    assert "/json/transaction" in mock.calls[0]["url"].lower()
    sent = recorded_request(mock)
    service = sent["Services"]["ServiceList"][0]
    assert service["Name"] == "Banking"
    assert service["Action"] == "PaymentOrder"
    assert sent["AmountCredit"] == 150.0
    assert "AmountDebit" not in sent
    assert response.key == "BNK-1"
    mock.assert_all_consumed()
