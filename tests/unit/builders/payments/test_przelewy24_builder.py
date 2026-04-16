"""Unit tests for :class:`Przelewy24Builder`.

Targets 100% line + branch coverage of
``buckaroo/builders/payments/przelewy24_builder.py``. The builder carries no
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
from buckaroo.builders.payments.przelewy24_builder import Przelewy24Builder
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
    builder = Przelewy24Builder(client)
    assert isinstance(builder, Przelewy24Builder)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_przelewy24(client):
    assert Przelewy24Builder(client).get_service_name() == "przelewy24"


def test_no_class_level_service_name_attribute():
    """Unlike :class:`CreditcardBuilder`, Przelewy24Builder doesn't declare a
    ``_serviceName`` class attribute. The authoritative name is exposed via
    ``get_service_name()``."""
    assert "_serviceName" not in Przelewy24Builder.__dict__


def test_get_allowed_service_parameters_pay_snapshot(client):
    builder = Przelewy24Builder(client)

    assert builder.get_allowed_service_parameters("Pay") == {
        "customerEmail": {
            "type": str,
            "required": True,
            "description": "Customer email address",
        },
        "customerFirstName": {
            "type": str,
            "required": True,
            "description": "Customer first name",
        },
        "customerLastName": {
            "type": str,
            "required": True,
            "description": "Customer last name",
        },
    }


def test_get_allowed_service_parameters_pay_is_case_insensitive(client):
    builder = Przelewy24Builder(client)

    assert builder.get_allowed_service_parameters("pay") == (
        builder.get_allowed_service_parameters("Pay")
    )


def test_get_allowed_service_parameters_defaults_to_pay(client):
    builder = Przelewy24Builder(client)

    assert builder.get_allowed_service_parameters() == (
        builder.get_allowed_service_parameters("Pay")
    )


@pytest.mark.parametrize("action", ["Refund", "Capture", "Authorize", "UnknownAction"])
def test_get_allowed_service_parameters_non_pay_returns_empty(client, action):
    assert Przelewy24Builder(client).get_allowed_service_parameters(action) == {}


def test_pay_dispatches_through_mock_buckaroo(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "p24-key-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        Przelewy24Builder(client)
        .currency("PLN")
        .amount(50.00)
        .description("P24 order")
        .invoice("INV-P24-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
        .pay(validate=False)
    )

    assert response.key == "p24-key-1"
    mock_strategy.assert_all_consumed()
