"""Unit tests for :class:`WeroBuilder`."""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.wero_builder import WeroBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.mock_request import BuckarooMockRequest
from tests.support.builders import populate_required_fields


def test_construction_with_client_succeeds(client):
    builder = WeroBuilder(client)
    assert isinstance(builder, WeroBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_wero(client):
    assert WeroBuilder(client).get_service_name() == "Wero"


def test_get_allowed_service_parameters_pay_snapshot(client):
    builder = WeroBuilder(client)
    assert builder.get_allowed_service_parameters("Pay") == {}


def test_get_allowed_service_parameters_pay_is_case_insensitive(client):
    builder = WeroBuilder(client)
    assert builder.get_allowed_service_parameters("pay") == (
        builder.get_allowed_service_parameters("Pay")
    )


@pytest.mark.parametrize("action", ["Refund", "Capture", "Authorize", "UnknownAction"])
def test_get_allowed_service_parameters_non_pay_returns_empty(client, action):
    assert WeroBuilder(client).get_allowed_service_parameters(action) == {}


def test_pay_posts_transaction_and_parses_response(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "wero-key-123", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        populate_required_fields(WeroBuilder(client), amount=25.00)
        .pay()
    )

    assert response.key == "wero-key-123"
    mock_strategy.assert_all_consumed()
