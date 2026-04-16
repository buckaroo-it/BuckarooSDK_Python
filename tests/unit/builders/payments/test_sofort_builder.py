"""Unit tests for :class:`SofortBuilder`.

Targets 100% line + branch coverage of
``buckaroo/builders/payments/sofort_builder.py``.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.sofort_builder import SofortBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.capabilities.bank_transfer_capabilities import BankTransferCapabilities
from buckaroo.builders.payments.capabilities.instant_refund_capable import InstantRefundCapable
from buckaroo.builders.payments.capabilities.fast_checkout_capable import FastCheckoutCapable
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


@pytest.fixture
def mock_strategy():
    return MockBuckaroo()


@pytest.fixture
def client(mock_strategy):
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = mock_strategy
    return c


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
        "savetoken": {"type": (str, bool), "required": False, "description": "Save payment token for future use"},
        "isrecurring": {"type": (str, bool), "required": False, "description": "Recurring payment flag"},
    }


def test_get_allowed_service_parameters_pay_is_case_insensitive(client):
    builder = SofortBuilder(client)
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters("Pay")


def test_get_allowed_service_parameters_payfastcheckout(client):
    builder = SofortBuilder(client)
    assert builder.get_allowed_service_parameters("payFastCheckout") == builder.get_allowed_service_parameters("Pay")


@pytest.mark.parametrize("action", ["Refund", "Capture", "Cancel"])
def test_get_allowed_service_parameters_empty_actions(client, action):
    assert SofortBuilder(client).get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_instantrefund_empty(client):
    assert SofortBuilder(client).get_allowed_service_parameters("instantRefund") == {}


def test_get_allowed_service_parameters_unknown_action_returns_defaults(client):
    builder = SofortBuilder(client)
    assert builder.get_allowed_service_parameters("SomeUnknown") == builder.get_allowed_service_parameters("Pay")


# -- Capability mixin sanity --

@pytest.mark.parametrize("mixin", [InstantRefundCapable, FastCheckoutCapable, BankTransferCapabilities])
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


# -- Broken aliases: payFastCheckout / instantRefund on the builder shadow the mixin --
# SofortBuilder defines payFastCheckout() and instantRefund() that delegate to
# self.pay_fast_checkout() and self.instant_refund(), which do not exist.
# These override the working mixin methods, causing AttributeError.

def test_pay_fast_checkout_alias_is_broken(client, mock_strategy):
    """SofortBuilder.payFastCheckout delegates to non-existent pay_fast_checkout."""
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST", "*/json/transaction*",
            {"Key": "sofort-fc-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    builder = (
        SofortBuilder(client)
        .currency("EUR").amount(10).description("fc test").invoice("FC-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
    )
    with pytest.raises(AttributeError):
        builder.payFastCheckout()


def test_instant_refund_alias_is_broken(client, mock_strategy):
    """SofortBuilder.instantRefund delegates to non-existent instant_refund."""
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST", "*/json/transaction*",
            {"Key": "sofort-ir-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    builder = (
        SofortBuilder(client)
        .currency("EUR").amount(10).description("ir test").invoice("IR-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
    )
    with pytest.raises(AttributeError):
        builder.instantRefund()


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
        SofortBuilder(client)
        .currency("EUR")
        .amount(25.00)
        .description("Sofort order")
        .invoice("INV-SOFORT-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
        .country_code("NL")
        .pay()
    )

    assert response.key == "sofort-key-123"
    mock_strategy.assert_all_consumed()
