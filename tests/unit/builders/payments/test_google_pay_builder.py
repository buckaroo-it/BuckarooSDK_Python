"""Per-builder unit tests for :class:`GooglePayBuilder`.

Covers construction, service-name shape, allowed-parameter snapshots for every
supported action, mixin presence, and an end-to-end ``pay()`` dispatch through
``MockBuckaroo``. Phase 7.15.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.google_pay_builder import GooglePayBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


def test_construct_with_buckaroo_client_returns_payment_builder(client):
    builder = GooglePayBuilder(client)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_google_pay(client):
    assert GooglePayBuilder(client).get_service_name() == "GooglePay"


def test_get_allowed_service_parameters_pay_snapshot(client):
    assert GooglePayBuilder(client).get_allowed_service_parameters("Pay") == {
        "PaymentData": {"type": str, "required": True, "description": ""},
        "CustomerCardName": {"type": str, "required": False, "description": ""},
    }


def test_get_allowed_service_parameters_is_case_insensitive_for_pay(client):
    """Source lower-cases the action before matching, so "pay" equals "Pay"."""
    builder = GooglePayBuilder(client)
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters("Pay")


def test_get_allowed_service_parameters_unsupported_action_returns_empty(client):
    assert GooglePayBuilder(client).get_allowed_service_parameters("Refund") == {}


def test_google_pay_declares_from_dict_method(client):
    """``from_dict`` is inherited from PaymentBuilder and used by GooglePay
    callers to bulk-populate service parameters. Pin the shape so a base-class
    refactor that renames it surfaces here."""
    builder = GooglePayBuilder(client)
    assert hasattr(builder, "from_dict")
    assert callable(builder.from_dict)


def test_pay_dispatches_googlepay_service_through_mock_buckaroo():
    client = BuckarooClient("store_key", "secret_key", mode="test")
    mock = MockBuckaroo()
    client.http_client.http_strategy = mock
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "GP-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    builder = populate_required_fields(GooglePayBuilder(client), amount=10.50)

    response = builder.pay(validate=False)

    assert response.key == "GP-1"
    mock.assert_all_consumed()
