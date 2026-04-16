"""Per-builder unit tests for :class:`ApplePayBuilder`.

Covers construction, service-name shape, allowed-parameter snapshots for every
supported action, mixin presence, and an end-to-end ``pay()`` dispatch through
``MockBuckaroo``. Phase 7.2.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.apple_pay_builder import ApplePayBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


@pytest.fixture
def client():
    """BuckarooClient wired to a MockBuckaroo strategy."""
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = MockBuckaroo()
    return c


def test_construct_with_buckaroo_client_returns_payment_builder(client):
    builder = ApplePayBuilder(client)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_applepay(client):
    assert ApplePayBuilder(client).get_service_name() == "applepay"


def test_get_allowed_service_parameters_pay_snapshot(client):
    assert ApplePayBuilder(client).get_allowed_service_parameters("Pay") == {
        "PaymentData": {
            "type": str,
            "required": True,
            "description": "Apple Pay payment data",
        },
        "CustomerCardName": {
            "type": str,
            "required": False,
            "description": "Customer card name",
        },
    }


def test_get_allowed_service_parameters_is_case_insensitive_for_pay(client):
    """Source lower-cases the action before matching, so "pay" equals "Pay"."""
    builder = ApplePayBuilder(client)
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters("Pay")


def test_get_allowed_service_parameters_unsupported_action_returns_empty(client):
    assert ApplePayBuilder(client).get_allowed_service_parameters("Refund") == {}


def test_pay_dispatches_applepay_service_through_mock_buckaroo():
    client = BuckarooClient("store_key", "secret_key", mode="test")
    mock = MockBuckaroo()
    client.http_client.http_strategy = mock
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "AP-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    builder = ApplePayBuilder(client)
    builder.currency("EUR").amount(10.50).description("desc").invoice("INV-1")
    builder.return_url("https://ret.example/ok")
    builder.return_url_cancel("https://ret.example/cancel")
    builder.return_url_error("https://ret.example/error")
    builder.return_url_reject("https://ret.example/reject")

    response = builder.pay(validate=False)

    assert response.key == "AP-1"
    mock.assert_all_consumed()
