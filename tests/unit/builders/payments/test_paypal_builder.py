"""Unit tests for :class:`PaypalBuilder`.

Targets 100% line + branch coverage of
``buckaroo/builders/payments/paypal_builder.py``. The builder carries no
capability mixins and defines no action methods of its own, so the surface
under test is:

- construction via ``BuckarooClient`` wired to :class:`MockBuckaroo`
- ``get_service_name()``
- ``get_allowed_service_parameters(action)`` for both branches
- ``pay()`` end-to-end through the mock strategy
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.paypal_builder import PaypalBuilder
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
    builder = PaypalBuilder(client)
    assert isinstance(builder, PaypalBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_paypal(client):
    assert PaypalBuilder(client).get_service_name() == "paypal"


def test_get_allowed_service_parameters_pay_snapshot(client):
    builder = PaypalBuilder(client)

    assert builder.get_allowed_service_parameters("Pay") == {
        "buyerEmail": {
            "type": str,
            "required": False,
            "description": "Buyer's email address.",
        },
        "productName": {
            "type": str,
            "required": False,
            "description": "Name of the product.",
        },
        "billingAgreementDescription": {
            "type": str,
            "required": False,
            "description": "Description of the billing agreement.",
        },
        "pageStyle": {
            "type": str,
            "required": False,
            "description": "Style of the payment page.",
        },
        "startrecurrent": {
            "type": str,
            "required": False,
            "description": "Start of recurrent payment.",
        },
        "payPalOrderId": {
            "type": str,
            "required": False,
            "description": "PayPal order ID.",
        },
    }


def test_get_allowed_service_parameters_pay_is_case_insensitive(client):
    builder = PaypalBuilder(client)

    assert builder.get_allowed_service_parameters("pay") == (
        builder.get_allowed_service_parameters("Pay")
    )


@pytest.mark.parametrize(
    "action", ["Refund", "Capture", "Authorize", "UnknownAction"]
)
def test_get_allowed_service_parameters_non_pay_returns_empty(client, action):
    assert PaypalBuilder(client).get_allowed_service_parameters(action) == {}


def test_pay_posts_transaction_and_parses_response(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "paypal-key-123", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        PaypalBuilder(client)
        .currency("EUR")
        .amount(42.50)
        .description("Paypal order")
        .invoice("INV-PP-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
        .add_parameter("buyerEmail", "buyer@example.test")
        .pay()
    )

    assert response.key == "paypal-key-123"
    mock_strategy.assert_all_consumed()
