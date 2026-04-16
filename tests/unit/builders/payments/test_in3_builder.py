"""Unit tests for :class:`In3Builder`.

Targets 100% line + branch coverage of
``buckaroo/builders/payments/in3_builder.py``.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.in3_builder import In3Builder
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
    builder = In3Builder(client)
    assert isinstance(builder, In3Builder)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_in3(client):
    assert In3Builder(client).get_service_name() == "in3"


def test_get_allowed_service_parameters_pay_snapshot(client):
    builder = In3Builder(client)

    assert builder.get_allowed_service_parameters("Pay") == {
        "billingCustomer": {
            "type": list,
            "required": True,
            "description": "Billing customer information",
        },
        "shippingCustomer": {
            "type": list,
            "required": True,
            "description": "Shipping customer information",
        },
        "article": {
            "type": list,
            "required": True,
            "description": "IN3 articles",
        },
    }


def test_get_allowed_service_parameters_pay_is_case_insensitive(client):
    builder = In3Builder(client)

    assert builder.get_allowed_service_parameters("pay") == (
        builder.get_allowed_service_parameters("Pay")
    )


@pytest.mark.parametrize("action", ["Refund", "Capture", "Authorize", "UnknownAction"])
def test_get_allowed_service_parameters_non_pay_returns_empty(client, action):
    assert In3Builder(client).get_allowed_service_parameters(action) == {}


def test_pay_posts_transaction_and_parses_response(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "in3-key-456", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        In3Builder(client)
        .currency("EUR")
        .amount(99.95)
        .description("IN3 order")
        .invoice("INV-IN3-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
        .add_parameter("billingCustomer", [{"Name": "John"}])
        .add_parameter("shippingCustomer", [{"Name": "John"}])
        .add_parameter("article", [{"Description": "Widget", "Quantity": 1}])
        .pay()
    )

    assert response.key == "in3-key-456"
    mock_strategy.assert_all_consumed()
