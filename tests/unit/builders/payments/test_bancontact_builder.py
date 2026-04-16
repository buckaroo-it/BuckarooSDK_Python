"""Unit tests for :class:`BancontactBuilder`.

Targets 100% line + branch coverage of
``buckaroo/builders/payments/bancontact_builder.py``.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.bancontact_builder import BancontactBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
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


def test_construction_with_client_succeeds(client):
    builder = BancontactBuilder(client)
    assert isinstance(builder, BancontactBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_bancontactmrcash(client):
    assert BancontactBuilder(client).get_service_name() == "bancontactmrcash"


def test_get_allowed_service_parameters_pay(client):
    params = BancontactBuilder(client).get_allowed_service_parameters("Pay")
    assert "savetoken" in params
    assert params["savetoken"]["required"] is False


def test_get_allowed_service_parameters_authenticate(client):
    params = BancontactBuilder(client).get_allowed_service_parameters("Authenticate")
    assert params == BancontactBuilder(client).get_allowed_service_parameters("Pay")


def test_get_allowed_service_parameters_pay_is_case_insensitive(client):
    builder = BancontactBuilder(client)
    assert builder.get_allowed_service_parameters("pay") == (
        builder.get_allowed_service_parameters("Pay")
    )


def test_get_allowed_service_parameters_payEncrypted_snapshot(client):
    assert BancontactBuilder(client).get_allowed_service_parameters("payEncrypted") == {
        "encryptedCardData": {"type": str, "required": True, "description": "Encrypted card data for payment"},
    }


def test_get_allowed_service_parameters_completePayment_snapshot(client):
    assert BancontactBuilder(client).get_allowed_service_parameters("completePayment") == {
        "encryptedCardData": {"type": str, "required": True, "description": "Encrypted card data for payment"},
    }


@pytest.mark.parametrize("action", ["Refund", "Capture", "Cancel"])
def test_get_allowed_service_parameters_refund_capture_cancel(client, action):
    assert BancontactBuilder(client).get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_unknown_action(client):
    assert BancontactBuilder(client).get_allowed_service_parameters("SomethingElse") == {}


def test_pay_posts_transaction_and_parses_response(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "bancontact-key-456", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        BancontactBuilder(client)
        .currency("EUR")
        .amount(25.00)
        .description("Bancontact order")
        .invoice("INV-BC-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
        .pay()
    )

    assert response.key == "bancontact-key-456"
    mock_strategy.assert_all_consumed()
