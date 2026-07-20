"""Unit coverage for :class:`PosBuilder`.

Point of Sale (POS) transactions are PIN-based in-store payments routed to a
physical terminal via ``TerminalID``. POS carries no redirect flow (no
``return_url`` family) and every request must be sent with a fixed
``Channel: "Web"`` regardless of anything the caller does — these tests pin
both invariants plus the ``TerminalID`` required-parameter contract.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.pos_builder import PosBuilder
from buckaroo.exceptions._parameter_validation_error import RequiredParameterMissingError
from buckaroo.factories.payment_method_factory import PaymentMethodFactory
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_request, wire_recording_http


@pytest.fixture
def builder(client: BuckarooClient) -> PosBuilder:
    return PosBuilder(client)


def _pos_ready(builder: PosBuilder, **overrides) -> PosBuilder:
    """Populate the fields POS actually requires — no return_url family."""
    fields = {
        "currency": "EUR",
        "amount": 0.01,
        "invoice": "TestFactuur01",
        "terminal_id": "50000001",
    }
    fields.update(overrides)
    return (
        builder.currency(fields["currency"])
        .amount(fields["amount"])
        .invoice(fields["invoice"])
        .terminal_id(fields["terminal_id"])
    )


# ---------------------------------------------------------------------------
# Construction


def test_construction_wires_client(builder: PosBuilder, client: BuckarooClient) -> None:
    assert isinstance(builder, PosBuilder)
    assert isinstance(builder, PaymentBuilder)
    assert builder._client is client


def test_create_builder_returns_pos_builder(client: BuckarooClient) -> None:
    builder = PaymentMethodFactory.create_builder("pospayment", client)
    assert isinstance(builder, PosBuilder)


def test_create_builder_is_case_insensitive(client: BuckarooClient) -> None:
    builder = PaymentMethodFactory.create_builder("POSPAYMENT", client)
    assert isinstance(builder, PosBuilder)


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_pospayment(builder: PosBuilder) -> None:
    assert builder.get_service_name() == "pospayment"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — TerminalID required on Pay only


def test_get_allowed_service_parameters_pay_requires_terminal_id(builder: PosBuilder) -> None:
    assert builder.get_allowed_service_parameters("Pay") == {
        "TerminalID": {
            "type": str,
            "required": True,
            "description": "Unique identifier of the physical POS terminal",
        },
    }


def test_get_allowed_service_parameters_pay_is_case_insensitive(builder: PosBuilder) -> None:
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters(
        "Pay"
    )


@pytest.mark.parametrize("action", ["Refund", "Capture", "Authorize", "UnknownAction"])
def test_get_allowed_service_parameters_non_pay_returns_empty(
    builder: PosBuilder, action: str
) -> None:
    assert builder.get_allowed_service_parameters(action) == {}


# ---------------------------------------------------------------------------
# required_fields — no return_url family, POS is in-store only


def test_required_fields_has_no_return_url_family(builder: PosBuilder) -> None:
    builder.currency("EUR").amount(0.01).invoice("TestFactuur01")
    assert builder.required_fields("Pay") == {
        "currency": "EUR",
        "amount_debit": 0.01,
        "invoice": "TestFactuur01",
    }


def test_pay_without_currency_amount_or_invoice_raises(builder: PosBuilder) -> None:
    with pytest.raises(ValueError, match="Missing required fields"):
        builder.terminal_id("50000001").pay()


# ---------------------------------------------------------------------------
# terminal_id() — valid and invalid input


def test_terminal_id_appends_exact_case_parameter(builder: PosBuilder) -> None:
    _pos_ready(builder)
    request = builder.build("Pay", validate=False)
    params = request.to_dict()["Services"]["ServiceList"][0]["Parameters"]
    assert params == [{"Name": "TerminalID", "GroupType": "", "GroupID": "", "Value": "50000001"}]


@pytest.mark.parametrize("invalid_terminal_id", ["", "   ", None])
def test_terminal_id_rejects_blank_values(builder: PosBuilder, invalid_terminal_id) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        builder.terminal_id(invalid_terminal_id)


def test_missing_terminal_id_raises_required_parameter_missing(builder: PosBuilder) -> None:
    builder.currency("EUR").amount(0.01).invoice("TestFactuur01")
    with pytest.raises(RequiredParameterMissingError):
        builder.pay()


# ---------------------------------------------------------------------------
# Channel is always forced to "Web"


def test_build_forces_channel_to_web(builder: PosBuilder) -> None:
    _pos_ready(builder)
    request = builder.build("Pay", validate=False)
    assert request.to_dict()["Channel"] == "Web"


def test_build_overrides_any_previously_set_channel(builder: PosBuilder) -> None:
    _pos_ready(builder).channel("Backoffice")
    request = builder.build("Pay", validate=False)
    assert request.to_dict()["Channel"] == "Web"


def test_pay_sends_channel_web_on_the_wire() -> None:
    mock, client = wire_recording_http()
    mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))

    _pos_ready(PosBuilder(client)).pay(validate=False)

    assert recorded_request(mock)["Channel"] == "Web"


def test_other_payment_builders_do_not_send_channel(client: BuckarooClient) -> None:
    """Channel is POS-specific; unrelated builders must not pick it up."""
    from buckaroo.builders.payments.swish_builder import SwishBuilder

    builder = (
        SwishBuilder(client)
        .currency("EUR")
        .amount(10.0)
        .description("desc")
        .invoice("INV-1")
        .return_url("https://x/ok")
        .return_url_cancel("https://x/cancel")
        .return_url_error("https://x/error")
        .return_url_reject("https://x/reject")
    )
    request = builder.build("Pay", validate=False)
    assert "Channel" not in request.to_dict()


# ---------------------------------------------------------------------------
# End-to-end pay via MockBuckaroo


def test_pay_posts_transaction_and_parses_response(
    builder: PosBuilder, mock_strategy: MockBuckaroo
) -> None:
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {
                "Key": "A5417E98043647D095B857E16C00000",
                "Status": {"Code": {"Code": 190, "Description": "Success"}},
                "ServiceCode": "pospayment",
                "Invoice": "TestFactuur01",
                "Currency": "EUR",
                "AmountDebit": 0.01,
                "TransactionType": "V735",
            },
        )
    )

    response = _pos_ready(builder).pay()

    assert response.key == "A5417E98043647D095B857E16C00000"
    assert response.status.code.code == 190
    assert response.service_code == "pospayment"


def test_pay_posts_service_name_and_action(client: BuckarooClient) -> None:
    mock, wired_client = wire_recording_http()
    mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))

    _pos_ready(PosBuilder(wired_client)).pay(validate=False)

    service = recorded_request(mock)["Services"]["ServiceList"][0]
    assert service["Name"] == "pospayment"
    assert service["Action"] == "Pay"


# ---------------------------------------------------------------------------
# Capability-only methods — POS mixes in nothing


def test_does_not_expose_capability_only_methods(builder: PosBuilder) -> None:
    for method in (
        "authorize",
        "authorizeEncrypted",
        "cancelAuthorize",
        "payEncrypted",
        "instantRefund",
        "payFastCheckout",
    ):
        assert not hasattr(builder, method), (
            f"PosBuilder unexpectedly exposes capability method {method!r}"
        )
