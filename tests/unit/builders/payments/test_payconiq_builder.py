"""Unit tests for :class:`PayconiqBuilder`.

Targets 100% line + branch coverage of
``buckaroo/builders/payments/payconiq_builder.py``.
"""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.payconiq_builder import PayconiqBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.capabilities.bank_transfer_capabilities import (
    BankTransferCapabilities,
)
from tests.support.mock_request import BuckarooMockRequest
from tests.support.builders import populate_required_fields
from tests.support.recording_mock import recorded_action, recorded_request


def test_construction_with_client_succeeds(client):
    builder = PayconiqBuilder(client)
    assert isinstance(builder, PayconiqBuilder)
    assert isinstance(builder, PaymentBuilder)
    assert isinstance(builder, BankTransferCapabilities)


def test_get_service_name_returns_payconiq(client):
    assert PayconiqBuilder(client).get_service_name() == "payconiq"


def test_get_allowed_service_parameters_pay_snapshot(client):
    params = PayconiqBuilder(client).get_allowed_service_parameters("Pay")
    assert params == {
        "mobilenumber": {
            "type": str,
            "required": False,
            "description": "Mobile number for Payconiq",
        },
        "savetoken": {
            "type": (str, bool),
            "required": False,
            "description": "Save payment token for future use",
        },
        "isrecurring": {
            "type": (str, bool),
            "required": False,
            "description": "Recurring payment flag",
        },
    }


def test_get_allowed_service_parameters_pay_is_case_insensitive(client):
    builder = PayconiqBuilder(client)
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters(
        "Pay"
    )


def test_get_allowed_service_parameters_payfastcheckout(client):
    builder = PayconiqBuilder(client)
    assert builder.get_allowed_service_parameters(
        "PayFastCheckout"
    ) == builder.get_allowed_service_parameters("Pay")


def test_get_allowed_service_parameters_instantrefund_returns_empty(client):
    assert PayconiqBuilder(client).get_allowed_service_parameters("InstantRefund") == {}


@pytest.mark.parametrize("action", ["Refund", "Capture", "Cancel"])
def test_get_allowed_service_parameters_other_actions_return_empty(client, action):
    assert PayconiqBuilder(client).get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_unknown_action_returns_default(client):
    builder = PayconiqBuilder(client)
    assert builder.get_allowed_service_parameters(
        "SomethingElse"
    ) == builder.get_allowed_service_parameters("Pay")


def test_capability_mixin_instant_refund(client):
    builder = PayconiqBuilder(client)
    assert hasattr(builder, "instantRefund") and callable(builder.instantRefund)


def test_capability_mixin_fast_checkout(client):
    builder = PayconiqBuilder(client)
    assert hasattr(builder, "payFastCheckout") and callable(builder.payFastCheckout)


def test_mobile_number_setter(client):
    builder = PayconiqBuilder(client).mobile_number("+31612345678")
    assert isinstance(builder, PayconiqBuilder)


def test_from_dict_with_mobile_number(client):
    builder = PayconiqBuilder(client).from_dict(
        {
            "currency": "EUR",
            "amount": 5.00,
            "mobile_number": "+31612345678",
        }
    )
    assert isinstance(builder, PayconiqBuilder)


def test_from_dict_without_mobile_number(client):
    builder = PayconiqBuilder(client).from_dict(
        {
            "currency": "EUR",
            "amount": 5.00,
        }
    )
    assert isinstance(builder, PayconiqBuilder)


def test_payconiq_payFastCheckout_works(client, mock_strategy):
    """PayconiqBuilder.payFastCheckout uses the inherited mixin method."""
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST", "*/json/transaction*", {"Key": "pcq-fc-1", "Status": {"Code": {"Code": 190}}}
        )
    )
    builder = populate_required_fields(PayconiqBuilder(client))
    response = builder.payFastCheckout(validate=False)
    assert response is not None


def test_payconiq_instantRefund_works(client, mock_strategy):
    """PayconiqBuilder.instantRefund uses the inherited mixin method."""
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST", "*/json/transaction*", {"Key": "pcq-ir-1", "Status": {"Code": {"Code": 190}}}
        )
    )
    builder = populate_required_fields(PayconiqBuilder(client))
    response = builder.instantRefund("ABC123", validate=False)
    assert response is not None


def test_payconiq_instantRefund_sends_original_transaction_key_and_amount_credit_on_wire(
    client, mock_strategy
):
    """InstantRefundCapable (inherited via BankTransferCapabilities) must put
    OriginalTransactionKey + AmountCredit on the wire for Payconiq, action instantRefund."""
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST", "*/json/transaction*", {"Key": "pcq-ir-2", "Status": {"Code": {"Code": 190}}}
        )
    )
    builder = populate_required_fields(PayconiqBuilder(client))

    builder.instantRefund("ABC123", validate=False)

    assert recorded_action(mock_strategy) == "instantRefund"
    request = recorded_request(mock_strategy)
    assert request["OriginalTransactionKey"] == "ABC123"
    assert request["AmountCredit"] == 10.0
    assert "AmountDebit" not in request


def test_payconiq_instantRefund_raises_without_original_transaction_key(client, mock_strategy):
    builder = populate_required_fields(PayconiqBuilder(client))

    with pytest.raises(ValueError, match="Original transaction key is required"):
        builder.instantRefund(validate=False)


def test_pay_end_to_end(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "payconiq-key-123", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        populate_required_fields(PayconiqBuilder(client), amount=25.00)
        .mobile_number("+31600000000")
        .pay()
    )

    assert response.key == "payconiq-key-123"
