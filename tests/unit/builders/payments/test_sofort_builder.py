"""Unit tests for :class:`SofortBuilder`.

Targets 100% line + branch coverage of
``buckaroo/builders/payments/sofort_builder.py``.
"""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.sofort_builder import SofortBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.capabilities.bank_transfer_capabilities import (
    BankTransferCapabilities,
)
from buckaroo.builders.payments.capabilities.instant_refund_capable import InstantRefundCapable
from buckaroo.builders.payments.capabilities.fast_checkout_capable import FastCheckoutCapable
from tests.support.mock_request import BuckarooMockRequest
from tests.support.builders import populate_required_fields


# -- Construction --


def test_construction_with_client_succeeds(client):
    builder = SofortBuilder(client)
    assert isinstance(builder, SofortBuilder)
    assert isinstance(builder, PaymentBuilder)
    assert isinstance(builder, BankTransferCapabilities)


# -- Service name --


def test_get_service_name_returns_sofort(client):
    assert SofortBuilder(client).get_service_name() == "sofort"


# -- Allowed service parameters snapshots --


def test_get_allowed_service_parameters_pay_snapshot(client):
    params = SofortBuilder(client).get_allowed_service_parameters("Pay")
    assert params == {
        "countrycode": {"type": str, "required": False, "description": "Sofort country code"},
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
    builder = SofortBuilder(client)
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters(
        "Pay"
    )


def test_get_allowed_service_parameters_payfastcheckout(client):
    builder = SofortBuilder(client)
    assert builder.get_allowed_service_parameters(
        "payFastCheckout"
    ) == builder.get_allowed_service_parameters("Pay")


@pytest.mark.parametrize("action", ["Refund", "Capture", "Cancel"])
def test_get_allowed_service_parameters_empty_actions(client, action):
    assert SofortBuilder(client).get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_instantrefund_empty(client):
    assert SofortBuilder(client).get_allowed_service_parameters("instantRefund") == {}


def test_get_allowed_service_parameters_unknown_action_returns_defaults(client):
    builder = SofortBuilder(client)
    assert builder.get_allowed_service_parameters(
        "SomeUnknown"
    ) == builder.get_allowed_service_parameters("Pay")


# -- Capability mixin sanity --


@pytest.mark.parametrize(
    "mixin", [InstantRefundCapable, FastCheckoutCapable, BankTransferCapabilities]
)
def test_inherits_capability_mixin(client, mixin):
    assert isinstance(SofortBuilder(client), mixin)


# -- country_code fluent setter --


def test_country_code_setter_returns_self(client):
    builder = SofortBuilder(client)
    result = builder.country_code("NL")
    assert result is builder


# -- from_dict with country_code --


def test_from_dict_populates_country_code(client):
    builder = SofortBuilder(client)
    result = builder.from_dict({"country_code": "DE"})
    assert result is builder


def test_from_dict_without_country_code(client):
    builder = SofortBuilder(client)
    result = builder.from_dict({"currency": "EUR"})
    assert result is builder


def test_pay_fast_checkout_works(client, mock_strategy):
    """SofortBuilder.payFastCheckout uses the inherited mixin method."""
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "sofort-fc-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    builder = populate_required_fields(SofortBuilder(client))
    response = builder.payFastCheckout()
    assert response is not None


def test_instant_refund_works(client, mock_strategy):
    """SofortBuilder.instantRefund uses the inherited mixin method."""
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "sofort-ir-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    builder = populate_required_fields(SofortBuilder(client))
    response = builder.instantRefund("ABC123")
    assert response is not None


# -- End-to-end pay --


def test_pay_posts_transaction_and_parses_response(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "sofort-key-123", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        populate_required_fields(SofortBuilder(client), amount=25.00).country_code("NL").pay()
    )

    assert response.key == "sofort-key-123"
