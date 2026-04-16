"""Unit tests for :class:`AlipayBuilder`.

Targets 100% line + branch coverage of
``buckaroo/builders/payments/alipay_builder.py``. The builder carries no
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
from buckaroo.builders.payments.alipay_builder import AlipayBuilder
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
    builder = AlipayBuilder(client)
    assert isinstance(builder, AlipayBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_alipay(client):
    assert AlipayBuilder(client).get_service_name() == "Alipay"


def test_get_allowed_service_parameters_pay_snapshot(client):
    builder = AlipayBuilder(client)

    assert builder.get_allowed_service_parameters("Pay") == {
        "UseMobileView": {
            "type": (str, bool),
            "required": True,
            "description": "Use mobile view for Alipay",
        },
    }


def test_get_allowed_service_parameters_pay_is_case_insensitive(client):
    builder = AlipayBuilder(client)

    assert builder.get_allowed_service_parameters("pay") == (
        builder.get_allowed_service_parameters("Pay")
    )


@pytest.mark.parametrize("action", ["Refund", "Capture", "Authorize", "UnknownAction"])
def test_get_allowed_service_parameters_non_pay_returns_empty(client, action):
    assert AlipayBuilder(client).get_allowed_service_parameters(action) == {}


def test_pay_posts_transaction_and_parses_response(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "alipay-key-123", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        AlipayBuilder(client)
        .currency("EUR")
        .amount(12.34)
        .description("Alipay order")
        .invoice("INV-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
        .add_parameter("UseMobileView", True)
        .pay()
    )

    assert response.key == "alipay-key-123"
    mock_strategy.assert_all_consumed()
